"""v8.302:任何抛给用户的决策项都必带「💡 建议 + 理由」—— 结构上承载它,不只写在红线里。

实证(SVC-CORE-F260728):AI 把 D-4~D-7 四条待决策项**光秃秃列出**,用户被迫追问
「这四条你的建议和理由是什么」。

🔴 根因是**结构性**的,不是 AI 偷懒:
  - `SKILL.md` R5 三选项格式**早就强制**「💡 推荐 + 理由」,红线甚至写着「缺任一 = 把判断甩回用户」;
  - **但 PRD §待决策项的表列是 `| ID | 问题 | 选项 | 决策 |`** —— 没有承载建议与理由的位置。
  AI 照表填,填出来必然是裸选项。**载体的形状决定内容会不会出现**
  (与 v8.297/298 的档位错配同类)。

修法两侧都要:表加列(结构承载)+ 红线从「三选项格式」扩到「任何决策项」(语义覆盖)。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


class TestPrdOpenDecisionsCarryRecommendation(unittest.TestCase):

    def _prd(self):
        return (ROOT / "templates" / "prd.md").read_text(encoding="utf-8")

    def test_table_has_recommendation_and_reason_columns(self):
        """结构性修复:没有列 = 内容必然缺失,靠自觉补不回来。"""
        t = self._prd()
        header = next((l for l in t.splitlines()
                       if l.startswith("| ID | 问题 |")), None)
        self.assertIsNotNone(header, "§待决策项 表头不见了")
        self.assertIn("建议", header, "缺「💡 建议」列 —— AI 照表填就只会给裸选项")
        self.assertIn("理由", header, "缺「理由」列 —— 只有结论没有依据,用户仍要追问")

    def test_columns_are_consistent_across_header_sep_and_example(self):
        t = self._prd().splitlines()
        i = next(k for k, l in enumerate(t) if l.startswith("| ID | 问题 |"))
        n = len(t[i].strip("|").split("|"))
        self.assertEqual(len(t[i + 1].strip("|").split("|")), n, "分隔行列数不符")
        self.assertEqual(len(t[i + 2].strip("|").split("|")), n, "示例行列数不符")

    def test_cannot_recommend_has_a_defined_escape(self):
        """🔴 不给逃生口,规则会被「这个我也不知道」绕过;给了就必须说明是哪一种。"""
        t = self._prd()
        self.assertIn("无法建议", t)
        for kind in ("缺信息", "纯偏好", "等上游"):
            self.assertIn(kind, t, f"「推荐不了」的合法情形缺:{kind}")
        self.assertIn("留空", t, "未明说留空不合法 → 逃生口会变成默认路径")


class TestRedlineCoversEveryDecisionPoint(unittest.TestCase):
    """R5 的红线原本只覆盖「三选项暂停点」—— 而这次出事的是 PRD 里的决策项列表。"""

    def _skill(self):
        return (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_scope_extended_beyond_three_option_format(self):
        t = self._skill()
        self.assertIn("不止于三选项格式", t)
        self.assertIn("待决策项", t, "未点名 PRD 决策项列表 → 规则还是够不着它")

    def test_names_why_it_matters(self):
        """「把判断甩回用户」+「AI 有全部上下文」—— 不写清就会被当成格式洁癖。"""
        t = self._skill()
        self.assertIn("把判断甩回用户", t)
        self.assertIn("AI 有全部上下文", t)

    def test_ok_shortcut_dependency_stated(self):
        """`ok` = 选推荐项 —— 没有推荐项,这个快捷词直接失灵。"""
        t = self._skill()
        self.assertIn("ok", t)
        p = (ROOT / "templates" / "prd.md").read_text(encoding="utf-8")
        self.assertIn("快捷词失灵", p, "未说明 ok 依赖推荐项 → 读者不知道漏建议的连带后果")


class TestGoalStageEscalationRequiresIt(unittest.TestCase):
    """终确认导读里「你要拍板的」早就要求「我的倾向」,而 §待决策项 escalate 那半句没有 —— 漏的正是它。"""

    def test_escalate_clause_requires_recommendation(self):
        t = (ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")
        i = t.index("剩余 §待决策项一次性 escalate")
        clause = t[i:i + 260]
        self.assertIn("建议", clause, "escalate 子句未要求带建议")
        self.assertIn("不许只列选项", clause, "缺禁止句 → 又会退回裸列表")

    def test_both_halves_of_the_readout_now_agree(self):
        """「你要拍板的」与「§待决策项」两档要求一致 —— 否则同一份导读里两套标准。"""
        t = (ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")
        self.assertIn("我的倾向", t)
        self.assertIn("💡 建议", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
