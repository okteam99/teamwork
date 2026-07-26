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


class TestReviewRoleCoverageRosterAware(unittest.TestCase):
    """v8.241 roster-aware 语义 · v8.289 机制换代:REVIEW-<role>.md 文件存在 → REVIEW.md coverage 申报。

    换代理由:旧门禁只查文件存在不解析内容,而角色归属早在 findings[].source;
    实测 REVIEW-arch 与 REVIEW.md 体量几乎相同 = 同一批判断写两遍。
    保住的性质不变 —— 「我确实看过、看了这些」的物证(防橡皮图章)+ roster 移出不查。
    """

    @staticmethod
    def _review(d, body):
        (Path(d) / "REVIEW.md").write_text(body, encoding="utf-8")

    def test_roster_without_arch_skips_arch(self):
        with tempfile.TemporaryDirectory() as d:
            self._review(d, "coverage: [qa 测试真实性]")
            state = {"stage_review_roles": {"review": ["qa", "external"]}}
            ok, msg = specs._evidence_review_role_coverage(state, _args(d))
            self.assertTrue(ok, msg)
            self.assertIn("qa", msg)          # 只查 roster 内的主审角色

    def test_roster_role_missing_declaration_fails(self):
        with tempfile.TemporaryDirectory() as d:
            self._review(d, "coverage: [qa 测试真实性]")   # 缺 architect 申报
            state = {"stage_review_roles": {"review": ["architect", "qa"]}}
            ok, msg = specs._evidence_review_role_coverage(state, _args(d))
            self.assertFalse(ok)
            self.assertIn("architect", msg)

    def test_declaration_accepted_in_line_form(self):
        """申报形式宽松:`coverage: …architect…` 或 `architect 覆盖/查过/视角:` 都算。"""
        with tempfile.TemporaryDirectory() as d:
            self._review(d, "- architect 覆盖:实现↔设计一致性 · 查过无发现\n- qa 查过:测试真实性")
            state = {"stage_review_roles": {"review": ["architect", "qa"]}}
            ok, msg = specs._evidence_review_role_coverage(state, _args(d))
            self.assertTrue(ok, msg)

    def test_legacy_state_without_roster_skips(self):
        """legacy state 无 roster → 跳过(不对存量加严 · v8.289 与旧行为的有意差异)。"""
        with tempfile.TemporaryDirectory() as d:
            ok, msg = specs._evidence_review_role_coverage({}, _args(d))
            self.assertTrue(ok, msg)

    def test_empty_roster_checks_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            state = {"stage_review_roles": {"review": []}}
            ok, msg = specs._evidence_review_role_coverage(state, _args(d))
            self.assertTrue(ok, msg)

    def test_external_only_roster_needs_no_main_declaration(self):
        """Bug 流默认 roster=[external] · 主审路为空 → 无需申报(external 走自己的 coverage 物化门)。"""
        with tempfile.TemporaryDirectory() as d:
            state = {"stage_review_roles": {"review": ["external"]}}
            ok, msg = specs._evidence_review_role_coverage(state, _args(d))
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
