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
        """goal/blueprint/review 三 brief 的两路派发行均带错开标记。"""
        for name, brief in (("goal", S._goal_brief({})),
                            ("blueprint", S._blueprint_brief({})),
                            ("review", S._review_brief({}))):
            self.assertIn("两路模型错开", brief, f"{name} brief 缺错开标记")

    def test_external_recipe_carries_stagger(self):
        """external-review subagent 配方指引含模型错开(措辞回归 · 源码级)。"""
        src = (Path(__file__).resolve().parent.parent / "state.py").read_text(encoding="utf-8")
        self.assertIn("模型错开", src)
