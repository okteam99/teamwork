#!/usr/bin/env python3
"""render-afk-skip.py 回归套件 · scripts-policy R-SP-6 render-first 物化。"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SCRIPT = TOOLS / "render-afk-skip.py"


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


class TestHappy(unittest.TestCase):
    def test_render_afk_skip_format(self) -> None:
        out, audit = run([
            "--pause-point", "设计批待确认",
            "--decision", "通过 → Blueprint",
            "--reason", "Designer 自查 5 维度全 ✅ + 用户未提修订项",
        ])
        self.assertEqual(
            out.strip(),
            "⚡ auto skip: 设计批待确认 | 💡 通过 → Blueprint | 📝 Designer 自查 5 维度全 ✅ + 用户未提修订项",
        )
        self.assertEqual(audit["verdict"], "OK")
        self.assertEqual(audit["matched_afk_pause_point"], "设计批待确认")

    def test_match_with_space_variation(self) -> None:
        out, audit = run([
            "--pause-point", "设计批 待确认",  # 中间有空格
            "--decision", "通过 → Blueprint",
            "--reason", "Designer 自查通过",
        ])
        self.assertIn("⚡ auto skip:", out)
        self.assertEqual(audit["matched_afk_pause_point"], "设计批待确认")

    def test_prd_pending_match(self) -> None:
        out, _ = run([
            "--pause-point", "PRD 待确认",
            "--decision", "进 UI Design",
            "--reason", "PRD 评审 PASS · 含 UI",
        ])
        self.assertIn("💡 进 UI Design", out)


class TestHITLReject(unittest.TestCase):
    """治本本对话 case：AI 把 'auto 模式继续' 用在 HITL 点 → 工具拒绝。"""

    def test_pm_acceptance_rejected(self) -> None:
        _, audit = run([
            "--pause-point", "PM 验收三选项",
            "--decision", "通过", "--reason", "x",
        ], expect_exit=2)
        self.assertEqual(audit["verdict"], "FAIL")
        self.assertIn("HITL", audit["error"])
        self.assertIn("pmo-auto-mode.md § 五", audit["cite"])

    def test_ship_push_failed_rejected(self) -> None:
        _, audit = run([
            "--pause-point", "Ship Stage push FAILED",
            "--decision", "x", "--reason", "y",
        ], expect_exit=2)
        self.assertIn("HITL", audit["error"])

    def test_blueprint_concerns_rejected(self) -> None:
        _, audit = run([
            "--pause-point", "Blueprint Stage concerns",
            "--decision", "x", "--reason", "y",
        ], expect_exit=2)
        self.assertIn("HITL", audit["error"])


class TestUnknownPausePoint(unittest.TestCase):
    def test_unknown_rejected(self) -> None:
        _, audit = run([
            "--pause-point", "完全自创的暂停点 xxx",
            "--decision", "x", "--reason", "y",
        ], expect_exit=2)
        self.assertIn("不在 AFK 清单", audit["error"])
        self.assertIn("valid_afk_pause_points", audit)


class TestValidation(unittest.TestCase):
    def test_empty_decision(self) -> None:
        _, audit = run([
            "--pause-point", "设计批待确认",
            "--decision", "  ", "--reason", "x",
        ], expect_exit=2)
        self.assertIn("--decision", audit["error"])

    def test_empty_reason(self) -> None:
        _, audit = run([
            "--pause-point", "设计批待确认",
            "--decision", "x", "--reason", "",
        ], expect_exit=2)
        self.assertIn("--reason", audit["error"])


if __name__ == "__main__":
    unittest.main()
