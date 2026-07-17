"""v8.260:fast mode —— 去掉所有评审环节(localconfig `fast_mode: true` · 默认关)。

去:goal 冷审(PRD-REVIEW)· blueprint 评审(TECH-REVIEW)· 整个 review stage(dev 直进 test)。
留:测试硬门 · 用户暂停点 · worktree 纪律。与 yolo 互斥。
"""
import json
import tempfile
import unittest
from pathlib import Path

import _v8_engine as E
import _v8_stage_specs as S
import state as ST


class TestFastModeReader(unittest.TestCase):
    def test_default_off(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / ".git").mkdir()
            self.assertFalse(ST._read_fast_mode(t))

    def test_explicit_true_on(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / ".git").mkdir()
            (Path(t) / ".teamwork_localconfig.json").write_text(
                json.dumps({"fast_mode": True}), encoding="utf-8")
            self.assertTrue(ST._read_fast_mode(t))

    def test_explicit_false_off(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / ".git").mkdir()
            (Path(t) / ".teamwork_localconfig.json").write_text(
                json.dumps({"fast_mode": False}), encoding="utf-8")
            self.assertFalse(ST._read_fast_mode(t))


class TestFastModeTransitions(unittest.TestCase):
    def test_dev_skips_review(self):
        self.assertEqual(S._dev_transition({"fast_mode": True}), "test")
        self.assertEqual(S._dev_transition({}), "review")

    def test_graph_edge_legal(self):
        # fast 跳 review 的 dev→test 转移在三条链图里合法
        for g in (ST.FEATURE_FLOW, ST.AGILE_FLOW, ST.BUG_FLOW):
            self.assertIn("test", g["dev"])

    def test_review_approved_prereq_skips(self):
        self.assertTrue(S._check_review_approved({"fast_mode": True}, None))
        self.assertFalse(S._check_review_approved({}, None))


class TestFastModeGatesAndArtifacts(unittest.TestCase):
    def test_prd_verdicts_skipped(self):
        import argparse
        with tempfile.TemporaryDirectory() as t:
            ok, msg = S._evidence_prd_verdicts_all_pass(
                {"fast_mode": True}, argparse.Namespace(feature=t, verdict=None))
            self.assertTrue(ok)
            self.assertIn("fast_mode", msg)

    def test_review_artifacts_flagged(self):
        prd_rev = next(a for a in S.GOAL_SPEC.artifacts if a.path == "PRD-REVIEW.md")
        tech_rev = next(a for a in S.BLUEPRINT_SPEC.artifacts if a.path == "TECH-REVIEW.md")
        self.assertTrue(prd_rev.review_artifact)
        self.assertTrue(tech_rev.review_artifact)
        prd = next(a for a in S.GOAL_SPEC.artifacts if a.path == "PRD.md")
        self.assertFalse(prd.review_artifact)  # 非评审产物不豁免


if __name__ == "__main__":
    unittest.main()
