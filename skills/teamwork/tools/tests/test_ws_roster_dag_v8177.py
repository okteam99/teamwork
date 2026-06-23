#!/usr/bin/env python3
"""v8.177 · ws-progress 名册驱动 + 依赖 DAG 回归套件。

治本(实证 supersimples WS-03):① 跨子项目前置 K0=SDK-F040 登记在 SDK ROADMAP 的 **legacy 表**
(无「关联 WS」列)→ v8.174 ws-progress 只扫「关联 WS」漏掉它 · 总览只 6 个不是 7 个。② 无 feature
执行依赖关系图。修法:读 WS frontmatter features[] 当权威名册(声明的全列出 · 状态自 ROADMAP 按 bl
匹配 · 放宽解析器吃 legacy 表)+ 自 dependencies 派生 Mermaid DAG。

运行:python3 -m pytest skills/teamwork/tools/tests/test_ws_roster_dag_v8177.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE_PY = HERE.parent / "state.py"
sys.path.insert(0, str(HERE.parent))

from state import (_parse_ws_features, _parse_roadmap_rows,  # noqa: E402
                   _render_ws_dag, _ws_short)

_NEW_HDR = ("| Feature ID | 功能名称 | 优先级 | 描述 | 核心验收标准 | 依赖 "
            "| 状态 | 当前阶段 | 对应 F编号 | 关联 WS |\n"
            "|---|---|---|---|---|---|---|---|---|---|\n")
_LEGACY_HDR = "| Feature ID | 功能名称 | 状态 | 当前阶段 |\n|---|---|---|---|\n"

_WS_FRONTMATTER = """<!-- TEAMWORK-MACHINE · WS 机读契约
ws_id: WS-03
status: ✅ 规划完成
features:
  - id: WS-03-K0
    target: SDK
    bl: SDK-F040
    dependencies: []
    status: planned
  - id: WS-03-S1
    target: SIMP
    bl: BL-001
    dependencies: []
    status: planned
  - id: WS-03-S2
    target: SIMP
    bl: BL-002
    dependencies: [WS-03-S1]
    status: planned
-->

# WS-03：模板

## feature 总览
<!-- WS-PROGRESS:START · 工具生成 · 勿手改 -->
（待刷新）
<!-- WS-PROGRESS:END -->

## feature 依赖关系图
<!-- WS-DAG:START · 工具生成 · 勿手改 -->
（待刷新）
<!-- WS-DAG:END -->

## 背景
xxx
"""


class TestParseWsFeatures(unittest.TestCase):
    def _ws(self):
        d = Path(tempfile.mkdtemp(prefix="wsf-"))
        f = d / "WS-03-x.md"
        f.write_text(_WS_FRONTMATTER, encoding="utf-8")
        return f

    def test_parses_roster_from_machine_block(self):
        roster = _parse_ws_features(self._ws())
        self.assertEqual([f["id"] for f in roster], ["WS-03-K0", "WS-03-S1", "WS-03-S2"])
        k0 = roster[0]
        self.assertEqual(k0["bl"], "SDK-F040")     # 跨子项目 id 抓到
        self.assertEqual(k0["target"], "SDK")
        self.assertEqual(roster[2]["deps"], ["WS-03-S1"])   # 依赖解析

    def test_short_id(self):
        self.assertEqual(_ws_short("WS-03-K0", "WS-03"), "K0")
        self.assertEqual(_ws_short("WS-03-S1", "WS-03"), "S1")


class TestLegacyTable(unittest.TestCase):
    def test_legacy_table_without_ws_column_parsed(self):
        # legacy 表无「关联 WS」列 · 放宽门槛后仍解析 · id_allow 放行非 BL id
        d = Path(tempfile.mkdtemp(prefix="lg-"))
        f = d / "ROADMAP.md"
        f.write_text("# SDK\n" + _LEGACY_HDR +
                     "| SDK-F040 | iOS SPM 远程发布 | 待开始 | - |\n", encoding="utf-8")
        rows = _parse_roadmap_rows(f, id_allow={"SDK-F040"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["bl"], "SDK-F040")
        self.assertEqual(rows[0]["ws"], "")        # 无关联WS列 → 空

    def test_legacy_id_dropped_without_allow(self):
        # 不在 id_allow 里的非 BL id 仍跳过(防 legacy 表噪音行)
        d = Path(tempfile.mkdtemp(prefix="lg2-"))
        f = d / "ROADMAP.md"
        f.write_text("# SDK\n" + _LEGACY_HDR +
                     "| SDK-F040 | x | 待开始 | - |\n", encoding="utf-8")
        self.assertEqual(_parse_roadmap_rows(f), [])


class TestDag(unittest.TestCase):
    def test_dag_nodes_and_edges(self):
        roster = [
            {"id": "WS-03-K0", "bl": "SDK-F040", "deps": [], "status": "planned"},
            {"id": "WS-03-S1", "bl": "BL-001", "deps": [], "status": "planned"},
            {"id": "WS-03-S2", "bl": "BL-002", "deps": ["WS-03-S1"], "status": "planned"},
        ]
        dag = _render_ws_dag(roster, "WS-03")
        self.assertIn("```mermaid", dag)
        self.assertIn("flowchart", dag)
        self.assertIn('K0["K0 · SDK-F040"]', dag)
        self.assertIn("S1 --> S2", dag)            # 依赖边
        self.assertNotIn("K0 --> ", dag)           # K0 无下游边

    def test_dag_skips_废弃(self):
        roster = [{"id": "WS-03-S9", "bl": "BL-009", "deps": [], "status": "废弃"}]
        self.assertIsNone(_render_ws_dag(roster, "WS-03"))


class TestCliRosterDriven(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="wsr-"))
        (self.root / "project-specs" / "simp").mkdir(parents=True)
        (self.root / "project-specs" / "sdk").mkdir(parents=True)
        (self.root / "product-overview" / "workstream").mkdir(parents=True)
        # SIMP:新格式(有关联WS)
        (self.root / "project-specs" / "simp" / "ROADMAP.md").write_text(
            "# SIMP\n" + _NEW_HDR +
            "| BL-001 | 子项目骨架 | P0 | x | ① | 无 | 已完成 | - | F-1 | WS-03 |\n"
            "| BL-002 | Android 工程 | P0 | y | ① | BL-001 | 待开始 | - | - | WS-03 |\n",
            encoding="utf-8")
        # SDK:legacy 格式(无关联WS)· K0 在此
        (self.root / "project-specs" / "sdk" / "ROADMAP.md").write_text(
            "# SDK\n" + _LEGACY_HDR +
            "| SDK-F040 | iOS SPM 远程发布 | 进行中 | RD |\n", encoding="utf-8")
        self.ws = self.root / "product-overview" / "workstream" / "WS-03-x.md"
        self.ws.write_text(_WS_FRONTMATTER, encoding="utf-8")

    def _run(self, *a):
        r = subprocess.run([sys.executable, str(STATE_PY), "ws-progress", *a],
                           capture_output=True, text=True, timeout=30, cwd=str(self.root))
        return json.loads(r.stdout) if r.stdout.strip().startswith("{") else None

    def test_k0_surfaces_from_legacy_roadmap(self):
        out = self._run("--ws", "WS-03")
        self.assertEqual(out["verdict"], "OK")
        self.assertEqual(out["roster"], 3)         # 名册 3 个
        self.assertEqual(out["rows"], 3)           # K0 + S1 + S2 全列(不是只 2)
        self.assertIn("SDK-F040", out["block"])    # 🔴 K0 现身(治本)
        self.assertIn("iOS SPM 远程发布", out["block"])
        self.assertIn("🔄 进行中", out["block"])     # K0 状态自 legacy 表读到

    def test_write_fills_progress_and_dag(self):
        out = self._run("--ws", "WS-03", "--write")
        self.assertEqual(out["verdict"], "OK")
        self.assertTrue(out["dag_written"])
        body = self.ws.read_text(encoding="utf-8")
        self.assertIn("SDK-F040", body)            # 进度块含 K0
        self.assertIn("```mermaid", body)          # DAG 块已填
        self.assertIn("S1 --> S2", body)
        self.assertNotIn("（待刷新）", body)         # 两个占位都被替换


if __name__ == "__main__":
    unittest.main()
