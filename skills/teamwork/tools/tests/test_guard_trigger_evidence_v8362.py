"""守卫清单:「只在绕过时变」必须给触发路径证据(用户拍板)。

起因:守卫表写「只在绕过正常写接口直接写 SQL 时变」+「低概率」,谁会直写从没指出 ——
AI 想象一条绕过路径就能让守卫立得住。判据:指不出现存绕过入口或坏数据已出现的证据 = 当「不变」删。
"""
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]


def _read(rel):
    return (SKILL_ROOT / rel).read_text(encoding="utf-8")


class TestTechTemplate(unittest.TestCase):

    def test_table_has_evidence_column(self):
        t = _read("templates/tech.md")
        self.assertIn("| 🔴 删了行为会变吗 | 🔴 触发路径证据 |", t)

    def test_no_evidence_means_delete(self):
        t = _read("templates/tech.md")
        self.assertIn("指不出证据 = 按「不变」处理,直接删", t)
        self.assertIn("「将来可能有人绕过」「理论上可能」不是证据", t)

    def test_imagined_future_bypass_example_removed(self):
        self.assertNotIn("将来绕过 service 的函数", _read("templates/tech.md"))

    def test_probability_grounded_in_evidence(self):
        self.assertIn("概率以「触发路径证据」为准", _read("templates/tech.md"))


class TestBlueprintStage(unittest.TestCase):

    def test_drafting_rule_requires_evidence(self):
        t = _read("stages/blueprint-stage.md")
        self.assertIn("必给触发路径证据", t)

    def test_confirm_card_carries_evidence_column(self):
        t = _read("stages/blueprint-stage.md")
        self.assertIn("「触发路径证据」列", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
