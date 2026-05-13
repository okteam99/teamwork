#!/usr/bin/env python3
"""
render-status-line.py — Teamwork 状态行 render-first 物化（v7.3.10+P0-141）

替代 spec 教 AI "怎么写状态行" → 工具持单源 · AI 传参 · 工具回吐合规输出。

规范：
- [standards/scripts-policy.md § R-SP-6](../standards/scripts-policy.md) render-first 原则
- [STATUS-LINE.md § 状态行格式定义](../STATUS-LINE.md) 单源约束

用法（最小）：
    python3 tools/render-status-line.py \\
      --flow Feature --role PMO --stage dev \\
      --next-step "等用户确认 TC 评审"

用法（含路径 / 分支 / worktree）：
    python3 tools/render-status-line.py \\
      --flow Feature --role PMO --stage dev \\
      --next-step "等用户确认 TC 评审" \\
      --feature "F042-用户头像" \\
      --path /abs/feature/dir \\
      --branch feature/F042 --merge-target main \\
      --worktree-path /abs/worktree

用法（auto 模式 + 外部模型）：
    python3 tools/render-status-line.py ... --auto-mode --ext-model codex

退出码（R-SP-5）：
- 0 OK · stdout = 合规状态行（多行 · AI 直接 cite 进 final response）· stderr = audit JSON
- 2 FAIL · 参数非法 · stderr JSON 含 error + cite spec hint
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

TOOL_VERSION = "v1.0"
TOOL_NAME = "render-status-line.py"

# Spec enums · 单源 cite STATUS-LINE.md § 阶段对照表 + SKILL.md 六种流程 + ROLES.md
FLOW_ENUM = [
    "Feature", "敏捷需求", "Bug", "Micro", "问题排查", "Feature Planning",
]
ROLE_ENUM = ["PMO", "PM", "Designer", "QA", "RD", "Architect", "PL"]
STAGE_ENUM = [
    "triage", "goal_plan", "ui_design", "blueprint", "dev", "review",
    "test", "browser_e2e", "pm_acceptance", "ship", "completed",
]
# STATUS-LINE.md L141-152 阶段语义映射
STAGE_SEMANTIC_DEFAULT = {
    "triage": "需求理解中",
    "goal_plan": "PRD 起草中",
    "ui_design": "UI 设计中",
    "blueprint": "Blueprint 中",
    "dev": "开发中",
    "review": "三视角并行审查",
    "test": "集成测试中",
    "browser_e2e": "Browser E2E 中",
    "pm_acceptance": "⏸️ PM 验收",
    "ship": "Ship 中",
    "completed": "✅ 已完成",
}
# 需要功能 / Bug 标识的流程
FLOW_REQUIRES_FEATURE = {"Feature", "敏捷需求", "Micro"}
FLOW_REQUIRES_BUG = {"Bug"}


def fail(error: str, cite: str = "", **extra: Any) -> None:
    payload: dict[str, Any] = {
        "verdict": "FAIL",
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "error": error,
    }
    if cite:
        payload["cite"] = cite
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(2)


def audit(stage_text: str, lines: list[str], args: argparse.Namespace) -> None:
    payload = {
        "verdict": "OK",
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "rendered_lines": len(lines),
        "stage_semantic": stage_text,
        "params": {
            "flow": args.flow,
            "role": args.role,
            "stage": args.stage,
            "next_step": args.next_step,
            "feature": args.feature,
            "bug": args.bug,
            "auto_mode": args.auto_mode,
            "ext_model": args.ext_model,
            "has_path": bool(args.path),
            "has_branch": bool(args.branch),
            "has_worktree": bool(args.worktree_path),
        },
        "rendered_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)


def validate(args: argparse.Namespace) -> None:
    if args.flow not in FLOW_ENUM:
        fail(
            f"flow='{args.flow}' 不在 enum",
            cite="SKILL.md 六种标准流程",
            valid_enum=FLOW_ENUM,
        )
    if args.role not in ROLE_ENUM:
        fail(
            f"role='{args.role}' 不在 enum",
            cite="ROLES.md / roles/*.md",
            valid_enum=ROLE_ENUM,
        )
    if args.stage not in STAGE_ENUM:
        fail(
            f"stage='{args.stage}' 不在 enum",
            cite="STATUS-LINE.md § 阶段对照表 L141-152",
            valid_enum=STAGE_ENUM,
        )
    if not args.next_step or not args.next_step.strip():
        fail("--next-step 必填 · 不可为空",
             cite="STATUS-LINE.md § 状态行格式定义 第一行")
    if args.flow in FLOW_REQUIRES_FEATURE and not args.feature:
        fail(
            f"flow='{args.flow}' 必须提供 --feature（必填功能编号）",
            cite="STATUS-LINE.md L21-23 流程类型必填字段",
        )
    if args.flow in FLOW_REQUIRES_BUG and not args.bug:
        fail(
            f"flow='Bug' 必须提供 --bug（如 BUG-007-简述）",
            cite="STATUS-LINE.md L22 Bug 必填字段",
        )
    if args.path and not args.path.startswith("/"):
        fail(
            f"path='{args.path}' 必须是绝对路径（以 / 开头）",
            cite="STATUS-LINE.md L60 路径硬规则",
        )
    if args.worktree_path and not args.worktree_path.startswith("/"):
        fail(
            f"worktree-path='{args.worktree_path}' 必须是绝对路径",
            cite="STATUS-LINE.md L52 禁止 worktree.path 相对路径",
        )
    if args.worktree_path and not args.branch:
        fail("--worktree-path 必须配 --branch",
             cite="STATUS-LINE.md L41-48 第三行分支格式")
    # ext-model 仅在用户传 --ext-model 时校验值
    if args.ext_model and args.ext_model not in {"codex", "claude", "gemini"}:
        fail(
            f"ext-model='{args.ext_model}' 不在 enum",
            cite="STATUS-LINE.md L30-34 🌐 Ext 徽章",
            valid_enum=["codex", "claude", "gemini"],
        )


def render_line1(args: argparse.Namespace, stage_text: str) -> str:
    parts: list[str] = ["🔄 Teamwork 模式"]
    if args.auto_mode:
        parts.append("⚡ AUTO")
    if args.ext_model:
        parts.append(f"🌐 Ext: {args.ext_model}")
    head = " ".join(parts)

    fields: list[str] = [
        f"流程：{args.flow}",
        f"角色：{args.role}",
    ]
    if args.feature:
        fields.append(f"功能：{args.feature}")
    if args.bug:
        fields.append(f"Bug：{args.bug}")
    fields.extend([
        f"阶段：{stage_text}",
        f"下一步：{args.next_step.strip()}",
    ])
    return f"{head} | " + " | ".join(fields)


def render_line2(args: argparse.Namespace) -> str | None:
    if not args.path:
        return None
    # 路径边界硬规则：emoji + 半角空格 · 路径后 \n 边界
    return f"📁 {args.path}"


def render_line3(args: argparse.Namespace) -> str | None:
    if not args.branch:
        return None
    if args.worktree_path:
        # 🌿 启用 worktree
        if args.merge_target:
            return (f"🌿 分支：{args.branch} → {args.merge_target} | "
                    f"worktree：{args.worktree_path}")
        return f"🌿 分支：{args.branch} | worktree：{args.worktree_path}"
    # 📍 未启用 worktree
    if args.flow == "Micro":
        warn = "⚠️ Micro 直接改主分支，操作前确认工作区干净"
    elif args.flow in ("Feature Planning", "问题排查"):
        warn = "Planning 阶段不改代码，分支仅供参考"
    elif args.flow in ("Feature", "敏捷需求", "Bug"):
        warn = "⚠️ 未启用 worktree，并行 Feature 请注意隔离"
    else:
        warn = ""
    if args.merge_target:
        head = f"📍 当前分支：{args.branch} → {args.merge_target}"
    else:
        head = f"📍 当前分支：{args.branch}"
    return f"{head}（{warn}）" if warn else head


def main() -> None:
    p = argparse.ArgumentParser(
        prog="render-status-line.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--flow", required=True, help=f"流程类型 {FLOW_ENUM}")
    p.add_argument("--role", required=True, help=f"当前角色 {ROLE_ENUM}")
    p.add_argument("--stage", required=True,
                   help=f"state.current_stage enum 值 {STAGE_ENUM}")
    p.add_argument("--next-step", required=True, help="下一步事项（短句）")
    p.add_argument("--stage-text",
                   help="覆盖默认阶段语义文本（如 '⏸️ PRD 待确认'）· 不传则按 enum 默认映射")
    p.add_argument("--feature", help="功能编号-名（Feature/敏捷/Micro 必填）")
    p.add_argument("--bug", help="Bug 编号-简述（Bug 流程必填）")
    p.add_argument("--path", help="功能目录绝对路径")
    p.add_argument("--branch", help="当前分支名")
    p.add_argument("--merge-target", help="合并目标分支")
    p.add_argument("--worktree-path", help="worktree 绝对路径（启用 worktree 时）")
    p.add_argument("--auto-mode", action="store_true", help="AUTO_MODE=true 时加 ⚡ AUTO 徽章")
    p.add_argument("--ext-model", help="外部模型徽章 enum: codex|claude|gemini")
    args = p.parse_args()

    validate(args)
    stage_text = args.stage_text or STAGE_SEMANTIC_DEFAULT[args.stage]

    lines: list[str] = [render_line1(args, stage_text)]
    line2 = render_line2(args)
    if line2:
        lines.append(line2)
    line3 = render_line3(args)
    if line3:
        lines.append(line3)

    print("\n".join(lines))
    audit(stage_text, lines, args)


if __name__ == "__main__":
    main()
