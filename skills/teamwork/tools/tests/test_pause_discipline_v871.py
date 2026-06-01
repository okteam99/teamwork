#!/usr/bin/env python3
"""v8.71 · 暂停点纪律「无暂停 stage」强化(治本 SDK-F038 case)。

治本:AI 在 blueprint→dev(无授权暂停点的连续执行 stage)自造「如何推进 dev /
落地节奏由你定」伪决策暂停点 · 把改动大/破坏式/不可逆/用户参与设计当暂停理由。
_render_pause_discipline 现对无暂停 stage 追加强化段(禁伪决策暂停 · 体量大用 subagent)·
且自动流转 emit 也带下一 stage 纪律(AI 转移那刻即见 · 不靠之后 xx-start)。

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


# 强化段标志短语(无暂停 stage 才出现)
HARDENING_MARKERS = ("不得自造暂停", "伪决策", "subagent", "改动大", "执行节奏" )


class TestNoPauseHardening(unittest.TestCase):
    """无暂停 stage → 追加「禁自造伪决策暂停 + 体量大用 subagent」强化。"""

    def test_no_pause_stage_adds_hardening(self):
        out = _render_pause_discipline("无暂停 · 完成后自动转 review")
        self.assertIn("无授权暂停点", out)
        self.assertIn("subagent", out)
        self.assertIn("伪决策", out)
        # 命中 case 里 AI 用过的具体借口字面 · 直接点名
        self.assertIn("改动大", out)
        self.assertIn("破坏式", out)
        self.assertIn("不可逆", out)

    def test_normal_pause_no_hardening(self):
        """有授权暂停点的 stage(如 goal Substep 6)→ 不加无暂停强化段。"""
        out = _render_pause_discipline("Substep 6 · 用户最终确认(全员 review 通过后)")
        self.assertNotIn("无授权暂停点", out)
        self.assertNotIn("伪决策", out)
        self.assertNotIn("subagent", out)
        # 但基础纪律仍在
        self.assertIn("暂停点纪律", out)
        self.assertIn("唯一授权暂停", out)

    def test_base_discipline_always_present(self):
        for app in ("无暂停 · 完成后自动转 review",
                    "Substep 6 · 用户最终确认"):
            out = _render_pause_discipline(app)
            self.assertIn("暂停点纪律", out)
            self.assertIn("04-PAUSE-POINT-DISCIPLINE.md", out)
            self.assertIn(app, out)  # 具体描述被填入


class TestContinuousStagesTriggerHardening(unittest.TestCase):
    """连续执行 stage(dev 等 · authorized_pause_point 含「无暂停」)必触发强化。

    防回归:有人改 dev 的 pause point 字面 · 若不再含「无暂停」· 此 test 红 ·
    提醒同步强化逻辑(治本 SDK-F038 = dev 无暂停 · AI 自造暂停)。
    """

    def test_dev_spec_is_no_pause_and_triggers_hardening(self):
        dev = STAGE_SPECS["dev"]
        self.assertIn("无暂停", dev.authorized_pause_point,
                      "dev 是连续执行 stage · authorized_pause_point 应含「无暂停」")
        out = _render_pause_discipline(dev.authorized_pause_point)
        self.assertIn("subagent", out, "dev 入口纪律应含 subagent 自决指引")
        self.assertIn("不得自造暂停", out)

    def test_at_least_one_no_pause_stage_exists(self):
        no_pause = [n for n, s in STAGE_SPECS.items()
                    if "无暂停" in (s.authorized_pause_point or "")]
        self.assertIn("dev", no_pause)
        # 每个无暂停 stage 的渲染都带强化
        for n in no_pause:
            out = _render_pause_discipline(STAGE_SPECS[n].authorized_pause_point)
            self.assertIn("subagent", out, f"{n} 无暂停 · 应触发 subagent 强化")


if __name__ == "__main__":
    unittest.main(verbosity=2)
