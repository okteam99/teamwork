#!/usr/bin/env python3
"""v8.172 · add-concern 命令重新实现回归套件。

治本:SKILL/goal-stage 多处文档引用 `state.py add-concern --severity WARN --message`,
但命令曾被误删 → AI 想记 incidental-scope concern 失败(实证 audit ×3:SVC-CORE /
ADMIN / TERMPRO 都只能塞 commit message)。重加命令 · append 到 state.concerns。

运行:python3 -m pytest skills/teamwork/tools/tests/test_add_concern_v8172.py -q
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


class TestAddConcern(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="addc-"))
        self.feat = self.tmp / "feat"
        self.feat.mkdir()
        (self.feat / "state.json").write_text(
            json.dumps({"feature_id": "X-F1", "flow_type": "Feature",
                        "current_stage": "goal", "concerns": []}),
            encoding="utf-8")

    def _run(self, *args):
        return subprocess.run([sys.executable, str(STATE_PY), "add-concern",
                               "--feature", str(self.feat), *args],
                              capture_output=True, text=True, timeout=30)

    def _concerns(self):
        return json.loads((self.feat / "state.json").read_text(encoding="utf-8")).get("concerns", [])

    def test_appends_concern(self):
        r = self._run("--severity", "WARN", "--message", "auto skip: DB schema change")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["verdict"], "OK")
        self.assertEqual(out["concerns_count"], 1)
        concerns = self._concerns()
        self.assertEqual(len(concerns), 1)
        self.assertIn("WARN", concerns[0])
        self.assertIn("auto skip: DB schema change", concerns[0])

    def test_appends_not_overwrites(self):
        self._run("--severity", "WARN", "--message", "first")
        self._run("--severity", "INFO", "--message", "second")
        concerns = self._concerns()
        self.assertEqual(len(concerns), 2)
        self.assertIn("first", concerns[0])
        self.assertIn("second", concerns[1])

    def test_severity_validated(self):
        # 非法 severity → argparse 拒绝(choices)
        r = self._run("--severity", "BOGUS", "--message", "x")
        self.assertNotEqual(r.returncode, 0)

    def test_message_required(self):
        r = self._run("--severity", "WARN")
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
