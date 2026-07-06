#!/usr/bin/env python3
"""v8.190 · teamwork main-sync auto-stash 回收回归套件。

治本(harvest 26× · 跨两次 harvest 最高频):main-sync stash-pull 每次备份不 pop · 跨 feature/session
累积 11+ · human 难判哪些可 drop。_reclaim_stashes:只认 teamwork 自建 main-sync stash · 默认 drop
**可证冗余的**(空 / 内容已在分支 · git apply --reverse --check 通过)· 其余含未合内容 surface ·
--drop-stashes 全清 · 🔴 绝不碰用户自己的 stash。

运行:python3 -m pytest skills/teamwork/tools/tests/test_stash_reclaim_v8190.py -q
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

from _v8_ship import _reclaim_stashes  # noqa: E402


def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, timeout=30)


class TestReclaim(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="rcl-"))
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "t@t")
        _git(self.repo, "config", "user.name", "t")
        (self.repo / "f.txt").write_text("base\n")
        _git(self.repo, "add", "f.txt")
        _git(self.repo, "commit", "-qm", "init")

    def _stash(self, msg):
        # 先造改动(clean tree 上 stash push 是 no-op · 不会建 stash)
        (self.repo / (msg.replace(" ", "_") + "_wip.txt")).write_text("wip\n")
        _git(self.repo, "stash", "push", "-q", "-u", "-m", msg)

    def _push(self, msg):
        # 直接 stash 当前改动(不加额外 wip · 供 redundant/live 精确构造)
        _git(self.repo, "stash", "push", "-q", "-u", "-m", msg)

    def _redundant_stash(self, tag):
        # 改 f.txt → stash → 把同样改动 commit(stash 内容已在 HEAD → 反向可 apply = 冗余)
        (self.repo / "f.txt").write_text(f"changed-{tag}\n")
        self._push(f"teamwork main-sync stash · ship 后 · {tag}")
        (self.repo / "f.txt").write_text(f"changed-{tag}\n")
        _git(self.repo, "add", "f.txt")
        _git(self.repo, "commit", "-qm", f"apply {tag}")

    def _live_stash(self, tag):
        # 新增文件(不在 HEAD)→ stash · 反向 apply 失败 = 非冗余
        (self.repo / f"{tag}.txt").write_text("live\n")
        self._push(f"teamwork main-sync stash · ship 后 · {tag}")

    def _list(self):
        return _git(self.repo, "stash", "list").stdout

    def test_drops_redundant_keeps_live(self):
        self._redundant_stash("RED1")
        self._live_stash("LIVE1")
        r = _reclaim_stashes(str(self.repo))
        self.assertEqual(r["teamwork_stashes"], 2)
        self.assertEqual(r["dropped"], 1)                     # 只 drop 冗余
        self.assertEqual([x["feature"] for x in r["remaining"]], ["LIVE1"])
        self.assertIn("LIVE1", self._list())
        self.assertNotIn("RED1", self._list())

    def test_never_touches_user_stash(self):
        self._live_stash("LIVE1")
        self._stash("my own wip")                             # 用户自己的(非 teamwork)
        r = _reclaim_stashes(str(self.repo))
        self.assertEqual(r["teamwork_stashes"], 1)            # 只认 teamwork 的
        self.assertIn("my own wip", self._list())             # 用户 stash 原封不动

    def test_drop_all_clears_teamwork_only(self):
        self._live_stash("LIVE1")
        self._live_stash("LIVE2")
        self._stash("my own wip")
        r = _reclaim_stashes(str(self.repo), drop_all=True)
        self.assertEqual(r["dropped"], 2)                     # 两个 teamwork 全清
        self.assertEqual(r["remaining_count"], 0)
        self.assertIn("my own wip", self._list())             # 用户的仍在
        self.assertNotIn("teamwork main-sync", self._list())

    def test_empty_when_no_teamwork_stash(self):
        self._stash("my own wip")
        r = _reclaim_stashes(str(self.repo))
        self.assertEqual(r["teamwork_stashes"], 0)
        self.assertEqual(r["dropped"], 0)
        self.assertIn("my own wip", self._list())

    def test_surface_hint_when_remaining(self):
        self._live_stash("LIVE1")
        r = _reclaim_stashes(str(self.repo))
        self.assertIn("hint", r)
        self.assertIn("--drop-stashes", r["hint"])


if __name__ == "__main__":
    unittest.main()
