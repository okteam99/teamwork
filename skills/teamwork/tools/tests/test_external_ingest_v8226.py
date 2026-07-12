#!/usr/bin/env python3
"""v8.226 · external-ingest:外部评审(ultra 等)摄入为标准第三视角产物。
主路径 = session(评审时 MR 多未创建 · 用户拍板修正)· paste 降级 · pr-comments MR 窗口增强。
分层:命令只做转录归一(确定性)· 裁决归 PMO。"""
from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE_PY = HERE.parent / "state.py"
sys.path.insert(0, str(HERE.parent))
from _v8_stage_specs import parse_frontmatter  # noqa: E402


def _run(feat, *a):
    r = subprocess.run([sys.executable, str(STATE_PY), "external-ingest",
                        "--feature", str(feat), *a],
                       capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)


class TestIngest(unittest.TestCase):
    def setUp(self):
        self.feat = Path(tempfile.mkdtemp(prefix="ing-"))

    def test_session_mode_normalizes(self):
        src = self.feat / "raw.md"
        src.write_text("## Findings\n- [MAJOR] store.py:88 并发写入丢更新,无锁保护,复现:双写同 key\n- [MINOR] 错误信息可带字段名\n", encoding="utf-8")
        out = _run(self.feat, "--from", "session", "--input-file", str(src))
        self.assertEqual(out["verdict"], "OK")
        body = Path(out["artifact"]).read_text(encoding="utf-8")
        fm = parse_frontmatter(Path(out["artifact"]))
        self.assertEqual(fm["review_via"], "ultra-ingest")
        self.assertEqual(fm["origin"], "in-session")
        self.assertIn("裁决管线", out["next_action_brief"])   # 分层:裁决归 PMO

    def test_paste_mode_marked_degraded(self):
        src = self.feat / "raw.md"
        src.write_text("x" * 100, encoding="utf-8")
        out = _run(self.feat, "--from", "paste", "--input-file", str(src))
        self.assertIn("manual-paste", out["origin"])           # 降级显式标

    def test_too_short_rejected(self):
        src = self.feat / "raw.md"; src.write_text("ok", encoding="utf-8")
        out = _run(self.feat, "--from", "session", "--input-file", str(src))
        self.assertEqual(out["verdict"], "FAIL")

    def test_pr_comments_requires_url(self):
        out = _run(self.feat, "--from", "pr-comments")
        self.assertEqual(out["verdict"], "FAIL")

    def test_gate_accepts_ultra_ingest(self):
        # yolo 单模型门禁:review_via ∈ {subagent, ultra-ingest} 均为合法冷视角
        import _v8_stage_specs as S
        from types import SimpleNamespace as NS
        d = self.feat / "external-cross-review"; d.mkdir()
        (d / "review-ultra.md").write_text(
            "---\nreview_via: ultra-ingest\norigin: in-session\nheterogeneous: multi-agent-pipeline\ndegraded: true\n---\nfindings body", encoding="utf-8")
        (self.feat / ".git").mkdir()
        (self.feat / ".teamwork_localconfig.json").write_text(json.dumps({"disable_external_review": True}), encoding="utf-8")
        st = {"yolo": True, "host": "claude-code", "current_stage": "review", "flow_type": "Feature"}
        ok, msg = S._evidence_external_review_artifact(st, NS(feature=str(self.feat)))
        self.assertTrue(ok, msg)

if __name__ == "__main__":
    unittest.main()
