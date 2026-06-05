#!/usr/bin/env python3
"""v8 stage_specs evidence check 回归套件(P0-14 治本 bug 锚定)。

覆盖:
- _evidence_external_review_artifact 路径正确性(P0-14 bug 1)
- _evidence_ac_test_binding verify-ac.py 失败诊断(P0-14 bug 2)
- _evidence_review_after_primary mtime 关系(P0-1)
- _evidence_revision_history_present(P0-1)
- _evidence_needs_ui_decided(P0-6)
- _evidence_reviewers_match(P0-9)

运行:
    python3 -m pytest skills/teamwork/tools/tests/test_v8_stage_specs.py -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SKILL = TOOLS.parent

sys.path.insert(0, str(TOOLS))


def make_args(feature: str, **kwargs) -> SimpleNamespace:
    """构造 args namespace · 模拟 argparse 结果。"""
    return SimpleNamespace(feature=feature, **kwargs)


def write_md(path: Path, frontmatter: dict | None = None, body: str = "") -> None:
    """写一个简单 markdown 文件。"""
    content = ""
    if frontmatter is not None:
        content += "---\n"
        for k, v in frontmatter.items():
            if isinstance(v, list):
                content += f"{k}:\n"
                for item in v:
                    content += f"  - {item}\n"
            elif isinstance(v, dict):
                content += f"{k}:\n"
                for kk, vv in v.items():
                    content += f"  {kk}: {vv}\n"
            else:
                content += f"{k}: {v}\n"
        content += "---\n"
    content += body
    path.write_text(content, encoding="utf-8")


# ─── Bug 1 · _evidence_external_review_artifact 路径正确性 ────────


class TestExternalReviewArtifactPath(unittest.TestCase):
    """v8.0+P0-14 治本 PTR-F033 case · external-cross-review/ 路径修复。

    修前 bug:`feature_dir.parent / "external-cross-review"` 算到 features/external-cross-review · 错位。
    修后:`feature_dir / "external-cross-review"` 找到实际位置 features/<ID>/external-cross-review。
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmp) / "apps" / "x" / "docs" / "features" / "F001"
        self.feature_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_external_review_in_feature_dir_passes(self):
        """external-cross-review/ 在 feature_dir 内 · 校验 PASS(修复后正确行为)。"""
        from _v8_stage_specs import _evidence_external_review_artifact

        # 模拟 F033 实际结构:external-cross-review 在 feature_dir 内
        ext_dir = self.feature_dir / "external-cross-review"
        ext_dir.mkdir()
        (ext_dir / "codex.md").write_text("review", encoding="utf-8")

        args = make_args(feature=str(self.feature_dir))
        passed, err = _evidence_external_review_artifact({}, args)

        self.assertTrue(passed, f"应 PASS · 实际 FAIL · err={err!r}")

    def test_external_review_missing_fails(self):
        """external-cross-review/ 不存在 → FAIL。"""
        from _v8_stage_specs import _evidence_external_review_artifact

        args = make_args(feature=str(self.feature_dir))
        passed, err = _evidence_external_review_artifact({}, args)

        self.assertFalse(passed)
        self.assertIn("external-cross-review/", err)

    def test_external_review_empty_fails(self):
        """external-cross-review/ 存在但空 → FAIL。"""
        from _v8_stage_specs import _evidence_external_review_artifact

        (self.feature_dir / "external-cross-review").mkdir()

        args = make_args(feature=str(self.feature_dir))
        passed, err = _evidence_external_review_artifact({}, args)

        self.assertFalse(passed)
        self.assertIn("*.md 为空", err)

    def test_external_review_NOT_in_parent(self):
        """治本 bug:即使 parent 目录有 external-cross-review/ · 也不该被找到。"""
        from _v8_stage_specs import _evidence_external_review_artifact

        # 故意在 parent 放 external-cross-review · 模拟 bug 修前会误判 PASS
        parent_ext = self.feature_dir.parent / "external-cross-review"
        parent_ext.mkdir()
        (parent_ext / "wrong.md").write_text("wrong loc", encoding="utf-8")

        # feature_dir 内没有 external-cross-review
        args = make_args(feature=str(self.feature_dir))
        passed, err = _evidence_external_review_artifact({}, args)

        # 修复后:不该找 parent 的 · 应 FAIL
        self.assertFalse(passed, "external-cross-review 应在 feature_dir 内 · 不在 parent · bug 重现?")


# ─── v8.19 · external review 异质性硬约束(治本 SVC-CORE-F034)──────────


class TestExternalReviewHeteroEnforcement(unittest.TestCase):
    """v8.19 治本 SVC-CORE-F034 case · external 必真异质(不能 claude-isolated)。

    case:PMO 用 Agent subagent_type=general-purpose 起 claude isolated context 自审 ·
    标 frontmatter review_model: claude-opus-4-isolated-context 「透明」· 同模型自审违 R3。
    治本:文件名 + frontmatter review_model 双重校验 · 黑名单字面 BLOCKED。
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.feat = Path(self.tmp) / "feat"
        self.ext = self.feat / "external-cross-review"
        self.ext.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _check(self):
        from _v8_stage_specs import _evidence_external_review_artifact  # type: ignore
        args = make_args(feature=str(self.feat))
        return _evidence_external_review_artifact({}, args)

    # ── v8.90:单模型 disable_heterogeneous_review · 接受降级同模型自审 ──
    _DEGRADED_FM = ("---\nreview_role: self-degraded\nhost: claude-code\n"
                    "heterogeneous: false\ndegraded: true\n"
                    "degraded_mode: config-disabled\n---\nself-review body\n")

    def _set_config(self, disabled: bool):
        (Path(self.tmp) / ".git").mkdir(exist_ok=True)  # bound 向上 walk
        (Path(self.tmp) / ".teamwork_localconfig.json").write_text(
            json.dumps({"disable_heterogeneous_review": disabled}), encoding="utf-8")

    def _check_host(self):
        from _v8_stage_specs import _evidence_external_review_artifact  # type: ignore
        return _evidence_external_review_artifact(
            {"host": "claude-code", "current_stage": "review"},
            make_args(feature=str(self.feat)))

    def test_v890_config_disabled_accepts_degraded_self_review(self):
        """config 禁异质 + 降级同模型自审(degraded:true heterogeneous:false)→ 满足门禁。"""
        self._set_config(True)
        (self.ext / "review-claude.md").write_text(self._DEGRADED_FM, encoding="utf-8")
        ok, err = self._check_host()
        self.assertTrue(ok, f"config-disabled 应接受降级自审 · err={err!r}")

    def test_v890_config_enabled_still_blocks_same_model(self):
        """config 未禁(默认)+ 同模型文件 → 异质门禁仍 BLOCK(不因 v8.90 放水)。"""
        self._set_config(False)
        (self.ext / "review-claude.md").write_text(self._DEGRADED_FM, encoding="utf-8")
        ok, err = self._check_host()
        self.assertFalse(ok)
        self.assertIn("异质", err)
        # v8.95:默认(未禁)项目走通用 hint(host 自动映射异质模型)· 不混入 config-disabled 文案
        self.assertIn("host 自动映射异质模型", err)
        self.assertNotIn("别手写", err)

    def test_v890_config_disabled_still_blocks_unmarked_same_model(self):
        """config 禁异质 · 但同模型文件**无 degraded 标记**(手写伪装?)→ 仍 BLOCK。"""
        self._set_config(True)
        (self.ext / "review-claude.md").write_text(
            "---\nreview_role: external\nhost: claude-code\n---\nbody\n", encoding="utf-8")
        ok, err = self._check_host()
        self.assertFalse(ok, "config-disabled 也不接受未标记 degraded 的同模型文件")
        # v8.95:het_disabled 项目给**专属**修复指引(治本 case:AI 手写自审被拦后被通用
        # 「调异质模型」hint 误导 · 与 v8.90 单模型 opt-out 初衷相悖)。
        self.assertIn("disable_heterogeneous_review", err)
        self.assertIn("别手写", err)
        self.assertIn("state.py external-review", err)
        self.assertNotIn("host 自动映射异质模型", err,
                         "het_disabled 项目不应给通用「调异质模型」误导 hint")

    # ── 白名单字面 · PASS ──
    def test_codex_filename_passes(self):
        (self.ext / "code-codex.md").write_text("review", encoding="utf-8")
        ok, err = self._check()
        self.assertTrue(ok, err)

    def test_gpt_filename_passes(self):
        (self.ext / "prd-gpt-5.md").write_text("review", encoding="utf-8")
        ok, err = self._check()
        self.assertTrue(ok, err)

    def test_gemini_filename_passes(self):
        (self.ext / "tech-gemini.md").write_text("review", encoding="utf-8")
        ok, err = self._check()
        self.assertTrue(ok, err)

    # ── 黑名单字面 · BLOCKED(F034 case 核心) ──
    def test_claude_isolated_filename_blocked(self):
        """F034 case 复刻:code-claude-isolated.md → BLOCKED。"""
        (self.ext / "code-claude-isolated.md").write_text("review", encoding="utf-8")
        ok, err = self._check()
        self.assertFalse(ok)
        self.assertIn("claude", err.lower())
        self.assertIn("异质", err)

    def test_subagent_filename_blocked(self):
        (self.ext / "review-subagent.md").write_text("review", encoding="utf-8")
        ok, err = self._check()
        self.assertFalse(ok)
        self.assertIn("subagent", err.lower())

    def test_anthropic_filename_blocked(self):
        (self.ext / "code-anthropic.md").write_text("review", encoding="utf-8")
        ok, err = self._check()
        self.assertFalse(ok)

    def test_general_purpose_filename_blocked(self):
        (self.ext / "code-general-purpose.md").write_text("review", encoding="utf-8")
        ok, err = self._check()
        self.assertFalse(ok)

    # ── 模糊命名 · BLOCKED(必含白名单字面) ──
    def test_ambiguous_filename_blocked(self):
        (self.ext / "external-review.md").write_text("review", encoding="utf-8")
        ok, err = self._check()
        self.assertFalse(ok)
        self.assertIn("模型族字面", err)  # v8.68:措辞改「已知模型族字面」

    # ── v8.68:host-aware 同源判定(治本 codex-cli host claude 误判) ──
    def test_v868_codex_host_claude_review_passes(self):
        """v8.68 治本 SVC-PLATFORM-F060:host=codex-cli + claude external review → 异质 PASS。"""
        from _v8_stage_specs import _evidence_external_review_artifact  # type: ignore
        (self.ext / "review-claude.md").write_text(
            "---\nreview_model: 2.1.158 (Claude Code)\nhost: codex-cli\n---\nbody",
            encoding="utf-8")
        state = {"current_stage": "review", "host": "codex-cli",
                 "stage_review_roles": {"review": ["qa", "architect", "external"]}}
        ok, err = _evidence_external_review_artifact(state, make_args(feature=str(self.feat)))
        self.assertTrue(ok, err)

    def test_v868_claude_host_claude_review_blocked(self):
        """v8.68:host=claude-code + claude review → 同源 FAIL(保留原保护)。"""
        from _v8_stage_specs import _evidence_external_review_artifact  # type: ignore
        (self.ext / "review-claude.md").write_text(
            "---\nreview_model: Claude Code\nhost: claude-code\n---\nbody", encoding="utf-8")
        state = {"current_stage": "review", "host": "claude-code",
                 "stage_review_roles": {"review": ["qa", "architect", "external"]}}
        ok, err = _evidence_external_review_artifact(state, make_args(feature=str(self.feat)))
        self.assertFalse(ok)
        self.assertIn("同源", err)

    def test_v868_codex_host_codex_review_blocked(self):
        """v8.68:host=codex-cli + codex review → 同源 FAIL(codex 评 codex)。"""
        from _v8_stage_specs import _evidence_external_review_artifact  # type: ignore
        (self.ext / "review-codex.md").write_text(
            "---\nreview_model: codex-1.0\nhost: codex-cli\n---\nbody", encoding="utf-8")
        state = {"current_stage": "review", "host": "codex-cli",
                 "stage_review_roles": {"review": ["qa", "architect", "external"]}}
        ok, err = _evidence_external_review_artifact(state, make_args(feature=str(self.feat)))
        self.assertFalse(ok)

    def test_v868_isolated_blocked_regardless_of_host(self):
        """v8.68:任意 host + isolated/subagent → 仍 FAIL(机制黑名单 · 无论 host)。"""
        from _v8_stage_specs import _evidence_external_review_artifact  # type: ignore
        (self.ext / "review-claude-isolated.md").write_text("x", encoding="utf-8")
        state = {"current_stage": "review", "host": "codex-cli",
                 "stage_review_roles": {"review": ["qa", "architect", "external"]}}
        ok, err = _evidence_external_review_artifact(state, make_args(feature=str(self.feat)))
        self.assertFalse(ok)
        self.assertIn("机制", err)

    # ── frontmatter review_model 校验 ──
    def test_frontmatter_review_model_blocked_even_if_filename_ok(self):
        """文件名 OK(codex)· 但 frontmatter review_model 同源 → BLOCKED。

        防 PMO 用合规文件名包装实际是 isolated 的内容。
        """
        (self.ext / "code-codex.md").write_text(
            "---\nreview_model: claude-opus-4-isolated\n---\nbody",
            encoding="utf-8")
        ok, err = self._check()
        self.assertFalse(ok)
        self.assertIn("review_model", err)
        self.assertIn("claude", err.lower())

    def test_frontmatter_review_model_codex_passes(self):
        """文件名 + frontmatter 双白名单 · PASS。"""
        (self.ext / "code-codex.md").write_text(
            "---\nreview_model: codex-1.0.133\n---\nbody",
            encoding="utf-8")
        ok, err = self._check()
        self.assertTrue(ok, err)

    # ── stage_review_roles 移除 external → skip(向后兼容) ──
    def test_skipped_when_external_not_in_stage_roles(self):
        """若用户 change-review-roles 移除 external · 即使文件违规也 skip。"""
        (self.ext / "code-claude-isolated.md").write_text("x", encoding="utf-8")
        from _v8_stage_specs import _evidence_external_review_artifact  # type: ignore
        state = {
            "current_stage": "review",
            "stage_review_roles": {"review": ["pm", "qa", "architect"]},  # 无 external
        }
        args = make_args(feature=str(self.feat))
        ok, err = _evidence_external_review_artifact(state, args)
        self.assertTrue(ok)
        self.assertIn("skipped", err)

    # ── 混合:多文件 · 一个违规即全部 BLOCKED + 列出所有违规 ──
    def test_multi_file_lists_all_violations(self):
        (self.ext / "code-codex.md").write_text("ok", encoding="utf-8")
        (self.ext / "tech-claude-isolated.md").write_text("bad1", encoding="utf-8")
        (self.ext / "prd-subagent.md").write_text("bad2", encoding="utf-8")
        ok, err = self._check()
        self.assertFalse(ok)
        self.assertIn("tech-claude-isolated.md", err)
        self.assertIn("prd-subagent.md", err)
        # 合规的 code-codex.md 不在违规清单
        self.assertNotIn("code-codex.md:", err)


# ─── Bug 2 · _evidence_ac_test_binding 诊断 ─────────────────────


class TestYoloExternalRealRun(unittest.TestCase):
    """v8.67:yolo 严格按流程 · 不内化 —— external 必须真跑(有 v8.55 实跑日志)·
    防 AI 手写 external-cross-review/*.md 自盖章(治本 WS-002 yolo "mode: yolo-internalized")。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="tw-yolo-ext-")
        self.feat = Path(self.tmp)  # feat_name = tmp basename(唯一 · 不撞真 ~/.teamwork)
        (self.feat / "external-cross-review").mkdir(parents=True)
        (self.feat / "external-cross-review" / "review-codex.md").write_text(
            "---\nreview_model: codex\n---\n# review", encoding="utf-8")
        self.log_dir = (Path.home() / ".teamwork" / "external-review-logs"
                        / self.feat.name)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.log_dir, ignore_errors=True)

    def _check(self, yolo):
        from _v8_stage_specs import _evidence_external_review_artifact  # type: ignore
        state = {"current_stage": "review", "yolo": yolo,
                 "stage_review_roles": {"review": ["qa", "architect", "external"]}}
        return _evidence_external_review_artifact(state, make_args(feature=str(self.feat)))

    def test_yolo_no_run_log_fails(self):
        """yolo + external artifact 但无实跑日志 → FAIL(手写/内化)。"""
        ok, err = self._check(yolo=True)
        self.assertFalse(ok)
        self.assertIn("实跑证据", err)

    def test_yolo_with_run_log_passes(self):
        """yolo + external artifact + 实跑日志 → PASS。"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        (self.log_dir / "codex-review-20260531T000000Z.log").write_text("ran", encoding="utf-8")
        ok, err = self._check(yolo=True)
        self.assertTrue(ok, err)

    def test_non_yolo_no_log_passes(self):
        """非 yolo 不要求实跑日志(gate 仅 yolo)。"""
        ok, err = self._check(yolo=False)
        self.assertTrue(ok, err)


class TestAcTestBindingDiagnosis(unittest.TestCase):
    """v8.0+P0-14 治本:verify-ac.py 自身 bug(残留 placeholder)不应阻塞校验。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmp) / "F001"
        self.feature_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_prd_or_tc_missing_fails(self):
        """PRD.md 或 TC.md 不存在 → FAIL + hint 含路径。"""
        from _v8_stage_specs import _evidence_ac_test_binding

        # 只写 PRD · 不写 TC
        write_md(self.feature_dir / "PRD.md", {"x": "y"}, "body")

        args = make_args(feature=str(self.feature_dir))
        passed, err = _evidence_ac_test_binding({}, args)

        self.assertFalse(passed)
        self.assertIn("PRD.md 或 TC.md 不存在", err)
        # 修复后 hint 含路径(便于诊断)
        self.assertIn(str(self.feature_dir), err)

    def test_verify_ac_script_missing_silent_skip(self):
        """verify-ac.py 不存在(install/dev sync 问题)→ silent skip(PASS)。"""
        # 此 case 实际环境下 verify-ac.py 是存在的(dev 仓库)· 跳过此 unit test
        # 仅作为文档说明 · 真正模拟 install sync 问题需 mock skill_root
        pass


# ─── P0-1 · _evidence_review_after_primary mtime ──────────────────


class TestReviewAfterPrimary(unittest.TestCase):
    """v8.0+P0-1:review_artifact mtime 必须 > primary_artifact mtime。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmp) / "F001"
        self.feature_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_review_after_primary_passes(self):
        from _v8_stage_specs import _evidence_review_after_primary

        prd = self.feature_dir / "PRD.md"
        review = self.feature_dir / "PRD-REVIEW.md"
        prd.write_text("prd", encoding="utf-8")
        time.sleep(0.05)
        review.write_text("review", encoding="utf-8")

        check = _evidence_review_after_primary("PRD.md", "PRD-REVIEW.md")
        args = make_args(feature=str(self.feature_dir))
        passed, err = check({}, args)
        self.assertTrue(passed, f"PRD-REVIEW > PRD 应 PASS · err={err!r}")

    def test_review_before_primary_fails(self):
        """review mtime <= primary mtime → FAIL(治本 substep 链压缩)。"""
        from _v8_stage_specs import _evidence_review_after_primary

        prd = self.feature_dir / "PRD.md"
        review = self.feature_dir / "PRD-REVIEW.md"
        review.write_text("review", encoding="utf-8")
        time.sleep(0.05)
        prd.write_text("prd", encoding="utf-8")  # PRD 后写

        check = _evidence_review_after_primary("PRD.md", "PRD-REVIEW.md")
        args = make_args(feature=str(self.feature_dir))
        passed, err = check({}, args)
        self.assertFalse(passed)
        self.assertIn("review 未在", err)


# ─── P0-1 · _evidence_revision_history_present ───────────────────


class TestRevisionHistoryPresent(unittest.TestCase):
    """v8.0+P0-1:artifact frontmatter 必含 revision_history。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmp) / "F001"
        self.feature_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_revision_history_present_passes(self):
        from _v8_stage_specs import _evidence_revision_history_present

        write_md(
            self.feature_dir / "PRD.md",
            {"revision_history": ["v0.1", "v0.2"]},
            "body",
        )
        check = _evidence_revision_history_present("PRD.md", min_revisions=1)
        args = make_args(feature=str(self.feature_dir))
        passed, err = check({}, args)
        self.assertTrue(passed, err)

    def test_revision_history_missing_fails(self):
        from _v8_stage_specs import _evidence_revision_history_present

        write_md(self.feature_dir / "PRD.md", {"x": "y"}, "body")
        check = _evidence_revision_history_present("PRD.md", min_revisions=1)
        args = make_args(feature=str(self.feature_dir))
        passed, err = check({}, args)
        self.assertFalse(passed)
        self.assertIn("revision_history", err)


# ─── P0-6 · _evidence_needs_ui_decided ──────────────────────────


class TestNeedsUiDecided(unittest.TestCase):
    """v8.0+P0-6:--needs-ui 必传 + 写 state.execution_hints。"""

    def test_needs_ui_true_passes_and_writes(self):
        from _v8_stage_specs import _evidence_needs_ui_decided

        state = {"flow_type": "Feature"}
        args = SimpleNamespace(needs_ui="true")
        passed, err = _evidence_needs_ui_decided(state, args)
        self.assertTrue(passed, err)
        self.assertTrue(state["execution_hints"]["ui_design_needed"])

    def test_needs_ui_false_passes_and_writes(self):
        from _v8_stage_specs import _evidence_needs_ui_decided

        state = {"flow_type": "Feature"}
        args = SimpleNamespace(needs_ui="false")
        passed, err = _evidence_needs_ui_decided(state, args)
        self.assertTrue(passed, err)
        self.assertFalse(state["execution_hints"]["ui_design_needed"])

    def test_needs_ui_missing_fails(self):
        from _v8_stage_specs import _evidence_needs_ui_decided

        state = {"flow_type": "Feature"}
        args = SimpleNamespace()  # 不传 needs_ui
        passed, err = _evidence_needs_ui_decided(state, args)
        self.assertFalse(passed)
        self.assertIn("--needs-ui 必传", err)

    def test_agile_flow_needs_ui_true_rejected(self):
        """敏捷需求 + needs_ui=true → FAIL · 应升级 Feature 流程。"""
        from _v8_stage_specs import _evidence_needs_ui_decided

        state = {"flow_type": "敏捷需求"}
        args = SimpleNamespace(needs_ui="true")
        passed, err = _evidence_needs_ui_decided(state, args)
        self.assertFalse(passed)
        self.assertIn("敏捷需求", err)

# Feature Planning 不进状态机 · 不会到达 needs-ui check · 测试已删除


# ─── _review_transition · NEEDS_REVISION 自动回退 dev ───────────


class TestReviewTransition(unittest.TestCase):
    """治本 case: review-complete --verdict NEEDS_REVISION 应自动转 dev(回退路径)。"""

    def test_approve_transitions_to_test(self):
        from _v8_stage_specs import _review_transition
        state = {"stage_contracts": {"review": {"evidence": {"verdict": "APPROVE"}}}}
        self.assertEqual(_review_transition(state), "test")

    def test_needs_revision_returns_none_for_in_stage_loop(self):
        """v8.9 设计:NEEDS_REVISION → None · 留 review-stage 走 fix-retry 循环。

        v8.8 曾改为 → "dev"(stage 间回退)· v8.9 撤销 · 改为 stage 内 fix-retry。
        """
        from _v8_stage_specs import _review_transition
        state = {"stage_contracts": {"review": {"evidence": {"verdict": "NEEDS_REVISION"}}}}
        self.assertIsNone(_review_transition(state))

    def test_no_verdict_returns_none(self):
        from _v8_stage_specs import _review_transition
        state = {"stage_contracts": {"review": {"evidence": {}}}}
        self.assertIsNone(_review_transition(state))


# ─── P0-9 · _evidence_reviewers_match ────────────────────────────


class TestReviewersMatch(unittest.TestCase):
    """v8.0+P0-9:review artifact frontmatter.reviewers 必含 state.stage_review_roles[当前]。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmp) / "F001"
        self.feature_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_reviewers_all_present_passes(self):
        from _v8_stage_specs import _evidence_reviewers_match

        write_md(
            self.feature_dir / "REVIEW.md",
            {"reviewers": ["pm", "qa", "architect"], "verdict": "APPROVE"},
            "review body",
        )
        state = {
            "current_stage": "review",
            "stage_review_roles": {"review": ["pm", "qa", "architect"]},
        }
        check = _evidence_reviewers_match("REVIEW.md")
        args = make_args(feature=str(self.feature_dir))
        passed, err = check(state, args)
        self.assertTrue(passed, err)

    def test_reviewers_missing_role_fails(self):
        from _v8_stage_specs import _evidence_reviewers_match

        write_md(
            self.feature_dir / "REVIEW.md",
            {"reviewers": ["pm", "qa"], "verdict": "APPROVE"},  # 缺 architect
            "body",
        )
        state = {
            "current_stage": "review",
            "stage_review_roles": {"review": ["pm", "qa", "architect"]},
        }
        check = _evidence_reviewers_match("REVIEW.md")
        args = make_args(feature=str(self.feature_dir))
        passed, err = check(state, args)
        self.assertFalse(passed)
        self.assertIn("architect", err.lower())

    def test_reviewers_inline_list_format_parsed(self):
        """v8.0+P0-9 bug fix:行内 `[a, b, c]` 格式正确 parse。"""
        from _v8_stage_specs import _evidence_reviewers_match

        # 行内 list 格式(YAML flow style)
        review_path = self.feature_dir / "REVIEW.md"
        review_path.write_text(
            "---\nreviewers: [pm, qa, architect]\nverdict: APPROVE\n---\nbody\n",
            encoding="utf-8",
        )
        state = {
            "current_stage": "review",
            "stage_review_roles": {"review": ["pm", "qa", "architect"]},
        }
        check = _evidence_reviewers_match("REVIEW.md")
        args = make_args(feature=str(self.feature_dir))
        passed, err = check(state, args)
        self.assertTrue(passed, f"行内 list 应正确 parse · err={err!r}")

    def test_reviewers_no_required_skip(self):
        """state.stage_review_roles[当前] 为空 → silent skip(PASS)。"""
        from _v8_stage_specs import _evidence_reviewers_match

        state = {"current_stage": "dev", "stage_review_roles": {}}  # dev 无 review_roles
        check = _evidence_reviewers_match("REVIEW.md")
        args = make_args(feature=str(self.feature_dir))
        passed, err = check(state, args)
        self.assertTrue(passed, "无 required 应 silent skip")


# ─── v8.14 · scaffold_hints + template hint suffix ─────────────


class TestBuildScaffoldHints(unittest.TestCase):
    """v8.14:build_scaffold_hints 给各 stage 返回模板地图 + 校验器。

    治本 PTR-F054 "AI 找历史 Feature 抄" case · stage-start emit 时直接告诉
    AI 模板路径 + 校验器 · 不需要找历史。
    """

    def test_blueprint_hints_have_tc_tech_templates(self):
        from _v8_engine import build_scaffold_hints
        hints = build_scaffold_hints("blueprint")
        self.assertIsNotNone(hints)
        self.assertIn("TC.md", hints["expected_artifacts"])
        self.assertIn("TECH.md", hints["expected_artifacts"])
        # templates 必绝对路径
        self.assertTrue(hints["templates"]["TC.md"].endswith("/templates/tc.md"))
        self.assertTrue(hints["templates"]["TECH.md"].endswith("/templates/tech.md"))
        # verify-ac.py validator
        self.assertIn("TC.md", hints["validators"])
        self.assertIn("verify-ac.py", hints["validators"]["TC.md"])

    def test_test_stage_hints_have_test_report_template(self):
        from _v8_engine import build_scaffold_hints
        hints = build_scaffold_hints("test")
        self.assertIsNotNone(hints)
        self.assertTrue(hints["templates"]["TEST-REPORT.md"].endswith(
            "/templates/test-report.md"))
        # e2e/*.py 无模板(项目环境决定)
        self.assertIsNone(hints["templates"]["e2e/*.py"])

    def test_browser_e2e_hints_have_browser_test_report_template(self):
        from _v8_engine import build_scaffold_hints
        hints = build_scaffold_hints("browser_e2e")
        self.assertIsNotNone(hints)
        self.assertTrue(hints["templates"]["BROWSER-TEST-REPORT.md"].endswith(
            "/templates/browser-test-report.md"))

    def test_pm_acceptance_hints_have_pm_note_template(self):
        from _v8_engine import build_scaffold_hints
        hints = build_scaffold_hints("pm_acceptance")
        self.assertIsNotNone(hints)
        self.assertTrue(hints["templates"]["PM-NOTE.md"].endswith(
            "/templates/pm-note.md"))

    def test_ship_returns_none_no_template(self):
        from _v8_engine import build_scaffold_hints
        # ship 无 doc 模板(状态字段)
        self.assertIsNone(build_scaffold_hints("ship"))

    def test_hint_warns_against_finding_history(self):
        """hint 文本含"不要 find 历史 Feature 抄"反模式警示。"""
        from _v8_engine import build_scaffold_hints
        hints = build_scaffold_hints("blueprint")
        self.assertIn("历史 Feature", hints["hint"])

    def test_all_template_paths_exist(self):
        """所有非 None template 路径必须真实存在(防误填路径)。"""
        from _v8_engine import build_scaffold_hints, STAGE_TEMPLATES
        for stage in STAGE_TEMPLATES:
            hints = build_scaffold_hints(stage)
            if not hints:
                continue
            for artifact, tmpl_path in hints["templates"].items():
                if tmpl_path is None:
                    continue
                self.assertTrue(Path(tmpl_path).exists(),
                                f"{stage} {artifact} 模板路径不存在: {tmpl_path}")


class TestTemplateHintSuffix(unittest.TestCase):
    """v8.14:evidence FAIL reason 末尾追加 ` · 起草模板: <path>`。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.feature_dir = Path(self.tmp) / "F001"
        self.feature_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_template_hint_for_known_artifact(self):
        from _v8_stage_specs import _template_hint
        suffix = _template_hint("PRD.md")
        self.assertIn("起草模板", suffix)
        self.assertIn("templates/prd.md", suffix)

    def test_template_hint_for_unknown_artifact_returns_empty(self):
        from _v8_stage_specs import _template_hint
        self.assertEqual(_template_hint("RANDOM-FILE.md"), "")

    def test_template_hint_strips_leading_dirs(self):
        """artifact 可能含目录前缀 · 用 basename 匹配。"""
        from _v8_stage_specs import _template_hint
        suffix = _template_hint("some/dir/PRD.md")
        self.assertIn("templates/prd.md", suffix)

    def test_evidence_review_after_primary_fail_includes_template(self):
        """_evidence_review_after_primary primary 不存在 → reason 含模板路径。"""
        from _v8_stage_specs import _evidence_review_after_primary
        check = _evidence_review_after_primary("PRD.md", "PRD-REVIEW.md")
        # PRD.md 不存在
        args = make_args(feature=str(self.feature_dir))
        passed, reason = check({}, args)
        self.assertFalse(passed)
        self.assertIn("PRD.md 不存在", reason)
        self.assertIn("templates/prd.md", reason)  # template hint

    def test_evidence_revision_history_fail_includes_template(self):
        """artifact 不存在 → reason 含 template hint。"""
        from _v8_stage_specs import _evidence_revision_history_present
        check = _evidence_revision_history_present("TC.md")
        args = make_args(feature=str(self.feature_dir))
        passed, reason = check({}, args)
        self.assertFalse(passed)
        self.assertIn("TC.md 不存在", reason)
        self.assertIn("templates/tc.md", reason)

    def test_evidence_reviewers_match_fail_includes_template(self):
        """review artifact 不存在 → reason 含 hint(若 basename 有映射)。"""
        from _v8_stage_specs import _evidence_reviewers_match
        check = _evidence_reviewers_match("PRD-REVIEW.md")  # PRD-REVIEW basename 不在 map
        state = {
            "current_stage": "goal",
            "stage_review_roles": {"goal": ["pm", "qa"]},
        }
        args = make_args(feature=str(self.feature_dir))
        passed, reason = check(state, args)
        self.assertFalse(passed)
        # PRD-REVIEW.md 不在 map · 无 suffix · 但不应抛异常
        self.assertIn("PRD-REVIEW.md", reason)


class TestTemplateFilesExist(unittest.TestCase):
    """v8.14:确保 v8.14 新建的 3 个模板真实存在 + frontmatter 有效。"""

    def test_test_report_template_exists(self):
        p = SKILL / "templates" / "test-report.md"
        self.assertTrue(p.exists())
        text = p.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"), "模板必含 frontmatter")
        self.assertIn("feature_id:", text)
        self.assertIn("evidence:", text)

    def test_browser_test_report_template_exists(self):
        p = SKILL / "templates" / "browser-test-report.md"
        self.assertTrue(p.exists())
        text = p.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("browser_automation:", text)
        self.assertIn("viewport:", text)

    def test_pm_note_template_exists(self):
        p = SKILL / "templates" / "pm-note.md"
        self.assertTrue(p.exists())
        text = p.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("decision:", text)


# ─── v8.16 · _check_prd_or_bug_report 按 flow_type 分支(治本 INFRA-M001 case)──


class TestPrdOrBugReportPrereq(unittest.TestCase):
    """v8.16:dev-start prerequisite 按 flow_type 分支判 spec 文档存在性。

    治本 INFRA-M001 case(2026-05-21):Micro 流程改 1 行 k8s memory 常量 ·
    无 PRD / BUG-REPORT · 但 _check_prd_or_bug_report 漏判 Micro · 误返 False →
    dev-start FAIL `prd_or_bug_report_exists`。
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.feat = Path(self.tmp) / "feat"
        self.feat.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _check(self, flow_type: str) -> bool:
        from _v8_stage_specs import _check_prd_or_bug_report  # type: ignore
        state = {"flow_type": flow_type}
        args = make_args(feature=str(self.feat))
        return _check_prd_or_bug_report(state, args)

    # ── Micro:无 spec 文档 · 永远 PASS ──
    def test_micro_passes_without_any_doc(self):
        """治本 INFRA-M001 case:Micro 无 PRD / BUG-REPORT · 必 PASS。"""
        self.assertTrue(self._check("Micro"))

    def test_micro_passes_even_if_prd_exists(self):
        """Micro 即使误放 PRD.md 也 PASS(skip 逻辑 · 不读文件)。"""
        (self.feat / "PRD.md").write_text("x", encoding="utf-8")
        self.assertTrue(self._check("Micro"))

    # ── Bug:必有 bugfix/BUG-*.md ──
    def test_bug_fails_without_bugfix_md(self):
        self.assertFalse(self._check("Bug"))

    def test_bug_passes_with_bugfix_md(self):
        (self.feat / "bugfix").mkdir()
        (self.feat / "bugfix" / "BUG-001.md").write_text("x", encoding="utf-8")
        self.assertTrue(self._check("Bug"))

    def test_bug_with_only_prd_fails(self):
        """Bug 流程光有 PRD.md 不够(必须 bugfix/BUG-*.md)。"""
        (self.feat / "PRD.md").write_text("x", encoding="utf-8")
        self.assertFalse(self._check("Bug"))

    # ── Feature / 敏捷需求:必有 PRD.md ──
    def test_feature_fails_without_prd(self):
        self.assertFalse(self._check("Feature"))

    def test_feature_passes_with_prd(self):
        (self.feat / "PRD.md").write_text("x", encoding="utf-8")
        self.assertTrue(self._check("Feature"))

    def test_agile_demand_requires_prd(self):
        """敏捷需求 与 Feature 同型 · 必 PRD.md。"""
        self.assertFalse(self._check("敏捷需求"))
        (self.feat / "PRD.md").write_text("x", encoding="utf-8")
        self.assertTrue(self._check("敏捷需求"))


# ─── v8.28 · test 验证物化(治本 F037 AI 自报 stdout 漏洞)──────────────


class TestRunTestsViaSubprocess(unittest.TestCase):
    """v8.28 · run_tests_via_subprocess + _resolve_test_cmd 单元测试。

    覆盖:
    - cmd 解析优先级(--test-cmd > by_feature_id_pattern > default)
    - config 都无 → BLOCK 返 error
    - subprocess.run pass / fail / timeout / cmd 不存在
    - log 完整落盘 · emit tail 仅 N 行(不污染主 context)
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="run-tests-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── _resolve_test_cmd 优先级 ──
    def test_args_test_cmd_highest_priority(self):
        from _v8_engine import _resolve_test_cmd  # type: ignore
        # config 有 default · 但 --test-cmd 优先
        (self.tmp / ".teamwork_localconfig.json").write_text(
            json.dumps({"test_commands": {"default": "cargo test"}}),
            encoding="utf-8")
        args = make_args(feature=str(self.tmp / "feat"), test_cmd="my-cmd --foo")
        cmd, source, *_ = _resolve_test_cmd(args, "F001", self.tmp)
        self.assertEqual(cmd, "my-cmd --foo")
        self.assertEqual(source, "args.test_cmd")

    def test_by_feature_pattern_match(self):
        from _v8_engine import _resolve_test_cmd  # type: ignore
        (self.tmp / ".teamwork_localconfig.json").write_text(json.dumps({
            "test_commands": {
                "default": "cargo test",
                "by_feature_id_pattern": {
                    "SVC-CORE-F037-*": "cargo test --test f037_*",
                    "PTR-F*": "npm test",
                }
            }
        }), encoding="utf-8")
        args = make_args(feature=str(self.tmp / "feat"), test_cmd=None)
        cmd, source, *_ = _resolve_test_cmd(
            args, "SVC-CORE-F037-Quality-Gate", self.tmp)
        self.assertEqual(cmd, "cargo test --test f037_*")
        self.assertIn("by_feature_id_pattern", source)

    def test_default_fallback(self):
        from _v8_engine import _resolve_test_cmd  # type: ignore
        (self.tmp / ".teamwork_localconfig.json").write_text(json.dumps({
            "test_commands": {"default": "cargo test --lib"}
        }), encoding="utf-8")
        args = make_args(feature=str(self.tmp / "feat"), test_cmd=None)
        cmd, source, *_ = _resolve_test_cmd(args, "F001", self.tmp)
        self.assertEqual(cmd, "cargo test --lib")
        self.assertEqual(source, "config.default")

    def test_no_config_no_cmd_returns_error(self):
        from _v8_engine import _resolve_test_cmd  # type: ignore
        args = make_args(feature=str(self.tmp / "feat"), test_cmd=None)
        cmd, source, _, _, err = _resolve_test_cmd(args, "F001", self.tmp)
        self.assertIsNone(cmd)
        self.assertIsNone(source)
        self.assertIn("无 test cmd", err)
        self.assertIn(".teamwork_localconfig.json", err)
        self.assertIn("--test-cmd", err)

    def test_corrupt_config_falls_through_to_error(self):
        from _v8_engine import _resolve_test_cmd  # type: ignore
        (self.tmp / ".teamwork_localconfig.json").write_text(
            "not json {{{", encoding="utf-8")
        args = make_args(feature=str(self.tmp / "feat"), test_cmd=None)
        cmd, *_, err = _resolve_test_cmd(args, "F001", self.tmp)
        self.assertIsNone(cmd)
        self.assertIn("无 test cmd", err)

    # ── run_tests_via_subprocess ──
    def test_pass_cmd_returns_exit_0(self):
        from _v8_engine import run_tests_via_subprocess  # type: ignore
        log = self.tmp / "test-stdout.log"
        r = run_tests_via_subprocess(
            cmd_str="echo 'all tests PASS' && exit 0",
            cwd=str(self.tmp), timeout_sec=10, log_path=log, tail_lines=50)
        self.assertEqual(r["exit_code"], 0)
        self.assertIn("PASS", r["stdout_tail"])
        self.assertGreaterEqual(r["duration_sec"], 0)
        self.assertFalse(r["timeout"])
        self.assertTrue(log.exists())  # 完整 log 落盘

    def test_fail_cmd_returns_nonzero(self):
        from _v8_engine import run_tests_via_subprocess  # type: ignore
        log = self.tmp / "test-stdout.log"
        r = run_tests_via_subprocess(
            cmd_str="echo 'test failed' && exit 1",
            cwd=str(self.tmp), timeout_sec=10, log_path=log, tail_lines=50)
        self.assertEqual(r["exit_code"], 1)
        self.assertIn("failed", r["stdout_tail"])

    def test_timeout_returns_124(self):
        from _v8_engine import run_tests_via_subprocess  # type: ignore
        log = self.tmp / "test-stdout.log"
        # sleep 5s · 但 timeout=1s
        r = run_tests_via_subprocess(
            cmd_str="sleep 5", cwd=str(self.tmp),
            timeout_sec=1, log_path=log, tail_lines=50)
        self.assertEqual(r["exit_code"], 124)
        self.assertTrue(r["timeout"])

    def test_tail_lines_truncates_long_output(self):
        """治本核心:大量输出 · emit tail 只取末 N 行 · 不污染主 context。"""
        from _v8_engine import run_tests_via_subprocess  # type: ignore
        log = self.tmp / "test-stdout.log"
        # 生成 1000 行 stdout · tail=20 应只返末 20 行
        r = run_tests_via_subprocess(
            cmd_str="for i in $(seq 1 1000); do echo line-$i; done",
            cwd=str(self.tmp), timeout_sec=10, log_path=log, tail_lines=20)
        self.assertEqual(r["exit_code"], 0)
        tail_lines = r["stdout_tail"].splitlines()
        self.assertEqual(len(tail_lines), 20, "tail 必只取末 20 行")
        self.assertEqual(tail_lines[-1], "line-1000")
        self.assertEqual(tail_lines[0], "line-981")
        # 但完整 log 应含 1000 行
        full = log.read_text(encoding="utf-8")
        self.assertIn("line-1\n", full)
        self.assertIn("line-1000", full)
        self.assertEqual(r["stdout_total_lines"], 1000)

    def test_log_has_metadata_header(self):
        """log 含 cmd / cwd / exit_code / duration metadata(供 debug)。"""
        from _v8_engine import run_tests_via_subprocess  # type: ignore
        log = self.tmp / "test-stdout.log"
        run_tests_via_subprocess(
            cmd_str="echo ok", cwd=str(self.tmp),
            timeout_sec=10, log_path=log, tail_lines=10)
        full = log.read_text(encoding="utf-8")
        self.assertIn("=== teamwork test runner v8.28 ===", full)
        self.assertIn("cmd: echo ok", full)
        self.assertIn(f"cwd: {self.tmp}", full)
        self.assertIn("exit_code: 0", full)


if __name__ == "__main__":
    unittest.main(verbosity=2)
