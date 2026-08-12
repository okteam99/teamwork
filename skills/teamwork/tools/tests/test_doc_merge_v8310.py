"""v8.310:文档合并与考古注释清理(用户:「看下各 md 是否需要合并 · 去掉没必要的注释」)。

合并三件(判据:**合并要么减少重复、要么减少读取量,两者都不减的不合**):
- STANDARDS.md 退役 —— 独有内容仅一句(覆盖注册处),其余是**已漂移的分册简介**
  (还在描述 v8.307 已删的「组件测试/状态管理/无障碍」)+ 与各分册头部重复的加载指引;
  索引描述是内容的副本,**索引也会漂**。
- TEMPLATES.md 退役 —— 红线与 templates/README 头部 + common §四C 三重复写,
  页脚还声称 roles/{pmo,pm,rd} 有「格式权威」条目(**三个文件都没有** · 幽灵引用)。
- standards/frontend.md 并入 common.md §七 —— 砍完教学后仅 13 行,头部比正文长;
  文件数不是成本、读取行数才是,13 行不值一个独立加载单元。

**评估后不合的**(记录判断,防下轮重新讨论):
- roles/ 9→1:引用 15 个 md 文件 + stage spec 逐点 cite 具体角色文件;合并不减重复
  也不减读取量,只减文件数 —— 文件数不是成本。
- PRODUCT-OVERVIEW-INTEGRATION → feature-planning:tools 层 3 处真实咬死路径
  (bootstrap flow_gates + state.py planning-check must_read emit);且两文件分工清楚
  (文档体系与状态管理 vs 流程步骤),合成 450 行巨文件反而变差。
- teamwork-space 模板/guide:bootstrap 拷模板做骨架,guide 内容不能进模板。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HISTORY = {"docs/CHANGELOG.md", "docs/CHANGELOG-ARCHIVE.md", "docs/RETRO-LEDGER.md"}


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _spec_files():
    return [p for p in ROOT.rglob("*.md")
            if "pytest_cache" not in str(p)
            and str(p.relative_to(ROOT)) not in HISTORY]


class TestRetiredFilesStayDead(unittest.TestCase):

    def test_files_gone(self):
        for rel in ("STANDARDS.md", "TEMPLATES.md", "standards/frontend.md"):
            self.assertFalse((ROOT / rel).exists(), f"{rel} 复活(已退役并入他处)")

    def test_no_spec_references_dead_files(self):
        """退役必须连引用一起清 —— 删了源留引用 = 又造断链。"""
        offenders = []
        for p in _spec_files():
            t = p.read_text(encoding="utf-8")
            for dead in ("STANDARDS.md", "TEMPLATES.md", "frontend.md"):
                if dead in t:
                    offenders.append(f"{p.relative_to(ROOT)} → {dead}")
        self.assertEqual(offenders, [], f"仍引用已退役文件:{offenders}")


class TestUniqueContentSurvived(unittest.TestCase):
    """退役的验收标准 = 独有内容逐条有新家,不是行数变少。"""

    def test_standards_unique_sentence_moved_to_hard_rules(self):
        """STANDARDS 唯一独有句:覆盖注册处 = DEV-RULES · KNOWLEDGE 不作注册处。"""
        t = _read("standards/HARD-RULES.md")
        self.assertIn("覆盖声明唯一注册处 = DEV-RULES.md", t)
        self.assertIn("不作规范覆盖注册处", t)
        self.assertIn("对外契约", t, "存量契约沿用规则丢失")

    def test_templates_redline_lives_in_readme(self):
        """TEMPLATES 红线并入 templates/README 头部 · meta 规则指 §四C 单源。"""
        t = _read("templates/README.md")
        self.assertIn("格式唯一真相源", t)
        self.assertIn("禁止以 peer Feature 产物为格式基准", t)
        self.assertIn("四C", t, "未 cite meta 规则单源 → 红线成孤立复述")

    def test_frontend_body_lives_in_common_section_seven(self):
        t = _read("standards/common.md")
        self.assertIn("## 七、前端专项", t)
        self.assertIn("覆盖率 > 70%", t)
        self.assertIn("禁混用", t)
        self.assertIn("仅前端子项目适用", t, "适用范围声明丢失(后端会误读)")

    def test_loading_hints_updated(self):
        self.assertIn("§七前端专项", _read("standards/backend.md"))
        hr = _read("standards/HARD-RULES.md")
        self.assertIn("§七前端专项", hr)


class TestSkillNavCurrent(unittest.TestCase):

    def test_nav_points_at_real_files(self):
        t = _read("SKILL.md")
        self.assertIn("templates/README.md", t)
        self.assertNotIn("TEMPLATES.md", t)
        self.assertNotIn("STANDARDS.md", t)


class TestNoArchaeologyComments(unittest.TestCase):
    """「没必要的注释」机器门:删除记账(原 N 行已删)与出处署名不属于现行真相。

    why 原则可以留(「模型内建常识不入库」支撑现行形状 · 防回潮);
    但「原 N 行 / 压缩原 / 借鉴某仓库」删掉后规则说服力不掉 —— 按 conventions 判据 = 考古。
    """

    PATTERNS = [
        (re.compile(r"原 ?~?\d+ 行"), "行数记账(原 N 行已删)"),
        (re.compile(r"压缩原"), "压缩记账"),
        (re.compile(r"借鉴 mattpocock"), "出处署名"),
    ]

    def test_specs_free_of_archaeology(self):
        offenders = []
        for p in _spec_files():
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                for pat, label in self.PATTERNS:
                    if pat.search(line):
                        offenders.append(f"{p.relative_to(ROOT)}:{i} [{label}]")
        self.assertEqual(offenders, [], "考古注释回潮:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main(verbosity=2)
