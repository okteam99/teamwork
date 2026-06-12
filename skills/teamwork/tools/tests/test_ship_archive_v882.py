#!/usr/bin/env python3
"""v8.82 ship2 归档本体(archive_on_ship)回归套件。

过程层 feature 目录交付后 zip 进 features/_archive/<id>.zip(+ INDEX.md)· 原目录从
merge_target 删 · 随收尾 MR 合(防 AI 检索过时 feature 信息 · 代码是唯一真相)。

覆盖:
- _read_archive_on_ship:localconfig 默认 true / 显式 false / 非法 → true
- _build_archive_zip:打包 + 可解 + arcname=<dir>/<rel>
- _archive_repo_paths:repo 相对路径推导
- 集成(subprocess ship-finalize · bare origin):
  - 首跑暂存归档收尾分支(zip + INDEX 在 · feature 目录从分支删)+ PENDING(archived=True)
  - 收尾 zip 含终态 state.json(current_stage=completed)
  - 全周期:暂存 → 模拟合并 → 重跑交付 + 本地 feature 目录清除 + zip 落地 + 幂等 3rd-run
  - archive_on_ship=false → 退回 v8.80(无 zip · 目录留存)

运行:python3 -m pytest skills/teamwork/tools/tests/test_ship_archive_v882.py -v
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
STATE_PY = TOOLS / "state.py"
sys.path.insert(0, str(TOOLS))


def _git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=True, text=True, timeout=20)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _git_blob(cwd, ref_path):
    """读 git 对象二进制(zip blob)· 返 (rc, bytes)。"""
    r = subprocess.run(["git", "cat-file", "blob", ref_path], cwd=str(cwd),
                       capture_output=True, timeout=20)
    return r.returncode, r.stdout


# ─── 单元:_read_archive_on_ship ────────────────────────────────────


class TestReadArchiveOnShip(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="arch-cfg-"))
        _git(self.tmp, "init", "-b", "main")  # .git 边界
        self.feat = self.tmp / "docs" / "features" / "F1"
        self.feat.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _read(self):
        from _v8_ship import _read_archive_on_ship  # type: ignore
        return _read_archive_on_ship(str(self.feat))

    def test_default_true_when_no_config(self):
        self.assertTrue(self._read())

    def test_explicit_false(self):
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"archive_on_ship": False}), encoding="utf-8")
        self.assertFalse(self._read())

    def test_explicit_true(self):
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"archive_on_ship": True}), encoding="utf-8")
        self.assertTrue(self._read())

    def test_malformed_json_defaults_true(self):
        (self.tmp / ".teamwork_localconfig.json").write_text(
            "{not json", encoding="utf-8")
        self.assertTrue(self._read())

    def test_non_bool_defaults_true(self):
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"archive_on_ship": "yes"}), encoding="utf-8")
        self.assertTrue(self._read())


# ─── 单元:_build_archive_zip ───────────────────────────────────────


class TestBuildArchiveZip(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="arch-zip-"))
        self.feat = self.tmp / "PTR-F700"
        (self.feat / "goal").mkdir(parents=True)
        (self.feat / "state.json").write_text('{"x":1}', encoding="utf-8")
        (self.feat / "goal" / "goal.md").write_text("# goal", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_zip_roundtrip_with_dir_prefix(self):
        from _v8_ship import _build_archive_zip  # type: ignore
        data = _build_archive_zip(self.feat)
        self.assertTrue(data)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = set(zf.namelist())
            self.assertIn("PTR-F700/state.json", names)
            self.assertIn("PTR-F700/goal/goal.md", names)
            self.assertEqual(zf.read("PTR-F700/state.json").decode(), '{"x":1}')

    def test_zip_deterministic(self):
        from _v8_ship import _build_archive_zip  # type: ignore
        self.assertEqual(_build_archive_zip(self.feat), _build_archive_zip(self.feat))


# ─── 单元:_archive_repo_paths ──────────────────────────────────────


class TestArchiveRepoPaths(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="arch-paths-"))
        _git(self.tmp, "init", "-b", "main")
        self.feat = self.tmp / "svc" / "docs" / "features" / "SVC-F260601"
        self.feat.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_paths(self):
        from _v8_ship import _archive_repo_paths  # type: ignore
        paths = _archive_repo_paths(str(self.tmp), self.feat, "SVC-F260601")
        self.assertIsNotNone(paths)
        feature_rel, zip_rel, index_rel = paths
        self.assertEqual(feature_rel, "svc/docs/features/SVC-F260601")
        self.assertEqual(zip_rel, "svc/docs/features/_archive/SVC-F260601.zip")
        self.assertEqual(index_rel, "svc/docs/features/_archive/INDEX.md")

    def test_paths_when_feature_dir_deleted(self):
        """feature 目录已删(3rd-run)· 用 features 根算 prefix 仍可推导。"""
        from _v8_ship import _archive_repo_paths  # type: ignore
        shutil.rmtree(self.feat)  # 目录已删 · 父(features 根)仍在
        paths = _archive_repo_paths(str(self.tmp), self.feat, "SVC-F260601")
        self.assertIsNotNone(paths)
        self.assertEqual(paths[1], "svc/docs/features/_archive/SVC-F260601.zip")


# ─── 集成:ship-finalize 归档(默认 archive_on_ship=true)──────────────


# ─── 集成测试已迁移 ───────────────────────────────────────────────
# v8.145 ship 重构:旧 finalize-deliver 双 MR 链路删除 · 新流程(ship1 archive
# in-worktree + ship2 零内容清场)集成覆盖 → test_ship_v8145_flow.py


if __name__ == "__main__":
    unittest.main(verbosity=2)
