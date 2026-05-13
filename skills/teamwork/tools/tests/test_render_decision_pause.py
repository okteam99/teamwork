#!/usr/bin/env python3
"""render-decision-pause.py 回归套件 · scripts-policy R-SP-6 render-first 物化。"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SCRIPT = TOOLS / "render-decision-pause.py"


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


class TestPMAcceptance(unittest.TestCase):
    """PM 验收（class 6）= 最常见决策点。"""

    def test_three_options_with_recommended(self) -> None:
        out, audit = run([
            "--decision-class", "6",
            "--pause-point", "PM 验收三选项",
            "--refs", "/abs/PRD.md,/abs/TC.md,/abs/test-report.md",
            "--options", "1=通过+Ship,2=通过不Ship,3=不通过+建议",
            "--recommended", "1",
        ])
        lines = out.strip().split("\n")
        self.assertEqual(lines[0], "⏸️ PM 验收三选项")
        self.assertIn("📚 决策参考：", out)
        self.assertIn("- /abs/PRD.md", out)
        self.assertIn("- /abs/TC.md", out)
        self.assertIn("- /abs/test-report.md", out)
        self.assertIn("请选（回数字）：", out)
        self.assertIn("1. 💡 通过+Ship（推荐）", out)
        self.assertIn("2. 通过不Ship", out)
        self.assertIn("3. 不通过+建议", out)
        # 自动补「其他指示」末项
        self.assertIn("4. 其他指示", out)
        # audit
        self.assertEqual(audit["verdict"], "OK")
        self.assertEqual(audit["decision_class"], 6)
        self.assertEqual(audit["recommended"], 1)

    def test_explicit_other_not_duplicated(self) -> None:
        """用户已显式给「其他指示」末项 · 工具不重复补。"""
        out, _ = run([
            "--decision-class", "6",
            "--pause-point", "PM 验收",
            "--refs", "/abs/PRD.md,/abs/TC.md",
            "--options", "1=A,2=B,3=其他指示",
            "--recommended", "1",
        ])
        # 不应出现 "4. 其他指示"
        self.assertNotIn("4. 其他指示", out)
        self.assertIn("3. 其他指示", out)


class TestNarrative(unittest.TestCase):
    def test_narrative_inserted(self) -> None:
        out, _ = run([
            "--decision-class", "1",
            "--pause-point", "Review QUALITY_ISSUE",
            "--refs", "/abs/REVIEW.md,/abs/src/foo.py",
            "--options", "1=A,2=B",
            "--recommended", "1",
            "--narrative", "本轮 finding 摘要: 架构师指出 3 处...",
        ])
        self.assertIn("本轮 finding 摘要", out)


class TestAutoRefs(unittest.TestCase):
    """v7.3.10+P0-144：--auto-refs 按 decision-class 自动发现 feature_dir 下的 refs。"""

    def setUp(self) -> None:
        import json
        import shutil
        import tempfile
        self.tmp = Path(tempfile.mkdtemp(prefix="rdp_auto_"))
        self.feature_dir = self.tmp / "auth" / "docs" / "features" / "F042"
        self.feature_dir.mkdir(parents=True)
        # state.json + PRD/TC/test-report
        state = {"feature_id": "AUTH-F042", "flow_type": "Feature"}
        (self.feature_dir / "state.json").write_text(
            json.dumps(state), encoding="utf-8"
        )
        (self.feature_dir / "PRD.md").write_text("# PRD", encoding="utf-8")
        (self.feature_dir / "TC.md").write_text("# TC", encoding="utf-8")
        self._shutil = shutil

    def tearDown(self) -> None:
        self._shutil.rmtree(self.tmp, ignore_errors=True)

    def test_auto_discover_class6_refs(self) -> None:
        out, audit = run([
            "--decision-class", "6",
            "--pause-point", "PM 验收",
            "--feature-dir", str(self.feature_dir),
            "--auto-refs",
            "--options", "1=A,2=B,3=C",
            "--recommended", "1",
        ])
        self.assertIn("📚 决策参考：", out)
        self.assertIn("/PRD.md", out)
        self.assertIn("/TC.md", out)
        self.assertIn("auto_discovered_refs", audit)
        self.assertGreaterEqual(len(audit["auto_discovered_refs"]), 2)

    def test_auto_refs_without_context_fails(self) -> None:
        _, audit = run([
            "--decision-class", "6",
            "--pause-point", "PM 验收",
            "--feature-dir", "/nonexistent/path",
            "--auto-refs",
            "--options", "1=A",
            "--recommended", "1",
        ], expect_exit=2)
        self.assertIn("feature context", audit["error"])

    def test_explicit_refs_merge_with_auto(self) -> None:
        """--refs 显式 + --auto-refs 同存 → 合并去重。"""
        out, _ = run([
            "--decision-class", "6",
            "--pause-point", "PM 验收",
            "--feature-dir", str(self.feature_dir),
            "--auto-refs",
            "--refs", "/abs/extra-report.md",
            "--options", "1=A,2=B,3=C",
            "--recommended", "1",
        ])
        self.assertIn("/abs/extra-report.md", out)
        self.assertIn("/PRD.md", out)


class TestValidation(unittest.TestCase):
    def test_invalid_decision_class(self) -> None:
        _, audit = run([
            "--decision-class", "99",
            "--pause-point", "x",
            "--refs", "/abs/PRD.md",
            "--options", "1=A",
            "--recommended", "1",
        ], expect_exit=2)
        self.assertIn("decision-class=99", audit["error"])
        self.assertIn("valid_classes", audit)

    def test_relative_path_rejected(self) -> None:
        _, audit = run([
            "--decision-class", "6",
            "--pause-point", "PM 验收",
            "--refs", "docs/PRD.md",  # 相对路径
            "--options", "1=A,2=B,3=C",
            "--recommended", "1",
        ], expect_exit=2)
        self.assertIn("绝对路径", audit["error"])

    def test_refs_not_match_class_expected(self) -> None:
        """class 6 PM 验收期望 PRD.md / TC.md / 测试报告 · refs 完全不符 → fail。"""
        _, audit = run([
            "--decision-class", "6",
            "--pause-point", "PM 验收",
            "--refs", "/abs/unrelated.txt,/abs/another.txt",
            "--options", "1=A,2=B,3=C",
            "--recommended", "1",
        ], expect_exit=2)
        self.assertIn("未命中任何期望类型", audit["error"])
        self.assertIn("expected_ref_keywords", audit)

    def test_recommended_not_in_options(self) -> None:
        _, audit = run([
            "--decision-class", "6",
            "--pause-point", "PM 验收",
            "--refs", "/abs/PRD.md,/abs/TC.md",
            "--options", "1=A,2=B,3=C",
            "--recommended", "5",  # 不在 1/2/3
        ], expect_exit=2)
        self.assertIn("--recommended=5", audit["error"])

    def test_options_non_consecutive(self) -> None:
        _, audit = run([
            "--decision-class", "6",
            "--pause-point", "PM 验收",
            "--refs", "/abs/PRD.md,/abs/TC.md",
            "--options", "1=A,3=C",  # 跳了 2
            "--recommended", "1",
        ], expect_exit=2)
        self.assertIn("不连续", audit["error"])

    def test_options_duplicate_num(self) -> None:
        _, audit = run([
            "--decision-class", "6",
            "--pause-point", "PM 验收",
            "--refs", "/abs/PRD.md,/abs/TC.md",
            "--options", "1=A,1=B",
            "--recommended", "1",
        ], expect_exit=2)
        self.assertIn("重复", audit["error"])

    def test_options_missing_equals(self) -> None:
        _, audit = run([
            "--decision-class", "6",
            "--pause-point", "PM 验收",
            "--refs", "/abs/PRD.md,/abs/TC.md",
            "--options", "1 通过,2 不通过",  # 缺 =
            "--recommended", "1",
        ], expect_exit=2)
        self.assertIn("缺 '='", audit["error"])


if __name__ == "__main__":
    unittest.main()
