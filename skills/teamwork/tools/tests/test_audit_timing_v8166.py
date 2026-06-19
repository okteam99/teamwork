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
        # v8.172:工作阶段总和 100 · 最耗时(工作)dev 50(50%)· 无 pm_acceptance 故无等用户段
        self.assertIn("工作阶段总和 100m", analysis)
        self.assertIn("最耗时(工作)dev 50m(50%)", analysis)

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
        self.assertIn("最耗时(工作)goal 15m(100%)", analysis)

    def test_await_user_stage_excluded_from_longest(self):
        # v8.172:pm_acceptance 等用户的墙钟不计入「最耗时(工作)」· 单列为决策等待
        state = {
            "completed_stages": ["goal", "dev", "pm_acceptance"],
            "stage_contracts": {
                "goal": {"duration_minutes": 20},
                "dev": {"duration_minutes": 40},
                "pm_acceptance": {"duration_minutes": 200},  # 等用户墙钟 · 占 77% 但不该算最耗时
            },
        }
        breakdown, analysis = _stage_durations(state)
        self.assertIn("pm_acceptance 200m", breakdown)                # breakdown 仍全列
        self.assertIn("工作阶段总和 60m", analysis)                    # 工作=goal+dev=60 · 不含 pm_acceptance
        self.assertIn("最耗时(工作)dev 40m", analysis)                # 最耗时是 dev 不是 pm_acceptance
        self.assertIn("pm_acceptance 200m=用户决策等待", analysis)     # 单列
        self.assertNotIn("最耗时(工作)pm_acceptance", analysis)       # 绝不把等用户当最耗时

    def test_empty_returns_none(self):
        self.assertEqual(_stage_durations({}), (None, None))
        self.assertEqual(
            _stage_durations({"completed_stages": ["x"], "stage_contracts": {}}),
            (None, None),
        )


if __name__ == "__main__":
    unittest.main()
