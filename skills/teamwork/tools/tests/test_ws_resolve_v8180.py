#!/usr/bin/env python3
"""v8.180 · ws-progress --feature 自解析 WS + ship 确定性自刷 回归套件。

治本(用户看 yolo ship2):WS 进度块更新原是软指令(ship §3.5「翻完跑 ws-progress」)· yolo 自主
无人接住 → routinely stale。改确定性:ship archive 翻牌后从 feature 自解析所属 WS(F-id → ROADMAP
「对应F编号」→ 关联WS · 带名册反查退路)+ 自跑 ws-progress --write + 纳进归档 commit。

运行:python3 -m pytest skills/teamwork/tools/tests/test_ws_resolve_v8180.py -q
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

from state import _resolve_ws_from_feature  # noqa: E402

_RM_HDR = ("| Feature ID | 功能名称 | 优先级 | 描述 | 核心验收标准 | 依赖 "
           "| 状态 | 当前阶段 | 对应 F编号 | 关联 WS |\n"
           "|---|---|---|---|---|---|---|---|---|---|\n")
_MACHINE = ("<!-- TEAMWORK-MACHINE\nws_id: WS-03\nfeatures:\n"
            "  - id: WS-03-S1\n    target: SIMP\n    bl: BL-001\n    dependencies: []\n-->\n")


def _proj(roadmap_row, fid="ADMIN-F260618055452-Tabs", ws_machine=True):
    root = Path(tempfile.mkdtemp(prefix="wr-"))
    (root / "project-specs" / "simp").mkdir(parents=True)
    (root / "product-overview" / "workstream").mkdir(parents=True)
    feat = root / "apps" / "x" / "docs" / "features" / fid
    feat.mkdir(parents=True)
    (feat / "state.json").write_text(json.dumps({"feature_id": fid}), encoding="utf-8")
    (root / "project-specs" / "simp" / "ROADMAP.md").write_text(
        "# SIMP\n" + _RM_HDR + roadmap_row + "\n", encoding="utf-8")
    ws = root / "product-overview" / "workstream" / "WS-03-x.md"
    ws.write_text(
        (_MACHINE if ws_machine else "") + "# WS-03\n"
        "<!-- WS-PROGRESS:START x -->\n（待刷新）\n<!-- WS-PROGRESS:END -->\n", encoding="utf-8")
    return root, feat, ws


class TestResolve(unittest.TestCase):
    def test_resolve_via_roadmap_f_column(self):
        # 对应F编号 含本 feature F-id · 关联WS=WS-03 → 解析 WS-03
        root, feat, _ = _proj(
            "| BL-001 | Tabs | P0 | x | ① | 无 | 已完成 | - | ADMIN-F260618055452 | WS-03 |")
        self.assertEqual(_resolve_ws_from_feature(feat, root), "WS-03")

    def test_resolve_fallback_via_roster(self):
        # 行有对应F编号匹配但「关联WS」空 → 用 BL 反查 WS 名册(features[].bl)
        root, feat, _ = _proj(
            "| BL-001 | Tabs | P0 | x | ① | 无 | 已完成 | - | ADMIN-F260618055452 | - |")
        self.assertEqual(_resolve_ws_from_feature(feat, root), "WS-03")

    def test_no_match_returns_none(self):
        # 对应F编号 不含本 F-id → None(best-effort)
        root, feat, _ = _proj(
            "| BL-001 | Tabs | P0 | x | ① | 无 | 已完成 | - | OTHER-F999 | WS-03 |")
        self.assertIsNone(_resolve_ws_from_feature(feat, root))

    def test_f_id_normalized_match(self):
        # 对应F编号 用短横 F-id 也匹配(归一化去横线)
        root, feat, _ = _proj(
            "| BL-001 | Tabs | P0 | x | ① | 无 | 进行中 | RD | F260618055452-Tabs | WS-03 |")
        self.assertEqual(_resolve_ws_from_feature(feat, root), "WS-03")


class TestCliFeature(unittest.TestCase):
    def _run(self, root, feat, *a):
        r = subprocess.run([sys.executable, str(STATE_PY), "ws-progress",
                            "--feature", str(feat), *a],
                           capture_output=True, text=True, timeout=30, cwd=str(root))
        return json.loads(r.stdout) if r.stdout.strip().startswith("{") else None

    def test_feature_resolves_and_writes(self):
        root, feat, ws = _proj(
            "| BL-001 | Tabs | P0 | x | ① | 无 | 已完成 | - | ADMIN-F260618055452 | WS-03 |")
        out = self._run(root, feat, "--write")
        self.assertEqual(out["verdict"], "OK")
        self.assertEqual(out["ws"], "WS-03")
        self.assertTrue(out["written_to"])
        body = ws.read_text(encoding="utf-8")
        self.assertIn("进度 1/1 已完成", body)
        self.assertNotIn("（待刷新）", body)

    def test_feature_unresolved_warns(self):
        root, feat, _ = _proj(
            "| BL-001 | Tabs | P0 | x | ① | 无 | 已完成 | - | OTHER-F999 | WS-03 |")
        out = self._run(root, feat, "--write")
        self.assertEqual(out["verdict"], "WARN")
        self.assertIsNone(out.get("resolved_ws"))


if __name__ == "__main__":
    unittest.main()


class TestV8196Chain(unittest.TestCase):
    def test_state_bl_resolves_without_f_column(self):
        # v8.196:state.json.bl 机读绑定 → 名册反查 · 不依赖 ROADMAP「对应F编号」
        root, feat, _ = _proj(
            "| BL-001 | Tabs | P0 | x | ① | 无 | 已完成 | - | - | - |")  # F列/关联WS 都空
        (feat / "state.json").write_text(
            json.dumps({"feature_id": "ADMIN-F999-Other", "bl": "BL-001"}), encoding="utf-8")
        self.assertEqual(_resolve_ws_from_feature(feat, root), "WS-03")

    def test_ready_to_start_emitted(self):
        # S1 已完成 → S2(依赖 S1)可启动;roster 需两条
        root = Path(tempfile.mkdtemp(prefix="rdy-"))
        (root / "project-specs" / "simp").mkdir(parents=True)
        (root / "product-overview" / "workstream").mkdir(parents=True)
        (root / "project-specs" / "simp" / "ROADMAP.md").write_text(
            "# SIMP\n" + _RM_HDR +
            "| BL-001 | A | P0 | x | ① | 无 | 已完成 | - | F-1 | WS-03 |\n"
            "| BL-002 | B | P0 | y | ① | BL-001 | 待开始 | - | - | WS-03 |\n", encoding="utf-8")
        (root / "product-overview" / "workstream" / "WS-03-x.md").write_text(
            "<!-- TEAMWORK-MACHINE\nws_id: WS-03\nfeatures:\n"
            "  - id: WS-03-S1\n    target: SIMP\n    bl: BL-001\n    dependencies: []\n"
            "  - id: WS-03-S2\n    target: SIMP\n    bl: BL-002\n    dependencies: [WS-03-S1]\n"
            "-->\n# WS-03\n<!-- WS-PROGRESS:START x -->\n（待刷新）\n<!-- WS-PROGRESS:END -->\n",
            encoding="utf-8")
        r = subprocess.run([sys.executable, str(STATE_PY), "ws-progress", "--ws", "WS-03"],
                           capture_output=True, text=True, timeout=30, cwd=str(root))
        out = json.loads(r.stdout)
        self.assertEqual(out["ready_to_start"], [{"feature": "S2", "bl": "BL-002"}])
        self.assertIn("可启动", out["block"])
