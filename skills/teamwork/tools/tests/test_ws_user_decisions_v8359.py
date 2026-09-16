"""v8.359 · WS 拆解明细:去「人维护」+ 用户决策事实入槽(用户拍板)。

用户(WS-48 财务链路截图):「这个人维护去掉,ws 这里 feature 补充一点可以详细一些,
**不能丢用户决策的事实**」。

两个问题都真:
  ① §拆出的 feature 标着「规划态 · **人维护**」,但这节恰恰是 feature-planning
     流程产出的 —— 标注会让 AI 以为不归它写,写薄或不写;
  ② 槽位只有 范围/依赖/**高层 AC**,**规划期用户拍的板没有落点** ——
     选了哪个方案、排除了什么、定了什么口径,全留在规划当时的对话里。

🔴 这是 v8.353「已确认意图入 PRD」的**上游断点**:v8.353 把 prepare 确认的意图搬进
PRD,但更早一层(WS 规划期的决策)仍然只活在对话里。换 session / 派 subagent 就没了,
下游 PM 只能凭「范围」一句去猜用户当初要什么 —— 而意图错了是唯一一类下游全部质量门
都拦不住的错。
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from state import _lint_ws_doc, _parse_ws_features_text  # noqa: E402


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _ws(features_block: str, extra: str = "") -> str:
    return (
        "<!-- TEAMWORK-MACHINE\n"
        "ws_id: WS-01\nstatus: 📝 草稿\nui_panorama: N-A\nui_panorama_confirmed: N-A\n"
        "承接执行线:\n  - Line 1\naffected_subprojects:\n  - X\n"
        f"features:\n{features_block}"
        "-->\n# WS-01\n"
        "<!-- WS-PROGRESS:START x -->\n(待)\n<!-- WS-PROGRESS:END -->\n"
        "<!-- WS-DAG:START x -->\n(待)\n<!-- WS-DAG:END -->\n" + extra
    )


class TestHumanMaintainedLabelRetired(unittest.TestCase):
    def test_template_dropped_the_label(self):
        t = _read("templates/workstream.md")
        self.assertNotIn("人维护", t)
        self.assertIn("## 拆出的 feature（拆解明细 · 规划态）", t)

    def test_lint_flags_the_stale_label(self):
        """存量 WS 抄着旧标题 —— lint 要能抓出来,否则它会一直传下去。"""
        doc = _ws("  - id: WS-01-S1\n    user_decisions: []\n",
                  extra="\n## 拆出的 feature（拆解明细 · 规划态 · 人维护）\n")
        missing = _lint_ws_doc(doc)
        self.assertTrue(any("人维护" in m for m in missing), missing)

    def test_planning_spec_says_it_is_flow_output(self):
        self.assertIn("不是「人维护」", _read("docs/feature-planning.md"))


class TestUserDecisionsHaveASlot(unittest.TestCase):
    """🔒 规划期拍的板要有机读落点 —— 只写正文 = 又一个「靠 AI 记得抄」的载体。"""

    def test_template_carries_both_ends(self):
        t = _read("templates/workstream.md")
        self.assertIn("user_decisions", t, "frontmatter 缺机读槽")
        self.assertIn("🔒 **用户已拍板的**", t, "正文缺人读槽")
        self.assertIn("原样搬不润色", t, "缺「不润色」要求 · 润色 = 二次解释")

    def test_parser_reads_the_field(self):
        feats = _parse_ws_features_text(_ws(
            '  - id: WS-01-S1\n    user_decisions: ["选了税务方案 A(不是 B)"]\n'))
        self.assertEqual(len(feats), 1)
        self.assertIn("税务方案 A", feats[0]["user_decisions"])

    def test_lint_flags_missing_slot(self):
        missing = _lint_ws_doc(_ws("  - id: WS-01-S1\n    bl: null\n"))
        self.assertTrue(any("user_decisions" in m for m in missing), missing)

    def test_empty_list_is_legal(self):
        """🔴 只查槽位在不在,不查非空 —— 强制非空会逼出**编造的决策**(同 v8.358 的判断)。"""
        missing = _lint_ws_doc(_ws("  - id: WS-01-S1\n    user_decisions: []\n"))
        self.assertFalse(any("user_decisions" in m for m in missing), missing)

    def test_lint_names_every_offending_feature(self):
        missing = _lint_ws_doc(_ws(
            "  - id: WS-01-S1\n    user_decisions: []\n  - id: WS-01-S2\n    bl: null\n"))
        hit = [m for m in missing if "user_decisions" in m]
        self.assertTrue(hit)
        self.assertIn("WS-01-S2", hit[0])
        self.assertNotIn("WS-01-S1", hit[0], "已填的件不该被点名")


class TestChainToPrdIsStated(unittest.TestCase):
    """载体到位还不够 —— 必须说清它往哪传,否则填了也没人用。"""

    def test_template_points_downstream(self):
        t = _read("templates/workstream.md")
        self.assertIn("--user-intent", t)
        self.assertIn("已确认意图", t)

    def test_planning_spec_states_the_cost_of_breaking_it(self):
        f = _read("docs/feature-planning.md")
        self.assertIn("换 session", f)
        self.assertIn("下游全部质量门都拦不住", f)


class TestBreakdownShouldBeDetailed(unittest.TestCase):
    """用户:「feature 补充一点可以详细一些」—— 原措辞「高层 AC」会诱导写薄。"""

    def test_template_no_longer_caps_at_high_level(self):
        t = _read("templates/workstream.md")
        self.assertNotIn("**核心 AC**（高层", t)
        self.assertIn("宁详勿略", t)
        self.assertIn("可写到具体字段/路由/状态值", t)

    def test_rationale_is_recorded(self):
        """why 要留住 —— 否则下次有人会以「PRD 里会写」为由把它压回去。"""
        self.assertIn("唯一", _read("templates/workstream.md"))


class TestSingleParserImplementation(unittest.TestCase):
    def test_text_parser_is_reused_not_duplicated(self):
        """ws-lint 拿到的是文本 —— 不该为此再写一份扫描器(双实现必漂)。"""
        src = _read("tools/state.py")
        self.assertIn("def _parse_ws_features_text", src)
        self.assertIn("return _parse_ws_features_text(text)", src)
        self.assertEqual(src.count("def _parse_ws_features"), 2)  # Path 版 + text 版


if __name__ == "__main__":
    unittest.main()
