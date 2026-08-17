"""链装配卡固定三槽(用户纠偏)。

case(supersdk 实证):PRD 终确认导读的「链装配」实际输出 =「进 UI 设计、也进浏览器
验收 / 不改数据库 / 动到的面…」—— 只剩环节与影响面,**评审力度整维丢失**(几路、
谁审、为什么,一个字没有),流程阶段也没按链展示。

根因 = v8.302 老病:导读要求是形容词式(「环节取舍 + 下游评审面」),形容词糊得过。
治法:固定三槽 —— 流程阶段(全链标进/跳)· 评审力度(逐 stage 是否×几路×谁×理由 ·
零也显式)· 四轴证据。
"""
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))
GOAL = SKILL_ROOT / "stages" / "goal-stage.md"


class TestCardSlots(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = GOAL.read_text(encoding="utf-8")
        cls.beat2 = doc.split("固定三槽 · 缺槽即漏", 1)[1].split("装配判断表")[0]
        cls.doc = doc

    def test_stage_chain_slot_shows_full_chain(self):
        self.assertIn("**流程阶段**", self.beat2)
        self.assertIn("pm_acceptance → ship", self.beat2)      # 完整链形态
        self.assertIn("进/跳", self.beat2)

    def test_review_intensity_slot_four_questions(self):
        """用户预期逐项:是否需要评审 × 需要几个 × 谁 × 理由。"""
        self.assertIn("**评审力度**", self.beat2)
        self.assertIn("是否需要 × 几路 × 谁 × 理由", self.beat2)
        self.assertIn("为什么这个力度", self.beat2)

    def test_zero_review_must_be_explicit(self):
        """评审收到零也要显式 0 路 + 理由 —— 与「静默跳」区分。"""
        self.assertIn("0 路 + 理由", self.beat2)

    def test_evidence_slot_kept(self):
        self.assertIn("**四轴证据**", self.beat2)

    def test_why_names_the_degradation_case_and_tax_goal(self):
        """卡的存在理由 = 减税可见(评审减没减一眼可核)· 整卡 ≤6 行防槽位变新税。"""
        self.assertIn("评审力度整维丢失", self.doc)
        self.assertIn("减税可见", self.doc)
        self.assertIn("整卡 ≤6 行", self.doc)

    def test_digest_item_points_to_slots(self):
        seg = self.doc.split("余节 ≤2 行", 1)[1].split("\n", 1)[0]
        self.assertIn("固定三槽", seg)
        self.assertIn("是否×几路×谁×理由", seg)


class TestBriefCarrier(unittest.TestCase):

    def test_goal_brief_carries_slots(self):
        from _v8_stage_specs import GOAL_SPEC
        b = GOAL_SPEC.brief_template_fn({})
        self.assertIn("固定三槽缺一即漏", b)
        self.assertIn("是否需要×几路×谁×理由", b)
        self.assertIn("0 路+理由", b)


if __name__ == "__main__":
    unittest.main()
