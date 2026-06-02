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


class TestArchiveOnShipV882(unittest.TestCase):
    FID = "INFRA-M888-archive"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ship-archive-v882-"))
        self.bare = self.tmp / "origin.git"
        self.bare.mkdir()
        _git(self.bare, "init", "--bare", "-b", "main")
        self.main = self.tmp / "main-repo"
        self.main.mkdir()
        _git(self.main, "init", "-b", "main")
        _git(self.main, "config", "user.email", "test@x.com")
        _git(self.main, "config", "user.name", "test")
        _git(self.main, "remote", "add", "origin", str(self.bare))
        self.feat_rel = f"infra/docs/features/{self.FID}"
        self.zip_rel = f"infra/docs/features/_archive/{self.FID}.zip"
        self.index_rel = "infra/docs/features/_archive/INDEX.md"
        feat_dir = self.main / self.feat_rel
        (feat_dir / "goal").mkdir(parents=True)
        state = {
            "feature_id": self.FID,
            "flow_type": "Micro",
            "current_stage": "ship",   # step 4 → completed(进 zip 的终态)
            "merge_target": "main",
            "worktree": {"strategy": "off"},   # 跳过 worktree-remove
            "ship": {
                "phase": "merged", "shipped": "merged",
                "feature_head_commit": "deadbeef", "merge_commit_hash": "cafebabe",
            },
            "stage_contracts": {},
            "completed_stages": ["goal", "dev", "review", "test", "pm_acceptance"],
            "concerns": [],
        }
        (feat_dir / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        (feat_dir / "goal" / "goal.md").write_text("# 目标", encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-m", "init feature")
        _git(self.main, "push", "origin", "main")
        self.feature_arg = str(feat_dir)
        self._prev_env = {
            "TEAMWORK_BYPASS_MAIN_WORKTREE": os.environ.get("TEAMWORK_BYPASS_MAIN_WORKTREE"),
            "TEAMWORK_BYPASS_CHECKSUM": os.environ.get("TEAMWORK_BYPASS_CHECKSUM"),
        }
        os.environ["TEAMWORK_BYPASS_MAIN_WORKTREE"] = "1"
        os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k, v in self._prev_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _finalize(self):
        prev = os.getcwd()
        os.chdir(str(self.main))
        try:
            r = subprocess.run(
                [sys.executable, str(STATE_PY), "ship-finalize",
                 "--feature", self.feature_arg],
                capture_output=True, text=True, timeout=40)
            self.assertNotIn("NameError", r.stderr, r.stderr[:400])
            self.assertNotIn("Traceback", r.stderr, r.stderr[:400])
            d = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
            return r, d
        finally:
            os.chdir(prev)

    def _sf_branch(self):
        return f"ship-finalize/{self.FID}"

    def test_first_run_stages_archive_branch(self):
        _, d = self._finalize()
        self.assertEqual(d.get("verdict"), "PENDING", d)
        self.assertEqual(d.get("pending_step"), "finalize-deliver")
        self.assertTrue(d["finalize_mr"]["archived"], d)
        self.assertEqual(d["finalize_mr"]["branch"], self._sf_branch())
        # 收尾分支推到 origin
        _git(self.main, "fetch", "origin", self._sf_branch())
        ref = f"origin/{self._sf_branch()}"
        # zip + INDEX 在收尾分支 · feature 目录从分支删
        rc_zip, _, _ = _git(self.main, "cat-file", "-e", f"{ref}:{self.zip_rel}")
        self.assertEqual(rc_zip, 0, "归档 zip 应在收尾分支")
        rc_idx, _, _ = _git(self.main, "cat-file", "-e", f"{ref}:{self.index_rel}")
        self.assertEqual(rc_idx, 0, "INDEX.md 应在收尾分支")
        rc_state, _, _ = _git(self.main, "cat-file", "-e", f"{ref}:{self.feat_rel}/state.json")
        self.assertNotEqual(rc_state, 0, "feature 目录应从收尾分支删除(已归档进 zip)")

    def test_index_md_has_feature_row(self):
        self._finalize()
        _git(self.main, "fetch", "origin", self._sf_branch())
        rc, content, _ = _git(self.main, "show",
                              f"origin/{self._sf_branch()}:{self.index_rel}")
        self.assertEqual(rc, 0)
        self.assertIn(self.FID, content)
        self.assertIn(f"`{self.FID}.zip`", content)

    def test_zip_contains_terminal_state(self):
        self._finalize()
        _git(self.main, "fetch", "origin", self._sf_branch())
        rc, raw = _git_blob(self.main, f"origin/{self._sf_branch()}:{self.zip_rel}")
        self.assertEqual(rc, 0)
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            inner = json.loads(zf.read(f"{self.FID}/state.json").decode())
            self.assertEqual(inner["current_stage"], "completed",
                             "归档 zip 内 state.json 应为终态 completed")
            self.assertIn(f"{self.FID}/goal/goal.md", zf.namelist())

    def test_full_cycle_archives_and_purges(self):
        _, d1 = self._finalize()
        self.assertEqual(d1.get("verdict"), "PENDING", d1)
        sf_commit = d1["finalize_mr"]["head_commit"]
        # 模拟收尾 MR 合并:ff origin/main 到归档 commit(父 = origin/main)
        rc, _, err = _git(self.main, "push", "origin", f"{sf_commit}:main")
        self.assertEqual(rc, 0, f"模拟合并失败:{err}")
        # 重跑:检测 zip 已在 merge_target → 交付 + 清本地 feature 目录 + ff-pull
        _, d2 = self._finalize()
        self.assertEqual(d2.get("verdict"), "PASS", d2)
        self.assertTrue(d2.get("archived"), d2)
        self.assertIn("main_sync_status", d2)
        merged = d2.get("completed_steps", []) + d2.get("skipped_steps", [])
        self.assertIn("finalize-deliver", merged)
        # 本地主工作区:feature 目录已删 · zip 已落地
        self.assertFalse((self.main / self.feat_rel).exists(),
                         "本地 feature 目录应被清除(已归档)")
        self.assertTrue((self.main / self.zip_rel).exists(),
                        "本地应已 ff-pull 到归档 zip")
        # origin/main:zip 在 · feature 目录无
        rc_z, _, _ = _git(self.main, "cat-file", "-e", f"origin/main:{self.zip_rel}")
        self.assertEqual(rc_z, 0)
        rc_s, _, _ = _git(self.main, "cat-file", "-e", f"origin/main:{self.feat_rel}/state.json")
        self.assertNotEqual(rc_s, 0)
        # 幂等 3rd-run:feature 目录已不在 · 检测已归档 → 幂等 PASS
        _, d3 = self._finalize()
        self.assertEqual(d3.get("verdict"), "PASS", d3)
        self.assertTrue(d3.get("idempotent"), d3)
        self.assertEqual(d3.get("archive"), self.zip_rel)


# ─── 集成:archive_on_ship=false 退回 v8.80 ──────────────────────────


class TestArchiveOffFallbackV882(unittest.TestCase):
    FID = "INFRA-M777-noarch"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ship-noarch-v882-"))
        self.bare = self.tmp / "origin.git"
        self.bare.mkdir()
        _git(self.bare, "init", "--bare", "-b", "main")
        self.main = self.tmp / "main-repo"
        self.main.mkdir()
        _git(self.main, "init", "-b", "main")
        _git(self.main, "config", "user.email", "test@x.com")
        _git(self.main, "config", "user.name", "test")
        _git(self.main, "remote", "add", "origin", str(self.bare))
        self.feat_rel = f"infra/docs/features/{self.FID}"
        self.zip_rel = f"infra/docs/features/_archive/{self.FID}.zip"
        feat_dir = self.main / self.feat_rel
        feat_dir.mkdir(parents=True)
        state = {
            "feature_id": self.FID, "flow_type": "Micro",
            "current_stage": "ship", "merge_target": "main",
            "worktree": {"strategy": "off"},
            "ship": {"phase": "merged", "shipped": "merged",
                     "feature_head_commit": "deadbeef", "merge_commit_hash": "cafebabe"},
            "stage_contracts": {},
            "completed_stages": ["goal", "dev", "review", "test", "pm_acceptance"],
            "concerns": [],
        }
        (feat_dir / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        # 关键:archive_on_ship=false → 退回 v8.80(同步 state.json 终态 · 不归档)
        (self.main / ".teamwork_localconfig.json").write_text(
            json.dumps({"archive_on_ship": False}), encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-m", "init feature")
        _git(self.main, "push", "origin", "main")
        self.feature_arg = str(feat_dir)
        self._prev_env = {
            "TEAMWORK_BYPASS_MAIN_WORKTREE": os.environ.get("TEAMWORK_BYPASS_MAIN_WORKTREE"),
            "TEAMWORK_BYPASS_CHECKSUM": os.environ.get("TEAMWORK_BYPASS_CHECKSUM"),
        }
        os.environ["TEAMWORK_BYPASS_MAIN_WORKTREE"] = "1"
        os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k, v in self._prev_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _finalize(self):
        prev = os.getcwd()
        os.chdir(str(self.main))
        try:
            r = subprocess.run(
                [sys.executable, str(STATE_PY), "ship-finalize",
                 "--feature", self.feature_arg],
                capture_output=True, text=True, timeout=40)
            d = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
            return r, d
        finally:
            os.chdir(prev)

    def test_fallback_no_archive(self):
        _, d = self._finalize()
        self.assertEqual(d.get("verdict"), "PENDING", d)
        self.assertFalse(d["finalize_mr"]["archived"], "archive_on_ship=false → 不归档")
        sf = f"ship-finalize/{self.FID}"
        _git(self.main, "fetch", "origin", sf)
        # v8.80 行为:收尾分支同步 state.json · 无 zip · feature 目录仍在
        rc_z, _, _ = _git(self.main, "cat-file", "-e", f"origin/{sf}:{self.zip_rel}")
        self.assertNotEqual(rc_z, 0, "archive off → 收尾分支不应有 zip")
        rc_s, _, _ = _git(self.main, "cat-file", "-e", f"origin/{sf}:{self.feat_rel}/state.json")
        self.assertEqual(rc_s, 0, "archive off → feature 目录(state.json)仍在收尾分支")


if __name__ == "__main__":
    unittest.main(verbosity=2)
