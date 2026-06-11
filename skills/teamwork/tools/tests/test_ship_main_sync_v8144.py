#!/usr/bin/env python3
"""v8.144 ship-finalize 收尾终态治理回归套件。

实证 case(SVC-PLATFORM-B260611083636 收尾 transcript):
- step 7 pull 失败分支无视 pop 结果 · 宣称「stash 已 pop」→ 改动埋 stash · AI 手工重写成双份
- 一切 pull 失败都喊「分叉 · 需手动 rebase」→ 仅落后+脏 index 被误导成 ~20 条手工 git 手术
  (沙箱实测:staged 删除 + 无关 M 文件不阻塞 ff-pull · 一条 pull 即愈)
- teamwork 自动 stash 跨 feature 堆积无人盘点

覆盖(helper 单元 · git 沙箱):
- _behind_ahead:仅落后 / 真分叉 / 同步 三态
- _pull_failure_remedy:仅落后 → 给 pull 不喊 rebase;真分叉 → 才给 rebase
- _list_teamwork_stashes:只捞 teamwork 系 stash

运行:python3 -m pytest skills/teamwork/tools/tests/test_ship_main_sync_v8144.py -v
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS))


def _git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=True, text=True, timeout=20)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


class _SandboxBase(unittest.TestCase):
    """bare origin + 本地 clone(main 分支 · 1 commit)。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-ms144-"))
        self.origin = self.tmp / "origin.git"
        self.local = self.tmp / "local"
        _git(self.tmp, "init", "-q", "--bare", str(self.origin))
        _git(self.tmp, "clone", "-q", str(self.origin), str(self.local))
        _git(self.local, "config", "user.email", "t@t")
        _git(self.local, "config", "user.name", "t")
        (self.local / "a.md").write_text("base\n", encoding="utf-8")
        _git(self.local, "add", "-A")
        _git(self.local, "commit", "-qm", "init")
        _git(self.local, "push", "-q", "origin", "HEAD:main")
        _git(self.local, "fetch", "-q", "origin", "main")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _origin_advance(self):
        """借第二个 clone 给 origin/main 推一个新 commit(本地变 behind)。"""
        b = self.tmp / "b"
        _git(self.tmp, "clone", "-q", str(self.origin), str(b))
        _git(b, "config", "user.email", "t@t")
        _git(b, "config", "user.name", "t")
        (b / "remote.md").write_text("r\n", encoding="utf-8")
        _git(b, "add", "-A")
        _git(b, "commit", "-qm", "remote change")
        _git(b, "push", "-q", "origin", "main")
        _git(self.local, "fetch", "-q", "origin", "main")


class TestBehindAhead(_SandboxBase):
    def test_in_sync_is_zero_zero(self):
        from _v8_ship import _behind_ahead  # type: ignore
        self.assertEqual(_behind_ahead(str(self.local), "main"), (0, 0))

    def test_behind_only(self):
        from _v8_ship import _behind_ahead  # type: ignore
        self._origin_advance()
        self.assertEqual(_behind_ahead(str(self.local), "main"), (1, 0))

    def test_true_divergence(self):
        from _v8_ship import _behind_ahead  # type: ignore
        self._origin_advance()
        (self.local / "local.md").write_text("l\n", encoding="utf-8")
        _git(self.local, "add", "-A")
        _git(self.local, "commit", "-qm", "local change")
        self.assertEqual(_behind_ahead(str(self.local), "main"), (1, 1))


class TestPullFailureRemedy(_SandboxBase):
    def test_behind_only_recommends_pull_not_rebase(self):
        """仅落后 → remedy 给 `git pull --ff-only` · 不喊 rebase(治本误导手术)。"""
        from _v8_ship import _pull_failure_remedy  # type: ignore
        self._origin_advance()
        remedy = _pull_failure_remedy(str(self.local), "main")
        self.assertIn("仅落后", remedy)
        self.assertIn("pull --ff-only", remedy)
        self.assertNotIn("rebase", remedy)

    def test_divergence_recommends_rebase(self):
        from _v8_ship import _pull_failure_remedy  # type: ignore
        self._origin_advance()
        (self.local / "local.md").write_text("l\n", encoding="utf-8")
        _git(self.local, "add", "-A")
        _git(self.local, "commit", "-qm", "local change")
        remedy = _pull_failure_remedy(str(self.local), "main")
        self.assertIn("真分叉", remedy)
        self.assertIn("rebase", remedy)


class TestListTeamworkStashes(_SandboxBase):
    def test_only_teamwork_stashes_listed(self):
        from _v8_ship import _list_teamwork_stashes  # type: ignore
        # teamwork 系 stash
        (self.local / "a.md").write_text("mod1\n", encoding="utf-8")
        _git(self.local, "stash", "push", "-m",
             "teamwork ship-finalize v8.32 step 7 auto-stash")
        # 非 teamwork stash
        (self.local / "a.md").write_text("mod2\n", encoding="utf-8")
        _git(self.local, "stash", "push", "-m", "user manual wip")
        got = _list_teamwork_stashes(str(self.local))
        self.assertEqual(len(got), 1)
        self.assertIn("teamwork ship-finalize", got[0])
        self.assertIn("stash@{", got[0])  # %gd ref 在 · 可直接 pop/drop

    def test_no_stash_returns_empty(self):
        from _v8_ship import _list_teamwork_stashes  # type: ignore
        self.assertEqual(_list_teamwork_stashes(str(self.local)), [])


class TestStagedDeleteFFPullGroundTruth(_SandboxBase):
    """沙箱固化 v8.144 的地面真相:staged 删除(本地删 vs origin 同删)+ 无关
    M 文件 **不阻塞** ff-pull —— v8.87「下次 pull 自愈」的前提成立 · 该补的是
    「立即 pull」而不是留终态等人。此测试防未来 git 行为回退时静默失真。"""

    def test_staged_delete_plus_modified_file_ff_pull_succeeds(self):
        # 本地先有 other.md(已推 origin)
        (self.local / "other.md").write_text("base other\n", encoding="utf-8")
        _git(self.local, "add", "other.md")
        _git(self.local, "commit", "-qm", "add other")
        _git(self.local, "push", "-q", "origin", "main")
        # origin 前进:删 a.md(模拟归档 MR 合入 · 本地变 behind 1)
        b = self.tmp / "b"
        _git(self.tmp, "clone", "-q", str(self.origin), str(b))
        _git(b, "config", "user.email", "t@t")
        _git(b, "config", "user.name", "t")
        _git(b, "rm", "-q", "a.md")
        _git(b, "commit", "-qm", "delete a.md (archive MR)")
        _git(b, "push", "-q", "origin", "main")
        _git(self.local, "fetch", "-q", "origin", "main")
        # 本地:staged 同删 a.md(模拟 v8.87 git rm)+ 无关文件 unstaged M
        _git(self.local, "rm", "-q", "--ignore-unmatch", "a.md")
        (self.local / "other.md").write_text("local mod\n", encoding="utf-8")
        rc, _, err = _git(self.local, "pull", "--ff-only", "origin", "main")
        self.assertEqual(rc, 0, f"staged 删除 + 无关 M 不应阻塞 ff-pull:{err}")
        # staged 删除随 pull 收敛 · 只剩无关 M(helper strip 了前导空格 · 按内容断言)
        _, out, _ = _git(self.local, "status", "--porcelain")
        self.assertEqual([ln.strip() for ln in out.splitlines()], ["M other.md"])


if __name__ == "__main__":
    unittest.main()
