#!/usr/bin/env python3
"""ws-progress 扫描域与状态词表回归套件。

实战 case(WS-19):① 主工作区跑 ws-progress --write · 文件被写进并行 feature 的
.worktree/ 旧副本(rglob 未排除 .worktree + 无序取首)· verdict 却 OK;② ROADMAP 用
「✅ 已交付」被词表(只认 已完成/进行中/已取消)判成待开始 → 进度 0/N 假象 ·
ready_to_start 失灵;③ 词表外写法静默吞 · 无任何 surface。

运行:python3 -m pytest skills/teamwork/tools/tests/test_ws_scan_vocab.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
STATE_PY = TOOLS / "state.py"
sys.path.insert(0, str(TOOLS))

from state import _find_ws_file, _ws_scan_ok, _ws_status_bucket  # noqa: E402

_HEADER = ("| Feature ID | 功能名称 | 优先级 | 依赖 | 状态 | 当前阶段 | 对应 F编号 | 关联 WS |\n"
           "|---|---|---|---|---|---|---|---|\n")

_WS_DOC = """<!-- TEAMWORK-MACHINE
ws: WS-19
features:
  - id: WS-19-S1
    target: core
    bl: BL-024
    dependencies: []
    status: planned
  - id: WS-19-S2
    target: platform
    bl: BL-025
    dependencies: [WS-19-S1]
    status: planned
  - id: WS-19-S3
    target: platform
    bl: BL-026
    dependencies: []
    status: planned
  - id: WS-19-S4
    target: core
    bl: BL-027
    dependencies: [WS-19-S2]
    status: planned
-->

# WS-19 · Canonical Offer

<!-- WS-PROGRESS:START -->
(占位)
<!-- WS-PROGRESS:END -->
"""


def _run_ws_progress(cwd: Path, *extra: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(STATE_PY), "ws-progress", "--ws", "19", *extra],
        capture_output=True, text=True, cwd=cwd)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(proc.stdout)


class _WsRepo(unittest.TestCase):
    """夹具:主工作区 WS-19 正本 + ROADMAP;可选 .worktree 旧副本。"""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        self.addCleanup(self._td.cleanup)
        self.ws_main = self.root / "product-overview" / "workstream" / "WS-19-canonical.md"
        self.ws_main.parent.mkdir(parents=True)
        self.ws_main.write_text(_WS_DOC, encoding="utf-8")

    def _roadmap(self, s1_status: str, s2_status: str = "🔒 已规划，待前置"):
        rm = self.root / "services" / "core" / "docs" / "ROADMAP.md"
        rm.parent.mkdir(parents=True, exist_ok=True)
        rm.write_text(
            "# ROADMAP\n" + _HEADER +
            f"| BL-024 | S1 身份 | P0 | — | {s1_status} | - | F-100 | WS-19 |\n"
            f"| BL-025 | S2 可见性 | P0 | BL-024 | {s2_status} | - | - | WS-19 |\n"
            "| BL-026 | S3 仲裁 | P1 | 外部 | ⏳ 等待外部依赖（PingPlus 契约） | - | - | WS-19 |\n"
            "| BL-027 | S4 墙 | P0 | BL-025 | 🔒 已规划，待前置 | - | - | WS-19 |\n",
            encoding="utf-8")

    def _stale_worktree_copy(self):
        stale = (self.root / ".worktree" / "INFRA-F001-cleanup" / "product-overview"
                 / "workstream" / "WS-19-canonical.md")
        stale.parent.mkdir(parents=True)
        stale.write_text(_WS_DOC.replace("Canonical Offer", "旧基线副本"), encoding="utf-8")
        return stale


class TestWorktreePollution(_WsRepo):
    def test_write_targets_main_tree_not_worktree_copy(self):
        # 核心回归:.worktree 内有旧副本(排序还在正本前)· --write 必须落主工作区正本
        self._roadmap("✅ 已交付（merged staging）")
        stale = self._stale_worktree_copy()
        stale_before = stale.read_text(encoding="utf-8")
        out = _run_ws_progress(self.root, "--write")
        self.assertEqual(out["written_to"],
                         str(self.ws_main.relative_to(self.root)))
        self.assertEqual(stale.read_text(encoding="utf-8"), stale_before,
                         ".worktree 内旧副本不得被写入")
        self.assertIn("进度 1/4", self.ws_main.read_text(encoding="utf-8"))

    def test_scan_ok_excludes_hidden_and_named_dirs(self):
        root = self.root
        self.assertFalse(_ws_scan_ok(root / ".worktree" / "X" / "WS-01.md", root))
        self.assertFalse(_ws_scan_ok(root / ".venv" / "WS-01.md", root))
        self.assertFalse(_ws_scan_ok(root / "node_modules" / "a" / "WS-01.md", root))
        self.assertFalse(_ws_scan_ok(root / "docs" / "_archive" / "WS-01.md", root))
        self.assertTrue(_ws_scan_ok(root / "product-overview" / "workstream" / "WS-01.md", root))

    def test_find_ws_file_prefers_product_overview_and_reports_candidates(self):
        dup = self.root / "notes" / "workstream" / "WS-19-copy.md"
        dup.parent.mkdir(parents=True)
        dup.write_text(_WS_DOC, encoding="utf-8")
        best, cands = _find_ws_file(self.root, "WS-19")
        self.assertEqual(best, self.ws_main)
        self.assertEqual(len(cands), 2)
        # 多候选要 surface 到 emit
        self._roadmap("已完成")
        out = _run_ws_progress(self.root)
        self.assertIn("ws_file_candidates", out)


class TestStatusVocab(_WsRepo):
    def test_delivered_alias_counts_done_and_unlocks_ready(self):
        # 「✅ 已交付」= 完成;S2 依赖 S1 · 应进 ready_to_start
        self._roadmap("✅ 已交付（merged staging `65e03f8` · 10/10 AC）")
        out = _run_ws_progress(self.root)
        self.assertIn("进度 1/4", out["block"])
        self.assertEqual([r["feature"] for r in out["ready_to_start"]], ["S2"])
        self.assertNotIn("unrecognized_status", out)

    def test_online_alias_counts_done(self):
        self._roadmap("已上线")
        out = _run_ws_progress(self.root)
        self.assertIn("进度 1/4", out["block"])

    def test_substring_done_no_longer_false_positive(self):
        # 「基本已完成，待测试」不算完成 · 且 surface 为词表外写法
        self._roadmap("基本已完成，待测试")
        out = _run_ws_progress(self.root)
        self.assertIn("进度 0/4", out["block"])
        self.assertEqual(out["unrecognized_status"][0]["feature"], "S1")
        self.assertIn("⚠️ 状态词不在词表", out["block"])
        # S1 未完成 → S2 不可启动
        self.assertNotIn("S2", [r["feature"] for r in out["ready_to_start"]])

    def test_bucket_unit(self):
        self.assertEqual(_ws_status_bucket("✅ 已交付（x）"), ("已完成", True))
        self.assertEqual(_ws_status_bucket("**已完成**"), ("已完成", True))
        self.assertEqual(_ws_status_bucket("🔄 进行中"), ("进行中", True))
        self.assertEqual(_ws_status_bucket("🗑️ 已取消"), ("已取消", True))
        self.assertEqual(_ws_status_bucket("⏳ 等待外部依赖（x）"), ("等待依赖", True))
        self.assertEqual(_ws_status_bucket("🔒 已规划，待前置"), ("待开始", True))
        self.assertEqual(_ws_status_bucket(""), ("待开始", True))
        self.assertEqual(_ws_status_bucket("基本已完成，待测试"), ("待开始", False))
        self.assertEqual(_ws_status_bucket("未匹配 ROADMAP"), ("未匹配", True))


if __name__ == "__main__":
    unittest.main()
