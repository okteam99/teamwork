#!/usr/bin/env python3
"""init_triage.py 回归套件 · 4 advisory topic + idempotent + skeleton 检测。"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SKILL = TOOLS.parent
INIT = TOOLS / "init_triage.py"
SKELETON_MARKER = "本文是 teamwork prepare-stage 自动创建的空骨架"


def run(args: list[str], expect_exit: int = 0) -> dict:
    cmd = [sys.executable, str(INIT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    )
    raw = r.stdout if r.returncode == 0 else (r.stdout or r.stderr)
    return json.loads(raw)


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.proj = Path(tempfile.mkdtemp(prefix="init_test_"))
        subprocess.run(["git", "init", "-q"], cwd=str(self.proj), check=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.proj, ignore_errors=True)

    def base_args(self) -> list[str]:
        return [
            "--cwd", str(self.proj),
            "--host", "claude-code",
            "--skill-root", str(SKILL),
            "--skill-version", "v7.3.10+P0-129",
        ]


class TestFreshRepo(_Base):
    def test_first_init_creates_skeletons(self) -> None:
        d = run(self.base_args())
        self.assertEqual(d["verdict"], "OK")
        self.assertTrue(d["project_files"]["TROUBLESHOOTING.md"]["created_now"])
        self.assertTrue(d["project_files"]["GLOSSARY.md"]["created_now"])
        topics = [a["topic"] for a in d["advisories"]]
        self.assertIn("first-init", topics)
        self.assertIn("skeleton-created", topics)
        # Both skeletons should be flagged once for empty + skeleton-created
        skel_created = sum(1 for a in d["advisories"] if a["topic"] == "skeleton-created")
        self.assertEqual(skel_created, 2)

    def test_files_have_marker_after_create(self) -> None:
        run(self.base_args())
        for name in ("TROUBLESHOOTING.md", "GLOSSARY.md"):
            content = (self.proj / name).read_text(encoding="utf-8")
            self.assertIn(SKELETON_MARKER, content)

    def test_idempotent_second_run(self) -> None:
        run(self.base_args())
        d = run(self.base_args())
        for name in ("TROUBLESHOOTING.md", "GLOSSARY.md"):
            f = d["project_files"][name]
            self.assertTrue(f["exists"])
            self.assertFalse(f["created_now"])
            self.assertTrue(f["is_empty_skeleton"])
        topics = [a["topic"] for a in d["advisories"]]
        self.assertIn("empty-skeleton", topics)
        self.assertNotIn("skeleton-created", topics)

    def test_no_create_dry_run(self) -> None:
        d = run(self.base_args() + ["--no-create"])
        self.assertFalse(d["project_files"]["TROUBLESHOOTING.md"]["exists"])
        self.assertFalse((self.proj / "TROUBLESHOOTING.md").exists())


class TestFilledFiles(_Base):
    def test_empty_skeleton_false_after_marker_removal(self) -> None:
        run(self.base_args())
        # 用户填充：删 marker 行
        f = self.proj / "TROUBLESHOOTING.md"
        text = f.read_text(encoding="utf-8")
        new_text = "\n".join(
            line for line in text.splitlines()
            if SKELETON_MARKER not in line
        )
        f.write_text(new_text, encoding="utf-8")
        d = run(self.base_args())
        self.assertFalse(d["project_files"]["TROUBLESHOOTING.md"]["is_empty_skeleton"])
        # 不再触发 empty-skeleton advisory（仅 GLOSSARY.md 还是空骨架）
        empty_topics = [a for a in d["advisories"]
                        if a["topic"] == "empty-skeleton"
                        and "TROUBLESHOOTING" in a["message"]]
        self.assertEqual(empty_topics, [])


class TestVersionCache(_Base):
    def test_version_match(self) -> None:
        (self.proj / ".teamwork_localconfig.md").write_text(
            "teamwork_version: v7.3.10+P0-129\n", encoding="utf-8"
        )
        d = run(self.base_args())
        self.assertTrue(d["version_match"])
        self.assertEqual(d["local_version"], "v7.3.10+P0-129")
        topics = [a["topic"] for a in d["advisories"]]
        self.assertNotIn("version-mismatch", topics)

    def test_version_mismatch_advisory(self) -> None:
        (self.proj / ".teamwork_localconfig.md").write_text(
            "teamwork_version: v7.3.10+P0-100\n", encoding="utf-8"
        )
        d = run(self.base_args())
        self.assertFalse(d["version_match"])
        topics = [a["topic"] for a in d["advisories"]]
        self.assertIn("version-mismatch", topics)


class TestProjectRoot(_Base):
    def test_git_root_takes_priority(self) -> None:
        sub = self.proj / "deep" / "nested"
        sub.mkdir(parents=True)
        d = run([
            "--cwd", str(sub),
            "--host", "claude-code",
            "--skill-root", str(SKILL),
            "--skill-version", "v7.3.10+P0-129",
        ])
        self.assertEqual(d["project_root_source"], "git")
        # project_root 解析到 git root（不是 sub）
        self.assertTrue(str(self.proj.resolve()) in d["project_root"]
                        or str(d["project_root"]) in str(self.proj.resolve()))


class TestSchemaDocs(_Base):
    def test_schema_docs_found(self) -> None:
        (self.proj / "services" / "core" / "docs" / "architecture").mkdir(parents=True)
        (self.proj / "services" / "core" / "docs" / "architecture" / "database-schema.md").write_text("x")
        d = run(self.base_args())
        docs = d["global_schema_docs"]["docs"]
        self.assertGreaterEqual(len(docs), 1)
        self.assertTrue(any("database-schema" in p for p in docs))
        topics = [a["topic"] for a in d["advisories"]]
        self.assertIn("schema-docs-found", topics)


class TestAuditLine(_Base):
    def test_audit_line_present(self) -> None:
        d = run(self.base_args())
        self.assertIn("audit_line", d)
        line = d["audit_line"]
        self.assertTrue(line.startswith("📊 init_triage:"))
        self.assertIn("verdict=OK", line)
        self.assertIn("host=claude-code", line)

    def test_audit_line_aggregates_skeleton_created(self) -> None:
        d = run(self.base_args())
        line = d["audit_line"]
        self.assertIn("已创建=", line)

    def test_audit_line_no_advisories_when_clean(self) -> None:
        # 用户已填 TROUBLESHOOTING.md / GLOSSARY.md / version match
        for name in ("TROUBLESHOOTING.md", "GLOSSARY.md"):
            (self.proj / name).write_text("# real content\n", encoding="utf-8")
        (self.proj / ".teamwork_localconfig.md").write_text(
            "teamwork_version: v7.3.10+P0-129\n", encoding="utf-8"
        )
        (self.proj / "teamwork_space.md").write_text("# real\n", encoding="utf-8")
        d = run(self.base_args())
        line = d["audit_line"]
        self.assertNotIn("已创建=", line)
        self.assertNotIn("空骨架=", line)
        self.assertNotIn("version-mismatch", line)


class TestErrorHandling(_Base):
    def test_invalid_skill_root(self) -> None:
        r = subprocess.run(
            [sys.executable, str(INIT),
             "--cwd", str(self.proj),
             "--host", "claude-code",
             "--skill-root", "/nonexistent/path/123",
             "--skill-version", "v"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 2)

    def test_invalid_host_enum(self) -> None:
        r = subprocess.run(
            [sys.executable, str(INIT),
             "--cwd", str(self.proj),
             "--host", "hax-cli",
             "--skill-root", str(SKILL),
             "--skill-version", "v"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
