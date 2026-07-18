"""v8.273:审核员只审内容 · 不重复跑测试脚本(静态审读 · 测试执行归 dev/test 硬门)。"""
import unittest

import _v8_stage_specs as S


class TestReviewContentOnly(unittest.TestCase):
    def test_round1_brief_carries_no_rerun_rule(self):
        self.assertIn("不重复跑测试脚本", S._review_brief({}))

    def test_verify_round_brief_carries_no_rerun_rule(self):
        vb = S._review_brief({"stage_contracts": {"review": {
            "rounds": [{"round": 1}, {"round": 2}], "findings_ledger": []}}})
        self.assertIn("不重复跑测试脚本", vb)

    def test_coverage_hint_disambiguates_test_really_ran(self):
        self.assertIn("非评审自己重跑", S._CROSS_REVIEW_COVERAGE_HINTS["review"])
