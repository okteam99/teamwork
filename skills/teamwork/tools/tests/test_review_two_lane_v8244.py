"""v8.244:blueprint/review 冷审 3→2 路并行(Architect 主审 + 覆盖方向制外审)。

QA 视角并入外审必覆盖方向(blueprint 可测试 · review 测试真实性/从严清单);
coverage 申报物化(external-cross-review 文件)· roster 可加回独立 qa。
"""
import argparse
import tempfile
import unittest
from pathlib import Path

import _v8_engine as engine
import _v8_stage_specs as specs


def _args(feature_dir: str) -> argparse.Namespace:
    return argparse.Namespace(feature=feature_dir)


class TestTwoLaneDefaults(unittest.TestCase):
    def test_feature_blueprint_default(self):
        roles = engine.build_default_stage_review_roles("Feature")
        self.assertEqual(roles["blueprint"], ["architect", "external"])

    def test_feature_review_default(self):
        roles = engine.build_default_stage_review_roles("Feature")
        self.assertEqual(roles["review"], ["architect", "external"])

    def test_bug_review_default(self):
        roles = engine.build_default_stage_review_roles("Bug")
        self.assertEqual(roles["review"], ["architect", "external"])

    def test_legacy_agile_review_untouched(self):
        roles = engine.build_default_stage_review_roles("敏捷需求")
        self.assertEqual(roles["review"], ["architect", "qa"])


class TestCrossReviewCoverage(unittest.TestCase):
    def _state(self, stage: str, roles: list) -> dict:
        return {"current_stage": stage, "stage_review_roles": {stage: roles}}

    def test_roster_without_external_auto_pass(self):
        ok, _ = specs._evidence_cross_review_coverage(
            self._state("review", ["architect"]), _args("/nonexistent"))
        self.assertTrue(ok)

    def test_no_artifacts_fails(self):
        with tempfile.TemporaryDirectory() as d:
            ok, msg = specs._evidence_cross_review_coverage(
                self._state("blueprint", ["architect", "external"]), _args(d))
            self.assertFalse(ok)
            self.assertIn("无产物", msg)

    def test_artifact_without_coverage_fails_with_stage_hint(self):
        with tempfile.TemporaryDirectory() as d:
            cr = Path(d) / "external-cross-review"; cr.mkdir()
            (cr / "review-subagent.md").write_text(
                "---\nreview_via: subagent\n---\n泛泛而谈", encoding="utf-8")
            ok, msg = specs._evidence_cross_review_coverage(
                self._state("review", ["architect", "external"]), _args(d))
            self.assertFalse(ok)
            self.assertIn("测试真实性", msg)  # review 从严清单出现在 hint

    def test_artifact_with_coverage_passes(self):
        with tempfile.TemporaryDirectory() as d:
            cr = Path(d) / "external-cross-review"; cr.mkdir()
            (cr / "blueprint-subagent.md").write_text(
                "---\nreview_via: subagent\ncoverage: [可测试, 方案盲区, 迁移风险]\n---\n",
                encoding="utf-8")
            ok, msg = specs._evidence_cross_review_coverage(
                self._state("blueprint", ["architect", "external"]), _args(d))
            self.assertTrue(ok, msg)


if __name__ == "__main__":
    unittest.main()
