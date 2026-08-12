"""v8.307:指导类第二轮减法 —— 「模型默认就会」的教学与示例,连同它们的死引用一起退役。

判据同 v8.285(与模型默认行为的距离),但这轮砍的是 v8.285 那轮**漏网的同类**:
- frontend.md 头部写着「选型教程不入库(v8.123 裁定)」,正文却仍是选型教程 —— 裁定只执行了一半;
- ui-design-stage v8.284 按「模型内建常识」删了 WCAG/触控细则,同类内容在 frontend.md 原样活着 ——
  **同一判例只执行了一个文件**;
- backend.md §四 的两大段 JS 示例只是把「必须字段」清单实例化(⑦教学示例 · 规则本体全保留)。

附带修断链(v8.293 类 · 本轮 review 撞见):
- backend/frontend 的「模块设计判定」引用 templates/knowledge.md 的两个节 ——
  **那两节 v8.96 就删了**(~200 版无人发现 = 零消费者);抗过度设计的活规则在 HARD-RULES.md 规则 5。
- scripts-policy 三处引用不存在的 tools/post-feature.py(含 R-SP-2 的示例命令本身);
  §4 迁移表还说 4 个 hook「保留」,而同文件 R-SP-1 明写 hooks 已全退役、目录已删。
- agents/README 与 SKILL.md 仍说 codex agent toml「bootstrap 部署」—— v8.304 已改回收
  (正是 v8.300 立过判例的「改规则只写新的、没撤旧的」,这次是自己上一版种的)。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
STD = ROOT / "standards"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class TestFrontendTeachingGone(unittest.TestCase):
    """前端规范:教程走 · 阈值与禁令留(v8.310 起并入 common.md §七 · 文件退役)。"""

    def setUp(self):
        self.t = _read(STD / "common.md")

    def test_tutorials_removed(self):
        """选型/手法教学 = 模型自带知识 · 命中任何一个都说明教程回潮。"""
        for marker in ("Zustand", "XState", "MSW", "fireEvent", "bundlephobia",
                       "WCAG", "aria-label", "LCP", "WebP", "source-map",
                       "总结与关键点"):
            self.assertNotIn(marker, self.t, f"教程内容回潮:{marker}")

    def test_thresholds_and_bans_retained(self):
        """留下的是模型猜不到的项目缺省(阈值)与跨 Feature 一致性禁令。"""
        self.assertIn("覆盖率 > 70%", self.t)
        self.assertIn("禁混用", self.t)
        self.assertIn("design token", self.t)
        self.assertIn("browser_e2e stage", self.t, "测试分层归属(框架约定)丢失")

    def test_lives_in_common_section_seven(self):
        self.assertIn("## 七、前端专项", self.t, "前端专项段丢失(v8.310 并入 common)")


class TestBackendExamplesGone(unittest.TestCase):
    """backend.md §四:砍示例**必须**留规则 —— 规则是逆默认最高价值格,示例只是它的实例化。"""

    def setUp(self):
        self.t = _read(STD / "backend.md")

    def test_js_examples_removed(self):
        for marker in ("paymentClient", "primaryService", "BusinessError", "```javascript"):
            self.assertNotIn(marker, self.t, f"JS 教学示例回潮:{marker}")

    def test_counter_default_log_rules_survive(self):
        """🔴 砍示例不许伤规则:外部调用必 ERROR / 降级必 WARN / 必须字段 / CR 门全在。"""
        for k in ("降级/兜底", "不得降为 WARN/INFO", "duration_ms", "traceId / spanId",
                  "降级原因", "缺失即阻塞", "静默降级 = 掩盖问题"):
            self.assertIn(k, self.t, f"逆默认规则被误伤:{k}")

    def test_checklist_trees_removed_carriers_kept(self):
        """§二:检查项树(模型默认)走 · TEST-DATA.md 载体与脚本契约指针留。"""
        self.assertNotIn("API 验证检查项", self.t)
        self.assertNotIn("数据库验证检查项", self.t)
        self.assertNotIn("docker-compose.test.yml", self.t, "实现指南树应已删")
        self.assertIn("TEST-DATA.md", self.t, "测试数据载体约定丢失")
        self.assertIn("test-env-setup.sh", self.t, "脚本名约定丢失")
        self.assertIn("common.md §三", self.t, "接口契约单源指针丢失")

    def test_api_versioning_compressed_registry_kept(self):
        """§六:breaking 枚举/deprecation 三步 = 教科书 · 走;api-design.md 登记义务留。"""
        self.assertNotIn("Step 1: 标记 Deprecated", self.t)
        self.assertNotIn("新增可选字段", self.t)
        self.assertIn("api-design.md 版本清单", self.t, "版本登记载体丢失")
        self.assertIn("Breaking Change 必升版本号", self.t)

    def test_fence_now_balanced(self):
        """§二 集成测试报告的断栏(v8.284 压缩时截断)已修 —— 计数配平且移出 KNOWN_ODD。"""
        n = sum(1 for l in self.t.splitlines() if l.strip().startswith("```"))
        self.assertEqual(n % 2, 0, f"backend.md 围栏未配平({n})")
        gate = _read(ROOT / "tools" / "tests" / "test_redundancy_sweep_v8293.py")
        self.assertNotIn('"backend.md"', gate, "修好断栏后应从 KNOWN_ODD 移出收紧门")
        self.assertNotIn('"frontend.md"', gate)


class TestModuleDesignSectionRetired(unittest.TestCase):
    """「模块设计判定」退役:单源死了 ~200 版无人发现 = 零消费者;活规则在 HARD-RULES。"""

    def test_dead_sections_gone_from_standards(self):
        for f in ("backend.md", "common.md"):
            t = _read(STD / f)
            self.assertNotIn("模块设计判定", t, f"{f} 仍留退役节")
            self.assertNotIn("通用架构词汇", t, f"{f} 仍引用 v8.96 已删的 knowledge.md 节")
            self.assertNotIn("删除测试", t, f"{f} 仍引用死单源")

    def test_surviving_rule_still_in_hard_rules(self):
        """🔴 退役副本的前提是活规则还在必读白名单 —— 这条断了退役就成了误删。"""
        t = _read(STD / "HARD-RULES.md")
        self.assertIn("两个 adapter 才抽象", t)

    def test_knowledge_md_really_lacks_the_cited_sections(self):
        """锁死退役依据:knowledge.md 里确实没有那两节(有人补回则本测试提醒重新评估)。"""
        t = _read(ROOT / "templates" / "knowledge.md")
        self.assertNotIn("通用架构词汇", t)
        self.assertNotIn("删除测试", t)


class TestTcTemplateExamplesGone(unittest.TestCase):
    """tc.md:骨架(TC-001 + 两张验证表)是载体 · 填好值的 TC-002/003 是教学。"""

    def setUp(self):
        self.t = _read(ROOT / "templates" / "tc.md")

    def test_filled_examples_removed(self):
        self.assertNotIn("TC-002", self.t)
        self.assertNotIn("TC-003", self.t)
        self.assertNotIn("张三", self.t)
        self.assertNotIn("wrong_password", self.t)

    def test_carriers_survive(self):
        """两张验证表 + 断言具体性红线 + 异常/参数化提示 —— 这些是约定不是教学。"""
        self.assertIn("TC-001", self.t)
        self.assertIn("数据库验证", self.t)
        self.assertIn("API 验证", self.t)
        self.assertIn("Scenario Outline", self.t, "参数化边界提示丢失")
        self.assertIn("异常场景必须有独立 Scenario", self.t)
        self.assertIn("不具体就不叫断言", self.t, "契约值分寸红线丢失")


class TestBottomUpCompressed(unittest.TestCase):
    """PRODUCT-OVERVIEW-INTEGRATION:信号枚举树(模型自判)走 · 用户主权协议 4 条留。"""

    def setUp(self):
        self.t = _read(ROOT / "PRODUCT-OVERVIEW-INTEGRATION.md")

    def test_enumeration_trees_gone(self):
        self.assertNotIn("信号 1：Feature 范围溢出", self.t)
        self.assertNotIn("裁剪规则：", self.t)

    def test_sovereignty_protocol_survives(self):
        """砍的是教学不是协议 —— 这四条全是用户主权/审计类(不衰减格)。"""
        for k in ("只标记 · 不改上游", "禁止自动向上传播", "上游未决前禁止恢复",
                  "不升级", "feature-planning 产 WS"):
            self.assertIn(k, self.t, f"协议条款被误伤:{k}")

    def test_upstream_still_referenced(self):
        """SKILL/feature-planning 对本文件的入链不受影响(整文件仍在 · 只瘦身)。"""
        self.assertIn("变更级联", self.t)
        self.assertIn("规划状态", self.t)


class TestScriptsPolicyDeadRefsFixed(unittest.TestCase):
    """scripts-policy:退役叙事与死引用清理 —— spec 是现行真相手册,不装迁移计划与过期快照。"""

    def setUp(self):
        self.t = _read(STD / "scripts-policy.md")

    def test_stale_plan_and_snapshot_gone(self):
        self.assertNotIn("第二阶段", self.t, "渐进切换计划不属于现行真相")
        self.assertNotIn("62.8%", self.t, "过期扫描快照仍在")
        self.assertNotIn("待评估", self.t, "§4 与 R-SP-1 hooks 已退役的声明矛盾")

    def test_every_cited_tool_file_exists(self):
        """🔴 零信任:本文件 cite 的每个可执行脚本必须真实存在(post-feature.py 类死引用的门)。"""
        missing = []
        for rel in set(re.findall(r"(?:tools|templates)/[\w\-]+\.py", self.t)):
            if not (ROOT / rel).exists():
                missing.append(rel)
        self.assertEqual(missing, [], f"cite 了不存在的脚本:{missing}")

    def test_rsp2_example_uses_real_tool(self):
        self.assertNotIn("post-feature", self.t)
        self.assertIn("verify-ac.py", self.t)

    def test_retired_rule_kept_as_tombstone_only(self):
        """R-SP-3 保留墓碑一行 · 不再带 bash 教学示例。"""
        self.assertIn("R-SP-3（已废）", self.t)
        self.assertNotIn("#!/bin/bash", self.t)


class TestV8304LooseEndsFixed(unittest.TestCase):
    """v8.304 把 codex agent toml 从「部署」改「回收」· 但两处文档没跟 —— 本版补撤。"""

    def test_no_doc_still_claims_toml_deployment(self):
        for rel in ("agents/README.md", "SKILL.md"):
            t = _read(ROOT / rel)
            self.assertNotIn("toml 部署", t, f"{rel} 仍称 bootstrap 部署 toml(v8.304 已改回收)")

    def test_recycling_stated_where_dispatch_is_described(self):
        t = _read(ROOT / "agents" / "README.md")
        self.assertIn("回收", t)
        self.assertIn("已退役", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
