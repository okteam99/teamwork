#!/usr/bin/env python3
"""v8.192 · pause-mark 计时排毒回归套件(stage 内 R5 等待与工作分离)。"""
from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _v8_engine import close_open_pause  # noqa: E402
from _v8_ship import _stage_durations    # noqa: E402
STATE_PY = HERE.parent / "state.py"

class TestClose(unittest.TestCase):
    def test_accumulates_await_into_stage(self):
        t0 = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        st = {"current_stage": "goal",
              "open_pause": {"stage": "goal", "started_at": t0}}
        close_open_pause(st)
        self.assertNotIn("open_pause", st)
        self.assertGreaterEqual(st["stage_contracts"]["goal"]["await_minutes"], 29)

    def test_noop_without_pause(self):
        st = {"current_stage": "dev"}
        close_open_pause(st)
        self.assertNotIn("stage_contracts", st)

    def test_accumulates_twice(self):
        t0 = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        st = {"stage_contracts": {"goal": {"await_minutes": 5}},
              "open_pause": {"stage": "goal", "started_at": t0}}
        close_open_pause(st)
        self.assertGreaterEqual(st["stage_contracts"]["goal"]["await_minutes"], 14)

class TestDurations(unittest.TestCase):
    def test_await_subtracted_from_work(self):
        st = {"completed_stages": ["goal", "dev"],
              "stage_contracts": {
                  "goal": {"duration_minutes": 50, "await_minutes": 30},
                  "dev": {"duration_minutes": 40}}}
        breakdown, analysis = _stage_durations(st)
        self.assertIn("goal 20m(+等待30m)", breakdown)   # 50-30=20 工作
        self.assertIn("工作阶段总和 60m", analysis)        # 20+40
        self.assertIn("最耗时(工作)dev 40m", analysis)     # 不再误判 goal

class TestCli(unittest.TestCase):
    def test_pause_mark_writes_open_pause(self):
        d = Path(tempfile.mkdtemp()) / "feat"; d.mkdir()
        (d / "state.json").write_text(json.dumps(
            {"feature_id": "X-F1", "current_stage": "goal", "concerns": []}), encoding="utf-8")
        r = subprocess.run([sys.executable, str(STATE_PY), "pause-mark",
                            "--feature", str(d), "--label", "PRD 确认"],
                           capture_output=True, text=True, timeout=30)
        out = json.loads(r.stdout)
        self.assertEqual(out["verdict"], "OK")
        st = json.loads((d / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(st["open_pause"]["stage"], "goal")
        self.assertEqual(st["open_pause"]["label"], "PRD 确认")

if __name__ == "__main__":
    unittest.main()


class TestTimingSplitV8208(unittest.TestCase):
    """v8.208 · 时长三分(AI 自主 vs 等待用户)+ git 邮箱 · 台账/审计细化。"""
    def _split(self, st):
        from _v8_ship import _timing_split
        return _timing_split(st)

    def test_ai_vs_wait_split(self):
        st = {"completed_stages": ["goal", "dev", "pm_acceptance"], "stage_contracts": {
            "goal": {"duration_minutes": 20, "await_minutes": 5},   # 15 AI · 5 wait
            "dev": {"duration_minutes": 40, "await_minutes": 0},    # 40 AI
            "pm_acceptance": {"duration_minutes": 30}}}             # 30 wait(纯等待 stage)
        ai, wait = self._split(st)
        self.assertEqual(ai, 55)
        self.assertEqual(wait, 35)

    def test_no_duration_returns_none(self):
        self.assertEqual(self._split({"completed_stages": [], "stage_contracts": {}}), (None, None))

    def test_email_helper(self):
        import tempfile, subprocess
        from pathlib import Path
        from _v8_ship import _git_user_email
        d = Path(tempfile.mkdtemp())
        subprocess.run(["git", "-C", str(d), "init", "-q"], capture_output=True)
        subprocess.run(["git", "-C", str(d), "config", "user.email", "who@x.co"], capture_output=True)
        self.assertEqual(_git_user_email(str(d)), "who@x.co")

    def test_audit_record_has_email_and_split(self):
        import tempfile, os, json
        from pathlib import Path
        from _v8_ship import _write_audit_record
        wt = Path(tempfile.mkdtemp())
        import subprocess
        subprocess.run(["git", "-C", str(wt), "init", "-q"], capture_output=True)
        subprocess.run(["git", "-C", str(wt), "config", "user.email", "dev@team.co"], capture_output=True)
        os.environ["HOME"] = tempfile.mkdtemp()
        st = {"feature_id": "F9", "completed_stages": ["dev", "pm_acceptance"], "flow_type": "Feature",
              "stage_contracts": {"dev": {"duration_minutes": 40, "await_minutes": 0},
                                  "pm_acceptance": {"duration_minutes": 30}}}
        rec = _write_audit_record(st, "F9", "staging", str(wt), None, "")
        body = Path(rec).read_text(encoding="utf-8")
        self.assertIn("user_email: dev@team.co", body)          # frontmatter
        self.assertIn("AI 自主运行:40m", body)                  # split
        self.assertIn("等待用户:30m", body)
