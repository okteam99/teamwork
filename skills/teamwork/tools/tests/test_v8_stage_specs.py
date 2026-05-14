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


# ─── Bug 2 · _evidence_ac_test_binding 诊断 ─────────────────────


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
