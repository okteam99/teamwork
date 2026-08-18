"""ship1 后 CI pipeline 自动检查(用户拍板)。

push 记录成功即自动查一次 CI;await-merge 每轮轮询带 CI —— MR 未合并且 CI 红
→ 不再傻等合并,CI_FAILING 退出并接 MR 窗口期修复口(v8.339 闭环)。
await-merge docstring 的原始痛点「CI 红无人接」至此有了机器动作。
"""
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

from _v8_ship import CI_FIX_HINT, _parse_gh_checks  # noqa: E402


class TestParseGhChecks(unittest.TestCase):
    """纯解析单测(shell 层 best-effort · 不在此测)。"""

    def test_all_pass(self):
        r = _parse_gh_checks(0, "build\tpass\t1m\nlint\tpass\t10s\n")
        self.assertEqual(r["status"], "passing")

    def test_failing_collects_names(self):
        r = _parse_gh_checks(1, "build\tfail\t1m\nlint\tpass\t10s\ntest\tfail\t2m\n")
        self.assertEqual(r["status"], "failing")
        self.assertEqual(r["failing"], ["build", "test"])

    def test_pending_by_exit8(self):
        r = _parse_gh_checks(8, "build\tpending\t\n")
        self.assertEqual(r["status"], "pending")

    def test_no_checks(self):
        self.assertEqual(_parse_gh_checks(0, "")["status"], "none")

    def test_unknown_on_weird_nonzero(self):
        self.assertEqual(_parse_gh_checks(2, "garbage output")["status"], "unknown")


class TestWiring(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")

    def test_push_emit_carries_ci_status(self):
        self.assertIn('"ci_status": (_ci := _mr_ci_status(ship.get("mr_url")', self.src)
        self.assertIn('"ci_fix_hint": CI_FIX_HINT', self.src)

    def test_await_merge_polls_ci_and_exits_on_red(self):
        fn = self.src.split("def cmd_await_merge", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("ci = _mr_ci_status(mr_url)", fn)
        self.assertIn('"CI_FAILING"', fn)
        self.assertIn("CI_FIX_HINT", fn)
        # 红灯检查在 MERGED 判定之前(合并前就切修复口 · 不傻等)
        self.assertLess(fn.index('"CI_FAILING"'), fn.index('"MERGED"'))

    def test_fix_hint_closes_v8339_loop(self):
        self.assertIn("jump-to-stage --to dev", CI_FIX_HINT)
        self.assertIn("push", CI_FIX_HINT)
        self.assertIn("MR 窗口期修复", CI_FIX_HINT)


class TestSpecCarrier(unittest.TestCase):

    def test_ship_stage_section(self):
        t = (SKILL_ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        seg = t.split("MR 窗口期 CI 自动检查", 1)[1].split("## MR 窗口期修复")[0]
        self.assertIn("push 记录成功即自动查一次 CI", seg)
        self.assertIn("每轮轮询同时带 CI", seg)
        self.assertIn("不再傻等合并", seg)
        self.assertIn("CI 红无人接", seg)


if __name__ == "__main__":
    unittest.main()
