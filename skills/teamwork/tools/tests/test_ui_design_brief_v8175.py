#!/usr/bin/env python3
"""v8.175 · ui_design brief 携带关键设计规则回归套件。

治本(实证 AON Offer-Analysis case):feature 给已有真实页 `/analytics/offers` 加 tab,
ui_design 却产出孤立**概念页**——没按真实代码复现整页(筛选区/KPI/Top card)→ 用户判
「设计稿不完整、和实际不一致」打回。规范加「扩已有页→复现整页」复现门 · 必须同步推到
brief(v8.170 铁律:spec 改了 brief 没跟 = 规则躺 doc 里被跳过 · 尤其治模型不主动应用判断)。

本套件锁 brief = 这些设计规则的消费点(抗漂移)。
运行:python3 -m pytest skills/teamwork/tools/tests/test_ui_design_brief_v8175.py -q
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

from _v8_stage_specs import _ui_design_brief  # noqa: E402


class TestUiDesignBrief(unittest.TestCase):
    def setUp(self):
        self.brief = _ui_design_brief({})

    def test_reproduce_full_page_rule_pushed(self):
        # v8.175:扩已有页 → 复现整页再加 feature · 禁概念页
        self.assertIn("复现整页", self.brief)
        self.assertIn("概念页", self.brief)        # 「禁概念页」反模式点名
        self.assertIn("真实代码", self.brief)      # 形态来源 = 真实代码不是猜

    def test_v8170_rules_still_pushed(self):
        # 回归护栏:v8.170 的 UI-RULES + dev 顶栏(设计=代码)不许被后续编辑挤掉
        self.assertIn("UI-RULES", self.brief)
        self.assertIn("dev 顶栏", self.brief)  # v8.187:措辞从「dev 全局顶栏」精确化(顶栏只放页面到不了的态)
        self.assertIn("rubric", self.brief)

    def test_brief_renders_without_fstring_break(self):
        # _ui_design_brief({}) 不抛(f-string 占位 {{子项目}}/{{panorama_path}} 正确转义 ·
        # 渲染成字面 {子项目} 给用户替换是预期行为 · 非破裂)· 内容/长度合理
        self.assertIn("UI Design Stage", self.brief)
        self.assertIn("ui_design-complete", self.brief)
        self.assertGreater(len(self.brief), 500)


if __name__ == "__main__":
    unittest.main()
