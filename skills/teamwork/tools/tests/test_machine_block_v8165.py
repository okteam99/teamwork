#!/usr/bin/env python3
"""v8.165 · PRD 机读契约搬进 <!-- TEAMWORK-MACHINE --> 注释块回归套件。

治本:YAML frontmatter 在 Zed / GitHub 等主流渲染器**不隐藏**(裸露机读 AC = 预览冗余)·
v8.158「机读内容预览隐藏」目标对 frontmatter 没达成。改:机读契约落 HTML 注释块(所有
渲染器都隐藏)· verify-ac + goal-complete 的解析器优先读注释块 · 兜底 --- frontmatter
(旧 PRD / 其他产物 TC/REVIEW 仍用 frontmatter · 不破)。

覆盖:
- 引擎 parse_frontmatter:读 TEAMWORK-MACHINE 块 / 兜底 frontmatter / 两者无 → None /
  注释块优先于 frontmatter
- verify-ac extract_frontmatter:从注释块抽 AC ids / 从 frontmatter 兜底抽

运行:python3 -m pytest skills/teamwork/tools/tests/test_machine_block_v8165.py -v
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS))

from _v8_engine import parse_frontmatter  # type: ignore  # noqa: E402

# verify-ac.py 是连字符脚本 · 用 importlib 加载
_VA = TOOLS.parent / "templates" / "verify-ac.py"
_spec = importlib.util.spec_from_file_location("verify_ac", _VA)
verify_ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify_ac)  # type: ignore

MACHINE_PRD = """<!-- TEAMWORK-MACHINE · 机读契约 · 预览隐藏
feature_id: "X-F001-demo"
status: pending_review
acceptance_criteria:
  - id: AC-1
    category: functional
  - id: AC-2
revision_history:
  - {version: "0.1", date: "2026-06-14", changes: "首版"}
-->

# Demo PRD

## 验收标准
"""

FM_PRD = """---
feature_id: "Y-F002-old"
acceptance_criteria:
  - id: AC-9
revision_history:
  - {version: "0.1"}
---

# Old PRD
"""


class TestEngineParseFrontmatter(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mblk-eng-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, content: str) -> Path:
        p = self.tmp / "PRD.md"
        p.write_text(content, encoding="utf-8")
        return p

    def test_reads_machine_block(self):
        # goal-complete 的两个 PRD 门:acceptance_criteria 存在 + revision_history ≥1
        fm = parse_frontmatter(self._write(MACHINE_PRD))
        self.assertIsNotNone(fm)
        self.assertIn("acceptance_criteria", fm)
        self.assertTrue(fm.get("revision_history"))

    def test_falls_back_to_frontmatter(self):
        # 旧 PRD / 其他产物仍用 --- frontmatter · 兜底不破
        fm = parse_frontmatter(self._write(FM_PRD))
        self.assertIsNotNone(fm)
        self.assertIn("acceptance_criteria", fm)
        self.assertTrue(fm.get("revision_history"))

    def test_none_when_neither(self):
        fm = parse_frontmatter(self._write("# 无机读块\n正文\n"))
        self.assertIsNone(fm)

    def test_machine_block_preferred_over_frontmatter(self):
        # 同时有 --- 和注释块 → 注释块优先(feature_id 取注释块的)
        mixed = "---\nfeature_id: \"FM-WINS\"\n---\n" + MACHINE_PRD
        fm = parse_frontmatter(self._write(mixed))
        self.assertEqual(fm.get("feature_id"), '"X-F001-demo"')


class TestVerifyAcExtract(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mblk-va-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ids(self, content: str):
        p = self.tmp / "PRD.md"
        p.write_text(content, encoding="utf-8")
        fm = verify_ac.parse_frontmatter(verify_ac.extract_frontmatter(p))
        return [ac.get("id") for ac in (fm.get("acceptance_criteria") or [])]

    def test_extract_from_machine_block(self):
        self.assertEqual(self._ids(MACHINE_PRD), ["AC-1", "AC-2"])

    def test_extract_from_frontmatter_fallback(self):
        self.assertEqual(self._ids(FM_PRD), ["AC-9"])


class TestTemplateMachineBlockWellFormed(unittest.TestCase):
    """v8.171:模板 TEAMWORK-MACHINE 块必须是**单个 well-formed HTML 注释** ——
    marker 行禁含字面 `-->`(否则浏览器在第一个 `-->` 提前闭合注释 · YAML 裸露在
    预览 · v8.165 隐藏机读内容的目标被自身 marker 文字破坏 · 实测 TermPro 编辑器)。
    """

    def test_no_premature_comment_close(self):
        prd = (TOOLS.parent / "templates" / "prd.md").read_text(encoding="utf-8")
        start = prd.index("<!-- TEAMWORK-MACHINE")
        # 浏览器看到的注释 = 从 <!-- 到**第一个** -->
        close = prd.index("-->", start)
        browser_comment = prd[start:close]
        # 若 marker 行无字面 --> · 第一个 --> 即真正闭合 · 注释含完整 YAML
        self.assertIn("feature_id:", browser_comment,
                      "marker 行可能含字面 --> 提前闭合注释 · feature_id 裸露在预览")
        self.assertIn("revision_history:", browser_comment,
                      "marker 行含字面 --> · YAML 尾部裸露在预览")


if __name__ == "__main__":
    unittest.main()
