"""v8.276:活动时间戳挖掘 —— 从墙钟 span 扣跨 session 空闲(治 goal 1012m/await+3m 类)。

信号 = stage 窗口内 git commit + 产物 mtime + round 边界;相邻间隔 ≤ 阈值(默认 30m)累加为
active_minutes,间隔 > 阈值判空闲扣除。无中间活动信号 → None(回退墙钟)。
顺带:P3 宽松解析(格式变体不静默丢)+ ②restart 重置 started_at/await。
"""
import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import _v8_engine as E
import _v8_ship as SHIP


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class TestParseFlexible(unittest.TestCase):
    def test_z_suffix(self):
        self.assertIsNotNone(E._parse_iso_flexible("2026-07-22T10:00:00Z"))

    def test_fractional_and_offset_no_longer_dropped(self):
        # P3:严格 strptime 会抛 · 宽松解析吃下
        self.assertIsNotNone(E._parse_iso_flexible("2026-07-22T10:00:00.500Z"))
        self.assertIsNotNone(E._parse_iso_flexible("2026-07-22T10:00:00+00:00"))

    def test_garbage_returns_none(self):
        self.assertIsNone(E._parse_iso_flexible("not-a-date"))
        self.assertIsNone(E._parse_iso_flexible(None))


class TestMineActiveMinutes(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-mine-"))
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)

    def _touch(self, name, when):
        p = self.tmp / name
        p.write_text("x", encoding="utf-8")
        import os
        ts = when.timestamp()
        os.utime(p, (ts, ts))
        return p

    def test_overnight_idle_excluded(self):
        """起草 60m 后过夜 · 次日 complete —— active≈60m 非 17h(goal 1012m 场景)。"""
        t0 = datetime(2026, 7, 21, 9, 0, tzinfo=timezone.utc)
        # 活动集中在前 60m(每 15m 一次产物写)· 之后 16h 无信号 = 空闲
        for m in (15, 30, 45, 60):
            self._touch(f"PRD-v{m}.md", t0 + timedelta(minutes=m))
        t1 = t0 + timedelta(hours=17)          # 次日 complete
        active = E._mine_active_minutes(self.tmp, _iso(t0), _iso(t1), {})
        self.assertIsNotNone(active)
        self.assertLessEqual(active, 90, f"active={active} 应≈60m 非墙钟 1020m")
        self.assertGreaterEqual(active, 45)

    def test_dense_work_counts_full(self):
        """全程密集活动(≤阈值间隔)→ active≈span。"""
        t0 = datetime(2026, 7, 21, 9, 0, tzinfo=timezone.utc)
        for m in range(10, 120, 10):
            self._touch(f"f{m}.md", t0 + timedelta(minutes=m))
        t1 = t0 + timedelta(minutes=120)
        active = E._mine_active_minutes(self.tmp, _iso(t0), _iso(t1), {})
        self.assertGreaterEqual(active, 100)

    def test_no_intermediate_signal_returns_none(self):
        """窗口内零活动信号 → None(不敢判空闲 · 回退墙钟)。"""
        t0 = datetime(2026, 7, 21, 9, 0, tzinfo=timezone.utc)
        t1 = t0 + timedelta(hours=5)
        self.assertIsNone(E._mine_active_minutes(self.tmp, _iso(t0), _iso(t1), {}))

    def test_bad_timestamps_return_none(self):
        self.assertIsNone(E._mine_active_minutes(self.tmp, "bad", "worse", {}))

    def test_threshold_configurable(self):
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"idle_threshold_minutes": 5}), encoding="utf-8")
        self.assertEqual(E._idle_threshold_minutes(self.tmp), 5)

    def test_threshold_default(self):
        self.assertEqual(E._idle_threshold_minutes(self.tmp), 30)


class TestTimingSplitPrefersActive(unittest.TestCase):
    def test_split_uses_active_when_present(self):
        state = {"completed_stages": ["goal"], "stage_contracts": {"goal": {
            "duration_minutes": 1020, "active_minutes": 60, "await_minutes": 3}}}
        ai, wait = SHIP._timing_split(state)
        self.assertEqual(ai, 60)          # active · 非 1020−3
        self.assertEqual(wait, 3)

    def test_split_fallback_without_active(self):
        state = {"completed_stages": ["goal"], "stage_contracts": {"goal": {
            "duration_minutes": 100, "await_minutes": 10}}}
        ai, wait = SHIP._timing_split(state)
        self.assertEqual(ai, 90)          # 回退 duration−await
        self.assertEqual(wait, 10)

    def test_breakdown_uses_active(self):
        state = {"completed_stages": ["goal"], "stage_contracts": {"goal": {
            "duration_minutes": 1020, "active_minutes": 60, "await_minutes": 3}}}
        breakdown, _ = SHIP._stage_durations(state)
        self.assertIn("goal 60m", breakdown)
        self.assertNotIn("goal 1017m", breakdown)


if __name__ == "__main__":
    unittest.main()
