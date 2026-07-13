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


class TestTriageCalibrationV8217(unittest.TestCase):
    def test_calibration_bundle(self):
        import tempfile, subprocess
        from _v8_ship import _triage_calibration
        d = Path(tempfile.mkdtemp())
        subprocess.run(["git", "-C", str(d), "init", "-q", "-b", "main"], capture_output=True)
        st = {"clarity": "explicit",
              "stage_review_roles_adjustments": [{"stage": "goal", "roles": ["qa"], "reason": "机械类"}],
              "stage_contracts": {"goal": {"rounds": []}, "review": {"rounds": [{"round": 1}]}}}
        c = _triage_calibration(st, str(d), "main")
        self.assertEqual(c["clarity"], "explicit")
        self.assertIn("goal→qa", c["roster"])
        self.assertEqual(c["goal_rounds"], 0)
        self.assertEqual(c["review_rounds"], 1)

    def test_default_roster_label(self):
        from _v8_ship import _triage_calibration
        c = _triage_calibration({}, "/nonexistent", "main")
        self.assertEqual(c["roster"], "默认矩阵")
        self.assertEqual(c["clarity"], "normal")


class TestDispatchModelsV8231(unittest.TestCase):
    def test_distribution_and_unspecified(self):
        import tempfile
        from _v8_ship import _dispatch_model_distribution
        d = Path(tempfile.mkdtemp()); dl = d / "dispatch_log"; dl.mkdir()
        (dl / "001-qa.md").write_text("- model: sonnet\n", encoding="utf-8")
        (dl / "002-pl.md").write_text("task only\n", encoding="utf-8")
        (dl / "INDEX.md").write_text("| i |\n", encoding="utf-8")
        dist = _dispatch_model_distribution(d)
        self.assertEqual(dist.get("sonnet"), 1)
        self.assertEqual(dist.get("unspecified(继承会话)"), 1)   # 未分档信号
        self.assertNotIn("INDEX", str(dist))
        self.assertEqual(_dispatch_model_distribution(Path(tempfile.mkdtemp())), {})

    def test_in_calibration_bundle(self):
        import tempfile, subprocess
        from _v8_ship import _triage_calibration
        d = Path(tempfile.mkdtemp())
        subprocess.run(["git", "-C", str(d), "init", "-q", "-b", "main"], capture_output=True)
        dl = d / "dispatch_log"; dl.mkdir()
        (dl / "001.md").write_text("model: haiku\n", encoding="utf-8")
        c = _triage_calibration({"artifact_root": str(d)}, str(d), "main")
        self.assertEqual(c["dispatch_models"], {"haiku": 1})
