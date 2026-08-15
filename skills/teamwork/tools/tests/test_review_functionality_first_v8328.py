"""finding 准入:功能优先 · 复杂度守恒(用户拍板)。

拍板原文:「review 的时候注意,优先功能实现,不要做过多的兜底、测试门之类的,
不要为了不重要的 bug 增加整体复杂度,真功能缺陷要报,PRD 和 TECH review 等都需要考虑。」

四载体:review-stage 规则 2.5(单源全文)· goal/blueprint 冷审各一行指针 ·
claude-agents/reviewer.md prompt 主体自含压缩版(动作点 —— subagent 只读 prompt)。
"""
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
REVIEW = SKILL_ROOT / "stages" / "review-stage.md"
GOAL = SKILL_ROOT / "stages" / "goal-stage.md"
BLUEPRINT = SKILL_ROOT / "stages" / "blueprint-stage.md"
PROMPT = SKILL_ROOT / "claude-agents" / "reviewer.md"


class TestSingleSourceRule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.doc = REVIEW.read_text(encoding="utf-8")
        cls.rule = cls.doc.split("功能优先 · 复杂度守恒", 1)[1].split("\n3. ")[0]

    def test_rule_exists_as_single_source(self):
        self.assertIn("功能优先 · 复杂度守恒", self.doc)
        self.assertIn("本条是单源", self.rule)

    def test_real_defects_zero_threshold(self):
        self.assertIn("真功能缺陷必报 · 零门槛", self.rule)
        for k in ("行为错", "契约破坏", "数据损坏", "安全"):
            self.assertIn(k, self.rule)

    def test_hardening_needs_real_trigger_path(self):
        self.assertIn("真实触发路径", self.rule)
        self.assertIn("不成 finding", self.rule)

    def test_reject_is_legitimate_when_fix_costs_more(self):
        """修复代价 > 缺陷危害 → REJECT 合法 —— 不重要的 bug 不值得复杂度。"""
        self.assertIn("REJECT 是合法且推荐的裁决", self.rule)
        self.assertIn("不重要的 bug 增加整体复杂度", self.rule)

    def test_no_process_or_test_gates_via_review(self):
        self.assertIn("不借 review 加流程 / 测试门", self.rule)
        self.assertIn("ci_reason", self.rule)              # 测试门单源指向生命周期分层
        self.assertIn("回归测试锁不在此列", self.rule)      # confirmed bug 回归锁不受限

    def test_simplification_direction_always_admissible(self):
        """高门槛只拦「往上加」—— 简化方向不设门槛(防被误读成「都别提」)。"""
        self.assertIn("简化方向不设门槛", self.rule)

    def test_existing_severity_discipline_untouched(self):
        self.assertIn("severity 定级纪律", self.doc)
        self.assertIn("钟摆", self.doc)


class TestStagePointers(unittest.TestCase):

    def test_goal_cold_review_carries_pointer(self):
        doc = GOAL.read_text(encoding="utf-8")
        seg = doc.split("功能优先 · 复杂度守恒", 1)[1].split("\n7. ")[0]
        self.assertIn("review-stage", seg)                 # 指针 · 不另立判据
        self.assertIn("要做的东西对不对", seg)
        self.assertIn("必报", seg)                          # 真需求缺陷仍必报

    def test_blueprint_cold_review_carries_pointer(self):
        doc = BLUEPRINT.read_text(encoding="utf-8")
        seg = doc.split("功能优先 · 复杂度守恒", 1)[1].split("\n10. ")[0]
        self.assertIn("review-stage", seg)
        self.assertIn("不可实现", seg)                      # 方案真缺陷必报
        self.assertIn("防御式设计", seg)


class TestPromptCarrier(unittest.TestCase):
    """动作点载体:冷审 subagent 只读 prompt —— 判据必须在 prompt 主体内。"""

    @classmethod
    def setUpClass(cls):
        cls.doc = PROMPT.read_text(encoding="utf-8")

    def test_admission_section_inside_prompt_body(self):
        body = self.doc.split("## Prompt 主体", 1)[1]
        idx_admission = body.index("Finding 准入")
        idx_output = body.index("## 输出格式")
        self.assertLess(idx_admission, idx_output)          # 在输出格式前 · 属 prompt 正文

    def test_prompt_filters_checklist_directions(self):
        """Checklist 的错误处理/边界方向被准入过滤 ——「理论上可能」不是触发路径。"""
        self.assertIn("理论上可能」不是触发路径", self.doc)

    def test_prompt_forbids_gate_suggestions(self):
        self.assertIn("不建议「加 CI 门 / 加流程门 / 泛化补测试提覆盖」", self.doc)
        self.assertIn("回归测试除外", self.doc)

    def test_prompt_keeps_functional_defect_duty(self):
        self.assertIn("真功能缺陷必报", self.doc)


if __name__ == "__main__":
    unittest.main()
