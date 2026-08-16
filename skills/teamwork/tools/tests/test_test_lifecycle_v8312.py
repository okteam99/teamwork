"""v8.312:测试生命周期三层(用户提出并两次拍板:①只写规范不配门 + L3 落 scratch ②进 L1 必须有充足理由)。

与 R-SP-1b(v8.299)不是翻案而是补另一半:那轮实测证明**执行**成本在进程派生不在数量,
但**维护**成本按语料线性(AI 每次重构都要同步全部测试 · CI 墙钟逐 feature 累加)——
执行便宜 ≠ 维护便宜。R-SP-1b 管「不合并断言」,本版管「留不留 / 在哪跑」,两条正交并立。

设计要点:
- 判据按「失败信号的消费者」不按阶段名:交付后还有谁需要它失败的信号?没有 = 脚手架。
- **L1 准入是例外不是默认**(用户拍板):`ci: true` 必带 `ci_reason`(拦什么级别的事故)——
  与 WS 拆分「默认合并 · 拆分是例外」同构;理由由模板字段承载(结构可见 · 不配扫描门)。
- L3 复用既有 scratch 机制(与「看一眼截图不落 worktree」同一条规则的同构应用)——
  临时 case 不是「写了再清」,是**写的时候就不进仓库**,清退成本归零。
- 用户裁定**不配机器门** —— 本文件锁的是规范文本本身(条款在 · 单源结构对),不是行为。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestLifecycleSingleSourceInTc(unittest.TestCase):
    """tc.md 是三层定义的单源 —— tech-rules 与 dev-stage 只 cite 不复述细节。"""

    def setUp(self):
        self.t = _read("templates/tc.md")

    def test_three_layers_defined(self):
        for k in ("L1 · CI 契约层", "L2 · 回归层", "L3 · 脚手架"):
            self.assertIn(k, self.t, f"层定义缺失:{k}")

    def test_criterion_is_failure_consumer_not_stage_name(self):
        self.assertIn("交付后还有谁需要它失败的信号", self.t)

    def test_l1_admission_is_exception_with_reason(self):
        """🔴 用户拍板:进 L1 一定要有充足的理由 —— 默认不进 · 理由说清拦什么事故。"""
        self.assertIn("默认不进", self.t)
        self.assertIn("ci_reason", self.t)
        self.assertIn("拦住什么级别的事故", self.t)
        self.assertIn("不算充足理由", self.t, "未排除「顺手写的/覆盖率好看」类假理由")

    def test_frontmatter_carries_the_reason_field(self):
        """理由靠模板字段承载(v8.302 判据:载体的形状决定内容会不会出现)· 不靠扫描门。"""
        self.assertIn("ci: true", self.t)
        self.assertIn('ci_reason: "', self.t)

    def test_second_tc_boundary_added(self):
        """与「换实现就要改的不属于 TC」并列的第二条:交付后不需再跑的不属于 TC。"""
        self.assertIn("交付后不需要再跑的,不属于 TC", self.t)
        self.assertIn("换实现就要改的内容,不属于 TC", self.t, "原第一条边界被误伤")

    def test_ci_wiring_stays_project_sovereign(self):
        self.assertIn("归项目主权", self.t)

    def test_rsp1b_boundary_restated_not_conflated(self):
        """分层不许被读成「合并断言省时间」—— R-SP-1b 边界原文引用留在场。"""
        self.assertIn("不为省时间合并断言", self.t)
        sp = _read("standards/scripts-policy.md")
        self.assertIn("手段是共享 setup,不是合并断言", sp, "R-SP-1b 本体被动过")


class TestScaffoldTestsLandInScratch(unittest.TestCase):
    """L3 复用 scratch 机制 —— 不入仓库 · 随 ship2 回收 · 与截图同规。"""

    def test_hard_rules_carries_the_rule(self):
        t = _read("standards/tech-rules.md")
        self.assertIn("scaffold-tests/", t)
        self.assertIn("不入仓库", t)
        self.assertIn("交付后还有谁需要它失败的信号", t, "判据未进必读白名单")
        self.assertIn("执行便宜 ≠ 维护便宜", t, "缺成本模型 why → 会被当成任意规定")

    def test_scratch_usage_lists_scaffold_dir(self):
        t = _read("docs/conventions.md")
        self.assertIn("scaffold-tests/", t)

    def test_dev_stage_has_action_point_rule(self):
        """写测试的动作点在 dev —— 规则必须到场(v8.301:写进别处 ≠ 到达)。"""
        t = _read("stages/dev-stage.md")
        self.assertIn("写测试时就定生命周期层", t)
        self.assertIn("scaffold-tests/", t)
        self.assertIn("ci_reason", t)


class TestNoHardGateAdded(unittest.TestCase):
    """用户裁定「只写规范不配门」—— 本版不得往 evidence_checks 加测试清退类硬门。"""

    def test_no_lifecycle_evidence_check(self):
        # 标记选「只有造这道门才会出现」的词(裸 "scaffold" 会撞既有 scaffold_hints 模板机制)
        src = _read("tools/_v8_stage_specs.py")
        for marker in ("scaffold-tests", "ci_reason", "test_lifecycle"):
            self.assertNotIn(marker, src,
                             f"发现疑似生命周期硬门({marker})—— 用户裁定只写规范不配门")


class TestLineCountClaimsRemoved(unittest.TestCase):
    """顺手清的一类数字宣称:「~50 行白名单」写死在三处 · 本版已 60 行 —— 数字宣称必漂,全部去数。"""

    def test_no_hardcoded_line_claims(self):
        for rel in ("standards/tech-rules.md", "stages/dev-stage.md", "stages/blueprint-stage.md"):
            self.assertNotIn("~50 行", _read(rel), f"{rel} 仍写死行数宣称")
        self.assertIn("行数不写死", _read("standards/tech-rules.md"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
