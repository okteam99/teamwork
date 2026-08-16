"""PRD 验收标准表:大白话固定第二列(用户拍板)。

case(截图实证):消费项目 PRD 里 BDD 列巨长,大白话被挤到右侧竖条
(一行一字)—— 给用户终确认读的列反而最不可读。
治法:列序 ID → 💬 大白话 → 描述(BDD)(渲染时紧跟 ID 拿到可读列宽)
+ 指引「写一句完整的话」;机器校验按表头名定位 · 天然不吃列序(存量两种列序都过)。
"""
import argparse
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

from _v8_stage_specs import _evidence_ac_plain_present  # noqa: E402


def _run(table):
    d = Path(tempfile.mkdtemp(prefix="acp-"))
    (d / "PRD.md").write_text(f"## 验收标准\n\n{table}\n", encoding="utf-8")
    return _evidence_ac_plain_present({}, argparse.Namespace(feature=str(d)))


class TestTemplateOrder(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.t = (SKILL_ROOT / "templates" / "prd.md").read_text(encoding="utf-8")

    def test_plain_words_second_column(self):
        hdr = next(l for l in self.t.splitlines() if l.startswith("| ID |") and "大白话" in l)
        cells = [c.strip() for c in hdr.strip("|").split("|")]
        self.assertEqual(cells[1], "💬 大白话")
        self.assertEqual(cells[2], "描述(BDD)")

    def test_width_guidance_present(self):
        self.assertIn("固定第二列", self.t)
        self.assertIn("一句完整的话", self.t)
        self.assertIn("不吃列序", self.t)                 # 机器兼容声明

    def test_sample_rows_follow_order(self):
        row = next(l for l in self.t.splitlines() if l.startswith("| AC-2 |"))
        cells = [c.strip() for c in row.strip("|").split("|")]
        self.assertIn("登录成功后", cells[1])             # 大白话在第二格
        self.assertTrue(cells[2].startswith("Given"))


class TestEvidenceOrderAgnostic(unittest.TestCase):
    """机器门按表头名定位 —— 新旧列序都过(存量 PRD 零迁移)。"""

    NEW = ("| ID | 💬 大白话 | 描述(BDD) | 优先级 |\n|---|---|---|---|\n"
           "| AC-1 | 用户能看到头像 | Given/When/Then | P0 |")
    OLD = ("| ID | 描述(BDD) | 💬 大白话 | 优先级 |\n|---|---|---|---|\n"
           "| AC-1 | Given/When/Then | 用户能看到头像 | P0 |")

    def test_new_order_passes(self):
        ok, _ = _run(self.NEW)
        self.assertTrue(ok)

    def test_legacy_order_still_passes(self):
        ok, _ = _run(self.OLD)
        self.assertTrue(ok)

    def test_empty_plain_still_caught_in_new_order(self):
        ok, msg = _run("| ID | 💬 大白话 | 描述(BDD) |\n|---|---|---|\n"
                       "| AC-1 | — | Given/When/Then |")
        self.assertFalse(ok)
        self.assertIn("AC-1", msg)


if __name__ == "__main__":
    unittest.main()
