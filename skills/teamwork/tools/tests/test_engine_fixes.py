#!/usr/bin/env python3
"""引擎层修复回归套件(_v8_engine / _v8_stage_specs)。

覆盖:
- 红 base 差分放行贯通 dev-complete → review-start(dev_diff_clean 证据)
- browser_e2e 可达:--needs-browser-e2e 写 execution_hints → test 转移消费
- 非法转移无 --bypass 假出口(恒 FAIL · hint 指 jump-to-stage)
- bypass 必带非空 --reason
- brief 截断保尾部纪律段/状态行模板段
- persist_args_to_evidence:bypass 路径也落库 · 校验函数纯谓词
- PRD-REVIEW verdicts 支持 TEAMWORK-MACHINE 机读块
- artifact 入 commit 精确匹配 + changeset 获取失败 FAIL
- yolo external 实跑日志门禁查 feature 目录新路径
- 未知 flow_type 显式 FAIL(不静默回退空图)
- 暂停点纪律「state.py 校验兜底」行仅对真有对应 evidence 的 stage 渲染
- sitemap panorama_path 行匹配不依赖 🔴 emoji

运行:python3 -m pytest skills/teamwork/tools/tests/test_engine_fixes.py -q
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
STATE_PY = TOOLS / "state.py"
sys.path.insert(0, str(TOOLS))

import _v8_engine as E  # noqa: E402
import _v8_stage_specs as S  # noqa: E402


def _git(cwd: Path, *args: str) -> tuple[int, str]:
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout.strip()


def _mk_repo(tmp: Path) -> None:
    _git(tmp, "init", "-b", "main")
    _git(tmp, "config", "user.email", "t@t.co")
    _git(tmp, "config", "user.name", "t")


def _run_state(cwd: Path, *args: str, expect_exit: int = 0) -> dict:
    """跑 state.py 子命令(cwd=repo 根)· 解析 stdout/stderr 里首个 JSON 对象。"""
    r = subprocess.run([sys.executable, str(STATE_PY), *args],
                       cwd=str(cwd), capture_output=True, text=True, timeout=60)
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}")
    out = r.stdout if r.stdout.strip() else r.stderr
    start = out.index("{")
    depth = 0
    for i in range(start, len(out)):
        if out[i] == "{":
            depth += 1
        elif out[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(out[start:i + 1])
    raise AssertionError(f"无法解析 JSON · stdout={r.stdout!r} stderr={r.stderr!r}")


def _write_state(feat: Path, **over) -> None:
    st = {
        "feature_id": "F1",
        "flow_type": "Feature",
        "current_stage": "dev",
        "merge_target": "main",
        "artifact_root": str(feat),
        "stage_contracts": {},
        "completed_stages": [],
        "concerns": [],
    }
    st.update(over)
    (feat / "state.json").write_text(
        json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


class _RepoCase(unittest.TestCase):
    """临时 git repo + feature 目录基类。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-engfix-"))
        _mk_repo(self.tmp)
        self.feat = self.tmp / "docs" / "features" / "F1"
        self.feat.mkdir(parents=True)
        (self.tmp / "seed.txt").write_text("seed", encoding="utf-8")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "seed")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @property
    def feat_rel(self) -> str:
        return "docs/features/F1"


# ─── 1 · 红 base 差分放行:dev-complete → review-start 贯通 ─────────────


class TestRedBaseDevToReview(_RepoCase):
    def setUp(self):
        super().setUp()
        # 项目级基线注册表:suite::legacy 是预存在失败
        (self.tmp / "project-specs").mkdir()
        (self.tmp / "project-specs" / "test-baseline.md").write_text(
            "# 测试基线失败集\n\n"
            "| 失败用例 (id) | 套件/命令 | 基线 commit | 原因（谁的债 · 何时清） | 登记于 |\n"
            "|---|---|---|---|---|\n"
            "| suite::legacy | pytest | abc | 历史债 | 2026-07-01 |\n",
            encoding="utf-8")

    def test_dev_complete_diff_clean_then_review_start_passes(self):
        """红 base(当前失败 ⊆ 基线)→ dev-complete 放行 + 落 dev_diff_clean → review-start PASS。"""
        _write_state(self.feat, current_stage="dev")
        d = _run_state(self.tmp, "dev-complete", "--feature", self.feat_rel,
                       "--test-stdout", "1 failed: suite::legacy",
                       "--test-exit-code", "1",
                       "--current-failures", "suite::legacy")
        self.assertEqual(d["verdict"], "PASS")
        self.assertEqual(d["transitioned_to"], "review")
        # 转移后引导指向 review-start(不引导直接 -complete)
        self.assertIn("review-start", d["status_line"])
        self.assertIn("review-start", d["next_stage_brief"])
        self.assertIn("获取完整 brief", d["next_stage_brief"])
        # evidence 落 dev_diff_clean(review-start 前置的机读依据)
        st = json.loads((self.feat / "state.json").read_text(encoding="utf-8"))
        ev = st["stage_contracts"]["dev"]["evidence"]
        self.assertEqual(ev["test_exit_code"], 1)
        self.assertIs(ev["dev_diff_clean"], True)
        self.assertEqual(st["execution_hints"]["test_baseline_excluded"], 1)

    def test_auto_transition_carries_continue_reminder(self):
        """v8.246:自动流转 emit 附「非暂停点 · 立即继续」提醒(治回合边界歇脚 · 实证 browser_e2e case)。"""
        _write_state(self.feat, current_stage="dev")
        d = _run_state(self.tmp, "dev-complete", "--feature", self.feat_rel,
                       "--test-stdout", "1 failed: suite::legacy",
                       "--test-exit-code", "1",
                       "--current-failures", "suite::legacy")
        self.assertEqual(d["transitioned_to"], "review")
        self.assertIn("continue_reminder", d)
        self.assertIn("review", d["continue_reminder"])
        self.assertIn("非暂停点", d["continue_reminder"])
        self.assertIn("回合边界", d["continue_reminder"])
        # review-start 前置接受差分放行
        d2 = _run_state(self.tmp, "review-start", "--feature", self.feat_rel)
        self.assertEqual(d2["verdict"], "PASS")

    def test_dev_complete_new_failure_still_blocks(self):
        """差分有新增失败 → dev-complete 仍 FAIL(回归必须修)。"""
        _write_state(self.feat, current_stage="dev")
        d = _run_state(self.tmp, "dev-complete", "--feature", self.feat_rel,
                       "--test-stdout", "2 failed",
                       "--test-exit-code", "1",
                       "--current-failures", "suite::legacy,suite::NEW",
                       expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        # 未放行 → 不写 dev_diff_clean
        st = json.loads((self.feat / "state.json").read_text(encoding="utf-8"))
        self.assertNotIn("dev_diff_clean",
                         st.get("stage_contracts", {}).get("dev", {}).get("evidence", {}))

    def test_review_start_blocked_when_red_without_diff_clean(self):
        """dev 红且无差分放行证据 → review-start 仍拦(防带 bug 进 review)。"""
        _write_state(self.feat, current_stage="dev", stage_contracts={
            "dev": {"input_satisfied": True, "process_satisfied": True,
                    "output_satisfied": True,
                    "evidence": {"test_exit_code": 1}},
        })
        d = _run_state(self.tmp, "review-start", "--feature", self.feat_rel,
                       expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        ids = [m["id"] for m in d["missing_prerequisites"]]
        self.assertIn("dev_test_passed", ids)

    def test_check_dev_test_passed_unit(self):
        """单元:exit_code==0 或 dev_diff_clean==true 都算通过。"""
        base = {"stage_contracts": {"dev": {"output_satisfied": True, "evidence": {}}}}
        ev = base["stage_contracts"]["dev"]["evidence"]
        ev.update({"test_exit_code": 0})
        self.assertTrue(S._check_dev_test_passed(base, NS()))
        ev.update({"test_exit_code": 1})
        self.assertFalse(S._check_dev_test_passed(base, NS()))
        ev.update({"dev_diff_clean": True})
        self.assertTrue(S._check_dev_test_passed(base, NS()))


# ─── 2 · browser_e2e 可达(--needs-browser-e2e → hints → test 转移)──────


class TestBrowserE2EWiring(_RepoCase):
    def _goal_complete_bypass(self, *extra: str) -> dict:
        _write_state(self.feat, current_stage="goal")
        return _run_state(
            self.tmp, "goal-complete", "--feature", self.feat_rel,
            "--needs-ui", "false", "--bypass",
            "--reason", "测试夹具:跳过 goal 产物", "--user-confirmed", *extra)

    def _prep_test_stage(self):
        """把 feature 推到 test stage + 备齐 test-complete 产物(commit 内含 TEST-REPORT.md)。

        PRD/TC 带真实 AC↔Test 绑定:verify-ac.py 门禁已真咬合(--prd/--tc CLI 修复后
        不再 silent skip)· 裸文件会 FAIL ac_test_binding。
        """
        _run_state(self.tmp, "raw-write", "--feature", self.feat_rel,
                   "--set", "current_stage=test",
                   "--reason", "测试夹具:直接切到 test stage")
        (self.feat / "PRD.md").write_text(
            "---\nacceptance_criteria:\n  - id: AC-1\n    desc: works\n---\n# prd",
            encoding="utf-8")
        (self.feat / "TC.md").write_text(
            "---\ntests:\n  - id: T-1\n    covers_ac: [AC-1]\n---\n# tc",
            encoding="utf-8")
        (self.feat / "TEST-REPORT.md").write_text("# report", encoding="utf-8")
        (self.feat / "e2e").mkdir(exist_ok=True)
        (self.feat / "e2e" / "t.py").write_text("print('ok')", encoding="utf-8")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "test artifacts")

    def test_needs_browser_e2e_true_transitions_to_browser_e2e(self):
        """--needs-browser-e2e true(bypass 路径也落库)→ test-complete 转 browser_e2e。"""
        d = self._goal_complete_bypass("--needs-browser-e2e", "true")
        self.assertEqual(d["verdict"], "PASS")
        st = json.loads((self.feat / "state.json").read_text(encoding="utf-8"))
        self.assertIs(st["execution_hints"]["browser_e2e_needed"], True)
        # bypass 下 needs-ui 决策也落库(不静默 fallback blueprint)
        self.assertIs(st["execution_hints"]["ui_design_needed"], False)
        self.assertEqual(d["transitioned_to"], "blueprint")

        self._prep_test_stage()
        d2 = _run_state(self.tmp, "test-complete", "--feature", self.feat_rel,
                        "--integration-test-exit-code", "0",
                        "--e2e-test-exit-code", "0")
        self.assertEqual(d2["verdict"], "PASS")
        self.assertEqual(d2["transitioned_to"], "browser_e2e")

    def test_without_flag_transitions_to_pm_acceptance(self):
        """未置 browser_e2e_needed → test-complete 转 pm_acceptance(默认不启用)。"""
        d = self._goal_complete_bypass()
        self.assertEqual(d["verdict"], "PASS")
        st = json.loads((self.feat / "state.json").read_text(encoding="utf-8"))
        self.assertNotIn("browser_e2e_needed", st.get("execution_hints", {}))

        self._prep_test_stage()
        d2 = _run_state(self.tmp, "test-complete", "--feature", self.feat_rel,
                        "--integration-test-exit-code", "0",
                        "--e2e-test-exit-code", "0")
        self.assertEqual(d2["verdict"], "PASS")
        self.assertEqual(d2["transitioned_to"], "pm_acceptance")

    def test_persist_unit_ui_design_flag(self):
        """单元:ui_design-complete 侧的 --needs-browser-e2e 同样由 persist 落 hints。"""
        st: dict = {}
        S.persist_args_to_evidence(
            "ui_design", st, NS(panorama_changed="false", needs_browser_e2e="true"))
        self.assertIs(st["execution_hints"]["browser_e2e_needed"], True)
        self.assertIs(st["execution_hints"]["panorama_changed"], False)
        # test 转移消费该 hint
        st["stage_contracts"] = {"test": {"evidence": {
            "integration_test_exit_code": 0, "e2e_test_exit_code": 0}}}
        self.assertEqual(S._test_transition(st), "browser_e2e")


# ─── 3 · 非法转移无 bypass 假出口 ───────────────────────────────────────


class TestIllegalTransitionNoBypassExit(_RepoCase):
    def test_bypass_flag_still_exit_1_and_hints_jump(self):
        _write_state(self.feat, current_stage="goal")
        d = _run_state(self.tmp, "dev-start", "--feature", self.feat_rel,
                       "--bypass", "--reason", "试图硬跳", "--user-confirmed",
                       "--missing", "legal_transition",
                       expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("非法转移", d["error"])
        self.assertIn("jump-to-stage", d["hint"])
        self.assertNotIn("--bypass", d["hint"])
        # 未迁移:current_stage 保持 goal
        st = json.loads((self.feat / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(st["current_stage"], "goal")


# ─── 6 · bypass 必带非空 --reason ──────────────────────────────────────


class TestBypassReasonRequired(_RepoCase):
    def test_start_bypass_empty_reason_fails(self):
        _write_state(self.feat, current_stage="dev")
        d = _run_state(self.tmp, "review-start", "--feature", self.feat_rel,
                       "--bypass", "--user-confirmed",
                       "--missing", "dev_completed,dev_test_passed",
                       expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("--reason", d["error"])

    def test_start_bypass_blank_reason_fails(self):
        _write_state(self.feat, current_stage="dev")
        d = _run_state(self.tmp, "review-start", "--feature", self.feat_rel,
                       "--bypass", "--user-confirmed", "--reason", "   ",
                       "--missing", "dev_completed,dev_test_passed",
                       expect_exit=1)
        self.assertIn("--reason", d["error"])

    def test_start_bypass_with_reason_passes(self):
        _write_state(self.feat, current_stage="dev")
        d = _run_state(self.tmp, "review-start", "--feature", self.feat_rel,
                       "--bypass", "--user-confirmed", "--reason", "夹具:跳过 dev 前置",
                       "--missing", "dev_completed,dev_test_passed")
        self.assertEqual(d["verdict"], "PASS")

    def test_complete_bypass_empty_reason_fails(self):
        _write_state(self.feat, current_stage="goal")
        d = _run_state(self.tmp, "goal-complete", "--feature", self.feat_rel,
                       "--needs-ui", "false", "--bypass", "--user-confirmed",
                       expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("--reason", d["error"])


# ─── 5 · brief 截断保尾部纪律段/状态行模板段 ────────────────────────────


class TestBriefTruncation(unittest.TestCase):
    def _mk_brief(self, body_lines: int) -> str:
        body = "\n".join(f"body-line-{i}" for i in range(body_lines))
        tail = (
            "\n\n---\n\n### 🔴 暂停点纪律(R5 物化)\n\n唯一授权暂停:**x**\n"
            + "\n".join(f"discipline-{i}" for i in range(6))
            + "\n\n---\n\n### 📊 状态行模板(R5+P0-10 · AI 每次主对话回复末尾必含)\n\n"
              "```\n🔄 F1 (Feature · dev)\n📁 /x\n🌿 b\n```\n"
        )
        return body + tail

    def test_tail_sections_survive_truncation(self):
        brief = self._mk_brief(200)
        out = E.truncate_brief(brief, "_brief_full_dev.md")
        self.assertIn("### 🔴 暂停点纪律", out)
        self.assertIn("### 📊 状态行模板", out)
        self.assertIn("中段截断", out)
        self.assertIn("_brief_full_dev.md", out)
        # 头部保留 · 中段被截
        self.assertIn("body-line-0", out)
        self.assertNotIn("body-line-150", out)

    def test_fallback_when_no_tail_marker(self):
        brief = "\n".join(f"l{i}" for i in range(200))
        out = E.truncate_brief(brief, "_brief_full_x.md")
        self.assertIn("l0", out)
        self.assertIn("截断", out)
        self.assertNotIn("l150", out)

    def test_tail_marker_inside_head_window_keeps_whole_tail(self):
        """尾部段起点落在头部保留区内(短 body + 长尾)→ 尾部整段保留 · 不再被截。"""
        brief = self._mk_brief(10)  # body 仅 10 行 · 纪律段起点 < 头部保留行数
        # 人为拉长尾部让总行数超限
        brief += "\n" + "\n".join(f"tail-extra-{i}" for i in range(120))
        out = E.truncate_brief(brief, "_brief_full_dev.md")
        self.assertIn("### 🔴 暂停点纪律", out)
        self.assertIn("### 📊 状态行模板", out)
        self.assertIn("tail-extra-119", out)


# ─── 9 · persist 纯谓词补充(review / pm_acceptance)─────────────────────


class TestPersistArgsToEvidence(unittest.TestCase):
    def test_review_verdict_persisted_not_by_check(self):
        st: dict = {}
        args = NS(verdict="APPROVE")
        ok, _ = S._evidence_review_verdict(st, args)
        self.assertTrue(ok)
        self.assertNotIn("stage_contracts", st)  # 纯谓词
        S.persist_args_to_evidence("review", st, args)
        self.assertEqual(
            st["stage_contracts"]["review"]["evidence"]["verdict"], "APPROVE")
        self.assertEqual(S._review_transition(st), "test")

    def test_pm_decision_persisted_not_by_check(self):
        st: dict = {}
        args = NS(decision="approved_and_ship", note="")
        ok, _ = S._evidence_pm_decision(st, args)
        self.assertTrue(ok)
        self.assertNotIn("stage_contracts", st)  # 纯谓词
        S.persist_args_to_evidence("pm_acceptance", st, args)
        self.assertEqual(S._pm_acceptance_transition(st), "ship")

    def test_invalid_values_not_persisted(self):
        st: dict = {}
        S.persist_args_to_evidence("goal", st, NS(needs_ui="banana"))
        self.assertNotIn("ui_design_needed", st.get("execution_hints", {}))


# ─── 10 · PRD-REVIEW verdicts 支持 TEAMWORK-MACHINE 机读块 ──────────────


class TestVerdictsMachineBlock(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-verdicts-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, verdict_line: str) -> None:
        (self.tmp / "PRD-REVIEW.md").write_text(
            "<!-- TEAMWORK-MACHINE 机读契约\n"
            "reviewers: [qa, architect]\n"
            f"verdicts: {verdict_line}\n"
            "-->\n\n# PRD Review\n正文\n",
            encoding="utf-8")

    def test_machine_block_all_approve_passes(self):
        self._write("{qa: APPROVE, architect: SKIP}")
        ok, err = S._evidence_prd_verdicts_all_pass({}, NS(feature=str(self.tmp)))
        self.assertTrue(ok, err)

    def test_machine_block_needs_revision_fails(self):
        self._write("{qa: APPROVE, architect: NEEDS_REVISION}")
        ok, err = S._evidence_prd_verdicts_all_pass({}, NS(feature=str(self.tmp)))
        self.assertFalse(ok)
        self.assertIn("未全员通过", err)

    def test_legacy_frontmatter_still_supported(self):
        (self.tmp / "PRD-REVIEW.md").write_text(
            "---\nverdicts: {qa: APPROVE}\n---\nbody\n", encoding="utf-8")
        ok, err = S._evidence_prd_verdicts_all_pass({}, NS(feature=str(self.tmp)))
        self.assertTrue(ok, err)


# ─── 11 · artifact 入 commit 精确匹配 + changeset 失败 FAIL ─────────────


class TestArtifactCommitExactMatch(_RepoCase):
    def _prep_test_state(self):
        _write_state(self.feat, flow_type="Bug", current_stage="test")
        (self.feat / "e2e").mkdir(exist_ok=True)
        (self.feat / "e2e" / "t.py").write_text("ok", encoding="utf-8")

    def test_substring_lookalike_not_accepted(self):
        """commit 只含 TEST-REPORT.md.bak(子串陷阱)→ 不算 TEST-REPORT.md 在 commit 内。"""
        self._prep_test_state()
        (self.feat / "TEST-REPORT.md.bak").write_text("bak", encoding="utf-8")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "bak only")
        # 磁盘有 TEST-REPORT.md(未提交)
        (self.feat / "TEST-REPORT.md").write_text("# report", encoding="utf-8")
        d = _run_state(self.tmp, "test-complete", "--feature", self.feat_rel,
                       "--integration-test-exit-code", "0",
                       "--e2e-test-exit-code", "0",
                       expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        reasons = " ".join(m.get("reason", "") for m in d["missing_artifacts"])
        self.assertIn("未在 commit", reasons)

    def test_exact_path_in_commit_passes(self):
        self._prep_test_state()
        (self.feat / "TEST-REPORT.md").write_text("# report", encoding="utf-8")
        _git(self.tmp, "add", "-A")
        _git(self.tmp, "commit", "-m", "with report")
        d = _run_state(self.tmp, "test-complete", "--feature", self.feat_rel,
                       "--integration-test-exit-code", "0",
                       "--e2e-test-exit-code", "0")
        self.assertEqual(d["verdict"], "PASS")

    def test_empty_changeset_fails_not_silent_pass(self):
        """空 commit(changeset 拿不到内容)→ must_be_in_commit 校验 FAIL · 不再静默通过。"""
        self._prep_test_state()
        (self.feat / "TEST-REPORT.md").write_text("# report", encoding="utf-8")
        _git(self.tmp, "commit", "--allow-empty", "-m", "empty")
        rc, head = _git(self.tmp, "rev-parse", "HEAD")
        d = _run_state(self.tmp, "test-complete", "--feature", self.feat_rel,
                       "--auto-commit", head,
                       "--integration-test-exit-code", "0",
                       "--e2e-test-exit-code", "0",
                       expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        reasons = " ".join(m.get("reason", "") for m in d["missing_artifacts"])
        self.assertIn("无法获取 commit", reasons)


# ─── 4 · yolo external 实跑日志门禁(feature 目录新路径)─────────────────


class TestYoloExternalLogNewPath(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-yolo-log-"))
        self.feat = self.tmp
        (self.feat / ".git").mkdir()  # v8.204:walk boundary
        (self.feat / ".teamwork_localconfig.json").write_text(  # opt-in 异质(默认关)
            json.dumps({"disable_external_review": False}), encoding="utf-8")
        (self.feat / "external-cross-review").mkdir(parents=True)
        (self.feat / "external-cross-review" / "review-codex.md").write_text(
            "---\nreview_model: codex\n---\n# review", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _check(self):
        state = {"current_stage": "review", "yolo": True,
                 "stage_review_roles": {"review": ["qa", "architect", "external"]}}
        return S._evidence_external_review_artifact(state, NS(feature=str(self.feat)))

    def test_no_log_fails_and_mentions_new_path(self):
        ok, err = self._check()
        self.assertFalse(ok)
        self.assertIn("实跑证据", err)
        self.assertIn("external-review-prompts", err)

    def test_feature_dir_log_passes(self):
        d = self.feat / "external-review-prompts"
        d.mkdir()
        (d / "review-claude-20260701T000000Z.log").write_text("ran", encoding="utf-8")
        ok, err = self._check()
        self.assertTrue(ok, err)

    def test_wrong_stage_log_does_not_pass(self):
        d = self.feat / "external-review-prompts"
        d.mkdir()
        (d / "goal-claude-20260701T000000Z.log").write_text("ran", encoding="utf-8")
        ok, _ = self._check()
        self.assertFalse(ok)

    def test_helper_both_paths(self):
        self.assertFalse(S._external_run_log_exists(self.feat, "review"))
        d = self.feat / "external-review-prompts"
        d.mkdir()
        (d / "review-codex-20260701T000000Z.log").write_text("ran", encoding="utf-8")
        self.assertTrue(S._external_run_log_exists(self.feat, "review"))


# ─── 15 · 未知 flow_type 显式 FAIL(引擎侧)──────────────────────────────


class TestUnknownFlowTypeExplicitFail(_RepoCase):
    def test_stage_start_unknown_flow_type_fails_explicitly(self):
        _write_state(self.feat, flow_type="bogus流程", current_stage="dev")
        d = _run_state(self.tmp, "dev-start", "--feature", self.feat_rel,
                       expect_exit=1)
        self.assertEqual(d["verdict"], "FAIL")
        self.assertIn("已知流程表", d["error"])
        self.assertIn("known_flow_types", d)


# ─── 21 · 暂停点纪律兜底行按 evidence 条件渲染 ──────────────────────────


class TestPauseDisciplineClaims(unittest.TestCase):
    def test_backstop_line_only_with_evidence(self):
        without = E._render_pause_discipline("x")
        self.assertNotIn("review mtime", without)
        with_ev = E._render_pause_discipline("x", has_review_convergence_evidence=True)
        self.assertIn("review mtime", with_ev)
        self.assertIn("revision_history", with_ev)

    def test_goal_has_convergence_evidence_dev_not(self):
        self.assertTrue(E._has_review_convergence_evidence(S.STAGE_SPECS["goal"]))
        self.assertFalse(E._has_review_convergence_evidence(S.STAGE_SPECS["dev"]))

    def test_open_questions_wording_generalized(self):
        out = E._render_pause_discipline("x")
        # goal 专属措辞(Open Questions 写进 PRD/Review)已泛化为中性表述
        self.assertNotIn("PRD/Review", out)
        self.assertIn("评审产物", out)


# ─── 22 · sitemap panorama_path 行匹配不依赖 🔴 ─────────────────────────


class TestSitemapPanoramaPathMatch(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-sitemap-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _check(self, ui_md_text: str):
        (self.tmp / "UI.md").write_text(ui_md_text, encoding="utf-8")
        return S._evidence_sitemap_updated({}, NS(feature=str(self.tmp)))

    def test_plain_line_without_emoji_matched(self):
        ok, err = self._check("panorama_path: /nonexistent/pano\n")
        self.assertFalse(ok)
        self.assertIn("sitemap.md 不存在", err)  # 已匹配到路径 · 走到 sitemap 校验

    def test_quote_line_with_emoji_matched(self):
        ok, err = self._check("> 🔴 panorama_path: /nonexistent/pano\n")
        self.assertFalse(ok)
        self.assertIn("sitemap.md 不存在", err)

    def test_bullet_line_matched(self):
        ok, err = self._check("- panorama_path: /nonexistent/pano\n")
        self.assertFalse(ok)
        self.assertIn("sitemap.md 不存在", err)

    def test_placeholder_blacklist_kept(self):
        ok, err = self._check("> panorama_path: null\n")
        self.assertFalse(ok)
        self.assertIn("无效", err)

    def test_prose_mention_not_matched(self):
        ok, err = self._check("本次不动 panorama_path 相关内容\n")
        self.assertFalse(ok)
        self.assertIn("未声明", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
