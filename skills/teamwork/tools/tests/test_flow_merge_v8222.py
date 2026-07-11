#!/usr/bin/env python3
"""v8.222 · 物化校验 flow 归一审计:v8.220 合并后 10 处 legacy 比较是死门 · 统一 _flow_key。

用户点名检查:python 脚本物化校验是否匹配合并。实锤:state 只存 Feature+preset 后 ·
`flow_type == "敏捷需求"/"Micro"` 全部失配(最重:Micro 错拿 initial=goal)。
"""
from __future__ import annotations
import sys, unittest
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _v8_stage_specs as S  # noqa: E402
from state import internal_flow_key, DEFAULT_INITIAL_STAGE  # noqa: E402


class TestFlowKey(unittest.TestCase):
    def test_internal_key_mapping(self):
        self.assertEqual(internal_flow_key("Feature", "micro"), "Micro")
        self.assertEqual(internal_flow_key("Feature", "lite"), "敏捷需求")
        self.assertEqual(internal_flow_key("Feature", "full"), "Feature")
        self.assertEqual(internal_flow_key("Micro"), "Micro")      # legacy 原样
        self.assertEqual(internal_flow_key("Bug", "micro"), "Bug")  # preset 只作用 Feature

    def test_micro_initial_stage_dev(self):
        # 🔴 v8.222 修的真 bug:归一后直接查表 → micro 错拿 goal
        self.assertEqual(DEFAULT_INITIAL_STAGE[internal_flow_key("Feature", "micro")], "dev")

    def test_specs_flow_key(self):
        self.assertEqual(S._flow_key({"flow_type": "Feature", "preset": "micro"}), "Micro")
        self.assertEqual(S._flow_key({"flow_type": "Feature", "preset": "lite"}), "敏捷需求")
        self.assertEqual(S._flow_key({"flow_type": "敏捷需求"}), "敏捷需求")  # 存量 state 兼容


class TestRevivedGates(unittest.TestCase):
    def test_needs_ui_true_blocked_for_lite(self):
        # 死门复活:Feature+lite + needs-ui=true 必须仍被拦
        st = {"flow_type": "Feature", "preset": "lite"}
        ok, msg = S._evidence_needs_ui_decided(st, NS(needs_ui="true"))
        self.assertFalse(ok)
        self.assertIn("敏捷", msg)

    def test_agile_check_revived(self):
        self.assertTrue(S._check_flow_is_agile({"flow_type": "Feature", "preset": "lite"}, None))
        self.assertFalse(S._check_flow_is_agile({"flow_type": "Feature", "preset": "full"}, None))

    def test_micro_test_gate_revived(self):
        self.assertTrue(S._check_test_done_or_micro({"flow_type": "Feature", "preset": "micro"}, None))

    def test_micro_dev_next_stage(self):
        self.assertEqual(S._dev_transition({"flow_type": "Feature", "preset": "micro"}), "pm_acceptance")

if __name__ == "__main__":
    unittest.main()
