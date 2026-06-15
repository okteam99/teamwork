#!/usr/bin/env python3
"""v8.166 · audit 记录加各阶段耗时 + 耗时分析 + 主对话模型回归套件。

用户(看 TermPro audit 截图):实际数据该加 ① 各阶段耗时 ② 耗时分析 ③ 主对话模型。
- 各阶段耗时/耗时分析:工具从 stage_contracts.duration_minutes 确定性抽。
- 主对话:host(state.host · 确定性)+ 模型(PMO ship-finalize --main-model 声明)。

运行:python3 -m pytest skills/teamwork/tools/tests/test_audit_timing_v8166.py -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

from _v8_ship import _stage_durations  # type: ignore  # noqa: E402


class TestStageDurations(unittest.TestCase):
    def test_normal_breakdown_and_analysis(self):
        state = {
            "completed_stages": ["goal", "blueprint", "dev"],
            "stage_contracts": {
                "goal": {"duration_minutes": 20},
                "blueprint": {"duration_minutes": 30},
                "dev": {"duration_minutes": 50},
            },
        }
        breakdown, analysis = _stage_durations(state)
        self.assertEqual(breakdown, "goal 20m · blueprint 30m · dev 50m")
        # 阶段总和 100 · 最耗时 dev 50(50%)
        self.assertIn("阶段总和 100m", analysis)
        self.assertIn("最耗时 dev 50m(50%)", analysis)

    def test_order_follows_completed_stages(self):
        # breakdown 按 completed_stages 顺序 · 非 dict 顺序
        state = {
            "completed_stages": ["dev", "goal"],
            "stage_contracts": {
                "goal": {"duration_minutes": 10},
                "dev": {"duration_minutes": 40},
            },
        }
        breakdown, _ = _stage_durations(state)
        self.assertEqual(breakdown, "dev 40m · goal 10m")

    def test_skips_stages_without_duration(self):
        # 无 duration_minutes 的 stage(如 ship 进行中)跳过 · 不崩
        state = {
            "completed_stages": ["goal", "ship"],
            "stage_contracts": {
                "goal": {"duration_minutes": 15},
                "ship": {"started_at": "..."},  # 无 duration
            },
        }
        breakdown, analysis = _stage_durations(state)
        self.assertEqual(breakdown, "goal 15m")
        self.assertIn("最耗时 goal 15m(100%)", analysis)

    def test_empty_returns_none(self):
        self.assertEqual(_stage_durations({}), (None, None))
        self.assertEqual(
            _stage_durations({"completed_stages": ["x"], "stage_contracts": {}}),
            (None, None),
        )


if __name__ == "__main__":
    unittest.main()
