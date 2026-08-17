#!/usr/bin/env python3
"""state.py 回归套件 · 14 子命令 happy + 边界 + 物化拦截。

运行：
    python3 -m pytest skills/teamwork/tools/tests/         （推荐）
    python3 skills/teamwork/tools/tests/test_state.py      （无 pytest 兜底）
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SKILL = TOOLS.parent
STATE_PY = TOOLS / "state.py"
sys.path.insert(0, str(TOOLS))  # 让 from _v8_stage_specs / _v8_engine 等内部模块 import 可用


def run(args: list[str], expect_exit: int = 0,
        env_extra: dict[str, str] | None = None) -> dict:
    """跑 state.py 子命令 · 返回 stdout JSON · 校验 exit code。

    env_extra: 临时叠加环境变量（如模拟 TEAMWORK_FORCE_LINKED_WORKTREE · v7.3.10+P0-156）.
    """
    cmd = [sys.executable, str(STATE_PY), *args]
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    )
    raw = r.stdout if r.returncode == 0 else (r.stdout or r.stderr)
    return json.loads(raw) if raw.strip().startswith("{") else {}


class TestInitFeature(unittest.TestCase):
    """v7.3.10+P0-148：init-feature 子命令 + checksum guard。

    v8.14:set TEAMWORK_BYPASS_PREPARE_CHECK=1 让现有 init-feature 测试不依赖
    prepare-check audit · 门禁本身的测试见 TestPrepareAuditGate。
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="init_feat_"))
        self._prev_bypass = os.environ.get("TEAMWORK_BYPASS_PREPARE_CHECK")
        os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = "1"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev_bypass is None:
            os.environ.pop("TEAMWORK_BYPASS_PREPARE_CHECK", None)
        else:
            os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = self._prev_bypass

    def test_init_feature_creates_state_json(self) -> None:
        target = self.tmp / "docs" / "features" / "ADMIN-F013"
        d = run([
            "init-feature",
            "--feature", str(target),
            "--feature-id", "ADMIN-F013-tax-billing",
            "--flow-type", "Feature",
            "--sub-project", "admin",
            "--merge-target", "staging",
            "--branch", "feat/admin-f013-tax-billing",
        ])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["action"], "init-feature")
        self.assertEqual(d["feature_id"], "ADMIN-F013-tax-billing")
        self.assertEqual(d["current_stage"], "goal")  # Feature default
        self.assertTrue(d["checksum_prefix"].startswith("sha256:"))
        # state.json 真存在 + 校验 schema 字段
        sf = target / "state.json"
        self.assertTrue(sf.exists())
        state = json.loads(sf.read_text(encoding="utf-8"))
        self.assertEqual(state["feature_id"], "ADMIN-F013-tax-billing")
        self.assertEqual(state["flow_type"], "Feature")
        self.assertEqual(state["merge_target"], "staging")
        self.assertEqual(state["worktree"]["branch"], "feat/admin-f013-tax-billing")
        self.assertIn("_state_checksum", state)

    def test_init_feature_bug_defaults_to_diagnose(self) -> None:
        """v8.107:Bug 首 stage = diagnose(根因细查 + 修复方案确认)· 不再直入 dev(防修偏)。"""
        target = self.tmp / "bug"
        d = run([
            "init-feature",
            "--feature", str(target),
            "--feature-id", "BUG-007-login",
            "--flow-type", "Bug",
            "--merge-target", "main",
            "--branch", "fix/login",
        ])
        self.assertEqual(d["current_stage"], "diagnose")

    def test_v8107_bug_dev_requires_diagnose(self) -> None:
        """v8.107:Bug 流程 dev 准入要求 diagnose output_satisfied(不再直入)· Micro 仍直入。"""
        from _v8_stage_specs import _check_blueprint_or_alt_done  # type: ignore
        self.assertFalse(_check_blueprint_or_alt_done(
            {"flow_type": "Bug", "stage_contracts": {}}, None))
        self.assertTrue(_check_blueprint_or_alt_done(
            {"flow_type": "Bug", "stage_contracts": {"diagnose": {"output_satisfied": True}}}, None))
        self.assertTrue(_check_blueprint_or_alt_done(
            {"flow_type": "Micro", "stage_contracts": {}}, None))

    def test_init_feature_existing_state_fails_without_force(self) -> None:
        target = self.tmp / "exists"
        target.mkdir(parents=True)
        (target / "state.json").write_text('{"feature_id":"old"}', encoding="utf-8")
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "X", "--flow-type", "Feature",
            "--merge-target", "main", "--branch", "feat/x",
        ], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("already exists", d["error"])

    # ── v8.63:yolo 模式硬约束(merge_target 必须非主分支)──

    def test_v863_yolo_rejects_main_merge_target(self) -> None:
        """v8.63:yolo + merge_target=main → FAIL(自动 merge 不得直接进 main)。"""
        target = self.tmp / "docs" / "features" / "YOLO-F001"
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F001", "--flow-type", "Feature",
            "--merge-target", "main", "--branch", "feat/yolo", "--yolo",
        ], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("主分支", d["error"])
        self.assertFalse((target / "state.json").exists())  # gate 早于建 state

    def test_v863_yolo_rejects_master_merge_target(self) -> None:
        """v8.63:yolo + merge_target=master → 同样 FAIL。"""
        target = self.tmp / "docs" / "features" / "YOLO-F002"
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F002", "--flow-type", "Feature",
            "--merge-target", "master", "--branch", "feat/yolo2", "--yolo",
        ], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")

    def _seed_yolo_preflight(self, target) -> None:
        """v8.179:yolo 预研门 —— init-feature --yolo 前 feature 目录须有已填 YOLO-PREFLIGHT.md。"""
        target.mkdir(parents=True, exist_ok=True)
        (target / "YOLO-PREFLIGHT.md").write_text(
            "# YOLO 预研\n## 1. 深入调研\nx\n## 2. 核心重要决策\n无 · 已充分清晰\n"
            "## 3. 用户确认\n用户已确认 · 授权 yolo 自主", encoding="utf-8")

    def test_v863_yolo_non_main_target_ok_implies_auto_mode(self) -> None:
        """v8.63:yolo + 非主分支(dev)→ OK · state.json yolo=true + auto_mode=true(implies)。"""
        target = self.tmp / "docs" / "features" / "YOLO-F003"
        self._seed_yolo_preflight(target)
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F003", "--flow-type", "Feature",
            "--merge-target", "dev", "--branch", "feat/yolo3", "--yolo",
        ])
        self.assertEqual(d["verdict"], "OK")
        state = json.loads((target / "state.json").read_text(encoding="utf-8"))
        self.assertTrue(state["yolo"])
        self.assertTrue(state["auto_mode"])  # yolo implies auto_mode

    def test_v8179_yolo_without_preflight_blocks(self) -> None:
        """v8.179:yolo 预研门 —— 无 YOLO-PREFLIGHT.md → init-feature --yolo FAIL。"""
        target = self.tmp / "docs" / "features" / "YOLO-F179"
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F179", "--flow-type", "Feature",
            "--branch", "feat/y179", "--yolo", "dev-int",
        ], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("预研门", d["error"])

    def test_v8179_yolo_preflight_sentinel_blocks(self) -> None:
        """v8.179:YOLO-PREFLIGHT.md 仍含未完成哨兵 → FAIL(强制真填)。"""
        target = self.tmp / "docs" / "features" / "YOLO-F180"
        target.mkdir(parents=True, exist_ok=True)
        (target / "YOLO-PREFLIGHT.md").write_text(
            "# x\n<!-- YOLO-PREFLIGHT-UNFILLED -->\n## 核心\n## 用户确认\n", encoding="utf-8")
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F180", "--flow-type", "Feature",
            "--branch", "feat/y180", "--yolo", "dev-int",
        ], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("哨兵", d["error"])

    def test_v863_non_yolo_main_target_unaffected(self) -> None:
        """v8.63:非 yolo + main → 不受 gate 影响(向后兼容)· yolo=false。"""
        target = self.tmp / "docs" / "features" / "YOLO-F004"
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F004", "--flow-type", "Feature",
            "--merge-target", "main", "--branch", "feat/normal",
        ])
        self.assertEqual(d["verdict"], "OK")
        state = json.loads((target / "state.json").read_text(encoding="utf-8"))
        self.assertFalse(state["yolo"])

    # ── v8.65:--yolo <branch> 携带 merge_target(覆盖 --merge-target / localconfig)──

    def test_v865_yolo_branch_is_merge_target(self) -> None:
        """v8.65:--yolo <branch>(无 --merge-target)→ branch 即 merge_target。"""
        target = self.tmp / "docs" / "features" / "YOLO-F005"
        self._seed_yolo_preflight(target)
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F005", "--flow-type", "Feature",
            "--branch", "feat/yolo5", "--yolo", "dev-integration",
        ])
        self.assertEqual(d["verdict"], "OK")
        state = json.loads((target / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["merge_target"], "dev-integration")
        self.assertTrue(state["yolo"])
        self.assertTrue(state["auto_mode"])

    def test_v865_yolo_branch_overrides_merge_target(self) -> None:
        """v8.65:--yolo <branch> 同时给 --merge-target → yolo branch 胜出。"""
        target = self.tmp / "docs" / "features" / "YOLO-F006"
        self._seed_yolo_preflight(target)
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F006", "--flow-type", "Feature",
            "--branch", "feat/yolo6", "--merge-target", "staging", "--yolo", "dedicated-int",
        ])
        self.assertEqual(d["verdict"], "OK")
        state = json.loads((target / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["merge_target"], "dedicated-int")  # yolo branch 覆盖 --merge-target

    def test_v865_yolo_branch_main_rejected(self) -> None:
        """v8.65:--yolo main(branch=主分支)→ FAIL(gate 同样拦)。"""
        target = self.tmp / "docs" / "features" / "YOLO-F007"
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F007", "--flow-type", "Feature",
            "--branch", "feat/yolo7", "--yolo", "main",
        ], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("主分支", d["error"])

    def test_v865_no_merge_target_source_fails(self) -> None:
        """v8.65:既无 --merge-target 又无 --yolo <branch> → FAIL(缺 merge_target)。"""
        target = self.tmp / "docs" / "features" / "YOLO-F008"
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F008", "--flow-type", "Feature",
            "--branch", "feat/yolo8",
        ], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("merge_target", d["error"])

    # ── v8.66:yolo 加重审核 · change-review-roles 去 external 物化 BLOCK ──

    def test_v866_yolo_blocks_external_removal(self) -> None:
        """v8.66:yolo 模式 change-review-roles 去 external → BLOCK(唯一安全网)。"""
        target = self.tmp / "docs" / "features" / "YOLO-F009"
        self._seed_yolo_preflight(target)
        run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F009", "--flow-type", "Feature",
            "--branch", "feat/yolo9", "--yolo", "dev-int",
        ])
        d = run([
            "change-review-roles", "--feature", str(target),
            "--stage", "blueprint", "--roles", "qa,architect", "--reason", "efficiency",
        ], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("external", d["error"])

    def test_v866_yolo_external_removal_with_ack(self) -> None:
        """v8.66:--accept-external-removal → 放行 + concern WARN 留痕。"""
        target = self.tmp / "docs" / "features" / "YOLO-F010"
        self._seed_yolo_preflight(target)
        run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F010", "--flow-type", "Feature",
            "--branch", "feat/yolo10", "--yolo", "dev-int",
        ])
        d = run([
            "change-review-roles", "--feature", str(target),
            "--stage", "blueprint", "--roles", "qa,architect",
            "--reason", "external CLI 未装 · 重试失败", "--accept-external-removal",
        ])
        self.assertEqual(d["verdict"], "OK")
        state = json.loads((target / "state.json").read_text(encoding="utf-8"))
        self.assertNotIn("external", state["stage_review_roles"]["blueprint"])
        self.assertTrue(any("yolo 去 external" in c for c in state.get("concerns", [])))

    def test_v866_non_yolo_external_removal_ok(self) -> None:
        """v8.66:非 yolo 去 external 不受 guard 影响(向后兼容)。"""
        target = self.tmp / "docs" / "features" / "YOLO-F011"
        run([
            "init-feature", "--feature", str(target),
            "--feature-id", "YOLO-F011", "--flow-type", "Feature",
            "--branch", "feat/n", "--merge-target", "staging",
        ])
        d = run([
            "change-review-roles", "--feature", str(target),
            "--stage", "blueprint", "--roles", "qa,architect", "--reason", "non-yolo",
        ])
        self.assertEqual(d["verdict"], "OK")

    def test_init_feature_uses_feature_as_single_source_for_path(self) -> None:
        """v7.3.10+P0-149 regression：PTR-F032 case · 防 --feature 和 artifact_root 分裂。

        实战 bug：4.6 传 --feature 仅 feature 名 + 期待 --artifact-root 控制路径 →
        state.json 落 CWD/feature-name/state.json（错位置）。
        修复：删 --artifact-root · --feature 单源 · artifact_root 字段 = --feature 值。
        """
        target = self.tmp / "apps" / "partner" / "docs" / "features" / "PTR-F032-test"
        d = run([
            "init-feature",
            "--feature", str(target),
            "--feature-id", "PTR-F032-test",
            "--flow-type", "Feature",
            "--sub-project", "partner",
            "--merge-target", "staging",
            "--branch", "feat/ptr-f032",
        ])
        self.assertEqual(d["verdict"], "OK")
        # state.json 必须落在 --feature 指定路径
        self.assertTrue((target / "state.json").exists())
        # artifact_root 字段 = --feature 路径
        state = json.loads((target / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["artifact_root"], str(target))

    def test_init_feature_rejects_old_artifact_root_arg(self) -> None:
        """v7.3.10+P0-149：--artifact-root 已删 · argparse 应直接 reject。"""
        target = self.tmp / "apps" / "x"
        cmd = [
            sys.executable, str(STATE_PY), "init-feature",
            "--feature", str(target),
            "--feature-id", "X",
            "--flow-type", "Feature",
            "--merge-target", "main",
            "--branch", "feat/x",
            "--artifact-root", "some/other/path",  # 旧参数
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--artifact-root", r.stderr + r.stdout)
        self.assertIn("unrecognized arguments", r.stderr + r.stdout)

    def test_init_feature_warns_on_mismatched_basename(self) -> None:
        """v7.3.10+P0-149 启发式：--feature basename 不含 --feature-id → stderr 警告。"""
        target = self.tmp / "wrong-slug"
        cmd = [
            sys.executable, str(STATE_PY), "init-feature",
            "--feature", str(target),
            "--feature-id", "ADMIN-F999-mismatch",  # basename 'wrong-slug' 不含
            "--flow-type", "Feature",
            "--merge-target", "main",
            "--branch", "feat/x",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)  # 不强阻 · 仅警告
        self.assertIn("WARNING", r.stderr)
        self.assertIn("basename", r.stderr)

    def test_init_feature_force_backs_up(self) -> None:
        target = self.tmp / "force"
        target.mkdir(parents=True)
        (target / "state.json").write_text('{"feature_id":"old","_state_checksum":"sha256:old"}', encoding="utf-8")
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "NEW", "--flow-type", "Feature",
            "--merge-target", "main", "--branch", "feat/new",
            "--force",
        ])
        self.assertEqual(d["verdict"], "OK")
        # backup 文件应存在
        backups = list(target.glob("state.json.bak.*"))
        self.assertEqual(len(backups), 1)

    # ── v8.36:--host 写到 state.json.host(治本 SVC-PLATFORM-F054 case)──

    def test_v836_init_feature_writes_host_to_state_json(self):
        """v8.36:init-feature --host codex-cli → state.json.host = 'codex-cli'。"""
        target = self.tmp / "v836_host"
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "TEST-F901", "--flow-type", "Feature",
            "--merge-target", "main", "--branch", "feat/test-f901",
            "--host", "codex-cli",
        ])
        self.assertEqual(d["verdict"], "OK")
        state = json.loads((target / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["host"], "codex-cli")
        # host_history 应初始化 1 条
        self.assertEqual(len(state["host_history"]), 1)
        self.assertEqual(state["host_history"][0]["host"], "codex-cli")
        self.assertEqual(state["host_history"][0]["source"], "init-feature")

    def test_v836_init_feature_no_host_defaults_to_none(self):
        """v8.36:不传 --host → state.json.host=None · host_history=[]·向后兼容。"""
        target = self.tmp / "v836_no_host"
        d = run([
            "init-feature", "--feature", str(target),
            "--feature-id", "TEST-F902", "--flow-type", "Feature",
            "--merge-target", "main", "--branch", "feat/test-f902",
        ])
        self.assertEqual(d["verdict"], "OK")
        state = json.loads((target / "state.json").read_text(encoding="utf-8"))
        self.assertIsNone(state["host"])
        self.assertEqual(state["host_history"], [])

    def test_v836_init_feature_illegal_host_blocked(self):
        """v8.36:--host 非法值 → argparse BLOCK。"""
        import subprocess
        target = self.tmp / "v836_illegal"
        r = subprocess.run([
            sys.executable,
            str(STATE_PY), "init-feature", "--feature", str(target),
            "--feature-id", "TEST-F903", "--flow-type", "Feature",
            "--merge-target", "main", "--branch", "feat/test-f903",
            "--host", "made-up-host",
        ], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("made-up-host", r.stderr)


class TestYoloBypass(unittest.TestCase):
    """v8.64:yolo 模式 require_user_confirmed 放行(零人工 bypass · AI 自主解决核心目标)。"""

    def _args(self, user_confirmed: bool = False):
        a = type("A", (), {})()
        a.user_confirmed = user_confirmed
        return a

    def test_yolo_skips_user_confirmed_gate(self):
        """v8.64:yolo=True + 无 --user-confirmed → 放行(返回 None · 不 exit)。"""
        sys.path.insert(0, str(TOOLS))
        from _v8_engine import require_user_confirmed  # type: ignore
        self.assertIsNone(
            require_user_confirmed(self._args(user_confirmed=False), yolo=True))

    def test_non_yolo_requires_user_confirmed(self):
        """v8.64:yolo=False + 无 --user-confirmed → emit FAIL + sys.exit(1)(防 AI 自决保留)。"""
        sys.path.insert(0, str(TOOLS))
        from _v8_engine import require_user_confirmed  # type: ignore
        import io
        from contextlib import redirect_stdout
        with self.assertRaises(SystemExit) as cm, redirect_stdout(io.StringIO()):
            require_user_confirmed(self._args(user_confirmed=False), yolo=False)
        self.assertEqual(cm.exception.code, 1)

    def test_explicit_user_confirmed_passes_regardless(self):
        """v8.64:显式 --user-confirmed → 放行(yolo 与否都行 · 向后兼容)。"""
        sys.path.insert(0, str(TOOLS))
        from _v8_engine import require_user_confirmed  # type: ignore
        self.assertIsNone(
            require_user_confirmed(self._args(user_confirmed=True), yolo=False))


class TestSetMode(unittest.TestCase):
    """v8.69:set-mode 语义化设 auto_mode / yolo(替代 raw-write · 物化 + audit)。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._prev = os.environ.get("TEAMWORK_BYPASS_PREPARE_CHECK")
        os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = "1"
        self.feat = self.tmp / "docs" / "features" / "SM-F001"
        run(["init-feature", "--feature", str(self.feat), "--feature-id", "SM-F001",
             "--flow-type", "Feature", "--branch", "feat/sm", "--merge-target", "staging"])

    def tearDown(self):
        if self._prev is None:
            os.environ.pop("TEAMWORK_BYPASS_PREPARE_CHECK", None)
        else:
            os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = self._prev
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _state(self):
        return json.loads((self.feat / "state.json").read_text(encoding="utf-8"))

    def _sm(self, *flags, expect_exit=0):
        return run(["set-mode", "--feature", str(self.feat), *flags], expect_exit=expect_exit)

    def test_enable_auto_mode(self):
        d = self._sm("--auto-mode", "--reason", "x")
        self.assertEqual(d["verdict"], "OK")
        st = self._state()
        self.assertTrue(st["auto_mode"])
        self.assertEqual(len(st["mode_changes"]), 1)

    def test_enable_yolo_with_branch_implies_auto(self):
        d = self._sm("--yolo", "dev-int", "--reason", "go yolo")
        self.assertEqual(d["verdict"], "OK")
        st = self._state()
        self.assertTrue(st["yolo"])
        self.assertTrue(st["auto_mode"])           # implies
        self.assertEqual(st["merge_target"], "dev-int")
        self.assertTrue(any("yolo 开启" in c for c in st.get("concerns", [])))

    def test_yolo_main_rejected(self):
        d = self._sm("--yolo", "main", "--reason", "bad", expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("主分支", d["error"])

    def test_disable_yolo_keeps_auto(self):
        self._sm("--yolo", "dev-int", "--reason", "on")
        d = self._sm("--no-yolo", "--reason", "off")
        self.assertEqual(d["verdict"], "OK")
        st = self._state()
        self.assertFalse(st["yolo"])
        self.assertTrue(st["auto_mode"])

    def test_no_auto_while_yolo_fails(self):
        self._sm("--yolo", "dev-int", "--reason", "on")
        d = self._sm("--no-auto-mode", "--reason", "x", expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")

    def test_no_flags_fails(self):
        d = self._sm("--reason", "nothing", expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")

    def test_noop_when_no_change(self):
        d = self._sm("--no-yolo", "--reason", "already off")  # yolo 本就 off
        self.assertEqual(d["verdict"], "NOOP")


class TestChecksumGuard(unittest.TestCase):
    """v7.3.10+P0-148：state.json checksum 物化拦截直写。

    v8.14:bypass prepare-check audit · 本类只测 checksum guard 行为 · 与 audit 解耦。
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="checksum_"))
        self._prev_bypass = os.environ.get("TEAMWORK_BYPASS_PREPARE_CHECK")
        os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = "1"
        # 用 init-feature 创建（含 checksum）
        run([
            "init-feature",
            "--feature", str(self.tmp),
            "--feature-id", "CHK-F001",
            "--flow-type", "Feature",
            "--merge-target", "main",
            "--branch", "feat/chk",
        ])

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev_bypass is None:
            os.environ.pop("TEAMWORK_BYPASS_PREPARE_CHECK", None)
        else:
            os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = self._prev_bypass

    def test_legitimate_read_passes(self) -> None:
        d = run(["snapshot", "--feature", str(self.tmp)])
        self.assertEqual(d["snapshot"]["feature_id"], "CHK-F001")

    def test_external_modification_blocked(self) -> None:
        """模拟 AI 用 Write 直改 state.json → 下次 state.py 调用 fail。"""
        sf = self.tmp / "state.json"
        state = json.loads(sf.read_text(encoding="utf-8"))
        state["feature_id"] = "TAMPERED"  # 手动改字段
        sf.write_text(json.dumps(state), encoding="utf-8")
        d = run(["snapshot", "--feature", str(self.tmp)], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("checksum mismatch", d["error"])
        self.assertIn("recover", d["hint"])

    def test_bypass_env_allows_read(self) -> None:
        """TEAMWORK_BYPASS_CHECKSUM=1 旁路（debug only）。"""
        sf = self.tmp / "state.json"
        state = json.loads(sf.read_text(encoding="utf-8"))
        state["feature_id"] = "TAMPERED"
        sf.write_text(json.dumps(state), encoding="utf-8")
        # 用 subprocess 设 env · run() helper 不支持 env · 直接 subprocess
        env = os.environ.copy()
        env["TEAMWORK_BYPASS_CHECKSUM"] = "1"
        r = subprocess.run(
            [sys.executable, str(STATE_PY), "snapshot", "--feature", str(self.tmp)],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(r.returncode, 0)

    def test_legacy_state_without_checksum_accepted(self) -> None:
        """旧 state.json 无 _state_checksum → silent accept · 下次写补上。"""
        sf = self.tmp / "state.json"
        state = json.loads(sf.read_text(encoding="utf-8"))
        del state["_state_checksum"]
        sf.write_text(json.dumps(state), encoding="utf-8")
        d = run(["snapshot", "--feature", str(self.tmp)])
        # 无 checksum 不阻断
        self.assertEqual(d["snapshot"]["feature_id"], "CHK-F001")


class TestRecover(unittest.TestCase):
    """v7.3.10+P0-148：recover 子命令重新认证 checksum + 写 concerns。

    v8.14:bypass prepare-check audit · 本类只测 recover 行为 · 与 audit 解耦。
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="recover_"))
        self._prev_bypass = os.environ.get("TEAMWORK_BYPASS_PREPARE_CHECK")
        os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = "1"
        run([
            "init-feature",
            "--feature", str(self.tmp),
            "--feature-id", "REC-F001",
            "--flow-type", "Feature",
            "--merge-target", "main",
            "--branch", "feat/rec",
        ])

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev_bypass is None:
            os.environ.pop("TEAMWORK_BYPASS_PREPARE_CHECK", None)
        else:
            os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = self._prev_bypass

    def test_recover_after_manual_edit(self) -> None:
        sf = self.tmp / "state.json"
        # 手动编辑
        state = json.loads(sf.read_text(encoding="utf-8"))
        state["feature_id"] = "MANUALLY-EDITED"
        sf.write_text(json.dumps(state), encoding="utf-8")
        # 先验证 snapshot 被阻
        run(["snapshot", "--feature", str(self.tmp)], expect_exit=2)
        # recover
        d = run([
            "recover", "--feature", str(self.tmp),
            "--reason", "手工修字段名笔误",
        ])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["action"], "recover")
        self.assertTrue(d["concerns_appended"])
        # 之后 snapshot 通过
        d2 = run(["snapshot", "--feature", str(self.tmp)])
        self.assertEqual(d2["snapshot"]["feature_id"], "MANUALLY-EDITED")
        # concerns 含 recover audit(统一字符串格式 "<ISO> WARN <msg>" · 与 add-concern 等一致)
        state = json.loads(sf.read_text(encoding="utf-8"))
        warns = [c for c in state["concerns"] if isinstance(c, str) and " WARN " in c]
        self.assertTrue(any("recovered after manual edit" in c for c in warns))
        # 防混型回归:concerns 全部是字符串(不再有 dict 条目)
        self.assertTrue(all(isinstance(c, str) for c in state["concerns"]))


class TestReadOnlyCommands(unittest.TestCase):
    """v8.45:补回 snapshot / validate / raw-read 三个 C 类维护命令的直接覆盖。

    背景:v8.45 清理删除了依赖缺失 fixture(`templates/feature-state.json` · v8.0
    切换时就删了 · 从 v8.0 起 v7 遗留的 TestP1ReadOnly 等类一直没通过)的 broken
    测试 · 连带删掉了对这 3 个**活命令**的直接单元测试。本类不依赖任何缺失模板 ·
    用 init-feature(TEAMWORK_BYPASS_PREPARE_CHECK=1 绕过 prepare 门禁)在临时目录
    造合法 state.json · 补回覆盖(pattern 同 TestChecksumGuard / TestRecover)。
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="readonly_"))
        self._prev_bypass = os.environ.get("TEAMWORK_BYPASS_PREPARE_CHECK")
        os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = "1"
        run([
            "init-feature",
            "--feature", str(self.tmp),
            "--feature-id", "RO-F001",
            "--flow-type", "Feature",
            "--merge-target", "main",
            "--branch", "feat/ro",
        ])

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev_bypass is None:
            os.environ.pop("TEAMWORK_BYPASS_PREPARE_CHECK", None)
        else:
            os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = self._prev_bypass

    # ── snapshot ──────────────────────────────────────────────────────
    def test_snapshot_verdict_ok_and_current_stage(self) -> None:
        """snapshot(默认 core tier)→ verdict OK · Feature 初始 current_stage=goal。"""
        d = run(["snapshot", "--feature", str(self.tmp)])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["tier"], "core")
        self.assertEqual(d["snapshot"]["current_stage"], "goal")
        self.assertEqual(d["snapshot"]["feature_id"], "RO-F001")

    # ── validate ──────────────────────────────────────────────────────
    def test_validate_legal_state_passes(self) -> None:
        """合法 state(init-feature 刚建)→ validate PASS · exit 0。"""
        d = run(["validate", "--feature", str(self.tmp)])
        self.assertEqual(d["verdict"], "PASS")
        self.assertIn("stage enum", d["checks_passed"])

    def test_validate_illegal_current_stage_fails(self) -> None:
        """注入非法 current_stage → validate FAIL · exit 1 · 错误指向 current_stage。

        用 raw-write 注入(而非手工 Write 改 state.json):手工改会先触发 checksum
        guard(exit 2)· validate 的 schema 校验根本跑不到;raw-write 走 atomic_write
        重算 checksum · state checksum 合法但 schema 非法 · 才隔离得出纯 schema FAIL。
        """
        run([
            "raw-write", "--feature", str(self.tmp),
            "--set", "current_stage=bogus_stage",
            "--reason", "test:注入非法 stage 验证 validate FAIL 路径",
        ])
        d = run(["validate", "--feature", str(self.tmp)], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertGreaterEqual(d["error_count"], 1)
        self.assertTrue(any("current_stage" in e for e in d["errors"]))

    # ── raw-read ──────────────────────────────────────────────────────
    def test_raw_read_field_current_stage(self) -> None:
        """raw-read --field current_stage → verdict OK · 返回该字段值(goal)。"""
        d = run(["raw-read", "--feature", str(self.tmp), "--field", "current_stage"])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["field"], "current_stage")
        self.assertEqual(d["value"], "goal")


class TestPrepareCheck(unittest.TestCase):
    """prepare-check · flow_type → artifact ID 字母(F/B/M · 治本 Bug 错推 -F)。

    v8.14:重定向 TEAMWORK_PREPARE_AUDIT_PATH → tmp · 防止污染真实 $HOME。
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-pc-"))
        self.root = self.tmp / "features"
        for name in ("PTR-F033-Alpha", "PTR-F046-Beta",
                     "PTR-B017-Gamma", "PTR-B018-Delta", "PTR-M001-Eps"):
            (self.root / name).mkdir(parents=True)
        # v8.79:本类断言顺序号精确值 → 显式 opt-out sequential(全局默认已改 utc 时间戳)
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"id_strategy": "sequential"}), encoding="utf-8")
        self.audit_path = self.tmp / "audit.jsonl"
        self._prev_audit = os.environ.get("TEAMWORK_PREPARE_AUDIT_PATH")
        os.environ["TEAMWORK_PREPARE_AUDIT_PATH"] = str(self.audit_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev_audit is None:
            os.environ.pop("TEAMWORK_PREPARE_AUDIT_PATH", None)
        else:
            os.environ["TEAMWORK_PREPARE_AUDIT_PATH"] = self._prev_audit

    def _check(self, flow_type: str) -> dict:
        # v8.34:全局强制必传 admission_judgment(SKIPPED 兼容路径已删)
        # 测试聚焦于 id_letter 等其他逻辑 · 这里造一个 consistent judgment
        judgment = json.dumps({
            "sections_reviewed": ["§2.1", "§2.2"],
            "matched_signals": [{"section": "§2.1", "signal": "测试用例",
                                 "evidence": "TestPrepareCheck fixture"}],
            "recommended_flow_type": flow_type,
            "ai_rationale": "test fixture (v8.34 mandatory admission_judgment)",
        })
        return run(["prepare-check", "--features-root", str(self.root),
                    "--feature-id-prefix", "PTR", "--flow-type", flow_type,
                    "--user-intent", f"test intent for {flow_type}",
                    "--admission-judgment", judgment])

    def test_bug_recommends_b_series(self) -> None:
        d = self._check("Bug")
        self.assertEqual(d["id_letter"], "B")
        self.assertEqual(d["next_available_id_stem"], "PTR-B019")
        self.assertEqual(d["existing_ids"], ["PTR-B017-Gamma", "PTR-B018-Delta"])

    def test_feature_recommends_f_series(self) -> None:
        d = self._check("Feature")
        self.assertEqual(d["id_letter"], "F")
        self.assertEqual(d["next_available_id_stem"], "PTR-F047")


    def test_micro_recommends_m_series(self) -> None:
        # v8.220:Micro 并入 Feature(preset=micro)· M 系退役 · 与 F 系同号池
        d = self._check("Micro")
        self.assertEqual(d["id_letter"], "F")
        self.assertEqual(d["next_available_id_stem"], "PTR-F047")

    def test_no_flow_type_defaults_to_f_with_warn(self) -> None:
        # v8.34:测「未传 --flow-type」分支 · 但 admission_judgment 仍必传
        judgment = json.dumps({
            "sections_reviewed": ["§2.1"],
            "matched_signals": [{"section": "§2.1", "signal": "test",
                                 "evidence": "no flow_type fixture"}],
            "recommended_flow_type": "Feature",
            "ai_rationale": "v8.34 mandatory admission_judgment fixture",
        })
        d = run(["prepare-check", "--features-root", str(self.root),
                 "--feature-id-prefix", "PTR",
                 "--user-intent", "test intent (no flow type)",
                 "--admission-judgment", judgment])
        self.assertEqual(d["id_letter"], "F")
        self.assertIn("--flow-type", d["hint"])

    def test_empty_series_starts_at_001(self) -> None:
        # v8.34:同上 · 仍需 admission_judgment
        judgment = json.dumps({
            "sections_reviewed": ["§2.1", "§2.2"],
            "matched_signals": [{"section": "§2.1", "signal": "test",
                                 "evidence": "empty series fixture"}],
            "recommended_flow_type": "Bug",
            "ai_rationale": "v8.34 mandatory admission_judgment fixture",
        })
        d = run(["prepare-check", "--features-root", str(self.root),
                 "--feature-id-prefix", "NEWPROJ", "--flow-type", "Bug",
                 "--user-intent", "test intent (empty series)",
                 "--admission-judgment", judgment])
        self.assertEqual(d["next_available_id_stem"], "NEWPROJ-B001")
        self.assertEqual(d["existing_ids"], [])

    def test_prepare_check_writes_audit_jsonl(self) -> None:
        """v8.14:prepare-check 跑成功 → 追写 audit jsonl(init-feature 门禁读这个)。"""
        d = self._check("Feature")
        self.assertTrue(d.get("audit_recorded"))
        self.assertTrue(self.audit_path.exists(),
                        f"audit jsonl 应已写 · path={self.audit_path}")
        lines = self.audit_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["feature_id_prefix"], "PTR")
        self.assertEqual(rec["flow_type"], "Feature")
        self.assertEqual(rec["id_letter"], "F")
        self.assertEqual(rec["next_available_id_stem"], "PTR-F047")
        self.assertIn("timestamp", rec)
        self.assertEqual(rec["existing_count"], 2)  # F033 + F046

    def test_prepare_check_audit_append_only(self) -> None:
        """多次跑 prepare-check · audit 是 append 不是覆盖。"""
        self._check("Feature")
        self._check("Bug")
        self._check("Micro")
        lines = self.audit_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 3)
        recs = [json.loads(l) for l in lines]
        # 顺序保留 · 字母不同
        self.assertEqual([r["id_letter"] for r in recs], ["F", "B", "F"])  # v8.220:Micro→F(M 退役)

    # ── v8.27 · reviewer_thinking_checklist(治本 F-Bv2-8 PMO 直接抄默认 case)──
    def test_v827_emit_includes_reviewer_thinking_checklist(self):
        """prepare-check emit 必含 reviewer_thinking_checklist 段 + hint。"""
        d = self._check("Feature")
        self.assertIn("reviewer_thinking_checklist", d)
        self.assertIn("reviewer_thinking_hint", d)

    def test_v827_checklist_has_4_core_questions(self):
        """checklist 4 个核心问题(用户拍板:不过载)。"""
        d = self._check("Feature")
        checklist = d["reviewer_thinking_checklist"]
        self.assertEqual(len(checklist), 4)
        # 每问含 question + 至少一个调整建议(if_yes / if_no)
        for i, q in enumerate(checklist):
            self.assertIn("question", q, f"Q{i+1} 缺 question 字段")
            self.assertTrue(q.get("if_yes") or q.get("if_no"),
                            f"Q{i+1} 必含 if_yes 或 if_no 调整建议")

    def test_v827_checklist_covers_core_dimensions(self):
        """4 问覆盖 产品方向 / UI / 跨 module / 数据模型重构 4 个维度。"""
        d = self._check("Feature")
        all_text = " ".join(
            q["question"] + (q.get("if_yes", "") or "") + (q.get("if_no", "") or "")
            for q in d["reviewer_thinking_checklist"]
        )
        self.assertIn("产品方向", all_text)  # v8.75:Q1 维度 ROADMAP → 产品方向
        self.assertIn("UI", all_text)
        self.assertIn("module", all_text)
        self.assertIn("数据模型重构", all_text)

    def test_v875_pl_not_roadmap_gated(self):
        """v8.75 治本:Q1 不再用『无 ROADMAP → 去 pl』· 默认保留 pl(产品方向视角)。

        根因:旧 Q1 把 PL 评审价值等同 ROADMAP 拆分 —— 但 ROADMAP 是规划层产物 ·
        执行层 Feature 几乎都『无 ROADMAP』→ 几乎所有 Feature 套路化删 pl(用户实证)。
        """
        d = self._check("Feature")
        q1 = d["reviewer_thinking_checklist"][0]
        q1_text = q1["question"] + (q1.get("if_yes", "") or "") + (q1.get("if_no", "") or "")
        # 默认保留 pl(产品方向 · 非 roadmap-gated)
        self.assertIn("保留 pl", q1_text)
        self.assertIn("产品方向", q1_text)
        # 旧的错误框架彻底删除(PL 评审价值低 = 系统性误删的根)
        self.assertNotIn("PL 评审价值低", q1_text)
        # 显式 debunk「无 ROADMAP」借口
        self.assertIn("ROADMAP", q1_text)
        # hint 也强调 pl 默认保留 + 无 ROADMAP 不是去 pl 理由
        hint = d["reviewer_thinking_hint"]
        self.assertIn("pl 默认保留", hint)

    def test_hint_defers_assembly_to_goal(self):
        """装配后移:hint 不再教 prepare 设 roster —— 4 问消费时点在 goal 调研后。

        原锁「不要直接抄默认」(F-Bv2-8 case):该关切在 prepare 不设 roster 后自然消解,
        「不抄默认」的义务随装配一起搬进 goal-stage § 链装配(case 实证仍在 hint cite)。
        """
        d = self._check("Feature")
        hint = d["reviewer_thinking_hint"]
        self.assertIn("消费时点在 goal 调研后", hint)
        self.assertIn("不设评审角色", hint)
        self.assertIn("F-Bv2-8", hint)

    # ── v8.44.4:output_style_hint(治本 case 2026-05-28 codex-cli markdown 表格失败)──

    def test_v8444_output_style_hint_emitted(self):
        """v8.44.4:prepare-check emit 必含 output_style_hint dict。"""
        d = self._check("Feature")
        self.assertIn("output_style_hint", d)
        hint = d["output_style_hint"]
        # 必含 host / style_id / table_format / list_format / emphasis / emoji_safe / rationale
        for key in ["host", "style_id", "description", "table_format",
                    "list_format", "emphasis", "emoji_safe", "rationale"]:
            self.assertIn(key, hint, f"output_style_hint 缺字段 {key!r}")

    def test_v8444_codex_cli_host_recommends_box_drawing(self):
        """v8.44.4:host=codex-cli → table_format=box_drawing(避免 raw markdown 失败)。"""
        from state import _build_output_style_hint  # type: ignore
        hint = _build_output_style_hint("codex-cli")
        self.assertEqual(hint["host"], "codex-cli")
        self.assertEqual(hint["style_id"], "box_drawing_or_plain")
        self.assertEqual(hint["table_format"], "box_drawing")
        self.assertEqual(hint["list_format"], "plain")
        self.assertEqual(hint["emphasis"], "plain")
        self.assertTrue(hint["emoji_safe"])

    def test_v8444_claude_code_host_recommends_markdown(self):
        """v8.44.4:host=claude-code → table_format=markdown(rich renderer 支持)。"""
        from state import _build_output_style_hint  # type: ignore
        hint = _build_output_style_hint("claude-code")
        self.assertEqual(hint["host"], "claude-code")
        self.assertEqual(hint["style_id"], "markdown_ok")
        self.assertEqual(hint["table_format"], "markdown")

    def test_v8444_unknown_host_defaults_to_box_drawing(self):
        """v8.44.4:host=unknown / None → 保守默认 box_drawing(最大兼容)。"""
        from state import _build_output_style_hint  # type: ignore
        for h in [None, "unknown", "weird-cli"]:
            hint = _build_output_style_hint(h)
            self.assertEqual(hint["table_format"], "box_drawing",
                             f"host={h!r} 应保守 box_drawing")
            self.assertEqual(hint["style_id"], "box_drawing_or_plain")

    def test_v8444_gemini_cli_host_box_drawing_too(self):
        """v8.44.4:host=gemini-cli → 保守同 codex-cli(未实测)。"""
        from state import _build_output_style_hint  # type: ignore
        hint = _build_output_style_hint("gemini-cli")
        self.assertEqual(hint["table_format"], "box_drawing")


class TestIdStrategyV879(unittest.TestCase):
    """v8.79:artifact ID 号段策略(默认 utc 时间戳 · opt-out sequential)+ 撞号硬校验。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-idstrat-"))
        self.root = self.tmp / "features"
        self.root.mkdir(parents=True)
        self.audit_path = self.tmp / "audit.jsonl"
        self._prev = {
            "TEAMWORK_PREPARE_AUDIT_PATH": os.environ.get("TEAMWORK_PREPARE_AUDIT_PATH"),
            "TEAMWORK_BYPASS_PREPARE_CHECK": os.environ.get("TEAMWORK_BYPASS_PREPARE_CHECK"),
        }
        os.environ["TEAMWORK_PREPARE_AUDIT_PATH"] = str(self.audit_path)
        os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = "1"  # init-feature audit 门禁解耦

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k, v in self._prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _write_config(self, strategy) -> None:
        cfg = self.tmp / ".teamwork_localconfig.json"
        if strategy is None:
            cfg.unlink(missing_ok=True)
        else:
            cfg.write_text(json.dumps({"id_strategy": strategy}), encoding="utf-8")

    def _prepare_check(self, prefix: str = "PTR", flow: str = "Feature") -> dict:
        judgment = json.dumps({
            "sections_reviewed": ["§2.1"],
            "matched_signals": [{"section": "§2.1", "signal": "t",
                                 "evidence": "id strategy fixture"}],
            "recommended_flow_type": flow,
            "ai_rationale": "id strategy test fixture",
        })
        return run(["prepare-check", "--features-root", str(self.root),
                    "--feature-id-prefix", prefix, "--flow-type", flow,
                    "--user-intent", "id strategy test",
                    "--admission-judgment", judgment])

    def _init(self, fid: str, *, force: bool = False, expect_exit: int = 0) -> dict:
        target = self.root / fid
        argv = ["init-feature", "--feature", str(target), "--feature-id", fid,
                "--flow-type", "Feature", "--merge-target", "staging",
                "--branch", "feat/x"]
        if force:
            argv.append("--force")
        return run(argv, expect_exit=expect_exit)

    # ── AC1:默认 = utc 秒级时间戳 ──
    def test_default_is_utc_timestamp(self) -> None:
        self._write_config(None)  # 无配置 → 默认策略
        d = self._prepare_check()
        self.assertEqual(d["id_strategy"], "utc-yymmddhhmmss")
        self.assertRegex(d["next_available_id_stem"], r"^PTR-F\d{12}$")

    def test_explicit_utc_config(self) -> None:
        self._write_config("utc-yymmddhhmmss")
        d = self._prepare_check(flow="Bug")
        self.assertEqual(d["id_strategy"], "utc-yymmddhhmmss")
        self.assertRegex(d["next_available_id_stem"], r"^PTR-B\d{12}$")

    # ── AC2:sequential opt-out 行为不变(max+1) ──
    def test_sequential_opt_out_max_plus_one(self) -> None:
        (self.root / "PTR-F003-x").mkdir()
        (self.root / "PTR-F007-y").mkdir()
        self._write_config("sequential")
        d = self._prepare_check()
        self.assertEqual(d["id_strategy"], "sequential")
        self.assertEqual(d["next_available_id_stem"], "PTR-F008")

    def test_invalid_strategy_falls_back_to_default(self) -> None:
        self._write_config("garbage-value")
        d = self._prepare_check()
        self.assertEqual(d["id_strategy"], "utc-yymmddhhmmss")  # 非法值 → 默认

    # ── AC4:撞号硬校验(init-feature) ──
    def test_init_feature_collision_fails(self) -> None:
        (self.root / "PTR-F045-existing").mkdir()
        d = self._init("PTR-F045-other", expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertEqual(d["collision"]["existing"], "PTR-F045-existing")
        self.assertIn("撞号", d["error"])
        self.assertFalse((self.root / "PTR-F045-other").exists())  # FAIL 前未建目录

    def test_init_feature_no_collision_distinct_number(self) -> None:
        (self.root / "PTR-F045-existing").mkdir()
        d = self._init("PTR-F046-fresh")  # 不同号 → 放行
        self.assertEqual(d["verdict"], "OK")

    def test_init_feature_collision_force_bypasses(self) -> None:
        (self.root / "PTR-F045-existing").mkdir()
        d = self._init("PTR-F045-other", force=True)  # --force 跳过撞号
        self.assertEqual(d["verdict"], "OK")

    # ── AC3:时间戳形态 ID 被 init-feature 接受 ──
    def test_init_feature_accepts_timestamp_id(self) -> None:
        fid = "PTR-F260601143012-Offer-Ranking"
        d = self._init(fid)
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["feature_id"], fid)


class TestPrepareAuditGate(unittest.TestCase):
    """v8.14:init-feature 物化校验 prepare-check audit · 治本 PTR-F054 case。

    AI 跳 prepare 直裸跑 init-feature → audit 缺失 → BLOCKED with hint。
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-gate-"))
        self.audit_path = self.tmp / "audit.jsonl"
        self.features_root = self.tmp / "features"
        self.features_root.mkdir(parents=True)
        # 重定向 audit + 不要继承 bypass(子进程要看到真实 gate)
        self._env_snapshot = {
            "TEAMWORK_PREPARE_AUDIT_PATH": os.environ.get("TEAMWORK_PREPARE_AUDIT_PATH"),
            "TEAMWORK_BYPASS_PREPARE_CHECK": os.environ.get("TEAMWORK_BYPASS_PREPARE_CHECK"),
        }
        os.environ["TEAMWORK_PREPARE_AUDIT_PATH"] = str(self.audit_path)
        os.environ.pop("TEAMWORK_BYPASS_PREPARE_CHECK", None)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k, v in self._env_snapshot.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _init_feature_args(self, feature_id: str = "PTR-F100-test") -> list[str]:
        target = self.tmp / "apps" / "partner" / "docs" / "features" / feature_id
        return [
            "init-feature",
            "--feature", str(target),
            "--feature-id", feature_id,
            "--flow-type", "Feature",
            "--merge-target", "staging",
            "--branch", f"feat/{feature_id.lower()}",
        ]

    def test_init_feature_blocks_without_audit(self) -> None:
        """无 audit 文件 · init-feature 直接 BLOCKED with hint。"""
        d = run(self._init_feature_args(), expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertEqual(d["action"], "init-feature")
        self.assertIn("prepare-check", d["error"])
        self.assertIn("prepare-check", d["hint"])
        self.assertEqual(d["audit_detail"]["verdict"], "FAIL")
        self.assertEqual(d["audit_detail"]["prefix"], "PTR")

    def test_init_feature_passes_after_prepare_check(self) -> None:
        """跑了 prepare-check → audit 写好 → init-feature 放行。"""
        # 1. 先跑 prepare-check 写 audit(v8.34 强制 admission_judgment)
        judgment = json.dumps({
            "sections_reviewed": ["§2.1", "§2.2"],
            "matched_signals": [{"section": "§2.1", "signal": "test",
                                 "evidence": "init-feature audit fixture"}],
            "recommended_flow_type": "Feature",
            "ai_rationale": "v8.34 mandatory admission_judgment fixture",
        })
        run(["prepare-check", "--features-root", str(self.features_root),
             "--feature-id-prefix", "PTR", "--flow-type", "Feature",
             "--user-intent", "test intent",
             "--admission-judgment", judgment])
        self.assertTrue(self.audit_path.exists())
        # 2. init-feature 应放行(没 routing/cwd 校验交叉干扰 · 因为 tmp 不在 git repo)
        d = run(self._init_feature_args())
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["feature_id"], "PTR-F100-test")

    def test_init_feature_bypass_env_skips_gate(self) -> None:
        """TEAMWORK_BYPASS_PREPARE_CHECK=1 → 跳门禁(debug / migration)。"""
        os.environ["TEAMWORK_BYPASS_PREPARE_CHECK"] = "1"
        d = run(self._init_feature_args())
        self.assertEqual(d["verdict"], "OK")

    def test_init_feature_blocks_on_expired_audit(self) -> None:
        """audit 超 60min 窗 · 视为缺失 · BLOCKED。"""
        # 手写一条过期 record(2h 前)
        from datetime import datetime, timedelta, timezone
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        rec = {"timestamp": old_ts, "feature_id_prefix": "PTR",
               "flow_type": "Feature", "id_letter": "F",
               "next_available_id_stem": "PTR-F100",
               "features_root": str(self.features_root), "existing_count": 0}
        self.audit_path.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        d = run(self._init_feature_args(), expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertEqual(d["audit_detail"]["verdict"], "FAIL")
        self.assertIn("60min", d["audit_detail"]["reason"])
        self.assertGreater(d["audit_detail"]["latest_match_age_sec"], 3600)

    def test_init_feature_blocks_on_prefix_mismatch(self) -> None:
        """audit 有 record · 但 prefix 不匹配 → BLOCKED。"""
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        rec = {"timestamp": ts, "feature_id_prefix": "OTHER",
               "flow_type": "Feature", "id_letter": "F",
               "next_available_id_stem": "OTHER-F001",
               "features_root": str(self.features_root), "existing_count": 0}
        self.audit_path.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        d = run(self._init_feature_args("PTR-F100-test"), expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("PTR", d["audit_detail"]["prefix"])
        self.assertIn("无匹配", d["audit_detail"]["reason"])

    def test_init_feature_uses_latest_match_when_multiple(self) -> None:
        """audit 有多条 PTR record · 用最新那条(倒序扫优先 · 即使早期有过期也 PASS)。"""
        from datetime import datetime, timedelta, timezone
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        new_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        lines = [
            json.dumps({"timestamp": old_ts, "feature_id_prefix": "PTR",
                        "flow_type": "Feature", "id_letter": "F",
                        "next_available_id_stem": "PTR-F099",
                        "features_root": str(self.features_root), "existing_count": 0}),
            json.dumps({"timestamp": new_ts, "feature_id_prefix": "PTR",
                        "flow_type": "Feature", "id_letter": "F",
                        "next_available_id_stem": "PTR-F100",
                        "features_root": str(self.features_root), "existing_count": 0}),
        ]
        self.audit_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        d = run(self._init_feature_args())
        self.assertEqual(d["verdict"], "OK")

    def test_init_feature_blocks_when_all_matches_expired(self) -> None:
        """所有匹配 prefix 的 record 都过期 → BLOCKED(倒序找到的最新匹配过期 = 全过期)。"""
        from datetime import datetime, timedelta, timezone
        ts1 = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        ts2 = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        lines = [
            json.dumps({"timestamp": ts1, "feature_id_prefix": "PTR",
                        "flow_type": "Feature", "id_letter": "F",
                        "next_available_id_stem": "PTR-F099",
                        "features_root": str(self.features_root), "existing_count": 0}),
            json.dumps({"timestamp": ts2, "feature_id_prefix": "PTR",
                        "flow_type": "Feature", "id_letter": "F",
                        "next_available_id_stem": "PTR-F100",
                        "features_root": str(self.features_root), "existing_count": 0}),
        ]
        self.audit_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        d = run(self._init_feature_args(), expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")

    def test_audit_helper_skip_on_unparseable_feature_id(self) -> None:
        """feature_id 抽不出 prefix → SKIP(不强阻 · 落到下游 routing/basename 校验)。"""
        from state import _check_prepare_audit  # type: ignore
        d = _check_prepare_audit("nonconforming-id")
        self.assertEqual(d["verdict"], "SKIP")


class TestAdmissionJudgment(unittest.TestCase):
    """v8.15:prepare-check --user-intent + --admission-judgment 校验(治本 F001 GCP gateway case)。

    设计:工具不扫 regex(伪枚举)· 强制 AI 必传 judgment JSON · 校验 schema + consistency。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-adm-"))
        self.root = self.tmp / "features"
        self.root.mkdir(parents=True)
        self.audit_path = self.tmp / "audit.jsonl"
        self._prev_audit = os.environ.get("TEAMWORK_PREPARE_AUDIT_PATH")
        os.environ["TEAMWORK_PREPARE_AUDIT_PATH"] = str(self.audit_path)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev_audit is None:
            os.environ.pop("TEAMWORK_PREPARE_AUDIT_PATH", None)
        else:
            os.environ["TEAMWORK_PREPARE_AUDIT_PATH"] = self._prev_audit

    def _base_args(self, *, user_intent=None, judgment=None, flow_type="Feature"):
        args = ["prepare-check",
                "--features-root", str(self.root),
                "--feature-id-prefix", "F"]
        if flow_type:
            args += ["--flow-type", flow_type]
        if user_intent is not None:
            args += ["--user-intent", user_intent]
        if judgment is not None:
            args += ["--admission-judgment",
                     json.dumps(judgment) if isinstance(judgment, dict) else judgment]
        return args

    def _good_judgment(self, recommended="Feature Planning"):
        return {
            "sections_reviewed": ["§2.1", "§2.2"],
            "matched_signals": [
                {"section": "§2.1", "signal": "方向级业务变更",
                 "evidence": "想做一个 GCP API gateway 服务"}
            ],
            "recommended_flow_type": recommended,
            "ai_rationale": "强信号 + 跨多 BL · 单 Feature 状态机承载不下",
        }

    # ── v8.34:两者都不传 = BLOCK(治本 SVC-CORE-M001 · 删 v8.15 SKIPPED 兼容口子)──

    def test_no_intent_no_judgment_blocked(self):
        """v8.34 治本:不传两参 → FAIL(治本 SVC-CORE-M001 case AI 跳过思考)。

        v8.15 留 SKIPPED 兼容口子让 AI 跳过 admission_judgment 写作 · v8.34 删除该口子 ·
        强制必传 · 调试场景走 TEAMWORK_BYPASS_PREPARE_CHECK=1 bypass。
        """
        d = run(self._base_args(), expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("--user-intent", d["error"])
        self.assertIn("--admission-judgment", d["error"])
        self.assertIn("v8.34", d["error"])
        # hint 必含 TEAMWORK_BYPASS_PREPARE_CHECK 引导(调试逃生)
        self.assertIn("TEAMWORK_BYPASS_PREPARE_CHECK", d["hint"])

    # ── 部分传 = BLOCK ──

    def test_intent_only_blocked(self):
        d = run(self._base_args(user_intent="想做一个服务"), expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("--admission-judgment", d["error"])

    def test_judgment_only_blocked(self):
        d = run(self._base_args(judgment=self._good_judgment()), expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("--user-intent", d["error"])

    # ── JSON schema 校验 ──

    def test_judgment_invalid_json_blocked(self):
        d = run(self._base_args(user_intent="x", judgment="not json {{{"),
                expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("不是合法 JSON", d["error"])

    def test_judgment_missing_required_field_blocked(self):
        j = self._good_judgment()
        del j["ai_rationale"]
        d = run(self._base_args(user_intent="x", judgment=j), expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("ai_rationale", d["error"])

    def test_judgment_illegal_recommended_flow_type_blocked(self):
        j = self._good_judgment(recommended="NotAFlow")
        d = run(self._base_args(user_intent="x", judgment=j), expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("recommended_flow_type", d["error"])

    def test_judgment_matched_signals_must_be_list(self):
        j = self._good_judgment()
        j["matched_signals"] = "not a list"
        d = run(self._base_args(user_intent="x", judgment=j), expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("matched_signals", d["error"])

    # ── consistency 校验 ──

    def test_consistency_ok_when_recommended_matches_flow_type(self):
        j = self._good_judgment(recommended="Feature")
        d = run(self._base_args(user_intent="x", judgment=j, flow_type="Feature"))
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["admission_consistency"], "OK")

    def test_consistency_mismatch_warns_not_blocked(self):
        """治本 F001 case 核心:judgment 推 Feature Planning · flow_type=Feature → WARN(不 BLOCK)。"""
        j = self._good_judgment(recommended="Feature Planning")
        d = run(self._base_args(user_intent="想做一个 GCP gateway 服务", judgment=j,
                                flow_type="Feature"))
        self.assertEqual(d["verdict"], "OK")  # 不 BLOCK
        self.assertEqual(d["admission_consistency"], "MISMATCH")
        self.assertIn("Feature Planning", d["admission_consistency_warning"])
        self.assertIn("不一致", d["admission_consistency_warning"])

    def test_audit_jsonl_records_admission_fields(self):
        """audit jsonl 必含 user_intent / admission_judgment / consistency / recommended_flow_type。"""
        j = self._good_judgment(recommended="Feature Planning")
        run(self._base_args(user_intent="想做一个服务", judgment=j, flow_type="Feature"))
        lines = self.audit_path.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[-1])
        self.assertEqual(rec["user_intent"], "想做一个服务")
        self.assertEqual(rec["consistency"], "MISMATCH")
        self.assertEqual(rec["recommended_flow_type"], "Feature Planning")
        self.assertEqual(rec["admission_judgment"]["recommended_flow_type"], "Feature Planning")

    # ── init-feature 加 MISMATCH WARN(不 BLOCK)──

    def test_init_feature_emits_admission_warning_on_mismatch(self):
        """audit 含 consistency=MISMATCH → init-feature emit admission_warning + state.concerns 留痕。"""
        # 1. prepare-check 写 MISMATCH audit(rec=Feature Planning · 但 init 用 Feature)
        j = self._good_judgment(recommended="Feature Planning")
        run(self._base_args(user_intent="想做一个服务", judgment=j, flow_type="Feature"))

        # 2. init-feature(prefix=F · flow_type=Feature · 与 judgment 推 Feature Planning 不一致)
        target = self.tmp / "apps" / "gcp" / "docs" / "features" / "F-F100-gateway"
        # Note:--feature-id 必含 F prefix(_check_prepare_audit 用 prefix 匹配)
        d = run([
            "init-feature",
            "--feature", str(target),
            "--feature-id", "F-F100-gateway",
            "--flow-type", "Feature",
            "--merge-target", "staging",
            "--branch", "feat/f-f100",
        ])
        self.assertEqual(d["verdict"], "OK")  # 不 BLOCK
        self.assertIn("admission_warning", d)
        self.assertIn("Feature Planning", d["admission_warning"])
        # state.json 的 concerns 也含 WARN
        state = json.loads((target / "state.json").read_text(encoding="utf-8"))
        self.assertTrue(any("admission MISMATCH" in c for c in state["concerns"]),
                        f"state.concerns 应含 admission WARN · 实际: {state['concerns']}")


class TestExternalReviewSubagentRecipe(unittest.TestCase):
    """v8.291:第三视角冷审 = 错开模型 subagent(唯一形态)· 本命令不 exec 子进程。

    退役的三个类(TestExternalReviewCommand 30 · TestHostAutoDetect 7 ·
    TestExternalReviewContentQuality 4)测的是跨厂商 CLI 机械:host→model 映射 / which <cli> /
    preflight 登录探测 / stdout 质量检查 / self-review-fallback 降级 —— 整套已随 v8.291 删除。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-extsub-"))
        for a in (["init", "-b", "main"], ["config", "user.email", "t@t.co"],
                  ["config", "user.name", "t"]):
            subprocess.run(["git", "-C", str(self.tmp), *a], capture_output=True)
        (self.tmp / "seed.txt").write_text("x", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.tmp), "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", str(self.tmp), "commit", "-m", "seed"], capture_output=True)
        self.feat = self.tmp / "docs" / "features" / "F1"
        self.feat.mkdir(parents=True)
        (self.feat / "state.json").write_text(json.dumps({
            "feature_id": "F1", "flow_type": "Feature", "current_stage": "review",
            "artifact_root": str(self.feat), "stage_contracts": {}, "completed_stages": [],
        }, ensure_ascii=False), encoding="utf-8")
        (self.feat / "REVIEW.md").write_text("# r", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_emits_subagent_recipe_not_exec(self):
        d = run(["external-review", "--feature", str(self.feat), "--stage", "review"])
        self.assertEqual(d["verdict"], "SUBAGENT_RECIPE")
        self.assertIn("prompt_doc", d)
        self.assertIn("model 参数必须 ≠ 会话主模型", d["next_action"])   # 错开是硬要求
        self.assertIn("review_via: subagent", d["next_action"])

    def test_prompt_doc_written_with_files_inlined(self):
        d = run(["external-review", "--feature", str(self.feat), "--stage", "review"])
        doc = Path(d["prompt_doc"])
        self.assertTrue(doc.is_file())
        self.assertGreater(len(doc.read_text(encoding="utf-8")), 100)

    def test_cross_vendor_flags_gone(self):
        """跨厂商 flag 已移除 —— 传了就是 argparse 错(exit 2)。"""
        for flag in ("--host", "--model", "--preflight", "--self-review-fallback"):
            run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", flag, "codex"], expect_exit=2)

    def test_verify_fixes_needs_prior(self):
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--verify-fixes"], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("找不到上一轮", d["error"])


class TestPMDecisionTolerance(unittest.TestCase):
    """pm_acceptance decision 容错读 contract 顶层旧位(治本 ADMIN-F013 case)。

    v7 cmd_pm_decision / 部分 migrate 漏迁 → decision 落 contract 顶层而非 evidence。
    v8 readers(_check_pm_approved_ship / _pm_acceptance_transition)容错读两位 ·
    已迁 Feature 无需重迁即恢复 ship 门禁。
    """

    def test_decision_at_evidence_passes(self):
        from _v8_stage_specs import _pm_decision_value, _check_pm_approved_ship
        pm_c = {"output_satisfied": True, "evidence": {"decision": "approved_and_ship"}}
        self.assertEqual(_pm_decision_value(pm_c), "approved_and_ship")
        self.assertTrue(_check_pm_approved_ship(
            {"stage_contracts": {"pm_acceptance": pm_c}}, None))

    def test_decision_at_contract_top_v7_legacy_passes(self):
        """治本 case · v7 老 Feature decision 在 contract 顶层 · 容错读必须通过。"""
        from _v8_stage_specs import _pm_decision_value, _check_pm_approved_ship
        pm_c = {"output_satisfied": True, "decision": "approved_and_ship"}
        self.assertEqual(_pm_decision_value(pm_c), "approved_and_ship")
        self.assertTrue(_check_pm_approved_ship(
            {"stage_contracts": {"pm_acceptance": pm_c}}, None))

    def test_evidence_wins_over_contract_top(self):
        from _v8_stage_specs import _pm_decision_value
        pm_c = {"evidence": {"decision": "approved_and_ship"},
                "decision": "rejected_with_feedback"}
        self.assertEqual(_pm_decision_value(pm_c), "approved_and_ship")

    def test_no_decision_anywhere(self):
        from _v8_stage_specs import _pm_decision_value, _check_pm_approved_ship
        self.assertIsNone(_pm_decision_value({"output_satisfied": True}))
        self.assertFalse(_check_pm_approved_ship(
            {"stage_contracts": {"pm_acceptance": {"output_satisfied": True}}}, None))

    def test_output_not_satisfied_blocks(self):
        from _v8_stage_specs import _check_pm_approved_ship
        pm_c = {"output_satisfied": False, "evidence": {"decision": "approved_and_ship"}}
        self.assertFalse(_check_pm_approved_ship(
            {"stage_contracts": {"pm_acceptance": pm_c}}, None))

    def test_transition_with_legacy_top_level(self):
        from _v8_stage_specs import _pm_acceptance_transition
        st = {"stage_contracts": {"pm_acceptance": {"decision": "approved_and_ship"}}}
        self.assertEqual(_pm_acceptance_transition(st), "ship")
        st2 = {"stage_contracts": {"pm_acceptance": {"decision": "approved_no_ship"}}}
        self.assertEqual(_pm_acceptance_transition(st2), "completed")


class TestPanoramaArtifactEvidence(unittest.TestCase):
    """UI_DESIGN_SPEC _evidence_panorama_artifact 按 panorama_medium 校验。
    v8.58 option B:same-stack 物化 = preview-project + preview.sh + package.json(用户拍板 ·
    supersede v8.56 静态 build)· static-html 维持 Feature 内 preview/*.html 校验。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-panorama-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _args(self):
        class _A: pass
        a = _A(); a.feature = str(self.tmp); return a

    def _write_ui(self, medium=None, panorama_path=None):
        lines = ["---", "pages:", "  - {id: page1, title: \"页面 1\"}"]
        if medium is not None:
            lines.append(f"panorama_medium: {medium}")
        if panorama_path is not None:
            lines.append(f"panorama_path: {panorama_path}")
        lines += ["---", "# UI"]
        (self.tmp / "UI.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _scaffold_preview_project(self, panorama_path="design",
                                  with_sh=True, with_pkg=True):
        proj = self.tmp / panorama_path / "preview-project"
        proj.mkdir(parents=True)
        if with_sh:
            (proj / "preview.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        if with_pkg:
            (proj / "package.json").write_text("{}", encoding="utf-8")
        return proj

    def test_v858_same_stack_no_panorama_path_fails(self):
        """v8.58:same-stack 无 panorama_path → FAIL。"""
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium="same-stack")
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertFalse(ok)
        self.assertIn("panorama_path", err)

    def test_v858_same_stack_with_preview_project_passes(self):
        """v8.58 option B:same-stack + preview-project + preview.sh + package.json → PASS。"""
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium="same-stack", panorama_path="design")
        self._scaffold_preview_project()
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertTrue(ok, err)

    def test_v858_same_stack_no_preview_project_fails(self):
        """v8.58:same-stack 声明 panorama_path 但无 preview-project → FAIL。"""
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium="same-stack", panorama_path="design")
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertFalse(ok)
        self.assertIn("preview-project", err)

    def test_v858_same_stack_missing_preview_sh_fails(self):
        """v8.58:preview-project 存在但缺 preview.sh → FAIL。"""
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium="same-stack", panorama_path="design")
        self._scaffold_preview_project(with_sh=False)
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertFalse(ok)
        self.assertIn("preview.sh", err)

    # ── v8.61:auto_commit 校验(治本 v8.58 物化漏洞:磁盘存在但没提交)──

    def _git_init_commit(self, *rel_or_abs_paths):
        """self.tmp 建 git 仓 + 提交指定路径 · 返 commit hash。"""
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

        def sh(*a):
            return subprocess.run(["git", "-C", str(self.tmp), *a],
                                  capture_output=True, text=True, env=env)
        sh("init", "-q")
        for p in rel_or_abs_paths:
            sh("add", str(p))
        sh("commit", "-q", "-m", "x")
        return sh("rev-parse", "HEAD").stdout.strip()

    def test_v861_same_stack_uncommitted_preview_project_fails(self):
        """v8.61:preview-project 在磁盘但未进 auto_commit → FAIL(治本 v8.58 物化漏洞)。"""
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium="same-stack", panorama_path="design")
        self._scaffold_preview_project()              # 建文件但不提交
        commit = self._git_init_commit("UI.md")        # 只提交 UI.md
        a = self._args(); a.auto_commit = commit
        ok, err = _evidence_panorama_artifact({}, a)
        self.assertFalse(ok)
        self.assertIn("未进 auto_commit", err)

    def test_v861_same_stack_committed_preview_project_passes(self):
        """v8.61:preview-project 已提交进 auto_commit → PASS。"""
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium="same-stack", panorama_path="design")
        proj = self._scaffold_preview_project()
        commit = self._git_init_commit(
            "UI.md", proj / "preview.sh", proj / "package.json")
        a = self._args(); a.auto_commit = commit
        ok, err = _evidence_panorama_artifact({}, a)
        self.assertTrue(ok, err)

    def test_v861_same_stack_no_auto_commit_skips_commit_check(self):
        """v8.61:不传 auto_commit → 仅磁盘校验(向后兼容 · None 不阻塞)。"""
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium="same-stack", panorama_path="design")
        self._scaffold_preview_project()
        ok, err = _evidence_panorama_artifact({}, self._args())  # _args 无 auto_commit
        self.assertTrue(ok, err)

    def test_static_html_no_preview_fails(self):
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium="static-html")
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertFalse(ok)
        self.assertIn("preview/*.html", err)

    def test_static_html_with_preview_passes(self):
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium="static-html")
        (self.tmp / "preview").mkdir()
        (self.tmp / "preview" / "page1.html").write_text("<html></html>", encoding="utf-8")
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertTrue(ok, err)

    def test_default_static_html_when_field_absent(self):
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium=None)
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertFalse(ok)
        self.assertIn("preview/*.html", err)

    def test_invalid_medium_fails(self):
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium="bogus")
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertFalse(ok)
        self.assertIn("非法", err)

    def test_no_ui_md_fails(self):
        from _v8_stage_specs import _evidence_panorama_artifact
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertFalse(ok)
        self.assertIn("UI.md", err)

    # ── v8.17:全景为唯一权威(pages_changed[] 优先)──

    def _write_ui_with_pages_changed(self, pages_changed_yaml: str,
                                     medium: str = "static-html") -> None:
        """写 UI.md 含 frontmatter pages_changed[] · 走 v8.17 新模式。"""
        lines = [
            "---",
            "pages:",
            "  - {id: offers, title: \"Offers\"}",
            f"panorama_medium: {medium}",
            "panorama_path: panorama-root",
            "pages_changed:",
            pages_changed_yaml,
            "---",
            "# UI",
        ]
        (self.tmp / "UI.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_v817_pages_changed_with_existing_file_passes(self):
        """v8.17:pages_changed[] 有 · panorama_file 存在 → PASS(全景为权威 · 不要求 Feature preview/)。"""
        from _v8_stage_specs import _evidence_panorama_artifact
        # 创建全景文件(用绝对路径避免 git toplevel 依赖)
        panorama_file = self.tmp / "panorama-root" / "preview" / "offers.html"
        panorama_file.parent.mkdir(parents=True)
        panorama_file.write_text("<html></html>", encoding="utf-8")
        # pages_changed[].panorama_file 用绝对路径
        self._write_ui_with_pages_changed(
            "  - {page_id: offers, panorama_file: " + str(panorama_file) +
            ", change_range: \"filter\"}"
        )
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertTrue(ok, err)
        # Feature 内无 preview/ 副本也 PASS(关键 · 全景为权威)
        self.assertFalse((self.tmp / "preview").exists())

    def test_v817_pages_changed_missing_file_fails(self):
        """v8.17:pages_changed[].panorama_file 不存在 → FAIL with missing list。"""
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui_with_pages_changed(
            "  - {page_id: offers, panorama_file: " + str(self.tmp) +
            "/nonexistent/offers.html, change_range: \"filter\"}"
        )
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertFalse(ok)
        self.assertIn("不存在", err)
        self.assertIn("offers", err)

    def test_v817_pages_changed_missing_page_id_fails(self):
        """v8.17:schema 缺 page_id → FAIL。"""
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui_with_pages_changed(
            "  - {panorama_file: /tmp/x.html}"  # 缺 page_id
        )
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertFalse(ok)
        self.assertIn("page_id", err)

    def test_v817_pages_changed_missing_panorama_file_fails(self):
        """v8.17:schema 缺 panorama_file → FAIL。"""
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui_with_pages_changed(
            "  - {page_id: offers}"  # 缺 panorama_file
        )
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertFalse(ok)
        self.assertIn("panorama_file", err)

    def test_v817_new_mode_overrides_old(self):
        """v8.17 新模式触发后 · 不再 fallback 老模式(即使 Feature 内有 preview/*.html)。

        证:即使 Feature 内有 preview/page1.html(老模式会 PASS)· 但新模式 panorama_file
        不存在时还是 FAIL · 不会被老路径绕过。
        """
        from _v8_stage_specs import _evidence_panorama_artifact
        # Feature 内有老 preview · 但 pages_changed[] 指的全景文件不存在
        (self.tmp / "preview").mkdir()
        (self.tmp / "preview" / "page1.html").write_text("<html></html>",
                                                          encoding="utf-8")
        self._write_ui_with_pages_changed(
            "  - {page_id: offers, panorama_file: /tmp/nonexistent/x.html}"
        )
        ok, err = _evidence_panorama_artifact({}, self._args())
        self.assertFalse(ok, "新模式优先 · 不该 fallback 到老 preview/")
        self.assertIn("panorama_file", err)


class TestPanoramaSyncStage(unittest.TestCase):
    """v8.336(用户拍板):panorama_sync stage 退役 —— 设计本就是改现有全景,
    「同步」是二次 touch;真价值(结构性 IA 变更判级/协调)并入 ui_design 出口规则 8。
    本类保留名字作迁移史 · 只锁退役终态(详 test_panorama_retire_v8336)。"""

    def test_stage_retired_from_registry(self):
        import sys as _s
        _s.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from _v8_stage_specs import STAGE_SPECS
        self.assertNotIn("panorama_sync", STAGE_SPECS)


class TestPlanningCheck(unittest.TestCase):
    """v8.46:planning-check · Feature Planning 物化入口(治本规划路径未物化漏洞)。

    用户洞察 2026-05-28:PRODUCT-OVERVIEW-INTEGRATION.md 纯靠 AI 自觉读 · Feature Planning
    不进状态机无兜底 · planning-check 物化 emit checklist + 必读规范 + 规划状态机。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-planning-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_v846_planning_check_no_product_overview(self):
        """无 product-overview/ → must_read 仍含 PRODUCT-OVERVIEW-INTEGRATION(v8.48 总必读)· 无 state_machine。"""
        d = run(["planning-check", "--project-root", str(self.tmp)])
        self.assertEqual(d["verdict"], "OK")
        self.assertFalse(d["product_overview_exists"])
        # v8.48:PRODUCT-OVERVIEW-INTEGRATION 总 must_read(无 po 时学冷启动初创 · 产品规划优先)
        self.assertEqual(d["must_read"],
                         ["PRODUCT-OVERVIEW-INTEGRATION.md", "docs/feature-planning.md"])
        self.assertNotIn("planning_state_machine", d)
        self.assertIn("无 product-overview", d["product_overview_hint"])
        # v8.48:产品规划优先(不再把上游当 optional 直接拆 ROADMAP)
        self.assertIn("产品规划优先", d["product_overview_hint"])
        self.assertIn("先建 product-overview", d["product_overview_hint"])

    def test_v846_planning_check_with_product_overview(self):
        """有 product-overview/ → must_read 含 PRODUCT-OVERVIEW-INTEGRATION + 规划状态机。"""
        (self.tmp / "product-overview").mkdir()
        d = run(["planning-check", "--project-root", str(self.tmp)])
        self.assertTrue(d["product_overview_exists"])
        self.assertIn("PRODUCT-OVERVIEW-INTEGRATION.md", d["must_read"])
        self.assertIn("planning_state_machine", d)
        sm = d["planning_state_machine"]
        self.assertIn("✅ 已确认", sm["states"])
        self.assertIn("已确认", sm["downstream_rule"])
        self.assertEqual(len(sm["required_tables"]), 2)

    def test_v846_planning_check_checklist_and_constraints(self):
        """checklist 6 条 + key_constraints 含「不进状态机」+「不出 feature 实现代码 R6」+ v8.184 worktree。"""
        d = run(["planning-check", "--project-root", str(self.tmp)])
        self.assertEqual(len(d["planning_checklist"]), 7)  # + 实际代码调研 · 全景UI初规 · v8.314 业务交付视角拆分(独立条目)
        constraints = " ".join(d["key_constraints"])
        self.assertIn("不进状态机", constraints)
        self.assertIn("不出 feature 实现代码", constraints)  # v8.184:精确化(全景 preview-project 是设计代码)
        self.assertIn("R6", constraints)
        # v8.184:feature-planning 进流程先建临时 worktree(隔离规划产物 · 同 feature 策略)
        self.assertIn("worktree_setup", d)
        self.assertIn("git worktree add", d["worktree_setup"])
        self.assertIn("worktree", constraints)
        self.assertIn("complexity_force_upgrade", d["entry_criteria"])
        # v8.49:planning_order 是权威链路 · 业务架构(愿景) → teamwork-space → WS → ROADMAP
        self.assertIn("planning_order", d)
        po = d["planning_order"]
        self.assertIn("WS", po)
        self.assertLess(po.index("业务架构"), po.index("teamwork-space"),
                        "业务架构(愿景) 必在 teamwork-space 之前")
        self.assertLess(po.index("teamwork-space"), po.index("ROADMAP"),
                        "teamwork-space 必在 ROADMAP 之前(WS 在中间)")

    def test_v8100_planning_check_panorama_before_ws(self):
        """v8.100:全景UI初步规划 checklist 项存在 · planning_order 里全景在 WS 之前。"""
        d = run(["planning-check", "--project-root", str(self.tmp)])
        items = " ".join(c["item"] for c in d["planning_checklist"])
        self.assertIn("全景UI初步规划", items)        # 新 checklist 项
        self.assertIn("全景初规", items)               # WS 项记状态
        self.assertIn("覆盖的全景页清单", items)        # WS 项记页清单
        self.assertIn("并行", items)                   # v8.104:WS 项给执行顺序与并行建议(波次)
        po = d["planning_order"]
        self.assertIn("全景UI初步规划", po)
        self.assertLess(po.index("全景UI初步规划"), po.index("WS"),
                        "全景UI初步规划 必在 WS 之前(拆 WS 前先出全景)")


class TestV8111BugFlowFixes(unittest.TestCase):
    """v8.111:Bug 流程 2 摩擦点修复(实证来自真实 Bug feature 跑流程)
    A. _evidence_reviewers_match 容许「角色-限定」写法(external-claude 满足 external)
    B. _test_brief 按 flow_type 分支(Bug 不列 verify-ac/AC 全覆盖 = 假信号)
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-v8111-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _args(self):
        class _A: pass
        a = _A(); a.feature = str(self.tmp); return a

    def _write_review(self, reviewers_inline):
        (self.tmp / "REVIEW.md").write_text(
            f"---\nreviewers: {reviewers_inline}\nverdict: APPROVE\n---\n# review\n",
            encoding="utf-8",
        )

    def _state_review(self):
        return {"current_stage": "review",
                "stage_review_roles": {"review": ["architect", "qa", "external"]}}

    # ── Fix A:reviewers roll-call 容许 `角色-限定` ──
    def test_v8111_role_qualified_external_claude_satisfies_external(self):
        """external-claude 满足 required external(保留模型 provenance · 不再被拒)。"""
        from _v8_stage_specs import _evidence_reviewers_match
        self._write_review("[architect, qa, external-claude]")
        ok, err = _evidence_reviewers_match("REVIEW.md")(self._state_review(), self._args())
        self.assertTrue(ok, err)

    def test_v8111_bare_external_still_satisfies(self):
        """裸 external 仍满足(向后兼容)。"""
        from _v8_stage_specs import _evidence_reviewers_match
        self._write_review("[architect, qa, external]")
        ok, err = _evidence_reviewers_match("REVIEW.md")(self._state_review(), self._args())
        self.assertTrue(ok, err)

    def test_v8111_missing_external_still_blocks(self):
        """完全缺 external 角色仍 BLOCK(放宽 ≠ 不校验)。"""
        from _v8_stage_specs import _evidence_reviewers_match
        self._write_review("[architect, qa]")
        ok, err = _evidence_reviewers_match("REVIEW.md")(self._state_review(), self._args())
        self.assertFalse(ok)
        self.assertIn("external", err)

    def test_v8111_unrelated_prefix_does_not_falsematch(self):
        """前缀匹配要 `角色-` 边界 · externalize 不算 external(避免乱匹配)。"""
        from _v8_stage_specs import _evidence_reviewers_match
        self._write_review("[architect, qa, externalize]")
        ok, _ = _evidence_reviewers_match("REVIEW.md")(self._state_review(), self._args())
        self.assertFalse(ok, "externalize 不应满足 external(需 `external-` 边界)")

    # ── Fix B:_test_brief 按 flow_type 分支 ──
    def test_v8111_test_brief_bug_no_verify_ac_lie(self):
        """Bug 流程 brief 不得把 verify-ac.py/AC 全覆盖列成完成判定(假信号)。"""
        from _v8_stage_specs import _test_brief
        brief = _test_brief({"flow_type": "Bug"})
        self.assertIn("回归", brief)
        self.assertIn("N/A", brief)                       # 明示 verify-ac 对 Bug N/A
        self.assertNotIn("verify-ac.py 通过", brief)       # 不作为完成判定
        self.assertNotIn("AC 全覆盖最终验证", brief)

    def test_v8111_test_brief_feature_keeps_verify_ac(self):
        """Feature 流程 brief 仍列 verify-ac.py 通过 + AC 全覆盖(不回归)。"""
        from _v8_stage_specs import _test_brief
        brief = _test_brief({"flow_type": "Feature"})
        self.assertIn("verify-ac.py 通过", brief)
        self.assertIn("AC 全覆盖", brief)


class TestExternalReviewPromptV8136(unittest.TestCase):
    """v8.136:claude -p 链路三修(治 case PTR-F260611065743):
    ① 固定名审计副本被下一轮当 prompt 优先读 → stale review(唯一命名根治 · 见路径测试)
    ② 模板整文件替换 → 占位符说明表里的 {file_list} 也被灌入完整 PRD(双嵌 · 提取 Prompt 主体根治)
    ③ 显式 --prompt-doc 无 staleness 防线(mtime 门禁根治)
    """

    def test_extract_prompt_body_excludes_template_docs(self):
        """提取后不含模板元说明/占位符表/对照表 · {file_list} 恰出现 1 次。"""
        from state import _extract_prompt_body  # type: ignore
        template = (SKILL / "claude-agents" / "reviewer.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(template.count("{file_list}"), 2)  # 前提:整文件确有多处(主体 + 说明表)
        body = _extract_prompt_body(template)
        self.assertNotIn("占位符说明", body)
        self.assertNotIn("codex-agents/reviewer.toml 的对照", body)
        self.assertEqual(body.count("{file_list}"), 1)  # 双嵌根治:替换点唯一

    def test_extract_prompt_body_fallback_without_marker(self):
        """无「Prompt 主体」标记的自定义模板 → 原样返回(兼容)。"""
        from state import _extract_prompt_body  # type: ignore
        custom = "You are a reviewer. {file_list}"
        self.assertEqual(_extract_prompt_body(custom), custom)



if __name__ == "__main__":
    unittest.main(verbosity=2)
