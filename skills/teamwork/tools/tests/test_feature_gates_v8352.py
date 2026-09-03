"""功能生效闸:必须在 TECH 明示 · 与 DB 变更同级需用户确认 · 设闸要有理由(用户拍板)。

拍板:「功能生效闸需要在 TECH 文档明确指出,如果有,需要和数据库变更等一起由用户确认。
设闸需要理由,避免无意义的闸导致上线功能不生效。」

实证事故(DEV-F260828054357 Performance Analytics):
- **PRD 只锁产品诚实性**:覆盖范围之外不补零、不把不完整说成完整 —— 「Today 可以
  partial / unavailable」;
- **TECH 把它翻译成了硬闸**:独立 query 水位、writer 开关、snapshot cap、未配置整页 503
  —— 「别报假数」被落成「**没配齐就不要开读**」;
- 结果:功能上线了,但 Account `/api/performance` fail-closed 503,**用户根本看不到**。

🔴 本版要治的形状:**默认失败方向(fail-closed vs fail-open)是产品决策,不是技术细节** ——
它决定「没配齐时用户看到降级内容还是什么都看不到」,后果完全不同,必须用户拍板。
可判问句:**这个闸不满足时,用户看到什么?PRD 承诺的是什么?** 不一致 → 交用户。
反向压力:**写不出「不设这个闸会出什么事」→ 不设**(避免无意义的闸让功能上线不生效)。
"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

from _v8_stage_specs import (_evidence_feature_gates as CHK,      # noqa: E402
                             BLUEPRINT_SPEC)

TECH_TPL = (SKILL_ROOT / "templates" / "tech.md").read_text(encoding="utf-8")
BP_MD = (SKILL_ROOT / "stages" / "blueprint-stage.md").read_text(encoding="utf-8")
SKILL_MD = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")


def _tpl_section():
    return re.search(r"(?ms)^## 功能生效闸.*?(?=^## 风险与缓解)", TECH_TPL).group(0)


class _Case(unittest.TestCase):
    def _chk(self, tech_body, state=None):
        d = Path(tempfile.mkdtemp())
        (d / "TECH.md").write_text(tech_body, encoding="utf-8")

        class A:
            feature = str(d)
        return CHK(state or {"flow_type": "Feature"}, A())


class TestGate(_Case):

    def test_missing_section_fails(self):
        ok, msg = self._chk("# T\n## 技术方案\nx\n")
        self.assertFalse(ok)
        self.assertIn("功能生效闸", msg)
        self.assertIn("无闸也要显式写「无」", msg)   # 静默没有 与 忘了写 分不开

    def test_template_as_is_fails(self):
        """模板原样(含 `{ENV_X}` 占位)必须挂 —— 抄模板能过 = 门形同虚设。"""
        ok, msg = self._chk("# T\n" + _tpl_section())
        self.assertFalse(ok)
        self.assertIn("未答齐", msg)

    def test_explicit_none_passes(self):
        """显式「无」放行 —— 不逼人为了过门编一个闸出来(那会制造真的无意义的闸)。"""
        ok, _ = self._chk("# T\n## 功能生效闸\n无\n\n## 风险与缓解\nx\n")
        self.assertTrue(ok)

    def test_row_must_answer_what_user_sees(self):
        """少列 = 没答「不满足时用户看到什么」—— 那正是这次事故漏掉的那一问。"""
        ok, msg = self._chk("# T\n## 功能生效闸\n\n| 闸 | 默认值 |\n|---|---|\n| ENV_X | false |\n")
        self.assertFalse(ok)
        self.assertIn("不满足时用户看到什么", msg)
        self.assertIn("不设这个闸", msg)          # 反向压力:写不出理由就别设

    def test_fully_answered_passes(self):
        ok, msg = self._chk(
            "# T\n## 功能生效闸\n\n"
            "| 闸 | 默认值 | 不满足时用户看到什么 | PRD 承诺的是什么 | 为什么要这个闸 | 谁能解开 |\n"
            "|---|---|---|---|---|---|\n"
            "| AON_DURABLE_QUERY | false | partial 展示不补零 | partial/unavailable 也要能看 "
            "| 防展示未回填假数 | 运维 · cutover 后 |\n")
        self.assertTrue(ok, msg)

    def test_skipped_for_flows_without_tech(self):
        for flow in ("Bug", "Micro", "Tiny", "Floor"):
            ok, msg = self._chk("# T\nx\n", {"flow_type": "Feature", "preset": flow.lower()}
                                if flow in ("Micro", "Tiny", "Floor") else {"flow_type": flow})
            self.assertTrue(ok, flow)

    def test_registered_on_blueprint(self):
        self.assertIn("feature_gates", [e.name for e in BLUEPRINT_SPEC.evidence_checks])


class TestTemplate(unittest.TestCase):

    def test_defines_what_counts_as_a_gate(self):
        seg = _tpl_section()
        for kind in ("env flag", "配置项必填", "cap", "fail-closed"):
            self.assertIn(kind, seg, kind)

    def test_columns_carry_the_decidable_question(self):
        seg = _tpl_section()
        self.assertIn("不满足时用户看到什么", seg)
        self.assertIn("PRD 承诺的是什么", seg)
        self.assertIn("不设会出什么事", seg)

    def test_reverse_pressure_against_pointless_gates(self):
        """用户拍板的第三条:设闸要有理由,避免无意义的闸让功能上线不生效。"""
        seg = _tpl_section()
        self.assertIn("写不出", seg)
        self.assertIn("不设", seg)
        self.assertIn("别让功能上了线却不生效", seg)

    def test_failure_direction_named_as_product_decision(self):
        seg = _tpl_section()
        self.assertIn("fail-closed", seg)
        self.assertIn("fail-open", seg)
        self.assertIn("产品决策", seg)
        self.assertIn("「别报假数」≠「宁可什么都不给」", seg)   # 事故的那一步误译


class TestPauseTrigger(unittest.TestCase):
    """与 DB 变更同级 —— 挂在既有的方案要素确认停等上,不另立新暂停点。"""

    def test_blueprint_rule_lists_third_trigger(self):
        self.assertIn("🚦 功能生效闸非空", BP_MD)
        self.assertIn("与 DB 变更同级", BP_MD)

    def test_pause_card_shows_gates(self):
        card = BP_MD.split("⏸️ TECH 方案要素确认", 1)[1].split("```", 1)[0]
        self.assertIn("🚦 功能生效闸", card)
        self.assertIn("不满足时用户看到什么", card)
        self.assertIn("产品决策伪装成技术细节", card)

    def test_adjust_option_covers_gates(self):
        self.assertIn("兜底/生效闸有异议", BP_MD)

    def test_skill_says_three_triggers(self):
        self.assertIn("**三触发**", SKILL_MD)
        self.assertIn("🚦 有功能生效闸", SKILL_MD)
        self.assertIn("生效闸与 DB 变更同级需确认", SKILL_MD)

    def test_red_budget_under_gate(self):
        self.assertLess(SKILL_MD.count("🔴"), 55)


class TestBrief(unittest.TestCase):

    def test_blueprint_brief_carries_it(self):
        b = BLUEPRINT_SPEC.brief_template_fn({})
        self.assertIn("功能生效闸", b)
        self.assertIn("不满足时用户看到什么", b)
        self.assertIn("写不出「不设会出什么事」就不设", b)
        self.assertIn("功能上线了但用户根本看不到", b)   # case 代价


if __name__ == "__main__":
    unittest.main()
