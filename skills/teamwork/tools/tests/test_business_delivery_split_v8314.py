"""v8.314:业务交付视角拆分 —— 治「跨子项目 → 顺手拆成多个 feature」。

用户:涉及跨多个子项目时容易拆多个 feature;应从业务交付视角拆,允许一个 feature 跨多个子项目。

判定:**规则早已存在**(「主判据=交付内聚 · feature 可跨子项目 · 子项目边界不是拆分理由」·
用户拍板过 · 在三处)—— 又一例「规则存在 ≠ 规则执行」。这次查的是**什么结构性推力在顶着规则**:

1. **prepare 路由单数假设**:「据改动代码所在的子项目目录定前缀」对跨子项目没有指引 ——
   「一个 feature 没法有两个前缀」的别扭感隐性推向拆开;
2. **判据到达质量差**:判据埋在 PLANNING_CHECKLIST 一个 500 字巨条目中段 + target 字段注释里;
3. **草案载体没逼出业务交付视角**:「边界理由」槽能用技术话术糊(「partner 侧改动独立」),
   没有槽逼 AI 写「这条单独上线后谁得到什么」—— 横切件恰恰写不出这个。

修法全部是结构不是措辞:路由补跨子项目指引(前缀取业务交付宿主)· 拆解讨论稿加「业务交付物」
必答槽 · checklist 判据拆成独立条目(一条一事)· WS 模板每-feature 节加交付物行。
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestPrepareRoutingCrossSubproject(unittest.TestCase):
    """路由单数假设是隐性拆分推力 —— 跨子项目必须有明确走法,别扭感才不会变成拆分。"""

    def setUp(self):
        self.t = _read("docs/prepare.md")

    def test_cross_subproject_stays_one_feature(self):
        self.assertIn("照样一个 feature", self.t)
        self.assertIn("业务交付宿主", self.t)
        self.assertIn("不是拆 feature 的理由", self.t)

    def test_names_the_hidden_pressure(self):
        """不点名「前缀别扭」这个推力,读者会觉得这条规则多余 —— 推力还在暗处起作用。"""
        self.assertIn("前缀选择的别扭不构成拆分压力", self.t)

    def test_cites_single_source(self):
        self.assertIn("交付内聚单源", self.t)


class TestDraftCarriesDeliverableSlot(unittest.TestCase):
    """拆解讨论稿的「业务交付物」必答槽 —— 载体的形状决定内容会不会出现(横切件写不出交付物)。"""

    def setUp(self):
        self.t = _read("docs/feature-planning.md")

    def test_slot_exists_with_criterion(self):
        # v8.316:术语统一为「大白话目标」(与 WS goal_plain 字段/总览表列同名 · 单名防漂)
        self.assertIn("大白话目标", self.t)
        self.assertIn("这条单独上线后,谁能干什么/得到什么", self.t)

    def test_slot_rejects_technical_pseudo_deliverables(self):
        """「后端接口就绪」这类技术黑话是横切件糊边界理由的惯用形态 —— 必须点名排除。"""
        self.assertIn("「后端接口就绪」「partner 侧改动」不算", self.t)

    def test_merge_back_consequence_stated(self):
        self.assertIn("写不出可感知目标 = 横切件,并回宿主", self.t)


class TestChecklistItemStandsAlone(unittest.TestCase):
    """判据从 500 字巨条目里拆成独立 checklist 条目 —— 一条一事才到达。"""

    def test_dedicated_item_exists_and_is_short(self):
        import state
        hits = [i for i in state.PLANNING_CHECKLIST if "大白话目标" in i["item"]]
        self.assertEqual(len(hits), 1, "跨子项目判据应有且只有一个独立条目")
        self.assertLess(len(hits[0]["item"]), 400,
                        "独立条目又长回巨条目 = 到达质量退化(一条一事)")
        self.assertIn("拆多个 feature", hits[0]["item"])
        self.assertIn("Step 5.7", hits[0]["spec"])

    def test_planning_check_emits_it(self):
        """checklist 经 planning-check emit 到动作点 —— 写在别处 ≠ 到达。"""
        src = _read("tools/state.py")
        self.assertIn('"planning_checklist": PLANNING_CHECKLIST', src)


class TestWorkstreamTemplateCarrier(unittest.TestCase):
    """WS 模板每-feature 节的交付物行 —— 长期载体(讨论稿是临时的 · WS 是落盘的)。"""

    def setUp(self):
        self.t = _read("templates/workstream.md")

    def test_per_feature_deliverable_line(self):
        self.assertIn("**大白话目标**：{同 frontmatter `goal_plain`", self.t)
        self.assertIn("写不出 = 不该独立成件", self.t)

    def test_existing_cohesion_rule_untouched(self):
        """新槽位是既有判据的载体化 · 不许动判据本体。"""
        self.assertIn("拆分按**交付内聚**(唯一主判据)", self.t)
        self.assertIn("不按子项目切", self.t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
