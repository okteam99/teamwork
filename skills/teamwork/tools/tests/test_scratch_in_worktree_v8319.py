"""v8.319:scratch 根迁入 worktree(用户拍板:「/tmp/teamwork 的内容能放到 worktree 下面么,
随着 worktree 就一起清理了」→ 做 · 完整迁入)。

新根 = `<worktree>/.teamwork-scratch/<用途>`(bootstrap 自动 gitignore「.teamwork-scratch*」·
随 worktree 生命周期消亡);worktree=off / legacy 回退旧根 `/tmp/teamwork/<feature_id>/`。

设计要点(三个插问的答案都物化在此):
- 「push 清理走脚本么」→ 是:`_prune_feature_tmp` 在 `ship-phase --action push` 处理器内,
  与 push 记录同一条命令,emit `scratch_cleanup`;
- 「清理耗时么」→ 原实现同步 rmtree + 全树统计 = 双遍历分钟级 → 改**同盘 rename(O(1) ·
  原路径立即消失)+ detached `rm -rf` 后台真删**,push 毫秒级返回;`du` 限时 3s 统计,大树跳过;
- 可行性实测:`git worktree remove` **不被 ignored 构建产物拦**(rename 后的 *-trash-* 残骸
  由 TTL 兜底);v8.306 指纹用 `git diff HEAD`,ignored 不进 diff,不受影响;
- worknode 额外收益:worktree 在绑定卷,scratch 不再堆容器可写层(141GB 实证环境)。
"""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import _v8_ship as SHIP  # noqa: E402
import bootstrap as BOOT  # noqa: E402


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestDualRootPrune(unittest.TestCase):

    def tearDown(self):
        os.environ.pop(SHIP.TEAMWORK_TMP_ROOT_ENV, None)

    def test_prunes_worktree_scratch_and_legacy(self):
        wt = Path(tempfile.mkdtemp(prefix="tw-wt319-"))
        (wt / ".teamwork-scratch" / "target").mkdir(parents=True)
        (wt / ".teamwork-scratch" / "target" / "a.o").write_text("x" * 512, encoding="utf-8")
        legacy_root = Path(tempfile.mkdtemp(prefix="tw-legacy319-"))
        os.environ[SHIP.TEAMWORK_TMP_ROOT_ENV] = str(legacy_root)
        (legacy_root / "T-F9" / "logs").mkdir(parents=True)
        (legacy_root / "T-F9" / "logs" / "t.log").write_text("y", encoding="utf-8")

        r = SHIP._prune_feature_tmp("T-F9", worktree_path=str(wt))
        self.assertEqual(r["status"], "ok")
        self.assertFalse((wt / ".teamwork-scratch").exists(), "worktree 侧原路径应 rename 后立即消失")
        self.assertFalse((legacy_root / "T-F9").exists(), "legacy 侧同清")
        self.assertEqual(len(r["paths"]), 2)
        self.assertGreater(r["pruned_bytes"], 0)

    def test_rename_makes_original_vanish_instantly(self):
        """耗时契约:原路径消失靠 rename(O(1))· 不等后台 rm —— push 命令不被大树拖住。"""
        wt = Path(tempfile.mkdtemp(prefix="tw-wt319b-"))
        (wt / ".teamwork-scratch").mkdir()
        t0 = time.monotonic()
        SHIP._prune_feature_tmp("", worktree_path=str(wt))
        self.assertLess(time.monotonic() - t0, 2.0)
        self.assertFalse((wt / ".teamwork-scratch").exists())

    def test_trash_leftovers_are_reclaimed_next_time(self):
        """后台删夭折的 *-trash-* 残骸 —— glob `.teamwork-scratch*` 下次调用一并回收。

        断言原名消失(rename 确定性)· 新 trash 名由后台 rm 收(小目录 ≤2s 内轮询等)。
        """
        wt = Path(tempfile.mkdtemp(prefix="tw-wt319c-"))
        stale = wt / ".teamwork-scratch-trash-99999"
        stale.mkdir()
        r = SHIP._prune_feature_tmp("", worktree_path=str(wt))
        self.assertEqual(r["status"], "ok")
        self.assertFalse(stale.exists(), "残骸原名应被 rename 走(确定性)")
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and any(wt.glob(".teamwork-scratch*")):
            time.sleep(0.05)
        self.assertFalse(any(wt.glob(".teamwork-scratch*")), "后台 rm 2s 内未收小目录")


class TestPushPassesWorktreePath(unittest.TestCase):

    def tearDown(self):
        os.environ.pop(SHIP.TEAMWORK_TMP_ROOT_ENV, None)

    def test_push_cleans_worktree_scratch(self):
        os.environ[SHIP.TEAMWORK_TMP_ROOT_ENV] = tempfile.mkdtemp(prefix="tw-e319-")
        wt = Path(tempfile.mkdtemp(prefix="tw-wtp319-"))
        (wt / ".teamwork-scratch").mkdir()
        (wt / ".teamwork-scratch" / "x.log").write_text("z", encoding="utf-8")
        state = {"ship": {"phase": "archived"}, "feature_id": "T-F319",
                 "merge_target": "dev", "worktree": {"path": str(wt)}}
        args = NS(feature=None, feature_head_commit="abc1234", git_host="github",
                  mr_creation_method="cli-gh", mr_url="https://x/pr/9",
                  mr_create_url=None, feature_pushed_at=None)
        result = SHIP._handle_ship_push(state, args)
        self.assertFalse((wt / ".teamwork-scratch").exists(),
                         "push 未清 worktree scratch —— 迁入后主时点必须认新根")
        self.assertEqual(result["scratch_cleanup"]["status"], "ok")


class TestBootstrapTTLSweepsWorktreeScratch(unittest.TestCase):
    """TTL 兜底第二根:只删各 worktree 的 .teamwork-scratch* 子目录 · 绝不动 worktree 本体。"""

    def _project(self):
        proj = Path(tempfile.mkdtemp(prefix="tw-proj319-"))
        (proj / ".teamwork_localconfig.json").write_text(
            json.dumps({"worktree_root_path": ".worktree"}), encoding="utf-8")
        return proj

    def test_stale_scratch_swept_fresh_kept_body_untouched(self):
        os.environ[BOOT.TEAMWORK_TMP_ROOT_ENV] = tempfile.mkdtemp(prefix="tw-b319-")
        try:
            proj = self._project()
            old_wt = proj / ".worktree" / "F-OLD"
            (old_wt / ".teamwork-scratch").mkdir(parents=True)
            (old_wt / ".teamwork-scratch" / "big.o").write_text("x", encoding="utf-8")
            (old_wt / "src.rs").write_text("code", encoding="utf-8")   # worktree 本体
            past = time.time() - 30 * 86400
            for p in [old_wt / ".teamwork-scratch" / "big.o", old_wt / ".teamwork-scratch"]:
                os.utime(p, (past, past))
            fresh_wt = proj / ".worktree" / "F-NEW"
            (fresh_wt / ".teamwork-scratch").mkdir(parents=True)
            (fresh_wt / ".teamwork-scratch" / "hot.o").write_text("y", encoding="utf-8")

            out = BOOT.prune_teamwork_tmp(retention_days=7, project_root=proj)
            self.assertEqual(out["worktree_scratch_pruned"], 1)
            self.assertFalse((old_wt / ".teamwork-scratch").exists(), "过期 scratch 应被扫")
            self.assertTrue((old_wt / "src.rs").exists(),
                            "🔴 worktree 本体被动了 —— 可能藏未提交工作 · 绝不许碰")
            self.assertTrue((fresh_wt / ".teamwork-scratch").exists(), "新鲜 scratch 误伤")
        finally:
            os.environ.pop(BOOT.TEAMWORK_TMP_ROOT_ENV, None)


class TestGitignoreEntry(unittest.TestCase):

    def test_bootstrap_adds_scratch_pattern(self):
        import subprocess
        proj = Path(tempfile.mkdtemp(prefix="tw-gi319-"))
        subprocess.run(["git", "init", "-q", str(proj)], capture_output=True)  # 函数有 not_git_repo 守卫
        BOOT.maintain_gitignore_worktree(proj, skill_root=None)
        gi = (proj / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".teamwork-scratch*", gi,
                      "通配必须覆盖 rename 残骸 .teamwork-scratch-trash-*")


class TestSpecsCarryNewRoot(unittest.TestCase):
    """七个载体同口径 —— 判据类内容多载体分叉的教训(部署单元 case)刚吃过。"""

    CARRIERS = ("standards/tech-rules.md", "docs/conventions.md",
                "SKILL.md", "stages/ui-design-stage.md", "stages/test-stage.md",
                "stages/ship-stage.md", "stages/dev-stage.md", "templates/tc.md")

    def test_all_carriers_state_worktree_root(self):
        for rel in self.CARRIERS:
            self.assertIn(".teamwork-scratch", _read(rel), f"{rel} 未更新新根")

    def test_common_keeps_off_mode_fallback(self):
        t = _read("docs/conventions.md")
        self.assertIn("worktree=off / legacy", t)
        self.assertIn("${TMPDIR:-/tmp}/teamwork/<feature_id>", t, "off 模式回退路径丢失")

    def test_lifecycle_channel_documented(self):
        t = _read("docs/conventions.md")
        self.assertIn("worktree 生命周期主兜底", t)
        self.assertIn("绝不动 worktree 本体", t)
        self.assertIn("rename", t, "耗时设计(rename+后台删)未成文")


if __name__ == "__main__":
    unittest.main(verbosity=2)
