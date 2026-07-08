#!/usr/bin/env python3
"""v8.161 · review-stage external-review 增量 diff 基线(review_base_commit)回归套件。

治本 aifriend yolo/ws02 实测:external review 评 merge_target...HEAD · 在长 WS / stacked
分支上随 deliverable 累积 → 跨 feature 串味(本 bug diff 只占 finding 的少数)+ 600s 超时。

修复:进 dev 那刻冻结 pre-dev HEAD(完成 stage 的 commit)进 state.review_base_commit ·
review-stage external-review 默认用它作 diff base(评本 feature 的 dev 增量)· 仅当它是
review 目标 commit 的祖先方采用 · 否则透明兜底 merge_target。

覆盖:
- maybe_freeze_review_base:进 dev 设 / 已设不覆盖 / 非 dev 不设 / commit 空不设
- _is_ancestor:祖先 True / 反向 False / bogus ref False(安全兜底)
- 集成(subprocess external-review --dry-run):
  - review stage + review_base_commit=祖先 → base_source=review_base_commit
  - review stage + review_base_commit=非祖先(sibling)→ 兜底 merge_target
  - review stage + 无 review_base_commit → merge_target
  - goal stage(评文档)+ review_base_commit 设 → 忽略 · merge_target

运行:python3 -m pytest skills/teamwork/tools/tests/test_review_base_commit_v8161.py -v
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
STATE_PY = TOOLS / "state.py"
sys.path.insert(0, str(TOOLS))


def _git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=True, text=True, timeout=20)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


# ─── 单元:maybe_freeze_review_base(纯函数 · 进 dev 冻结锚) ───────────────


class TestMaybeFreezeReviewBase(unittest.TestCase):
    def _fn(self):
        from _v8_engine import maybe_freeze_review_base  # type: ignore
        return maybe_freeze_review_base

    def test_sets_on_entering_dev(self):
        fn = self._fn()
        st: dict = {}
        self.assertTrue(fn(st, "dev", "abc123"))
        self.assertEqual(st["review_base_commit"], "abc123")

    def test_does_not_overwrite_existing(self):
        # review→dev 回退:已冻结的锚不被覆盖(再审仍覆盖全部 dev 增量)
        fn = self._fn()
        st = {"review_base_commit": "original"}
        self.assertFalse(fn(st, "dev", "newer"))
        self.assertEqual(st["review_base_commit"], "original")

    def test_noop_when_next_not_dev(self):
        fn = self._fn()
        st: dict = {}
        self.assertFalse(fn(st, "review", "abc123"))
        self.assertNotIn("review_base_commit", st)

    def test_noop_when_commit_empty(self):
        # git_head 失败返 None → 不设(external-review 兜底 merge_target)
        fn = self._fn()
        st: dict = {}
        self.assertFalse(fn(st, "dev", None))
        self.assertNotIn("review_base_commit", st)


# ─── 单元:_is_ancestor(真 git repo · 安全兜底) ─────────────────────────


class TestIsAncestor(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rbc-anc-"))
        _git(self.tmp, "init", "-b", "main")
        (self.tmp / ".teamwork_localconfig.json").write_text(  # v8.204:opt-in 异质(默认关)
            json.dumps({"disable_external_review": False}), encoding="utf-8")
        _git(self.tmp, "config", "user.email", "t@t.co")
        _git(self.tmp, "config", "user.name", "t")
        (self.tmp / "a.txt").write_text("a")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "A")
        self.A = _git(self.tmp, "rev-parse", "HEAD")[1]
        (self.tmp / "b.txt").write_text("b")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "B")
        self.B = _git(self.tmp, "rev-parse", "HEAD")[1]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fn(self):
        from state import _is_ancestor  # type: ignore
        return _is_ancestor

    def test_ancestor_true(self):
        self.assertTrue(self._fn()(self.A, self.B, str(self.tmp)))

    def test_reverse_false(self):
        # B 不是 A 的祖先(A 在前)
        self.assertFalse(self._fn()(self.B, self.A, str(self.tmp)))

    def test_bogus_ref_false(self):
        # 无效 ref → git 失败 → False(安全:external-review 兜底 merge_target · 绝不 BLOCK)
        self.assertFalse(self._fn()("deadbeef" * 5, self.B, str(self.tmp)))


# ─── 集成:external-review --dry-run base 解析 ──────────────────────────


class TestExternalReviewBaseResolution(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rbc-ext-"))
        _git(self.tmp, "init", "-b", "main")
        (self.tmp / ".teamwork_localconfig.json").write_text(  # v8.204:opt-in 异质(默认关)
            json.dumps({"disable_external_review": False}), encoding="utf-8")
        _git(self.tmp, "config", "user.email", "t@t.co")
        _git(self.tmp, "config", "user.name", "t")
        self.feat = self.tmp / "docs" / "features" / "F1"
        self.feat.mkdir(parents=True)
        # blueprint commit(= pre-dev 锚)
        (self.tmp / "a.txt").write_text("a")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "blueprint")
        self.BP = _git(self.tmp, "rev-parse", "HEAD")[1]
        # dev commit(review 目标 · BP 是其祖先)
        (self.tmp / "b.txt").write_text("b")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "dev")
        self.DEV = _git(self.tmp, "rev-parse", "HEAD")[1]
        # sibling commit(从 BP 另分叉 · 不是 DEV 祖先)
        _git(self.tmp, "checkout", "-b", "sib", self.BP)
        (self.tmp / "c.txt").write_text("c")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "sibling")
        self.SIB = _git(self.tmp, "rev-parse", "HEAD")[1]
        _git(self.tmp, "checkout", "main")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_state(self, stage, review_base_commit):
        st = {
            "feature_id": "F1", "flow_type": "Feature",
            "current_stage": stage, "merge_target": "main",
            "artifact_root": "docs/features/F1",
            # host 单源 = state.json.host(全局 host_audit.json 已退役 · 不再兜底)
            "host": "claude-code",
        }
        if review_base_commit is not None:
            st["review_base_commit"] = review_base_commit
        (self.feat / "state.json").write_text(json.dumps(st), encoding="utf-8")

    def _dry_run(self, stage, commit):
        r = subprocess.run(
            [sys.executable, str(STATE_PY), "external-review",
             "--feature", "docs/features/F1", "--stage", stage,
             "--commit", commit, "--dry-run"],
            cwd=str(self.tmp), capture_output=True, text=True, timeout=60)
        # stdout 是 JSON(末尾可能带其它行 · 取第一段 { ... })
        out = r.stdout
        start = out.index("{")
        # 平衡括号截取首个完整 JSON 对象
        depth = 0
        for i in range(start, len(out)):
            if out[i] == "{":
                depth += 1
            elif out[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(out[start:i + 1])
        raise AssertionError(f"无法解析 JSON · stdout={out!r} stderr={r.stderr!r}")

    def test_review_stage_ancestor_uses_review_base_commit(self):
        self._write_state("review", self.BP)
        d = self._dry_run("review", self.DEV)
        self.assertEqual(d["base_source"], "review_base_commit")
        self.assertEqual(d["base"], self.BP)

    def test_review_stage_non_ancestor_falls_back_merge_target(self):
        # review_base_commit = sibling(非 DEV 祖先)→ 校验失败 → 兜底 merge_target
        self._write_state("review", self.SIB)
        d = self._dry_run("review", self.DEV)
        self.assertEqual(d["base_source"], "merge_target")
        self.assertEqual(d["base"], "main")

    def test_review_stage_no_anchor_falls_back_merge_target(self):
        self._write_state("review", None)
        d = self._dry_run("review", self.DEV)
        self.assertEqual(d["base_source"], "merge_target")
        self.assertEqual(d["base"], "main")

    def test_goal_stage_ignores_review_base_commit(self):
        # goal/blueprint 评文档不评 diff · 即便锚存在也用 merge_target(base 不入 prompt)
        self._write_state("goal", self.BP)
        d = self._dry_run("goal", self.DEV)
        self.assertEqual(d["base_source"], "merge_target")


if __name__ == "__main__":
    unittest.main()
