#!/usr/bin/env python3
"""v8.94 归档 INDEX.md 加「描述」列(极简 feature 描述)回归套件。

用户:feature archive 的时候给一段极简的 feature 描述,写到 INDEX.md。
实现:`ship-finalize --archive-desc '<≤200 字>'`(AI 在 planning-backref 暂停点连同
--planning-artifacts 一起给)→ 写进 `_archive/INDEX.md` 的「描述」列 · 便于日后不解压识别。
v8.112:上限 50 → 200 字(给更完整的描述空间)。
v8.113:超 200 不再截断 —— ship-finalize 前置门禁 FAIL · 要求 AI 压缩表达方式重写到 ≤200 重跑。

覆盖:
- `_clean_archive_desc`:正常 / 超 200 不截断(纯净化)/ `|` 净化 / 换行折叠 / 空 → `—`
- `_build_archive_index`:新行含描述列 + 旧 3 列行自动迁移 4 列(补 `—`)+ dedup
- 集成:ship-finalize --archive-desc → 收尾分支 INDEX.md 含描述

运行:python3 -m pytest skills/teamwork/tools/tests/test_ship_archive_desc_v894.py -v
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
STATE_PY = TOOLS / "state.py"
sys.path.insert(0, str(TOOLS))


def _git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=True, text=True, timeout=20)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


# ─── 单元:_clean_archive_desc ──────────────────────────────────────


class TestCleanArchiveDesc(unittest.TestCase):
    def _c(self, raw):
        from _v8_ship import _clean_archive_desc  # type: ignore
        return _clean_archive_desc(raw)

    def test_normal_kept(self):
        self.assertEqual(self._c("Admin 后台改单原子化 CAS 加固"),
                         "Admin 后台改单原子化 CAS 加固")

    def test_none_and_empty_to_dash(self):
        self.assertEqual(self._c(None), "—")
        self.assertEqual(self._c(""), "—")
        self.assertEqual(self._c("   "), "—")

    def test_over_200_not_truncated_by_sanitizer(self):
        """v8.113:净化函数不再截断 —— 长度上限由 ship-finalize 前置门禁 FAIL 强制。"""
        raw = "字" * 210
        out = self._c(raw)
        self.assertEqual(out, raw, "原样返回 · 不截断 · 不加 …")
        self.assertNotIn("…", out)

    def test_exactly_200_kept(self):
        raw = "字" * 200
        out = self._c(raw)
        self.assertEqual(out, raw)
        self.assertNotIn("…", out)

    def test_between_50_and_200_kept(self):
        """v8.112 回归:51–200 字现在不再截断(旧上限会截 · 防回退)。"""
        raw = "描" * 120
        out = self._c(raw)
        self.assertEqual(out, raw)
        self.assertNotIn("…", out)

    def test_pipe_sanitized(self):
        self.assertEqual(self._c("a|b|c"), "a/b/c")

    def test_newline_tab_collapsed(self):
        self.assertEqual(self._c("行一\n行二\t  行三"), "行一 行二 行三")


# ─── 单元:_build_archive_index(git repo · base_commit)──────────────


class TestBuildArchiveIndex(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="arch-idx-v894-"))
        _git(self.tmp, "init", "-b", "main")
        _git(self.tmp, "config", "user.email", "t@x.com")
        _git(self.tmp, "config", "user.name", "t")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _base_commit(self):
        rc, out, _ = _git(self.tmp, "rev-parse", "HEAD")
        return out

    def test_new_index_has_desc_column(self):
        from _v8_ship import _build_archive_index  # type: ignore
        # base 无 INDEX.md(git show 失败)→ 仅 header + 新行
        (self.tmp / "seed.txt").write_text("x", encoding="utf-8")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "seed")
        out = _build_archive_index(str(self.tmp), self._base_commit(),
                                   "docs/features/_archive/INDEX.md",
                                   "ADMIN-F260603", "2026-06-03T00:00:00Z",
                                   archive_desc="Admin 改单历史")
        self.assertIn("| Feature | 描述 | 交付归档时间 | 归档物 |", out)
        self.assertIn("| ADMIN-F260603 | Admin 改单历史 | 2026-06-03T00:00:00Z | "
                      "`ADMIN-F260603.zip` |", out)

    def test_absent_desc_renders_dash(self):
        from _v8_ship import _build_archive_index  # type: ignore
        out = _build_archive_index(str(self.tmp), "HEAD",
                                   "docs/features/_archive/INDEX.md",
                                   "F2", "t", archive_desc=None)
        self.assertIn("| F2 | — | t | `F2.zip` |", out)

    def test_old_3col_row_migrated_to_4col(self):
        from _v8_ship import _build_archive_index  # type: ignore
        # 写一个旧 3 列格式 INDEX.md 并提交(模拟 v8.93 及更早归档)
        idx_rel = "docs/features/_archive/INDEX.md"
        idx_abs = self.tmp / idx_rel
        idx_abs.parent.mkdir(parents=True)
        idx_abs.write_text(
            "# Feature 归档索引\n\n"
            "| Feature | 交付归档时间 | 归档物 |\n"
            "| --- | --- | --- |\n"
            "| OLD-F1 | 2026-01-01 | `OLD-F1.zip` |\n",
            encoding="utf-8")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "old index")
        out = _build_archive_index(str(self.tmp), self._base_commit(), idx_rel,
                                   "NEW-F2", "2026-06-03", archive_desc="新功能")
        # 旧行迁移为 4 列(补 — 描述)
        self.assertIn("| OLD-F1 | — | 2026-01-01 | `OLD-F1.zip` |", out)
        # 新行带描述
        self.assertIn("| NEW-F2 | 新功能 | 2026-06-03 | `NEW-F2.zip` |", out)
        # 表头 4 列
        self.assertIn("| Feature | 描述 | 交付归档时间 | 归档物 |", out)

    def test_re_archive_dedups_same_feature(self):
        from _v8_ship import _build_archive_index  # type: ignore
        idx_rel = "docs/features/_archive/INDEX.md"
        idx_abs = self.tmp / idx_rel
        idx_abs.parent.mkdir(parents=True)
        idx_abs.write_text(
            "# Feature 归档索引\n\n"
            "| Feature | 描述 | 交付归档时间 | 归档物 |\n"
            "| --- | --- | --- | --- |\n"
            "| F1 | 旧描述 | 2026-01-01 | `F1.zip` |\n",
            encoding="utf-8")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "idx")
        out = _build_archive_index(str(self.tmp), self._base_commit(), idx_rel,
                                   "F1", "2026-06-03", archive_desc="新描述")
        self.assertEqual(out.count("| F1 |"), 1, "同 feature 去重(只留新行)")
        self.assertIn("| F1 | 新描述 | 2026-06-03 | `F1.zip` |", out)
        self.assertNotIn("旧描述", out)


# ─── 集成:ship-finalize --archive-desc → INDEX ─────────────────────


class TestArchiveDescIntegration(unittest.TestCase):
    FID = "ADMIN-M260603-desc"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ship-desc-v894-"))
        self.bare = self.tmp / "origin.git"
        self.bare.mkdir()
        _git(self.bare, "init", "--bare", "-b", "main")
        self.main = self.tmp / "main-repo"
        self.main.mkdir()
        _git(self.main, "init", "-b", "main")
        _git(self.main, "config", "user.email", "test@x.com")
        _git(self.main, "config", "user.name", "test")
        _git(self.main, "remote", "add", "origin", str(self.bare))
        self.feat_rel = f"docs/features/{self.FID}"
        self.index_rel = "docs/features/_archive/INDEX.md"
        feat_dir = self.main / self.feat_rel
        feat_dir.mkdir(parents=True)
        state = {
            "feature_id": self.FID, "flow_type": "Micro",
            "current_stage": "ship", "merge_target": "main",
            "worktree": {"strategy": "off"},
            "ship": {"phase": "merged", "shipped": "merged",
                     "feature_head_commit": "deadbeef", "merge_commit_hash": "cafebabe"},
            "stage_contracts": {},
            "completed_stages": ["goal", "dev", "review", "test", "pm_acceptance"],
            "concerns": [],
        }
        (feat_dir / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-m", "init feature")
        _git(self.main, "push", "origin", "main")
        self.feature_arg = str(feat_dir)
        self._prev_env = {
            "TEAMWORK_BYPASS_MAIN_WORKTREE": os.environ.get("TEAMWORK_BYPASS_MAIN_WORKTREE"),
            "TEAMWORK_BYPASS_CHECKSUM": os.environ.get("TEAMWORK_BYPASS_CHECKSUM"),
        }
        os.environ["TEAMWORK_BYPASS_MAIN_WORKTREE"] = "1"
        os.environ["TEAMWORK_BYPASS_CHECKSUM"] = "1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k, v in self._prev_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _finalize(self, *extra):
        prev = os.getcwd()
        os.chdir(str(self.main))
        try:
            r = subprocess.run(
                [sys.executable, str(STATE_PY), "ship-finalize",
                 "--feature", self.feature_arg, *extra],
                capture_output=True, text=True, timeout=40)
            self.assertNotIn("Traceback", r.stderr, r.stderr[:500])
            d = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
            return r, d
        finally:
            os.chdir(prev)

    def test_archive_desc_written_to_index(self):
        _, d = self._finalize("--no-planning-changes",
                              "--archive-desc", "Admin 改单原子化 CAS 加固")
        self.assertEqual(d.get("verdict"), "PENDING", d)
        sf = f"ship-finalize/{self.FID}"
        _git(self.main, "fetch", "origin", sf)
        rc, content, _ = _git(self.main, "show", f"origin/{sf}:{self.index_rel}")
        self.assertEqual(rc, 0)
        self.assertIn("| Feature | 描述 | 交付归档时间 | 归档物 |", content)
        self.assertIn(self.FID, content)
        self.assertIn("Admin 改单原子化 CAS 加固", content)

    def test_over_200_blocks_with_compress_hint(self):
        """v8.113:超 200 → FAIL(压缩重跑)· 不截断 · 归档暂存前就拦(收尾分支不应被推)。"""
        long_desc = "描" * 210
        r, d = self._finalize("--no-planning-changes", "--archive-desc", long_desc)
        self.assertEqual(d.get("verdict"), "FAIL", d)
        self.assertEqual(d.get("failed_step"), "finalize-deliver", d)
        blob = json.dumps(d, ensure_ascii=False)
        self.assertIn("压缩", blob, "hint 应要求压缩表达方式")
        self.assertIn("200", blob)
        self.assertNotIn("…", blob, "不再截断 · 不应出现 …")
        # BLOCK 发生在归档暂存前 → 收尾分支不应被推
        sf = f"ship-finalize/{self.FID}"
        rc, _, _ = _git(self.main, "fetch", "origin", sf)
        self.assertNotEqual(rc, 0, "FAIL 应在归档暂存前 · 收尾分支不应存在")

    def test_compressed_under_200_passes_after_block(self):
        """v8.113:压缩到 ≤200 后重跑 → PENDING(门禁放行 · 描述完整写入)。"""
        compressed = "描" * 180
        _, d = self._finalize("--no-planning-changes", "--archive-desc", compressed)
        self.assertEqual(d.get("verdict"), "PENDING", d)
        sf = f"ship-finalize/{self.FID}"
        _git(self.main, "fetch", "origin", sf)
        rc, content, _ = _git(self.main, "show", f"origin/{sf}:{self.index_rel}")
        self.assertEqual(rc, 0)
        self.assertIn(compressed, content, "≤200 描述应完整写入 · 无截断")
        self.assertNotIn("…", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
