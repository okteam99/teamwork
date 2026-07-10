#!/usr/bin/env python3
"""v8.215→v8.216 · 智能分诊:clarity 仅证据记录 · 评审配置动态化(roster 路由 · 无硬编码)。

用户裁决(v8.216):--clarity 硬编码消费太规则化 —— 该动态决策 · 可去 pl 也可去 qa/architect。
机制 = stage_review_roles(既有)· gate 按 roster 放行 · change-review-roles 审计留痕。
"""
from __future__ import annotations
import sys, unittest
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _v8_stage_specs as S  # noqa: E402


class TestDynamicRoster(unittest.TestCase):
    def test_clarity_alone_does_not_skip_pl(self):
        # v8.216:clarity=explicit 不再硬编码跳过 —— pl 在 roster 里就照拦
        st = {"clarity": "explicit", "stage_review_roles": {"goal": ["pl"]}}
        ok, _ = S._evidence_pl_challenge_present(st, NS(feature="/nonexistent"))
        self.assertFalse(ok)

    def test_roster_without_pl_skips(self):
        # 动态路由:AI 判 pl 无值 → roster 去 pl → gate 放行(clarity 无关)
        st = {"clarity": "normal", "stage_review_roles": {"goal": ["qa", "architect"]}}
        ok, _ = S._evidence_pl_challenge_present(st, NS(feature="/nonexistent"))
        self.assertTrue(ok)

    def test_clarity_alone_does_not_skip_external(self):
        st = {"clarity": "explicit", "current_stage": "blueprint",
              "stage_review_roles": {"blueprint": ["architect", "external"]}}
        ok, msg = S._evidence_external_review_artifact(st, NS(feature="/nonexistent"))
        self.assertFalse(ok and "explicit" in (msg or ""))

    def test_roster_without_external_skips(self):
        st = {"current_stage": "blueprint",
              "stage_review_roles": {"blueprint": ["architect"]}}
        ok, msg = S._evidence_external_review_artifact(st, NS(feature="/nonexistent"))
        self.assertTrue(ok)
        self.assertIn("stage_review_roles", msg)

if __name__ == "__main__":
    unittest.main()
