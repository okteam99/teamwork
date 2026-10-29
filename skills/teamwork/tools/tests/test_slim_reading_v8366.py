#!/usr/bin/env python3
"""v8.366 · 提效方案第 3 批:读取分层 · 文档单一权威 · 评审不凑数。"""
from __future__ import annotations
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class TestReadingTiers(unittest.TestCase):
    def test_skill_has_three_tiers(self):
        s = _read("SKILL.md")
        self.assertIn("## 读取分层", s)
        for layer in ("| 入口 |", "| 当前阶段 |", "| 参考 |"):
            self.assertIn(layer, s)

    def test_prepare_minimal_path_not_upfront_must_read(self):
        s = _read("docs/prepare.md")
        self.assertIn("**最小路径**", s)
        self.assertNotIn("Must-read(PMO 进 prepare 前必读)", s)


class TestSingleAuthority(unittest.TestCase):
    def test_tech_does_not_copy_tc_table(self):
        s = _read("templates/tech.md")
        self.assertNotIn("| TC 用例 | 测试方法名 | 状态 |", s)
        self.assertIn("单一权威", s)


class TestReviewNoQuota(unittest.TestCase):
    def test_no_reason_quota_in_review_docs(self):
        for rel in ("SKILL.md", "stages/goal-stage.md", "stages/blueprint-stage.md",
                    "stages/review-stage.md", "claude-agents/reviewer.md"):
            t = _read(rel)
            self.assertNotIn("无 + 为什么没有", t, rel)
            self.assertNotIn("无实质质疑 + 理由", t, rel)

    def test_premise_first(self):
        self.assertIn("评审先核验关键前提", _read("SKILL.md"))


if __name__ == "__main__":
    unittest.main()
