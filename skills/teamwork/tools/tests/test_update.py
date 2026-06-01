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
        # v8.44.3:也 override TEAMWORK_BACKUP_ROOT 到 tmp · 不污染 ~/.teamwork/backups
        self._prev_env_url = os.environ.get("TEAMWORK_SKILL_TARBALL_URL")
        self._prev_env_backup = os.environ.get("TEAMWORK_BACKUP_ROOT")
        os.environ["TEAMWORK_SKILL_TARBALL_URL"] = f"file://{self.tarball}"
        self.backup_root = self.tmp / "backups"
        os.environ["TEAMWORK_BACKUP_ROOT"] = str(self.backup_root)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self._prev_env_url is None:
            os.environ.pop("TEAMWORK_SKILL_TARBALL_URL", None)
        else:
            os.environ["TEAMWORK_SKILL_TARBALL_URL"] = self._prev_env_url
        if self._prev_env_backup is None:
            os.environ.pop("TEAMWORK_BACKUP_ROOT", None)
        else:
            os.environ["TEAMWORK_BACKUP_ROOT"] = self._prev_env_backup

    def _run_update(self, *extra_args) -> dict:
        """跑 update.py(skill_root = self.local_skill)· 捕 JSON。"""
        r = subprocess.run(
            ["/opt/homebrew/opt/python@3.14/bin/python3.14",
             str(self.local_skill / "tools" / "update.py"), *extra_args],
            capture_output=True, text=True, timeout=30, cwd=str(self.local_skill),
            env={**os.environ,
                 "TEAMWORK_SKILL_TARBALL_URL": f"file://{self.tarball}",
                 "TEAMWORK_BACKUP_ROOT": str(self.backup_root)},
        )
        out = (r.stdout or r.stderr).strip()
        idx = out.find("{")
        self.assertGreaterEqual(idx, 0,
                                f"未找到 JSON · stdout/stderr=\n{out}")
        return json.loads(out[idx:])

    # ── v8.44.3:默认 backup + overwrite(治本 v8.41 BLOCK 二次问用户)──

    def test_v8443_default_backup_and_overwrite_succeeds(self):
        """v8.44.3:有本地改动 + 不带任何 flag · 默认 backup + overwrite · PASS 一步走。

        治本 v8.41 设计:之前 BLOCK 必须 --accept-overwrite · case 暴露用户被迫做 2 次决策。
        v8.44.3 默认 backup 兜底 · 直接 overwrite · 用户不知道 backup 也安全。
        """
        d = self._run_update()  # 不带任何 flag
        self.assertEqual(d["verdict"], "OK", f"应默认成功 · 实际 emit:\n{json.dumps(d, ensure_ascii=False, indent=2)}")
        self.assertEqual(d["command"], "update")
        self.assertEqual(d["old_version"], "v8.41")
        self.assertEqual(d["new_version"], "v8.99")
        # 文件真被覆盖
        skill_md = self.local_skill / "SKILL.md"
        self.assertIn("version: v8.99", skill_md.read_text(encoding="utf-8"))
        # backup 真创建
        self.assertIsNotNone(d["backup_path"])
        self.assertGreater(d["backup_file_count"], 0)
        backup_path = Path(d["backup_path"])
        self.assertTrue(backup_path.exists())
        self.assertTrue(backup_path.is_dir())
        # backup 含原 SKILL.md(v8.41 版本)
        backup_skill = backup_path / "SKILL.md"
        self.assertTrue(backup_skill.exists())
        self.assertIn("version: v8.41", backup_skill.read_text(encoding="utf-8"))

    def test_v8443_backup_path_in_teamwork_backups_dir(self):
        """v8.44.3:backup 路径在 TEAMWORK_BACKUP_ROOT(默认 ~/.teamwork/backups/<ts>/)。"""
        d = self._run_update()
        backup_path = Path(d["backup_path"])
        # backup 在 self.backup_root(env override)下
        self.assertTrue(str(backup_path).startswith(str(self.backup_root)),
                        f"backup 路径应在 {self.backup_root}/ 下 · 实际 {backup_path}")
        # 路径名是 timestamp 格式(20260528T143022Z)
        name = backup_path.name
        self.assertRegex(name, r"^\d{8}T\d{6}Z(-\d+)?$",
                          f"backup 目录名应为 ISO timestamp 紧凑格式 · 实际 {name}")

    def test_v8443_no_backup_flag_skips_backup(self):
        """v8.44.3:--no-backup 跳 backup · 仍 overwrite · emit backup_skip_reason。"""
        d = self._run_update("--no-backup")
        self.assertEqual(d["verdict"], "OK")
        self.assertIsNone(d["backup_path"])
        self.assertEqual(d["backup_file_count"], 0)
        self.assertIn("--no-backup", d["backup_skip_reason"])
        # 文件仍被覆盖
        skill_md = self.local_skill / "SKILL.md"
        self.assertIn("version: v8.99", skill_md.read_text(encoding="utf-8"))
        # backup 目录不存在(因为 skip 了)
        if self.backup_root.exists():
            self.assertEqual(list(self.backup_root.iterdir()), [],
                             "backup_root 应为空 · 因为 --no-backup")

    def test_v8443_accept_overwrite_deprecated_no_op(self):
        """v8.44.3:--accept-overwrite 仍接受但 no-op + emit deprecation_warning(向后兼容)。"""
        d = self._run_update("--accept-overwrite")
        self.assertEqual(d["verdict"], "OK")
        # 仍默认 backup
        self.assertIsNotNone(d["backup_path"])
        # deprecation warning 显式提示
        self.assertIn("deprecation_warning", d)
        self.assertIn("deprecated", d["deprecation_warning"].lower())
        self.assertIn("v8.44.3", d["deprecation_warning"])

    # ── v8.42:原有 PASS path 测试调整(仍传 --accept-overwrite 兼容) ──

    def test_v842_pass_with_accept_overwrite_and_overwrites_files(self):
        """v8.42→v8.44.3:--accept-overwrite 仍接受 · 文件真被覆盖。"""
        d = self._run_update("--accept-overwrite")
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["command"], "update")
        self.assertEqual(d["old_version"], "v8.41")
        self.assertEqual(d["new_version"], "v8.99")
        self.assertTrue(d["version_changed"])
        self.assertGreaterEqual(d["modified_overwritten_total"], 1)
        skill_md = self.local_skill / "SKILL.md"
        self.assertIn("version: v8.99", skill_md.read_text(encoding="utf-8"))
        new_file = self.local_skill / "tools" / "NEW_FILE.py"
        self.assertTrue(new_file.exists())
        self.assertGreaterEqual(d["new_files_added_total"], 1)
        self.assertIn("tools/NEW_FILE.py", d["new_files_added"])
        # v8.44.3:emit 字段从 timestamp 改名 · 但保留 timestamp 字段(now_ts_compact)
        self.assertIn("timestamp", d)

    # ── BLOCK path:tarball 下载失败(保留 · 不受 v8.44.3 影响) ──

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
        d = self._run_update("--channel", "dev")  # v8.44.3 不需 --accept-overwrite
        self.assertEqual(d["channel"], "dev")
        self.assertEqual(d["channel_source"], "args")

    def test_v842_default_channel_main(self):
        """无 --channel + 无 localconfig → channel=main · channel_source=default。"""
        d = self._run_update()
        self.assertEqual(d["channel"], "main")
        self.assertEqual(d["channel_source"], "default")


if __name__ == "__main__":
    unittest.main(verbosity=2)
