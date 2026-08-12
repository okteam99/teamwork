"""v8.309:spec 版本标清零 + 机器门(用户裁定:R-SP-8 为主 · 实证 case 允许 · 版本标清扫)。

conventions「不写版本标 / 不写实证叙事」与 R-SP-8「实证 case 是合法消费者标注」冲突了多版,
两条各自被遵守一半 —— 用户拍板:**实证留 · 版本标走**。

清扫前全库 244 处版本标(49 个 spec 文件)· 其中相当一部分是本 session 自己近几版写进去的 ——
**版本标随发版必然持续渗入,写作约定挡不住自己人**,所以这道门必须是机器的:
不是「别写」,而是「写了就红」。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# 历史文件:版本标是它们的内容本体,不在门内
HISTORY = {"docs/CHANGELOG.md", "docs/CHANGELOG-ARCHIVE.md", "docs/RETRO-LEDGER.md"}
# v8.0 是范式名不是发版号(SKILL 顶部「v8.0 Code-driven」);门只拦 v8.1+
TAG = re.compile(r"v8\.[1-9]\d*")


def _spec_files():
    return [p for p in ROOT.rglob("*.md")
            if "pytest_cache" not in str(p)
            and str(p.relative_to(ROOT)) not in HISTORY]


class TestNoVersionTagsInSpecs(unittest.TestCase):

    def test_all_specs_are_tag_free(self):
        """🔴 门本体:任何 spec 行含 v8.N+ 即红(SKILL frontmatter `version:` 行豁免 —— 版本单源)。"""
        offenders = []
        for p in _spec_files():
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if line.startswith("version:"):
                    continue
                if TAG.search(line):
                    offenders.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()[:80]}")
        self.assertEqual(offenders, [],
                         "spec 出现版本标(conventions §spec 写作约定 · 历史归 CHANGELOG):\n"
                         + "\n".join(offenders))

    def test_version_single_source_untouched(self):
        """清扫绝不许伤版本单源:SKILL frontmatter 的 version 行必须还是真版本号。"""
        head = (ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines()[:6]
        self.assertTrue(any(re.match(r"^version: v8\.\d+", l) for l in head),
                        "SKILL.md frontmatter version 行被清扫误伤")

    def test_paradigm_marker_survives(self):
        """v8.0 范式标是明文例外 · 不许被顺手清掉。"""
        t = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("v8.0 Code-driven", t)


class TestConventionsRulingApplied(unittest.TestCase):
    """conventions 与 R-SP-8 的冲突按用户裁定收口 —— 条文本身也要锁,防哪版又改回去。"""

    def setUp(self):
        self.t = (ROOT / "docs" / "conventions.md").read_text(encoding="utf-8")

    def test_case_evidence_now_allowed(self):
        self.assertIn("实证 case 允许写", self.t)
        self.assertIn("R-SP-8", self.t, "未 cite 对齐来源 · 下次读到会当成孤立规则")
        self.assertNotIn("不写 case-id / 实证叙事", self.t, "旧禁令还在 = 两条又打架")

    def test_pure_archaeology_still_banned_with_criterion(self):
        """放开的是实证 · 不是考古 —— 边界判据必须写明,否则「允许实证」会被扩大解释。"""
        self.assertIn("纯考古", self.t)
        self.assertIn("说服力", self.t, "缺可判定判据(删掉这句规则说服力掉不掉)")

    def test_version_tag_ban_now_machine_gated(self):
        self.assertIn("机器门", self.t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
