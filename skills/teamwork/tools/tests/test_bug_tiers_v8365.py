#!/usr/bin/env python3
"""v8.365 · 提效方案第 2 批:Bug 按风险分三档(floor / tiny / full)。

- 轻档链由装配计划推导:floor = dev → ship · tiny = dev → review → ship
- 轻档准入 = 机器证据:repro-record 修复前红 · dev-complete 重跑同命令绿
- 拿不出复现 / 新事实 → bug-escalate 升 full 回 diagnose(记录保留)
- full 档链不变(diagnose → … → ship)
真跑 CLI + 真实临时 Git 仓库。
"""
from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
STATE_PY = str(HERE.parent / "state.py")
GENV = {"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
JUDGMENT = json.dumps({"sections_reviewed": ["§2.1", "§2.2"], "matched_signals": [],
                       "recommended_flow_type": "Bug", "ai_rationale": "t"})


class _Repo(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bugtier-"))
        self.env = dict(GENV, HOME=str(self.root), TEAMWORK_BYPASS_PREPARE_CHECK="1")
        self.git("init", "-q")
        (self.root / "app.txt").write_text("v1\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")

    def git(self, *a):
        return subprocess.run(["git", *a], cwd=self.root, env=self.env, check=True,
                              capture_output=True, text=True).stdout.strip()

    def run_state(self, *a):
        r = subprocess.run([sys.executable, STATE_PY, *a], cwd=self.root, env=self.env,
                           capture_output=True, text=True, timeout=120)
        for o in (r.stdout, r.stderr):
            try:
                return r.returncode, json.loads(o)
            except ValueError:
                continue
        return r.returncode, {"_raw": r.stdout + r.stderr}

    def init(self, preset, fid="T-B001-x"):
        self.feat = self.root / "docs" / "features" / fid
        self.feat.mkdir(parents=True)
        r = subprocess.run([sys.executable, STATE_PY, "init-feature", "--feature", str(self.feat),
                            "--feature-id", fid, "--flow-type", "Bug", "--preset", preset,
                            "--merge-target", "main", "--branch", "b", "--worktree-mode", "off"],
                           cwd=self.root, env=self.env, capture_output=True, text=True, timeout=60)
        return r

    def state(self):
        return json.loads((self.feat / "state.json").read_text(encoding="utf-8"))

    def fix_and_commit(self):
        (self.root / "fixed.txt").write_text("ok\n", encoding="utf-8")
        self.git("add", "fixed.txt")
        self.git("commit", "-qm", "fix")

    def dev_complete(self):
        fp = subprocess.run([sys.executable, STATE_PY, "tree-hash", "--feature", str(self.feat)],
                            cwd=self.root, env=self.env, capture_output=True, text=True).stdout.strip()
        return self.run_state("dev-complete", "--feature", str(self.feat), "--test-exit-code", "0",
                              "--test-stdout", "1 passed", "--test-runner", "subagent",
                              "--test-runner-model", "haiku", "--test-tree-hash", fp)


class TestInit(_Repo):
    def test_floor_chain(self):
        r = self.init("floor")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        st = self.state()
        self.assertEqual(st["current_stage"], "dev")
        self.assertEqual(st["assembly_plan"]["tier"], "floor")
        self.assertIn("repro-record", r.stdout)
        self.assertNotIn("先 diagnose", r.stdout)

    def test_tiny_chain_has_no_pm_acceptance(self):
        self.assertEqual(self.init("tiny").returncode, 0)
        rv = self.state()["assembly_plan"]["dims"]["review"]
        self.assertEqual(rv.get("pm_acceptance"), [])
        self.assertEqual(rv.get("review"), ["external"])

    def test_full_unchanged(self):
        self.assertEqual(self.init("full").returncode, 0)
        st = self.state()
        self.assertEqual(st["current_stage"], "diagnose")
        self.assertNotIn("assembly_plan", st)

    def test_other_presets_rejected(self):
        for i, p in enumerate(("micro", "lite", "medium")):
            r = self.init(p, fid=f"T-B00{i + 2}-x")
            self.assertNotEqual(r.returncode, 0, p)


class TestFloorRedGreen(_Repo):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.init("floor").returncode, 0)
        rc, out = self.run_state("dev-start", "--feature", str(self.feat))
        self.assertEqual(rc, 0, out)

    def test_dev_complete_without_repro_fails(self):
        self.fix_and_commit()
        rc, out = self.dev_complete()
        self.assertNotEqual(rc, 0)
        self.assertIn("repro-record", json.dumps(out, ensure_ascii=False))

    def test_passing_cmd_not_accepted_as_repro(self):
        rc, out = self.run_state("repro-record", "--feature", str(self.feat), "--cmd", "true")
        self.assertNotEqual(rc, 0)
        self.assertNotIn("repro", self.state())

    def test_red_then_green_reaches_ship(self):
        rc, out = self.run_state("repro-record", "--feature", str(self.feat),
                                 "--cmd", "test -f fixed.txt")
        self.assertEqual(rc, 0, out)
        self.assertNotEqual(self.state()["repro"]["red_exit"], 0)
        self.fix_and_commit()
        rc, out = self.dev_complete()
        self.assertEqual(rc, 0, out)
        st = self.state()
        self.assertEqual(st["current_stage"], "ship")          # floor:dev → ship
        self.assertEqual(st["repro"].get("green_exit"), 0)     # 绿也落库
        rc, out = self.run_state("ship-start", "--feature", str(self.feat))
        self.assertEqual(rc, 0, out)                             # 无 pm_acceptance · ship 准入放行

    def test_red_without_new_commit_rejected(self):
        self.run_state("repro-record", "--feature", str(self.feat), "--cmd", "test -f fixed.txt")
        (self.root / "fixed.txt").write_text("ok\n", encoding="utf-8")   # 改了没 commit
        rc, out = self.dev_complete()
        self.assertNotEqual(rc, 0)
        self.assertIn("没有新 commit", json.dumps(out, ensure_ascii=False))


class TestTinyRun(_Repo):
    def test_tiny_dev_complete_goes_to_review(self):
        self.assertEqual(self.init("tiny").returncode, 0)
        self.run_state("dev-start", "--feature", str(self.feat))
        self.run_state("repro-record", "--feature", str(self.feat), "--cmd", "test -f fixed.txt")
        self.fix_and_commit()
        rc, out = self.dev_complete()
        self.assertEqual(rc, 0, out)
        st = self.state()
        self.assertIn(st["current_stage"], ("dev", "review"))
        self.assertEqual(st["legal_next_stages"], ["review"]) if st["current_stage"] == "dev" else None
        self.assertNotIn("pm_acceptance", st.get("stage_review_roles", {}).get("pm_acceptance", []) or [])


class TestEscalate(_Repo):
    def test_escalate_back_to_diagnose_keeps_records(self):
        self.assertEqual(self.init("floor").returncode, 0)
        self.run_state("dev-start", "--feature", str(self.feat))
        self.run_state("repro-record", "--feature", str(self.feat), "--cmd", "test -f nope.txt")
        rc, out = self.run_state("bug-escalate", "--feature", str(self.feat),
                                 "--evidence", "根因在上游 SDK")
        self.assertEqual(rc, 0, out)
        st = self.state()
        self.assertEqual(st["preset"], "full")
        self.assertNotIn("assembly_plan", st)
        self.assertEqual(st["plan_history"][-1]["from"], "floor")
        self.assertIn("repro", st)
        rc, out = self.run_state("diagnose-start", "--feature", str(self.feat))
        self.assertEqual(rc, 0, out)

    def test_escalate_requires_light_bug(self):
        self.assertEqual(self.init("full").returncode, 0)
        rc, _ = self.run_state("bug-escalate", "--feature", str(self.feat), "--evidence", "x")
        self.assertNotEqual(rc, 0)


class TestPreview(unittest.TestCase):
    def preview(self, preset):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "docs" / "features").mkdir(parents=True)
        r = subprocess.run([sys.executable, STATE_PY, "prepare-check", "--feature-id-prefix", "T",
                            "--features-root", str(tmp / "docs" / "features"), "--flow-type", "Bug",
                            "--preset", preset, "--user-intent", "t", "--admission-judgment", JUDGMENT],
                           cwd=tmp, env={"PATH": "/usr/bin:/bin", "HOME": str(tmp),
                                         "TEAMWORK_PREPARE_AUDIT_PATH": str(tmp / "a.jsonl")},
                           capture_output=True, text=True, timeout=60)
        return [c["stage"] for c in json.loads(r.stdout).get("stage_chain_preview", [])]

    def test_bug_previews(self):
        self.assertEqual(self.preview("floor"), ["dev", "ship"])
        self.assertEqual(self.preview("tiny"), ["dev", "review", "ship"])
        self.assertEqual(self.preview("full")[0], "diagnose")


if __name__ == "__main__":
    unittest.main()
