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
        """必读文件必须短 —— 1773 行没法要求必读,~50 行可以。"""
        self.assertLess(len(self.t.splitlines()), 70)

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
                  "安全加固 / 兜底降级必过 ROI", "NEVER refactor while RED"):
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
        total = sum(len((STD / f).read_text(encoding="utf-8").splitlines())
                    for f in ("common.md", "backend.md", "frontend.md", "tdd.md"))
        self.assertLess(total, 1150, f"四件分册应已从 1773 降到 1150 内 · 现 {total}")
