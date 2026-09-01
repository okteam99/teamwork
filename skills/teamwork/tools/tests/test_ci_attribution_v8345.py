"""CI 失败归因:自己引入的直接修 · 别人的红不中断(用户拍板)。

拍板:「ship1 产出 MR 后监控合并的同时检查是否有 pipeline 失败,如果是自己引入的,直接修下」。

v8.340 已经做了「查 CI」,但停在**任何红都退出**去找修复口 —— 这会把 AI 支去修它
没弄坏的东西(base 本来就红的场景)。这正是 dev/test 早就解掉的「base 即红」坑:
那边用**差分基线**(test-baseline --diff)区分「新增回归」与「预存在失败」。
本版把同一个形状搬到 CI 上,并把归因后的**默认动作**定死:
  - 自己引入 → 中断等待,**直接修**(不问用户 —— 修自己弄坏的不是用户主权)
  - base 预存在 → **不中断**,回显一行继续等合并
"""
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

from _v8_ship import attribute_ci_failures, CI_FIX_HINT   # noqa: E402

SHIP_MD = SKILL_ROOT / "stages" / "ship-stage.md"


class TestAttribution(unittest.TestCase):
    """纯函数 · 四象限逐个锁。"""

    def test_green_base_means_ours(self):
        r = attribute_ci_failures(["build", "lint"], {"lint"}, True)
        self.assertEqual(r["self_introduced"], ["build"])
        self.assertEqual(r["pre_existing"], ["lint"])

    def test_base_also_red_is_not_ours(self):
        r = attribute_ci_failures(["build", "lint"], {"build", "lint"}, True)
        self.assertEqual(r["self_introduced"], [])
        self.assertEqual(r["pre_existing"], ["build", "lint"])

    def test_unknown_base_defaults_to_ours(self):
        """🔴 保守偏置:代价不对称 —— 把自己的红当别人的 = 把坏的合进去。
        与 test-baseline「不在基线里就算新增回归」同口径,不是「查不到就放行」。"""
        r = attribute_ci_failures(["build"], set(), False)
        self.assertEqual(r["self_introduced"], ["build"])
        self.assertIs(r["base_known"], False)

    def test_no_failures_is_empty_not_ours(self):
        r = attribute_ci_failures([], {"build"}, True)
        self.assertEqual(r["self_introduced"], [])
        self.assertEqual(r["pre_existing"], [])

    def test_blank_names_ignored(self):
        self.assertEqual(attribute_ci_failures(["", "  "], set(), True)["self_introduced"], [])


class TestDefaultActionIsFix(unittest.TestCase):
    """归因之后的**默认动作**要定死 —— 否则 AI 会把「要不要修」再抛给用户。"""

    def test_hint_says_fix_directly_without_asking(self):
        self.assertIn("直接修", CI_FIX_HINT)
        self.assertIn("不问用户是否要修", CI_FIX_HINT)
        self.assertIn("不是用户主权", CI_FIX_HINT)

    def test_hint_keeps_the_mr_window_loop(self):
        for k in ("jump-to-stage --to dev", "ship-phase --action push", "await-merge"):
            self.assertIn(k, CI_FIX_HINT, k)

    def test_escalation_boundary_kept(self):
        """修不动 / 根因在别处才升级 —— 不给「直接修」留无限重试的口子。"""
        self.assertIn("修不动", CI_FIX_HINT)
        self.assertIn("才升级用户", CI_FIX_HINT)


class TestWiring(unittest.TestCase):

    def test_await_merge_only_breaks_on_our_failures(self):
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        seg = src.split("def cmd_await_merge", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("_ci_with_attribution", seg)
        self.assertIn("if mine:", seg)
        self.assertIn("归因到本 feature", seg)
        self.assertIn("不中断等待", seg)          # 别人的红:继续等,不退出

    def test_base_branch_defaults_to_merge_target(self):
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        seg = src.split("def cmd_await_merge", 1)[1].split("\ndef ", 1)[0]
        self.assertIn('st.get("merge_target")', seg)

    def test_push_emit_carries_attribution(self):
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        self.assertIn('_ci := _ci_with_attribution(', src)
        # 只有归因到自己才给修复口 —— 别人的红不催修
        self.assertIn('if (_ci.get("attribution") or {}).get("self_introduced")', src)

    def test_attribution_only_queried_when_red(self):
        """绿/pending 不查 base —— 不为没发生的事付一次网络往返。"""
        src = (SKILL_ROOT / "tools" / "_v8_ship.py").read_text(encoding="utf-8")
        seg = src.split("def _ci_with_attribution", 1)[1].split("\ndef ", 1)[0]
        self.assertIn('if ci.get("status") != "failing":', seg)


class TestSpecCarrier(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = SHIP_MD.read_text(encoding="utf-8")
        cls.sec = doc.split("## MR 窗口期 CI 自动检查", 1)[1].split("\n## ", 1)[0]

    def test_section_states_both_branches(self):
        self.assertIn("归因到本 feature", self.sec)
        self.assertIn("直接修", self.sec)
        self.assertIn("base 预存在", self.sec)
        self.assertIn("不中断", self.sec)

    def test_section_names_the_reused_shape(self):
        """复用既有形状要点名 —— 否则下次又当新问题重新发明一遍。"""
        self.assertIn("base 即红", self.sec)
        self.assertIn("差分基线", self.sec)

    def test_conservative_bias_is_justified_not_asserted(self):
        self.assertIn("代价不对称", self.sec)
        self.assertIn("把坏的合进去", self.sec)

    def test_parallel_not_either_or(self):
        """用户原话:监控合并「的同时」检查 pipeline。"""
        self.assertIn("不是二选一", self.sec)


if __name__ == "__main__":
    unittest.main()
