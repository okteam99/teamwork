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

    def make_modified_source(self) -> Path:
        """复制 SOURCE 并在 teamwork-pointer 段内加一行 · 模拟模板内容变化。"""
        text = SOURCE.read_text(encoding="utf-8")
        marked = text.replace(
            "\n<!-- TEAMWORK_END:teamwork-pointer",
            "\n[test] 模板新增内容行\n<!-- TEAMWORK_END:teamwork-pointer",
        )
        assert marked != text, "SOURCE 中未找到 teamwork-pointer END marker"
        p = self.tmp / "modified-source.md"
        p.write_text(marked, encoding="utf-8")
        return p


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

    def test_version_bump_alone_is_noop(self) -> None:
        """内容相同 + 仅版本号变 → noop 不重写(否则每次 patch bump 都 churn 宿主文件)。"""
        run(["--target", str(self.target), "--source", str(SOURCE),
             "--skill-version", "v8.100", "--init"])
        before = self.target.read_text(encoding="utf-8")
        d = run(["--target", str(self.target), "--source", str(SOURCE),
                 "--skill-version", "v8.100.1"])
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["action"], "noop")
        self.assertIn("teamwork-pointer", d["sections_unchanged"])
        # 文件逐字节未动 · marker 仍是旧版本号
        text = self.target.read_text(encoding="utf-8")
        self.assertEqual(text, before)
        self.assertIn("TEAMWORK_BEGIN:teamwork-pointer v8.100 -->", text)

    def test_content_change_updates_and_bumps_version(self) -> None:
        """内容变化 → updated · marker 版本号随内容一起更新。"""
        run(["--target", str(self.target), "--source", str(SOURCE),
             "--skill-version", "v8.100", "--init"])
        modified = self.make_modified_source()
        d = run(["--target", str(self.target), "--source", str(modified),
                 "--skill-version", "v8.101"])
        self.assertEqual(d["action"], "updated")
        self.assertEqual(d["sections_updated"][0]["from_version"], "v8.100")
        self.assertEqual(d["sections_updated"][0]["to_version"], "v8.101")
        text = self.target.read_text(encoding="utf-8")
        self.assertIn("[test] 模板新增内容行", text)
        self.assertIn("TEAMWORK_BEGIN:teamwork-pointer v8.101", text)


class TestUserContentPreservation(_Base):
    def test_user_content_outside_markers_preserved_on_upgrade(self) -> None:
        run(["--target", str(self.target), "--source", str(SOURCE),
             "--skill-version", "v7.3.10+P0-134", "--init"])
        # 用户在 marker 外加内容
        with self.target.open("a", encoding="utf-8") as f:
            f.write("\n\n# 用户编辑段\n用户自定义内容 1\n用户自定义内容 2\n")
        # 内容变化才触发 updated(纯版本 bump 是 noop)· 用修改过的 source
        modified = self.make_modified_source()
        d = run(["--target", str(self.target), "--source", str(modified),
                 "--skill-version", "v7.3.10+P0-135"])
        self.assertEqual(d["action"], "updated")
        self.assertEqual(d["sections_updated"][0]["from_version"], "v7.3.10+P0-134")
        self.assertEqual(d["sections_updated"][0]["to_version"], "v7.3.10+P0-135")
        # 用户外部内容行数统计精确(2 空行 + 3 内容行 = 5 · 空行不误判为 marker 内容)
        self.assertEqual(d["user_content_preserved_lines"], 5)
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
        # 内容变化(修改过的 source)才有 diff · dry-run 只报不写
        modified = self.make_modified_source()
        d = run(["--target", str(self.target), "--source", str(modified),
                 "--skill-version", "v7.3.10+P0-200", "--dry-run"])
        self.assertEqual(d["verdict"], "DRY_RUN")
        self.assertEqual(self.target.read_text(encoding="utf-8"), before)


class TestMissingMarkerWithoutInit(_Base):
    def test_target_exists_but_no_marker_without_init(self) -> None:
        # 模拟用户已有 CLAUDE.md 但没有 teamwork marker · 阻断错误(R-SP-5 exit 2)
        self.target.write_text("# 用户已有的 CLAUDE.md\n\n用户内容\n", encoding="utf-8")
        d = run(["--target", str(self.target), "--source", str(SOURCE),
                 "--skill-version", "v7.3.10+P0-134"], expect_exit=2)
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
