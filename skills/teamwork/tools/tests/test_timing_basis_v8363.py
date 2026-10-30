#!/usr/bin/env python3
"""v8.363 · 计时口径 v2 回归套件(提效方案第 0 批:先把统计做对再改流程)。

- 总时长起点含 prepare-check / init(旧口径只从最早 stage 起 · 漏启动准备)
- 启动准备耗时单列 · 暂停次数机器计数
- pm_acceptance 不再整段算等待(v8.361 起 AC 全过不停)
- 存量 state(无 timing_basis)口径不变 —— 新旧不混比
"""
from __future__ import annotations
import json, os, subprocess, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _v8_engine import close_open_pause  # noqa: E402
from _v8_ship import (_feature_duration_h, _pause_count, _stage_durations,  # noqa: E402
                      _startup_minutes, _timing_split)
STATE_PY = str(HERE.parent / "state.py")


def _st(v2: bool, **extra) -> dict:
    st = {
        "created_at": "2026-10-01T09:50:00Z",
        "completed_stages": ["dev", "pm_acceptance"],
        "stage_contracts": {
            "dev": {"started_at": "2026-10-01T10:00:00Z", "completed_at": "2026-10-01T11:00:00Z",
                    "duration_minutes": 60},
            "pm_acceptance": {"started_at": "2026-10-01T11:00:00Z",
                              "completed_at": "2026-10-01T11:30:00Z",
                              "duration_minutes": 30, "await_minutes": 10},
        },
    }
    if v2:
        st.update(timing_basis="v2", prepare_check_at="2026-10-01T09:30:00Z")
    st.update(extra)
    return st


class TestLegacyUnchanged(unittest.TestCase):
    def test_duration_from_first_stage(self):
        self.assertEqual(_feature_duration_h(_st(False)), "1.5h")

    def test_pm_acceptance_whole_wait(self):
        self.assertEqual(_timing_split(_st(False)), (60, 30))

    def test_new_fields_none(self):
        self.assertIsNone(_startup_minutes(_st(False)))
        self.assertIsNone(_pause_count(_st(False)))


class TestV2(unittest.TestCase):
    def test_duration_from_prepare_check(self):
        self.assertEqual(_feature_duration_h(_st(True)), "2.0h")   # 09:30 → 11:30

    def test_duration_falls_back_to_created_at(self):
        st = _st(True, prepare_check_at=None)
        self.assertEqual(_feature_duration_h(st), "1.7h")          # 09:50 → 11:30

    def test_startup_minutes(self):
        self.assertEqual(_startup_minutes(_st(True)), 30)
        self.assertEqual(_startup_minutes(_st(True, prepare_check_at=None)), 10)

    def test_pm_acceptance_is_work_minus_await(self):
        self.assertEqual(_timing_split(_st(True)), (60 + 20, 10))

    def test_pm_acceptance_counted_in_work_analysis(self):
        _, analysis = _stage_durations(_st(True))
        self.assertIn("工作阶段总和 80m", analysis)
        self.assertNotIn("用户决策等待", analysis)

    def test_pause_count(self):
        self.assertEqual(_pause_count(_st(True)), 0)
        self.assertEqual(_pause_count(_st(True, pause_log=[{}, {}])), 2)


class TestPauseLog(unittest.TestCase):
    def test_close_appends_log_even_zero_minutes(self):
        st = {"current_stage": "goal",
              "open_pause": {"stage": "goal", "label": "PRD 确认",
                             "started_at": datetime.now(timezone.utc).isoformat()}}
        close_open_pause(st)
        self.assertEqual(st["pause_log"], [{"stage": "goal", "label": "PRD 确认", "decision": "",
                                           "minutes": 0}])

    def test_close_accumulates(self):
        t0 = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        st = {"pause_log": [{"stage": "goal", "label": "a", "minutes": 1}],
              "open_pause": {"stage": "dev", "started_at": t0}}
        close_open_pause(st)
        self.assertEqual(len(st["pause_log"]), 2)
        self.assertGreaterEqual(st["pause_log"][1]["minutes"], 4)

    def test_no_pause_no_log(self):
        st = {"current_stage": "dev"}
        close_open_pause(st)
        self.assertNotIn("pause_log", st)


class TestInitCli(unittest.TestCase):
    """真跑 prepare-check → init-feature:prepare_check_at 取 audit 记录时间戳。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        genv = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(self.tmp),
                "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "i"],
                       cwd=self.tmp, check=True, env=genv)
        self.audit = self.tmp / "audit.jsonl"
        self.env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(self.tmp),
                    "TEAMWORK_PREPARE_AUDIT_PATH": str(self.audit)}
        self.root = self.tmp / "docs" / "features"
        self.root.mkdir(parents=True)

    def _run(self, *args, env=None):
        return subprocess.run([sys.executable, STATE_PY, *args], capture_output=True,
                              text=True, cwd=self.tmp, env=env or self.env, timeout=60)

    def _init(self, fid, env=None):
        d = self.root / fid
        d.mkdir()
        r = self._run("init-feature", "--feature", str(d), "--feature-id", fid,
                      "--flow-type", "Bug", "--merge-target", "main", "--branch", "b",
                      "--worktree-mode", "off", env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads((d / "state.json").read_text(encoding="utf-8"))

    def test_prepare_check_timestamp_recorded(self):
        r = self._run("prepare-check", "--feature-id-prefix", "T",
                      "--features-root", str(self.root), "--flow-type", "Bug",
                      "--user-intent", "t", "--admission-judgment", json.dumps(
                          {"sections_reviewed": ["§2.1", "§2.2"], "matched_signals": [],
                           "recommended_flow_type": "Bug", "ai_rationale": "t"}))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        stem = json.loads(self.audit.read_text().splitlines()[-1])["next_available_id_stem"]
        rec_ts = json.loads(self.audit.read_text().splitlines()[-1])["timestamp"]
        st = self._init(f"{stem}-x")
        self.assertEqual(st["timing_basis"], "v2")
        self.assertEqual(st["prepare_check_at"], rec_ts)

    def test_bypass_leaves_prepare_check_at_none(self):
        env = dict(self.env, TEAMWORK_BYPASS_PREPARE_CHECK="1")
        st = self._init("T-B001-x", env=env)
        self.assertEqual(st["timing_basis"], "v2")
        self.assertIsNone(st["prepare_check_at"])


if __name__ == "__main__":
    unittest.main()
