"""v8.303:断言必须标注证据边界 + 测试输入必须来自真实链路。

来源:SVC-CORE-F260728 的 AI 自省 —— 它把本 session 犯的 9 个错列表后,归纳出**唯一共同点**:

    「我读了旁边的代码,然后把结论说成读过那一行。」

其中:把 external 给的行号直接写进 TECH(该函数根本不存在)· 据类型签名推出「新字段会被丢弃」
(实为 `deny_unknown_fields` 会 502)· 把死代码当活路径写进已合并的 WS/ROADMAP。

🔴 **它自己的定性最关键**:「**不是验证不够** —— 那个 session 跑了几十次 grep 与 staging 实测;
**是不标注验证止于何处、推论始于何处**。已验证的和推出来的,在我的输出里长得一模一样,
你没法分辨该信哪句。」

框架已有的 7+ 条规则(grounded 真实代码 / 不轻信摘要 / decisive 前提核验 / grep 不凭记忆)
**全在输入端**,没有一条管**输出端怎么标**。本版补的就是这一面。

第二条(错误 #3)是另一个面:测试验的是「我伪造的输入能被正确处理」而非「真实链路会产生这样的输入」
—— 11 测试 + 4 变异验证全绿、功能全坏,**冷审/变异/CI 全在自己画的圈里**,靠生产数据才发现。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


class TestEvidenceBoundaryRule(unittest.TestCase):

    def _skill(self):
        return (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_rule_exists_with_binary_requirement(self):
        """「要么读过那一行,要么写推断」—— **不许中间态**是这条的全部力量所在。"""
        t = self._skill()
        self.assertIn("R3-E", t, "证据边界规则不见了")
        self.assertIn("读过那一行", t)
        self.assertIn("不许中间态", t, "缺二元要求 → 会退化成「尽量标注」= 不标注")

    def test_names_the_high_frequency_shape(self):
        """不点名「读了旁边」这个具体形态,规则就只是句正确的废话。"""
        t = self._skill()
        self.assertIn("读了旁边", t)
        for attr in ("serde", "约束", "默认值", "死代码"):
            self.assertIn(attr, t, f"未举「没亲眼看过的属性」实例:{attr}")

    def test_shows_the_layered_output_form(self):
        """给形式,不只给要求 —— 否则 AI 不知道「标注」长什么样。"""
        t = self._skill()
        self.assertIn("已验证", t)
        self.assertIn("未验证", t)

    def test_states_it_does_not_decay_with_stronger_models(self):
        """🔴 本 session 的分类学里,只有「不衰减」那几类才值得长期占位。

        这条要说明白它属于哪一类,否则下一轮减法会把它当「手段规定」砍掉。
        """
        t = self._skill()
        self.assertIn("不随模型变强而衰减", t,
                      "未声明抗衰减属性 → 下次减法会误砍")
        self.assertIn("越像事实", t, "未说明为什么模型越强越需要它")

    def test_states_input_side_rules_do_not_cover_this(self):
        """框架已有一堆输入端规则 —— 不说清「它们管不到输出端」,读者会以为重复。"""
        t = self._skill()
        self.assertIn("全在输入端", t)

    def test_red_mark_discipline_applied_to_itself(self):
        """自我施用:R3-E 段只有**规则本身**配标红,解释性文字不配。

        (本版加完 R3-E 后 SKILL 的 🔴 计数门当场红了 —— 正确做法是按门自己的判据
         裁掉解释性 🔴,不是抬阈值。)
        """
        t = self._skill()
        i = t.index("### R3-E ·"); j = t.index("### R4 · 流程边界")
        self.assertEqual(t[i:j].count("🔴"), 1,
                         "R3-E 段的 🔴 应只标规则本身(判据①-⑤)· 解释与 why 不标")


class TestTestInputProvenance(unittest.TestCase):
    """恒绿假绿有两条路:① mock 掉被测组件自身 ② 用自造 fixture 绕开真实链路。

    HARD-RULES 7 原本只堵了 ①。
    """

    def _hr(self):
        return (ROOT / "standards" / "HARD-RULES.md").read_text(encoding="utf-8")

    def test_input_provenance_required(self):
        t = self._hr()
        self.assertIn("测试输入必须来自真实链路", t)
        self.assertIn("自造 fixture", t)
        self.assertIn("差异", t, "自造时未要求说清与真实输入的差异 → 标注沦为形式")

    def test_one_line_criterion_is_decidable(self):
        """判据要能当场判,否则又是软要求。"""
        t = self._hr()
        self.assertIn("我伪造的输入能被正确处理", t)
        self.assertIn("真实链路会产生这样的输入", t)

    def test_names_why_the_usual_safety_nets_missed_it(self):
        """🔴 最关键的一句:冷审/变异/CI 全在自己画的圈里 ——

        不写这句,读者会觉得「多加一道评审就能拦住」,而实际上拦不住。
        """
        t = self._hr()
        self.assertIn("全在自己画的那个圈里", t)
        self.assertIn("生产数据", t, "未点明是靠什么发现的 → 低估这条的严重性")

    def test_original_mock_clause_survived(self):
        """扩规则不能顺手挤掉原有的那半条。"""
        t = self._hr()
        self.assertIn("禁止 mock 被测组件自身的内部方法", t)
        self.assertIn("真断言", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
