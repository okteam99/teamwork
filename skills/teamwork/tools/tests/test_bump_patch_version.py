#!/usr/bin/env python3
"""v8.44.1:tools/bump_patch_version.py 单测(用户拍板 dev push auto-bump)。

设计:
- 测纯函数 bump_patch(text) → (new_text, old_v, new_v)
- 测 main(argv) e2e:文件读写 / 错误码
- 独立小脚本 · 不依赖 state.py / bootstrap.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
BUMP_PY = TOOLS / "bump_patch_version.py"
sys.path.insert(0, str(TOOLS))


class TestBumpPatchFunction(unittest.TestCase):
    """v8.44.1:bump_patch 纯函数 · 不动文件。"""

    def test_v8441_no_patch_adds_dot_1(self):
        """v8.44(无 patch 段)→ v8.44.1。"""
        from bump_patch_version import bump_patch  # type: ignore
        new, old_v, new_v = bump_patch("---\nname: x\nversion: v8.44\n---\nbody\n")
        self.assertEqual(old_v, "v8.44")
        self.assertEqual(new_v, "v8.44.1")
        self.assertIn("version: v8.44.1", new)
        self.assertNotIn("version: v8.44\n", new)

    def test_v8441_with_patch_increments(self):
        """v8.44.1 → v8.44.2 → v8.44.3 ...(patch 段 +1)。"""
        from bump_patch_version import bump_patch  # type: ignore
        _, _, v2 = bump_patch("---\nversion: v8.44.1\n---\n")
        self.assertEqual(v2, "v8.44.2")
        _, _, v3 = bump_patch("---\nversion: v8.44.99\n---\n")
        self.assertEqual(v3, "v8.44.100")  # 无上限

    def test_v8441_strips_v_prefix_consistently(self):
        """带 v / 不带 v · 都输出 vX.Y.Z。"""
        from bump_patch_version import bump_patch  # type: ignore
        _, _, v1 = bump_patch("---\nversion: 8.44\n---\n")  # 无 v 前缀
        self.assertEqual(v1, "v8.44.1")  # 输出始终带 v
        _, _, v2 = bump_patch("---\nversion: v8.44\n---\n")
        self.assertEqual(v2, "v8.44.1")

    def test_v8441_raises_when_no_version(self):
        """frontmatter 无 version 字段 → ValueError。"""
        from bump_patch_version import bump_patch  # type: ignore
        with self.assertRaises(ValueError):
            bump_patch("---\nname: teamwork\n---\nbody\n")

    def test_v8441_preserves_other_frontmatter_fields(self):
        """name / description 等其他 frontmatter 字段不动 · 只动 version 行。"""
        from bump_patch_version import bump_patch  # type: ignore
        text = (
            "---\n"
            "name: teamwork\n"
            "version: v8.44\n"
            "description: AI 协作开发一体化框架\n"
            "---\n"
            "body line 1\n"
            "body line 2\n"
        )
        new, _, _ = bump_patch(text)
        # 其他字段保留
        self.assertIn("name: teamwork", new)
        self.assertIn("description: AI 协作开发一体化框架", new)
        self.assertIn("body line 1", new)
        self.assertIn("body line 2", new)
        # version 更新
        self.assertIn("version: v8.44.1", new)


class TestBumpPatchE2E(unittest.TestCase):
    """v8.44.1:main(argv) e2e · 真读写文件 + subprocess 跑独立脚本。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-bump-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, args):
        import subprocess
        return subprocess.run(
            [sys.executable,
             str(BUMP_PY), *args],
            capture_output=True, text=True, timeout=10,
        )

    def test_v8441_bumps_file_in_place(self):
        """跑脚本 → 文件 version 字段被更新。"""
        skill = self.tmp / "SKILL.md"
        skill.write_text("---\nname: teamwork\nversion: v8.44\n---\nbody\n",
                          encoding="utf-8")
        r = self._run([str(skill)])
        self.assertEqual(r.returncode, 0)
        self.assertIn("v8.44 → v8.44.1", r.stdout)
        self.assertIn("version: v8.44.1", skill.read_text(encoding="utf-8"))

    def test_v8441_idempotent_each_run_bumps(self):
        """每次跑都 bump · idempotent 由调用方[hook]控制(本工具不重复检测)。"""
        skill = self.tmp / "SKILL.md"
        skill.write_text("---\nversion: v8.44\n---\n", encoding="utf-8")
        self._run([str(skill)])
        self._run([str(skill)])
        self._run([str(skill)])
        self.assertIn("version: v8.44.3", skill.read_text(encoding="utf-8"))

    def test_v8441_exit_2_when_no_frontmatter(self):
        """无 frontmatter → exit 2 · stderr 含 FAIL。"""
        skill = self.tmp / "SKILL.md"
        skill.write_text("no frontmatter here\n", encoding="utf-8")
        r = self._run([str(skill)])
        self.assertEqual(r.returncode, 2)
        self.assertIn("FAIL", r.stderr)

    def test_v8441_exit_2_when_no_version_field(self):
        """frontmatter 无 version 字段 → exit 2。"""
        skill = self.tmp / "SKILL.md"
        skill.write_text("---\nname: teamwork\n---\nbody\n", encoding="utf-8")
        r = self._run([str(skill)])
        self.assertEqual(r.returncode, 2)
        self.assertIn("version", r.stderr)

    def test_v8441_exit_2_when_file_missing(self):
        """文件不存在 → exit 2。"""
        r = self._run([str(self.tmp / "nonexistent.md")])
        self.assertEqual(r.returncode, 2)
        self.assertIn("不存在", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
