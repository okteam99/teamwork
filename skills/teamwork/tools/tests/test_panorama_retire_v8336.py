"""panorama_sync stage 退役 · 全景变更判级并入 ui_design 出口(用户拍板)。

前提验证成立:设计流程就是**基于现有全景改造**(ui_design 新模式:全景唯一权威 ·
Designer 直接改 · Feature 不存副本)—— panorama-sync 自己承认「不重复同步」,只剩
sitemap 登记 + 判级 + summary;且机器自相矛盾实锤:附录维度 4 要求 ui_design 期改
sitemap,退役前的 mtime 门(> 本 stage started_at)逼人**二次 touch**。消费数据
11 次全是 L1 分钟级过场,零 L2 真协调。

真价值(结构性 IA 变更判级/跨 Feature 协调)是条件暂停,不配独立 stage ——
并入 ui_design 既有的用户确认停等(零新增停等 · 与 blueprint DB 变更 R5 同形态)。
"""
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))


class TestStageRetired(unittest.TestCase):

    def test_gone_from_registry_and_disk(self):
        from _v8_stage_specs import STAGE_SPECS
        self.assertNotIn("panorama_sync", STAGE_SPECS)
        self.assertFalse((SKILL_ROOT / "stages" / "panorama-sync-stage.md").exists())

    def test_ui_design_transition_unconditional(self):
        from _v8_stage_specs import _ui_design_transition
        self.assertEqual(_ui_design_transition({}), "blueprint")
        self.assertEqual(_ui_design_transition(
            {"execution_hints": {"panorama_changed": True}}), "blueprint")  # legacy hint 无效化

    def test_flag_no_longer_persisted(self):
        from _v8_stage_specs import persist_args_to_evidence
        from argparse import Namespace
        st = {}
        persist_args_to_evidence("ui_design", st,
                                 Namespace(panorama_changed="true", needs_browser_e2e="false"))
        self.assertNotIn("panorama_changed", st.get("execution_hints", {}))

    def test_legacy_enum_kept_for_history(self):
        """存量 state 的 completed_stages 含 panorama_sync → 枚举仍认(兼容读)。"""
        src = (SKILL_ROOT / "tools" / "state.py").read_text(encoding="utf-8")
        self.assertIn('"panorama_sync",   # 退役 stage', src)
        self.assertIn('"ui_design": ["blueprint"]', src)


class TestValueAbsorbedByUiDesign(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        doc = (SKILL_ROOT / "stages" / "ui-design-stage.md").read_text(encoding="utf-8")
        cls.doc = doc
        cls.rule8 = doc.split("全景变更判级(出口", 1)[1].split("\n\n")[0]

    def test_l1_three_criteria_mechanical(self):
        for k in ("无节点增删移", "token", "受影响 Features 扫描零命中"):
            self.assertIn(k, self.rule8, k)
        self.assertIn("WARN", self.rule8)

    def test_l2_rides_existing_pause(self):
        """条件暂停搭既有停等 —— 零新增停等(与 blueprint DB 变更同形态)。"""
        self.assertIn("既有的用户确认设计稿暂停点", self.rule8)
        self.assertIn("零新增停等", self.rule8)

    def test_summary_replaced_by_ui_md_section(self):
        self.assertIn("UI.md §全景变更判级", self.rule8)
        # 仅存的一处是「替代原 …」迁移史标注 · 不是活产物要求
        self.assertEqual(self.doc.count("panorama-change-summary"), 1)

    def test_sitemap_contradiction_resolved(self):
        """旧规则 5「不直接改 sitemap」与附录维度 4 打架 —— 现同轴:随设计一并改。"""
        self.assertIn("sitemap / overview 随设计一并改", self.doc)
        self.assertNotIn("归 panorama_sync", self.doc)


class TestNoDanglingReferences(unittest.TestCase):

    def test_repo_wide_clean(self):
        """锁「活引用」而非字面:符号 / 注册键 / 链边 / 文档表行必须死透 ——
        迁移史标注(「原 panorama_sync 并入」「退役」)是合法的,不在禁列。"""
        specs = (SKILL_ROOT / "tools" / "_v8_stage_specs.py").read_text(encoding="utf-8")
        self.assertNotIn("PANORAMA_SYNC_SPEC", specs)
        self.assertNotIn('"panorama_sync":', specs)                  # 注册键
        engine = (SKILL_ROOT / "tools" / "_v8_engine.py").read_text(encoding="utf-8")
        self.assertNotIn("panorama_sync", engine)
        self.assertNotIn("panorama_sync", (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8"))
        self.assertNotIn("panorama_sync", (SKILL_ROOT / "FLOWS.md").read_text(encoding="utf-8"))
        self.assertNotIn("panorama-sync-stage.md",
                         (SKILL_ROOT / "STAGES.md").read_text(encoding="utf-8"))  # 索引表行已删

    def test_no_stage_count_literals(self):
        """数字宣称必漂的现行实证(12→11)—— SKILL/STAGES 不再写死 stage 数。"""
        for rel in ("SKILL.md", "STAGES.md"):
            t = (SKILL_ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn("12 stage", t, rel)


if __name__ == "__main__":
    unittest.main()
