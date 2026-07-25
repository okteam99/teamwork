"""v8.283:模板减法 —— 砍掉限制模型能力发挥的约束(能力封顶/手段规定/教学示例/重复/环节化)。

判据(用户讨论后确立 · 按规则类型分衰减速率):
- 不衰减必保留:① 证据/验证(信任架构)② 独立采样(相关盲区)③ 用户主权(谁决定)④ 纯机械操作
- 随模型变强而衰减可砍:⑤ 手段规定(HOW-to)⑥ 能力上限 ⑦ 教学示例 ⑧ 重复 ⑨ 环节化自检
本套件锁"砍掉的别回来"+"该留的还在"。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


class TestPrdSlimming(unittest.TestCase):
    def setUp(self):
        self.t = (ROOT / "templates" / "prd.md").read_text(encoding="utf-8")

    def test_no_investigation_depth_caps(self):
        """⑥ 能力上限:调研深度/文件数/时间预算封顶不得作为活约束存在。

        实证:与 v8.282「在 ship 目标分支读真代码」自相矛盾 —— 那个 case 翻车恰恰是 grounding 不够深。
        """
        for cap in ("❌ Read 5+ 个文件", "时间预算：5-10 min", "不超过 10 min", "~500 行内"):
            self.assertNotIn(cap, self.t, f"能力封顶回归:{cap}")

    def test_no_stepwise_investigation_procedure(self):
        """⑤ 手段规定:Step1-4 调研流程(怎么 grep / 读什么 / 怎么内化)已交还模型自主。"""
        for step in ("Step 1: 从用户原始消息", "Step 2: grep 关键词", "Step 3: Read 这些文件"):
            self.assertNotIn(step, self.t, f"HOW-to 流程回归:{step}")

    def test_grounding_goal_retained(self):
        """但目标必须保留:起草前把真实代码现状内化 · 且在 ship 目标分支读(v8.282)。"""
        self.assertIn("起草前把真实代码现状内化", self.t)
        self.assertIn("当前 worktree", self.t)
        self.assertIn("只读不输出", self.t)

    def test_machine_contract_retained(self):
        """① 证据类必保留:机读块 / AC 机器校验 / code_context_read 字段。"""
        for k in ("TEAMWORK-MACHINE", "acceptance_criteria", "code_context_read",
                  "verify-ac.py", "💬 大白话"):
            self.assertIn(k, self.t, f"证据/契约丢失:{k}")

    def test_user_sovereignty_retained(self):
        """③ 用户主权必保留:既有行为变更必入待决策项让用户拍板。"""
        self.assertIn("既有行为变更", self.t)
        self.assertIn("待决策项", self.t)

    def test_adversarial_rule_retained_examples_trimmed(self):
        """① 对称举证规则保留 · ⑦ 两个 worked example 压缩。"""
        self.assertIn("adversarial_self_check", self.t)
        self.assertIn("steelman", self.t)
        self.assertNotIn("dev/handler.go:42", self.t)      # worked example 已压缩

    def test_slimmed(self):
        self.assertLess(len(self.t.splitlines()), 340, "prd.md 应已瘦身到 340 行内")


class TestTechSlimming(unittest.TestCase):
    def setUp(self):
        self.t = (ROOT / "templates" / "tech.md").read_text(encoding="utf-8")

    def test_teaching_examples_trimmed(self):
        """⑦ 教学示例:字段表/文件树/mermaid 填充示例砍掉(模型本来就会)。"""
        for ex in ("RFC 5322 邮箱格式", "snake_case ↔ camelCase",
                   "└── xxx.tsx # 新增/修改 xxx 组件", "participant D as 数据库"):
            self.assertNotIn(ex, self.t, f"教学示例回归:{ex}")

    def test_tdd_granularity_not_prescribed_as_mandate(self):
        """⑤ 手段规定:TDD 红绿粒度示例表砍掉(dev-stage 早已把 TDD 降为「强烈建议」)。"""
        self.assertNotIn("写 XXX 失败测试", self.t)
        self.assertNotIn("实现用户登录模块", self.t)
        self.assertIn("强烈建议的默认", self.t)          # 但节奏建议保留

    def test_core_contracts_retained(self):
        """①②③ 必保留:兜底 ROI 清单 / 现状基线 / 变更四问 / Schema 影响 / 完工自查。"""
        for k in ("兜底清单", "现状基线", "decisive 前提核验", "变更最小化先问",
                  "Schema 影响分析", "FK 决策", "完工自查", "不静默吞异常",
                  "地板不是天花板"):
            self.assertIn(k, self.t, f"核心契约丢失:{k}")

    def test_machine_gate_duplicates_removed(self):
        """⑧ 重复:完工自查里与机器门 100% 重复的两项去掉(test exit-code / commit changeset)。"""
        self.assertNotIn("- [ ] 已有测试无回归(exit-code=0", self.t)
        self.assertNotIn("- [ ] commit message 含 Feature ID", self.t)

    def test_slimmed(self):
        self.assertLess(len(self.t.splitlines()), 250, "tech.md 应已瘦身到 250 行内")
