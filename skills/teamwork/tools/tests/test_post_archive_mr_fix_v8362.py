"""GPT-F261014120919-Offer-Plugin 实跑缺陷回归(用户拍板修复)。

P0-1 归档后 MR 修复无路可走:修一行 tsconfig 被迫重走整条链 + 报告「未在 commit 内」逼 bypass 两次。
P0-2 await-merge 把本分支新增文件导致的 CI 红连判 8 次「base 预存在」(GitLab 路径拿不到失败 job 名)。
P1   ci-commands 不跟 include:local · test-baseline 越界写主工作区 · 防御清单门禁只能跳过 ·
     dev 中途追加范围的回退口 · blueprint 问「取值集合会不会增长」。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL_ROOT = Path(__file__).resolve().parents[2]
TOOLS = SKILL_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import _v8_engine as E  # noqa: E402
import _v8_ship as H  # noqa: E402
import _v8_stage_specs as S  # noqa: E402
from _v8_engine import save_state  # noqa: E402

FID = "X-F261014120919-Offer-Plugin"


def _git(c, *a):
    return subprocess.run(["git", "-C", str(c), *a], check=True,
                          capture_output=True, text=True).stdout.strip()


def _run(*a):
    r = subprocess.run([sys.executable, str(TOOLS / "state.py"), *a],
                       capture_output=True, text=True, timeout=60)
    for o in (r.stdout, r.stderr):
        try:
            return json.loads(o)
        except ValueError:
            continue
    return {"_raw": r.stdout, "_err": r.stderr}


def _pushed_feature(code_lines=1):
    """已归档 + 已 push 的 feature(需求目录在分支里已不存在 · 工作树留接力卡)。"""
    root = Path(tempfile.mkdtemp(prefix="mrfix-"))
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@t")
    _git(root, "config", "user.name", "t")
    (root / "tsconfig.json").write_text('{"a": 1}\n', encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "code")
    head = _git(root, "rev-parse", "HEAD")
    feat = root / "docs" / "features" / FID          # untracked 接力卡(archive 已 rm --cached)
    feat.mkdir(parents=True)
    (feat / "PRD.md").write_text("# PRD\n", encoding="utf-8")
    (feat / "TEST-REPORT.md").write_text("# report\n", encoding="utf-8")
    roles = {"goal": ["external"], "blueprint": ["external"], "review": ["external"],
             "pm_acceptance": ["pm"]}
    save_state(feat / "state.json", {
        "feature_id": FID, "flow_type": "Feature", "current_stage": "completed",
        "legal_next_stages": [], "artifact_root": str(feat), "worktree": {"path": str(root)},
        "completed_stages": ["goal", "blueprint", "dev", "review", "test", "pm_acceptance", "ship"],
        "assembly_plan": {"tier": "full", "dims": {"spec_depth": "prd_tech", "evidence_gate": True,
                                                   "verify_depth": "test", "ui": False, "review": roles}},
        "stage_review_roles": roles,
        "ship": {"phase": "pushed", "mr_url": "http://x/pr/1", "feature_head_commit": head},
        "stage_contracts": {"blueprint": {"output_satisfied": True},
                            "pm_acceptance": {"output_satisfied": True,
                                              "evidence": {"decision": "approved_and_ship"}}},
    })
    return root, feat


def _fix_and_dev_complete(root, feat, lines):
    (root / "tsconfig.json").write_text("".join(f'{{"a": {i}}}\n' for i in range(lines)),
                                        encoding="utf-8")
    _git(root, "add", "tsconfig.json")
    _git(root, "commit", "-qm", "fix")
    fp = subprocess.run([sys.executable, str(TOOLS / "state.py"), "tree-hash", "--feature", str(feat)],
                        capture_output=True, text=True).stdout.strip()
    return _run("dev-complete", "--feature", str(feat), "--test-exit-code", "0",
                "--test-stdout", "1 passed", "--test-runner", "subagent",
                "--test-runner-model", "haiku", "--test-tree-hash", fp)


def _state(feat):
    return json.loads((feat / "state.json").read_text(encoding="utf-8"))


class TestPostArchiveLightFix(unittest.TestCase):

    def test_one_line_fix_reaches_push_without_bypass(self):
        root, feat = _pushed_feature()
        self.assertEqual(_run("jump-to-stage", "--feature", str(feat), "--to", "dev",
                              "--reason", "MR 修复:CI 红 tsconfig").get("verdict"), "OK")
        out = _fix_and_dev_complete(root, feat, 1)
        self.assertEqual(out.get("verdict"), "PASS", out)
        self.assertEqual(out.get("transitioned_to"), "ship")      # 不重走 review/test/验收
        self.assertEqual(_run("ship-start", "--feature", str(feat)).get("verdict"), "PASS")
        h2 = _git(root, "rev-parse", "HEAD")
        push = _run("ship-phase", "--action", "push", "--feature", str(feat),
                    "--feature-head-commit", h2, "--git-host", "github",
                    "--mr-creation-method", "cli-gh", "--mr-url", "http://x/pr/1")
        self.assertEqual(push.get("verdict"), "PASS", push)
        st = _state(feat)
        self.assertFalse(st.get("bypass_log"))
        self.assertFalse((st.get("ship") or {}).get("bypass_log"))
        self.assertTrue(st["ship"]["reopened_fixes"][-1].get("pushed_at"))   # 轻量通道关闭
        self.assertEqual(st["current_stage"], "completed")
        self.assertFalse(S.mr_fix_light(st))

    def test_large_fix_walks_full_chain(self):
        root, feat = _pushed_feature()
        _run("jump-to-stage", "--feature", str(feat), "--to", "dev", "--reason", "MR 修复:大改")
        out = _fix_and_dev_complete(root, feat, 40)
        self.assertEqual(out.get("transitioned_to"), "review", out)

    def test_reopen_to_goal_is_not_light(self):
        st = {"ship": {"phase": "pushed", "reopened_fixes": [{"target": "goal"}]}}
        self.assertFalse(S.mr_fix_light(st))

    def test_report_commit_check_skipped_after_archive(self):
        root, feat = _pushed_feature()
        st = _state(feat)
        st["current_stage"] = "test"
        st["stage_contracts"]["test"] = {"started_at": "2026-10-16T00:00:00Z"}
        save_state(feat / "state.json", st)
        out = _run("test-complete", "--feature", str(feat), "--auto-commit", _git(root, "rev-parse", "HEAD"))
        specs = [m.get("spec") for m in out.get("missing_artifacts") or []]
        self.assertNotIn("TEST-REPORT.md", specs, out)
        # 对照:未归档时同样的未提交报告照拦(豁免只给归档后)
        st["ship"]["phase"] = None
        save_state(feat / "state.json", st)
        out = _run("test-complete", "--feature", str(feat), "--auto-commit", _git(root, "rev-parse", "HEAD"))
        specs = [m.get("spec") for m in out.get("missing_artifacts") or []]
        self.assertIn("TEST-REPORT.md", specs, out)

    def test_dev_brief_announces_ci_command(self):
        st = {"ship": {"phase": "pushed", "reopened_fixes": [{}]}}
        self.assertIn("CI 失败的那条命令", S._mr_fix_line(st))


class TestCiAttribution(unittest.TestCase):

    def test_branch_added_file_is_self_introduced_even_if_base_red(self):
        attr = H.attribute_ci_failures(
            ["fe-ember-official-site-build"], {"fe-ember-official-site-build"}, True,
            ["fe-ember-official-site/docs/design/preview-project/proxy.ts"])
        self.assertEqual(attr["self_introduced"], ["fe-ember-official-site-build"])
        self.assertIn("命中本分支改动目录", attr["evidence"]["fe-ember-official-site-build"])

    def test_untouched_job_red_on_base_is_pre_existing(self):
        attr = H.attribute_ci_failures(["other-svc-test"], {"other-svc-test"}, True,
                                       ["fe-ember-official-site/x.ts"])
        self.assertEqual(attr["pre_existing"], ["other-svc-test"])

    def test_gitlab_status_reports_failed_job_names(self):
        mr = json.dumps({"project_id": 7, "head_pipeline": {"id": 99, "status": "failed"}})
        jobs = json.dumps([{"name": "fe-ember-official-site-build"}])

        def fake(cmd, timeout=0):
            out = mr if cmd[1] == "mr" else jobs
            return subprocess.CompletedProcess(cmd, 0, out, "")
        with mock.patch.object(H, "_git_run", side_effect=fake):
            ci = H._mr_ci_status("https://gitlab.example.com/g/p/-/merge_requests/1")
        self.assertEqual(ci["status"], "failing")
        self.assertEqual(ci["failing"], ["fe-ember-official-site-build"])

    def test_gitlab_unknown_job_names_never_default_to_pre_existing(self):
        mr = json.dumps({"project_id": 7, "head_pipeline": {"id": 99, "status": "failed"}})

        def fake(cmd, timeout=0):
            return subprocess.CompletedProcess(cmd, 0 if cmd[1] == "mr" else 1, mr, "")
        with mock.patch.object(H, "_git_run", side_effect=fake):
            ci = H._mr_ci_status("https://gitlab.example.com/g/p/-/merge_requests/1")
        self.assertEqual(ci["failing"], ["pipeline"])
        attr = H.attribute_ci_failures(ci["failing"], set(), False, [])
        self.assertEqual(attr["self_introduced"], ["pipeline"])


class TestCiIncludes(unittest.TestCase):

    def test_gitlab_local_include_is_followed_recursively(self):
        r = Path(tempfile.mkdtemp())
        (r / ".gitlab-ci.yml").write_text(
            "include:\n  - local: 'fe-site/ci/build.yml'\n  - project: 'x/y'\n    file: '/t.yml'\n",
            encoding="utf-8")
        (r / "fe-site" / "ci").mkdir(parents=True)
        (r / "fe-site" / "ci" / "build.yml").write_text(
            "include:\n  - local: /deep/more.yml\nb:\n  script:\n    - npm run build\n", encoding="utf-8")
        (r / "deep").mkdir()
        (r / "deep" / "more.yml").write_text("l:\n  script:\n    - npx tsc --noEmit\n", encoding="utf-8")
        found = E.scan_ci_commands(r)
        self.assertIn("fe-site/ci/build.yml", found)
        self.assertIn("deep/more.yml", found)


class TestBaselineStaysInWorktree(unittest.TestCase):

    def _layout(self):
        main = Path(tempfile.mkdtemp(prefix="main-"))
        (main / "project-specs").mkdir()                    # 主工作区 project-specs(未跟踪)
        (main / "project-specs" / "test-baseline.md").write_text(
            "| 失败用例 (id) | x |\n|---|---|\n| old_case | x |\n", encoding="utf-8")
        wt = main / ".worktree" / "F1"
        wt.mkdir(parents=True)
        _git(wt, "init", "-q")
        feat = wt / "docs" / "features" / "F1"
        feat.mkdir(parents=True)
        return main, wt, feat

    def test_add_without_target_does_not_touch_main(self):
        main, wt, feat = self._layout()
        before = (main / "project-specs" / "test-baseline.md").read_text(encoding="utf-8")
        out = _run("test-baseline", "--add", "--feature", str(feat), "--test-id", "new_case",
                   "--reason", "他人欠债")
        self.assertEqual(out.get("verdict"), "PENDING", out)
        self.assertEqual(before, (main / "project-specs" / "test-baseline.md").read_text(encoding="utf-8"))

    def test_target_worktree_writes_inside_and_reads_union(self):
        main, wt, feat = self._layout()
        out = _run("test-baseline", "--add", "--feature", str(feat), "--test-id", "new_case",
                   "--reason", "他人欠债", "--target", "worktree")
        self.assertEqual(out.get("verdict"), "OK", out)
        self.assertTrue((wt / "project-specs" / "test-baseline.md").is_file())
        self.assertEqual(S._read_test_baseline(str(feat)), {"old_case", "new_case"})


class TestDefenseListLanding(unittest.TestCase):

    def test_untracked_main_specs_gives_both_paths(self):
        main = Path(tempfile.mkdtemp(prefix="main-"))
        (main / "project-specs").mkdir()
        wt = main / ".worktree" / "F1"
        wt.mkdir(parents=True)
        kn, main_kn = H._defense_knowledge_paths(wt)
        self.assertEqual(main_kn.resolve(), (main / "project-specs" / "KNOWLEDGE.md").resolve())
        where = H._defense_where(kn, main_kn)
        self.assertIn(str(main_kn), where)
        self.assertIn(str(kn), where)


class TestDocs(unittest.TestCase):

    def test_dev_scope_change_goes_back_to_blueprint(self):
        t = (SKILL_ROOT / "stages" / "dev-stage.md").read_text(encoding="utf-8")
        self.assertIn("jump-to-stage --to blueprint", t)

    def test_blueprint_asks_whether_value_set_grows(self):
        t = (SKILL_ROOT / "stages" / "blueprint-stage.md").read_text(encoding="utf-8")
        self.assertIn("这个集合是固定的还是会增长", t)

    def test_ship_stage_documents_light_path_and_diff_attribution(self):
        t = (SKILL_ROOT / "stages" / "ship-stage.md").read_text(encoding="utf-8")
        self.assertIn("dev-complete **直达 ship**", t)
        self.assertIn("先比对本分支改动", t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
