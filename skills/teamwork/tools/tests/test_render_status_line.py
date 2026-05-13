#!/usr/bin/env python3
"""render-status-line.py 回归套件 · scripts-policy R-SP-6 render-first 物化。"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
SCRIPT = TOOLS / "render-status-line.py"


def run(args: list[str], expect_exit: int = 0) -> tuple[str, dict]:
    """返回 (stdout, stderr_audit_json)。失败时尝试 parse stderr 为 JSON。"""
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == expect_exit, (
        f"exit {r.returncode} ≠ {expect_exit}\n"
        f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    )
    try:
        audit = json.loads(r.stderr) if r.stderr.strip() else {}
    except json.JSONDecodeError:
        raise AssertionError(
            f"stderr 非 JSON (R-SP-4 违反)\nstderr:\n{r.stderr}"
        )
    return r.stdout, audit


class TestFeatureFlow(unittest.TestCase):
    def test_full_feature_with_worktree(self) -> None:
        out, audit = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "dev",
            "--next-step", "等用户确认 TC",
            "--feature", "F042-用户头像",
            "--path", "/abs/feature",
            "--branch", "feature/F042",
            "--merge-target", "main",
            "--worktree-path", "/abs/wt",
        ])
        lines = out.strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith("🔄 Teamwork 模式 |"))
        self.assertIn("流程：Feature", lines[0])
        self.assertIn("角色：PMO", lines[0])
        self.assertIn("功能：F042-用户头像", lines[0])
        self.assertIn("阶段：开发中", lines[0])
        self.assertIn("下一步：等用户确认 TC", lines[0])
        self.assertEqual(lines[1], "📁 /abs/feature")
        self.assertEqual(
            lines[2],
            "🌿 分支：feature/F042 → main | worktree：/abs/wt",
        )
        # audit
        self.assertEqual(audit["verdict"], "OK")
        self.assertEqual(audit["tool"], "render-status-line.py")
        self.assertEqual(audit["rendered_lines"], 3)
        self.assertEqual(audit["params"]["flow"], "Feature")

    def test_feature_without_worktree_shows_warning(self) -> None:
        out, _ = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "dev",
            "--next-step", "x", "--feature", "F042",
            "--branch", "feature/F042", "--merge-target", "main",
        ])
        # 📍 with worktree warning
        self.assertIn("📍 当前分支：feature/F042 → main", out)
        self.assertIn("未启用 worktree", out)

    def test_auto_mode_badge(self) -> None:
        out, _ = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "dev",
            "--next-step", "x", "--feature", "F042", "--auto-mode",
        ])
        self.assertIn("⚡ AUTO", out.split("\n")[0])

    def test_ext_model_badge(self) -> None:
        out, _ = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "review",
            "--next-step", "x", "--feature", "F042", "--ext-model", "codex",
        ])
        self.assertIn("🌐 Ext: codex", out.split("\n")[0])

    def test_stage_text_override(self) -> None:
        out, audit = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "goal_plan",
            "--next-step", "x", "--feature", "F042",
            "--stage-text", "⏸️ PRD 待确认",
        ])
        self.assertIn("阶段：⏸️ PRD 待确认", out)
        self.assertEqual(audit["stage_semantic"], "⏸️ PRD 待确认")


class TestBugFlow(unittest.TestCase):
    def test_bug_field(self) -> None:
        out, _ = run([
            "--flow", "Bug", "--role", "RD", "--stage", "dev",
            "--next-step", "修复中", "--bug", "BUG-007-登录失败",
        ])
        self.assertIn("Bug：BUG-007-登录失败", out)
        self.assertNotIn("功能：", out)


class TestMicroFlow(unittest.TestCase):
    def test_micro_uses_feature_field(self) -> None:
        out, _ = run([
            "--flow", "Micro", "--role", "RD", "--stage", "dev",
            "--next-step", "改文案", "--feature", "Micro-按钮文案",
            "--branch", "main",
        ])
        self.assertIn("功能：Micro-按钮文案", out)
        # Micro w/o worktree → 📍 + Micro warning
        self.assertIn("📍 当前分支：main", out)
        self.assertIn("Micro 直接改主分支", out)


class TestPlanningFlow(unittest.TestCase):
    def test_no_feature_required(self) -> None:
        out, _ = run([
            "--flow", "Feature Planning", "--role", "PMO", "--stage", "triage",
            "--next-step", "讨论 Roadmap",
        ])
        # 无功能/Bug 字段
        self.assertNotIn("功能：", out)
        self.assertNotIn("Bug：", out)


class TestValidationFailures(unittest.TestCase):
    def test_invalid_flow(self) -> None:
        _, audit = run([
            "--flow", "FeatureX", "--role", "PMO", "--stage", "dev",
            "--next-step", "x",
        ], expect_exit=2)
        self.assertEqual(audit["verdict"], "FAIL")
        self.assertIn("flow=", audit["error"])
        self.assertIn("valid_enum", audit)

    def test_invalid_role(self) -> None:
        _, audit = run([
            "--flow", "Feature", "--role", "Architect2", "--stage", "dev",
            "--next-step", "x", "--feature", "F042",
        ], expect_exit=2)
        self.assertIn("role=", audit["error"])

    def test_invalid_stage(self) -> None:
        _, audit = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "developing",
            "--next-step", "x", "--feature", "F042",
        ], expect_exit=2)
        self.assertIn("stage='developing'", audit["error"])
        self.assertIn("STATUS-LINE.md", audit["cite"])

    def test_feature_flow_missing_feature(self) -> None:
        _, audit = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "dev",
            "--next-step", "x",
        ], expect_exit=2)
        self.assertIn("--feature", audit["error"])

    def test_bug_flow_missing_bug(self) -> None:
        _, audit = run([
            "--flow", "Bug", "--role", "RD", "--stage", "dev",
            "--next-step", "x",
        ], expect_exit=2)
        self.assertIn("--bug", audit["error"])

    def test_relative_path_rejected(self) -> None:
        _, audit = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "dev",
            "--next-step", "x", "--feature", "F042",
            "--path", "docs/features/F042",
        ], expect_exit=2)
        self.assertIn("绝对路径", audit["error"])

    def test_worktree_path_without_branch(self) -> None:
        _, audit = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "dev",
            "--next-step", "x", "--feature", "F042",
            "--worktree-path", "/abs/wt",
        ], expect_exit=2)
        self.assertIn("--worktree-path", audit["error"])
        self.assertIn("--branch", audit["error"])

    def test_empty_next_step(self) -> None:
        _, audit = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "dev",
            "--next-step", "   ", "--feature", "F042",
        ], expect_exit=2)
        self.assertIn("next-step", audit["error"])

    def test_invalid_ext_model(self) -> None:
        _, audit = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "dev",
            "--next-step", "x", "--feature", "F042", "--ext-model", "gpt4",
        ], expect_exit=2)
        self.assertIn("ext-model=", audit["error"])


class TestFeatureContextAutoFill(unittest.TestCase):
    """v7.3.10+P0-144：state.json auto-fill 降低 PMO 调用负担。"""

    def setUp(self) -> None:
        import json
        import os
        import shutil
        import tempfile
        self.tmp = Path(tempfile.mkdtemp(prefix="rsl_ctx_"))
        self.feature_dir = self.tmp / "auth" / "docs" / "features" / "F042"
        self.feature_dir.mkdir(parents=True)
        state = {
            "feature_id": "AUTH-F042-test",
            "flow_type": "Feature",
            "current_stage": "dev",
            "worktree": {
                "path": "/abs/.worktree/AUTH-F042-test",
                "branch": "feature/AUTH-F042-test",
            },
            "merge_target": "staging",
            "external_cross_review": {"model": None},
        }
        (self.feature_dir / "state.json").write_text(
            json.dumps(state), encoding="utf-8"
        )
        self._json = json
        self._os = os
        self._shutil = shutil

    def tearDown(self) -> None:
        self._shutil.rmtree(self.tmp, ignore_errors=True)
        self._os.environ.pop("TEAMWORK_FEATURE", None)

    def test_auto_fill_via_feature_dir(self) -> None:
        """显式 --feature-dir · 不传 flow/stage/feature/path/branch/merge-target/worktree-path 7 字段 → 全部自动填。"""
        out, audit = run([
            "--role", "PMO", "--next-step", "等用户确认 TC",
            "--feature-dir", str(self.feature_dir),
        ])
        lines = out.strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("流程：Feature", lines[0])
        self.assertIn("功能：AUTH-F042-test", lines[0])
        self.assertIn("阶段：开发中", lines[0])
        self.assertIn("📁", lines[1])
        self.assertIn("🌿 分支：feature/AUTH-F042-test → staging", lines[2])
        # audit context 信息
        self.assertIn("feature_context", audit)
        self.assertEqual(audit["feature_context"]["feature_id"], "AUTH-F042-test")
        self.assertEqual(audit["feature_context"]["discovery_source"], "explicit")

    def test_auto_fill_via_env_var(self) -> None:
        self._os.environ["TEAMWORK_FEATURE"] = str(self.feature_dir)
        out, audit = run([
            "--role", "PMO", "--next-step", "等用户确认 TC",
        ])
        self.assertIn("流程：Feature", out)
        self.assertEqual(audit["feature_context"]["discovery_source"],
                         "env_TEAMWORK_FEATURE")

    def test_explicit_overrides_context(self) -> None:
        """显式 --flow 与 context flow_type 不同 → 用显式 · audit 记 override。"""
        out, audit = run([
            "--role", "PMO", "--next-step", "x",
            "--feature-dir", str(self.feature_dir),
            "--flow", "Bug", "--bug", "BUG-007-x",
            # Override flow + 不传 feature 让 auto-fill 走（但下面会被 Bug 流程覆盖）
        ])
        self.assertIn("流程：Bug", out)
        self.assertIn("overrides_from_context", audit)
        self.assertIn("flow", audit["overrides_from_context"])

    def test_no_context_flag_disables_autofill(self) -> None:
        """--no-context 时 · 即使 TEAMWORK_FEATURE 设了也不读 · 仍走显式参数（缺则 fail）。"""
        self._os.environ["TEAMWORK_FEATURE"] = str(self.feature_dir)
        _, audit = run([
            "--role", "PMO", "--next-step", "x", "--no-context",
            # 不传 --flow → 缺 → fail
        ], expect_exit=2)
        self.assertIn("--flow 未提供", audit["error"])


class TestSpecSyncMeta(unittest.TestCase):
    """v7.3.10+P0-142：保证 STATUS-LINE.md 中残留的引用与工具实现一致。

    防漂移：STATUS-LINE.md 删去了格式 / enum 表正文 · 必须保留指向工具的指针。
    """

    SKILL_ROOT = TOOLS.parent
    STATUS_LINE_MD = SKILL_ROOT / "STATUS-LINE.md"
    POLICY_MD = SKILL_ROOT / "standards" / "scripts-policy.md"

    def test_status_line_md_cites_tool(self) -> None:
        """STATUS-LINE.md 必须含指向 render-status-line.py 的指针 ≥1 次。"""
        text = self.STATUS_LINE_MD.read_text(encoding="utf-8")
        self.assertIn(
            "tools/render-status-line.py", text,
            "STATUS-LINE.md 缺工具指针 · R-SP-6 单源链路断裂",
        )

    def test_status_line_md_no_old_enum_table(self) -> None:
        """STATUS-LINE.md 不应再含被工具持有的 enum 表大段（A 类）。"""
        text = self.STATUS_LINE_MD.read_text(encoding="utf-8")
        # 旧 enum 表标志：连续多行 "├── triage" / "├── goal_plan" 等列举
        old_table_signature = "├── triage              → "
        self.assertNotIn(
            old_table_signature, text,
            "STATUS-LINE.md 残留旧 enum 表 · 应改为指向工具 · 详 P0-142",
        )

    def test_status_line_md_no_format_block(self) -> None:
        """STATUS-LINE.md 不应再含状态行格式完整定义块（A 类）。"""
        text = self.STATUS_LINE_MD.read_text(encoding="utf-8")
        # 旧 format block 标志：列举所有徽章规则
        old_block = "🔴 ⚡ AUTO 徽章（v7.3.9+P0-11 新增）"
        self.assertNotIn(
            old_block, text,
            "STATUS-LINE.md 残留旧格式定义块 · 应由工具持单源 · 详 P0-142",
        )

    def test_scripts_policy_lists_status_line_stage(self) -> None:
        """scripts-policy.md 当前阶段速查必须含 render-status-line.py 条目。"""
        text = self.POLICY_MD.read_text(encoding="utf-8")
        self.assertIn("当前阶段速查", text)
        self.assertIn("render-status-line.py", text)
        self.assertIn("第二阶段", text)


class TestEmojiSpacing(unittest.TestCase):
    """STATUS-LINE.md L66 emoji 间距硬规则 · 工具必须保证。"""

    def test_path_emoji_has_space(self) -> None:
        out, _ = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "dev",
            "--next-step", "x", "--feature", "F042",
            "--path", "/abs/x",
        ])
        # 📁 后必须有 1 个半角空格
        self.assertIn("📁 /abs/x", out)
        self.assertNotIn("📁/abs", out)

    def test_branch_emoji_has_space(self) -> None:
        out, _ = run([
            "--flow", "Feature", "--role", "PMO", "--stage", "dev",
            "--next-step", "x", "--feature", "F042",
            "--branch", "feature/F042", "--merge-target", "main",
            "--worktree-path", "/abs/wt",
        ])
        self.assertIn("🌿 分支：", out)
        self.assertNotIn("🌿分支", out)


if __name__ == "__main__":
    unittest.main()
