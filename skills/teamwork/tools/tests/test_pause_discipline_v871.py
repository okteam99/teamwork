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

from _v8_engine import _render_pause_discipline  # type: ignore  # noqa: E402
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


class TestSubagentInPauseDisciplineV874(unittest.TestCase):
    """v8.74:subagent 不再独立成 brief 段(防 brief 膨胀)· 仅暂停点纪律内 1 行提及。

    治本:用户指出 ① 「标准执行手段」措辞促 AI 过度使用 → 改「可选 · 详 SKILL.md」;
    ② brief 不应越来越大 → 删 _render_execution_capability 独立段 · 指引移 SKILL.md/stage.md。
    """

    def test_pause_line_mentions_subagent_as_optional(self):
        out = _render_pause_discipline("无暂停 · 完成后自动转 review")
        self.assertIn("subagent", out)
        self.assertIn("可按需", out)          # 可选措辞 · 非「标准/必用」
        self.assertIn("SKILL.md", out)        # 指向 spec · 不在 brief 展开

    def test_render_execution_capability_removed(self):
        """独立执行手段段已删(防 brief 膨胀)· 函数不应再存在。"""
        import _v8_engine  # type: ignore
        self.assertFalse(hasattr(_v8_engine, "_render_execution_capability"),
                         "v8.74 已删 _render_execution_capability(指引移 SKILL.md/stage.md)")

    def test_pause_discipline_no_dedicated_execution_section(self):
        out = _render_pause_discipline("无暂停 · 完成后自动转 review")
        self.assertNotIn("🧩 执行手段", out)   # 不再有独立段标题
        self.assertNotIn("标准配置", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
