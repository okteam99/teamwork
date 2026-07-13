#!/usr/bin/env python3
"""v8.198 · loops 对照两修:yolo fix-retry 10 轮止损 + await-merge 轮询。"""
from __future__ import annotations
import json, subprocess, sys, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _v8_engine import yolo_rounds_exceeded, YOLO_MAX_FIX_ROUNDS  # noqa: E402
STATE_PY = HERE.parent / "state.py"

class TestYoloStop(unittest.TestCase):
    def _st(self, yolo, n):
        return {"yolo": yolo, "stage_contracts": {"review": {"rounds": [{"round": i} for i in range(n)]}}}
    def test_yolo_at_limit_true(self):
        self.assertTrue(yolo_rounds_exceeded(self._st(True, YOLO_MAX_FIX_ROUNDS), "review"))
    def test_yolo_below_limit_false(self):
        self.assertFalse(yolo_rounds_exceeded(self._st(True, YOLO_MAX_FIX_ROUNDS - 1), "review"))
    def test_non_yolo_never(self):
        self.assertFalse(yolo_rounds_exceeded(self._st(False, 99), "review"))

class TestAwaitMergeCli(unittest.TestCase):
    def test_no_url_fails(self):
        r = subprocess.run([sys.executable, str(STATE_PY), "await-merge"],
                           capture_output=True, text=True, timeout=30)
        out = json.loads(r.stdout)
        self.assertEqual(out["verdict"], "FAIL")
        self.assertIn("MR URL", out["error"])

if __name__ == "__main__":
    unittest.main()


class TestPrdConformanceV8201(unittest.TestCase):
    def _chk(self, body):
        import tempfile
        from types import SimpleNamespace as NS
        from _v8_stage_specs import _evidence_prd_template_conformance
        d = Path(tempfile.mkdtemp()); (d / "PRD.md").write_text(body, encoding="utf-8")
        return _evidence_prd_template_conformance({}, NS(feature=str(d)))

    def test_freeform_prd_blocked_with_all_three(self):
        ok, msg = self._chk("自由结构\n## 背景\n")
        self.assertFalse(ok)
        for k in ("机读块", "验收标准", "开工前"): self.assertIn(k, msg)
        self.assertIn("别抄项目里旧 PRD", msg)

    def test_canonical_passes(self):
        ok, _ = self._chk("<!-- TEAMWORK-MACHINE\nx: 1\n-->\n# P\n## 验收标准\n- AC-1\n## 开工前必须想清的\n无\n")
        self.assertTrue(ok)

    def test_legacy_frontmatter_with_ac_needs_zone(self):
        ok, msg = self._chk("---\nacceptance_criteria: [a]\n---\n# P\n")
        self.assertFalse(ok)                      # 缺扩展区仍拦
        self.assertIn("开工前", msg)


class TestShip1UserCardV8232(unittest.TestCase):
    """v8.232 · ship1 终点 user_card:工具生成 · URL 置顶 · AI 原样贴(治 MR 地址埋段落)。"""
    def test_card_url_first(self):
        import tempfile, subprocess, json
        from pathlib import Path as P
        d = P(tempfile.mkdtemp()); feat = d / "docs" / "features" / "F1"; feat.mkdir(parents=True)
        subprocess.run(["git", "-C", str(d), "init", "-q", "-b", "feature/f1"], capture_output=True)
        (feat / "state.json").write_text(json.dumps({
            "feature_id": "F1", "flow_type": "Feature", "current_stage": "completed",
            "merge_target": "staging",
            "ship": {"phase": "archived"}, "stage_contracts": {}, "concerns": []}), encoding="utf-8")
        import os
        prev = os.environ.get("TEAMWORK_BYPASS_CHECKSUM"); os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"
        try:
            r = subprocess.run([sys.executable, str(STATE_PY), "ship-phase", "--action", "push",
                                "--feature", str(feat), "--feature-head-commit", "deadbeef",
                                "--git-host", "gitlab", "--mr-creation-method", "cli-glab",
                                "--mr-url", "http://git.example.com/mr/757"],
                               capture_output=True, text=True, timeout=30)
            out = json.loads(r.stdout)
        finally:
            if prev is None: os.environ.pop("TEAMWORK_BYPASS_CHECKSUM", None)
            else: os.environ["TEAMWORK_BYPASS_CHECKSUM"] = prev
        self.assertIn("user_card", out)
        lines = [l for l in out["user_card"].splitlines() if l.strip()]
        self.assertIn("请合并 MR", lines[0])
        self.assertTrue(lines[1].startswith("🔗 http://git.example.com/mr/757"))  # URL 第二行(标题后首信息)
        self.assertIn("原样贴", out["next_action_brief"])
