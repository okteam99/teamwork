"""v8.268:正常模式双路评审模型错开 —— 外审路 ≠ 主审路(如 fable5 会话 → 外审 opus)。

同模型双路 = 盲区相关(系统性偏差两路同瞎)· 错开 = 零 CLI 成本近异质
(上下文与权重双错开)。fast 单路不适用 · 跨厂商异质 opt-in 天然错开。
"""
import unittest
from pathlib import Path

import _v8_engine as E
import _v8_stage_specs as S


class TestModelStagger(unittest.TestCase):
    def test_dispatch_tier_reminder_carries_stagger(self):
        """stage-start 附带的派发提醒含错开规则(消费时点单源)。"""
        self.assertIn("错开", E.DISPATCH_TIER_REMINDER)
        self.assertIn("外审路 ≠ 主审路", E.DISPATCH_TIER_REMINDER)

    def test_normal_mode_briefs_carry_stagger(self):
        """goal/blueprint/review 三 brief 的多路派发行均带错开标记。

        v8.356:措辞从「两路模型错开」改为「逐路模型错开」—— 去角色后路数由 D4 定,
        不再固定两路;不变式本身没变(任何配置至少一路 ≠ 会话主模型)。
        """
        for name, brief in (("goal", S._goal_brief({})),
                            ("blueprint", S._blueprint_brief({})),
                            ("review", S._review_brief({}))):
            self.assertIn("逐路模型错开", brief, f"{name} brief 缺错开标记")

    def test_external_recipe_carries_stagger(self):
        """external-review subagent 配方指引含模型错开(措辞回归 · 源码级)。"""
        src = (Path(__file__).resolve().parent.parent / "state.py").read_text(encoding="utf-8")
        self.assertIn("模型错开", src)


class TestSingleLaneStagger(unittest.TestCase):
    """v8.269:单路评审(fast 合并单路 / roster 减到一路)与会话主模型错开。"""

    def test_reminder_carries_single_lane_rule(self):
        self.assertIn("该路 ≠ 会话主模型", E.DISPATCH_TIER_REMINDER)

    def test_single_lane_briefs_carry_stagger(self):
        """v8.355:提示改按**路数**判(原先只挂 fast_mode · 那是搭便车的通用条款)。"""
        one = {"stage_review_roles": {"goal": ["external"], "review": ["external"]}}
        self.assertIn("单路模型错开", S._goal_brief(one))
        self.assertIn("单路模型错开", S._review_brief({**one, "flow_type": "Bug"}))

    def test_single_lane_does_not_mean_shorter_checklist(self):
        """🔴 降档降路数 · 不降清单 —— 否则「单路」会被读成「少查几项」。"""
        gb = S._goal_brief({"stage_review_roles": {"goal": ["external"]}})
        self.assertIn("单路不减清单", gb)

    def test_two_lane_briefs_not_polluted_by_single_lane_line(self):
        self.assertNotIn("单路模型错开", S._goal_brief({"stage_review_roles": {"goal": ["pl", "external"]}}))
        self.assertNotIn("单路模型错开", S._goal_brief({}))
