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


def run(args: list[str], expect_exit: int = 0) -> dict:
    """跑 state.py 子命令 · 返回 stdout JSON · 校验 exit code。"""
    cmd = [sys.executable, str(STATE_PY), *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
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


class TestP4General(_Base):
    def test_pm_decision_wrong_stage(self) -> None:
        d = run(["pm-decision", "--feature", self.feat(),
                 "--decision", "approved_and_ship"], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")

    def test_pm_decision_happy(self) -> None:
        self.push_to_stage("pm_acceptance")
        d = run(["pm-decision", "--feature", self.feat(),
                 "--decision", "approved_and_ship", "--note", "AC OK"])
        self.assertEqual(d["verdict"], "PASS")
        self.assertEqual(d["updated_fields"]["stage_contracts.pm_acceptance.decision"],
                         "approved_and_ship")

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
