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

    # ─── v7.3.10+P0-155: section-aware --flow / --feature 治本 Dev→Review 歧义 ─

    def test_dev_review_ambiguous_without_flow(self) -> None:
        """Dev→Review 在 Feature + 敏捷需求 两个 section 都有 · 不带 --flow → 歧义 FAIL."""
        _, audit = run(["--from", "Dev", "--to", "Review"], expect_exit=2)
        self.assertEqual(audit["verdict"], "FAIL")
        self.assertIn("匹配歧义", audit["error"])
        # matches_detail 必含每个匹配的 section
        sections = [m["section"] for m in audit["matches_detail"]]
        self.assertIn("Feature 流程", sections)
        self.assertIn("敏捷需求流程", sections)
        # hint 必提 --flow
        self.assertIn("--flow", audit["hint"])

    def test_dev_review_flow_feature_resolves(self) -> None:
        """--flow Feature 缩到 Feature 流程 section · L163."""
        out, audit = run(["--from", "Dev", "--to", "Review", "--flow", "Feature"])
        self.assertEqual(audit["verdict"], "OK")
        self.assertIn("Dev Stage", out)
        self.assertIn("Review Stage", out)
        # 真实 spec L163（漂移时此 assertion 会提醒 · 同 design_review_to_blueprint）
        self.assertGreater(audit["matched_line"], 100)
        self.assertLess(audit["matched_line"], 250)

    def test_dev_review_flow_agile_resolves(self) -> None:
        """--flow 敏捷需求 缩到敏捷需求流程 section · L264."""
        out, audit = run(["--from", "Dev", "--to", "Review", "--flow", "敏捷需求"])
        self.assertEqual(audit["verdict"], "OK")
        # 敏捷需求 section 在 spec 后半 · L264
        self.assertGreater(audit["matched_line"], 250)

    def test_flow_topic_strips_suffix_exact(self) -> None:
        """--flow Feature 不应误匹配 'Feature Planning 流程' section（topic 精确匹配）."""
        # Feature Planning section 没有 Dev→Review 转移 · 但确认 topic 不重叠：
        # _section_topic("Feature Planning 流程") = "Feature Planning" ≠ "Feature"
        # 用一个 Feature 流程内独有的转移确认
        _, audit = run(["--from", "Dev Stage", "--to", "Review Stage",
                         "--flow", "Feature"])
        self.assertEqual(audit["verdict"], "OK")


class TestP0_155FeatureAutoDerive(unittest.TestCase):
    """v7.3.10+P0-155: --feature 路径自动从 state.json.flow_type 派生 --flow."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ft_feat_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_state(self, flow_type: str) -> None:
        (self.tmp / "state.json").write_text(
            json.dumps({"flow_type": flow_type}), encoding="utf-8"
        )

    def test_feature_path_auto_derives_flow_type(self) -> None:
        """--feature 含 state.json (flow_type=Feature) · 自动派生 → 解 Dev→Review 歧义."""
        self._write_state("Feature")
        out, audit = run(["--from", "Dev", "--to", "Review",
                           "--feature", str(self.tmp)])
        self.assertEqual(audit["verdict"], "OK")
        # Feature section · L163
        self.assertLess(audit["matched_line"], 250)

    def test_feature_path_agile_flow(self) -> None:
        """--feature 含 flow_type=敏捷需求 · 自动派生 → 解到 L264."""
        self._write_state("敏捷需求")
        out, audit = run(["--from", "Dev", "--to", "Review",
                           "--feature", str(self.tmp)])
        self.assertEqual(audit["verdict"], "OK")
        self.assertGreater(audit["matched_line"], 250)

    def test_feature_missing_state_falls_back_to_ambiguous(self) -> None:
        """--feature 路径没 state.json · 静默 fallback · 仍歧义 FAIL."""
        # 不写 state.json · tmp 为空
        _, audit = run(["--from", "Dev", "--to", "Review",
                         "--feature", str(self.tmp)], expect_exit=2)
        self.assertIn("匹配歧义", audit["error"])

    def test_flow_explicit_overrides_feature(self) -> None:
        """--flow 显式优先于 --feature 派生."""
        self._write_state("敏捷需求")  # state 是敏捷需求
        out, audit = run(["--from", "Dev", "--to", "Review",
                           "--feature", str(self.tmp),
                           "--flow", "Feature"])  # 但 --flow 显式给 Feature
        self.assertEqual(audit["verdict"], "OK")
        self.assertLess(audit["matched_line"], 250)  # 走 Feature section


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
