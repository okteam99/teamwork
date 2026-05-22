#!/usr/bin/env python3
"""ship-finalize step 0 state-sync 回归套件(v8.16 治本 SVC-CORE-B006 case)。

测 _step_state_sync 单元 + 通过 cmd_ship_finalize 触发的集成路径。

设计:
- _step_state_sync 是纯函数式 helper · 直接 import 单测覆盖核心逻辑
- 不跑完整 ship-finalize(需要真 worktree + remote · 集成成本高)· 单元覆盖即可

运行:
    python3 -m pytest skills/teamwork/tools/tests/test_ship_finalize_state_sync.py -v
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

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SKILL = TOOLS.parent
sys.path.insert(0, str(TOOLS))


def _git(cwd, *args):
    """跑 git · 返 (returncode, stdout, stderr)。"""
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=True, text=True, timeout=15)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _make_repo_with_worktree(tmp: Path) -> tuple[Path, Path]:
    """建主 repo + linked worktree · 返 (main_path, wt_path)。"""
    main = tmp / "main-repo"
    main.mkdir()
    _git(main, "init", "-b", "main")
    _git(main, "config", "user.email", "test@example.com")
    _git(main, "config", "user.name", "test")
    # initial commit on main
    (main / "README.md").write_text("init", encoding="utf-8")
    _git(main, "add", "README.md")
    _git(main, "commit", "-m", "init")

    # 建 linked worktree
    wt_root = tmp / "worktrees" / "feat"
    _git(main, "worktree", "add", "-b", "feat/test", str(wt_root))
    return main, wt_root


def _make_state_json(path: Path, *, feature_head_commit: str = "",
                     wt_path_rel: str = "", wt_branch: str = "feat/test",
                     merge_target: str = "main") -> dict:
    """构造 state.json · 控制 ship.feature_head_commit 是否齐全。"""
    state = {
        "feature_id": "PTR-F999-test",
        "flow_type": "Feature",
        "current_stage": "ship",
        "merge_target": merge_target,
        "worktree": {
            "strategy": "manual",
            "path": wt_path_rel,
            "branch": wt_branch,
        },
        "stage_contracts": {},
        "concerns": [],
        "ship": {},
    }
    if feature_head_commit:
        state["ship"]["feature_head_commit"] = feature_head_commit
        state["ship"]["phase"] = "pushed"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return state


class TestStepStateSync(unittest.TestCase):
    """v8.16 ship-finalize step 0 state-sync(治本 SVC-CORE-B006 case)。

    场景:
    1. 主工作区 state.json 完整 → skip(可重入)
    2. 主工作区 state.json 不存在 + worktree 内有完整态 → 复制过来
    3. 主工作区 state.json 缺 feature_head_commit + worktree 内完整 → 用 worktree 覆盖
    4. 主工作区 state.json 不存在 + worktree 也无 state.json → BLOCK
    5. worktree state.json 也不全 → BLOCK
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="state-sync-"))
        self.main, self.wt = _make_repo_with_worktree(self.tmp)
        # feature_dir 在 main 内的相对路径
        self.feat_rel = "services/svc/docs/features/PTR-F999-test"
        self.main_feat_dir = self.main / self.feat_rel
        self.wt_feat_dir = self.wt / self.feat_rel

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _call(self, feature_path):
        from _v8_ship import _step_state_sync  # type: ignore
        return _step_state_sync(str(self.main), str(feature_path))

    # ── 场景 1:主工作区 state.json 完整 · skip ──
    def test_skip_when_main_state_complete(self):
        # 主工作区 state.json 已含 feature_head_commit
        _make_state_json(
            self.main_feat_dir / "state.json",
            feature_head_commit="abc123def456",
            wt_path_rel=str(self.wt),
        )
        result = self._call(self.main_feat_dir)
        self.assertTrue(result["ok"])
        self.assertIn("main state.json 完整", result["sync_action"])

    # ── 场景 2:主工作区 state.json 不存在 + worktree 有完整 → 复制 ──
    def test_copy_from_worktree_when_main_missing(self):
        # worktree 内有完整 state.json
        _make_state_json(
            self.wt_feat_dir / "state.json",
            feature_head_commit="wtsha111222333",
            wt_path_rel=str(self.wt),
        )
        # 主工作区 feature dir 不存在
        self.assertFalse((self.main_feat_dir / "state.json").exists())
        result = self._call(self.main_feat_dir)
        self.assertTrue(result["ok"], result.get("error"))
        self.assertIn("synced state.json from worktree", result["sync_action"])
        # 验证主工作区现在有 state.json + feature_head_commit
        synced = json.loads((self.main_feat_dir / "state.json").read_text(
            encoding="utf-8"))
        self.assertEqual(synced["ship"]["feature_head_commit"], "wtsha111222333")

    # ── 场景 3:主工作区不全 + worktree 完整 → 覆盖 ──
    def test_overwrite_main_incomplete_from_worktree(self):
        """治本 SVC-CORE-B006 核心 case · case-AI 手工修复的物化版本。"""
        # 主工作区 state.json 不全(缺 feature_head_commit · 模拟合并前快照)
        _make_state_json(
            self.main_feat_dir / "state.json",
            feature_head_commit="",  # 空 · 模拟 d15dcfb7 不全快照
            wt_path_rel=str(self.wt),
        )
        # worktree 内有完整态
        _make_state_json(
            self.wt_feat_dir / "state.json",
            feature_head_commit="wtcompletehash",
            wt_path_rel=str(self.wt),
        )
        result = self._call(self.main_feat_dir)
        self.assertTrue(result["ok"], result.get("error"))
        self.assertIn("synced state.json from worktree", result["sync_action"])
        # 验证主工作区被覆盖
        synced = json.loads((self.main_feat_dir / "state.json").read_text(
            encoding="utf-8"))
        self.assertEqual(synced["ship"]["feature_head_commit"], "wtcompletehash")

    # ── 场景 4:主工作区 + worktree 都无 state.json → BLOCK ──
    def test_block_when_no_state_anywhere(self):
        result = self._call(self.main_feat_dir)
        self.assertFalse(result["ok"])
        self.assertIn("not found", result["error"])
        self.assertIn("worktree 已被手工删", result["hint"])

    # ── 场景 5:worktree state.json 也不全 → BLOCK ──
    def test_block_when_worktree_state_also_incomplete(self):
        # 主工作区不全
        _make_state_json(
            self.main_feat_dir / "state.json",
            feature_head_commit="",
            wt_path_rel=str(self.wt),
        )
        # worktree 内 state.json 也不全(没 feature_head_commit)
        _make_state_json(
            self.wt_feat_dir / "state.json",
            feature_head_commit="",
            wt_path_rel=str(self.wt),
        )
        result = self._call(self.main_feat_dir)
        self.assertFalse(result["ok"])
        self.assertIn("worktree state.json", result["error"])
        self.assertIn("Phase 1 push 未完成", result["error"])

    # ── 场景 6:worktree path 是绝对路径 ──
    def test_handles_absolute_worktree_path(self):
        # 主工作区不全 · worktree.path 用绝对路径
        _make_state_json(
            self.main_feat_dir / "state.json",
            feature_head_commit="",
            wt_path_rel=str(self.wt.resolve()),  # 绝对路径
        )
        _make_state_json(
            self.wt_feat_dir / "state.json",
            feature_head_commit="abscompletehash",
            wt_path_rel=str(self.wt.resolve()),
        )
        result = self._call(self.main_feat_dir)
        self.assertTrue(result["ok"], result.get("error"))
        synced = json.loads((self.main_feat_dir / "state.json").read_text(
            encoding="utf-8"))
        self.assertEqual(synced["ship"]["feature_head_commit"], "abscompletehash")

    # ── 场景 7:主区 state.json 读 worktree.path 失败 → 扫 git worktree list 兜底 ──
    def test_fallback_scan_git_worktree_list(self):
        """主区 state.json 不存在 → 没法读 worktree.path · 扫 git worktree list 找 worktree 内 state.json。"""
        # 主工作区 state.json 不存在(场景 2 的变种)· 关键是不能从 state 读出 wt path
        # _step_state_sync 实现已经支持:扫 git worktree list 找 candidate
        _make_state_json(
            self.wt_feat_dir / "state.json",
            feature_head_commit="scanned_hash",
            wt_path_rel="",  # state 里 wt path 空 · 强制走 scan 兜底
        )
        result = self._call(self.main_feat_dir)
        self.assertTrue(result["ok"], result.get("error"))
        synced = json.loads((self.main_feat_dir / "state.json").read_text(
            encoding="utf-8"))
        self.assertEqual(synced["ship"]["feature_head_commit"], "scanned_hash")

    # ── 场景 8:fetch 失败不致命(网络问题 · sync_action 留痕)──
    def test_fetch_fail_not_fatal_when_state_complete(self):
        """fetch 失败但 state.json 已完整 → ok=True · 只是 sync_action 记 fetch FAIL。"""
        _make_state_json(
            self.main_feat_dir / "state.json",
            feature_head_commit="completehash",
            wt_path_rel=str(self.wt),
        )
        # 这里 git fetch origin main 一定失败(local repo 无 remote)
        result = self._call(self.main_feat_dir)
        self.assertTrue(result["ok"], result.get("error"))
        # sync_action 应记 fetch FAIL(non-fatal)
        self.assertIn("fetch FAIL", result["sync_action"])


# ─── v8.18 · _finalize_push_plumbing multi-file + 去自引用(治本 SVC-CORE-F028)─


class TestFinalizePushPlumbingV818(unittest.TestCase):
    """v8.18:_finalize_push_plumbing multi-file + 不再回写自引用 finalize_commit。

    治本 SVC-CORE-F028 case:
    - 旧:plumbing 推后回写 ship.merge_target_finalize_commit = X(X 自己的 hash)→
      worktree state.json 多这字段 · 但 commit X 内不含 → 必然 delta
    - 新:不回写自引用 · 调用方预设 pushed_at/failed=false 在 commit 前 · 0 delta

    用 git fake remote 测真实 plumbing 推送(local bare 当 origin)。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="finalize-v818-"))
        # bare repo 当 fake remote
        self.bare = self.tmp / "origin.git"
        self.bare.mkdir()
        _git(self.bare, "init", "--bare", "-b", "main")
        # main repo
        self.main = self.tmp / "main-repo"
        self.main.mkdir()
        _git(self.main, "init", "-b", "main")
        _git(self.main, "config", "user.email", "test@example.com")
        _git(self.main, "config", "user.name", "test")
        _git(self.main, "remote", "add", "origin", str(self.bare))
        # initial commit with feature dir
        self.feat_rel = "services/svc/docs/features/F999-test"
        feat_dir = self.main / self.feat_rel
        feat_dir.mkdir(parents=True)
        (feat_dir / "state.json").write_text(
            json.dumps({"feature_id": "F999-test", "ship": {"phase": "pushed"}},
                       ensure_ascii=False, indent=2),
            encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-m", "init feature")
        _git(self.main, "push", "origin", "main")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _setup_ship_state(self, *, with_review_log=True):
        """模拟 ship 已 sanitize/push 后的状态(state.json 已含 ship.feature_head_commit 等)。"""
        feat_dir = self.main / self.feat_rel
        # 改 state.json 到 phase=merged 终态
        state = {
            "feature_id": "F999-test",
            "merge_target": "main",
            "ship": {
                "phase": "merged",
                "feature_head_commit": "abc123",
                "merge_commit_hash": "def456",
                # v8.18:caller 预设(在 plumbing 调用前)
                "merge_target_pushed_at": "2026-05-22T07:00:00Z",
                "merge_target_push_failed": False,
                "merge_target_push_failed_reason": None,
            },
        }
        (feat_dir / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8")
        if with_review_log:
            (feat_dir / "review-log.jsonl").write_text(
                json.dumps({"stage": "ship", "status": "completed"},
                           ensure_ascii=False) + "\n",
                encoding="utf-8")
        return state

    def _call_plumbing(self, state, with_extra=True):
        from _v8_ship import _finalize_push_plumbing  # type: ignore
        feat_dir = self.main / self.feat_rel
        extra = []
        if with_extra:
            rl = feat_dir / "review-log.jsonl"
            if rl.exists():
                extra.append(("review-log.jsonl", rl))
        return _finalize_push_plumbing(
            str(self.main), feat_dir, feat_dir / "state.json", "main",
            state, state["ship"], extra_files=extra,
        )

    def test_returns_commit_hash_not_persisted_to_state(self):
        """v8.18:成功路径返 (True, "", commit_hash) · 不写 ship.merge_target_finalize_commit。"""
        state = self._setup_ship_state()
        ok, warn, commit_hash = self._call_plumbing(state)
        self.assertTrue(ok, warn)
        self.assertEqual(warn, "")
        self.assertEqual(len(commit_hash), 40, f"commit hash 应是 sha-1 长度 · got {commit_hash!r}")
        # 关键断言:ship dict 不含 merge_target_finalize_commit 自引用字段
        self.assertNotIn("merge_target_finalize_commit", state["ship"],
                         "v8.18 不该写自引用 finalize_commit 字段")

    def test_multi_file_pushes_both_state_and_review_log(self):
        """v8.18:multi-file 模式 · state.json + review-log.jsonl 都进同一 commit。"""
        state = self._setup_ship_state(with_review_log=True)
        ok, warn, commit_hash = self._call_plumbing(state, with_extra=True)
        self.assertTrue(ok, warn)
        # 验证 origin/main HEAD commit 含两个文件
        rc, files, _ = _git(self.main, "show", "--stat",
                            f"origin/main:{self.feat_rel}/review-log.jsonl")
        # 如果 review-log.jsonl 在 commit 内 · cat-file 应能找到
        rc2, contents, _ = _git(self.main, "show",
                                f"origin/main:{self.feat_rel}/review-log.jsonl")
        self.assertEqual(rc2, 0, "review-log.jsonl 应在 origin/main 内(multi-file push)")
        self.assertIn("ship", contents)

    def test_no_extra_files_pushes_state_only(self):
        """无 extra_files · 只推 state.json(向后兼容)。"""
        state = self._setup_ship_state(with_review_log=False)
        ok, warn, commit_hash = self._call_plumbing(state, with_extra=False)
        self.assertTrue(ok, warn)
        # state.json 必存在
        rc, _, _ = _git(self.main, "show",
                        f"origin/main:{self.feat_rel}/state.json")
        self.assertEqual(rc, 0)

    def test_idempotent_no_change(self):
        """tree 无变化(state.json 已是终态)→ ok=True · commit_hash 空 · 不再推。"""
        state = self._setup_ship_state(with_review_log=False)
        # 先推一次
        ok1, _, hash1 = self._call_plumbing(state, with_extra=False)
        self.assertTrue(ok1)
        self.assertTrue(hash1)
        # 重跑 · 内容没变 → tree 一致 → 不再生新 commit
        ok2, _, hash2 = self._call_plumbing(state, with_extra=False)
        self.assertTrue(ok2)
        self.assertEqual(hash2, "", "tree 无变化 · 不该生新 commit")

    def test_failure_path_writes_failed_to_ship(self):
        """push 失败(远程不存在分支)→ plumbing 写 failed=true + reason。"""
        from _v8_ship import _finalize_push_plumbing  # type: ignore
        state = self._setup_ship_state()
        feat_dir = self.main / self.feat_rel
        # 故意调用一个不存在的 merge_target → base = origin/<x> rev-parse 失败
        ok, warn, hash_str = _finalize_push_plumbing(
            str(self.main), feat_dir, feat_dir / "state.json",
            "nonexistent-branch", state, state["ship"], extra_files=[],
        )
        self.assertFalse(ok)
        self.assertEqual(hash_str, "")
        # ship.merge_target_push_failed 应被写为 True
        self.assertTrue(state["ship"]["merge_target_push_failed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
