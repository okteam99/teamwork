#!/usr/bin/env python3
"""state.py 一致性修复回归套件。

覆盖:
- state.json 缺失时输出 JSON 错误(全输出可 json.load 承诺)
- jump-to-stage / reset-prev 不再旁路 checksum(外改 state 先 recover)
- init-feature --force:校验全过才 rename 旧 state.json(校验失败旧状态不毁)
- prepare-check 门禁精确化:stem 精确命中 PASS · 仅 prefix 命中 → 放行 + WARN 留痕
- validate:flow_type 枚举校验
- ship 枚举收紧:phase=merged 不再合法
- 全局 host_audit fallback 退役(external-review 侧见 test_state.TestHostAutoDetect)

运行:python3 -m pytest skills/teamwork/tools/tests/test_state_fixes.py -q
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
STATE_PY = TOOLS / "state.py"
sys.path.insert(0, str(TOOLS))


def run(args: list[str], expect_exit: int = 0) -> dict:
    r = subprocess.run([sys.executable, str(STATE_PY), *args],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}")
    raw = r.stdout if r.stdout.strip().startswith("{") else r.stderr
    return json.loads(raw) if raw.strip().startswith("{") else {}


class _InitCase(unittest.TestCase):
    """init-feature 造合法 state 的基类(bypass prepare 门禁)。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-statefix-"))
        self._prev = os.environ.get("TEAMWORK_BYPASS_PREPARE_CHECK")
        os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev is None:
            os.environ.pop("TEAMWORK_BYPASS_PREPARE_CHECK", None)
        else:
            os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = self._prev

    def _init(self, feature_dir: Path, feature_id: str = "SF-F001", **kw) -> dict:
        args = ["init-feature", "--feature", str(feature_dir),
                "--feature-id", feature_id, "--flow-type", "Feature",
                "--merge-target", "main", "--branch", "feat/x"]
        for k, v in kw.items():
            args += [f"--{k.replace('_', '-')}", v] if v is not True else [f"--{k.replace('_', '-')}"]
        return run(args, expect_exit=kw.pop("expect_exit", 0) if "expect_exit" in kw else 0)


# ─── 19 · state.json 缺失 → JSON 错误输出 ───────────────────────────────


class TestStatePathJsonError(unittest.TestCase):
    def test_missing_state_json_emits_json(self):
        d = run(["snapshot", "--feature", "/nonexistent/feature/dir"], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("state.json not found", d["error"])
        self.assertIn("hint", d)


# ─── 18 · jump-to-stage / reset-prev 不再旁路 checksum ─────────────────


class TestChecksumNoBypassOnJumpReset(_InitCase):
    def _tamper(self, feature_dir: Path) -> None:
        sf = feature_dir / "state.json"
        st = json.loads(sf.read_text(encoding="utf-8"))
        st["feature_id"] = "TAMPERED"  # 外改 · checksum 变 stale
        sf.write_text(json.dumps(st), encoding="utf-8")

    def test_jump_to_stage_dies_on_tampered_state(self):
        feat = self.tmp / "f1"
        self._init(feat)
        self._tamper(feat)
        d = run(["jump-to-stage", "--feature", str(feat),
                 "--to", "blueprint", "--reason", "test"], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("checksum", d["error"])
        self.assertIn("recover", d["hint"])

    def test_reset_prev_dies_on_tampered_state(self):
        feat = self.tmp / "f2"
        self._init(feat)
        self._tamper(feat)
        d = run(["reset-prev", "--feature", str(feat),
                 "--reason", "test"], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("checksum", d["error"])

    def test_jump_works_after_recover(self):
        feat = self.tmp / "f3"
        self._init(feat)
        self._tamper(feat)
        run(["recover", "--feature", str(feat), "--reason", "test 外改后认证"])
        d = run(["jump-to-stage", "--feature", str(feat),
                 "--to", "blueprint", "--reason", "test 改道"])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["to_stage"], "blueprint")


# ─── 16 · init-feature --force 先验后毁 ────────────────────────────────


class TestInitForceValidatesBeforeRename(_InitCase):
    def test_failed_validation_keeps_old_state_json(self):
        feat = self.tmp / "keep"
        d = self._init(feat, feature_id="SF-F010")
        self.assertEqual(d["verdict"], "OK")
        original = (feat / "state.json").read_text(encoding="utf-8")
        # --force 重建 · 但 worktree path 不存在 → die(worktree 物理存在校验)
        r = subprocess.run(
            [sys.executable, str(STATE_PY), "init-feature",
             "--feature", str(feat), "--feature-id", "SF-F010",
             "--flow-type", "Feature", "--merge-target", "main",
             "--branch", "feat/x", "--force",
             "--worktree-mode", "manual",
             "--worktree-path", str(self.tmp / "no-such-worktree")],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        # 旧 state.json 原位未动 · 无 .bak 残留
        self.assertEqual((feat / "state.json").read_text(encoding="utf-8"), original)
        self.assertEqual(list(feat.glob("state.json.bak.*")), [])

    def test_force_success_still_backs_up(self):
        feat = self.tmp / "backup"
        self._init(feat, feature_id="SF-F011")
        d = self._init(feat, feature_id="SF-F011", force=True)
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(len(list(feat.glob("state.json.bak.*"))), 1)


# ─── 17 · prepare-check 门禁精确化(exact vs prefix_only)────────────────


class TestPrepareGateExactMatch(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-gatex-"))
        self.audit = self.tmp / "audit.jsonl"
        self._env = {
            "TEAMWORK_PREPARE_AUDIT_PATH": os.environ.get("TEAMWORK_PREPARE_AUDIT_PATH"),
            "TEAMWORK_BYPASS_PREPARE_CHECK": os.environ.get("TEAMWORK_BYPASS_PREPARE_CHECK"),
        }
        os.environ["TEAMWORK_PREPARE_AUDIT_PATH"] = str(self.audit)
        os.environ.pop("TEAMWORK_BYPASS_PREPARE_CHECK", None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _write_audit(self, stem: str, age_sec: int = 0) -> None:
        ts = (datetime.now(timezone.utc) - timedelta(seconds=age_sec)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        rec = {"timestamp": ts, "feature_id_prefix": "GATEX",
               "flow_type": "Feature", "id_letter": "F",
               "next_available_id_stem": stem,
               "features_root": str(self.tmp), "existing_count": 0}
        with self.audit.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    def _init(self, feature_id: str, expect_exit: int = 0) -> dict:
        feat = self.tmp / feature_id
        return run(["init-feature", "--feature", str(feat),
                    "--feature-id", feature_id, "--flow-type", "Feature",
                    "--merge-target", "main", "--branch", "feat/x"],
                   expect_exit=expect_exit)

    def test_exact_stem_match_passes_without_warning(self):
        self._write_audit("GATEX-F100")
        d = self._init("GATEX-F100-thing")
        self.assertEqual(d["verdict"], "OK")
        self.assertNotIn("prepare_match_warning", d)
        st = json.loads((self.tmp / "GATEX-F100-thing" / "state.json")
                        .read_text(encoding="utf-8"))
        self.assertFalse(any("仅 prefix 命中" in c for c in st["concerns"]))

    def test_prefix_only_match_passes_with_warning_and_concern(self):
        self._write_audit("GATEX-F100")  # 号段属于另一 feature
        d = self._init("GATEX-F200-other")
        self.assertEqual(d["verdict"], "OK")
        self.assertIn("prepare_match_warning", d)
        self.assertIn("仅 prefix 命中", d["prepare_match_warning"])
        st = json.loads((self.tmp / "GATEX-F200-other" / "state.json")
                        .read_text(encoding="utf-8"))
        self.assertTrue(any("仅 prefix 命中" in c for c in st["concerns"]))

    def test_stem_number_prefix_not_false_exact(self):
        """stem=GATEX-F100 不精确命中 GATEX-F1001-x(号段边界:stem 后必接 '-')。"""
        self._write_audit("GATEX-F100")
        d = self._init("GATEX-F1001-x")
        self.assertEqual(d["verdict"], "OK")
        self.assertIn("prepare_match_warning", d)

    def test_expired_still_blocks(self):
        self._write_audit("GATEX-F100", age_sec=7200)
        d = self._init("GATEX-F100-thing", expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("60min", d["audit_detail"]["reason"])

    def test_helper_unit_exact_vs_prefix(self):
        from state import _check_prepare_audit  # type: ignore
        self._write_audit("GATEX-F100")
        d = _check_prepare_audit("GATEX-F100-thing")
        self.assertEqual(d["verdict"], "PASS")
        self.assertEqual(d["match"], "exact")
        d2 = _check_prepare_audit("GATEX-F999-other")
        self.assertEqual(d2["verdict"], "PASS")
        self.assertEqual(d2["match"], "prefix_only")


# ─── 15 · validate flow_type 枚举 ──────────────────────────────────────


class TestValidateFlowType(_InitCase):
    def test_bogus_flow_type_fails_validate(self):
        feat = self.tmp / "vft"
        self._init(feat)
        run(["raw-write", "--feature", str(feat),
             "--set", "flow_type=bogus流程",
             "--reason", "test:注入非法 flow_type"])
        d = run(["validate", "--feature", str(feat)], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertTrue(any("flow_type" in e for e in d["errors"]))

    def test_legal_flow_type_passes(self):
        feat = self.tmp / "vok"
        self._init(feat)
        d = run(["validate", "--feature", str(feat)])
        self.assertEqual(d["verdict"], "PASS")
        self.assertIn("flow_type enum", d["checks_passed"])


# ─── 20 · ship 枚举收紧(merged/failed 死值已删)─────────────────────────


class TestShipEnumTightened(_InitCase):
    def test_phase_merged_now_illegal(self):
        feat = self.tmp / "ship1"
        self._init(feat)
        run(["raw-write", "--feature", str(feat),
             "--set", "ship.phase=merged",
             "--reason", "test:注入已删枚举值"])
        d = run(["validate", "--feature", str(feat)], expect_exit=1)
        self.assertTrue(any("ship.phase" in e for e in d["errors"]))

    def test_shipped_failed_now_illegal(self):
        feat = self.tmp / "ship2"
        self._init(feat)
        run(["raw-write", "--feature", str(feat),
             "--set", "ship.shipped=failed",
             "--reason", "test:注入已删枚举值"])
        d = run(["validate", "--feature", str(feat)], expect_exit=1)
        self.assertTrue(any("ship.shipped" in e for e in d["errors"]))

    def test_pushed_still_legal(self):
        feat = self.tmp / "ship3"
        self._init(feat)
        run(["raw-write", "--feature", str(feat),
             "--set", "ship.phase=pushed",
             "--set", "ship.feature_head_commit=abc123",
             "--reason", "test:合法值不受影响"])
        d = run(["validate", "--feature", str(feat)])
        self.assertEqual(d["verdict"], "PASS")


# ─── 20 · 死代码确认删除(import 面)─────────────────────────────────────


class TestDeadCodeRemoved(unittest.TestCase):
    def test_state_dead_symbols_gone(self):
        import state  # type: ignore
        for name in ("_enforce_main_worktree", "_check_main_worktree",
                     "write_or_die", "compute_legal_next", "HOST_AUDIT_PATH_ENV"):
            self.assertFalse(hasattr(state, name), f"state.{name} 应已删除")

    def test_specs_dead_symbols_gone(self):
        import _v8_stage_specs as sp  # type: ignore
        for name in ("_pause_discipline_block", "EXTERNAL_REVIEW_SAME_SOURCE_BLOCKED"):
            self.assertFalse(hasattr(sp, name), f"_v8_stage_specs.{name} 应已删除")

    def test_engine_dead_entries_gone(self):
        import _v8_engine as en  # type: ignore
        self.assertNotIn("planning", en.STAGE_SPEC_FILES)
        self.assertFalse(any(ft == "Feature Planning"
                             for ft, _ in en.DEFAULT_REVIEW_ROLES))

    def test_ship_enum_dead_values_gone(self):
        import state  # type: ignore
        self.assertNotIn("merged", state.SHIP_PHASE_ENUM)
        self.assertNotIn("merged", state.SHIP_SHIPPED_ENUM)
        self.assertNotIn("failed", state.SHIP_SHIPPED_ENUM)


if __name__ == "__main__":
    unittest.main(verbosity=2)
