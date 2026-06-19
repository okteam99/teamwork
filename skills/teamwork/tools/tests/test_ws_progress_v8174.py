#!/usr/bin/env python3
"""v8.174 · ws-progress（WS 进度 rollup）回归套件。

治本:WS 文档只有「规划态」(features[].status)· 无执行态进度 · 用户翻 5 个 ROADMAP 才
能看「这条线建到哪了」。执行态单一源在各 ROADMAP「状态」列(职责单一禁手抄)→ 只能派生。
本命令 glob 全仓 ROADMAP.md · 按「关联 WS」列过滤 · 确定性汇总(--write 写回标记区)。

运行:python3 -m pytest skills/teamwork/tools/tests/test_ws_progress_v8174.py -q
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

from state import _parse_roadmap_rows, _ws_nums, _render_ws_progress  # noqa: E402

_HEADER = ("| Feature ID | 功能名称 | 优先级 | 描述 | 核心验收标准 | 依赖 "
           "| 状态 | 当前阶段 | 对应 F编号 | 关联 WS |\n"
           "|---|---|---|---|---|---|---|---|---|---|\n")


def _roadmap(*rows: str) -> str:
    return "# ROADMAP\n" + _HEADER + "".join(r + "\n" for r in rows)


class TestParse(unittest.TestCase):
    def test_parse_by_header_tolerates_order(self):
        # 列序打乱 → 仍按列名定位
        txt = ("| 状态 | Feature ID | 关联 WS | 功能名称 | 当前阶段 | 对应 F编号 |\n"
               "|---|---|---|---|---|---|\n"
               "| 已完成 | BL-001 | WS-01 | 脚手架 | - | F-012 |\n")
        rows = _parse_roadmap_rows(_write(txt))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["bl"], "BL-001")
        self.assertEqual(rows[0]["status"], "已完成")
        self.assertEqual(rows[0]["f_id"], "F-012")

    def test_scans_multiple_tables_one_file(self):
        # 一个 ROADMAP 多张表(各 Wave 段)· 都要扫到
        txt = _roadmap("| BL-001 | a | P0 | x | ① | 无 | 已完成 | - | F-1 | WS-01 |")
        txt += "\n## Wave 2\n" + _HEADER + "| BL-004 | b | P0 | y | ① | 无 | 待开始 | - | - | WS-01 |\n"
        rows = _parse_roadmap_rows(_write(txt))
        self.assertEqual({r["bl"] for r in rows}, {"BL-001", "BL-004"})

    def test_skips_non_bl_rows(self):
        # 技术债表 / 占位行(Feature ID 非 BL)跳过 · 不崩
        txt = _roadmap("| DEP-1 | 债务 | - | x | - | 无 | 待清理 | - | - | - |",
                       "| BL-002 | 真feature | P0 | y | ① | 无 | 进行中 | RD | F-2 | WS-01 |")
        rows = _parse_roadmap_rows(_write(txt))
        self.assertEqual([r["bl"] for r in rows], ["BL-002"])


class TestWsNums(unittest.TestCase):
    def test_extract_variants(self):
        self.assertEqual(_ws_nums("WS-01"), {1})
        self.assertEqual(_ws_nums("WS-1"), {1})
        self.assertEqual(_ws_nums("`WS-02`"), {2})
        self.assertEqual(_ws_nums("WS-01 / WS-03"), {1, 3})
        self.assertEqual(_ws_nums("无"), set())


class TestRender(unittest.TestCase):
    def _items(self):
        return [
            {"bl": "BL-001", "subproject": "infra", "name": "脚手架",
             "status": "已完成", "stage": "-", "f_id": "F-012"},
            {"bl": "BL-002", "subproject": "infra", "name": "crates",
             "status": "进行中", "stage": "RD 开发中", "f_id": "F-018"},
            {"bl": "BL-003", "subproject": "platform-api", "name": "服务",
             "status": "待开始", "stage": "-", "f_id": "-"},
        ]

    def test_rollup_line(self):
        out = _render_ws_progress("WS-01", self._items(), 2)
        self.assertIn("进度 1/3 已完成", out)
        self.assertIn("1 进行中", out)
        self.assertIn("1 待开始", out)

    def test_table_has_icons_and_sorted(self):
        out = _render_ws_progress("WS-01", self._items(), 2)
        self.assertIn("✅ 已完成", out)
        self.assertIn("🔄 进行中", out)
        self.assertIn("| BL | 子项目 | 功能 | 状态 | 当前阶段 | F |", out)

    def test_empty_items_friendly_message(self):
        out = _render_ws_progress("WS-01", [], 3)
        self.assertIn("暂无数据", out)
        self.assertNotIn("| BL |", out)  # 空表不渲染表头


def _write(txt: str) -> Path:
    f = Path(tempfile.mkdtemp(prefix="rm-")) / "ROADMAP.md"
    f.write_text(txt, encoding="utf-8")
    return f


class TestCli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="wsp-"))
        (self.root / "project-specs" / "infra").mkdir(parents=True)
        (self.root / "project-specs" / "platform-api").mkdir(parents=True)
        (self.root / "product-overview" / "workstream").mkdir(parents=True)
        (self.root / "project-specs" / "infra" / "ROADMAP.md").write_text(
            _roadmap("| BL-001 | 脚手架 | P0 | x | ① | 无 | 已完成 | - | F-012 | WS-01 |",
                     "| BL-002 | crates | P0 | y | ① | 无 | 进行中 | RD | F-018 | WS-01 |",
                     "| BL-009 | 别条线 | P1 | z | ① | 无 | 待开始 | - | - | WS-02 |"),
            encoding="utf-8")
        (self.root / "project-specs" / "platform-api" / "ROADMAP.md").write_text(
            _roadmap("| BL-003 | 服务骨架 | P0 | x | ① | 无 | 待开始 | - | - | `WS-01` |"),
            encoding="utf-8")
        self.ws = self.root / "product-overview" / "workstream" / "WS-01-infra-auth.md"
        self.ws.write_text(
            "# WS-01\n## 进度\n<!-- WS-PROGRESS:START · 工具生成 · 勿手改 -->\n"
            "（待刷新）\n<!-- WS-PROGRESS:END -->\n## 背景\nxxx\n", encoding="utf-8")

    def _run(self, *args):
        r = subprocess.run([sys.executable, str(STATE_PY), "ws-progress", *args],
                           capture_output=True, text=True, timeout=30, cwd=str(self.root))
        return r, (json.loads(r.stdout) if r.stdout.strip().startswith("{") else None)

    def test_filters_by_ws_excludes_others(self):
        _, out = self._run("--ws", "WS-01")
        self.assertEqual(out["verdict"], "OK")
        self.assertEqual(out["rows"], 3)               # BL-001/002/003 · 不含 WS-02 的 BL-009
        self.assertEqual(out["roadmaps_scanned"], 2)
        self.assertIn("进度 1/3 已完成", out["block"])
        self.assertNotIn("BL-009", out["block"])

    def test_bare_number_arg(self):
        # help 承诺 01 / 1 均可 · 裸数字必须能跑(治本:曾因正则强制 WS 前缀而 FAIL)
        _, out = self._run("--ws", "1")
        self.assertEqual(out["verdict"], "OK")
        self.assertEqual(out["ws"], "WS-01")
        self.assertEqual(out["rows"], 3)

    def test_write_replaces_markers(self):
        _, out = self._run("--ws", "WS-01", "--write")
        self.assertEqual(out["verdict"], "OK")
        self.assertTrue(out["written_to"].endswith("WS-01-infra-auth.md"))
        body = self.ws.read_text(encoding="utf-8")
        self.assertIn("进度 1/3 已完成", body)
        self.assertIn("| BL-001 | infra | 脚手架 | ✅ 已完成", body)
        self.assertNotIn("（待刷新）", body)            # 占位被替换
        self.assertIn("## 背景", body)                  # 标记区外内容不动

    def test_write_warns_without_markers(self):
        self.ws.write_text("# WS-01\n无标记区\n", encoding="utf-8")
        _, out = self._run("--ws", "WS-01", "--write")
        self.assertEqual(out["verdict"], "WARN")
        self.assertIn("block", out)                     # 仍给出 block 供手贴
        self.assertIn("标记", out["reason"])

    def test_idempotent_rewrite(self):
        # 连写两次 · 标记区不应嵌套/翻倍
        self._run("--ws", "WS-01", "--write")
        self._run("--ws", "WS-01", "--write")
        body = self.ws.read_text(encoding="utf-8")
        self.assertEqual(body.count("WS-PROGRESS:START"), 1)
        self.assertEqual(body.count("WS-PROGRESS:END"), 1)


if __name__ == "__main__":
    unittest.main()
