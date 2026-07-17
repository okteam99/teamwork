"""v8.260/261:fast mode —— 评审收敛为两端单路(localconfig `fast_mode: true` · 默认关)。

v8.261 语义:goal 留单路合并冷审(PL+外审 · PRD-REVIEW 必产)· review 留单路合并评审
(Architect+QA · REVIEW.md 单份 · 协议照跑)· blueprint 评审去(TECH-REVIEW 不产)。与 yolo 互斥。
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
    def test_dev_goes_review_even_in_fast(self):
        # v8.261:fast 不再跳 review(留单路合并代码评审)
        self.assertEqual(S._dev_transition({"fast_mode": True}), "review")
        self.assertEqual(S._dev_transition({}), "review")

    def test_graph_has_no_fast_skip_edge(self):
        for g in (ST.FEATURE_FLOW, ST.AGILE_FLOW, ST.BUG_FLOW):
            self.assertEqual(g["dev"], ["review"])

    def test_review_approved_prereq_not_bypassed(self):
        # v8.261:review 照走 · fast 不豁免 test 前置
        self.assertFalse(S._check_review_approved({"fast_mode": True}, None))


class TestFastModeGatesAndArtifacts(unittest.TestCase):
    def test_prd_verdicts_enforced_in_fast(self):
        # v8.261:PRD-REVIEW 恢复必产必查(单路合并冷审 · verdicts {fast: APPROVE})
        import argparse
        with tempfile.TemporaryDirectory() as t:
            ok, msg = S._evidence_prd_verdicts_all_pass(
                {"fast_mode": True}, argparse.Namespace(feature=t, verdict=None))
            self.assertFalse(ok)
            self.assertIn("PRD-REVIEW.md 不存在", msg)

    def test_review_artifacts_flags(self):
        prd_rev = next(a for a in S.GOAL_SPEC.artifacts if a.path == "PRD-REVIEW.md")
        tech_rev = next(a for a in S.BLUEPRINT_SPEC.artifacts if a.path == "TECH-REVIEW.md")
        self.assertFalse(prd_rev.review_artifact)   # v8.261:fast 亦必产
        self.assertTrue(tech_rev.review_artifact)   # blueprint 评审仍去 · fast 不产不查

    def test_fast_briefs_carry_merged_mandates(self):
        gb = S._goal_brief({"fast_mode": True})
        self.assertIn("单路合并冷审", gb); self.assertIn("质疑六问", gb); self.assertIn("可实现", gb)
        rb = S._review_brief({"fast_mode": True})
        self.assertIn("单路合并评审", rb); self.assertIn("一致性", rb); self.assertIn("测试真实性", rb)


if __name__ == "__main__":
    unittest.main()
