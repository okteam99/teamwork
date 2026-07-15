"""v8.243:goal 冷审 3→2 路并行(PL 对抗质疑 + 覆盖方向制外审)。

QA 可验证 / ARCH 可实现并入外审必覆盖方向 + AI 自主方向 ≥1;
coverage 申报物化(对称 pl_challenge_present)· roster 可加回独立 qa/architect。
"""
import argparse
import tempfile
import unittest
from pathlib import Path

import _v8_engine as engine
import _v8_stage_specs as specs


def _args(feature_dir: str) -> argparse.Namespace:
    return argparse.Namespace(feature=feature_dir)


class TestGoalDefaultRosterTwoLane(unittest.TestCase):
    def test_feature_goal_default_is_pl_external(self):
        roles = engine.build_default_stage_review_roles("Feature")
        self.assertEqual(roles["goal"], ["pl", "external"])

    def test_legacy_agile_goal_untouched(self):
        roles = engine.build_default_stage_review_roles("敏捷需求")
        self.assertEqual(roles["goal"], ["qa", "pl"])


class TestExternalCoveragePresent(unittest.TestCase):
    def test_roster_without_external_auto_pass(self):
        state = {"stage_review_roles": {"goal": ["pl"]}}
        ok, _ = specs._evidence_external_coverage_present(state, _args("/nonexistent"))
        self.assertTrue(ok)

    def test_missing_review_file_fails(self):
        with tempfile.TemporaryDirectory() as d:
            state = {"stage_review_roles": {"goal": ["pl", "external"]}}
            ok, msg = specs._evidence_external_coverage_present(state, _args(d))
            self.assertFalse(ok)
            self.assertIn("不存在", msg)

    def test_review_without_coverage_fails(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "PRD-REVIEW.md").write_text(
                "---\nreviewers: [pl, external]\n---\n泛泛而谈一段", encoding="utf-8")
            state = {"stage_review_roles": {"goal": ["pl", "external"]}}
            ok, msg = specs._evidence_external_coverage_present(state, _args(d))
            self.assertFalse(ok)
            self.assertIn("coverage", msg)
            self.assertIn("可实现", msg)  # hint 教做法

    def test_review_with_coverage_passes(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "PRD-REVIEW.md").write_text(
                "---\nreviewers: [pl, external]\n"
                "reviews:\n - role: external\n coverage: [可实现, 可验证, 数据一致性]\n---\n",
                encoding="utf-8")
            state = {"stage_review_roles": {"goal": ["pl", "external"]}}
            ok, _ = specs._evidence_external_coverage_present(state, _args(d))
            self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
