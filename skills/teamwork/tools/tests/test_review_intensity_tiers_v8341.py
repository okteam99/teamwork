"""评审力度分级:装配判断表补减法侧(用户点名优化空间)。

case(jolichatbox 域名配置):v8.334-337 链条全部正常工作(深调研 / 判断卡 /
跳 ui_design·browser_e2e),但四轴全低的配置改动仍默认吃满六路评审
(goal 双路 + blueprint 2 路 + review 2 路)—— 用户当场问「这么简单的需求
为什么还要那么多 review」。

根因:装配判断表只有加法触发(跨模块→升异质 · 数据模型→加 dba),
没有减法判据 —— AI 有权减(0 路合法已立)但无判据可引,保守偏置默认全保。
"""
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))
GOAL = SKILL_ROOT / "stages" / "goal-stage.md"


class TestReductionSide(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = GOAL.read_text(encoding="utf-8")
        cls.table = doc.split("加减两侧都要判", 1)[1].split("(why:prepare")[0]

    def test_ultra_low_is_users_direct_shape(self):
        """超低档 = 用户拍板句:直接开发 → 架构师 review 一下 → PM 盯 staging。"""
        self.assertIn("直接开发,完成后架构师 review 一下,PM 验收盯 staging", self.table)
        self.assertIn("建议改走 `preset=micro`", self.table)
        self.assertIn("单路 architect diff 冷审", self.table)
        self.assertIn("盯 staging 部署", self.table)

    def test_low_tier_defaults_per_stage(self):
        """低档缺省逐 stage 点名 —— 让「减」有判据可引 · review 缺省 architect(用户形态)。"""
        self.assertIn("goal:[fast] 单路合并冷审", self.table)
        self.assertIn("blueprint:0 路(评审跳 · verify-ac 照跑)", self.table)
        self.assertIn("review:[architect] 单路", self.table)

    def test_micro_insist_legitimized_in_prepare(self):
        """消费 AI 的逃生路径(re-init micro)正名:坚持 micro 附轻门。"""
        prep = (SKILL_ROOT / "docs" / "prepare.md").read_text(encoding="utf-8")
        self.assertIn("行为性小改动亦合法", prep)
        self.assertIn("architect diff 冷审", prep)
        self.assertIn("盯 staging 部署", prep)

    def test_consistency_forcing(self):
        """一致性倒逼:四轴全低而 ≥2 路 → 必须写「为什么不降」(写不出就降)。"""
        self.assertIn("为什么不降", self.table)
        self.assertIn("写不出就降", self.table)

    def test_addition_side_kept(self):
        for k in ("升异质", "加 dba", "ui_design + browser_e2e 双跳"):
            self.assertIn(k, self.table, k)

    def test_case_evidence_in_why(self):
        self.assertIn("六路评审", self.table)
        self.assertIn("这么简单为什么那么多 review", self.table)

    def test_single_route_stagger_still_holds(self):
        """低档单路合并仍守模型错开(评审独立性不因降档丢)。"""
        self.assertIn("模型照错开", self.table)


class TestBriefCarrier(unittest.TestCase):

    def test_goal_brief_carries_both_sides(self):
        from _v8_stage_specs import GOAL_SPEC
        b = GOAL_SPEC.brief_template_fn({})
        self.assertIn("加减两侧都判", b)
        self.assertIn("为什么不降", b)
        self.assertIn("micro+轻门", b)


if __name__ == "__main__":
    unittest.main()
