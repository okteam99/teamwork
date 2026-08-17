"""方向类停等第 2 项恒为「继续讨论」(用户拍板)。

拍板:PRD 和 Feature Planning 给出 1/2/3 选项时,第 2 项永远都是继续讨论 ——
目的是方便 AI 和用户讨论清楚目标和方向(修订/落地是讨论收敛后的事,
不逼用户在「确认」与「给修改点」之间二选一)。
"""
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]


class TestGlobalRule(unittest.TestCase):

    def test_r5b_carries_standing_rule(self):
        t = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        seg = t.split("方向类停等第 2 项恒为「继续讨论」", 1)[1].split("\n\n")[0]
        self.assertIn("PRD 终确认", seg)
        self.assertIn("Feature Planning 全部 R5", seg)
        self.assertIn("把目标和方向聊清楚", seg)


class TestCarriers(unittest.TestCase):

    def test_goal_final_confirm(self):
        t = (SKILL_ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")
        self.assertIn("**2=继续讨论**〔恒定第 2 项", t)
        self.assertNotIn("2=按反馈修订重审", t)

    def test_planning_panorama_confirm(self):
        t = (SKILL_ROOT / "docs" / "feature-planning.md").read_text(encoding="utf-8")
        self.assertIn("2. 继续讨论 —— 对 design system", t)
        self.assertNotIn("2. 要改全景", t)

    def test_planning_split_discussion(self):
        t = (SKILL_ROOT / "docs" / "feature-planning.md").read_text(encoding="utf-8")
        self.assertIn("2. 继续讨论(合并 X+Y / 砍 Z / 改边界 / 方向疑虑", t)

    def test_planning_closeout_reordered(self):
        """收尾停等:2=继续讨论插位 · 一步到位组合顺延为 1/3 · 自动合并硬门同步改号。"""
        t = (SKILL_ROOT / "docs" / "feature-planning.md").read_text(encoding="utf-8")
        self.assertIn("2. 继续讨论 —— 对拆分结果 / 收尾方式 / BL 启动顺序", t)
        self.assertIn("3. 确认 · 合入收尾 + 启动首个 BL", t)
        self.assertIn("选项 1 / 3 = 一步到位", t)
        self.assertIn("自动合并硬门(选 1 / 3)", t)
        self.assertNotIn("自动合并硬门(选 1 / 2)", t)


if __name__ == "__main__":
    unittest.main()
