"""开发规范收形:方法论不设限 · 兜底白名单 + 收口自查表 · 读取契约(用户拍板)。

拍板:「进一步降低对模型的限制,告诉他需要开发,不需要强制 TDD 等;有一个兜底的
规范和自查项列表即可(例:异常分支必须打 log、DB 字段改动需充分论证);需要读
各项目自己的开发和架构规范 + teamwork 兜底的开发和架构规范。」

盘点结论:TDD 强制早已撤除、HARD-RULES 已是兜底白名单 —— 本版补三块:
①收口自查表(HARD-RULES §三 · 判断题不设机器门)②ARCHITECTURE 升必读
③「方法论不设限」总纲(dev-stage 1.5 + brief 动作点)。
"""
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

HARD = SKILL_ROOT / "standards" / "tech-rules.md"  # v8.331:HARD-RULES 并入 tech-rules
DEV = SKILL_ROOT / "stages" / "dev-stage.md"


class TestClosingChecklist(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = HARD.read_text(encoding="utf-8")
        cls.doc = doc
        cls.sec = doc.split("收口自查表", 1)[1].split("## 相关")[0]

    def test_checklist_exists_as_slots(self):
        """槽位式自查项(载体形状决定内容会不会出现)· ≥6 项 checkbox。"""
        self.assertGreaterEqual(self.sec.count("- [ ]"), 6)

    def test_user_named_examples_present(self):
        self.assertIn("异常/降级分支都有日志", self.sec)
        self.assertIn("DB 字段/表结构改动已充分论证", self.sec)

    def test_checklist_is_judgment_not_gate(self):
        self.assertIn("不设机器门", self.sec)

    def test_methodology_freedom_declared_at_checklist(self):
        self.assertIn("全由 AI 自定,框架不设限", self.sec)

    def test_existing_whitelist_untouched(self):
        """兜底白名单本体不动:逆默认/不可知收录判据与日志规则仍在。"""
        self.assertIn("与模型默认行为的距离", self.doc)
        self.assertIn("必打 WARN 日志", self.doc)
        self.assertIn("怎么测由 AI 自觉", self.doc)


class TestReadingContract(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = DEV.read_text(encoding="utf-8")

    def test_architecture_promoted_to_must_read(self):
        rule1 = self.doc.split("读取契约", 1)[1].split("\n2. ")[0]
        self.assertIn("ARCHITECTURE.md", rule1)
        self.assertIn("升必读", rule1)
        self.assertIn("冲突以项目为准", self.doc)

    def test_charter_rule_exists(self):
        self.assertIn("方法论不设限(总纲)", self.doc)
        seg = self.doc.split("方法论不设限(总纲)", 1)[1].split("\n2. ")[0]
        self.assertIn("框架不规定手段", seg)
        self.assertIn("注意力税", seg)
        for kept in ("读取契约", "收口自查表", "结果证据门"):
            self.assertIn(kept, seg)                       # 只收三样 · 逐样点名

    def test_dual_checklist_at_completion(self):
        self.assertIn("完工自查双源", self.doc)
        self.assertIn("收口自查表", self.doc)
        self.assertIn("兜底裸奔", self.doc)

    def test_context_entry_lists_architecture(self):
        entry = self.doc.split("上下文入口", 1)[1]
        self.assertIn("DEV-RULES + ARCHITECTURE 必读", entry)


class TestRuntimeBrief(unittest.TestCase):

    def test_dev_brief_carries_charter_and_checklist(self):
        from _v8_stage_specs import DEV_SPEC
        brief = DEV_SPEC.brief_template_fn({})
        self.assertIn("方法论不设限", brief)
        self.assertIn("收口自查表", brief)
        self.assertIn("冲突以项目为准", brief)
        self.assertIn("ARCHITECTURE", brief)

    def test_no_new_machine_gate(self):
        """自查是判断题 —— DEV_SPEC evidence/artifacts 不因本版增门。"""
        from _v8_stage_specs import DEV_SPEC
        names = [e.name for e in DEV_SPEC.evidence_checks]
        self.assertNotIn("closing_checklist", names)


if __name__ == "__main__":
    unittest.main()
