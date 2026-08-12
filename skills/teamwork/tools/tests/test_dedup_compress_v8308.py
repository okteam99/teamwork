"""v8.308:第二梯队 —— 双写合并与重复壳压缩(第一梯队 v8.307 是整段砍教学 · 两批分开是刻意的:
「删教学」与「改语义的合并」混在一个 diff 里 review 分不开)。

本批全部是 ⑧重复 的收口:同一规则在同文件写两遍(backend WARN 双段)、
同一模板存两份且已漂移(Designer 自查报告 5 维 vs 6 维)、
checklist 复述模板正文已有的段(prd)、注意事项复述正文步骤(feature-planning 坑 1/3/5)。

判据:**合并双写必须零语义丢失** —— 每个被合并段的实质条款(字段清单 / CR 门 / why)
都要在幸存段里找得到,测试逐条锁。
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestBackendLogRulesMerged(unittest.TestCase):
    """WARN 规则原本写两遍(非预期分支树里一遍 + 独立硬规则块一遍)—— 合一后实质零丢失。"""

    def setUp(self):
        self.t = _read("standards/backend.md")

    def test_duplicate_block_gone(self):
        self.assertNotIn("降级兜底逻辑 WARN 日志规则", self.t, "旧独立块标题仍在 = 没合并")
        self.assertEqual(self.t.count("先 ERROR"), 1, "先 ERROR 再 WARN 应只出现一处")

    def test_no_substance_lost_in_merge(self):
        """两段的实质条款逐条核:触发面 · 字段 · CR 门 · 逆默认 why。"""
        for k in ("A 失败 → B 兜底", "else/default", "理论上不应该走到",
                  "降级原因", "降级前方案", "降级后方案",
                  "限流/熔断/降级信号", "APM / sidecar 自动上报 ≠ 免除",
                  "先 ERROR(异常本身)再 WARN(降级动作)",
                  "traceId / spanId", "duration_ms",
                  "catch-and-continue", "缺失即阻塞",
                  "静默降级 = 掩盖问题", "MTTR"):
            self.assertIn(k, self.t, f"合并丢了实质条款:{k}")

    def test_migration_hygiene_compressed_gates_kept(self):
        """迁移基本卫生(up/down 可逆/不可改)= 模型默认 · 走;项目守卫与跨子项目链是门 · 留。"""
        self.assertNotIn("迁移必须可逆", self.t)
        self.assertNotIn("不写 down 回滚脚本", self.t)
        for k in ("version-ceiling", "Schema 影响分析", "独立验证", "ORM 反序列化报错"):
            self.assertIn(k, self.t, f"真门被误伤:{k}")

    def test_flow_chart_gone_terminology_table_kept(self):
        """衔接流程图 = 状态机 stage 链复述 · 走;术语对照表(唯一映射信息)· 留。"""
        self.assertNotIn("PMO 完成报告 → 确认 database-schema.md", self.t)
        self.assertIn("Schema 变更链条术语对照", self.t)

    def test_json_naming_one_liner(self):
        self.assertNotIn("userId（驼峰）", self.t)
        self.assertIn("snake_case", self.t)


class TestDesignerSelfCheckSingleSourced(unittest.TestCase):
    """自查报告模板此前两份且已漂移(common.md 5 维 · ui.md 6 维)—— 双副本必漂的现行实证。"""

    def test_report_template_only_in_ui_md(self):
        common = _read("standards/common.md")
        ui = _read("templates/ui.md")
        self.assertNotIn("检查结果汇总", common, "common.md 仍存报告模板副本")
        self.assertIn("检查结果汇总", ui)
        self.assertIn("框架基线唯一性", ui, "ui.md 6 维表是幸存单源 · 第 6 维必须在")

    def test_dimension_count_synced_to_six(self):
        common = _read("standards/common.md")
        self.assertIn("6 维度", common)
        self.assertNotIn("5 维度", common, "维度数仍是漂移前的 5")
        self.assertIn("框架基线唯一性", common, "第 6 维缺清单定义(此前只在 ui.md 表里有一行)")

    def test_dead_anchors_in_4c_fixed(self):
        """四C 表指过 designer.md § 6 维自查 / ui-design-stage § 框架基线唯一性 —— 两个锚点都不存在。"""
        common = _read("standards/common.md")
        self.assertNotIn("6 维自查", common)
        self.assertNotIn("格式权威守门", common, "pmo.md 无此节 · 死锚点应已改为裸文件链接")

    def test_verify_panorama_anchor_still_alive(self):
        """verify-panorama.py 的 hint 指向 common.md §四B —— 压缩不许弄断工具的指路牌。"""
        common = _read("standards/common.md")
        self.assertIn("四B、Designer 自查规范", common)
        tool = _read("tools/verify-panorama.py")
        self.assertIn("四B", tool)

    def test_dimension_six_gap_documented_in_tool(self):
        """维度 6 未进硬校验是已知缺口 —— 必须在工具里写明是存量兼容 · 不许静默。"""
        tool = _read("tools/verify-panorama.py")
        self.assertIn("维度 6", tool)
        self.assertIn("存量", tool)

    def test_ui_md_count_matches_its_own_table(self):
        ui = _read("templates/ui.md")
        self.assertIn("6 维度全 ✅", ui, "ui.md 正文说 5 维而自己的表有 6 行(原漂移)")


class TestPrdChecklistDeduped(unittest.TestCase):
    """checkbox 复述模板正文已有的段 = ⑨环节化自检;只留结构没问到的三件义务。"""

    def setUp(self):
        self.t = _read("templates/prd.md")

    def test_checkbox_ritual_gone(self):
        self.assertNotIn("- [ ] 解决什么用户问题", self.t)
        self.assertNotIn("- [ ] 明确 in_scope", self.t)

    def test_three_non_structural_obligations_kept(self):
        for k in ("KNOWLEDGE / ADR 关联", "跨子项目依赖", "业务风险"):
            self.assertIn(k, self.t, f"结构没问到的义务被误删:{k}")

    def test_third_restatement_of_doc_split_gone(self):
        self.assertNotIn("三阶段职责正交", self.t, "三文档分工第三遍复述仍在")
        self.assertIn("PRD 不写什么", self.t, "边界契约(第二处 · 有裁决功能)должна留")


class TestFeaturePlanningPitfallsDeduped(unittest.TestCase):
    """坑 1/3/5 全是正文步骤的复述 —— 留下的三条都是正文没讲过的。"""

    def setUp(self):
        self.t = _read("docs/feature-planning.md")

    def test_restated_pitfalls_gone(self):
        self.assertNotIn("坑 5", self.t)
        self.assertNotIn("Planning 完成自动启 Feature", self.t)

    def test_unique_pitfalls_kept(self):
        for k in ("业务架构 vs 技术架构", "三者分工", "planning-start"):
            self.assertIn(k, self.t, f"非重复坑被误删:{k}")

    def test_no_dangling_pitfall_refs(self):
        """删了编号坑之后 · 正文不许再引用「坑 N」编号(引用会随删除悬空)。"""
        import re
        self.assertEqual(re.findall(r"坑 \d", self.t), [], "残留编号引用")


class TestUiDesignStageDupBlockGone(unittest.TestCase):
    """全景模型节尾的「🔴 硬规则」块与 ② 硬规则 1-2 几乎逐字双写 —— ② 是单源。"""

    def setUp(self):
        self.t = _read("stages/ui-design-stage.md")

    def test_restated_block_gone(self):
        self.assertNotIn("必须开 Feature 把 panorama 迁到", self.t)
        self.assertEqual(self.t.count("必开 Feature 迁移"), 1,
                         "dirty state 的规则句应只在 ② 出现一次(词可复现 · 规则不双写)")

    def test_backward_compat_line_survived(self):
        """双写块里唯一非重复的一条(缺 panorama_medium 视作 static-html)必须留。"""
        self.assertIn("视作 `static-html`", self.t)


class TestCommonScriptsCompressed(unittest.TestCase):
    """§三 逐脚本职责树压缩 —— 名称清单与接口契约是信息 · 必须一个不丢。"""

    def setUp(self):
        self.t = _read("standards/common.md")

    def test_all_script_names_survive(self):
        for s in ("test-env-setup.sh", "test-env-check.sh", "test-env-teardown.sh",
                  "test-unit.sh", "test-integration.sh", "test-api-e2e.sh", "test-browser-e2e.sh"):
            self.assertIn(s, self.t, f"脚本名清单丢失:{s}")

    def test_interface_contract_survives(self):
        for k in ("幂等", "无交互", "最后一行输出环境信息 JSON", "--skip-if-running",
                  "假定全局环境已就绪", "根级 setup → 子项目 test-*"):
            self.assertIn(k, self.t, f"接口契约丢失:{k}")

    def test_fence_gate_tightened(self):
        gate = _read("tools/tests/test_redundancy_sweep_v8293.py")
        self.assertNotIn('"common.md"', gate, "common.md 配平后应移出 KNOWN_ODD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
