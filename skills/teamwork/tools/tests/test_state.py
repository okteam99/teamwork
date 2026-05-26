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
TEMPLATE_STATE = SKILL / "templates" / "feature-state.json"
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


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.fix = Path(tempfile.mkdtemp(prefix="state_test_"))
        shutil.copy2(TEMPLATE_STATE, self.fix / "state.json")

    def tearDown(self) -> None:
        shutil.rmtree(self.fix, ignore_errors=True)

    def feat(self) -> str:
        return str(self.fix)

    def push_to_stage(self, stage: str, allow_skip: bool = True) -> None:
        """模板初始 current_stage=dev · 推到目标 stage。"""
        for g in ("process", "output"):
            run(["satisfy-gate", "--feature", self.feat(), "--stage", "dev",
                 "--gate", g, "--auto-commit", "c1"])
        run(["complete-stage", "--feature", self.feat(), "--stage", "dev"])
        order = ["review", "test", "pm_acceptance", "ship", "completed"]
        for s in order:
            args = ["enter-stage", "--feature", self.feat(), "--stage", s]
            if allow_skip:
                args.append("--allow-skip")
            run(args)
            if s == stage:
                return


class TestP1ReadOnly(_Base):
    def test_snapshot_core(self) -> None:
        d = run(["snapshot", "--feature", self.feat()])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["snapshot"]["current_stage"], "dev")
        self.assertIn("ship.phase", d["snapshot"])

    def test_snapshot_full(self) -> None:
        d = run(["snapshot", "--feature", self.feat(), "--tier", "full"])
        self.assertIn("snapshot", d)
        self.assertEqual(d["snapshot"]["feature_id"], "AUTH-F042-email-login")

    def test_validate_clean_template(self) -> None:
        d = run(["validate", "--feature", self.feat()])
        self.assertEqual(d["verdict"], "PASS")

    def test_validate_inject_illegal(self) -> None:
        p = self.fix / "state.json"
        s = json.loads(p.read_text())
        s["current_stage"] = "hacking"
        s["ship"]["phase"] = "merged"
        s["ship"].pop("merge_commit_hash", None)
        p.write_text(json.dumps(s))
        d = run(["validate", "--feature", self.feat()], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertGreaterEqual(d["error_count"], 2)
        self.assertTrue(any("hacking" in e for e in d["errors"]))
        self.assertTrue(any("merge_commit_hash" in e for e in d["errors"]))

    def test_raw_read_field(self) -> None:
        d = run(["raw-read", "--feature", self.feat(), "--field", "current_stage"])
        self.assertEqual(d["value"], "dev")


class TestP2Transitions(_Base):
    def test_enter_stage_legal(self) -> None:
        for g in ("process", "output"):
            run(["satisfy-gate", "--feature", self.feat(), "--stage", "dev",
                 "--gate", g, "--auto-commit", "c1"])
        run(["complete-stage", "--feature", self.feat(), "--stage", "dev"])
        d = run(["enter-stage", "--feature", self.feat(), "--stage", "review"])
        self.assertEqual(d["verdict"], "PASS")
        # review 已进入 · legal_next_stages 是 review 之后的（test / dev 回炉）
        self.assertIn("test", d["updated_fields"]["legal_next_stages"])

    def test_enter_stage_illegal_rejected(self) -> None:
        d = run(["enter-stage", "--feature", self.feat(), "--stage", "ship"], expect_exit=3)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("dev", d["error"])

    def test_satisfy_gate_order_violation(self) -> None:
        # template dev gate.input=true / process=false
        d = run(["satisfy-gate", "--feature", self.feat(), "--stage", "dev",
                 "--gate", "output"], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("process_satisfied", d["error"])

    def test_complete_stage_missing_gates(self) -> None:
        d = run(["complete-stage", "--feature", self.feat(), "--stage", "dev"], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("missing_gates", d)

    def test_allow_skip_writes_concern(self) -> None:
        d = run(["enter-stage", "--feature", self.feat(), "--stage", "ship",
                 "--allow-skip"])
        self.assertEqual(d["verdict"], "PASS")
        c = run(["raw-read", "--feature", self.feat(), "--field", "concerns"])
        self.assertTrue(any("allow-skip" in x for x in c["value"]))

    # ─── v7.3.10+P0-154: external review artifact 物化拦截 ─────────────
    # 治本 SVC-PLATFORM-F043 跳 codex CR case · review_roles[] 含 external 时
    # 必须有 {artifact_root}/external-cross-review/*.md · 否则 satisfy-gate output FAIL

    def _inject_state(self, mutator) -> None:
        """改 state.json · 移除 checksum（fallback 到 legacy 模式）· 让 state.py 下次写自动重 stamp."""
        p = self.fix / "state.json"
        s = json.loads(p.read_text())
        s.pop("_state_checksum", None)
        mutator(s)
        p.write_text(json.dumps(s))

    def test_satisfy_gate_output_review_external_artifact_missing(self) -> None:
        """review_roles[] 含 external · 无 codex 产物 → FAIL（治本 P0-154）."""
        self.push_to_stage("review")

        def m(s: dict) -> None:
            s["review_substeps_config"] = {
                "review_roles": [{"role": "external", "execution": "subagent"}],
            }
            s["artifact_root"] = str(self.fix)
        self._inject_state(m)

        for g in ("input", "process"):
            run(["satisfy-gate", "--feature", self.feat(), "--stage", "review",
                 "--gate", g])
        d = run(["satisfy-gate", "--feature", self.feat(), "--stage", "review",
                 "--gate", "output", "--auto-commit", "c2"], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("external", d["error"])
        self.assertIn("P0-154", d["rule"])

    def test_satisfy_gate_output_review_external_artifact_present(self) -> None:
        """review_roles[] 含 external + 产物存在 → PASS（治本 P0-154）."""
        self.push_to_stage("review")

        def m(s: dict) -> None:
            s["review_substeps_config"] = {
                "review_roles": [{"role": "external"}]
            }
            s["artifact_root"] = str(self.fix)
        self._inject_state(m)

        ecr = self.fix / "external-cross-review"
        ecr.mkdir()
        (ecr / "review-external-codex.md").write_text(
            "---\nperspective: external-codex\n---\n# Codex Review\n",
            encoding="utf-8",
        )

        for g in ("input", "process"):
            run(["satisfy-gate", "--feature", self.feat(), "--stage", "review",
                 "--gate", g])
        d = run(["satisfy-gate", "--feature", self.feat(), "--stage", "review",
                 "--gate", "output", "--auto-commit", "c2"])
        self.assertEqual(d["verdict"], "PASS")

    def test_satisfy_gate_output_review_external_opt_out(self) -> None:
        """review_roles[] 不含 external · 无产物仍 PASS（用户已 opt-out · 治本 P0-154）."""
        self.push_to_stage("review")

        def m(s: dict) -> None:
            s["review_substeps_config"] = {
                "review_roles": [{"role": "architect"}, {"role": "qa"}]
            }
            s["artifact_root"] = str(self.fix)
        self._inject_state(m)

        for g in ("input", "process"):
            run(["satisfy-gate", "--feature", self.feat(), "--stage", "review",
                 "--gate", g])
        d = run(["satisfy-gate", "--feature", self.feat(), "--stage", "review",
                 "--gate", "output", "--auto-commit", "c2"])
        self.assertEqual(d["verdict"], "PASS")

    def test_satisfy_gate_output_dev_skips_external_check(self) -> None:
        """dev stage 不在 EXTERNAL_REVIEW_STAGES · 不触发 codex 校验（治本 P0-154 · 边界）."""
        run(["satisfy-gate", "--feature", self.feat(), "--stage", "dev",
             "--gate", "process"])
        d = run(["satisfy-gate", "--feature", self.feat(), "--stage", "dev",
                 "--gate", "output", "--auto-commit", "c1"])
        self.assertEqual(d["verdict"], "PASS")


class TestP3Ship(_Base):
    def test_ship_full_happy_path(self) -> None:
        self.push_to_stage("ship")
        run(["ship-sanitize", "--feature", self.feat()])
        run(["ship-push", "--feature", self.feat(),
             "--feature-head-commit", "abc1234",
             "--git-host", "github",
             "--mr-creation-method", "cli-gh",
             "--mr-url", "http://x/p/1"])
        run(["ship-confirm-merged", "--feature", self.feat(),
             "--merge-commit-hash", "abc1234",
             "--merge-detection-method", "branch-contains"])
        d = run(["ship-cleanup", "--feature", self.feat(), "--status", "cleaned"])
        self.assertEqual(d["verdict"], "PASS")
        self.assertEqual(d["updated_fields"]["ship.worktree_cleanup"], "cleaned")

    def test_ship_cleanup_blocked_before_merged(self) -> None:
        """治本 P0-124：cleanup --status cleaned 在 phase ≠ merged 时 BLOCKED。"""
        self.push_to_stage("ship")
        run(["ship-push", "--feature", self.feat(),
             "--feature-head-commit", "abc1234",
             "--git-host", "github",
             "--mr-creation-method", "cli-gh",
             "--mr-url", "http://x/p/1"])
        d = run(["ship-cleanup", "--feature", self.feat(), "--status", "cleaned"],
                expect_exit=1)
        self.assertEqual(d["verdict"], "BLOCKED")
        self.assertEqual(d["current_ship_phase"], "pushed")

    def test_ship_push_cli_gh_missing_mr_url(self) -> None:
        self.push_to_stage("ship")
        d = run(["ship-push", "--feature", self.feat(),
                 "--feature-head-commit", "abc",
                 "--git-host", "github",
                 "--mr-creation-method", "cli-gh",
                 "--mr-create-url", "http://fallback/x"], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("--mr-url", d["error"])

    def test_ship_confirm_merged_user_reported_logs_concern(self) -> None:
        self.push_to_stage("ship")
        run(["ship-push", "--feature", self.feat(),
             "--feature-head-commit", "abc",
             "--git-host", "github",
             "--mr-creation-method", "cli-gh",
             "--mr-url", "http://x"])
        d = run(["ship-confirm-merged", "--feature", self.feat(),
                 "--merge-commit-hash", "abc",
                 "--merge-detection-method", "user-reported"])
        self.assertTrue(any("user-reported" in w for w in d["warnings"]))
        c = run(["raw-read", "--feature", self.feat(), "--field", "concerns"])
        self.assertTrue(any("user-reported" in x for x in c["value"]))

    def test_ship_cleanup_n_a_unblocked(self) -> None:
        """worktree=off 路径 · status=n_a 不需 phase=merged。"""
        self.push_to_stage("ship")
        d = run(["ship-cleanup", "--feature", self.feat(), "--status", "n_a"])
        self.assertEqual(d["verdict"], "PASS")

    def test_ship_closed_abandon(self) -> None:
        self.push_to_stage("ship")
        run(["ship-push", "--feature", self.feat(),
             "--feature-head-commit", "abc",
             "--git-host", "github",
             "--mr-creation-method", "cli-gh",
             "--mr-url", "http://x"])
        d = run(["ship-closed", "--feature", self.feat(), "--abandon",
                 "--reason", "用户放弃"])
        self.assertEqual(d["updated_fields"]["ship.shipped"], "abandoned")

    # ─── v7.3.10+P0-156: linked-worktree 物化拦截 · 治本 ADMIN-F013 ────

    def test_ship_confirm_merged_rejects_linked_worktree(self) -> None:
        """ship-confirm-merged 在 linked worktree → FAIL early（治本 P0-156）."""
        d = run([
            "ship-confirm-merged", "--feature", self.feat(),
            "--merge-commit-hash", "abc",
            "--merge-detection-method", "branch-contains",
        ], expect_exit=2, env_extra={
            "TEAMWORK_FORCE_LINKED_WORKTREE": "/path/main/.git/worktrees/feat-x"
        })
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("linked worktree", d["error"])
        self.assertIn("P0-156", d["rule"])
        self.assertIn("ship-stage.md", d["cite"])

    def test_ship_cleanup_rejects_linked_worktree(self) -> None:
        """ship-cleanup 同型保护（治本 P0-156）."""
        d = run([
            "ship-cleanup", "--feature", self.feat(), "--status", "cleaned",
        ], expect_exit=2, env_extra={
            "TEAMWORK_FORCE_LINKED_WORKTREE": "/path/main/.git/worktrees/feat-x"
        })
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("linked worktree", d["error"])
        self.assertIn("P0-156", d["rule"])

    def test_ship_confirm_merged_bypass_main_worktree(self) -> None:
        """TEAMWORK_BYPASS_MAIN_WORKTREE=1 旁路 · 不强制（debug 场景）."""
        self.push_to_stage("ship")
        run(["ship-push", "--feature", self.feat(),
             "--feature-head-commit", "abc1234",
             "--git-host", "github",
             "--mr-creation-method", "cli-gh",
             "--mr-url", "http://x/p/1"])
        # 即使 force linked · BYPASS 旁路掉
        d = run(["ship-confirm-merged", "--feature", self.feat(),
                 "--merge-commit-hash", "abc1234",
                 "--merge-detection-method", "branch-contains"],
                env_extra={
                    "TEAMWORK_FORCE_LINKED_WORKTREE": "/fake/worktrees/x",
                    "TEAMWORK_BYPASS_MAIN_WORKTREE": "1",
                })
        self.assertEqual(d["verdict"], "PASS")


class TestP4General(_Base):
    def test_add_concern_dedup(self) -> None:
        run(["add-concern", "--feature", self.feat(),
             "--severity", "WARN", "--message", "测试 dedup"])
        d = run(["add-concern", "--feature", self.feat(),
                 "--severity", "WARN", "--message", "测试 dedup"])
        self.assertIn("skipped", d)

    def test_raw_write_requires_reason(self) -> None:
        r = subprocess.run(
            [sys.executable, str(STATE_PY), "raw-write",
             "--feature", self.feat(), "--set", "foo.bar=1"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(r.returncode, 0)

    def test_raw_write_logs_warn_concern(self) -> None:
        d = run(["raw-write", "--feature", self.feat(),
                 "--set", "foo.bar=42",
                 "--reason", "P3 未覆盖字段兜底"])
        self.assertEqual(d["verdict"], "OK")
        c = run(["raw-read", "--feature", self.feat(), "--field", "concerns"])
        self.assertTrue(any("raw-write" in x and "P3 未覆盖" in x for x in c["value"]))


class TestBugFrontmatter(_Base):
    def _setup_bug(self) -> Path:
        bug_dir = self.fix / "bugfix"
        bug_dir.mkdir()
        bug = bug_dir / "BUG-001-login-fail.md"
        bug.write_text(
            "---\n"
            "flow_type: bug\n"
            "phase: summarized\n"
            "shipped: null\n"
            "---\n\n"
            "# Bug\n",
            encoding="utf-8",
        )
        return bug

    def test_bug_set_phase_pushed(self) -> None:
        self._setup_bug()
        d = run(["bug-frontmatter", "--feature", self.feat(),
                 "--bug-id", "BUG-001",
                 "--set", "phase=pushed",
                 "--set", "feature_head_commit=abc1234",
                 "--validate-ship"])
        self.assertEqual(d["verdict"], "PASS")

    def test_bug_merged_missing_triple_blocked(self) -> None:
        """治本 P0-124 镜像：phase=merged 缺 hash + mr_merged_at 拒绝。"""
        self._setup_bug()
        d = run(["bug-frontmatter", "--feature", self.feat(),
                 "--bug-id", "BUG-001",
                 "--set", "phase=merged", "--validate-ship"], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertTrue(any("merge_commit_hash" in e for e in d["errors"]))


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


class TestMicroValidate(_Base):
    def test_valid_commit_in_main(self) -> None:
        # 用本仓 HEAD against origin/main · CI 环境可能不一致 · 仅校验脚本不崩
        # 真实 PASS / BLOCKED / FAIL 都接受
        cmd = [sys.executable, str(STATE_PY), "micro-validate",
               "--commit", "HEAD", "--merge-target", "main",
               "--cwd", str(SKILL.parent.parent)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1))
        d = json.loads(r.stdout or r.stderr)
        self.assertIn(d["verdict"], ("PASS", "BLOCKED", "FAIL"))


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
        return run(["prepare-check", "--features-root", str(self.root),
                    "--feature-id-prefix", "PTR", "--flow-type", flow_type])

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
        d = run(["prepare-check", "--features-root", str(self.root),
                 "--feature-id-prefix", "PTR"])
        self.assertEqual(d["id_letter"], "F")
        self.assertIn("--flow-type", d["hint"])

    def test_empty_series_starts_at_001(self) -> None:
        d = run(["prepare-check", "--features-root", str(self.root),
                 "--feature-id-prefix", "NEWPROJ", "--flow-type", "Bug"])
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
        # 1. 先跑 prepare-check 写 audit
        run(["prepare-check", "--features-root", str(self.features_root),
             "--feature-id-prefix", "PTR", "--flow-type", "Feature"])
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

    # ── 向后兼容:两者都不传 = SKIPPED ──

    def test_no_intent_no_judgment_skipped(self):
        d = run(self._base_args())
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d.get("admission_consistency"), "SKIPPED")

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
        # v8.23 旧:default 'gpt-5-codex' · v8.29 改 None(治本 ChatGPT 订阅死锁)
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
        """--codex-model gpt-5-codex 显式 · 用于 API 用户。"""
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "claude-code",
                 "--codex-model", "gpt-5-codex", "--dry-run"])
        self.assertEqual(d["codex_model"], "gpt-5-codex")
        self.assertIn("--config 'model=gpt-5-codex'", d["preview_command"])

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
                 "--codex-model", "gpt-5-codex", "--dry-run"])
        # 显式覆盖 config
        self.assertEqual(d["codex_model"], "gpt-5-codex")
        self.assertIn("model=gpt-5-codex", d["preview_command"])


class TestHostAutoDetect(unittest.TestCase):
    """v8.21:host 自动探测(治本 PMO 心智 · --host 改可选 · 缺省读 audit)。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="host-detect-"))
        self.feat = self.tmp / "feat"
        self.feat.mkdir(parents=True)
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

    # ── audit 不存在 + --host 缺 → BLOCK with hint ──
    def test_no_audit_no_host_blocked_with_hint(self):
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--dry-run"], expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("无法自动探测", d["error"])
        self.assertIn("bootstrap", d["hint"])
        self.assertIn("v8.21", d["hint"])

    # ── audit 存在 → host 自动 + host_source=audit ──
    def test_audit_exists_auto_host(self):
        self.audit_path.write_text(json.dumps({
            "host": "claude-code", "timestamp": "2026-05-25T00:00:00Z"
        }), encoding="utf-8")
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--dry-run"])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["host"], "claude-code")
        self.assertEqual(d["host_source"], "audit")
        self.assertEqual(d["model"], "codex")

    # ── audit + 显式 --host → 用显式(host_source=explicit) ──
    def test_explicit_host_overrides_audit(self):
        self.audit_path.write_text(json.dumps({
            "host": "claude-code", "timestamp": "2026-05-25T00:00:00Z"
        }), encoding="utf-8")
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--host", "codex-cli", "--dry-run"])
        self.assertEqual(d["host"], "codex-cli")  # 显式覆盖
        self.assertEqual(d["host_source"], "explicit")
        self.assertEqual(d["model"], "claude")

    # ── audit JSON 损坏 → fallback BLOCK ──
    def test_corrupt_audit_blocked(self):
        self.audit_path.write_text("not json {{{", encoding="utf-8")
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--dry-run"], expect_exit=0)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("无法自动探测", d["error"])

    # ── audit host 非法值 → fallback BLOCK ──
    def test_audit_invalid_host_value_blocked(self):
        self.audit_path.write_text(json.dumps({
            "host": "nonexistent-host", "timestamp": "2026-05-25T00:00:00Z"
        }), encoding="utf-8")
        d = run(["external-review", "--feature", str(self.feat),
                 "--stage", "review", "--dry-run"], expect_exit=0)
        # audit host 不在 EXTERNAL_HOST_TO_MODEL · _detect_host 返 None · 走 BLOCK
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("无法自动探测", d["error"])

    # ── _detect_host helper 单元测试 ──
    def test_detect_host_helper_returns_audit_source(self):
        from state import _detect_host  # type: ignore
        self.audit_path.write_text(json.dumps({"host": "codex-cli"}),
                                    encoding="utf-8")
        host, source = _detect_host()
        self.assertEqual(host, "codex-cli")
        self.assertEqual(source, "audit")

    def test_detect_host_helper_returns_none_when_missing(self):
        from state import _detect_host  # type: ignore
        # audit 不存在
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
