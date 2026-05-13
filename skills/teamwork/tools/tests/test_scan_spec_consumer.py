#!/usr/bin/env python3
"""scan-spec-consumer.py 回归套件 · R-SP-8 writer-only 规则扫描器。"""

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
SCRIPT = TOOLS / "scan-spec-consumer.py"


def run(args: list[str], expect_exit: int = 0) -> tuple[str, dict | None]:
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\n"
        f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    )
    out = r.stdout
    payload: dict | None = None
    if r.returncode == 0 and "--output-format" not in args:
        try:
            payload = json.loads(out)
        except json.JSONDecodeError:
            raise AssertionError(f"stdout 非 JSON\n{out}")
    elif r.returncode == 2:
        try:
            payload = json.loads(r.stderr)
        except json.JSONDecodeError:
            pass
    return out, payload


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="scs_"))
        # 最小 skill root
        (self.tmp / "SKILL.md").write_text("# SKILL\n", encoding="utf-8")
        (self.tmp / "stages").mkdir()
        (self.tmp / "standards").mkdir()
        (self.tmp / "roles").mkdir()
        (self.tmp / "rules").mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel: str, content: str) -> None:
        p = self.tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(content), encoding="utf-8")


class TestDetection(_Base):
    def test_rule_with_consumer_classified_correctly(self) -> None:
        self.write("stages/dev-stage.md", """\
            # Dev Stage

            🔴 必须调用 state.py · 否则 enter-stage exit 1 拒绝进入下一 Stage。
        """)
        _, payload = run(["--skill-root", str(self.tmp), "--limit", "0"])
        assert payload is not None
        self.assertEqual(payload["total_rules"], 1)
        self.assertEqual(payload["with_consumer"], 1)
        self.assertEqual(payload["missing_consumer"], 0)

    def test_writer_only_rule_flagged(self) -> None:
        self.write("stages/dev-stage.md", """\
            # Dev Stage

            🔴 必须创建 state.json。
        """)
        _, payload = run(["--skill-root", str(self.tmp), "--limit", "0"])
        assert payload is not None
        self.assertEqual(payload["total_rules"], 1)
        self.assertEqual(payload["missing_consumer"], 1)
        missing = payload["missing"]
        self.assertEqual(len(missing), 1)
        self.assertIn("必须创建 state.json", missing[0]["line_text"])

    def test_consumer_in_nearby_lines_counts(self) -> None:
        """同段内 ±8 行包含消费者标志 → has_consumer。"""
        self.write("stages/dev-stage.md", """\
            # Dev Stage

            🔴 角色切换必须 cite 关键要点。
            不 cite 时评审退化为自我对话（实证 PTR-F001 case）。
        """)
        _, payload = run(["--skill-root", str(self.tmp), "--limit", "0"])
        assert payload is not None
        self.assertEqual(payload["with_consumer"], 1)
        self.assertEqual(payload["missing_consumer"], 0)

    def test_multiple_keywords_detected(self) -> None:
        """必须 / 必填 / 必读 / 禁止 都识别为规则触发。"""
        self.write("rules/check.md", """\
            # Rules

            🔴 必填字段 X。
            🔴 必读 spec Y。
            🔴 禁止编造行号。
            🔴 不得绕过 state.py。
        """)
        _, payload = run(["--skill-root", str(self.tmp), "--limit", "0"])
        assert payload is not None
        self.assertEqual(payload["total_rules"], 4)


class TestOutputFormats(_Base):
    def test_json_output_well_formed(self) -> None:
        self.write("rules/x.md", "🔴 必须 do something.\n")
        _, payload = run(["--skill-root", str(self.tmp), "--limit", "0"])
        assert payload is not None
        # 必含字段
        for field in ("verdict", "tool", "tool_version", "total_rules",
                      "with_consumer", "missing_consumer", "ratio_missing",
                      "missing", "rendered_at"):
            self.assertIn(field, payload)

    def test_markdown_output_renders(self) -> None:
        # 两条规则用足够空行分隔（避开 ±8 行扫描窗口）· 一 writer-only / 一 has-consumer
        sep = "\n" * 20
        self.write("rules/x.md", f"🔴 必须 do X.{sep}🔴 必须 do Y · exit 1 否则.\n")
        out, _ = run([
            "--skill-root", str(self.tmp),
            "--output-format", "markdown", "--limit", "0",
        ])
        self.assertIn("# Spec Consumer Coverage Report", out)
        self.assertIn("Total 🔴/必须 rules:", out)
        self.assertIn("Writer-only rules", out)

    def test_limit_truncates_output(self) -> None:
        # 创建 5 条 writer-only 规则
        lines = "\n".join(f"🔴 必须 do {i}." for i in range(5))
        self.write("rules/x.md", lines)
        _, payload = run(["--skill-root", str(self.tmp), "--limit", "2"])
        assert payload is not None
        self.assertEqual(payload["missing_consumer"], 5)
        self.assertEqual(len(payload["missing"]), 2)
        self.assertTrue(payload.get("truncated"))


class TestFailures(_Base):
    def test_missing_skill_root(self) -> None:
        _, payload = run([
            "--skill-root", str(self.tmp / "nope"),
            "--limit", "0",
        ], expect_exit=2)
        assert payload is not None
        self.assertEqual(payload["verdict"], "FAIL")
        self.assertIn("SKILL.md", payload["error"])

    def test_empty_skill_root(self) -> None:
        # 删 SKILL.md
        (self.tmp / "SKILL.md").unlink()
        _, payload = run([
            "--skill-root", str(self.tmp),
            "--limit", "0",
        ], expect_exit=2)
        assert payload is not None
        self.assertEqual(payload["verdict"], "FAIL")


class TestRealSpec(unittest.TestCase):
    """对真实 teamwork spec 跑 · 防 scanner 突然崩。"""

    SKILL_ROOT = TOOLS.parent

    def test_real_spec_scans_without_crash(self) -> None:
        cmd = [sys.executable, str(SCRIPT),
               "--skill-root", str(self.SKILL_ROOT), "--limit", "10"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
        payload = json.loads(r.stdout)
        # 至少扫到一些规则（spec 有几百条 · 不可能为 0）
        self.assertGreater(payload["total_rules"], 50)
        # missing 数量限制为 10
        self.assertLessEqual(len(payload["missing"]), 10)


if __name__ == "__main__":
    unittest.main()
