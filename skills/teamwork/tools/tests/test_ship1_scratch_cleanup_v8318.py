"""v8.318:scratch 清理前移到 ship1(用户拍板:「按理 ship1 阶段就应该清」)。

实证(worknode · Docker-in-Docker):`/tmp/teamwork` 独占 **141GB**,单 feature
SRUN-F260810160028 达 **78GB**。回答用户「feature 结束时是否清理临时文件」:
**设计上有**(ship2 tmp-cleanup + bootstrap TTL 7 天),但两条通道在 worknode 形态下都够不着:
- tmp-cleanup 挂在 ship2 —— session 常在 ship1 交 MR 后结束/换机,ship2 不在本机跑;
- TTL 是时间判据不是空间判据 —— 7 天窗 × 78GB/feature,窗内即可打满磁盘。

改法:**push 成功即清**(主时点 · 证据已入 state.json,scratch 无对账价值;
MR 窗口期撞冲突回炉需冷编 = 用户接受的代价)+ 放弃(--abandon)即清 +
ship2 转幂等兜底 + TTL 扫孤儿。closed_unmerged(可重开)保留缓存。
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import _v8_ship as SHIP  # noqa: E402


def _scratch_with(feature_id: str) -> Path:
    root = Path(tempfile.mkdtemp(prefix="tw-scratch318-"))
    d = root / feature_id
    (d / "target").mkdir(parents=True)
    (d / "target" / "big.o").write_text("x" * 1024, encoding="utf-8")
    os.environ[SHIP.TEAMWORK_TMP_ROOT_ENV] = str(root)
    return d


class TestPushCleansScratch(unittest.TestCase):

    def tearDown(self):
        os.environ.pop(SHIP.TEAMWORK_TMP_ROOT_ENV, None)

    def test_push_success_prunes_feature_dir(self):
        d = _scratch_with("T-F318")
        state = {"ship": {"phase": "archived"}, "feature_id": "T-F318",
                 "merge_target": "dev", "branch": "feature/t-f318"}
        args = NS(feature=None, feature_head_commit="abc1234", git_host="github",
                  mr_creation_method="cli-gh", mr_url="https://x/pr/1",
                  mr_create_url=None, feature_pushed_at=None)
        result = SHIP._handle_ship_push(state, args)
        self.assertFalse(d.exists(), "push 成功后 scratch 未清 —— 141GB 场景原样复发")
        self.assertEqual(result["scratch_cleanup"]["status"], "ok")
        self.assertGreater(result["scratch_cleanup"]["pruned_bytes"], 0,
                           "清了但没报体量 —— 用户看不到省了多少")

    def test_push_without_scratch_is_noop(self):
        os.environ[SHIP.TEAMWORK_TMP_ROOT_ENV] = tempfile.mkdtemp(prefix="tw-empty318-")
        state = {"ship": {"phase": "archived"}, "feature_id": "T-NONE",
                 "merge_target": "dev"}
        args = NS(feature=None, feature_head_commit="abc1234", git_host="github",
                  mr_creation_method="cli-gh", mr_url="https://x/pr/2",
                  mr_create_url=None, feature_pushed_at=None)
        result = SHIP._handle_ship_push(state, args)
        self.assertEqual(result["scratch_cleanup"]["status"], "n_a")


class TestCloseUnmergedPaths(unittest.TestCase):
    """放弃即清 · 暂关可重开保缓存 —— 两条终止路径的保留语义相反,必须分开。"""

    def tearDown(self):
        os.environ.pop(SHIP.TEAMWORK_TMP_ROOT_ENV, None)

    def test_abandon_prunes(self):
        d = _scratch_with("T-F318B")
        state = {"ship": {"phase": "pushed"}, "feature_id": "T-F318B"}
        result = SHIP._handle_ship_close_unmerged(state, NS(abandon=True, reason=None))
        self.assertFalse(d.exists(), "放弃的 feature 不会再回炉 · 缓存无保留价值")
        self.assertEqual(result["scratch_cleanup"]["status"], "ok")

    def test_temporary_close_keeps_cache(self):
        d = _scratch_with("T-F318C")
        state = {"ship": {"phase": "pushed"}, "feature_id": "T-F318C"}
        result = SHIP._handle_ship_close_unmerged(state, NS(abandon=False, reason=None))
        self.assertTrue(d.exists(), "暂关可重开(重跑 archive→push)· 增量缓存该留")
        self.assertEqual(result["scratch_cleanup"]["status"], "kept")


class TestShip2StaysIdempotentBackstop(unittest.TestCase):

    def test_prune_missing_dir_is_na(self):
        """ship1 已清 → ship2 同名步骤对空目录必须安静跳过。"""
        os.environ[SHIP.TEAMWORK_TMP_ROOT_ENV] = tempfile.mkdtemp(prefix="tw-idem318-")
        try:
            r = SHIP._prune_feature_tmp("GONE-F1")
            self.assertEqual(r["status"], "n_a")
        finally:
            os.environ.pop(SHIP.TEAMWORK_TMP_ROOT_ENV, None)

    def test_finalize_still_carries_backstop_step(self):
        self.assertIn("tmp-cleanup", SHIP.SHIP_FINALIZE_STEPS,
                      "ship2 兜底步骤被移除 —— legacy in-flight 无人收")


class TestSpecsUpdated(unittest.TestCase):

    def test_common_states_three_channels(self):
        t = (ROOT / "standards" / "common.md").read_text(encoding="utf-8")
        self.assertIn("回收三通道", t)
        self.assertIn("ship1 push 成功即清", t)
        self.assertIn("幂等兜底", t)
        self.assertIn("141GB", t, "缺实证 why —— 会被当成任意时点选择")

    def test_ship_stage_push_section_states_cleanup(self):
        t = (ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        self.assertIn("顺手清本 feature scratch", t)
        self.assertIn("冲突回炉需冷编", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
