#!/usr/bin/env python3
"""diff-html-vs-panorama.py 回归套件 · Designer 全景对齐物化校验。"""

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
SCRIPT = TOOLS / "diff-html-vs-panorama.py"


def run(args: list[str], expect_exit: int | None = None) -> tuple[int, dict]:
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    raw = r.stdout if r.stdout.strip() else r.stderr
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise AssertionError(
            f"非 JSON 输出（R-SP-4 违反）\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
        )
    if expect_exit is not None:
        assert r.returncode == expect_exit, (
            f"exit {r.returncode} ≠ {expect_exit}\n"
            f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
        )
    return r.returncode, payload


PANORAMA_HTML = textwrap.dedent("""\
    <!DOCTYPE html>
    <html><head><title>P</title></head>
    <body class="bg-slate-50 text-slate-900">
    <nav class="bg-slate-900 text-white">N</nav>
    <main class="flex gap-4 p-6">
      <aside class="w-64 bg-white border-r border-slate-200">A</aside>
      <section class="flex-1 text-base">C</section>
    </main>
    <footer class="bg-slate-100 text-sm text-slate-600">F</footer>
    </body></html>
""")

FEATURE_ALIGNED_HTML = textwrap.dedent("""\
    <!DOCTYPE html><html><body class="bg-slate-50">
    <nav class="bg-slate-900 text-white">N</nav>
    <main class="flex gap-4 p-6">
      <section class="flex-1 text-base">C</section>
    </main></body></html>
""")

FEATURE_DRIFT_HTML = textwrap.dedent("""\
    <!DOCTYPE html><html><body class="bg-purple-50">
    <nav class="bg-pink-500 text-yellow-300">N</nav>
    <main class="flex gap-12 p-20 text-3xl">Big</main>
    </body></html>
""")

FEATURE_MISSING_MAIN_HTML = textwrap.dedent("""\
    <!DOCTYPE html><html><body>
    <div class="bg-slate-50">No landmark</div>
    </body></html>
""")


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="dhvp_"))
        self.panorama = self.tmp / "panorama.html"
        self.panorama.write_text(PANORAMA_HTML, encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_feature(self, name: str, html: str) -> Path:
        p = self.tmp / name
        p.write_text(html, encoding="utf-8")
        return p


class TestAlignment(_Base):
    def test_aligned_feature_passes(self) -> None:
        f = self.write_feature("aligned.html", FEATURE_ALIGNED_HTML)
        exit_code, payload = run([
            "--panorama", str(self.panorama),
            "--feature", str(f),
        ], expect_exit=0)
        self.assertEqual(payload["verdict"], "OK")
        self.assertEqual(payload["diff"]["extra_colors"], [])
        self.assertEqual(payload["diff"]["extra_font_sizes"], [])
        self.assertEqual(payload["diff"]["extra_layouts"], [])
        self.assertEqual(payload["diff"]["color_alignment_pct"], 100.0)

    def test_panorama_landmarks_detected(self) -> None:
        f = self.write_feature("aligned.html", FEATURE_ALIGNED_HTML)
        _, payload = run([
            "--panorama", str(self.panorama),
            "--feature", str(f),
        ], expect_exit=0)
        self.assertEqual(
            set(payload["panorama_profile"]["landmarks"]),
            {"nav", "main", "aside", "section", "footer"},
        )


class TestDrift(_Base):
    def test_drift_feature_warns(self) -> None:
        f = self.write_feature("drift.html", FEATURE_DRIFT_HTML)
        exit_code, payload = run([
            "--panorama", str(self.panorama),
            "--feature", str(f),
        ], expect_exit=1)
        self.assertEqual(payload["verdict"], "WARN")
        diff = payload["diff"]
        self.assertIn("bg-pink-500", diff["extra_colors"])
        self.assertIn("bg-purple-50", diff["extra_colors"])
        self.assertIn("text-yellow-300", diff["extra_colors"])
        self.assertIn("text-3xl", diff["extra_font_sizes"])
        self.assertIn("gap-12", diff["extra_layouts"])
        self.assertIn("p-20", diff["extra_layouts"])
        # reasons 含三类
        self.assertTrue(any("color tokens" in r for r in payload["reasons"]))
        self.assertTrue(any("字号" in r for r in payload["reasons"]))

    def test_strict_mode_warn_becomes_fail(self) -> None:
        f = self.write_feature("drift.html", FEATURE_DRIFT_HTML)
        exit_code, payload = run([
            "--panorama", str(self.panorama),
            "--feature", str(f),
            "--strict",
        ], expect_exit=2)
        # verdict 仍是 WARN（语义不变）· 但 exit 升 2
        self.assertEqual(payload["verdict"], "WARN")


class TestMissingLandmark(_Base):
    def test_missing_main_blocker(self) -> None:
        f = self.write_feature("nomain.html", FEATURE_MISSING_MAIN_HTML)
        exit_code, payload = run([
            "--panorama", str(self.panorama),
            "--feature", str(f),
        ], expect_exit=2)
        self.assertEqual(payload["verdict"], "FAIL")
        self.assertIn("main", payload["diff"]["missing_required_landmarks"])
        self.assertTrue(any("landmark" in r for r in payload["reasons"]))


class TestFailures(_Base):
    def test_missing_panorama(self) -> None:
        exit_code, payload = run([
            "--panorama", str(self.tmp / "nope.html"),
            "--feature", str(self.write_feature("a.html", FEATURE_ALIGNED_HTML)),
        ], expect_exit=2)
        self.assertEqual(payload["verdict"], "FAIL")
        self.assertIn("panorama 不存在", payload["error"])

    def test_missing_feature(self) -> None:
        exit_code, payload = run([
            "--panorama", str(self.panorama),
            "--feature", str(self.tmp / "nope.html"),
        ], expect_exit=2)
        self.assertIn("feature 不存在", payload["error"])

    def test_empty_panorama(self) -> None:
        empty = self.tmp / "empty.html"
        empty.write_text("<html></html>", encoding="utf-8")
        exit_code, payload = run([
            "--panorama", str(empty),
            "--feature", str(self.write_feature("a.html", FEATURE_ALIGNED_HTML)),
        ], expect_exit=2)
        self.assertIn("未解析出任何 class", payload["error"])


class TestBatchMode(_Base):
    def test_feature_dir_scans_all_html(self) -> None:
        feat_dir = self.tmp / "feature"
        feat_dir.mkdir()
        (feat_dir / "aligned.html").write_text(FEATURE_ALIGNED_HTML, encoding="utf-8")
        (feat_dir / "drift.html").write_text(FEATURE_DRIFT_HTML, encoding="utf-8")
        exit_code, payload = run([
            "--panorama", str(self.panorama),
            "--feature-dir", str(feat_dir),
        ], expect_exit=1)
        # 整体 verdict = WARN（最差 result 决定）
        self.assertEqual(payload["verdict"], "WARN")
        self.assertEqual(payload["feature_count"], 2)
        verdicts = sorted(r["verdict"] for r in payload["results"])
        self.assertEqual(verdicts, ["OK", "WARN"])

    def test_feature_dir_no_html_fails(self) -> None:
        empty_dir = self.tmp / "empty_feature"
        empty_dir.mkdir()
        exit_code, payload = run([
            "--panorama", str(self.panorama),
            "--feature-dir", str(empty_dir),
        ], expect_exit=2)
        self.assertIn("无 .html", payload["error"])


if __name__ == "__main__":
    unittest.main()
