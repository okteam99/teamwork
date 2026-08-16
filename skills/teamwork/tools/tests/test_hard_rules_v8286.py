"""v8.286:standards 硬规则白名单 + 读取路径接通 + 消除最后一处模板副本。

用户设计:AI 读「框架工程规范 + 项目 DEV-RULES」并集 · 冲突以项目为准。
落地选择:不新建 dev-rules-teamwork.md(会成第三个家)· 用 standards/HARD-RULES.md 作唯一必读入口
(分册按需查)—— standards/ 本就是框架级那层,DEV-RULES 模板早写明了这个分工,缺的是**读取路径**。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
STD = ROOT / "standards"


class TestHardRulesWhitelist(unittest.TestCase):
    def setUp(self):
        self.t = (STD / "HARD-RULES.md").read_text(encoding="utf-8")

    def test_compact_enough_to_be_required_reading(self):
        """必读文件必须短 —— 1773 行没法要求必读,~50 行可以。

        上限 70→85:收口自查表(用户拍板的兜底自查载体)入驻 —— 自查表本身
        就是「短清单」形态,与本锁「防膨胀回 1773 行」的初衷同向不冲突。
        """
        self.assertLess(len(self.t.splitlines()), 85)

    def test_states_union_and_project_precedence(self):
        self.assertIn("并集", self.t)
        self.assertIn("冲突以项目为准", self.t)

    def test_selection_criterion_documented(self):
        """收录判据 = 与模型默认的距离(逆默认 / 不可知)· 模型默认就会的不收。"""
        self.assertIn("与模型默认行为的距离", self.t)
        self.assertIn("逆默认", self.t)
        self.assertIn("不可知", self.t)
        self.assertIn("模型默认就会的一律不收", self.t)

    def test_counter_default_rules_present(self):
        """🔴 逆默认类 —— 模型越强越需要,一条不能漏。"""
        for k in ("默认避免 DB-level", "降级 / 兜底 / fallback 路径触发 → 必打 WARN",
                  "三方 / 外部服务调用异常", "两个 adapter 才抽象",
                  "安全加固 / 兜底降级必过 ROI", "测试必须真断言"):
            self.assertIn(k, self.t, f"逆默认规则缺失:{k}")

    def test_framework_specific_rules_present(self):
        """模型不可能知道的框架约定。"""
        for k in ("scratch 根", "DEBUG-{Feature}", "test-env-setup.sh",
                  "trace_id", "Build 必须跑通"):
            self.assertIn(k, self.t, f"框架约定缺失:{k}")


class TestReadPathWired(unittest.TestCase):
    """读取路径:stage 必须指向「白名单 + 项目 DEV-RULES 并集 · 项目优先」。"""

    def _rule1(self, stage):
        return (ROOT / "stages" / f"{stage}-stage.md").read_text(encoding="utf-8")

    def test_blueprint_and_dev_wired(self):
        for s in ("blueprint", "dev"):
            t = self._rule1(s)
            self.assertIn("standards/HARD-RULES.md", t, f"{s} 未接白名单")
            self.assertIn("并集", t, f"{s} 缺并集语义")
            self.assertIn("冲突以项目为准", t, f"{s} 缺优先级")

    def test_dev_rules_template_documents_precedence(self):
        t = (ROOT / "templates" / "dev-rules.md").read_text(encoding="utf-8")
        self.assertIn("HARD-RULES.md", t)
        self.assertIn("冲突以本文件为准", t)   # 项目侧视角:本文件 = DEV-RULES 优先


class TestNoDuplicateCopies(unittest.TestCase):
    def test_tech_template_points_not_copies(self):
        """最后一处同源副本(日志规则)已改指针 —— 规则单源在白名单。"""
        t = (ROOT / "templates" / "tech.md").read_text(encoding="utf-8")
        self.assertIn("standards/HARD-RULES.md", t)
        self.assertNotIn("静默 catch = 线上盲区", t)   # 原副本正文已删


class TestStandardsFurtherSlimmed(unittest.TestCase):
    def test_total(self):
        # v8.310:frontend.md 已并入 common.md §七 · 文件退役
        total = sum(len((STD / f).read_text(encoding="utf-8").splitlines())
                    for f in ("common.md", "backend.md"))
        self.assertLess(total, 1150, f"分册应已从 1773 降到 1150 内 · 现 {total}")


class TestNoDanglingStandardsLinks(unittest.TestCase):
    """v8.287:通用断链守护 —— 删/改 standards 文件后,不许有指向不存在文件的链接。

    实证:v8.285 删 stage heading 导致 6 处 cite 失效(agent 报出才发现);v8.287 退役 tdd.md
    需改 10 处入链。这类操作应被自动拦,不靠人肉 grep。
    """

    def test_all_standards_links_resolve(self):
        import re
        bad = []
        for f in list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.py")):
            if "docs/audit" in str(f) or "CHANGELOG" in f.name or "RETRO" in f.name:
                continue
            if f.name.startswith("test_"):
                continue
            for m in re.finditer(r"standards/([a-zA-Z0-9_-]+\.md)", f.read_text(encoding="utf-8", errors="replace")):
                if not (STD / m.group(1)).is_file():
                    bad.append(f"{f.relative_to(ROOT)} → standards/{m.group(1)}")
        self.assertEqual(bad, [], f"指向不存在的 standards 文件:{bad}")

    def test_tdd_md_retired(self):
        """v8.287:tdd.md 退役(三条结果规则已在白名单 · 留着就是第二份副本)。"""
        self.assertFalse((STD / "tdd.md").exists())
        h = (STD / "HARD-RULES.md").read_text(encoding="utf-8")
        for k in ("每个 TC 用例必须有对应实现", "测试必须真断言", "≥3 次失败修复"):
            self.assertIn(k, h, f"退役前必须确保规则已在白名单:{k}")


class TestDesignDocModelTier(unittest.TestCase):
    """v8.290:PRD 与 TECH 必须主模型/高级模型出设计或参与评审(两份设计文档定全局质量上限)。

    与 v8.268/269 模型错开的复合语义:PRD/TECH 错开时**只在高档之间错**(fable5↔opus),
    不许降到验证档;其余环节(TC 对照/测试执行/机械外化)该降档就降 · 主对话编排 subagent 并行。
    """

    def test_dispatch_reminder_carries_rule(self):
        import _v8_engine as E
        self.assertIn("PRD 与 TECH 必须主模型/高级模型", E.DISPATCH_TIER_REMINDER)
        self.assertIn("不许降到验证档", E.DISPATCH_TIER_REMINDER)
        self.assertIn("主对话编排", E.DISPATCH_TIER_REMINDER)

    def test_goal_and_blueprint_hard_rules(self):
        for s, kw in (("goal", "PRD 起草与冷审必用主模型"),
                      ("blueprint", "TECH 起草与评审必用主模型")):
            t = (ROOT / "stages" / f"{s}-stage.md").read_text(encoding="utf-8")
            self.assertIn(kw, t, f"{s} 缺设计文档档位硬规则")
            self.assertIn("不许降到验证档", t)

    def test_briefs_surface_rule(self):
        import _v8_stage_specs as S
        self.assertIn("主模型/高级模型", S._goal_brief({}))
        self.assertIn("主模型/高级模型", S._blueprint_brief({}))

    def test_architect_telos_states_bottom_line_and_autonomy(self):
        """用户示例:底线=架构合理防维护成本失控 · 怎么设计 AI 自决(显式声明)。"""
        t = (ROOT / "roles" / "architect.md").read_text(encoding="utf-8")
        self.assertIn("别让未来的维护成本过高", t)
        self.assertIn("架构怎么设计 —— AI 自决", t)
