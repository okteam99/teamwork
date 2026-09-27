"""PRD 终确认:用户先拍能直接定的项 · 其余自动进逐项讨论(用户拍板)。

拍板:待决策点要求用户给出能直接拍板的决策项,剩下的自动进入讨论模式 —— 逐个过,
给问题背景、发生场景和建议方案,确认后进下一项;讨论结果影响其他项 → 改 PRD 后重新梳理讨论点。
"""
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]


class TestGoalItemDiscussion(unittest.TestCase):

    def setUp(self):
        t = (SKILL_ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")
        self.seg = t.split("**逐项讨论模式**", 1)[1].split("\n\n")[0]
        self.full = t

    def test_escalate_splits_direct_vs_discuss(self):
        self.assertIn("能直接拍板的项", self.full)
        self.assertIn("自动进逐项讨论模式", self.full)

    def test_one_item_at_a_time_with_background_and_recommendation(self):
        for kw in ("一次只过一项", "问题背景与发生场景", "建议方案", "用户确认该项后才进下一项"):
            self.assertIn(kw, self.seg)

    def test_cross_impact_revises_prd_then_regroups(self):
        self.assertIn("先改 PRD,再重新梳理讨论点", self.seg)
        self.assertIn("退回待讨论", self.seg)

    def test_converges_back_to_final_confirm(self):
        self.assertIn("重新 emit 终确认", self.seg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
