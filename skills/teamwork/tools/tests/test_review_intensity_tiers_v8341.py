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

    def test_low_tier_is_users_direct_shape(self):
        """用户拍板句「直接开发 → 架构师 review 一下 → PM 盯 staging」= 低档 · v8.342 起有正式档位。

        史:本条初版把这个形态拼成「micro + 手工附加轻门」——「附加」是形容词式承诺,
        没有载体就不会发生。现在它是 preset=tiny,链和 roster 都由机器给。
        """
        self.assertIn("直接开发,完成后架构师 review 一下,PM 验收盯 staging", self.table)
        self.assertIn("**`tiny`", self.table)
        self.assertIn("external 单路", self.table)      # v8.346 年检:单路留高产的那一路
        self.assertIn("盯 staging 部署", self.table)

    def test_tiers_named_per_stage(self):
        """各档缺省逐 stage 点名 —— 让「减」有判据可引(不是形容词式「轻一点」)。"""
        self.assertIn("dev → review〔external 单路〕 → pm_acceptance → ship", self.table)   # tiny 链
        self.assertIn("冷审 0 路缺省", self.table)                                            # lite goal
        self.assertIn("不写 TECH", self.table)                                               # lite 环节

    def test_lite_keeps_prd_and_user_sovereignty(self):
        """降档不动用户主权:lite 仍有 PRD + 终确认停等(用户拍板「lite 也要有 PRD」)。"""
        self.assertIn("PRD 照要", self.table)
        self.assertIn("终确认停等照停", self.table)
        self.assertIn("test_refs", self.table)          # 无 TC 时 AC↔测试绑定的替代载体
        self.assertIn("引用真实存在", self.table)        # 只校验非空 = 门形同虚设

    def test_tiny_tier_available_in_prepare(self):
        """定档要在能定的时点可选:tiny 是 preset · prepare 就得给得出。"""
        prep = (SKILL_ROOT / "docs" / "prepare.md").read_text(encoding="utf-8")
        self.assertIn("preset=tiny", prep)
        self.assertIn("盯 staging 部署", prep)
        self.assertIn("继续讨论", prep)                 # v8.338:方向类停等第 2 项恒定

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
        """降档单路仍守模型错开(评审独立性不因降档丢 · v8.269 单路不变式)。"""
        self.assertIn("模型照错开", self.table)
        self.assertIn("降档不降独立性", self.table)


class TestBriefCarrier(unittest.TestCase):

    def test_goal_brief_carries_both_sides(self):
        from _v8_stage_specs import GOAL_SPEC
        b = GOAL_SPEC.brief_template_fn({})
        self.assertIn("加减两侧都判", b)
        self.assertIn("为什么不降", b)
        for tier in ("micro", "tiny", "lite", "full"):
            self.assertIn(tier, b, tier)
        # 装配卡是 lite 的**唯一**入口 —— brief 必须点出这层(定档零 re-init 的兑现处)
        self.assertIn("--needs-blueprint false", b)
        self.assertIn("模型照错开", b)


if __name__ == "__main__":
    unittest.main()
