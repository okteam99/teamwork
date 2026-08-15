"""merged worktree 巡检(P1-4)。

case:aon-core `.worktree/` 23G · 14 个注册 worktree 里 13 个已 merge(18G 垃圾 ·
最老 31 天)+ 1 孤儿;supersdk 5 个僵尸壳被递归工具扫成双份(ws-progress 9→18)。
根因与 141GB scratch 同款:回收挂在 ship2,session 死在 ship1 后 ship2 永不跑;
`worktree_cleanup` 配置键此前**没有任何代码消费者**(安慰剂配置)。

治法:巡检挂 bootstrap(每 session 会跑到的地方)· 配置成真开关:
auto(新默认)merged+干净即删;ask 逐个报告;keep 只计数;
僵尸壳任何模式都清;未 merge / 有真实未提交内容永不动。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT / "tools"))

from bootstrap import LOCALCONFIG_CONFIG_DEFAULTS, prune_merged_worktrees  # noqa: E402


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, timeout=30)


def _project(mode="auto"):
    """主仓(staging 为 merge_target)+ .worktree/wt-merged(已合入 staging · 干净)。"""
    root = Path(tempfile.mkdtemp(prefix="wtp-"))
    _git(root, "init", "-q", "-b", "staging")
    _git(root, "config", "user.email", "t@x.com")
    _git(root, "config", "user.name", "t")
    (root / "a.txt").write_text("a\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")
    (root / ".teamwork_localconfig.json").write_text(json.dumps({
        "worktree_cleanup": mode, "worktree_root_path": ".worktree",
        "merge_target": "staging"}), encoding="utf-8")
    wt = root / ".worktree" / "wt-merged"
    _git(root, "worktree", "add", "-q", "-b", "feat/m", str(wt), "staging")
    (wt / "f.txt").write_text("f\n", encoding="utf-8")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-qm", "feat")
    _git(root, "merge", "-q", "--no-ff", "-m", "merge", "feat/m")
    return root, wt


class TestAutoMode(unittest.TestCase):

    def test_merged_clean_removed_and_branch_deleted(self):
        root, wt = _project("auto")
        res = prune_merged_worktrees(root)
        self.assertEqual(res["status"], "ok")
        self.assertEqual([r["path"] for r in res["removed"]], ["wt-merged"])
        self.assertFalse(wt.exists())
        self.assertNotIn("feat/m", _git(root, "branch").stdout)
        self.assertEqual(res["reported"], [])

    def test_handoff_card_untracked_does_not_block(self):
        """archive 后接力卡转 untracked 属预期 —— 不挡 auto 删。"""
        root, wt = _project("auto")
        card = wt / "docs" / "features" / "X-F1"
        card.mkdir(parents=True)
        (card / "state.json").write_text("{}", encoding="utf-8")
        res = prune_merged_worktrees(root)
        self.assertEqual(len(res["removed"]), 1)
        self.assertFalse(wt.exists())

    def test_real_leftover_reported_not_removed(self):
        root, wt = _project("auto")
        (wt / "precious.txt").write_text("勿删\n", encoding="utf-8")
        res = prune_merged_worktrees(root)
        self.assertEqual(res["removed"], [])
        self.assertTrue(wt.exists())
        self.assertIn("非接力卡未提交内容", res["reported"][0]["reason"])

    def test_unmerged_untouched(self):
        root, wt = _project("auto")
        (wt / "new.txt").write_text("n\n", encoding="utf-8")
        _git(wt, "add", "-A")
        _git(wt, "commit", "-qm", "ahead")          # 领先 staging → 未 merge
        res = prune_merged_worktrees(root)
        self.assertEqual(res["removed"], [])
        self.assertTrue(wt.exists())


class TestAskKeepModes(unittest.TestCase):

    def test_ask_reports_not_removes(self):
        root, wt = _project("ask")
        res = prune_merged_worktrees(root)
        self.assertEqual(res["removed"], [])
        self.assertTrue(wt.exists())
        self.assertEqual(res["reported"][0]["path"], "wt-merged")
        self.assertIn("worktree_cleanup=ask", res["reported"][0]["reason"])

    def test_keep_counts_silently(self):
        root, wt = _project("keep")
        res = prune_merged_worktrees(root)
        self.assertEqual(res["removed"], [])
        self.assertEqual(res["reported"], [])
        self.assertTrue(wt.exists())


class TestZombieAndOrphan(unittest.TestCase):

    def test_zombie_shell_removed_in_any_mode(self):
        """supersdk 形态:git worktree 已 remove · 目录壳(只有 .DS_Store)残留。"""
        root, _ = _project("keep")
        shell = root / ".worktree" / "old-shell"
        shell.mkdir()
        (shell / ".DS_Store").write_bytes(b"\x00")
        res = prune_merged_worktrees(root)
        self.assertIn("old-shell", res["zombie_removed"])
        self.assertFalse(shell.exists())

    def test_orphan_with_content_reported_only(self):
        """aon 形态:不在 git worktree list 但有真实内容 → 只报告不动。"""
        root, _ = _project("auto")
        orphan = root / ".worktree" / "orphan"
        orphan.mkdir()
        (orphan / "data.bin").write_text("x", encoding="utf-8")
        res = prune_merged_worktrees(root)
        self.assertTrue(orphan.exists())
        self.assertTrue(any(r["path"] == "orphan" and "孤儿" in r["reason"]
                            for r in res["reported"]))


class TestConfigActivation(unittest.TestCase):

    def test_default_flipped_to_auto(self):
        """安慰剂配置转正:默认 auto · 存量显式 ask 不被覆盖(backfill 只补缺失键)。"""
        self.assertEqual(LOCALCONFIG_CONFIG_DEFAULTS["worktree_cleanup"], "auto")
        tpl = json.loads((SKILL_ROOT / "templates" / "teamwork_localconfig.json")
                         .read_text(encoding="utf-8"))
        self.assertEqual(tpl["worktree_cleanup"], "auto")

    def test_invalid_mode_falls_back_to_ask(self):
        root, wt = _project("whatever")
        res = prune_merged_worktrees(root)
        self.assertEqual(res["mode"], "ask")
        self.assertTrue(wt.exists())

    def test_no_worktree_root_skips(self):
        root = Path(tempfile.mkdtemp(prefix="wtp-"))
        _git(root, "init", "-q")
        self.assertEqual(prune_merged_worktrees(root)["status"], "no_worktree_root")

    def test_bootstrap_wires_check(self):
        src = (SKILL_ROOT / "tools" / "bootstrap.py").read_text(encoding="utf-8")
        self.assertIn('"merged_worktree_prune": worktree_prune', src)


class TestBuildWorldSpec(unittest.TestCase):
    """构建世界纪律收编(六条消费项目 KNOWLEDGE 同根教训 → 框架 conventions)。"""

    def test_conventions_carries_build_world_table(self):
        doc = (SKILL_ROOT / "docs" / "conventions.md").read_text(encoding="utf-8")
        self.assertIn("不隔离构建世界", doc)
        for key in ("node_modules", ".pth", "TMPDIR 绝不指 worktree 内",
                    "TEST_PG_DB_NAME", "共享测试库 = 并发毒"):
            self.assertIn(key, doc)


if __name__ == "__main__":
    unittest.main()
