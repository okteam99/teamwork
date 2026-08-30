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
        # v8.345:push emit 的 CI 查询升级为带归因(_ci_with_attribution)
        self.assertIn('"ci_status": (_ci := _ci_with_attribution(ship.get("mr_url")', self.src)
        self.assertIn('"ci_fix_hint": CI_FIX_HINT', self.src)

    def test_await_merge_polls_ci_and_exits_on_our_red(self):
        """v8.345 收窄:退出条件从「任何红」变成「**归因到本 feature** 的红」。

        本条初版锁的是「见红就退出去修」—— 那会把 AI 支去修 base 本来就红的东西
        (dev/test 的「base 即红」同一个坑)。归因层加上之后,退出仍然发生、
        但只对自己引入的失败;别人的红继续等合并。锁的实质(不傻等 CI 红)不变。"""
        fn = self.src.split("def cmd_await_merge", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("_ci_with_attribution", fn)
        self.assertIn('"CI_FAILING"', fn)
        self.assertIn("CI_FIX_HINT", fn)
        # 红灯检查仍在 MERGED 判定之前(合并前就切修复口 · 不傻等)
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
        # v8.345 改写本节:「不再傻等」的实质保留,但表述随归因分支变化 ——
        # 自己引入的才中断(直接修),别人的红继续等。
        self.assertIn("中断等待,直接修", seg)
        self.assertIn("不中断", seg)


if __name__ == "__main__":
    unittest.main()
