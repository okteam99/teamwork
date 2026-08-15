"""browser-e2e 可重放契约锁。

拍板两条(同一根:可重放性,不是工具名):
1. 关键路径必留可重放脚本 —— 判据「交付后还需重跑(回归/CI)吗」,
   需要 → 脚本进 repo + TC 注册(生命周期 L2);只看一眼 → 截图即可。
   why:AI 手点一次不可重放 —— 代码一改,旧截图证明不了新代码。
2. 工具默认首选 Playwright;项目已有其他 e2e 基建则复用(一致性优先)。

设计边界:不设机器门 ——「关键与否」是判断题,载体承载
(报告 frontmatter `replay_entry` 必填槽位,空着即可见)。
"""
import re
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
STAGE = SKILL_ROOT / "stages" / "browser-e2e-stage.md"
REPORT_TPL = SKILL_ROOT / "templates" / "browser-test-report.md"
TC_TPL = SKILL_ROOT / "templates" / "tc.md"


class TestReplayableHardRule(unittest.TestCase):
    """stage ② 硬规则:可重放脚本 + 判据 + 生命周期衔接。"""

    @classmethod
    def setUpClass(cls):
        cls.stage = STAGE.read_text(encoding="utf-8")

    def test_hard_rule_exists(self):
        """关键路径必留可重放脚本 —— 7 月拍板落地。"""
        self.assertIn("关键路径必留可重放脚本", self.stage)

    def test_criterion_is_rerun_after_delivery(self):
        """判据必须是「交付后还需重跑」,不是「用没用某工具」。"""
        rule = next(l for l in self.stage.splitlines() if "关键路径必留可重放脚本" in l)
        self.assertIn("交付后还需要重跑", rule)
        self.assertIn("回归 / CI", rule)

    def test_replay_script_lands_in_repo_and_tc(self):
        """命中判据 → 脚本进 repo + TC 注册,且按生命周期归 L2(不自动进 L1)。"""
        rule = next(l for l in self.stage.splitlines() if "关键路径必留可重放脚本" in l)
        self.assertIn("TC 注册", rule)
        self.assertIn("L2 回归层", rule)
        self.assertIn("ci_reason", rule)  # 进 L1 仍走 ci_reason 门 · 不因是 e2e 就豁免

    def test_why_names_the_real_mechanism(self):
        """why 必须点破:手点不可重放 + 只点名工具约束不了产物。"""
        rule = next(l for l in self.stage.splitlines() if "关键路径必留可重放脚本" in l)
        self.assertIn("不可重放", rule)
        self.assertIn("手点也算", rule)  # 反例:用 playwright MCP 手点 ≠ 可重放

    def test_exploratory_stays_screenshot_only(self):
        """一次性验收不被误伤 —— 截图即可,探索落 scratch。"""
        rule = next(l for l in self.stage.splitlines() if "关键路径必留可重放脚本" in l)
        self.assertIn("截图即可", rule)
        self.assertIn("scratch", rule)


class TestPlaywrightDefault(unittest.TestCase):
    """工具菜单:Playwright 默认首选 + 既有基建复用。"""

    @classmethod
    def setUpClass(cls):
        cls.stage = STAGE.read_text(encoding="utf-8")

    def test_menu_row_declares_default(self):
        menu = next(l for l in self.stage.splitlines()
                    if l.startswith("|") and "Playwright" in l)
        self.assertIn("默认首选", menu)

    def test_reuse_clause_survives(self):
        """已有 Puppeteer/Selenium/Cypress 基建 → 复用,不逼迁移。"""
        menu = next(l for l in self.stage.splitlines()
                    if l.startswith("|") and "Playwright" in l)
        self.assertIn("复用", menu)
        self.assertIn("一致性优先", menu)
        for legacy in ("Puppeteer", "Selenium", "Cypress"):
            self.assertIn(legacy, menu)


class TestOutputContract(unittest.TestCase):
    """stage ④ 产物契约 + 报告模板槽位 + tc.md 执行方式二分。"""

    def test_stage_output_lists_replay_script(self):
        stage = STAGE.read_text(encoding="utf-8")
        self.assertIn("**可重放脚本**", stage)
        self.assertIn("replay_entry", stage)

    def test_no_machine_gate_by_design(self):
        """不设机器门是拍板边界:artifacts 仍 2 项 · evidence_checks 空。"""
        stage = STAGE.read_text(encoding="utf-8")
        self.assertIn("不设机器门", stage)
        import sys
        sys.path.insert(0, str(SKILL_ROOT / "tools"))
        from _v8_stage_specs import BROWSER_E2E_SPEC
        self.assertEqual(len(BROWSER_E2E_SPEC.artifacts), 2)
        self.assertEqual(BROWSER_E2E_SPEC.evidence_checks, [])

    def test_report_frontmatter_has_replay_entry(self):
        """replay_entry 槽位 —— 载体的形状决定内容会不会出现。"""
        tpl = REPORT_TPL.read_text(encoding="utf-8")
        fm = tpl.split("---")[1]
        self.assertIn("replay_entry:", fm)
        line = next(l for l in fm.splitlines() if l.startswith("replay_entry:"))
        self.assertIn("n/a", line)  # 一次性验收有合法出口 · 空着才是违规

    def test_report_automation_comment_states_default(self):
        tpl = REPORT_TPL.read_text(encoding="utf-8")
        line = next(l for l in tpl.splitlines() if l.startswith("browser_automation:"))
        self.assertIn("默认首选 playwright", line)
        self.assertIn("复用", line)

    def test_tc_execution_mode_split(self):
        """browser-script(可重放)/ browser(手点 · 仅探索性)二分。"""
        tc = TC_TPL.read_text(encoding="utf-8")
        line = next(l for l in tc.splitlines() if "**执行方式**: browser" in l)
        self.assertIn("browser-script", line)
        self.assertIn("Playwright 优先", line)
        self.assertIn("探索性", line)
        self.assertIn("不可重放", line)  # 手点的降级理由写在选项旁 · 选错时看得见

    def test_runtime_brief_carries_rule(self):
        """动作点载体同步 —— brief 不同步 = 模式承诺未物化(既往两例同族)。"""
        import sys
        sys.path.insert(0, str(SKILL_ROOT / "tools"))
        from _v8_stage_specs import BROWSER_E2E_SPEC
        brief = BROWSER_E2E_SPEC.brief_template_fn({})
        self.assertIn("replay_entry", brief)
        self.assertIn("可重放脚本", brief)
        self.assertIn("Playwright 优先", brief)
        self.assertNotIn("注意事项 5 条", brief)


class TestSpecHygiene(unittest.TestCase):
    """新增文本不触版本标门 / 考古门。"""

    def test_no_version_tags_in_touched_specs(self):
        for f in (STAGE, REPORT_TPL, TC_TPL):
            body = f.read_text(encoding="utf-8")
            hits = re.findall(r"v8\.\d+", body)
            self.assertEqual(hits, [], f"{f.name} 含版本标: {hits}")


if __name__ == "__main__":
    unittest.main()
