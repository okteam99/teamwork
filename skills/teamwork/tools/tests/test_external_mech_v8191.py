#!/usr/bin/env python3
"""v8.191 · external 机械成本三连修回归套件。

治本(harvest 20× · 耗时归因原因 2):① CLI 未登录到 review 才发现 → --preflight 微 probe
② 超时/空跑手动重跑吃墙钟 → 自动重试一次(1.5x)+ localconfig 超时可调
③ 每采纳 finding 即全量重跑 → --verify-fixes 增量重验(上轮已评 commit..HEAD 修复 diff)。

运行:python3 -m pytest skills/teamwork/tools/tests/test_external_mech_v8191.py -q
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

from state import (_external_timeout_sec, _find_prior_external_review,  # noqa: E402
                   _build_verify_fixes_block, _preflight_external,
                   EXTERNAL_REVIEW_TIMEOUT_SEC)


class TestTimeoutConfig(unittest.TestCase):
    def test_default_when_no_localconfig(self):
        d = Path(tempfile.mkdtemp()); (d / ".git").mkdir()
        self.assertEqual(_external_timeout_sec(d), EXTERNAL_REVIEW_TIMEOUT_SEC)

    def test_localconfig_override(self):
        d = Path(tempfile.mkdtemp()); (d / ".git").mkdir()
        (d / ".teamwork_localconfig.json").write_text(
            json.dumps({"external_review_timeout_sec": 900}), encoding="utf-8")
        sub = d / "a" / "b"; sub.mkdir(parents=True)
        self.assertEqual(_external_timeout_sec(sub), 900)

    def test_bad_value_falls_back(self):
        d = Path(tempfile.mkdtemp()); (d / ".git").mkdir()
        (d / ".teamwork_localconfig.json").write_text(
            json.dumps({"external_review_timeout_sec": -1}), encoding="utf-8")
        self.assertEqual(_external_timeout_sec(d), EXTERNAL_REVIEW_TIMEOUT_SEC)


class TestPriorReview(unittest.TestCase):
    def setUp(self):
        self.fd = Path(tempfile.mkdtemp())
        (self.fd / "external-cross-review").mkdir()

    def _write(self, name, commit):
        (self.fd / "external-cross-review" / name).write_text(
            f"---\nreview_model: codex\ntarget_commit: {commit}\n---\nbody", encoding="utf-8")

    def test_finds_target_commit(self):
        self._write("review-codex.md", "abc123")
        p, c = _find_prior_external_review(self.fd, "review")
        self.assertEqual(c, "abc123")

    def test_fixverify_file_also_counts(self):
        # 后续重验锚最新已验 commit(fixverify 结果也带 target_commit)
        self._write("review-codex.md", "abc123")
        import time, os
        self._write("review-codex-fixverify.md", "def456")
        os.utime(self.fd / "external-cross-review" / "review-codex-fixverify.md",
                 (time.time() + 10, time.time() + 10))
        _, c = _find_prior_external_review(self.fd, "review")
        self.assertEqual(c, "def456")

    def test_none_when_absent(self):
        self.assertIsNone(_find_prior_external_review(self.fd, "review"))
        self.assertIsNone(_find_prior_external_review(Path(tempfile.mkdtemp()), "review"))


class TestVerifyBlock(unittest.TestCase):
    def test_block_content(self):
        b = _build_verify_fixes_block("PRIOR FINDINGS", "abc", "def", "diff --git a/x")
        self.assertIn("增量重验", b)
        self.assertIn("abc..def", b)
        self.assertIn("fixed", b)
        self.assertIn("PRIOR FINDINGS", b)
        self.assertIn("不重评整个 feature", b)

    def test_caps_length(self):
        b = _build_verify_fixes_block("x" * 50000, "a", "b", "y" * 60000)
        self.assertLess(len(b), 55000)   # prior 20k + diff 30k + 框架文本

    def test_empty_diff_omits_section(self):
        b = _build_verify_fixes_block("F", "a", "b", "")
        self.assertNotIn("```diff", b)


class TestPreflight(unittest.TestCase):
    def test_which_missing(self):
        with mock.patch("shutil.which", return_value=None):
            r = _preflight_external("codex")
        self.assertFalse(r["ok"])
        self.assertEqual(r["step"], "which")

    def test_probe_auth_failure_classified(self):
        fake = mock.Mock(returncode=1, stdout="", stderr="Error: Not logged in")
        with mock.patch("shutil.which", return_value="/usr/bin/claude"), \
             mock.patch("state.subprocess.run", return_value=fake):
            r = _preflight_external("claude")
        self.assertFalse(r["ok"])
        self.assertIn("登录", r["reason"] + r["fix"])

    def test_probe_ok(self):
        fake = mock.Mock(returncode=0, stdout="PONG", stderr="")
        with mock.patch("shutil.which", return_value="/usr/bin/codex"), \
             mock.patch("state.subprocess.run", return_value=fake):
            r = _preflight_external("codex")
        self.assertTrue(r["ok"])


if __name__ == "__main__":
    unittest.main()
