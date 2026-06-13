#!/usr/bin/env python3
"""v8.76 · 简洁性(防过度设计)counter-lens 落地校验(治本 SDK-F038 过度设计)。

治本:所有评审视角都偏「加 rigor」(PM 看 AC 完整 · QA 看边界覆盖 · external 找缺口)·
无人审「是否过度设计 / 职责是否归错层 / 能否更简单」。SDK-F038 实证:16 AC 全绿 +
3 轮 external 闭环 · 用户仍在 pm_acceptance 一眼看出 SDK 过度复杂(哑管道焊进字段语义)。

修复:Architect 成为唯一的**简洁性 counter-lens** · 落进 architect role + goal/blueprint/
review stage 评审视角 + PRD 评审聚焦(业务目标/可实现/恰当简洁 · AC 写行为价值高度)。

本测试锁定这些 spec 文案不被回退删除。

运行:
    python3 -m pytest skills/teamwork/tools/tests/test_simplicity_lens_v876.py -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent.parent  # tools/tests → tools → skills/teamwork


def _read(rel: str) -> str:
    return (SKILL / rel).read_text(encoding="utf-8")


class TestArchitectOwnsSimplicityLens(unittest.TestCase):
    """Architect role telos 必含简洁性 / 防过度设计 + 独占 counter-lens 定位。"""

    def test_architect_telos_has_simplicity(self):
        t = _read("roles/architect.md")
        self.assertIn("简洁性", t)
        self.assertIn("过度设计", t)
        self.assertIn("counter-lens", t)
        # 点名其余角色偏加 rigor · Architect 是唯一简洁性视角
        self.assertIn("职责", t)


class TestStageDocsCarrySimplicityLens(unittest.TestCase):
    """goal / blueprint / review 评审视角必含简洁性 lens。"""

    def test_goal_stage_focus_and_lens(self):
        t = _read("stages/goal-stage.md")
        # PRD 评审聚焦:业务目标 + 可实现 + 恰当简洁
        self.assertIn("PRD 评审聚焦", t)
        self.assertIn("业务目标", t)
        self.assertIn("恰当简洁", t)
        # AC 写行为/价值高度 · 不下沉机制
        self.assertIn("行为 / 价值", t)
        # Architect 简洁性 counter-lens
        self.assertIn("简洁性 counter-lens", t)
        # v8.149:goal 不做 external(过度设计防线 = Architect 内审 · 细节/异质归 blueprint)
        self.assertIn("goal 不做 external", t)

    def test_blueprint_tech_review_simplicity(self):
        t = _read("stages/blueprint-stage.md")
        self.assertIn("过度设计", t)
        self.assertIn("简洁性", t)
        # 拦在 TECH 比拦在代码便宜
        self.assertIn("TECH", t)

    def test_review_stage_architect_simplicity(self):
        t = _read("stages/review-stage.md")
        self.assertIn("简洁性", t)
        self.assertIn("counter-lens", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
