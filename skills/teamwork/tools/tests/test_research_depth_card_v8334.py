"""起草前深入调研 + 评审深度判断卡(回显不阻塞)(用户拍板)。

case(supersdk Analytics-Dashboard 实证):起草前调研 = KNOWLEDGE/GLOSSARY +
读 1 个文件 + 2 条命令 → 直接写 174 行 PRD;派冷审用默认双路,零「这个 feature
需要什么评审深度」的判断输出 —— 旧 spec「按需选查」下这完全合规,判据缺失。

拍板:做深入调研 → 给出 PRD 评审深度判断(是否需要额外评审 · 需要谁 · 理由)
→ 回显给用户但不阻塞,自动进行评审调度。
"""
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))
GOAL = SKILL_ROOT / "stages" / "goal-stage.md"


class TestDeepResearch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = GOAL.read_text(encoding="utf-8")
        cls.seg = doc.split("起草前深入调研", 1)[1].split("**起草思考规范**")[0]

    def test_four_faces_mandatory_with_explicit_optout(self):
        """四面必过 · 不相关写「不涉」—— 静默跳被禁(按需选查退役)。"""
        for face in ("代码现状", "数据面", "既有相似实现", "上游与规范"):
            self.assertIn(face, self.seg, face)
        self.assertIn("不涉", self.seg)
        self.assertIn("不许静默跳", self.seg)

    def test_grep_not_single_file_read(self):
        """case 原型:只读一个文件不算调研。"""
        self.assertIn("grep 实测", self.seg)
        self.assertIn("只读一个文件不算调研", self.seg)

    def test_depth_criterion_decidable(self):
        """深度判据可判定:能答装配四轴 + 能写「最可能错在哪」· 答不出不许起草。"""
        self.assertIn("最可能错在哪", self.seg)
        self.assertIn("不许起草", self.seg)

    def test_feeds_both_cards(self):
        self.assertIn("装配证据", self.seg)
        self.assertIn("评审深度判断卡", self.seg)


class TestReviewDepthCard(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = GOAL.read_text(encoding="utf-8")
        cls.rule = doc.split("链装配(调研后", 1)[1].split("\n4. ")[0]

    def test_card_before_dispatch(self):
        self.assertIn("评审深度判断卡", self.rule)
        self.assertIn("派冷审**前**", self.rule)

    def test_card_carries_decision_and_reasons(self):
        """拍板三要素:是否额外评审 · 需要谁 · 判断理由。"""
        self.assertIn("是否需要额外评审", self.rule)
        self.assertIn("逐项判断理由", self.rule)
        self.assertIn("调研纪要", self.rule)

    def test_echo_without_blocking(self):
        """回显给用户但不阻塞 —— 与下游装配「默认执行」同律。"""
        self.assertIn("不问用户、但必回显", self.rule)
        self.assertIn("回显后直接派发不停等", self.rule)

    def test_v8329_two_beat_structure_intact(self):
        self.assertIn("AI 自定", self.rule)
        self.assertIn("默认按此执行", self.rule)          # 第②拍不受扰


class TestBriefCarrier(unittest.TestCase):

    def test_goal_brief_carries_research_and_card(self):
        from _v8_stage_specs import GOAL_SPEC
        b = GOAL_SPEC.brief_template_fn({})
        self.assertIn("深入调研", b)
        self.assertIn("最可能错在哪", b)
        self.assertIn("评审深度判断卡", b)
        self.assertIn("回显给用户但不阻塞", b)


if __name__ == "__main__":
    unittest.main()
