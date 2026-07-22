"""v8.278:给 dev 装 goal 已验证的 shift-left —— 复发 finding 类沉淀 + dev 起草写时防。

诊断(aon-core):findings 82% 真实、集中 code review、反复撞同类(stale×7/timeout×6)·
沉淀回路断(DEV-RULES=0)。闭环:review 收敛→复发类进 KNOWLEDGE §复发防御清单→dev 起草必读照写。
"""
import unittest
from pathlib import Path

import _v8_stage_specs as S

ROOT = Path(__file__).resolve().parent.parent.parent


class TestDevShiftLeft(unittest.TestCase):
    def test_knowledge_template_has_defense_list(self):
        tpl = (ROOT / "templates" / "knowledge.md").read_text(encoding="utf-8")
        self.assertIn("复发防御清单", tpl)
        self.assertIn("写时防", tpl)

    def test_dev_brief_surfaces_defense_list(self):
        b = S._dev_brief({})
        self.assertIn("复发防御清单", b)
        self.assertIn("写时防", b)

    def test_dev_stage_has_authoring_discipline(self):
        d = (ROOT / "stages" / "dev-stage.md").read_text(encoding="utf-8")
        self.assertIn("复发防御清单", d)
        self.assertIn("起草思考规范", d)

    def test_review_stage_has_harvest_step(self):
        r = (ROOT / "stages" / "review-stage.md").read_text(encoding="utf-8")
        self.assertIn("复发防御沉淀", r)

    def test_verify_round_brief_carries_harvest(self):
        vb = S._review_brief({"stage_contracts": {"review": {
            "rounds": [{"round": 1}, {"round": 2}], "findings_ledger": []}}})
        self.assertIn("复发防御清单", vb)

    def test_round1_brief_no_harvest_pollution(self):
        # harvest 提醒挂验证轮(收敛时刻)· round-1 不必带
        b = S._review_brief({})
        self.assertNotIn("复发防御清单", b)
