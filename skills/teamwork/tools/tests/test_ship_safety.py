#!/usr/bin/env python3
"""ship 链路安全回归套件(_v8_ship.py)。

覆盖(按模块行为 · 非版本):
- stash 回收:`git stash show` 失败(rc≠0)不可证冗余 → 保留;rc==0 且 diff 空才算真空;
  --drop-stashes 全清排除本次 main-sync 策略新建的备份(快照外的不 drop)
- ship-finalize worktree-remove:接力卡之外仍有 dirty/untracked → PENDING 不删(--force 会连带销毁)
- ship1 archive:归档 commit 失败 → 磁盘 state.json 不留 completed/archived 终态(回滚 · 可重入);
  zip/INDEX 写盘 OSError → FAIL JSON(不裸 traceback)+ 回滚
- ship1 push:phase=pushed 重跑 = 幂等重录(覆盖 mr_url/head · concerns WARN 留痕)
- archive 同步:本地未提交改动挡住 merge(git 拒启动 · 非冲突)→ local-dirty PENDING 对症指引
- INDEX 冲突自动解:本 feature 行存在性按首列单元格精确匹配(防 F001 命中 F0012 子串)

运行:python3 -m pytest skills/teamwork/tools/tests/test_ship_safety.py -q
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
STATE_PY = TOOLS / "state.py"
sys.path.insert(0, str(TOOLS))

import _v8_ship  # noqa: E402
from _v8_ship import (  # noqa: E402
    _GitResult,
    _index_has_row,
    _reclaim_stashes,
    _stash_hashes,
)


def _git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=True, text=True, timeout=20)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _run_state(cwd, *args, timeout=60):
    r = subprocess.run([sys.executable, str(STATE_PY), *args],
                       cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    assert "Traceback" not in r.stderr, r.stderr[:600]
    d = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
    return r, d


# ─── stash 回收安全 ────────────────────────────────────────────────


class _StashRepoBase(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="ship-safety-stash-"))
        _git(self.repo, "init", "-q", "-b", "main")
        _git(self.repo, "config", "user.email", "t@t")
        _git(self.repo, "config", "user.name", "t")
        (self.repo / "f.txt").write_text("base\n")
        _git(self.repo, "add", "f.txt")
        _git(self.repo, "commit", "-qm", "init")

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def _tw_stash(self, tag):
        """建一个含未合内容的 teamwork main-sync stash(新文件 · 反向 apply 必失败 = 非冗余)。"""
        (self.repo / f"{tag}.txt").write_text("live\n")
        _git(self.repo, "stash", "push", "-q", "-u", "-m",
             f"teamwork main-sync stash · ship 后 · {tag}")

    def _redundant_tw_stash(self, tag):
        """内容已在分支的 teamwork stash(反向 apply 通过 = 可证冗余)。"""
        (self.repo / "f.txt").write_text(f"changed-{tag}\n")
        _git(self.repo, "stash", "push", "-q", "-u", "-m",
             f"teamwork main-sync stash · ship 后 · {tag}")
        (self.repo / "f.txt").write_text(f"changed-{tag}\n")
        _git(self.repo, "add", "f.txt")
        _git(self.repo, "commit", "-qm", f"apply {tag}")

    def _stash_list(self):
        return _git(self.repo, "stash", "list")[1]


class TestReclaimStashShowFailure(_StashRepoBase):
    def _fake_git(self, fail_rc):
        orig = _v8_ship._git

        def fake(args, cwd=None, timeout=60, env=None):
            if list(args[:2]) == ["stash", "show"]:
                return _GitResult(fail_rc, "", "simulated failure")
            return orig(args, cwd=cwd, timeout=timeout, env=env)
        return fake

    def test_show_failure_never_drops(self):
        """stash show rc≠0(timeout/老 git)→ 不可证冗余 → 保留(空 stdout 不得误判真空)。"""
        self._redundant_tw_stash("RED1")   # 正常路径下会被 drop 的冗余 stash
        with mock.patch.object(_v8_ship, "_git", self._fake_git(124)):
            r = _reclaim_stashes(str(self.repo))
        self.assertEqual(r["dropped"], 0, r)
        self.assertIn("RED1", self._stash_list())

    def test_rc0_empty_diff_still_drops(self):
        """rc==0 且 diff 空 = 真空 stash → 仍安全 drop(守住原有回收能力)。"""
        self._tw_stash("LIVE1")            # 正常路径下会被保留的非冗余 stash
        fake = self._fake_git(0)           # rc=0 + 空 stdout → 真空
        with mock.patch.object(_v8_ship, "_git", fake):
            r = _reclaim_stashes(str(self.repo))
        self.assertEqual(r["dropped"], 1, r)


class TestDropAllExcludesNew(_StashRepoBase):
    def test_drop_all_excludes_stash_created_after_snapshot(self):
        """快照后新建的 stash(= 本次策略备份)· drop_all 也不碰 · 输出注明排除数。"""
        self._tw_stash("OLD1")
        snap = _stash_hashes(str(self.repo))
        self._tw_stash("NEW1")             # 模拟 stash-pull 策略刚建的备份
        r = _reclaim_stashes(str(self.repo), drop_all=True, preexisting=snap)
        self.assertEqual(r["dropped"], 1, r)
        self.assertEqual(r.get("excluded_new"), 1, r)
        self.assertIn("排除本次新建 1 个", r.get("dropped_reason", ""), r)
        listing = self._stash_list()
        self.assertIn("NEW1", listing, "本次新建备份必须保留")
        self.assertNotIn("OLD1", listing, "快照内旧 stash 应被全清")

    def test_drop_all_without_snapshot_keeps_old_behavior(self):
        """preexisting=None(直接调用)→ 全清 teamwork stash(兼容既有语义)。"""
        self._tw_stash("A")
        self._tw_stash("B")
        r = _reclaim_stashes(str(self.repo), drop_all=True)
        self.assertEqual(r["dropped"], 2, r)
        self.assertEqual(r["remaining_count"], 0, r)


class TestMainSyncDropStashesIntegration(unittest.TestCase):
    """state.py main-sync --strategy stash-pull --drop-stashes:刚建的备份不能被一起清。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ship-safety-ms-"))
        self.bare = self.tmp / "o.git"
        self.bare.mkdir()
        _git(self.bare, "init", "--bare", "-b", "main")
        self.repo = self.tmp / "r"
        self.repo.mkdir()
        _git(self.repo, "init", "-b", "main")
        _git(self.repo, "config", "user.email", "t@x.com")
        _git(self.repo, "config", "user.name", "t")
        _git(self.repo, "remote", "add", "origin", str(self.bare))
        (self.repo / "a.md").write_text("x\n", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-m", "init")
        _git(self.repo, "push", "origin", "main")
        os.environ["TEAMWORK_BYPASS_MAIN_WORKTREE"] = "1"

    def tearDown(self):
        os.environ.pop("TEAMWORK_BYPASS_MAIN_WORKTREE", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fresh_backup_survives_drop_stashes(self):
        # 旧 teamwork stash(含未合内容)
        (self.repo / "old_wip.txt").write_text("old\n")
        _git(self.repo, "stash", "push", "-q", "-u", "-m",
             "teamwork main-sync stash · ship 后 · OLDF")
        # 用户脏文件 → stash-pull 策略会为它新建备份 stash
        (self.repo / "user_wip.txt").write_text("wip\n")
        _, d = _run_state(self.repo, "main-sync", "--strategy", "stash-pull",
                          "--drop-stashes")
        self.assertEqual(d.get("verdict"), "PASS", d)
        rec = d.get("stash_reclaim", {})
        self.assertEqual(rec.get("dropped"), 1, d)
        self.assertEqual(rec.get("excluded_new"), 1, d)
        listing = _git(self.repo, "stash", "list")[1]
        self.assertNotIn("OLDF", listing, "旧 stash 应被全清")
        self.assertIn("teamwork main-sync stash", listing,
                      "本次 stash-pull 刚建的备份必须幸存")
        # 备份内容可恢复(用户改动没丢)
        rc, _, err = _git(self.repo, "stash", "pop")
        self.assertEqual(rc, 0, err)
        self.assertTrue((self.repo / "user_wip.txt").exists())


# ─── ship1/ship2 流程安全(bare origin + 主工作区 + feature worktree)──


class _ShipFlowBase(unittest.TestCase):
    """精简版 ship 流程 fixture(与 test_ship_v8145_flow 同构 · 本套件自含)。"""

    FID = "INFRA-M001-safety"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ship-safety-flow-"))
        self.bare = self.tmp / "origin.git"
        self.bare.mkdir()
        _git(self.bare, "init", "--bare", "-b", "main")
        self.main = self.tmp / "main-repo"
        self.main.mkdir()
        _git(self.main, "init", "-b", "main")
        _git(self.main, "config", "user.email", "t@x.com")
        _git(self.main, "config", "user.name", "t")
        _git(self.main, "remote", "add", "origin", str(self.bare))
        (self.main / "README.md").write_text("# repo\n", encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-m", "init")
        _git(self.main, "push", "origin", "main")

        self.branch = "feat/safety"
        self.wt = self.tmp / "wt"
        _git(self.main, "worktree", "add", "-b", self.branch, str(self.wt), "main")
        _git(self.wt, "config", "user.email", "t@x.com")
        _git(self.wt, "config", "user.name", "t")
        self.feat_rel = f"docs/features/{self.FID}"
        self.zip_rel = f"docs/features/_archive/{self.FID}.zip"
        feat_dir = self.wt / self.feat_rel
        (feat_dir / "goal").mkdir(parents=True)
        (feat_dir / "goal" / "PRD.md").write_text("# PRD\n", encoding="utf-8")
        self.state = {
            "feature_id": self.FID,
            "flow_type": "Micro",
            "current_stage": "ship",
            "merge_target": "main",
            "worktree": {"strategy": "branch",
                         "path": os.path.relpath(self.wt, self.main),
                         "branch": self.branch},
            "ship": {},
            "stage_contracts": {},
            "completed_stages": ["goal", "dev", "review", "test", "pm_acceptance"],
            "concerns": [],
        }
        self._write_state()
        _git(self.wt, "add", "-A")
        _git(self.wt, "commit", "-m", "feature work")
        self.feature_arg = str(feat_dir)
        self._prev_env = {k: os.environ.get(k) for k in
                          ("TEAMWORK_BYPASS_MAIN_WORKTREE", "TEAMWORK_BYPASS_CHECKSUM",
                           "TEAMWORK_AUDIT_DIR")}
        os.environ["TEAMWORK_BYPASS_MAIN_WORKTREE"] = "1"
        os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"
        os.environ["TEAMWORK_AUDIT_DIR"] = str(self.tmp / "audit-inbox")

    def _write_state(self):
        (self.wt / self.feat_rel / "state.json").write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k, v in self._prev_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # helpers
    def _archive(self, *extra):
        return _run_state(self.wt, "ship-phase", "--action", "archive",
                          "--feature", self.feature_arg, *extra)

    def _push_record(self, mr_url, head="h1"):
        return _run_state(self.wt, "ship-phase", "--action", "push",
                          "--feature", self.feature_arg,
                          "--feature-head-commit", head, "--git-host", "github",
                          "--mr-creation-method", "cli-gh", "--mr-url", mr_url)

    def _finalize(self):
        return _run_state(self.main, "ship-finalize", "--feature", self.feature_arg)

    def _disk_state(self):
        return json.loads((self.wt / self.feat_rel / "state.json")
                          .read_text(encoding="utf-8"))

    def _origin_commit(self, files: dict, msg: str):
        """借第二个 clone 给 origin/main 推一笔(模拟并行改动已合)。"""
        b = self.tmp / "sideclone"
        if not b.exists():
            _git(self.tmp, "clone", "-q", str(self.bare), str(b))
            _git(b, "config", "user.email", "t@x.com")
            _git(b, "config", "user.name", "t")
        _git(b, "pull", "-q", "--ff-only", "origin", "main")
        for rel, content in files.items():
            fp = b / rel
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
        _git(b, "add", "-A")
        _git(b, "commit", "-qm", msg)
        rc, _, err = _git(b, "push", "origin", "main")
        assert rc == 0, err

    def _ship1_and_merge(self):
        _, d = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d.get("verdict"), "PASS", d)
        rc, _, err = _git(self.wt, "push", "origin", self.branch)
        self.assertEqual(rc, 0, err)
        rc, head, _ = _git(self.wt, "rev-parse", "HEAD")
        self.assertEqual(rc, 0)
        rc, _, err = _git(self.wt, "push", "origin", f"{head}:main")
        self.assertEqual(rc, 0, err)


class TestArchiveCommitFailureRollback(_ShipFlowBase):
    def _install_failing_hook(self):
        hooks = self.tmp / "hooks"
        hooks.mkdir()
        h = hooks / "pre-commit"
        h.write_text("#!/bin/sh\nexit 1\n")
        h.chmod(0o755)
        _git(self.wt, "config", "core.hooksPath", str(hooks))

    def test_commit_failure_leaves_no_terminal_state(self):
        """归档 commit 失败 → 磁盘 state.json 保持原状态(不留 completed/archived 假象)。"""
        self._install_failing_hook()
        r, d = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d.get("verdict"), "FAIL", d)
        self.assertIn("归档 commit 失败", d.get("error", ""), d)
        disk = self._disk_state()
        self.assertEqual(disk["current_stage"], "ship", "磁盘不得停留在 completed")
        self.assertIsNone(disk.get("ship", {}).get("phase"), "phase 不得残留 archived")
        self.assertNotIn("ship", disk.get("completed_stages", []))
        # 修复后重跑可重入 · 终态随 commit 成功后持久化
        _git(self.wt, "config", "--unset", "core.hooksPath")
        _, d2 = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d2.get("verdict"), "PASS", d2)
        rc, _, _ = _git(self.wt, "cat-file", "-e", f"HEAD:{self.zip_rel}")
        self.assertEqual(rc, 0, "重跑后 zip 应在 HEAD")
        disk2 = self._disk_state()
        self.assertEqual(disk2["current_stage"], "completed")
        self.assertEqual(disk2["ship"]["phase"], "archived")

    def test_zip_write_oserror_fail_json_and_rollback(self):
        """zip 写盘 OSError(_archive 位置被文件占)→ FAIL JSON(无 traceback)+ state 回滚。"""
        blocker = self.wt / "docs" / "features" / "_archive"
        blocker.write_text("not a dir\n", encoding="utf-8")   # mkdir 处必 OSError
        r, d = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d.get("verdict"), "FAIL", d)
        self.assertIn("归档产物写入失败", d.get("error", ""), d)
        disk = self._disk_state()
        self.assertEqual(disk["current_stage"], "ship")
        self.assertIsNone(disk.get("ship", {}).get("phase"))
        # 排障后重跑可重入
        blocker.unlink()
        _, d2 = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d2.get("verdict"), "PASS", d2)


class TestPushRerecord(_ShipFlowBase):
    def test_pushed_rerun_rerecords_with_warn(self):
        """phase=pushed 重跑 push = 幂等重录:覆盖 mr_url/head · concerns WARN 留痕。"""
        _, d = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d.get("verdict"), "PASS", d)
        _, d1 = self._push_record("http://mr/1", head="h1")
        self.assertEqual(d1.get("verdict"), "PASS", d1)
        _, d2 = self._push_record("http://mr/2", head="h2")
        self.assertEqual(d2.get("verdict"), "PASS", d2)
        self.assertEqual(d2.get("transition"), "pushed → pushed", d2)
        self.assertTrue(d2.get("rerecorded"), d2)
        disk = self._disk_state()
        self.assertEqual(disk["ship"]["mr_url"], "http://mr/2")
        self.assertEqual(disk["ship"]["feature_head_commit"], "h2")
        self.assertTrue(any("ship-push 重录" in c for c in disk.get("concerns", [])),
                        disk.get("concerns"))

    def test_push_from_null_still_fails(self):
        """phase=None 直接 push 仍 FAIL(重录仅放行 pushed)。"""
        _, d = self._push_record("http://mr/1")
        self.assertEqual(d.get("verdict"), "FAIL", d)
        self.assertIn("archive", d.get("hint", "") + d.get("error", ""))


class TestFinalizeWorktreeDirtyGuard(_ShipFlowBase):
    def test_stray_content_pending_not_removed(self):
        """接力卡之外的 dirty/untracked → PENDING 列清单 · 不删 worktree。"""
        self._ship1_and_merge()
        (self.wt / "STRAY.md").write_text("uncommitted note\n", encoding="utf-8")
        (self.wt / "README.md").write_text("# repo\nlocal edit\n", encoding="utf-8")
        _, d = self._finalize()
        self.assertEqual(d.get("verdict"), "PENDING", d)
        self.assertEqual(d.get("pending_step"), "worktree-remove", d)
        self.assertIn("STRAY.md", d.get("dirty_files", []), d)
        self.assertIn("README.md", d.get("dirty_files", []), d)
        self.assertTrue(self.wt.exists(), "🔴 有未处置内容 · worktree 不得删")
        # 处置后重跑 → 干净删除
        (self.wt / "STRAY.md").unlink()
        _git(self.wt, "checkout", "--", "README.md")
        _, d2 = self._finalize()
        self.assertEqual(d2.get("verdict"), "PASS", d2)
        self.assertFalse(self.wt.exists(), "干净后 worktree 应被删除")

    def test_handoff_card_only_is_clean(self):
        """只剩接力卡(feature 目录 untracked)= 预期形态 · 正常删除。"""
        self._ship1_and_merge()
        rc, out, _ = _git(self.wt, "status", "--porcelain")
        self.assertIn(self.FID, out, "前提:接力卡目录应是 untracked")
        _, d = self._finalize()
        self.assertEqual(d.get("verdict"), "PASS", d)
        self.assertFalse(self.wt.exists())


class TestArchiveLocalDirtyPending(_ShipFlowBase):
    def test_uncommitted_change_blocking_merge_gets_dedicated_pending(self):
        """本地未提交改动挡住 merge(git 拒启动 · U 列表空)→ local-dirty PENDING · 非误诊 conflict。"""
        self._origin_commit({"README.md": "# repo\norigin change\n"}, "origin readme")
        (self.wt / "README.md").write_text("# repo\nlocal uncommitted\n", encoding="utf-8")
        _, d = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d.get("verdict"), "PENDING", d)
        self.assertEqual(d.get("pending_step"), "local-dirty", d)
        self.assertIn("README.md", d.get("detail", ""), d)
        # 按指引 stash 后重跑 → 同步干净通过
        rc, _, err = _git(self.wt, "stash", "-u")
        self.assertEqual(rc, 0, err)
        _, d2 = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d2.get("verdict"), "PASS", d2)
        self.assertIn("已自动合入", d2.get("sync", ""), d2)


class TestIndexRowExactMatch(unittest.TestCase):
    def test_substring_id_not_matched(self):
        content = ("| Feature | 描述 | 交付归档时间 | 归档物 |\n"
                   "| --- | --- | --- | --- |\n"
                   "| F0012 | 别家 | 2026-01-01T00:00:00Z | `F0012.zip` |\n")
        self.assertFalse(_index_has_row(content, "F001"),
                         "F001 不得因 F0012 子串被误判已存在")
        self.assertTrue(_index_has_row(content, "F0012"))

    def test_non_table_mention_not_matched(self):
        self.assertFalse(_index_has_row("正文提到 F001 但无表格行\n", "F001"))

    def test_exact_row_matched(self):
        content = "| F001 | 本家 | 2026-01-01T00:00:00Z | `F001.zip` |\n"
        self.assertTrue(_index_has_row(content, "F001"))


if __name__ == "__main__":
    unittest.main()
