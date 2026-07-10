#!/usr/bin/env python3
"""v8.215 · 智能分诊 v1:clarity 维度(明确度)→ 评审强度比例化。

治本(i18n case):「大而明确」的需求走全重流程 —— 车道把「大」和「不确定」绑死。
clarity 解耦:explicit → goal PL 质疑跳过 + blueprint external 跳过;review 不动。
"""
from __future__ import annotations
import sys, unittest
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _v8_stage_specs as S  # noqa: E402


class TestClarityGates(unittest.TestCase):
    def test_pl_challenge_skipped_when_explicit(self):
        st = {"clarity": "explicit", "stage_review_roles": {"goal": ["qa", "architect", "pl"]}}
        ok, msg = S._evidence_pl_challenge_present(st, NS(feature="/nonexistent"))
        self.assertTrue(ok)
        self.assertIn("explicit", msg)

    def test_pl_challenge_enforced_when_normal(self):
        st = {"clarity": "normal", "stage_review_roles": {"goal": ["pl"]}}
        ok, _ = S._evidence_pl_challenge_present(st, NS(feature="/nonexistent"))
        self.assertFalse(ok)   # PRD-REVIEW 不存在 → 照常拦

    def test_blueprint_external_skipped_when_explicit(self):
        st = {"clarity": "explicit", "current_stage": "blueprint"}
        ok, msg = S._evidence_external_review_artifact(st, NS(feature="/nonexistent"))
        self.assertTrue(ok)
        self.assertIn("explicit", msg)

    def test_review_external_not_affected_by_clarity(self):
        # 🔴 review 三视角不受 clarity 影响(拦真主力)
        st = {"clarity": "explicit", "current_stage": "review"}
        ok, msg = S._evidence_external_review_artifact(st, NS(feature="/nonexistent"))
        self.assertFalse(ok or "explicit" in (msg or ""))

if __name__ == "__main__":
    unittest.main()
