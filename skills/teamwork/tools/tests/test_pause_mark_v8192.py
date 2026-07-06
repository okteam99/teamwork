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
