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
    """v7.3.10+P0-148：init-feature 子命令 + checksum guard。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="init_feat_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

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
    """v7.3.10+P0-148：state.json checksum 物化拦截直写。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="checksum_"))
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
    """v7.3.10+P0-148：recover 子命令重新认证 checksum + 写 concerns。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="recover_"))
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
    """prepare-check · flow_type → artifact ID 字母(F/B/M · 治本 Bug 错推 -F)。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-pc-"))
        self.root = self.tmp / "features"
        for name in ("PTR-F033-Alpha", "PTR-F046-Beta",
                     "PTR-B017-Gamma", "PTR-B018-Delta", "PTR-M001-Eps"):
            (self.root / name).mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
