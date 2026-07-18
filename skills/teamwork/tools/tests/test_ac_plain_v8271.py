"""v8.271:每条 AC 必配 💬 大白话(§验收标准表列 · goal-complete 逐条机器校验)。

BDD 给 QA/机器绑 TC · 大白话给用户终确认拍板(非技术也能逐条看懂在验证什么)。
"""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import _v8_stage_specs as S

HEAD = "# PRD\n\n## 验收标准\n\n"
TAIL = "\n\n## Out of Scope\n\n无\n"


class TestAcPlain(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-acplain-"))

    def _run(self, table: str):
        (self.tmp / "PRD.md").write_text(HEAD + table + TAIL, encoding="utf-8")
        return S._evidence_ac_plain_present({}, NS(feature=str(self.tmp)))

    def test_filled_plain_passes(self):
        ok, msg = self._run(
            "| ID | 描述(BDD) | 💬 大白话 | 优先级 |\n|---|---|---|---|\n"
            "| AC-1 | Given/When/Then | 登录后能看到头像 | P0 |\n"
            "| AC-2 | Given/When/Then | 断网时给出可重试提示 | P1 |")
        self.assertTrue(ok, msg)

    def test_missing_column_fails(self):
        ok, msg = self._run(
            "| ID | 描述(BDD) | 优先级 |\n|---|---|---|\n"
            "| AC-1 | Given/When/Then | P0 |")
        self.assertFalse(ok)
        self.assertIn("缺 💬 大白话 列", msg)

    def test_empty_and_placeholder_cells_fail_listing_ids(self):
        ok, msg = self._run(
            "| ID | 描述(BDD) | 💬 大白话 | 优先级 |\n|---|---|---|---|\n"
            "| AC-1 | Given/When/Then | 正常说明 | P0 |\n"
            "| AC-2 | Given/When/Then | | P0 |\n"
            "| AC-3 | Given/When/Then | {一句人话:这条在验证什么} | P1 |")
        self.assertFalse(ok)
        self.assertIn("AC-2", msg)
        self.assertIn("AC-3", msg)
        self.assertNotIn("AC-1", msg)

    def test_no_section_defers_to_conformance(self):
        (self.tmp / "PRD.md").write_text("# PRD\n\n无验收段", encoding="utf-8")
        ok, _ = S._evidence_ac_plain_present({}, NS(feature=str(self.tmp)))
        self.assertTrue(ok)

    def test_plain_cell_containing_keyword_not_misparsed(self):
        ok, msg = self._run(
            "| ID | 描述(BDD) | 💬 大白话 | 优先级 |\n|---|---|---|---|\n"
            "| AC-1 | Given/When/Then | 用大白话讲:能一键导出 | P0 |")
        self.assertTrue(ok, msg)


class TestGoalFinalConfirmPrdPathEcho(unittest.TestCase):
    """v8.272:PRD 终确认暂停点导读头行回显 PRD 绝对路径(brief 消费时点携带)。"""

    def test_goal_brief_carries_prd_path_echo(self):
        self.assertIn("PRD 绝对路径", S._goal_brief({}))
        self.assertIn("PRD 绝对路径", S._goal_brief({"fast_mode": True}))
