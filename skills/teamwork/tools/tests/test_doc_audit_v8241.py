"""v8.241 全库文档审计的两处工具侧修复。

1. REVIEW-arch/REVIEW-qa roster-aware(治「角色按 roster 可调」承诺与静态必查门禁互斥)。
2. close-unmerged 可从任意 stage 走(治 pm_acceptance rejected「放弃 Feature」选项死路)。
"""
import argparse
import tempfile
import unittest
from pathlib import Path

import _v8_stage_specs as specs
import _v8_ship as ship


def _args(feature_dir: str) -> argparse.Namespace:
    return argparse.Namespace(feature=feature_dir)


class TestReviewRoleArtifactsRosterAware(unittest.TestCase):
    def test_roster_without_arch_skips_arch_artifact(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "REVIEW-qa.md").write_text("# qa", encoding="utf-8")
            state = {"stage_review_roles": {"review": ["qa", "external"]}}
            ok, msg = specs._evidence_review_role_artifacts(state, _args(d))
            self.assertTrue(ok, msg)
            self.assertIn("REVIEW-qa.md", msg)

    def test_roster_role_missing_artifact_fails(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "REVIEW-qa.md").write_text("# qa", encoding="utf-8")
            state = {"stage_review_roles": {"review": ["architect", "qa"]}}
            ok, msg = specs._evidence_review_role_artifacts(state, _args(d))
            self.assertFalse(ok)
            self.assertIn("REVIEW-arch.md", msg)

    def test_legacy_state_without_roster_checks_both(self):
        with tempfile.TemporaryDirectory() as d:
            state = {}  # legacy:无 stage_review_roles → 按旧行为全查
            ok, msg = specs._evidence_review_role_artifacts(state, _args(d))
            self.assertFalse(ok)
            self.assertIn("REVIEW-arch.md", msg)
            self.assertIn("REVIEW-qa.md", msg)

    def test_empty_roster_checks_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            state = {"stage_review_roles": {"review": []}}
            ok, msg = specs._evidence_review_role_artifacts(state, _args(d))
            self.assertTrue(ok, msg)


class TestCloseUnmergedFromAnyStage(unittest.TestCase):
    def test_close_unmerged_allowed_from_pm_acceptance(self):
        # v8.241 前:current_stage=pm_acceptance → emit FAIL + SystemExit(死路)
        state = {"current_stage": "pm_acceptance", "ship": {}}
        self.assertIsNone(ship._require_ship_stage(state, "close-unmerged"))

    def test_other_actions_still_require_ship(self):
        state = {"current_stage": "pm_acceptance", "ship": {}}
        with self.assertRaises(SystemExit):
            ship._require_ship_stage(state, "sanitize")


if __name__ == "__main__":
    unittest.main()
