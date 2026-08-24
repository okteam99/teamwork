"""子代理禁问用户 · 问题回路收口主对话(用户拍板)。

case(Grok 宿主消费现场):写测试用例的子代理调宿主的 ask_user_question,把
「/analysis 登录回跳测试写在哪个文件」直接弹到用户屏幕 —— 纯实现细节,teamwork
设计上永远不该到用户面前。

盘点:回路早就有(agents/README verdict 枚举 🔄 NEEDS_CONTEXT → 补上下文重派;
stage brief 暂停点纪律「Substep 中间禁 AskUserQuestion」),但两个口没封:
① 暂停点纪律管的是**主对话**,子代理侧没有**对着工具名**的红线 —— 对没带全量
   context 的执行路径,别处的规则等于不存在(v8.321「模式承诺 × 动作点载体」同款);
② 派发 prompt 没要求带禁问句 —— 读过规则仍会漏,义务要寄生在必写载体上(v8.299)。

用户拍板:「子代理/subagent 的问题由主对话自行处理,无需找用户确认,
只有主对话判断需要用户确认的才交给用户确认」。
"""
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

AGENTS = SKILL_ROOT / "agents" / "README.md"


class TestAgentsReadmeRedline(unittest.TestCase):
    """单源:agents/README §二 通用执行约束。"""

    @classmethod
    def setUpClass(cls):
        doc = AGENTS.read_text(encoding="utf-8")
        cls.doc = doc
        cls.rule = doc.split("禁向用户提问", 1)[1].split("\n- ")[0]

    def test_redline_names_the_tool_not_the_behavior(self):
        """对着工具名锁(AskUserQuestion + snake_case 宿主变体)—— 「不要打扰用户」
        这类行为式表述糊得过,工具名糊不过(v8.302 槽位式同理)。"""
        self.assertIn("`AskUserQuestion`", self.rule)
        self.assertIn("`ask_user_question`", self.rule)
        self.assertIn("宿主变体", self.rule)          # 覆盖未来宿主的同类工具

    def test_uncertainty_routes_to_result(self):
        self.assertIn("写进返回结果", self.rule)
        self.assertIn("NEEDS_CONTEXT", self.rule)

    def test_users_exact_ruling_encoded(self):
        """拍板原文入规:主对话自行处理 · 只有用户主权才 escalate。"""
        self.assertIn("子代理的问题由主对话自行处理", self.rule)
        self.assertIn("只有主对话判断属于用户主权的,才走 R5", self.rule)

    def test_main_dialog_bisection_explicit(self):
        """主对话的二分要写死:实现细节自答重派 / 用户主权走 R5 —— 否则红线只堵了
        子代理,主对话拿到 NEEDS_CONTEXT 又原样转抛给用户,问题换了个出口。"""
        self.assertIn("自答后补上下文重派", self.rule)
        self.assertIn("偏好/业务取舍/外部事实", self.rule)   # 用户主权判据沿用早问门闸 2 口径
        self.assertIn("R5 编号选项", self.rule)

    def test_why_cites_the_real_case(self):
        self.assertIn("Grok 宿主", self.rule)
        self.assertIn("测试写哪个文件", self.rule)
        self.assertIn("暂停点纪律只管主对话", self.rule)   # 命名此前的漏格

    def test_needs_context_loop_still_intact(self):
        """既有回路不动:verdict 枚举与「补上下文重派 · 不降级」仍在。"""
        self.assertIn("🔄 NEEDS_CONTEXT | 补上下文 → 重新 dispatch(不降级)", self.doc)


class TestDispatchCarrier(unittest.TestCase):
    """动作点载体:引擎的派发提醒(每个 stage-start 都带)。"""

    @classmethod
    def setUpClass(cls):
        from _v8_engine import DISPATCH_TIER_REMINDER
        cls.r = DISPATCH_TIER_REMINDER

    def test_prompt_must_carry_the_ban(self):
        self.assertIn("派发 prompt 必带一句", self.r)
        self.assertIn("禁止调用任何向用户提问/确认的工具", self.r)
        self.assertIn("AskUserQuestion 等宿主变体", self.r)

    def test_parasitic_on_meta_line(self):
        """与 tier 声明同寄生一处 —— 不另立「记得写禁问句」的孤立义务。"""
        self.assertIn("与 Meta 同寄生一处", self.r)

    def test_uncertainty_routing_in_reminder(self):
        self.assertIn("NEEDS_CONTEXT", self.r)
        self.assertIn("不问用户", self.r)

    def test_case_evidence_present(self):
        self.assertIn("Grok 宿主", self.r)
        self.assertIn("测试写哪个文件", self.r)

    def test_single_source_pointer(self):
        self.assertIn("agents/README §二", self.r)


class TestSkillCite(unittest.TestCase):

    def test_skill_carries_one_line_cite(self):
        t = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        seg = t.split("子代理禁问用户", 1)[1].split("\n- ")[0]
        self.assertIn("NEEDS_CONTEXT", seg)
        self.assertIn("自答重派", seg)
        self.assertIn("真用户主权才走 R5", seg)
        self.assertIn("agents/README §二", seg)      # 单源指针 · SKILL 只 cite 不另立判据

    def test_red_budget_still_under_gate(self):
        """密度门 <55(v8.315 判例:预算内塞不下就换 ❌,不顶爆)—— 本版 SKILL 行用 ❌。"""
        t = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(t.count("🔴"), 55)
        self.assertIn("❌ **子代理禁问用户", t)


class TestMainDialogRuleUntouched(unittest.TestCase):
    """主对话侧既有纪律不因本版动(本版补的是子代理侧,两条规则互补不重叠)。"""

    def test_stage_brief_still_bans_midstep_ask(self):
        from _v8_engine import _render_pause_discipline
        d = _render_pause_discipline("无暂停 · 完成后自动转 review")
        self.assertIn("Substep 中间禁 AskUserQuestion", d)


if __name__ == "__main__":
    unittest.main()
