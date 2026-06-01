#!/usr/bin/env python3
"""v8.71→v8.72 · 暂停点纪律「禁执行节奏伪决策 + 体量大用 subagent」(治本 SDK-F038)。

治本:AI 在 blueprint→dev(无授权暂停点的连续执行 stage)自造「如何推进 dev /
落地节奏由你定」伪决策暂停点 · 把改动大/破坏式/不可逆/用户参与设计当暂停理由。

v8.71:无暂停 stage(dev/blueprint/blueprint_lite/test)追加强化 + 自动流转 emit 带纪律。
v8.72:执行节奏伪决策 + subagent 自决改为**通用红线**(所有 stage)—— 有授权暂停点的
stage(goal/ui_design/review/...)也可能在「那一个」授权暂停**之外**自造执行节奏伪暂停;
「无授权暂停点 · 任何暂停都违规」抬头仍仅无暂停 stage。

运行:
    python3 -m pytest skills/teamwork/tools/tests/test_pause_discipline_v871.py -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS))

from _v8_engine import (  # type: ignore  # noqa: E402
    _render_execution_capability,
    _render_pause_discipline,
)
from _v8_stage_specs import STAGE_SPECS  # type: ignore  # noqa: E402


class TestNoPauseStageHeadline(unittest.TestCase):
    """无暂停 stage → 额外「任何暂停都违规」抬头(连续执行 stage 专属)。"""

    def test_no_pause_stage_has_headline(self):
        out = _render_pause_discipline("无暂停 · 完成后自动转 review")
        self.assertIn("无授权暂停点", out)
        self.assertIn("任何暂停都是违规", out)

    def test_pause_stage_no_headline(self):
        """有授权暂停点的 stage(如 goal Substep 6)→ 不加无暂停抬头。"""
        out = _render_pause_discipline("Substep 6 · 用户最终确认(全员 review 通过后)")
        self.assertNotIn("无授权暂停点", out)
        self.assertNotIn("任何暂停都是违规", out)
        # 但基础纪律仍在
        self.assertIn("暂停点纪律", out)
        self.assertIn("唯一授权暂停", out)


class TestUniversalExecutionPacingGuard(unittest.TestCase):
    """v8.72:执行节奏伪决策 + subagent = 通用红线 · 所有 stage(含有授权暂停的)都带。"""

    def test_pause_stage_also_has_subagent_and_pacing_guard(self):
        """治本核心:有授权暂停点的 stage 也要有「禁执行节奏伪决策 + subagent」。"""
        out = _render_pause_discipline("Substep 6 · 用户最终确认(全员 review 通过后)")
        self.assertIn("subagent", out, "有授权暂停的 stage 也应有 subagent 自决指引")
        self.assertIn("执行节奏", out)
        self.assertIn("改动大", out)  # 点名 AI 用过的具体借口

    def test_every_stage_has_pacing_guard(self):
        """所有 11 个 stage 的入口纪律都含执行节奏护栏 + subagent(通用)。"""
        for name, spec in STAGE_SPECS.items():
            app = spec.authorized_pause_point or "x"
            out = _render_pause_discipline(app)
            self.assertIn("subagent", out, f"{name} 应含 subagent 自决指引")
            self.assertIn("执行节奏", out, f"{name} 应含执行节奏伪决策护栏")

    def test_headline_only_for_no_pause_stages(self):
        """「无授权暂停点」抬头只出现在无暂停 stage · 不误加到有授权暂停的 stage。"""
        for name, spec in STAGE_SPECS.items():
            app = spec.authorized_pause_point or ""
            out = _render_pause_discipline(app)
            if "无暂停" in app:
                self.assertIn("无授权暂停点", out, f"{name} 无暂停 · 应有抬头")
            else:
                self.assertNotIn("无授权暂停点", out, f"{name} 有授权暂停 · 不应有抬头")


class TestBaseDisciplineAlwaysPresent(unittest.TestCase):
    def test_base_present_both_kinds(self):
        for app in ("无暂停 · 完成后自动转 review",
                    "Substep 6 · 用户最终确认"):
            out = _render_pause_discipline(app)
            self.assertIn("暂停点纪律", out)
            self.assertIn("04-PAUSE-POINT-DISCIPLINE.md", out)
            self.assertIn(app, out)  # 具体描述被填入


class TestContinuousStagesRegression(unittest.TestCase):
    """防回归:dev/blueprint/blueprint_lite/test 仍是无暂停 · 触发抬头 + subagent。

    有人改 dev 的 pause point 字面 · 若不再含「无暂停」· 此 test 红 ·
    提醒同步强化逻辑(治本 SDK-F038 = dev 无暂停 · AI 自造暂停)。
    """

    EXPECTED_NO_PAUSE = {"dev", "blueprint", "blueprint_lite", "test"}

    def test_expected_no_pause_set(self):
        actual = {n for n, s in STAGE_SPECS.items()
                  if "无暂停" in (s.authorized_pause_point or "")}
        self.assertEqual(actual, self.EXPECTED_NO_PAUSE,
                         f"无暂停 stage 集合变化 · 实际 {actual}")

    def test_dev_triggers_headline_and_subagent(self):
        out = _render_pause_discipline(STAGE_SPECS["dev"].authorized_pause_point)
        self.assertIn("无授权暂停点", out)
        self.assertIn("subagent", out)


class TestExecutionCapabilityV873(unittest.TestCase):
    """v8.73:subagent = 标准执行手段 · 每 stage 起手评估(非任务大才用)。

    治本:用户指出「合理使用 subagent 应是各个 stage 必须知道的点 · 不是任务大才想起」·
    故独立成段 · 每 stage brief 都带 · 框成主动标准手段(非 reactive 兜底)。
    """

    def test_segment_is_proactive_standard(self):
        out = _render_execution_capability()
        self.assertIn("subagent", out)
        self.assertIn("标准", out)
        self.assertIn("起手", out)            # 每 stage 起手评估
        # 主动框架 · 明确「不是任务大才用」
        self.assertIn("非任务大才用", out)

    def test_segment_mentions_benefits_and_boundary(self):
        out = _render_execution_capability()
        self.assertIn("并行", out)            # 并行提速
        self.assertIn("context 干净", out)    # 主编排 context 干净
        self.assertIn("worktree", out)        # 边界:子 agent 守 worktree 纪律
        self.assertIn("不外包整个 stage", out)  # 边界:不跳流程

    def test_no_size_gating_language(self):
        """不应把 subagent 框成「工作量大 / session 吃紧才用」的兜底。"""
        out = _render_execution_capability()
        # 段落主张是「标准 · 起手评估」· 不以「工作量大」为前置条件触发
        self.assertNotIn("工作量大 →", out)
        self.assertNotIn("工作量大 / session 吃紧 →", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
