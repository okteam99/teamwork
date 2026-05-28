#!/usr/bin/env python3
"""v8.42:tools/update.py 独立脚本测试(从 test_state.py:TestUpdateSkillTarballDownload 迁移)。

设计:
- update.py 抽离自 state.py:cmd_update_skill(v8.41 实现 · v8.42 抽离)
- 测试用 file:// URL + 临时 tarball 模拟 GitHub download · 避免真网络
- 验证 update.py 独立可跑(不依赖 state.py argparse)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SKILL = TOOLS.parent
UPDATE_PY = TOOLS / "update.py"
STATE_PY = TOOLS / "state.py"
BOOTSTRAP_PY = TOOLS / "bootstrap.py"
sys.path.insert(0, str(TOOLS))


class TestUpdatePyStandalone(unittest.TestCase):
    """v8.42:update.py 是独立 python 脚本(治本元工具混运行时)。

    用户拍板 2026-05-27:"更新文件本身是否有必要单独一个 python"
    """

    def test_v842_update_py_exists(self):
        """tools/update.py 存在(v8.42 创建)。"""
        self.assertTrue(UPDATE_PY.exists(), f"update.py 应存在:{UPDATE_PY}")

    def test_v842_update_py_runs_help_independently(self):
        """update.py --help 独立可跑(不依赖 state.py argparse)。"""
        r = subprocess.run(
            ["/opt/homebrew/opt/python@3.14/bin/python3.14",
             str(UPDATE_PY), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(r.returncode, 0)
        # 应有 --channel 和 --accept-overwrite
        self.assertIn("--channel", r.stdout)
        self.assertIn("--accept-overwrite", r.stdout)
        # 应明确是 update.py(不是 state.py)
        self.assertIn("update.py", r.stdout)

    def test_v842_state_py_no_longer_has_update_skill(self):
        """state.py update-skill subparser 已删(v8.42 抽到 update.py)。"""
        r = subprocess.run(
            ["/opt/homebrew/opt/python@3.14/bin/python3.14",
             str(STATE_PY), "update-skill", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        # update-skill 已不在 subparsers · argparse 应报 invalid choice
        self.assertNotEqual(r.returncode, 0)
        combined = (r.stdout + r.stderr).lower()
        # 报错应含 "invalid choice" 或 "update-skill"(未注册)
        self.assertTrue("invalid choice" in combined or "update-skill" in combined,
                        f"expected error mentioning invalid choice or update-skill · got:\n{r.stdout}\n{r.stderr}")


class TestUpdatePyTarballDownload(unittest.TestCase):
    """v8.42:update.py tarball download + 覆盖核心逻辑(从 test_state.py 迁移)。

    用 file:// URL + 临时 tarball 模拟 GitHub download · 避免真网络。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-v842-update-"))
        # 1. 建"远端" tarball · 模拟 GitHub archive 结构 teamwork-<channel>/skills/teamwork/
        remote = self.tmp / "remote-extract" / "teamwork-dev" / "skills" / "teamwork"
        remote.mkdir(parents=True)
        (remote / "SKILL.md").write_text(
            "---\nname: teamwork\nversion: v8.99\n---\nbody updated\n", encoding="utf-8")
        (remote / "tools").mkdir()
        (remote / "tools" / "state.py").write_text("# updated state.py\n", encoding="utf-8")
        # 模拟新增文件
        (remote / "tools" / "NEW_FILE.py").write_text("# v8.99 new file\n", encoding="utf-8")
        # 打 tarball(GitHub archive 结构:tarball 顶层目录是 teamwork-<branch>/)
        self.tarball = self.tmp / "remote.tar.gz"
        with tarfile.open(self.tarball, "w:gz") as tf:
            tf.add(self.tmp / "remote-extract" / "teamwork-dev",
                   arcname="teamwork-dev")

        # 2. 建"本地" skill_root(模拟用户已安装的 skill · v8.41)
        self.local_skill = self.tmp / "local-skill"
        self.local_skill.mkdir()
        # 拷真 update.py 让 update 能跑(自推 skill_root)
        (self.local_skill / "tools").mkdir()
        shutil.copy(UPDATE_PY, self.local_skill / "tools" / "update.py")
        # 拷 bootstrap.py(_read_update_channel 用)
        if BOOTSTRAP_PY.exists():
            shutil.copy(BOOTSTRAP_PY, self.local_skill / "tools" / "bootstrap.py")
        # SKILL.md 本地 v8.41
        (self.local_skill / "SKILL.md").write_text(
            "---\nname: teamwork\nversion: v8.41\n---\noriginal body\n",
            encoding="utf-8")

        # 3. env override TEAMWORK_SKILL_TARBALL_URL → file:// 本地 tarball
        self._prev_env = os.environ.get("TEAMWORK_SKILL_TARBALL_URL")
        os.environ["TEAMWORK_SKILL_TARBALL_URL"] = f"file://{self.tarball}"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev_env is None:
            os.environ.pop("TEAMWORK_SKILL_TARBALL_URL", None)
        else:
            os.environ["TEAMWORK_SKILL_TARBALL_URL"] = self._prev_env

    def _run_update(self, *extra_args) -> dict:
        """跑 update.py(skill_root = self.local_skill)· 捕 JSON。"""
        r = subprocess.run(
            ["/opt/homebrew/opt/python@3.14/bin/python3.14",
             str(self.local_skill / "tools" / "update.py"), *extra_args],
            capture_output=True, text=True, timeout=30, cwd=str(self.local_skill),
            env={**os.environ, "TEAMWORK_SKILL_TARBALL_URL": f"file://{self.tarball}"},
        )
        out = (r.stdout or r.stderr).strip()
        idx = out.find("{")
        self.assertGreaterEqual(idx, 0,
                                f"未找到 JSON · stdout/stderr=\n{out}")
        return json.loads(out[idx:])

    # ── BLOCK path:本地有改动 + 无 --accept-overwrite ──

    def test_v842_block_when_local_modified_without_accept(self):
        """本地有改动(SKILL.md v8.41 ≠ 远端 v8.99) + 无 --accept-overwrite → BLOCK。"""
        d = self._run_update()
        self.assertEqual(d["verdict"], "FAIL")
        self.assertEqual(d["command"], "update")
        self.assertIn("本地有改动", d["error"])
        self.assertIn("SKILL.md", str(d["modified_files"]))
        self.assertGreaterEqual(d["modified_files_total"], 1)
        # hint 含逃生口
        self.assertIn("--accept-overwrite", d["hint"])
        self.assertIn("backup", d["hint"])
        # hint 提到 update.py(不是 state.py update-skill)
        self.assertIn("update.py", d["hint"])
        self.assertNotIn("state.py update-skill", d["hint"])
        # 仍 emit old/new version
        self.assertEqual(d["old_version"], "v8.41")
        self.assertEqual(d["new_version"], "v8.99")

    # ── PASS path:--accept-overwrite 通过 + 文件被覆盖 ──

    def test_v842_pass_with_accept_overwrite_and_overwrites_files(self):
        """有本地改动 + --accept-overwrite → PASS + 文件真被覆盖。"""
        d = self._run_update("--accept-overwrite")
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["command"], "update")
        self.assertEqual(d["old_version"], "v8.41")
        self.assertEqual(d["new_version"], "v8.99")
        self.assertTrue(d["version_changed"])
        self.assertGreaterEqual(d["modified_overwritten_total"], 1)
        # 文件真被覆盖
        skill_md = self.local_skill / "SKILL.md"
        self.assertIn("version: v8.99", skill_md.read_text(encoding="utf-8"))
        # 新文件也被添加(NEW_FILE.py · 远端有本地没)
        new_file = self.local_skill / "tools" / "NEW_FILE.py"
        self.assertTrue(new_file.exists())
        # new_files_added_total ≥ 1(NEW_FILE.py · 可能含其他 setUp 拷过去但远端没的文件)
        self.assertGreaterEqual(d["new_files_added_total"], 1)
        self.assertIn("tools/NEW_FILE.py", d["new_files_added"])
        # 含 timestamp(update.py 独立 emit)
        self.assertIn("timestamp", d)

    # ── BLOCK path:tarball 下载失败 ──

    def test_v842_block_when_tarball_url_invalid(self):
        """URL 指向不存在 file:// → curl 失败 → BLOCK with hint。"""
        r = subprocess.run(
            ["/opt/homebrew/opt/python@3.14/bin/python3.14",
             str(self.local_skill / "tools" / "update.py")],
            capture_output=True, text=True, timeout=30, cwd=str(self.local_skill),
            env={**os.environ,
                 "TEAMWORK_SKILL_TARBALL_URL": "file:///tmp/nonexistent-v842.tar.gz"},
        )
        out = (r.stdout or r.stderr).strip()
        idx = out.find("{")
        d = json.loads(out[idx:])
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("下载", d["error"])

    # ── channel 参数 ──

    def test_v842_channel_passed_through_to_emit(self):
        """--channel dev → emit channel=dev · channel_source=args。"""
        d = self._run_update("--accept-overwrite", "--channel", "dev")
        self.assertEqual(d["channel"], "dev")
        self.assertEqual(d["channel_source"], "args")

    def test_v842_default_channel_main(self):
        """无 --channel + 无 localconfig → channel=main · channel_source=default。"""
        d = self._run_update("--accept-overwrite")
        self.assertEqual(d["channel"], "main")
        self.assertEqual(d["channel_source"], "default")


if __name__ == "__main__":
    unittest.main(verbosity=2)
