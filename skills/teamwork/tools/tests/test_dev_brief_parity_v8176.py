#!/usr/bin/env python3
"""v8.176 · dev brief 携带「设计↔实际一致性核对」闸回归套件。

治本:「最大限度保障设计稿和实际效果一致」需闭环两端 —— 设计时构造(ui_design §3 导入真实页源)
+ dev 后验证(dev §3 把已有的「并排对照·可选」升成必做的四要素核对 + 留证 + 背离 reconcile)。
验证侧若只改 stage.md 不推 brief,模型 dev 时不会主动核对(v8.170 再验:brief 推才生效)。
本套件锁 dev brief = 这道落地闸的消费点。

运行:python3 -m pytest skills/teamwork/tools/tests/test_dev_brief_parity_v8176.py -q
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

from _v8_stage_specs import _dev_brief  # noqa: E402


class TestDevBriefParity(unittest.TestCase):
    def setUp(self):
        self.brief = _dev_brief({})

    def test_parity_gate_pushed(self):
        # v8.176:UI feature dev 后必做设计↔实际四要素核对
        self.assertIn("设计↔实际", self.brief)
        self.assertIn("ui_design", self.brief)        # 条件:走过 ui_design 才适用
        self.assertIn("四要素", self.brief)            # 核对的是四要素(非像素)

    def test_divergence_handling_pushed(self):
        # 背离 → 修实现 or 回 ui_design · 不在 dev 顺手改设计
        self.assertIn("背离", self.brief)
        self.assertTrue("修实现" in self.brief or "回 ui_design" in self.brief)

    def test_brief_renders(self):
        self.assertIn("Dev Stage", self.brief)
        self.assertIn("dev-complete", self.brief)
        self.assertGreater(len(self.brief), 400)


if __name__ == "__main__":
    unittest.main()
