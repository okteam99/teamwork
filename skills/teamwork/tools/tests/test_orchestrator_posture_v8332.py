"""主对话 = Orchestrator(默认姿态 · 用户拍板)。

拍板原文:「dev stage 和 test stage 加上不建议在主对话(主循环)进行开发和测试,
主对话(主循环)优先用做 Orchestrator —— 任务拆解、阶段规划、子代理调度、集成接线、
提交/推送、验证门禁、小型精准修改等。」

设计要点:位置(谁持有 context)与档位(用什么模型)正交 —— 执行档模型继承
会话模型不降,但位置默认 subagent;「小型精准修改」是显式出口(小/耦合/强串行
派发反拖慢);建议姿态不设机器门。
"""
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

DEV = SKILL_ROOT / "stages" / "dev-stage.md"
TEST = SKILL_ROOT / "stages" / "test-stage.md"
AGENTS = SKILL_ROOT / "agents" / "README.md"

ORCH_DUTIES = ("任务拆解", "子代理调度", "集成接线", "提交/推送", "验证门禁", "小型精准修改")


class TestDevPosture(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = DEV.read_text(encoding="utf-8")
        cls.rule = doc.split("主对话 = Orchestrator", 1)[1].split("\n2. ")[0]

    def test_discourages_bulk_dev_in_main_loop(self):
        self.assertIn("不建议在主对话(主循环)直接进行成块开发", self.rule)

    def test_orchestrator_duties_verbatim(self):
        """拍板列举的职责逐项入规。"""
        for d in ORCH_DUTIES:
            self.assertIn(d, self.rule, d)

    def test_small_precise_edit_escape_kept(self):
        """出口显式:小/耦合/强串行 → 主对话直接做(派发协调开销反拖慢)。"""
        self.assertIn("小 / 耦合 / 强串行", self.rule)
        self.assertIn("反拖慢", self.rule)

    def test_position_orthogonal_to_tier(self):
        """派 subagent 时执行档继承会话模型 —— 位置姿态不是降档指令。"""
        self.assertIn("执行档继承会话模型不降档", self.rule)

    def test_why_names_context_scarcity(self):
        self.assertIn("最稀缺资源", self.rule)


class TestTestPosture(unittest.TestCase):

    def test_test_stage_carries_posture(self):
        doc = TEST.read_text(encoding="utf-8")
        rule = doc.split("主对话 = Orchestrator", 1)[1].split("\n2. ")[0]
        self.assertIn("不建议在主对话(主循环)直接编写与执行测试", rule)
        self.assertIn("验证类白名单", rule)          # 与既有档位硬约束衔接 · 不另立
        self.assertIn("差分基线裁决", rule)          # 主对话保留的裁决职责
        self.assertIn("context 污染源", rule)


class TestGlobalCharter(unittest.TestCase):
    """全局单源在 SKILL(用户追拍:其他阶段也需要)· dev/test 1.7 是 stage 实例。"""

    def test_skill_carries_global_posture(self):
        t = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        seg = t.split("主对话 = Orchestrator(全 stage 默认姿态", 1)[1].split("\n- ")[0]
        for d in ORCH_DUTIES:
            self.assertIn(d, seg, d)
        self.assertIn("成块产出", seg)
        self.assertIn("位置与档位正交", seg)
        self.assertIn("dev-stage 1.7", seg)          # stage 实例指针

    def test_stage_rules_cite_skill_as_source(self):
        for rel in ("stages/dev-stage.md", "stages/test-stage.md"):
            doc = (SKILL_ROOT / rel).read_text(encoding="utf-8")
            rule = doc.split("主对话 = Orchestrator", 1)[1].split("\n2. ")[0]
            self.assertIn("全局单源", rule, rel)
            self.assertIn("stage 实例", rule, rel)


class TestTierTableReconciled(unittest.TestCase):

    def test_execution_tier_row_decouples_position(self):
        """档位表执行档行不再背书主对话写码 —— 位置默认 subagent · 单源指 dev-stage。"""
        t = AGENTS.read_text(encoding="utf-8")
        row = next(l for l in t.splitlines() if "**执行档**" in l)
        self.assertIn("位置默认 subagent", row)
        self.assertIn("主对话 = Orchestrator", row)
        self.assertIn("dev-stage 1.7", row)
        self.assertNotIn("主对话继承会话模型即是", row)   # 旧背书措辞退役


class TestBriefCarriers(unittest.TestCase):
    """动作点载体:三个 brief(dev · test Feature 流 · test Bug 流)全带姿态。"""

    def test_dev_brief(self):
        from _v8_stage_specs import DEV_SPEC
        b = DEV_SPEC.brief_template_fn({})
        self.assertIn("主对话 = Orchestrator", b)
        self.assertIn("小型精准修改", b)

    def test_test_brief_both_flows(self):
        from _v8_stage_specs import TEST_SPEC
        for st in ({}, {"flow_type": "Bug"}):
            b = TEST_SPEC.brief_template_fn(st)
            self.assertIn("主对话 = Orchestrator", b, st)

    def test_no_machine_gate(self):
        """建议姿态 · 不设机器门(dev/test 的 evidence 不因本版增门)。"""
        from _v8_stage_specs import DEV_SPEC, TEST_SPEC
        for spec in (DEV_SPEC, TEST_SPEC):
            names = [e.name for e in spec.evidence_checks]
            self.assertNotIn("orchestrator_posture", names)


if __name__ == "__main__":
    unittest.main()
