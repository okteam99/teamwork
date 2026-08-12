"""v8.315:拍板项固定四槽 —— 治「建议理由都在 · 用户仍被迫追问上下文」。

实证(CA-F260810 镜像仓治理):goal 终确认导读四条 D 项写成「D-1:建议 A——跳到独立创建流程;
不隐式复制配置,也不扩建跨环境服务模型」—— 建议有、理由有(v8.302 修过的都在),
但**全是术语压缩**,且**B 选项从头到尾没出现**(「例如回复 D1=B」而 B 是什么从没写过 = 假选择题)。
用户被迫追问:「大白话解释下 · 问题上下文是什么 · 用在什么场景 · 建议的业务逻辑是什么」。

这是 v8.302 族的下一层:那次缺的是「建议+理由」两列,这次缺的是**场景上下文 + 大白话 +
完整选项集**。同一判据换个提问方向,可糊性完全不同 —— 修法仍是载体不是措辞:
拍板项固定四槽(场景 / 要定什么 / 每个选项内容与后果 / 建议+理由)。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestGoalReadoutFourSlots(unittest.TestCase):
    """终确认导读是拍板动作点 —— 四槽格式必须写在它身上。"""

    def setUp(self):
        self.t = _read("stages/goal-stage.md")

    def test_four_slots_defined(self):
        self.assertIn("拍板项每条固定四槽", self.t)
        for slot in ("场景", "要定什么", "建议 + 理由"):
            self.assertIn(slot, self.t, f"四槽缺:{slot}")

    def test_complete_option_set_required(self):
        """🔴 核心:每个选项的内容都必须写出 —— 只给推荐项 = 假选择题。"""
        self.assertIn("每个选项的内容与后果各一句都必须写出", self.t)
        self.assertIn("假选择题", self.t)

    def test_plain_language_rationale_present(self):
        """为什么要大白话:导读给没读过 PRD 的人 —— 术语自由的读者拍不了板。"""
        self.assertIn("术语自由的读者拍不了板", self.t)
        self.assertIn("导读给没读过 PRD 的人", self.t, "既有原则被误删")


class TestPrdTableFeedsTheSlots(unittest.TestCase):
    """PRD 待决策项表是四槽的数据源 —— 表里没有,导读只能现编或漏。"""

    def setUp(self):
        self.t = _read("templates/prd.md")

    def test_question_column_carries_scenario(self):
        self.assertIn("「问题」列自含场景上下文", self.t)
        self.assertIn("什么时候会遇到 · 影响谁", self.t)

    def test_option_column_bans_placeholders(self):
        self.assertIn("「选项」列每个选项写完整内容", self.t)
        self.assertIn("禁「B. 其他/另议」占位", self.t)

    def test_v8302_requirements_untouched(self):
        """本版是 v8.302 的加层不是替换 —— 建议+理由结构性要求原样在。"""
        self.assertIn("每条待决策项必带「💡 建议 + 理由」", self.t)
        self.assertIn("无法建议", self.t)


class TestSkillR5Extended(unittest.TestCase):

    def setUp(self):
        self.t = _read("SKILL.md")

    def test_option_set_completeness_in_r5(self):
        self.assertIn("选项集必须完整摊开", self.t)
        self.assertIn("面向没读过产物的人写", self.t)
        self.assertIn("假选择题", self.t)

    def test_red_budget_respected(self):
        """扩条款不许把 🔴 预算顶爆(密度门 <55)—— 新增内容用 ❌ 不用 🔴。"""
        self.assertLess(self.t.count("🔴"), 55)

    def test_v8302_line_survives(self):
        self.assertIn("不止于三选项格式", self.t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
