#!/usr/bin/env python3
"""v8.145 ship 重构回归套件(用户拍板架构)。

ship1 全交付(worktree 内 · sanitize → archive → push · 终点 = feature MR 提交):
归档 zip + 规划翻牌 + 终态 state.json 全随 feature MR 原子合入 · 无第二收尾 MR。
ship2(ship-finalize)零内容清场:verify-delivered → 删 worktree → 净化主工作区。

覆盖:
- ship1 archive:planning gate PENDING / --no-planning-changes 归档 commit(zip+INDEX
  在 HEAD · 目录从分支删 · 工作树保留接力卡)/ 翻牌文件随归档 commit / desc 门禁 /
  幂等重跑 / zip 内终态 state.json
- ship2:MR 未合 PENDING(绝不删 worktree)/ 合并后 PASS(worktree 删 · 主工作区
  pull 到 zip 终态 · 从未物化过程目录)/ 副产物自动 commit+push / 用户改动决策面板 /
  幂等(接力卡消亡 → zip-on-origin noop)

运行:python3 -m pytest skills/teamwork/tools/tests/test_ship_v8145_flow.py -v
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


def _run_state(cwd, *args, timeout=40):
    r = subprocess.run([sys.executable, str(STATE_PY), *args],
                       cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    assert "Traceback" not in r.stderr, r.stderr[:600]
    d = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
    return r, d


class _ShipFlowBase(unittest.TestCase):
    """bare origin + 主工作区 clone + feature worktree(分支上已有 feature 目录)。"""

    FID = "INFRA-M945-newship"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ship-v8145-"))
        self.bare = self.tmp / "origin.git"
        self.bare.mkdir()
        _git(self.bare, "init", "--bare", "-b", "main")
        self.main = self.tmp / "main-repo"
        self.main.mkdir()
        _git(self.main, "init", "-b", "main")
        _git(self.main, "config", "user.email", "t@x.com")
        _git(self.main, "config", "user.name", "t")
        _git(self.main, "remote", "add", "origin", str(self.bare))
        (self.main / "AGENTS.md").write_text("<!-- ptr v1 -->\n", encoding="utf-8")
        (self.main / "README.md").write_text("# repo\n", encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-m", "init")
        _git(self.main, "push", "origin", "main")
        _git(self.main, "branch", "--set-upstream-to=origin/main", "main")

        # feature worktree(分支 feat/x 自 main)
        self.branch = "feat/newship"
        self.wt = self.tmp / "wt"
        _git(self.main, "worktree", "add", "-b", self.branch, str(self.wt), "main")
        _git(self.wt, "config", "user.email", "t@x.com")
        _git(self.wt, "config", "user.name", "t")
        self.feat_rel = f"docs/features/{self.FID}"
        self.zip_rel = f"docs/features/_archive/{self.FID}.zip"
        self.index_rel = "docs/features/_archive/INDEX.md"
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
                          ("TEAMWORK_BYPASS_MAIN_WORKTREE", "TEAMWORK_BYPASS_CHECKSUM")}
        os.environ["TEAMWORK_BYPASS_MAIN_WORKTREE"] = "1"
        os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"

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

    def _finalize(self):
        return _run_state(self.main, "ship-finalize", "--feature", self.feature_arg)

    def _push_branch(self):
        rc, _, err = _git(self.wt, "push", "origin", self.branch)
        self.assertEqual(rc, 0, err)

    def _merge_mr(self):
        """模拟用户平台合并 feature MR(ff 推 branch tip 到 main)。"""
        rc, head, _ = _git(self.wt, "rev-parse", "HEAD")
        self.assertEqual(rc, 0)
        rc, _, err = _git(self.wt, "push", "origin", f"{head}:main")
        self.assertEqual(rc, 0, f"模拟合并失败:{err}")


class TestShip1Archive(_ShipFlowBase):
    def test_planning_gate_pending_without_flag(self):
        _, d = self._archive()
        self.assertEqual(d.get("verdict"), "PENDING", d)
        self.assertEqual(d.get("pending_step"), "planning-backref")
        self.assertIn("worktree", d.get("next_action", ""))

    def test_archive_commits_zip_removes_dir_keeps_handoff(self):
        _, d = self._archive("--no-planning-changes", "--archive-desc", "极简描述")
        self.assertEqual(d.get("verdict"), "PASS", d)
        self.assertEqual(d.get("phase"), "archived")
        # 分支树:zip + INDEX 在 · 过程目录无
        rc, _, _ = _git(self.wt, "cat-file", "-e", f"HEAD:{self.zip_rel}")
        self.assertEqual(rc, 0, "zip 应在 HEAD")
        rc, _, _ = _git(self.wt, "cat-file", "-e", f"HEAD:{self.index_rel}")
        self.assertEqual(rc, 0, "INDEX.md 应在 HEAD")
        rc, _, _ = _git(self.wt, "cat-file", "-e", f"HEAD:{self.feat_rel}/state.json")
        self.assertNotEqual(rc, 0, "过程目录应从分支删除")
        # 工作树:接力卡保留(untracked)
        self.assertTrue((self.wt / self.feat_rel / "state.json").exists(),
                        "工作树 state.json = ship2 接力卡 · 必须保留")
        disk = json.loads((self.wt / self.feat_rel / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(disk["ship"]["phase"], "archived")
        self.assertEqual(disk["current_stage"], "completed")
        # zip 内终态
        rc, out, _ = _git(self.wt, "rev-parse", f"HEAD:{self.zip_rel}")
        self.assertEqual(rc, 0)
        raw = subprocess.run(["git", "cat-file", "blob", out], cwd=str(self.wt),
                             capture_output=True, timeout=20).stdout
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            inner = json.loads(zf.read(f"{self.FID}/state.json").decode())
            self.assertEqual(inner["current_stage"], "completed")
            self.assertIn(f"{self.FID}/goal/PRD.md", zf.namelist())
        # INDEX 行含描述
        rc, content, _ = _git(self.wt, "show", f"HEAD:{self.index_rel}")
        self.assertIn(self.FID, content)
        self.assertIn("极简描述", content)

    def test_planning_artifacts_bundled_in_same_commit(self):
        roadmap = self.wt / "ROADMAP.md"
        roadmap.write_text(f"- {self.FID} ✅ 已交付\n", encoding="utf-8")
        _, d = self._archive("--planning-artifacts", "ROADMAP.md",
                             "--archive-desc", "x")
        self.assertEqual(d.get("verdict"), "PASS", d)
        self.assertEqual(d.get("planning_bundled"), ["ROADMAP.md"])
        rc, content, _ = _git(self.wt, "show", "HEAD:ROADMAP.md")
        self.assertEqual(rc, 0)
        self.assertIn("已交付", content, "翻牌随归档 commit 原子进分支")

    def test_nonexistent_planning_artifact_fails(self):
        _, d = self._archive("--planning-artifacts", "NOPE.md")
        self.assertEqual(d.get("verdict"), "FAIL", d)
        self.assertIn("不存在", d.get("error", ""))

    def test_desc_over_200_fails_with_compress_hint(self):
        _, d = self._archive("--no-planning-changes", "--archive-desc", "长" * 201)
        self.assertEqual(d.get("verdict"), "FAIL", d)
        self.assertIn("200", d.get("error", ""))

    def test_archive_idempotent_rerun(self):
        _, d1 = self._archive("--no-planning-changes")
        self.assertEqual(d1.get("verdict"), "PASS", d1)
        _, d2 = self._archive("--no-planning-changes")
        self.assertEqual(d2.get("verdict"), "PASS", d2)
        self.assertTrue(d2.get("already_archived"), d2)

    def test_push_action_requires_archived(self):
        _, d = _run_state(self.wt, "ship-phase", "--action", "push",
                          "--feature", self.feature_arg,
                          "--feature-head-commit", "x", "--git-host", "github",
                          "--mr-creation-method", "cli-gh", "--mr-url", "http://x")
        self.assertEqual(d.get("verdict"), "FAIL", d)
        self.assertIn("archive", d.get("hint", "") + d.get("error", ""))


class TestShip2Finalize(_ShipFlowBase):
    def _ship1(self):
        _, d = self._archive("--no-planning-changes", "--archive-desc", "x")
        self.assertEqual(d.get("verdict"), "PASS", d)
        self._push_branch()

    def test_pending_before_merge_keeps_worktree(self):
        self._ship1()
        _, d = self._finalize()
        self.assertEqual(d.get("verdict"), "PENDING", d)
        self.assertEqual(d.get("pending_step"), "verify-delivered")
        self.assertTrue(self.wt.exists(), "🔴 MR 未合并 · worktree 绝不可删")

    def test_pass_after_merge_full_cleanup(self):
        self._ship1()
        self._merge_mr()
        _, d = self._finalize()
        self.assertEqual(d.get("verdict"), "PASS", d)
        for step in ("verify-delivered", "worktree-remove", "main-sync"):
            self.assertIn(step, d.get("completed_steps", []), d)
        self.assertTrue(d.get("worktree_removed"), d)
        self.assertFalse(self.wt.exists(), "worktree 应被删除(接力卡随之消亡)")
        # 主工作区:pull 到 zip 终态 · 过程目录从未物化
        self.assertTrue((self.main / self.zip_rel).exists(), "主工作区应 pull 到归档 zip")
        self.assertFalse((self.main / self.feat_rel).exists(),
                         "主工作区从未物化过程目录(新架构核心收益)")
        # 幂等重跑(接力卡已消亡 → zip-on-origin noop)
        _, d2 = self._finalize()
        self.assertEqual(d2.get("verdict"), "PASS", d2)
        self.assertTrue(d2.get("idempotent"), d2)

    def test_byproduct_autocommit_and_push(self):
        self._ship1()
        self._merge_mr()
        # 主工作区注入块脏(bootstrap_pointers)
        (self.main / "AGENTS.md").write_text("<!-- ptr v2 -->\n", encoding="utf-8")
        _, d = self._finalize()
        self.assertEqual(d.get("verdict"), "PASS", d)
        self.assertIn("byproduct_commit", d, d)
        rc, out, _ = _git(self.main, "status", "--porcelain")
        self.assertNotIn("AGENTS.md", out, "副产物应已自动 commit(用户拍板)")
        self.assertEqual(d.get("main_sync_status"), "cleaned_pulled_pushed", d)
        # 已推 origin
        rc, content, _ = _git(self.main, "show", "origin/main:AGENTS.md")
        self.assertIn("v2", content, "副产物 commit 应已 push")

    def test_user_dirt_surfaces_decision_panel(self):
        self._ship1()
        self._merge_mr()
        (self.main / "notes.txt").write_text("user wip\n", encoding="utf-8")
        _git(self.main, "add", "notes.txt")  # 让其入 tracked? 不 · untracked 即 other_files
        _, _, _ = _git(self.main, "reset", "notes.txt")
        _, d = self._finalize()
        self.assertEqual(d.get("verdict"), "PASS", d)
        self.assertEqual(d.get("main_sync_status"), "user_dirty_decision", d)
        dec = d.get("main_sync_decision", {})
        self.assertTrue(dec, d)
        # v8.145:决策命令不依赖 --feature(接力卡此刻已消亡)
        for opt in dec.get("options", []):
            self.assertIn("--merge-target", opt["command"])
            self.assertNotIn("--feature", opt["command"])
        self.assertTrue(self.main.joinpath("notes.txt").exists(), "用户改动不被自动动")


class TestMainSyncFeatureless(unittest.TestCase):
    """v8.145:main-sync 不依赖 feature(接力卡可已消亡)。"""

    def test_strategy_skip_without_feature(self):
        tmp = Path(tempfile.mkdtemp(prefix="ms-nofeat-"))
        try:
            bare = tmp / "o.git"; bare.mkdir()
            _git(bare, "init", "--bare", "-b", "main")
            repo = tmp / "r"; repo.mkdir()
            _git(repo, "init", "-b", "main")
            _git(repo, "config", "user.email", "t@x.com")
            _git(repo, "config", "user.name", "t")
            _git(repo, "remote", "add", "origin", str(bare))
            (repo / "a.md").write_text("x\n", encoding="utf-8")
            _git(repo, "add", "-A"); _git(repo, "commit", "-m", "init")
            _git(repo, "push", "origin", "main")
            os.environ["TEAMWORK_BYPASS_MAIN_WORKTREE"] = "1"
            _, d = _run_state(repo, "main-sync", "--strategy", "skip")
            self.assertEqual(d.get("verdict"), "PASS", d)
            self.assertEqual(d.get("merge_target"), "main")  # 从当前分支推导
        finally:
            os.environ.pop("TEAMWORK_BYPASS_MAIN_WORKTREE", None)
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
