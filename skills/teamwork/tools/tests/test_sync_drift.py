#!/usr/bin/env python3
"""sync-drift.py 回归套件 · marker-aware 同步引擎。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SKILL = TOOLS.parent
SCRIPT = TOOLS / "sync-drift.py"
SOURCE = SKILL / "templates" / "host-instruction-injection.md"


def run(args: list[str], expect_exit: int = 0) -> dict:
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    )
    raw = r.stdout if r.returncode == 0 else (r.stdout or r.stderr)
    return json.loads(raw)


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="sync_"))
        self.target = self.tmp / "CLAUDE.md"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestInitCreate(_Base):
    def test_create_when_missing_with_init(self) -> None:
        d = run(["--target", str(self.target), "--source", str(SOURCE),
                 "--skill-version", "v7.3.10+P0-134", "--init"])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["action"], "created")
        self.assertIn("teamwork-pointer", d["sections_inserted"])
        self.assertTrue(self.target.exists())
        text = self.target.read_text(encoding="utf-8")
        self.assertIn("TEAMWORK_BEGIN:teamwork-pointer v7.3.10+P0-134", text)
        self.assertIn("TEAMWORK_END:teamwork-pointer", text)

    def test_missing_without_init_fails(self) -> None:
        d = run(["--target", str(self.target), "--source", str(SOURCE),
                 "--skill-version", "v7.3.10+P0-134"], expect_exit=2)
        self.assertEqual(d["verdict"], "FAIL")


class TestIdempotency(_Base):
    def test_same_version_is_noop(self) -> None:
        run(["--target", str(self.target), "--source", str(SOURCE),
             "--skill-version", "v7.3.10+P0-134", "--init"])
        d = run(["--target", str(self.target), "--source", str(SOURCE),
                 "--skill-version", "v7.3.10+P0-134"])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["action"], "noop")
        self.assertIn("teamwork-pointer", d["sections_unchanged"])


class TestUserContentPreservation(_Base):
    def test_user_content_outside_markers_preserved_on_upgrade(self) -> None:
        run(["--target", str(self.target), "--source", str(SOURCE),
             "--skill-version", "v7.3.10+P0-134", "--init"])
        # 用户在 marker 外加内容
        with self.target.open("a", encoding="utf-8") as f:
            f.write("\n\n# 用户编辑段\n用户自定义内容 1\n用户自定义内容 2\n")
        d = run(["--target", str(self.target), "--source", str(SOURCE),
                 "--skill-version", "v7.3.10+P0-135"])
        self.assertEqual(d["action"], "updated")
        self.assertEqual(d["sections_updated"][0]["from_version"], "v7.3.10+P0-134")
        self.assertEqual(d["sections_updated"][0]["to_version"], "v7.3.10+P0-135")
        # 用户内容仍在
        text = self.target.read_text(encoding="utf-8")
        self.assertIn("用户自定义内容 1", text)
        self.assertIn("用户自定义内容 2", text)
        # marker 版本已升
        self.assertIn("TEAMWORK_BEGIN:teamwork-pointer v7.3.10+P0-135", text)


class TestDryRun(_Base):
    def test_dry_run_no_write(self) -> None:
        run(["--target", str(self.target), "--source", str(SOURCE),
             "--skill-version", "v7.3.10+P0-134", "--init"])
        before = self.target.read_text(encoding="utf-8")
        d = run(["--target", str(self.target), "--source", str(SOURCE),
                 "--skill-version", "v7.3.10+P0-200", "--dry-run"])
        self.assertEqual(d["verdict"], "DRY_RUN")
        self.assertEqual(self.target.read_text(encoding="utf-8"), before)


class TestMissingMarkerWithoutInit(_Base):
    def test_target_exists_but_no_marker_without_init(self) -> None:
        # 模拟用户已有 CLAUDE.md 但没有 teamwork marker
        self.target.write_text("# 用户已有的 CLAUDE.md\n\n用户内容\n", encoding="utf-8")
        d = run(["--target", str(self.target), "--source", str(SOURCE),
                 "--skill-version", "v7.3.10+P0-134"], expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("--init", d["hint"])
        # 用户内容未被改
        self.assertIn("用户已有的 CLAUDE.md", self.target.read_text(encoding="utf-8"))

    def test_target_exists_no_marker_with_init_inserts_top(self) -> None:
        self.target.write_text("# 用户已有内容\n", encoding="utf-8")
        d = run(["--target", str(self.target), "--source", str(SOURCE),
                 "--skill-version", "v7.3.10+P0-134", "--init"])
        self.assertEqual(d["action"], "updated")
        self.assertIn("teamwork-pointer", d["sections_inserted"])
        text = self.target.read_text(encoding="utf-8")
        # marker 应在文件顶部 + 用户内容仍在底部
        self.assertTrue(text.startswith("<!-- TEAMWORK_BEGIN:teamwork-pointer"))
        self.assertIn("# 用户已有内容", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
