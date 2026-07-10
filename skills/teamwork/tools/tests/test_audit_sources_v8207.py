#!/usr/bin/env python3
"""v8.207 · ship-finalize 在 worktree-remove 前预抽 REVIEW/TEST 源材料入 audit 草稿。

治本(实证 case):audit 三段判断需 REVIEW.md/TEST-REPORT.md · 但 ship2 先删 worktree 再要 AI
补三段 → 源只剩 zip 内 → AI 被迫 unzip 反读。改:worktree 删前抓摘录嵌草稿 · AI 读草稿即填。
"""
from __future__ import annotations
import json, os, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _v8_ship import _capture_audit_sources, _write_audit_record  # noqa: E402


class TestCaptureSources(unittest.TestCase):
    def _feat(self):
        d = Path(tempfile.mkdtemp(prefix="aud-"))
        (d / "REVIEW.md").write_text(
            "---\nreviewers: [architect, qa, external]\nverdict: APPROVE\n---\nCR-1 secret 丢失", encoding="utf-8")
        (d / "REVIEW-arch.md").write_text("架构视角:路由绕过 leave guard", encoding="utf-8")
        (d / "TEST-REPORT.md").write_text("AC 11/11 · 119 tests pass", encoding="utf-8")
        return d

    def test_captures_review_and_test(self):
        src = _capture_audit_sources(self._feat())
        self.assertIn("CR-1 secret", src)          # REVIEW.md
        self.assertIn("路由绕过", src)              # REVIEW-arch.md(glob REVIEW*)
        self.assertIn("11/11", src)                # TEST-REPORT.md

    def test_missing_dir_returns_empty(self):
        self.assertEqual(_capture_audit_sources(Path("/nonexistent/xyz")), "")

    def test_embedded_into_draft_and_pointer(self):
        src = _capture_audit_sources(self._feat())
        home = tempfile.mkdtemp(); os.environ["HOME"] = home
        rec = _write_audit_record(
            {"feature_id": "F1", "completed_stages": ["dev"], "flow_type": "Feature"},
            "F1", "staging", str(self._feat()), None, src)
        body = Path(rec).read_text(encoding="utf-8")
        self.assertIn("## 源材料摘录", body)        # 段存在
        self.assertIn("CR-1 secret", body)          # 源嵌入
        self.assertIn("无需 unzip", body)           # 三段指向摘录 · 不 unzip

    def test_no_sources_no_section(self):
        home = tempfile.mkdtemp(); os.environ["HOME"] = home
        rec = _write_audit_record(
            {"feature_id": "F2", "completed_stages": [], "flow_type": "Bug"},
            "F2", "dev", str(tempfile.mkdtemp()), None, "")
        body = Path(rec).read_text(encoding="utf-8")
        self.assertNotIn("## 源材料摘录", body)      # 无源 → 不加空段(占位注释里的字样不算)
        self.assertIn("## 做的好的", body)           # 三段仍在

if __name__ == "__main__":
    unittest.main()
