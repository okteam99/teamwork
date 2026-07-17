"""v8.250:micro 流程重构 = execute → ship(去 dev 门禁 + pm_acceptance)。

用户拍板:prepare 之后 AI 自由完成任务(自选 model/subagent/workflow/测试 · 无规范限制)· 然后 ship。
唯一硬边界 = worktree 路径 + 准入白名单;用户验收从 pm_acceptance 挪到 ship1 MR diff。
"""
import unittest

import _v8_engine as E
import _v8_stage_specs as S
import state as ST


class TestMicroChain(unittest.TestCase):
    def test_chain_is_execute_ship(self):
        self.assertEqual([s[0] for s in E.FLOW_STAGE_CHAIN["Micro"]], ["execute", "ship"])

    def test_transition_graph(self):
        self.assertEqual(ST.MICRO_FLOW, {"execute": ["ship"], "ship": ["completed"], "completed": []})
        self.assertEqual(ST.resolve_flow_graph("Feature", "micro"), ST.MICRO_FLOW)

    def test_initial_stage_execute(self):
        self.assertEqual(ST.DEFAULT_INITIAL_STAGE["Micro"], "execute")

    def test_no_pm_acceptance_no_dev_in_micro(self):
        stages = {s[0] for s in E.FLOW_STAGE_CHAIN["Micro"]}
        self.assertNotIn("dev", stages)
        self.assertNotIn("pm_acceptance", stages)
        self.assertNotIn("review", stages)
        self.assertNotIn("test", stages)


class TestExecuteSpec(unittest.TestCase):
    def test_registered_micro_only(self):
        self.assertIn("execute", S.STAGE_SPECS)
        self.assertEqual(S.STAGE_SPECS["execute"].allowed_flow_types, ["Micro"])

    def test_zero_gates(self):
        spec = S.STAGE_SPECS["execute"]
        self.assertEqual(spec.prerequisites, [])
        self.assertEqual(spec.artifacts, [])
        self.assertEqual(spec.evidence_checks, [])

    def test_transition_to_ship(self):
        st = {"flow_type": "Feature", "preset": "micro", "current_stage": "execute"}
        self.assertEqual(S._execute_transition(st), "ship")

    def test_brief_carries_hard_boundaries(self):
        st = {"flow_type": "Feature", "preset": "micro"}
        b = S._execute_brief(st)
        self.assertIn("worktree", b)          # 硬边界 1
        self.assertIn("准入白名单", b)          # 硬边界 2
        self.assertIn("无规范限制", b)
        self.assertIn("execute-complete", b)


class TestShipEntryFromExecute(unittest.TestCase):
    def test_pm_approved_ship_skips_for_micro(self):
        st = {"flow_type": "Feature", "preset": "micro"}
        self.assertTrue(S._check_pm_approved_ship(st, None))

    def test_pm_approved_ship_still_enforced_for_feature(self):
        st = {"flow_type": "Feature", "preset": "full",
              "stage_contracts": {"pm_acceptance": {"output_satisfied": False}}}
        self.assertFalse(S._check_pm_approved_ship(st, None))


if __name__ == "__main__":
    unittest.main()
