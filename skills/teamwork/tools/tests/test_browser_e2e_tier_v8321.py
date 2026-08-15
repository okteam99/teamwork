"""browser_e2e 档位承载锁。

case:用户问「browser_e2e 是 subagent + 验证档执行么」→ 答案在全局白名单里是,
但 stage 自身硬规则与运行时 brief 零承载(goal/blueprint/review 都有 🎚️ 行,唯独它空)——
执行到该 stage 的 AI 若 context 没带全局白名单,默认继承会话主模型手点(常费而不自知)。

锁三件事:
1. stage 硬规则 🎚️ 行:默认验证档 subagent · 降档唯一路径 · R5 例外 · 降级 WARN。
2. brief 同步(动作点载体 —— 模式承诺必须物化到执行入口)。
3. 单源不漂:agents/README 白名单仍含 e2e(此处只指针复述,不另立判据)。
"""
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
STAGE = SKILL_ROOT / "stages" / "browser-e2e-stage.md"
AGENTS_README = SKILL_ROOT / "agents" / "README.md"


def _tier_rule(text: str) -> str:
    return next(l for l in text.splitlines() if "默认派验证档 subagent 执行" in l)


class TestStageTierRule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.stage = STAGE.read_text(encoding="utf-8")
        cls.rule = _tier_rule(cls.stage)

    def test_rule_exists_with_tier_marker(self):
        self.assertIn("🎚️", self.rule)

    def test_names_the_only_downgrade_path(self):
        """降档只有派 subagent 传 model 一条路(主对话模型 = 用户主权不可切)。"""
        self.assertIn("显式传 model", self.rule)
        self.assertIn("用户主权", self.rule)
        self.assertIn("Meta: tier=验证", self.rule)  # 申报寄生 prompt 首行 · 与派发协议同格式

    def test_exception_goes_through_r5(self):
        """例外不许 AI 自决 —— 首份可重放脚本(探索占主体)是典型例外,须用户授权。"""
        self.assertIn("不许 AI 自决", self.rule)
        self.assertIn("R5", self.rule)
        self.assertIn("首份可重放脚本", self.rule)

    def test_degradation_emits_warn(self):
        """宿主不支持 subagent → 串行降级必 WARN(静默降级 = 隐藏问题)。"""
        self.assertIn("degradation-fallback", self.rule)

    def test_points_to_single_source(self):
        """档位判据单源 agents/README §一 —— 本行是指针复述,不另立表。"""
        self.assertIn("agents/README", self.rule)

    def test_upstream_whitelist_still_covers_e2e(self):
        """单源锚:agents/README 白名单含 e2e · 例外条款在(本 rule 漂了会先在这里响)。"""
        readme = AGENTS_README.read_text(encoding="utf-8")
        wl = next(l for l in readme.splitlines() if "白名单一律降到这档" in l)
        self.assertIn("e2e", wl)
        self.assertIn("验证类白名单的例外必须用户授权", readme)


class TestBriefCarriesTier(unittest.TestCase):
    """运行时 brief = 执行入口 —— 档位不在这里出现就等于不存在。"""

    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, str(SKILL_ROOT / "tools"))
        from _v8_stage_specs import BROWSER_E2E_SPEC
        cls.brief = BROWSER_E2E_SPEC.brief_template_fn({})

    def test_brief_has_tier_line(self):
        self.assertIn("验证档 subagent", self.brief)
        self.assertIn("Meta: tier=验证", self.brief)

    def test_brief_exception_needs_user(self):
        self.assertIn("R5", self.brief)
        self.assertIn("不许自决", self.brief)

    def test_brief_count_updated(self):
        self.assertIn("注意事项 7 条", self.brief)
        self.assertNotIn("注意事项 6 条", self.brief)


if __name__ == "__main__":
    unittest.main()
