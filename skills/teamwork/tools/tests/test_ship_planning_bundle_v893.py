#!/usr/bin/env python3
"""v8.93 规划层 back-ref 随收尾 MR 合入回归套件。

治本 case(aon ADMIN-F260603063006):旧 §5.7(v8.77)在 ship-finalize 全跑完(收尾 MR 已合
+ worktree 已清)**之后**才提规划层翻牌 · 且用**直推 merge_target** —— 与 v8.80「去直推」
自相矛盾(保护分支被拒)· 且收尾 MR 早已关闭 → 规划层物理塞不进 → 非原子 + 直推隐患。

现在:finalize-deliver 暂存收尾分支**前**先停在 planning-backref 暂停点(gate)· AI 判断
WS/ROADMAP/teamwork-space.md(+变更单)哪些翻「已交付」· 改完用 `--planning-artifacts <files>`
重跑 → 这些文件随 {archive zip + 删目录 + state.json} **同一收尾 MR** 原子合入(走 MR ·
兼容保护分支)。确无可翻 → `--no-planning-changes` 显式跳过。🔴 不 amend(一次打包一个 MR)。

覆盖:
- 首跑(无 flag)→ planning-backref gate(不暂存收尾分支)
- --no-planning-changes → 暂存归档收尾分支(无规划文件)+ deliver-pending
- --planning-artifacts → 规划文件随收尾分支暂存(分支内含翻牌后内容)+ 工作树还原 HEAD
- --planning-artifacts 文件不存在 / 仓外 → FAIL
- 全周期:暂存(含规划)→ 模拟合并 → 重跑交付 → origin/main + 工作树含翻牌内容
- 收尾分支已存在 → reuse(不 amend)+ warning

运行:python3 -m pytest skills/teamwork/tools/tests/test_ship_planning_bundle_v893.py -v
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


ROADMAP_PLANNED = "# ROADMAP\n\n- BL-020 Admin in-place edit · 📋 规划中/可启动\n"
ROADMAP_DELIVERED = "# ROADMAP\n\n- BL-020 Admin in-place edit · ✅ 已交付(2026-06-03)\n"
WS_PLANNED = "# WS-01\n\n进度:BL-020 待交付\n"
WS_DELIVERED = "# WS-01\n\n进度:BL-020 已交付 · WS 完成\n"


class _ShipPlanningBase(unittest.TestCase):
    FID = "ADMIN-M260603-bundle"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ship-plan-v893-"))
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
        self.zip_rel = f"docs/features/_archive/{self.FID}.zip"
        feat_dir = self.main / self.feat_rel
        (feat_dir / "goal").mkdir(parents=True)
        state = {
            "feature_id": self.FID,
            "flow_type": "Micro",
            "current_stage": "ship",   # step 4 → completed(进 zip 的终态)
            "merge_target": "main",
            "worktree": {"strategy": "off"},   # 跳过 worktree-remove
            "ship": {
                "phase": "merged", "shipped": "merged",
                "feature_head_commit": "deadbeef", "merge_commit_hash": "cafebabe",
            },
            "stage_contracts": {},
            "completed_stages": ["goal", "dev", "review", "test", "pm_acceptance"],
            "concerns": [],
        }
        (feat_dir / "state.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        (feat_dir / "goal" / "goal.md").write_text("# 目标", encoding="utf-8")
        # 规划层文件(repo 根 + workstream)· 初始为「规划中」
        (self.main / "ROADMAP.md").write_text(ROADMAP_PLANNED, encoding="utf-8")
        (self.main / "workstream").mkdir()
        (self.main / "workstream" / "WS-01.md").write_text(WS_PLANNED, encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-m", "init feature + planning")
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

    def _sf_branch(self):
        return f"ship-finalize/{self.FID}"

    def _show_on_branch(self, ref_path):
        rc, out, _ = _git(self.main, "show", ref_path)
        return rc, out


class TestPlanningGate(_ShipPlanningBase):
    def test_first_run_no_flag_emits_planning_gate(self):
        """首跑(无 flag)→ planning-backref gate · 不暂存收尾分支。"""
        _, d = self._finalize()
        self.assertEqual(d.get("verdict"), "PENDING", d)
        self.assertEqual(d.get("pending_step"), "planning-backref", d)
        # 收尾分支此刻**不应**已暂存(gate 在暂存之前)
        rc, _, _ = _git(self.main, "ls-remote", "origin", self._sf_branch())
        _, out, _ = _git(self.main, "ls-remote", "origin", self._sf_branch())
        self.assertEqual(out, "", "planning gate 阶段不应暂存收尾分支")
        # 文案点到三处规划层锚 + 两个出口
        na = d.get("next_action", "")
        self.assertIn("ROADMAP", na)
        self.assertIn("WS", na)
        self.assertIn("--planning-artifacts", na)
        self.assertIn("--no-planning-changes", na)


class TestNoPlanningChanges(_ShipPlanningBase):
    def test_skips_gate_stages_archive_only(self):
        """--no-planning-changes → 跳过 gate · 暂存归档收尾分支(无规划文件)。"""
        _, d = self._finalize("--no-planning-changes")
        self.assertEqual(d.get("verdict"), "PENDING", d)
        self.assertEqual(d.get("pending_step"), "finalize-deliver", d)
        self.assertTrue(d["finalize_mr"]["archived"], d)
        self.assertNotIn("planning_bundled", d["finalize_mr"],
                         "--no-planning-changes 不应 bundle 规划文件")
        # 收尾分支:ROADMAP 仍是原内容(未翻牌)
        _git(self.main, "fetch", "origin", self._sf_branch())
        rc, content = self._show_on_branch(f"origin/{self._sf_branch()}:ROADMAP.md")
        self.assertEqual(rc, 0)
        self.assertIn("📋 规划中", content)


class TestPlanningArtifactsBundle(_ShipPlanningBase):
    def test_planning_files_bundled_and_worktree_restored(self):
        """--planning-artifacts → 翻牌文件随收尾分支暂存 + 工作树还原 HEAD(防 ff-pull 冲突)。"""
        # AI 翻牌:改主工作区 ROADMAP + WS
        (self.main / "ROADMAP.md").write_text(ROADMAP_DELIVERED, encoding="utf-8")
        (self.main / "workstream" / "WS-01.md").write_text(WS_DELIVERED, encoding="utf-8")
        _, d = self._finalize("--planning-artifacts", "ROADMAP.md,workstream/WS-01.md")
        self.assertEqual(d.get("verdict"), "PENDING", d)
        self.assertEqual(d.get("pending_step"), "finalize-deliver", d)
        self.assertEqual(set(d["finalize_mr"].get("planning_bundled", [])),
                         {"ROADMAP.md", "workstream/WS-01.md"}, d)
        # 收尾分支内含翻牌后内容
        _git(self.main, "fetch", "origin", self._sf_branch())
        _, rm = self._show_on_branch(f"origin/{self._sf_branch()}:ROADMAP.md")
        self.assertIn("✅ 已交付", rm, "收尾分支 ROADMAP 应是翻牌后内容")
        _, ws = self._show_on_branch(f"origin/{self._sf_branch()}:workstream/WS-01.md")
        self.assertIn("WS 完成", ws)
        # zip 仍在(归档与规划同一收尾 commit)
        rc_z, _, _ = _git(self.main, "cat-file", "-e",
                          f"origin/{self._sf_branch()}:{self.zip_rel}")
        self.assertEqual(rc_z, 0, "归档 zip 应与规划文件在同一收尾分支")
        # 🔴 工作树还原 HEAD:ROADMAP/WS 不再 dirty(内容已进收尾分支)
        _, status, _ = _git(self.main, "status", "--short")
        self.assertNotIn("ROADMAP.md", status, "规划文件应已还原 HEAD(防 step7 ff-pull 冲突)")
        self.assertNotIn("WS-01.md", status)
        self.assertEqual((self.main / "ROADMAP.md").read_text(encoding="utf-8"),
                         ROADMAP_PLANNED, "工作树 ROADMAP 已还原原内容(翻牌内容在收尾分支)")

    def test_nonexistent_planning_artifact_fails(self):
        _, d = self._finalize("--planning-artifacts", "NOPE.md")
        self.assertEqual(d.get("verdict"), "FAIL", d)
        self.assertIn("不存在", json.dumps(d, ensure_ascii=False))

    def test_planning_artifact_outside_repo_fails(self):
        outside = self.tmp / "outside.md"
        outside.write_text("x", encoding="utf-8")
        _, d = self._finalize("--planning-artifacts", str(outside))
        self.assertEqual(d.get("verdict"), "FAIL", d)
        self.assertIn("仓库外", json.dumps(d, ensure_ascii=False))


class TestFullCyclePlanning(_ShipPlanningBase):
    def test_planning_merged_into_main_atomically(self):
        """全周期:暂存(含规划)→ 模拟合并 → 重跑交付 → origin/main + 工作树含翻牌内容。"""
        (self.main / "ROADMAP.md").write_text(ROADMAP_DELIVERED, encoding="utf-8")
        _, d1 = self._finalize("--planning-artifacts", "ROADMAP.md")
        self.assertEqual(d1.get("verdict"), "PENDING", d1)
        sf_commit = d1["finalize_mr"]["head_commit"]
        # 模拟收尾 MR 合并:ff origin/main 到收尾 commit(父 = origin/main)
        rc, _, err = _git(self.main, "push", "origin", f"{sf_commit}:main")
        self.assertEqual(rc, 0, f"模拟合并失败:{err}")
        # 重跑:检测已交付 → 续 step6/7 → PASS
        _, d2 = self._finalize()
        self.assertEqual(d2.get("verdict"), "PASS", d2)
        # origin/main:ROADMAP 翻牌 + 归档 zip 在 + feature 目录无 —— 原子
        _, rm_origin = self._show_on_branch("origin/main:ROADMAP.md")
        self.assertIn("✅ 已交付", rm_origin, "origin/main ROADMAP 应已翻牌(随收尾 MR 合入)")
        rc_z, _, _ = _git(self.main, "cat-file", "-e", f"origin/main:{self.zip_rel}")
        self.assertEqual(rc_z, 0, "归档 zip 应与 ROADMAP 翻牌同一 MR 合入 origin/main")
        rc_s, _, _ = _git(self.main, "cat-file", "-e", f"origin/main:{self.feat_rel}/state.json")
        self.assertNotEqual(rc_s, 0, "feature 目录应已归档删除")
        # 本地工作树:ff-pull 后 ROADMAP 是翻牌内容 + clean
        self.assertIn("✅ 已交付",
                      (self.main / "ROADMAP.md").read_text(encoding="utf-8"),
                      "本地 ff-pull 后应拉回翻牌内容")
        _, status, _ = _git(self.main, "status", "--short")
        self.assertNotIn("ROADMAP.md", status, "ff-pull 后 ROADMAP clean")


class TestReuseNoAmend(_ShipPlanningBase):
    def test_existing_sf_branch_reused_not_amended(self):
        """收尾分支已存在 → reuse(不 amend)· 传 --planning-artifacts 给 warning。"""
        # 先用 --no-planning-changes 暂存 archive-only 收尾分支
        _, d1 = self._finalize("--no-planning-changes")
        self.assertEqual(d1.get("pending_step"), "finalize-deliver", d1)
        # 改主意:现在想翻 ROADMAP · 但收尾分支已存在 → reuse + warning(不 amend)
        (self.main / "ROADMAP.md").write_text(ROADMAP_DELIVERED, encoding="utf-8")
        _, d2 = self._finalize("--planning-artifacts", "ROADMAP.md")
        self.assertEqual(d2.get("verdict"), "PENDING", d2)
        self.assertEqual(d2.get("pending_step"), "finalize-deliver", d2)
        warns = json.dumps(d2.get("warnings", []), ensure_ascii=False)
        self.assertIn("不 amend", warns)
        self.assertIn("--delete", warns, "warning 应给删分支重跑的逃生口")
        # 收尾分支仍是 archive-only(ROADMAP 未被偷偷塞进)
        _git(self.main, "fetch", "origin", self._sf_branch())
        _, content = self._show_on_branch(f"origin/{self._sf_branch()}:ROADMAP.md")
        self.assertIn("📋 规划中", content, "reuse 不 amend · 收尾分支 ROADMAP 仍原内容")


if __name__ == "__main__":
    unittest.main(verbosity=2)
