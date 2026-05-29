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

    def test_init_feature_bug_defaults_to_dev(self) -> None:
        target = self.tmp / "bug"
        d = run([
            "init-feature",
            "--feature", str(target),
            "--feature-id", "BUG-007-login",
            "--flow-type", "Bug",
            "--merge-target", "main",
            "--branch", "fix/login",
        ])
        self.assertEqual(d["current_stage"], "dev")

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
            "/opt/homebrew/opt/python@3.14/bin/python3.14",
            str(STATE_PY), "init-feature", "--feature", str(target),
            "--feature-id", "TEST-F903", "--flow-type", "Feature",
            "--merge-target", "main", "--branch", "feat/test-f903",
            "--host", "made-up-host",
        ], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("made-up-host", r.stderr)


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
        # concerns 含 recover audit
        state = json.loads(sf.read_text(encoding="utf-8"))
        warns = [c for c in state["concerns"] if c.get("severity") == "WARN"]
        self.assertTrue(any("recovered after manual edit" in c.get("message", "") for c in warns))


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

    def test_agile_shares_f_series(self) -> None:
        d = self._check("敏捷需求")
        self.assertEqual(d["id_letter"], "F")
        self.assertEqual(d["next_available_id_stem"], "PTR-F047")

    def test_micro_recommends_m_series(self) -> None:
        d = self._check("Micro")
        self.assertEqual(d["id_letter"], "M")
        self.assertEqual(d["next_available_id_stem"], "PTR-M002")

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
        self.assertEqual([r["id_letter"] for r in recs], ["F", "B", "M"])

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
        """4 问覆盖 ROADMAP / UI / 跨 module / 数据模型重构 4 个维度。"""
        d = self._check("Feature")
        all_text = " ".join(
            q["question"] + (q.get("if_yes", "") or "") + (q.get("if_no", "") or "")
            for q in d["reviewer_thinking_checklist"]
        )
        self.assertIn("ROADMAP", all_text)
        self.assertIn("UI", all_text)
        self.assertIn("module", all_text)
        self.assertIn("数据模型重构", all_text)

    def test_v827_hint_cite_f_bv2_8_case(self):
        """hint 提示 PMO 不直接抄默认 · cite F-Bv2-8 case 实证。"""
        d = self._check("Feature")
        hint = d["reviewer_thinking_hint"]
        self.assertIn("不要直接抄", hint)
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


class TestExternalReviewCommand(unittest.TestCase):
    """v8.20:state.py external-review · 异质模型评审一条命令调起(治本 SVC-CORE-F034)。

    覆盖:
    - host→model 自动映射(claude-code→codex / codex-cli→claude)
    - 显式 --model 同源 BLOCK(claude-code + claude 违 R3)
    - which <cli> 不在 BLOCK with hint(绝不 substitute)
    - stage 非法 BLOCK(只支持 goal/blueprint/review)
    - dry-run:输出 preview_command + 不实际调 CLI
    - commit / base fallback(state.json 取)
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ext-rev-"))
        self.feat = self.tmp / "feat"
        self.feat.mkdir(parents=True)
        (self.feat / "state.json").write_text(json.dumps({
            "feature_id": "TEST-F001",
            "flow_type": "Feature",
            "current_stage": "review",
            "merge_target": "main",
            "stage_contracts": {"dev": {"auto_commit": "abc123def456"}},
            "concerns": [],
            "completed_stages": ["dev"],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        self._prev_bypass = os.environ.get("TEAMWORK_BYPASS_CHECKSUM")
        os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev_bypass is None:
            os.environ.pop("TEAMWORK_BYPASS_CHECKSUM", None)
        else:
            os.environ["TEAMWORK_BYPASS_CHECKSUM"] = self._prev_bypass

    # ── host→model 自动映射 ──
    def test_host_claude_code_auto_maps_to_codex(self):
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code", "--dry-run"])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["model"], "codex")  # claude-code → codex 自动

    def test_host_codex_cli_auto_maps_to_claude(self):
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "codex-cli", "--dry-run"])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["model"], "claude")  # codex-cli → claude 自动

    # ── 同源 BLOCK(治本 case-AI 反模式) ──
    def test_explicit_model_same_source_blocked(self):
        """claude-code 主对话 + 显式 --model claude → BLOCK(违 R3)。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code", "--model", "claude",
                 "--dry-run"], expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("同源", d["error"])
        self.assertIn("R3", d["error"])

    def test_explicit_model_codex_with_codex_host_blocked(self):
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "codex-cli", "--model", "codex",
                 "--dry-run"], expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("同源", d["error"])

    # ── stage 校验 ──
    def test_stage_choices_enforced(self):
        """argparse choices 限定 goal/blueprint/review · 其他直接 argparse error。"""
        # ship 不在 choices · argparse exit 2
        r = subprocess.run(
            [sys.executable, str(STATE_PY), "external-review",
             "--feature", str(self.feat), "--stage", "ship",
             "--host", "claude-code", "--dry-run"],
            capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("invalid choice", (r.stderr + r.stdout).lower())

    # ── dry-run 输出 preview_command(v8.26 stage-specific + v8.29 default 不传 model) ──
    def test_dry_run_includes_preview_command(self):
        """review stage 用 codex review 子命令(v8.26 各司其职 · v8.29 默认不传 --config)。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code", "--dry-run"])
        self.assertTrue(d["dry_run"])
        self.assertIn("preview_command", d)
        # v8.26:review stage 改回 codex review(专业 diff review · 内置 prompt)
        self.assertIn("codex review", d["preview_command"])
        self.assertIn("--commit", d["preview_command"])
        self.assertIn("--title", d["preview_command"])
        # v8.29:默认不传 --config(ChatGPT 订阅兼容)· --codex-model 显式才传
        self.assertNotIn("--config", d["preview_command"])
        # 不带 [PROMPT](避免与 review 对象 flag 互斥)· 不带 --base(避免与 --commit 互斥)
        self.assertNotIn("--base", d["preview_command"])
        # codex_prompt 字段 None(review 模式无 PROMPT)
        self.assertIsNone(d["codex_prompt"])
        # 没真跑 · 不该有 model_version 字段
        self.assertNotIn("model_version", d)

    # ── v8.38:claude CLI 用 -p(用户约定 · case SVC-PLATFORM-F054 round 2)──

    def test_v838_claude_path_preview_uses_dash_p_not_dash_dash_print(self):
        """v8.38:codex-cli host → claude model 路径 preview_command 必含 'claude -p' 不含 '--print'。

        case 用户决策 2026-05-27:"外部调用 claude 的时候 要使用 -p"。
        防 _run_claude_review / preview_command 退化回 --print。
        """
        # codex-cli → claude 异质 · 走 _run_claude_review path
        # blueprint stage 是 claude 走的(review 是 codex review)· 用 blueprint
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "blueprint", "--host", "codex-cli", "--dry-run"])
        self.assertEqual(d["model"], "claude")
        self.assertIn("preview_command", d)
        # 必含 claude -p · 不含 --print
        self.assertIn("claude -p", d["preview_command"])
        self.assertNotIn("--print", d["preview_command"])

    def test_v838_run_claude_review_cmd_array_uses_dash_p(self):
        """v8.38:_run_claude_review subprocess cmd 数组必带 '-p'(不退回 '--print')。"""
        from unittest import mock
        from state import _run_claude_review  # type: ignore

        captured_cmd = []
        captured_kwargs = {}
        def fake_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            captured_kwargs.update(kwargs)
            class R:
                returncode = 0
                stdout = "ok"
                stderr = ""
            return R()

        with mock.patch("state.subprocess.run", side_effect=fake_run):
            rc, stdout, stderr = _run_claude_review("test prompt")
        self.assertEqual(rc, 0)
        # 必带 "-p" · 不含 "--print"
        self.assertIn("-p", captured_cmd)
        self.assertNotIn("--print", captured_cmd)

    # ── v8.43:claude -p prompt 从 stdin 改 argv(治本 case SVC-PLATFORM-F054 blueprint round 3)──

    def test_v843_run_claude_review_prompt_in_argv_not_stdin(self):
        """v8.43:prompt 必在 argv(而不是 stdin) · 治本 Claude CLI 2.1.153 stdin "Not logged in" bug。

        case 实证(用户跑):
          ✓ claude -p 'prompt' --model X  → OK
          ✗ printf 'prompt' | claude -p --model X  → "Not logged in"
        """
        from unittest import mock
        from state import _run_claude_review  # type: ignore

        captured_cmd = []
        captured_kwargs = {}
        def fake_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            captured_kwargs.update(kwargs)
            class R:
                returncode = 0
                stdout = "ok"
                stderr = ""
            return R()

        with mock.patch("state.subprocess.run", side_effect=fake_run):
            _run_claude_review("v843 test prompt body")

        # prompt 在 argv 里(治本 stdin "Not logged in")
        self.assertIn("v843 test prompt body", captured_cmd)
        # 不能再传 input=(stdin 模式)
        self.assertNotIn("input", captured_kwargs)
        # cmd 顺序:claude -p <prompt> --model X ...
        self.assertEqual(captured_cmd[0], "claude")
        self.assertEqual(captured_cmd[1], "-p")
        self.assertEqual(captured_cmd[2], "v843 test prompt body")
        self.assertIn("--model", captured_cmd)
        self.assertIn("--output-format", captured_cmd)

    # ── v8.55:external review 执行默认落日志(排查 codex/claude 卡住 / 跑不起来) ──

    def test_v855_log_external_run_writes_log(self):
        """v8.55:_log_external_run 落 ~/.teamwork/external-review-logs/<feat>/<label>-ts.log(含 rc/cmd/输出)。"""
        from unittest import mock
        from state import _log_external_run  # type: ignore
        with tempfile.TemporaryDirectory() as home:
            with mock.patch("state.Path.home", return_value=Path(home)):
                p = _log_external_run(Path("/x/PTR-F042-foo"), "codex-review",
                                      ["codex", "exec", "PROMPT"], "/x",
                                      124, "the-stdout", "the-stderr", 12.3)
            self.assertIsNotNone(p, "应返回日志路径")
            self.assertTrue(Path(p).exists())
            self.assertIn("PTR-F042-foo", p)  # feature-scoped 子目录
            body = Path(p).read_text(encoding="utf-8")
            self.assertIn("returncode: 124", body)
            self.assertIn("codex exec", body)
            self.assertIn("the-stdout", body)
            self.assertIn("the-stderr", body)

    def test_v855_log_external_run_none_feature_dir_no_crash(self):
        """v8.55:feature_dir=None → 不写 · 返 None(绝不阻塞 review)。"""
        from state import _log_external_run  # type: ignore
        self.assertIsNone(_log_external_run(None, "x", [], "", 0, "", "", 0.0))

    def test_v855_timeout_10min(self):
        """v8.55:EXTERNAL_REVIEW_TIMEOUT_SEC = 600(5min→10min)。"""
        from state import EXTERNAL_REVIEW_TIMEOUT_SEC  # type: ignore
        self.assertEqual(EXTERNAL_REVIEW_TIMEOUT_SEC, 600)

    # ── v8.43:reviewer.md 占位符真替换(治本 Bug B) ──

    def test_v843_gather_review_files_inlines_blueprint_targets(self):
        """v8.43:_gather_review_files_for_claude 把 stage=blueprint 的 TC.md/TECH.md 内容 inline。"""
        from state import _gather_review_files_for_claude  # type: ignore
        feat = Path(tempfile.mkdtemp(prefix="tw-v843-gather-"))
        try:
            (feat / "TC.md").write_text("# TC content\nfoo TC body", encoding="utf-8")
            (feat / "TECH.md").write_text("# TECH content\nbar TECH body", encoding="utf-8")
            block, meta = _gather_review_files_for_claude("blueprint", feat)
            # block 含两个文件内容 inline
            self.assertIn("### TC.md", block)
            self.assertIn("foo TC body", block)
            self.assertIn("### TECH.md", block)
            self.assertIn("bar TECH body", block)
            # meta:两个文件 exists=True · bytes 真
            names = {m["name"] for m in meta}
            self.assertEqual(names, {"TC.md", "TECH.md"})
            for m in meta:
                self.assertTrue(m["exists"])
                self.assertGreater(m["bytes"], 0)
        finally:
            shutil.rmtree(feat, ignore_errors=True)

    def test_v843_gather_review_files_truncates_oversized(self):
        """v8.43:超 60KB 单文件 truncate · meta 标 truncated=True。"""
        from state import (_gather_review_files_for_claude,  # type: ignore
                            EXTERNAL_REVIEW_INLINE_MAX_BYTES_PER_FILE)
        feat = Path(tempfile.mkdtemp(prefix="tw-v843-trunc-"))
        try:
            huge = "x" * (EXTERNAL_REVIEW_INLINE_MAX_BYTES_PER_FILE + 1000)
            (feat / "PRD.md").write_text(huge, encoding="utf-8")
            block, meta = _gather_review_files_for_claude("goal", feat)
            self.assertIn("truncated", block.lower())
            self.assertTrue(meta[0]["truncated"])
            # bytes 是原始大小(不是截断后)
            self.assertGreater(meta[0]["bytes"],
                                EXTERNAL_REVIEW_INLINE_MAX_BYTES_PER_FILE)
        finally:
            shutil.rmtree(feat, ignore_errors=True)

    def test_v843_gather_review_files_handles_missing(self):
        """v8.43:缺失文件 → block 标提示 + meta exists=False · 不抛异常。"""
        from state import _gather_review_files_for_claude  # type: ignore
        feat = Path(tempfile.mkdtemp(prefix="tw-v843-missing-"))
        try:
            # TC.md / TECH.md 都不存在
            block, meta = _gather_review_files_for_claude("blueprint", feat)
            self.assertIn("文件不存在", block)
            for m in meta:
                self.assertFalse(m["exists"])
                self.assertEqual(m["bytes"], 0)
        finally:
            shutil.rmtree(feat, ignore_errors=True)

    def test_v843_stage_review_files_maps_correctly(self):
        """v8.43:STAGE_REVIEW_FILES + STAGE_TO_REVIEW_TARGET 映射表正确。"""
        from state import STAGE_REVIEW_FILES, STAGE_TO_REVIEW_TARGET  # type: ignore
        self.assertEqual(STAGE_REVIEW_FILES["goal"], ["PRD.md"])
        self.assertEqual(STAGE_REVIEW_FILES["blueprint"], ["TC.md", "TECH.md"])
        self.assertEqual(STAGE_REVIEW_FILES["review"], [])  # review 走 diff 不 inline
        self.assertEqual(STAGE_TO_REVIEW_TARGET["goal"], "prd")
        self.assertEqual(STAGE_TO_REVIEW_TARGET["blueprint"], "blueprint")
        self.assertEqual(STAGE_TO_REVIEW_TARGET["review"], "code")

    # ── v8.44:doc-based prompt(治本 case round 4 长 prompt 卡 + 不可审计)──

    def test_v844_default_prompt_doc_path(self):
        """v8.44:_default_prompt_doc_path 返 <feature>/external-review-prompts/<stage>-<model>.md。"""
        from state import _default_prompt_doc_path  # type: ignore
        feat = Path("/tmp/foo")
        p = _default_prompt_doc_path(feat, "blueprint", "claude")
        self.assertEqual(p, feat / "external-review-prompts" / "blueprint-claude.md")
        p2 = _default_prompt_doc_path(feat, "goal", "codex")
        self.assertEqual(p2, feat / "external-review-prompts" / "goal-codex.md")

    def test_v844_scaffold_creates_doc_with_required_sections(self):
        """v8.44:scaffold-review-prompt 生成 doc 含必要 sections(checklist / TODO / Schema)。"""
        tmp = Path(tempfile.mkdtemp(prefix="tw-v844-scaffold-"))
        try:
            d = run(["scaffold-review-prompt", "--feature", str(tmp),
                     "--stage", "blueprint", "--model", "claude"])
            self.assertEqual(d["verdict"], "OK")
            self.assertEqual(d["stage"], "blueprint")
            self.assertEqual(d["model"], "claude")
            doc = Path(d["prompt_doc"])
            self.assertTrue(doc.exists())
            body = doc.read_text(encoding="utf-8")
            # 必含 checklist / TODO 标记 / output schema
            self.assertIn("Review Checklist", body)
            self.assertIn("C1 TC to AC mapping", body)  # blueprint checklist
            self.assertIn("TODO", body)
            self.assertIn("compact", body)  # "TODO · ... 填以下 Summary 段(compact · ...)"
            self.assertIn("Output Schema", body)
            self.assertIn("findings_summary", body)
            self.assertIn("perspective: external-claude", body)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_v844_scaffold_block_when_exists_without_force(self):
        """v8.44:scaffold 若 doc 已存在 + 无 --force → BLOCK(防覆盖编辑)。"""
        tmp = Path(tempfile.mkdtemp(prefix="tw-v844-exists-"))
        try:
            run(["scaffold-review-prompt", "--feature", str(tmp),
                 "--stage", "blueprint", "--model", "claude"])
            d = run(["scaffold-review-prompt", "--feature", str(tmp),
                     "--stage", "blueprint", "--model", "claude"], expect_exit=0)
            self.assertEqual(d["verdict"], "FAIL")
            self.assertIn("已存在", d["error"])
            self.assertIn("--force", d["hint"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_v844_scaffold_force_overwrites(self):
        """v8.44:--force 通过覆盖 · 用户编辑会丢但用户已显式承认。"""
        tmp = Path(tempfile.mkdtemp(prefix="tw-v844-force-"))
        try:
            run(["scaffold-review-prompt", "--feature", str(tmp),
                 "--stage", "goal", "--model", "claude"])
            doc = tmp / "external-review-prompts" / "goal-claude.md"
            # 手动改 doc · 模拟用户编辑
            doc.write_text("USER EDITED · should be overwritten with --force\n",
                            encoding="utf-8")
            d = run(["scaffold-review-prompt", "--feature", str(tmp),
                     "--stage", "goal", "--model", "claude", "--force"])
            self.assertEqual(d["verdict"], "OK")
            body = doc.read_text(encoding="utf-8")
            self.assertNotIn("USER EDITED", body)
            self.assertIn("Review Checklist", body)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_v844_scaffold_different_stages_have_different_checklists(self):
        """v8.44:scaffold goal/blueprint/review 生成不同 checklist。"""
        tmp = Path(tempfile.mkdtemp(prefix="tw-v844-stages-"))
        try:
            for stage in ["goal", "blueprint", "review"]:
                d = run(["scaffold-review-prompt", "--feature", str(tmp),
                         "--stage", stage, "--model", "claude"])
                self.assertEqual(d["verdict"], "OK")
                body = Path(d["prompt_doc"]).read_text(encoding="utf-8")
                if stage == "goal":
                    self.assertIn("PRD scope clarity", body)
                elif stage == "blueprint":
                    self.assertIn("TC to AC mapping", body)
                elif stage == "review":
                    self.assertIn("Code correctness", body)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ── commit fallback ──
    def test_commit_fallback_from_state_dev_auto_commit(self):
        """--commit 缺 → state.stage_contracts.dev.auto_commit 取。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code", "--dry-run"])
        self.assertEqual(d["commit"], "abc123def456")

    def test_explicit_commit_overrides_state(self):
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code",
                 "--commit", "deadbeef99", "--dry-run"])
        self.assertEqual(d["commit"], "deadbeef99")

    # ── base fallback ──
    def test_base_fallback_from_state_merge_target(self):
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code", "--dry-run"])
        self.assertEqual(d["base"], "main")

    # ── which BLOCK(模拟 codex 不在 · 用窄 PATH) ──
    def test_codex_cli_missing_blocked_with_hint(self):
        """which codex 失败 → BLOCK + hint 含 'change-review-roles' / '绝不 substitute'。"""
        # 用窄 PATH 模拟 codex 不在(/usr/bin:/bin · 通常没 codex)
        r = subprocess.run(
            [sys.executable, str(STATE_PY), "external-review",
             "--feature", str(self.feat), "--stage", "review",
             "--host", "claude-code"],  # 不加 --dry-run · 真跑到 which
            capture_output=True, text=True,
            env={**os.environ, "PATH": "/usr/bin:/bin",
                 "TEAMWORK_BYPASS_CHECKSUM": "1"})
        d = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        self.assertEqual(d.get("verdict"), "FAIL", f"应 FAIL · 实际 stdout={r.stdout}")
        self.assertIn("不在", d["error"])
        self.assertIn("substitute", d["hint"])  # "绝不 substitute"
        self.assertIn("change-review-roles", d["hint"])

    # ── 自动 frontmatter 文件命名 ──
    def test_output_file_path_uses_compliant_naming(self):
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code", "--dry-run"])
        # 文件名必含异质模型字面(v8.19 校验通过)· 自动 <stage>-<model>.md
        self.assertTrue(d["output_file"].endswith("review-codex.md"),
                        f"应 review-codex.md · 实际 {d['output_file']}")

    def test_output_file_for_blueprint_stage(self):
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "blueprint", "--host", "codex-cli", "--dry-run"])
        self.assertTrue(d["output_file"].endswith("blueprint-claude.md"))

    # ── v8.23:PROMPT 模式 + stage-specific prompt template ──
    def test_v823_goal_stage_uses_prd_review_prompt(self):
        """goal stage 用 PRD review prompt(不是 commit diff)。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "goal", "--host", "claude-code", "--dry-run"])
        self.assertEqual(d["verdict"], "OK")
        self.assertIn("PRD reviewer", d["codex_prompt"])
        self.assertIn("PRD.md", d["codex_prompt"])

    def test_v823_blueprint_stage_uses_blueprint_review_prompt(self):
        """blueprint stage 用 TC + TECH review prompt。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "blueprint", "--host", "claude-code", "--dry-run"])
        self.assertIn("blueprint reviewer", d["codex_prompt"])
        self.assertIn("TC.md and TECH.md", d["codex_prompt"])

    def test_v823_review_stage_uses_code_review_prompt(self):
        """review stage:v8.26 用 codex review 子命令 · 无 PROMPT(codex review 内置专业 prompt)。

        v8.23/v8.25 曾用 PROMPT 模式 · v8.26 用户洞察:review 用 codex review 子命令
        各司其职 · 不再传 PROMPT(避免与 --commit/--base/--uncommitted 互斥)。
        """
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code", "--dry-run"])
        # codex review 子命令 · 不带 PROMPT
        self.assertIn("codex review", d["preview_command"])
        self.assertIsNone(d["codex_prompt"])
        # commit SHA 通过 --commit flag 传(不在 PROMPT)
        self.assertIn("abc123def", d["preview_command"])

    def test_v823_codex_model_default_gpt_5_codex(self):
        """v8.29 治本 ChatGPT 订阅 case · 缺省 codex_model=None(不传 --config · 用账号默认模型)。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code", "--dry-run"])
        # v8.23 旧:default 虚构 'gpt-5-codex'(v8.30 实证不存在)· v8.29 改 None(ChatGPT 订阅兼容)
        self.assertIsNone(d["codex_model"])
        self.assertNotIn("--config", d["preview_command"])
        self.assertNotIn("model=", d["preview_command"])

    def test_v823_codex_model_explicit_override(self):
        """--codex-model gpt-5-pro 显式覆盖。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code",
                 "--codex-model", "gpt-5-pro", "--dry-run"])
        self.assertEqual(d["codex_model"], "gpt-5-pro")
        self.assertIn("model=gpt-5-pro", d["preview_command"])

    def test_v823_emit_includes_cwd_and_codex_model(self):
        """emit JSON 含 cwd(git root) + codex_model(透明 · v8.29 默认 null)。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code", "--dry-run"])
        self.assertIn("cwd", d)
        self.assertIn("codex_model", d)
        # v8.29:default None(ChatGPT 订阅兼容)· 字段仍 emit 但值 null
        self.assertIsNone(d["codex_model"])

    def test_v823_codex_model_not_in_claude_path(self):
        """claude 路径不传 codex_model · 字段为 null(避免 PMO 误以为 claude 走 codex 配置)。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "codex-cli",  # host=codex → model=claude
                 "--dry-run"])
        self.assertEqual(d["model"], "claude")
        self.assertIsNone(d["codex_model"])  # claude 路径 codex_model 为 None

    # ── v8.26:stage-specific dispatch · review→codex review · others→codex exec ──
    def test_v826_review_stage_uses_codex_review(self):
        """v8.26 用户洞察:review stage 用 codex review 子命令(专业 diff review)。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code", "--dry-run"])
        self.assertIn("codex review", d["preview_command"])
        self.assertNotIn("codex exec", d["preview_command"])
        # title 用 --title flag(codex review 支持)· 不进 PROMPT
        self.assertIn("--title", d["preview_command"])
        self.assertIsNone(d["codex_prompt"])  # review 模式无 PROMPT

    def test_v826_goal_blueprint_stage_uses_codex_exec(self):
        """v8.26:goal / blueprint stage 用 codex exec(文档 review · review 子命令是 diff-only)。"""
        for stage in ["goal", "blueprint"]:
            d = run(["external-review", "--feature", str(self.feat),
                     "--stage", stage, "--host", "claude-code", "--dry-run"])
            self.assertIn("codex exec", d["preview_command"],
                          f"{stage} stage 应用 codex exec · 实际:{d['preview_command']}")
            self.assertNotIn("codex review", d["preview_command"],
                             f"{stage} stage 不用 codex review(diff-only · 无法 review 文档)")
            self.assertIsNotNone(d["codex_prompt"])
            self.assertIn("[Review title:", d["codex_prompt"])  # title 进 PROMPT

    def test_v826_review_stage_no_base_flag_avoid_commit_base_互斥(self):
        """v8.26:review stage 不传 --base(只传 --commit · 避开 --commit/--base 互斥)。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code",
                 "--base", "main-custom", "--dry-run"])
        # --base flag 不在 cmd 里(只用 --commit)
        self.assertNotIn("--base", d["preview_command"])
        # 但 base 字段仍 emit(留 audit · base 用户传了 PMO 能看到)
        self.assertEqual(d["base"], "main-custom")

    # ── v8.29:codex_model 3 层 fallback(治本 ChatGPT 订阅死锁)──
    def test_v829_chatgpt_subscription_compat_default_no_model_flag(self):
        """治本核心:default codex_model=None · 不传 --config · ChatGPT 订阅可跑。"""
        for stage in ["goal", "blueprint", "review"]:
            d = run(["external-review", "--feature", str(self.feat),
                     "--stage", stage, "--host", "claude-code", "--dry-run"])
            self.assertIsNone(d["codex_model"], f"{stage} default codex_model 必 None")
            self.assertNotIn("--config", d["preview_command"],
                             f"{stage} 不应传 --config(ChatGPT 订阅会 400)")

    def test_v829_explicit_codex_model_overrides_default(self):
        """--codex-model gpt-5.3-codex 显式 · 用于 API 用户。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code",
                 "--codex-model", "gpt-5.3-codex", "--dry-run"])
        self.assertEqual(d["codex_model"], "gpt-5.3-codex")
        self.assertIn("--config 'model=gpt-5.3-codex'", d["preview_command"])

    def test_v829_config_external_review_codex_model_fallback(self):
        """.teamwork_localconfig.json external_review.codex_model fallback。"""
        # 写 config 到 git_root(feat 的 git toplevel)
        cfg = self.feat.parent / ".teamwork_localconfig.json"
        cfg.write_text(json.dumps({
            "external_review": {"codex_model": "gpt-5-pro"}
        }), encoding="utf-8")
        # 让 feat 处于 git repo
        subprocess.run(["git", "-C", str(self.feat.parent), "init", "-q"],
                       capture_output=True)
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code", "--dry-run"])
        self.assertEqual(d["codex_model"], "gpt-5-pro")
        self.assertIn("--config 'model=gpt-5-pro'", d["preview_command"])

    def test_v829_explicit_overrides_config(self):
        """--codex-model 显式 > config fallback。"""
        cfg = self.feat.parent / ".teamwork_localconfig.json"
        cfg.write_text(json.dumps({
            "external_review": {"codex_model": "gpt-5-pro"}
        }), encoding="utf-8")
        subprocess.run(["git", "-C", str(self.feat.parent), "init", "-q"],
                       capture_output=True)
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code",
                 "--codex-model", "gpt-5.3-codex", "--dry-run"])
        # 显式覆盖 config
        self.assertEqual(d["codex_model"], "gpt-5.3-codex")
        self.assertIn("model=gpt-5.3-codex", d["preview_command"])


class TestHostAutoDetect(unittest.TestCase):
    """v8.21 → v8.36:host 自动探测。

    v8.21:全局 ~/.teamwork/host_audit.json
    v8.36:主路径 per-feature state.json.host · audit 仅 fallback(deprecation WARN)
    治本 SVC-PLATFORM-F054 case · 全局 audit 跨 session 残留 · 异质映射出错。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="host-detect-"))
        self.feat = self.tmp / "feat"
        self.feat.mkdir(parents=True)
        # 默认 state.json 不含 host(测 v8.21 fallback 路径)
        (self.feat / "state.json").write_text(json.dumps({
            "feature_id": "TEST-F001",
            "flow_type": "Feature",
            "current_stage": "review",
            "merge_target": "main",
            "stage_contracts": {"dev": {"auto_commit": "abc123"}},
            "concerns": [],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        self.audit_path = self.tmp / "host_audit.json"
        self._prev_audit = os.environ.get("TEAMWORK_HOST_AUDIT_PATH")
        self._prev_bypass = os.environ.get("TEAMWORK_BYPASS_CHECKSUM")
        os.environ["TEAMWORK_HOST_AUDIT_PATH"] = str(self.audit_path)
        os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for var, prev in [("TEAMWORK_HOST_AUDIT_PATH", self._prev_audit),
                          ("TEAMWORK_BYPASS_CHECKSUM", self._prev_bypass)]:
            if prev is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = prev

    def _write_state_with_host(self, host: str) -> None:
        """v8.36 helper:写 state.json.host(模拟 init-feature --host 写入)。"""
        state = json.loads((self.feat / "state.json").read_text(encoding="utf-8"))
        state["host"] = host
        (self.feat / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2),
                                                 encoding="utf-8")

    # ── audit 不存在 + state.json 无 host + --host 缺 → BLOCK ──
    def test_no_audit_no_host_blocked_with_hint(self):
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--dry-run"], expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        # v8.36:错误信息改"无法确定主对话宿主"(覆盖 state.json/audit/env 三源)
        self.assertIn("无法确定", d["error"])
        self.assertIn("v8.36", d["hint"])

    # ── v8.36 主路径:state.json.host 存在 → host_source=state_json ──
    def test_v836_state_json_host_main_path(self):
        self._write_state_with_host("codex-cli")
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--dry-run"])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["host"], "codex-cli")
        self.assertEqual(d["host_source"], "state_json")
        self.assertEqual(d["model"], "claude")  # 异质映射
        # 主路径不应有 deprecation_warning
        self.assertNotIn("deprecation_warning", d)

    # ── v8.36 fallback:audit 存在 + state.json 无 host → audit_deprecated + WARN ──
    def test_v836_audit_fallback_with_deprecation_warning(self):
        self.audit_path.write_text(json.dumps({
            "host": "claude-code", "timestamp": "2026-05-25T00:00:00Z"
        }), encoding="utf-8")
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--dry-run"])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["host"], "claude-code")
        self.assertEqual(d["host_source"], "audit_deprecated")
        # v8.36:fallback 路径应携带 deprecation_warning
        self.assertIn("deprecation_warning", d)
        self.assertIn("v8.36", d["deprecation_warning"])
        self.assertIn("per-feature", d["deprecation_warning"])

    # ── v8.36 优先级:state.json.host 优先于 audit ──
    def test_v836_state_json_overrides_audit(self):
        self._write_state_with_host("codex-cli")
        self.audit_path.write_text(json.dumps({
            "host": "claude-code", "timestamp": "2026-05-25T00:00:00Z"
        }), encoding="utf-8")
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--dry-run"])
        # state.json 赢:host=codex-cli(audit 里是 claude-code 但被忽略)
        self.assertEqual(d["host"], "codex-cli")
        self.assertEqual(d["host_source"], "state_json")
        # 主路径 → 无 deprecation_warning
        self.assertNotIn("deprecation_warning", d)

    # ── 显式 --host 仍最高优先 ──
    def test_explicit_host_overrides_all(self):
        self._write_state_with_host("claude-code")  # state.json 说 claude-code
        self.audit_path.write_text(json.dumps({
            "host": "claude-code", "timestamp": "2026-05-25T00:00:00Z"
        }), encoding="utf-8")
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "codex-cli", "--dry-run"])
        self.assertEqual(d["host"], "codex-cli")  # 显式覆盖
        self.assertEqual(d["host_source"], "explicit")
        self.assertEqual(d["model"], "claude")

    # ── audit JSON 损坏 → fallback BLOCK(state.json 也无 host) ──
    def test_corrupt_audit_blocked(self):
        self.audit_path.write_text("not json {{{", encoding="utf-8")
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--dry-run"], expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("无法确定", d["error"])

    # ── audit host 非法值 → fallback BLOCK ──
    def test_audit_invalid_host_value_blocked(self):
        self.audit_path.write_text(json.dumps({
            "host": "nonexistent-host", "timestamp": "2026-05-25T00:00:00Z"
        }), encoding="utf-8")
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--dry-run"], expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("无法确定", d["error"])

    # ── _detect_host helper 单元测试 ──
    def test_detect_host_helper_returns_audit_source_v836(self):
        """v8.36:audit 命中时 source=audit_deprecated(原 audit)。"""
        from state import _detect_host  # type: ignore
        self.audit_path.write_text(json.dumps({"host": "codex-cli"}),
                                    encoding="utf-8")
        host, source = _detect_host()  # 不传 feature → 走 audit fallback
        self.assertEqual(host, "codex-cli")
        self.assertEqual(source, "audit_deprecated")

    def test_v836_detect_host_helper_state_json_priority(self):
        """v8.36:_detect_host(feature) 命中 state.json → source=state_json。"""
        from state import _detect_host  # type: ignore
        self._write_state_with_host("codex-cli")
        self.audit_path.write_text(json.dumps({"host": "claude-code"}),
                                    encoding="utf-8")
        host, source = _detect_host(str(self.feat))
        self.assertEqual(host, "codex-cli")
        self.assertEqual(source, "state_json")

    def test_detect_host_helper_returns_none_when_missing(self):
        from state import _detect_host  # type: ignore
        # audit 不存在 + 不传 feature
        host, source = _detect_host()
        self.assertIsNone(host)
        self.assertEqual(source, "none")


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
    """UI_DESIGN_SPEC _evidence_panorama_artifact 按 panorama_medium 校验
    (治本 PTR-F052:same-stack 跳过 preview/*.html 要求 · static-html 维持原校验)。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-panorama-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _args(self):
        class _A: pass
        a = _A(); a.feature = str(self.tmp); return a

    def _write_ui(self, medium=None):
        lines = ["---", "pages:", "  - {id: page1, title: \"页面 1\"}"]
        if medium is not None:
            lines.append(f"panorama_medium: {medium}")
        lines += ["---", "# UI"]
        (self.tmp / "UI.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_same_stack_no_preview_passes(self):
        from _v8_stage_specs import _evidence_panorama_artifact
        self._write_ui(medium="same-stack")
        ok, err = _evidence_panorama_artifact({}, self._args())
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
    """panorama_sync 条件 stage(从 ui_design step 4 隐式动作拆出)·
    `_ui_design_transition` + `_evidence_panorama_changed_decided` +
    `_evidence_sitemap_updated`。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-panosync-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _args(self, **kw):
        class _A: pass
        a = _A()
        a.feature = str(self.tmp)
        for k, v in kw.items():
            setattr(a, k, v)
        return a

    # ── _ui_design_transition 分支 ───────────────────────────────

    def test_transition_panorama_changed_true_goes_to_panorama_sync(self):
        from _v8_stage_specs import _ui_design_transition
        st = {"flow_type": "Feature",
              "execution_hints": {"panorama_changed": True}}
        self.assertEqual(_ui_design_transition(st), "panorama_sync")

    def test_transition_panorama_changed_false_feature_goes_to_blueprint(self):
        from _v8_stage_specs import _ui_design_transition
        st = {"flow_type": "Feature",
              "execution_hints": {"panorama_changed": False}}
        self.assertEqual(_ui_design_transition(st), "blueprint")

    def test_transition_panorama_changed_false_agile_goes_to_blueprint_lite(self):
        from _v8_stage_specs import _ui_design_transition
        st = {"flow_type": "敏捷需求",
              "execution_hints": {"panorama_changed": False}}
        self.assertEqual(_ui_design_transition(st), "blueprint_lite")

    def test_transition_no_hint_defaults_to_blueprint(self):
        """无 panorama_changed hint · 回退非-panorama-sync 路径(向后兼容)。"""
        from _v8_stage_specs import _ui_design_transition
        self.assertEqual(_ui_design_transition({"flow_type": "Feature"}), "blueprint")

    # ── _evidence_panorama_changed_decided ──────────────────────

    def test_panorama_changed_missing_arg_fails(self):
        from _v8_stage_specs import _evidence_panorama_changed_decided
        ok, err = _evidence_panorama_changed_decided({}, self._args())
        self.assertFalse(ok)
        self.assertIn("--panorama-changed", err)

    def test_panorama_changed_true_writes_hint(self):
        from _v8_stage_specs import _evidence_panorama_changed_decided
        st = {}
        ok, err = _evidence_panorama_changed_decided(st, self._args(panorama_changed="true"))
        self.assertTrue(ok, err)
        self.assertIs(st["execution_hints"]["panorama_changed"], True)

    def test_panorama_changed_false_writes_hint(self):
        from _v8_stage_specs import _evidence_panorama_changed_decided
        st = {}
        ok, err = _evidence_panorama_changed_decided(st, self._args(panorama_changed="false"))
        self.assertTrue(ok, err)
        self.assertIs(st["execution_hints"]["panorama_changed"], False)

    # ── _evidence_sitemap_updated ───────────────────────────────

    def test_sitemap_no_ui_md_fails(self):
        from _v8_stage_specs import _evidence_sitemap_updated
        ok, err = _evidence_sitemap_updated({}, self._args())
        self.assertFalse(ok)
        self.assertIn("UI.md", err)

    def test_sitemap_no_panorama_path_fails(self):
        from _v8_stage_specs import _evidence_sitemap_updated
        (self.tmp / "UI.md").write_text("# UI\n无 panorama_path 声明\n", encoding="utf-8")
        ok, err = _evidence_sitemap_updated({}, self._args())
        self.assertFalse(ok)
        self.assertIn("panorama_path", err)

    def test_sitemap_panorama_path_null_fails(self):
        from _v8_stage_specs import _evidence_sitemap_updated
        (self.tmp / "UI.md").write_text("> 🔴 panorama_path: null\n", encoding="utf-8")
        ok, err = _evidence_sitemap_updated({}, self._args())
        self.assertFalse(ok)
        self.assertIn("无效", err)

    def test_sitemap_fresh_mtime_passes(self):
        from _v8_stage_specs import _evidence_sitemap_updated
        pano = self.tmp / "pano"
        pano.mkdir()
        (pano / "sitemap.md").write_text("# sitemap\n", encoding="utf-8")
        (self.tmp / "UI.md").write_text(
            f"> 🔴 panorama_path: {pano}\n", encoding="utf-8")
        # started_at 早于 sitemap mtime 必通过(sitemap 刚写)
        st = {"stage_contracts": {"panorama_sync": {"started_at": "2020-01-01T00:00:00Z"}}}
        ok, err = _evidence_sitemap_updated(st, self._args())
        self.assertTrue(ok, err)

    def test_sitemap_old_mtime_fails(self):
        from _v8_stage_specs import _evidence_sitemap_updated
        import os as _os, time as _time
        pano = self.tmp / "pano"
        pano.mkdir()
        sm = pano / "sitemap.md"
        sm.write_text("# sitemap\n", encoding="utf-8")
        # 把 mtime 拨到很早(2020)
        _os.utime(str(sm), (1577836800, 1577836800))  # 2020-01-01
        (self.tmp / "UI.md").write_text(
            f"> 🔴 panorama_path: {pano}\n", encoding="utf-8")
        st = {"stage_contracts": {"panorama_sync": {"started_at": "2026-01-01T00:00:00Z"}}}
        ok, err = _evidence_sitemap_updated(st, self._args())
        self.assertFalse(ok)
        self.assertIn("早于", err)


class TestExternalReviewContentQuality(unittest.TestCase):
    """v8.36 治本 SVC-PLATFORM-F054 Bug 2:reviewer 只 echo template 不真 review case。

    用户决策:不语义判 reviewer 质量 · 只校验明显空/模板 · WARN 不 BLOCK · 决策权留用户。
    """

    def test_quality_check_empty_content_warns(self):
        from state import _check_external_review_quality  # type: ignore
        # 短于阈值 200 bytes → empty_content WARN
        warnings = _check_external_review_quality("short", stage="goal", model="claude")
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["type"], "empty_content")
        self.assertEqual(warnings[0]["severity"], "WARN")
        self.assertLess(warnings[0]["actual_bytes"], warnings[0]["threshold_bytes"])

    def test_quality_check_template_echo_warns(self):
        from state import _check_external_review_quality  # type: ignore
        # 含 "你给了我 reviewer prompt template" 字面命中 template_echo
        # 长度必须超过 200 字节 · 否则会先命中 empty_content
        body = (
            "你给了我 reviewer prompt template · 我并没有真的去 review PRD · "
            + ("仅复述模板内容。" * 30)
        )
        warnings = _check_external_review_quality(body, stage="goal", model="claude")
        types = {w["type"] for w in warnings}
        self.assertIn("template_echo", types)
        echo_w = next(w for w in warnings if w["type"] == "template_echo")
        self.assertEqual(echo_w["severity"], "WARN")
        self.assertGreater(len(echo_w["matched_signatures"]), 0)

    def test_quality_check_placeholder_unreplaced_caught(self):
        """v8.36:占位符未替换({{stage}} 等)也算 template echo 信号。"""
        from state import _check_external_review_quality  # type: ignore
        body = (
            "Review for stage {{stage}} commit {{commit}} feature {{feature_id}}\n"
            + ("This is a fake long review body to bypass empty check. " * 10)
        )
        warnings = _check_external_review_quality(body, stage="goal", model="claude")
        types = {w["type"] for w in warnings}
        self.assertIn("template_echo", types)

    def test_quality_check_normal_review_passes(self):
        """v8.36:正常长内容 + 无 echo signature → 无 warnings。"""
        from state import _check_external_review_quality  # type: ignore
        body = (
            "## Finding 1: missing edge case\n\n"
            "The PRD does not cover the case where targeting includes ALL but also exclude. "
            "This could lead to ambiguous behavior in admin offers list response. "
            "Recommend clarifying the priority rule explicitly in AC-2.\n\n"
            "## Finding 2: country code validation\n\n"
            "Token validation rule is implicit · suggest documenting ISO 3166-1 alpha-2 "
            "constraint and case-insensitive matching algorithm step by step.\n"
        )
        warnings = _check_external_review_quality(body, stage="goal", model="claude")
        self.assertEqual(warnings, [])


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
        """checklist 4 条 + key_constraints 含「不进状态机」+「不出代码 R6」。"""
        d = run(["planning-check", "--project-root", str(self.tmp)])
        self.assertEqual(len(d["planning_checklist"]), 5)  # v8.52:+ 实际代码调研项
        constraints = " ".join(d["key_constraints"])
        self.assertIn("不进状态机", constraints)
        self.assertIn("不出代码", constraints)
        self.assertIn("R6", constraints)
        self.assertIn("complexity_force_upgrade", d["entry_criteria"])
        # v8.49:planning_order 是权威链路 · 业务架构(愿景) → teamwork-space → WS → ROADMAP
        self.assertIn("planning_order", d)
        po = d["planning_order"]
        self.assertIn("WS", po)
        self.assertLess(po.index("业务架构"), po.index("teamwork-space"),
                        "业务架构(愿景) 必在 teamwork-space 之前")
        self.assertLess(po.index("teamwork-space"), po.index("ROADMAP"),
                        "teamwork-space 必在 ROADMAP 之前(WS 在中间)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
