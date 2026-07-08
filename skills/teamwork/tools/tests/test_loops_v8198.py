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
