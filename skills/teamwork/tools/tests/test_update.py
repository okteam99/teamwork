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
            [sys.executable,
             str(UPDATE_PY), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(r.returncode, 0)
        # 应有 --channel / --no-backup / --allow-downgrade
        self.assertIn("--channel", r.stdout)
        self.assertIn("--no-backup", r.stdout)
        self.assertIn("--allow-downgrade", r.stdout)
        # --accept-overwrite 已删除(自认 deprecated no-op 的参数清理掉)
        self.assertNotIn("--accept-overwrite", r.stdout)
        # 应明确是 update.py(不是 state.py)
        self.assertIn("update.py", r.stdout)

    def test_v842_state_py_no_longer_has_update_skill(self):
        """state.py update-skill subparser 已删(v8.42 抽到 update.py)。"""
        r = subprocess.run(
            [sys.executable,
             str(STATE_PY), "update-skill", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        # update-skill 已不在 subparsers · argparse 应报 invalid choice
        self.assertNotEqual(r.returncode, 0)
        combined = (r.stdout + r.stderr).lower()
        # 报错应含 "invalid choice" 或 "update-skill"(未注册)
        self.assertTrue("invalid choice" in combined or "update-skill" in combined,
                        f"expected error mentioning invalid choice or update-skill · got:\n{r.stdout}\n{r.stderr}")


class _TarballFixture(unittest.TestCase):
    """update.py tarball 测试共享 fixture:file:// URL + 临时 tarball 模拟 GitHub download。

    远端 tarball 结构模拟 GitHub archive:teamwork-<channel>/skills/teamwork/。
    远端含 tools/update.py + bootstrap.py(与真实 tarball 一致 · 受管目录对账不误删自身)。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-v842-update-"))
        # 1. 建"远端" tarball · 模拟 GitHub archive 结构 teamwork-<channel>/skills/teamwork/
        self.remote = self.tmp / "remote-extract" / "teamwork-dev" / "skills" / "teamwork"
        remote = self.remote
        remote.mkdir(parents=True)
        (remote / "SKILL.md").write_text(
            "---\nname: teamwork\nversion: v8.99\n---\nbody updated\n", encoding="utf-8")
        (remote / "tools").mkdir()
        (remote / "tools" / "state.py").write_text("# updated state.py\n", encoding="utf-8")
        # 模拟新增文件
        (remote / "tools" / "NEW_FILE.py").write_text("# v8.99 new file\n", encoding="utf-8")
        # 真实 tarball 总含 update.py / bootstrap.py · fixture 保持一致
        shutil.copy(UPDATE_PY, remote / "tools" / "update.py")
        if BOOTSTRAP_PY.exists():
            shutil.copy(BOOTSTRAP_PY, remote / "tools" / "bootstrap.py")
        # 打 tarball(GitHub archive 结构:tarball 顶层目录是 teamwork-<branch>/)
        self.tarball = self.tmp / "remote.tar.gz"
        self._build_tarball()

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

    def _build_tarball(self):
        """(重)打远端 tarball · 测试改 self.remote 后调用可生效。"""
        if self.tarball.exists():
            self.tarball.unlink()
        with tarfile.open(self.tarball, "w:gz") as tf:
            tf.add(self.tmp / "remote-extract" / "teamwork-dev",
                   arcname="teamwork-dev")

    def _run_update(self, *extra_args) -> dict:
        """跑 update.py(skill_root = self.local_skill)· 捕 JSON。"""
        r = subprocess.run(
            [sys.executable,
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


class TestUpdatePyTarballDownload(_TarballFixture):
    """v8.42:update.py tarball download + 覆盖核心逻辑(从 test_state.py 迁移)。"""

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

    def test_accept_overwrite_flag_removed(self):
        """--accept-overwrite 已删除(自认 deprecated no-op)· argparse 直接拒绝。"""
        r = subprocess.run(
            [sys.executable,
             str(self.local_skill / "tools" / "update.py"), "--accept-overwrite"],
            capture_output=True, text=True, timeout=30, cwd=str(self.local_skill),
            env={**os.environ,
                 "TEAMWORK_SKILL_TARBALL_URL": f"file://{self.tarball}",
                 "TEAMWORK_BACKUP_ROOT": str(self.backup_root)},
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--accept-overwrite", r.stderr)

    # ── PASS path:默认 flag(不带参数)覆盖文件 ──

    def test_v842_pass_overwrites_files_and_reports_new_files(self):
        """默认(无 flag)更新 · 文件真被覆盖 · 新增文件正确上报。"""
        d = self._run_update()
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
            [sys.executable,
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


class TestManifestReconcile(_TarballFixture):
    """受管目录 manifest 对账:tarball 没有的受管目录文件 = 幽灵 · 更新时删除。

    实证背景:只覆盖不删导致安装侧积累已删工具/僵尸测试(如 _v8_migrate.py 残留)。
    """

    def test_stale_files_in_managed_dirs_removed(self):
        """target 有而 tarball 无的受管目录文件被删 + emit stale_files_removed 清单。"""
        stale_tool = self.local_skill / "tools" / "_v8_migrate.py"
        stale_tool.write_text("# 已删工具残留\n", encoding="utf-8")
        stale_test = self.local_skill / "tools" / "tests" / "test_zombie.py"
        stale_test.parent.mkdir(parents=True)
        stale_test.write_text("# 僵尸测试\n", encoding="utf-8")
        stale_stage = self.local_skill / "stages" / "ghost-stage.md"
        stale_stage.parent.mkdir(parents=True)
        stale_stage.write_text("# 幽灵 stage\n", encoding="utf-8")

        d = self._run_update()
        self.assertEqual(d["verdict"], "OK")
        self.assertFalse(stale_tool.exists())
        self.assertFalse(stale_test.exists())
        self.assertFalse(stale_stage.exists())
        self.assertEqual(d["stale_files_removed_total"], 3)
        self.assertIn("tools/_v8_migrate.py", d["stale_files_removed"])
        self.assertIn("tools/tests/test_zombie.py", d["stale_files_removed"])
        self.assertIn("stages/ghost-stage.md", d["stale_files_removed"])
        # 对账后空掉的受管子目录也被清掉(tarball 无 stages/)
        self.assertFalse((self.local_skill / "stages").exists())

    def test_audit_retro_whitelist_preserved(self):
        """docs/audit/ 与 docs/retro/ 是安装侧运行时数据 · tarball 没有也不删。"""
        audit = self.local_skill / "docs" / "audit" / "PROJ-F001-runtime.md"
        audit.parent.mkdir(parents=True)
        audit.write_text("# 运行时审计数据\n", encoding="utf-8")
        retro = self.local_skill / "docs" / "retro" / "notes.md"
        retro.parent.mkdir(parents=True)
        retro.write_text("# retro 数据\n", encoding="utf-8")
        # 对照组:docs/ 下白名单外的幽灵文件应被删
        ghost_doc = self.local_skill / "docs" / "stale-doc.md"
        ghost_doc.write_text("# 幽灵 doc\n", encoding="utf-8")

        d = self._run_update()
        self.assertEqual(d["verdict"], "OK")
        self.assertTrue(audit.exists())
        self.assertTrue(retro.exists())
        self.assertFalse(ghost_doc.exists())
        self.assertNotIn("docs/audit/PROJ-F001-runtime.md", d["stale_files_removed"])
        self.assertNotIn("docs/retro/notes.md", d["stale_files_removed"])
        self.assertIn("docs/stale-doc.md", d["stale_files_removed"])

    def test_junk_caches_removed_not_counted_as_stale(self):
        """__pycache__ / .pytest_cache / .DS_Store 顺带清理 · 不计入幽灵清单。"""
        pyc = self.local_skill / "tools" / "__pycache__" / "state.cpython-314.pyc"
        pyc.parent.mkdir(parents=True)
        pyc.write_bytes(b"\x00fakepyc")
        cachetag = self.local_skill / "tools" / ".pytest_cache" / "CACHEDIR.TAG"
        cachetag.parent.mkdir(parents=True)
        cachetag.write_text("Signature: fake\n", encoding="utf-8")
        ds = self.local_skill / "tools" / ".DS_Store"
        ds.write_bytes(b"\x00\x01")

        d = self._run_update()
        self.assertEqual(d["verdict"], "OK")
        self.assertFalse(pyc.exists())
        self.assertFalse(pyc.parent.exists())  # 清空后的 __pycache__ 目录也清掉
        self.assertFalse(cachetag.exists())
        self.assertFalse(ds.exists())
        # ≥3:update.py 运行时 import bootstrap 也会顺带生成真实 __pycache__ · 一并清掉
        self.assertGreaterEqual(d["junk_removed_total"], 3)
        self.assertEqual(d["stale_files_removed_total"], 0)

    def test_root_scatter_and_unmanaged_dirs_untouched(self):
        """根目录散文件 / 未受管目录(用户自定义)不参与对账 · 不删。"""
        user_note = self.local_skill / "my-notes.md"
        user_note.write_text("# 用户根目录笔记\n", encoding="utf-8")
        custom = self.local_skill / "custom-dir" / "keep.txt"
        custom.parent.mkdir(parents=True)
        custom.write_text("用户自定义目录\n", encoding="utf-8")

        d = self._run_update()
        self.assertEqual(d["verdict"], "OK")
        self.assertTrue(user_note.exists())
        self.assertTrue(custom.exists())
        self.assertEqual(d["stale_files_removed_total"], 0)


class TestDowngradeGuard(_TarballFixture):
    """降级防护:目标版本低于本地 → FAIL · --allow-downgrade 显式放行。"""

    def test_downgrade_blocked_without_flag(self):
        (self.local_skill / "SKILL.md").write_text(
            "---\nname: teamwork\nversion: v9.50\n---\nnewer body\n", encoding="utf-8")
        d = self._run_update()
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("降级", d["error"])
        self.assertIn("--allow-downgrade", d["hint"])
        # 未覆盖:本地仍是 v9.50
        self.assertIn("version: v9.50",
                      (self.local_skill / "SKILL.md").read_text(encoding="utf-8"))
        # 降级防护在 backup 之前拦截 · 不产生 backup
        if self.backup_root.exists():
            self.assertEqual(list(self.backup_root.iterdir()), [])

    def test_downgrade_allowed_with_flag(self):
        (self.local_skill / "SKILL.md").write_text(
            "---\nname: teamwork\nversion: v9.50\n---\nnewer body\n", encoding="utf-8")
        d = self._run_update("--allow-downgrade")
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["old_version"], "v9.50")
        self.assertEqual(d["new_version"], "v8.99")
        self.assertIn("version: v8.99",
                      (self.local_skill / "SKILL.md").read_text(encoding="utf-8"))

    def test_same_version_not_treated_as_downgrade(self):
        (self.local_skill / "SKILL.md").write_text(
            "---\nname: teamwork\nversion: v8.99\n---\nbody updated\n", encoding="utf-8")
        d = self._run_update()
        self.assertEqual(d["verdict"], "OK")
        self.assertFalse(d["version_changed"])


class TestBackupPrune(_TarballFixture):
    """backup 保留策略:成功更新后 backup 根目录只留最近 10 份。"""

    def test_prune_keeps_latest_10(self):
        self.backup_root.mkdir(parents=True)
        for i in range(12):
            fake = self.backup_root / f"20200101T0000{i:02d}Z"
            fake.mkdir()
            (fake / "SKILL.md").write_text(f"fake backup {i}\n", encoding="utf-8")

        d = self._run_update()
        self.assertEqual(d["verdict"], "OK")
        # 12 份旧 + 本次新建 1 份 = 13 → 保留 10 · prune 3
        self.assertEqual(d["backups_pruned"], 3)
        remaining = sorted(p.name for p in self.backup_root.iterdir() if p.is_dir())
        self.assertEqual(len(remaining), 10)
        # 最老 3 份被清 · 本次新 backup 保留
        self.assertNotIn("20200101T000000Z", remaining)
        self.assertNotIn("20200101T000001Z", remaining)
        self.assertNotIn("20200101T000002Z", remaining)
        self.assertIn(Path(d["backup_path"]).name, remaining)

    def test_no_prune_when_under_limit(self):
        d = self._run_update()
        self.assertEqual(d["verdict"], "OK")
        self.assertEqual(d["backups_pruned"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
