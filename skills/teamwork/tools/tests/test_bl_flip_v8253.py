"""v8.253:ship archive 翻牌验收门 —— state.bl 的 ROADMAP 行状态须已翻完成态。

case:S1 ship 漏翻 ROADMAP 状态格 → ws-progress 误报 0/4 · ready_to_start 失真 · 人工查账才发现。
--planning-artifacts 是自由声明 · 本门验「声明的翻牌真的翻了」。
"""
import tempfile
import unittest
from pathlib import Path

import _v8_ship as ship

_HDR = ("| Feature ID | 功能名称 | 状态 | 当前阶段 | 对应 F编号 | 关联 WS |\n"
        "|---|---|---|---|---|---|\n")


def _roadmap(root: Path, rel: str, rows: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# RM\n" + _HDR + rows, encoding="utf-8")


class TestCheckBlFlipped(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)

    def tearDown(self):
        self._td.cleanup()

    def test_no_bl_skips(self):
        r = ship._check_bl_flipped(str(self.root), {})
        self.assertEqual(r["status"], "skip")

    def test_row_absent_skips(self):
        _roadmap(self.root, "docs/ROADMAP.md", "| BL-002 | x | 待开始 | - | - | WS-01 |\n")
        r = ship._check_bl_flipped(str(self.root), {"bl": "BL-001"})
        self.assertEqual(r["status"], "skip")

    def test_not_flipped_caught(self):
        _roadmap(self.root, "docs/ROADMAP.md", "| BL-001 | x | 待开始 | - | - | WS-01 |\n")
        r = ship._check_bl_flipped(str(self.root), {"bl": "BL-001"})
        self.assertEqual(r["status"], "not_flipped")
        self.assertEqual(r["rows"][0]["status"], "待开始")

    def test_delivered_alias_counts_flipped(self):
        # v8.252 词表复用:「✅ 已交付」= 完成态
        _roadmap(self.root, "docs/ROADMAP.md", "| BL-001 | x | ✅ 已交付 | - | F-9 | WS-01 |\n")
        r = ship._check_bl_flipped(str(self.root), {"bl": "BL-001"})
        self.assertEqual(r["status"], "flipped")

    def test_worktree_stale_copy_ignored(self):
        # 主树未翻 · .worktree 旧副本已翻 → 仍判 not_flipped(v8.252 _ws_scan_ok 复用)
        _roadmap(self.root, "docs/ROADMAP.md", "| BL-001 | x | 待开始 | - | - | WS-01 |\n")
        _roadmap(self.root, ".worktree/OLD-F1/docs/ROADMAP.md",
                 "| BL-001 | x | 已完成 | - | - | WS-01 |\n")
        r = ship._check_bl_flipped(str(self.root), {"bl": "BL-001"})
        self.assertEqual(r["status"], "not_flipped")

    def test_substring_fake_done_not_flipped(self):
        # 「基本已完成，待测试」起始词非完成态 → 不算翻
        _roadmap(self.root, "docs/ROADMAP.md", "| BL-001 | x | 基本已完成，待测试 | - | - | WS-01 |\n")
        r = ship._check_bl_flipped(str(self.root), {"bl": "BL-001"})
        self.assertEqual(r["status"], "not_flipped")


if __name__ == "__main__":
    unittest.main()
