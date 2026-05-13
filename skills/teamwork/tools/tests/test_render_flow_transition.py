#!/usr/bin/env python3
"""render-flow-transition.py 回归套件 · scripts-policy R-SP-6 render-first 物化。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SCRIPT = TOOLS / "render-flow-transition.py"
DEFAULT_SPEC = TOOLS.parent / "rules" / "flow-transitions.md"


def run(args: list[str], expect_exit: int = 0) -> tuple[str, dict]:
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\n"
        f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    )
    try:
        audit = json.loads(r.stderr) if r.stderr.strip() else {}
    except json.JSONDecodeError:
        raise AssertionError(f"stderr 非 JSON (R-SP-4 违反)\nstderr:\n{r.stderr}")
    return r.stdout, audit


class TestRealSpec(unittest.TestCase):
    """对真实 flow-transitions.md 跑 · 防 spec 漂移。"""

    def test_design_review_to_blueprint(self) -> None:
        """本对话 case 反例：AI 编造 L153 + 原文 · 工具直接读真实行。"""
        out, audit = run(["--from", "设计批 待确认", "--to", "Blueprint"])
        self.assertIn("📋", out)
        self.assertIn("→", out)
        self.assertIn("📖 ⏸️", out)
        self.assertIn("flow-transitions.md L", out)
        # 真实行号（按当前 flow-transitions.md 状态 · 漂移时此 case 会提醒）
        self.assertEqual(audit["verdict"], "OK")
        self.assertGreater(audit["matched_line"], 100)
        self.assertEqual(audit["type_icon"], "⏸️")

    def test_blueprint_to_pause(self) -> None:
        """另一个 happy case · 缩窄关键词避免歧义。"""
        out, audit = run(["--from", "Blueprint Stage", "--to", "方案待确认"])
        self.assertIn("Blueprint", out)
        self.assertIn("方案待确认", out)
        self.assertEqual(audit["type_icon"], "⏸️")


class TestSyntheticSpec(unittest.TestCase):
    """用临时 spec 文件覆盖边界 · 不依赖真实文件状态。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ft_"))
        self.spec = self.tmp / "ft.md"
        self.spec.write_text(textwrap.dedent("""\
            # Header

            | from | to | 类型 | 说明 |
            | --- | --- | --- | --- |
            | A | B | 🚀自动 | 测试自动 |
            | C | D | ⏸️暂停 | 测试暂停 |
            | E | F | 🔀条件 | 测试条件 |
            | G | H | ⏸️暂停 | 重复 H 之 1 |
            | G | H2 | ⏸️暂停 | 重复 H 之 2（不同 to）|
            """), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_auto_transition(self) -> None:
        out, audit = run(["--from", "A", "--to", "B", "--spec", str(self.spec)])
        self.assertIn("📖 🚀", out)
        self.assertEqual(audit["type_icon"], "🚀")

    def test_condition_transition(self) -> None:
        out, audit = run(["--from", "E", "--to", "F", "--spec", str(self.spec)])
        self.assertEqual(audit["type_icon"], "🔀")
        self.assertIn("📖 🔀", out)

    def test_no_match_fails(self) -> None:
        _, audit = run([
            "--from", "NotExist", "--to", "AlsoNotExist",
            "--spec", str(self.spec),
        ], expect_exit=2)
        self.assertEqual(audit["verdict"], "FAIL")
        self.assertIn("未在 flow-transitions.md 找到匹配", audit["error"])

    def test_ambiguous_fails(self) -> None:
        # G → H 也命中 G → H2（H2 含 H · 双向匹配会同时命中）
        _, audit = run([
            "--from", "G", "--to", "H",
            "--spec", str(self.spec),
        ], expect_exit=2)
        self.assertIn("匹配歧义", audit["error"])
        self.assertIn("ambiguous_lines", audit)

    def test_missing_spec_fails(self) -> None:
        _, audit = run([
            "--from", "A", "--to", "B",
            "--spec", str(self.tmp / "nope.md"),
        ], expect_exit=2)
        self.assertIn("flow-transitions.md 不存在", audit["error"])


if __name__ == "__main__":
    unittest.main()
