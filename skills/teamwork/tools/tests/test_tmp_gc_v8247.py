"""v8.247:/tmp/teamwork scratch 回收(ship2 即时 + bootstrap TTL 兜底)。

实证 case:CI 机磁盘 100% 打满 · /tmp/teamwork 48GB 全是 cargo target(单 feature 26GB)。
关键设计:按目录整体删(cargo fingerprint 一致性)· 不照抄 review-logs 的按文件删。
"""
import os
import tempfile
import unittest
from pathlib import Path

import bootstrap as B
import _v8_ship as ship


class _EnvRoot(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        os.environ["TEAMWORK_TMP_ROOT"] = str(self.root)

    def tearDown(self):
        os.environ.pop("TEAMWORK_TMP_ROOT", None)
        self._td.cleanup()


class TestPruneTeamworkTmpTTL(_EnvRoot):
    def test_expired_pruned_active_kept(self):
        old = self.root / "OLD-F001"; old.mkdir()
        (old / "CACHEDIR.TAG").write_text("x", encoding="utf-8")
        new = self.root / "NEW-F002"; new.mkdir()
        (new / "CACHEDIR.TAG").write_text("x", encoding="utf-8")
        # 深度 2 内全部过期(目录与子文件 mtime 都归零)
        os.utime(old / "CACHEDIR.TAG", (0, 0)); os.utime(old, (0, 0))
        res = B.prune_teamwork_tmp(retention_days=7)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["pruned"], 1)
        self.assertFalse(old.exists())
        self.assertTrue(new.exists())

    def test_deep_old_dir_with_recent_shallow_mtime_kept(self):
        """活跃判定看浅层 mtime:cargo 构建期间 .cargo-lock 持续更新 → 不误删。"""
        d = self.root / "ACTIVE-F003"; d.mkdir()
        (d / "debug").mkdir(); (d / "debug" / ".cargo-lock").write_text("", encoding="utf-8")
        res = B.prune_teamwork_tmp(retention_days=7)
        self.assertEqual(res["pruned"], 0)
        self.assertTrue(d.exists())

    def test_missing_root_na(self):
        os.environ["TEAMWORK_TMP_ROOT"] = str(self.root / "nope")
        self.assertEqual(B.prune_teamwork_tmp()["status"], "n_a")


class TestShipPruneFeatureTmp(_EnvRoot):
    def test_prunes_feature_dir_and_reports_bytes(self):
        d = self.root / "PTR-F033"; (d / "test-stage").mkdir(parents=True)
        (d / "test-stage" / "big.log").write_text("x" * 1024, encoding="utf-8")
        res = ship._prune_feature_tmp("PTR-F033")
        self.assertEqual(res["status"], "ok")
        self.assertGreaterEqual(res["pruned_bytes"], 1024)
        self.assertFalse(d.exists())

    def test_idempotent_na_when_missing(self):
        self.assertEqual(ship._prune_feature_tmp("NOT-EXIST")["status"], "n_a")
        self.assertEqual(ship._prune_feature_tmp("")["status"], "n_a")

    def test_finalize_steps_contain_tmp_cleanup(self):
        self.assertIn("tmp-cleanup", ship.SHIP_FINALIZE_STEPS)
        # 时序:必须在 verify-delivered/worktree-remove 之后 · main-sync 之前
        s = ship.SHIP_FINALIZE_STEPS
        self.assertLess(s.index("worktree-remove"), s.index("tmp-cleanup"))
        self.assertLess(s.index("tmp-cleanup"), s.index("main-sync"))


if __name__ == "__main__":
    unittest.main()
