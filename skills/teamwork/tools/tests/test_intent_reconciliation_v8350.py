"""AC 意图对照:主对话 PM 确认「有无理解偏差」(用户拍板)。

拍板:「对用户意图可能有偏差的改动,一定要在 PRD 阶段确认好。尤其是 AC,
主对话 PM 要确认下 AC 是否有对原始用户意图理解偏差的风险。」

实证事故(aon-main click 导出):Feature 把「AON Link」狭义解释成 `/{code}` 短链、
明确排除 `/static/{code}` —— TECH 写「static 不登记」,测试甚至断言 static
"must remain unwired"。**dev 和 review 都在认真验证一个错误的范围定义**,
线上投放点击因此全部没有回传。

🔴 为什么冷审拦不住:**范围被悄悄收窄时,PRD 是完全自洽的** —— 冷审只能核对
「PRD 内部一致 / 技术可实现」,它拿不到用户原话。所以责任人只能是主对话 PM。

三槽的形状(可判,不是形容词):
① 用户原话里的名词 → 我理解成了什么 → **用户说过 / 我推的**
② §Out of Scope 每条 → **技术限制 / 我的解释**(我的解释 = 范围决策 · 必须进待决策项)
③ **AC 全绿时,用户要的那件事一定发生了吗?**(与协议事故的「测试验证了错误的前提」同形)
"""
import pathlib
import re
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

from _v8_stage_specs import (_evidence_intent_reconciliation as CHK,   # noqa: E402
                             GOAL_SPEC)

PRD_TPL = (SKILL_ROOT / "templates" / "prd.md").read_text(encoding="utf-8")
GOAL_MD = (SKILL_ROOT / "stages" / "goal-stage.md").read_text(encoding="utf-8")


def _section():
    """模板里 §意图对照 + §Out of Scope 整段(② 并进后者的「性质」列)。"""
    return re.search(r"(?ms)^## 意图对照.*?(?=^## 开工前)", PRD_TPL).group(0)


def _filled():
    return (_section()
            .replace("{词}", "AON Link")
            .replace("{我的解释}", "含 /static/{code} 在内的全部投放入口")
            .replace("{🔴 我推的 · 用户没说过是否含 …}", "用户说过(原话:「投放链接的点击」)")
            .replace("{具体后果：如「投放链接的点击全部不回传,广告优化拿不到转化数据」"
                     "→ 生产/不可逆 → 已进 D-N}",
                     "投放点击全部不回传 · 广告拿不到转化数据 → 生产/不可逆 → 已进 D-1")
            .replace("{反例 + 处置} / {无反例 · 因为 AC 覆盖了：…}",
                     "无反例 · AC 覆盖 /{code} 与 /static/{code} 两条真实入口")
            .replace("{X}", "历史点击补发").replace("{Y}", "无")
            .replace("{一句}", "成本明确不值")
            .replace("{一句 · 已进 §待决策项 D-N}", "—"))


class _Case(unittest.TestCase):
    def _chk(self, body):
        d = Path(tempfile.mkdtemp())
        (d / "PRD.md").write_text(body, encoding="utf-8")

        class A:
            feature = str(d)
        return CHK({}, A())


class TestGate(_Case):

    def test_missing_section_fails_with_all_three_slots_named(self):
        ok, msg = self._chk("# X\n## 验收标准\n表\n")
        self.assertFalse(ok)
        for k in ("术语解释对照", "排除项定性", "反向验证"):
            self.assertIn(k, msg, k)

    def test_template_as_is_is_not_enough(self):
        """🔴 模板原样必须挂 —— 否则「抄模板」就能过门 = 门形同虚设。

        初版把表格行(`|` 开头)和引导语一起剔掉再数占位符,而三槽的内容主体
        恰恰全在表格里 → 模板原样也 PASS。这条锁住那个具体的失效方式。
        """
        ok, msg = self._chk("# X\n" + _section())
        self.assertFalse(ok)
        self.assertIn("仍是模板占位", msg)

    def test_filled_passes(self):
        ok, msg = self._chk("# X\n" + _filled())
        self.assertTrue(ok, msg)

    def test_slot2_reads_out_of_scope_not_a_second_table(self):
        """②并进 §Out of Scope 的「性质」列 —— 排除项已在那儿列过,不两处写(双载体必漂)。"""
        body = _filled().split("## Out of Scope")[0] + "## Out of Scope\n- 不做 A\n"
        ok, msg = self._chk("# X\n" + body)
        self.assertFalse(ok)
        self.assertIn("性质", msg)

    def test_gate_registered_on_goal(self):
        self.assertIn("intent_reconciliation", [e.name for e in GOAL_SPEC.evidence_checks])


class TestCostIsComputedNotToldV8351(unittest.TestCase):
    """v8.351(用户拍板:「PM 要知道一旦理解错了,代价非常高」)。

    🔴 「要知道代价高」**本身是形容词** —— 本仓连着多版实证过它不产生行为
    (v8.334 按需/酌情 · v8.337 形容词式装配卡 · v8.341 权限休眠 · v8.342 附加轻门)。
    所以代价不是被告知的,是**逐行算出来的**:①表末列写「若这条错了最坏会怎样」的
    **具体后果**;写不出具体后果 = 其实没想过代价。

    而「代价高」这件事本身有一个**结构性**的说法(不是劝导):意图错误是唯一一类
    下游全部质量门都拦不住的错 —— 评审/测试/CI/验收全都以「意图正确」为前提,
    只能答「做得对不对」、答不了「做的是不是对的东西」。**越认真做,错得越彻底**。
    """

    def _chk(self, body):
        d = Path(tempfile.mkdtemp())
        (d / "PRD.md").write_text(body, encoding="utf-8")

        class A:
            feature = str(d)
        return CHK({}, A())

    def test_cost_column_is_required(self):
        """砍掉代价列必须挂 —— 否则这一列只是文档里的建议,不是必答项。"""
        body = (_filled().replace(" | 🔴 若这条理解错了 → 最坏会怎样", "")
                         .replace("|---|---|---|---|", "|---|---|---|"))
        ok, msg = self._chk("# X\n" + body)
        self.assertFalse(ok)
        self.assertIn("最坏会怎样", msg)

    def test_template_demands_concrete_not_adjective(self):
        seg = _section()
        self.assertIn("不写「影响较大」", seg)
        self.assertIn("生产/外部/不可逆", seg)
        self.assertIn("必进 §待决策项", seg)      # 后果严重 → 强制升级 · 与信心无关

    def test_structural_why_not_exhortation(self):
        """why 给的是**结构性事实**,不是「要重视」——「唯一一类全部质量门拦不住的错」。"""
        rule = GOAL_MD.split("为什么这一关的代价与众不同", 1)[1].split("\n   - 📎", 1)[0]
        self.assertIn("唯一一类下游全部质量门都拦不住的错", rule)
        self.assertIn("以「意图正确」为前提", rule)
        self.assertIn("越认真做,错得越彻底", rule)
        self.assertIn("代价 ≈ 一轮返工", rule)     # 与实现错误的量级对比
        self.assertIn("两次实证", rule)            # 协议归零 + click 不回传

    def test_cost_must_be_computed_clause(self):
        rule = GOAL_MD.split("代价要算,不要被告知", 1)[1].split("\n   - 📎", 1)[0]
        self.assertIn("写不出具体后果 = 其实没想过代价", rule)

    def test_brief_carries_the_stakes(self):
        b = GOAL_SPEC.brief_template_fn({})
        self.assertIn("越认真做,错得越彻底", b)
        self.assertIn("最坏会怎样", b)


class TestTemplate(unittest.TestCase):

    def test_three_slots_present(self):
        seg = _section()
        self.assertIn("① 术语解释对照", seg)
        self.assertIn("③ 反向验证", seg)
        self.assertIn("每条标性质", seg)                  # ② 在 Out of Scope

    def test_decidable_questions_not_adjectives(self):
        seg = _section()
        self.assertIn("用户说过", seg)
        self.assertIn("我推的", seg)
        self.assertIn("做不到", seg)                      # 排除项判据
        self.assertIn("我选的边界", seg)
        self.assertIn("用户真正要的那件事一定发生了吗", seg)

    def test_my_interpretation_exclusions_must_escalate(self):
        self.assertIn("必须进 §待决策项", _section())

    def test_slimming_gate_respected(self):
        """v8.283 瘦身门 <340 行 —— 服从门裁自己的红(v8.303 判例),不是改门限。"""
        self.assertLess(len(PRD_TPL.splitlines()), 340)


class TestStageRule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rule = GOAL_MD.split("意图对照(主对话 PM 自查", 1)[1].split("\n5. ", 1)[0]

    def test_owner_is_main_dialog_only(self):
        self.assertIn("只能主对话 PM 做,不可委托冷审", self.rule)
        self.assertIn("冷审拿不到用户原话", self.rule)
        self.assertIn("范围被悄悄收窄时,PRD 是完全自洽的", self.rule)   # 为什么冷审无能为力

    def test_case_evidence_recorded(self):
        self.assertIn("AON Link", self.rule)
        self.assertIn("must remain unwired", self.rule)
        self.assertIn("认真验证一个错误的范围定义", self.rule)

    def test_division_from_rule5_stated(self):
        """与「既有行为变更必升级」分工写明 —— 否则两条会被当成一条,漏掉其中一种。"""
        self.assertIn("规则 5 管**改了既有行为**", self.rule)
        self.assertIn("本条管**理解偏了原始意图**", self.rule)

    def test_digest_surfaces_the_risky_rows(self):
        """终确认导读要把「我推的」和「我的解释」两类摆给用户 —— 这是最可能偏的地方。"""
        seg = GOAL_MD.split("余节 ≤2 行", 1)[1].split("\n", 1)[0]
        self.assertIn("意图对照", seg)
        self.assertIn("我推的", seg)


class TestBrief(unittest.TestCase):

    def test_goal_brief_carries_it(self):
        b = GOAL_SPEC.brief_template_fn({})
        self.assertIn("意图对照", b)
        self.assertIn("我推的", b)
        self.assertIn("不可委托冷审", b)
        self.assertIn("用户要的事一定发生了吗", b)


if __name__ == "__main__":
    unittest.main()
