"""装配后移:prepare 只对齐意图 · 链装配在 goal 调研后定(用户拍板)。

拍板链:①「只对齐意图,不做装配,装配调整到 Goal 深入调研之后再结合实际复杂度给出」
②「feature 的执行流程不变 · 链装配包含环节和评审面两个维度」
③「写 PRD 的时候提示出来装配链,默认按装配链执行,不阻塞,提示用户可调整」
④「goal 的评审面在调研之后 AI 自己定;剩下的装配在 PRD 确认时一起提示,用户不要求改就默认」

机器层零新参数(needs-ui / needs-browser-e2e / change-review-roles 全部既有)——
本版是决策时点搬迁:让 spec 对齐机器早已存在的形状。
"""
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

PREPARE = SKILL_ROOT / "docs" / "prepare.md"
GOAL = SKILL_ROOT / "stages" / "goal-stage.md"
FLOWS = SKILL_ROOT / "FLOWS.md"
STATE_PY = SKILL_ROOT / "tools" / "state.py"


class TestPrepareOnlyAlignsIntent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = PREPARE.read_text(encoding="utf-8")

    def test_q1_q4_table_gone_from_prepare(self):
        """Q1-Q4 装配思考不再在 prepare —— 信息最少的时刻不做信息最密的决策。"""
        self.assertNotIn("| Q1 |", self.doc)
        self.assertNotIn("已据 §1.5.4 Q1-Q4 设", self.doc)

    def test_deferral_declared_with_single_source(self):
        self.assertIn("prepare 不做装配", self.doc)
        self.assertIn("goal 调研之后", self.doc)
        self.assertIn("goal-stage § 链装配", self.doc)      # 单源指针

    def test_prepare_keeps_its_four_duties(self):
        for k in ("意图对齐", "flow 大类", "白名单速通", "机械配置"):
            self.assertIn(k, self.doc)
        self.assertIn("preset=micro 准入校验", self.doc)     # micro 速通保留(类型判断非装配)

    def test_pause_template_shows_deferral_not_roster(self):
        self.assertIn("装配:环节 + 评审面在 **goal 调研后**", self.doc)
        self.assertNotIn("评审:各 stage 按 flow 默认", self.doc)


class TestGoalAssemblyRule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = GOAL.read_text(encoding="utf-8")
        cls.doc = doc
        cls.rule = doc.split("链装配(调研后", 1)[1].split("\n4. ")[0]

    def test_two_dimensions_and_only_two_stage_knobs(self):
        self.assertIn("环节", self.rule)
        self.assertIn("评审面", self.rule)
        self.assertIn("唯二可选段", self.rule)               # 执行流程不变 · 只有 2 个环节旋钮

    def test_four_axis_evidence_required(self):
        for axis in ("改动方向", "契约面", "影响面", "验证成本"):
            self.assertIn(axis, self.rule)
        self.assertIn("装配证据必填", self.rule)
        self.assertIn("定价不许建立在需求字面上", self.rule)

    def test_two_beat_activation(self):
        """拍④:goal 自身面 AI 自定不问用户;下游默认执行不单独停等。"""
        self.assertIn("AI 自定", self.rule)
        self.assertIn("不问用户", self.rule)
        self.assertIn("默认按此执行", self.rule)
        self.assertIn("不单独停等", self.rule)

    def test_activation_uses_existing_machinery(self):
        self.assertIn("--needs-ui / --needs-browser-e2e", self.rule)
        self.assertIn("change-review-roles", self.rule)

    def test_judgment_table_migrated_from_prepare(self):
        for k in ("产品方向影响", "跨 ≥3 模块", "数据模型重构", "dba"):
            self.assertIn(k, self.rule)

    def test_prd_digest_carries_assembly_section(self):
        seg = self.doc.split("余节 ≤2 行", 1)[1].split("\n", 1)[0]
        self.assertIn("🔗 **链装配**", seg)
        self.assertIn("默认按此执行", seg)


class TestRuntimeCarriers(unittest.TestCase):

    def test_goal_brief_carries_assembly(self):
        from _v8_stage_specs import GOAL_SPEC
        brief = GOAL_SPEC.brief_template_fn({})
        self.assertIn("链装配", brief)
        self.assertIn("--needs-browser-e2e", brief)
        self.assertIn("默认按此执行", brief)
        self.assertNotIn("prepare 已按", brief)              # 旧「prepare 预设 roster」话术退役

    def test_prepare_check_emit_no_longer_assembles(self):
        src = STATE_PY.read_text(encoding="utf-8")
        self.assertNotIn("PMO 必基于此 checklist 4 问思考 · 设定实际评审角色 + stage 链", src)
        self.assertIn("消费时点在 goal 调研后", src)
        self.assertIn("评审面与环节装配不在 prepare 做", src)

    def test_flows_declares_decision_point(self):
        doc = FLOWS.read_text(encoding="utf-8")
        self.assertIn("装配决策点 = goal 调研后", doc)
        self.assertIn("用户不要求改就生效", doc)


class TestMachineUnchanged(unittest.TestCase):
    """执行流程不变(拍②)—— 机器层既有机关未动。"""

    def test_goal_complete_hints_params_still_wired(self):
        src = (SKILL_ROOT / "tools" / "_v8_stage_specs.py").read_text(encoding="utf-8")
        self.assertIn("--needs-ui → hints.ui_design_needed", src)
        self.assertIn("--needs-browser-e2e → hints.browser_e2e_needed", src)

    def test_empty_roster_semantics_survive(self):
        """空 roster = 有意不评审 —— 评审面收到零的机器基础仍在。"""
        src = (SKILL_ROOT / "tools" / "_v8_stage_specs.py").read_text(encoding="utf-8")
        self.assertIn("空 roster = 本 stage 不要求评审", src)


if __name__ == "__main__":
    unittest.main()
