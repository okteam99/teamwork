#!/usr/bin/env python3
"""
render-afk-skip.py — AFK auto skip 日志 render-first 物化（v7.3.10+P0-143）

替代 spec 教 AI "怎么写 ⚡ auto skip" → 工具持单源 · AI 传参 · 工具回吐合规输出。
治本本对话 case：AI 把 "auto 模式继续" 当用户投票 · 输出"视为通过"错措辞。

权威源：[roles/pmo-auto-mode.md § 三 AFK 暂停点](../roles/pmo-auto-mode.md)。

用法：
    python3 tools/render-afk-skip.py \\
      --pause-point "设计批待确认" \\
      --decision "通过 → Blueprint" \\
      --reason "Designer 自查 5 维度全 ✅ + 用户未提修订项"

退出码（与 scripts-policy.md R-SP-5 一致）：
- 0 OK · stdout = `⚡ auto skip: X | 💡 Y | 📝 Z`
- 2 FAIL · 参数非法 / pause-point 不在 AFK 清单 / 命中 HITL 清单（不应输出 auto skip）
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

TOOL_VERSION = "v1.0"
TOOL_NAME = "render-afk-skip.py"

# AFK 清单（pmo-auto-mode.md § 三）· canonical names · normalize 后 substring 匹配
AFK_PAUSE_POINTS = [
    "triage → Goal-Plan",
    "PRD 待确认",
    "设计批待确认",
    "方案待确认",
    "排查待确认",
    "Roadmap 待确认",
    "teamwork_space.md 待确认",
    "Workspace Planning 收尾",
    "精简 PRD 待确认",
    "Micro 分析 → PMO 执行改动",
    "外部依赖已就绪",
    "Test Stage → Browser E2E Stage",
]

# HITL 清单（flow-transitions.md § HITL · pmo-auto-mode.md § 五）
# 命中 HITL = 不应输出 auto skip · 工具直接 reject
HITL_PAUSE_POINTS = [
    "PM 验收",
    "worktree 清理待确认",
    "Ship Stage push FAILED",
    "Ship Stage 等待合并",
    "Ship Stage 第二段检测失败",
    "Ship Stage 异常处理",
    "Ship Stage 第二段 Step 6 pull",
    "Ship Stage 第二段 Step 8 push",
    "变更归属检查阻塞",
    "变更状态 planning → locked",
    "Goal-Plan Stage 评审组合决策",
    "Goal-Plan Stage 评审循环超",
    "Goal-Plan Stage 子步骤 5 用户最终确认",
    "Dev Stage 用户决策",
    "Review Stage FAILED",
    "Test Stage BLOCKED",
    "Goal-Plan Stage 分歧",
    "Blueprint Stage concerns",
    "Micro 流程 用户验收",
    "Micro 流程 升级确认",
    "Test Stage 前置确认",
]


def _normalize(s: str) -> str:
    return s.replace(" ", "").replace("　", "").lower()


def _match(target: str, candidates: list[str]) -> str | None:
    """双向 substring 匹配（容错空格 / 大小写）。"""
    t = _normalize(target)
    for c in candidates:
        nc = _normalize(c)
        if nc in t or t in nc:
            return c
    return None


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


def audit(rendered: str, args: argparse.Namespace, matched_afk: str) -> None:
    payload = {
        "verdict": "OK",
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "rendered_chars": len(rendered),
        "matched_afk_pause_point": matched_afk,
        "params": {
            "pause_point": args.pause_point,
            "decision": args.decision,
            "reason": args.reason,
        },
        "rendered_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)


def validate(args: argparse.Namespace) -> str:
    if not args.pause_point.strip():
        fail("--pause-point 必填",
             cite="pmo-auto-mode.md § 三 AFK 暂停点")
    if not args.decision.strip():
        fail("--decision 必填 · 描述按 💡 建议推进的结果",
             cite="pmo-auto-mode.md § 三 AFK 暂停点 · 豁免动作列")
    if not args.reason.strip():
        fail("--reason 必填 · auto skip 日志的可审计理由",
             cite="pmo-auto-mode.md § 三 AFK 暂停点 · 归类列")

    # HITL 检查优先（防把 HITL 暂停点误用 auto skip）
    hitl_match = _match(args.pause_point, HITL_PAUSE_POINTS)
    if hitl_match:
        fail(
            f"pause-point='{args.pause_point}' 命中 HITL 清单 ('{hitl_match}') · "
            "不应输出 auto skip · HITL 暂停点 auto 模式不豁免 · 必须等用户决策",
            cite="pmo-auto-mode.md § 五 HITL 暂停点 / flow-transitions.md § HITL 清单",
            hint="如确认是 AFK 暂停点 · 请用更精确的 --pause-point 命名 · 或先 cite 权威源确认归属",
        )

    afk_match = _match(args.pause_point, AFK_PAUSE_POINTS)
    if not afk_match:
        fail(
            f"pause-point='{args.pause_point}' 不在 AFK 清单",
            cite="pmo-auto-mode.md § 三 AFK 清单 L106-121",
            valid_afk_pause_points=AFK_PAUSE_POINTS,
            hint="若属新暂停点 · 先在 pmo-auto-mode.md § 三 加入 AFK 清单 + 同步 AFK_PAUSE_POINTS 常量",
        )
    return afk_match


def main() -> None:
    p = argparse.ArgumentParser(
        prog="render-afk-skip.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--pause-point", required=True,
                   help="AFK 暂停点名称（须在 pmo-auto-mode.md § 三 清单内）")
    p.add_argument("--decision", required=True,
                   help="按 💡 推荐项推进的具体决策（如 '通过 → Blueprint'）")
    p.add_argument("--reason", required=True,
                   help="auto skip 理由（可审计 · 不可为'auto 模式继续'等空洞描述）")
    args = p.parse_args()

    matched_afk = validate(args)
    rendered = (f"⚡ auto skip: {args.pause_point.strip()} | "
                f"💡 {args.decision.strip()} | "
                f"📝 {args.reason.strip()}")
    print(rendered)
    audit(rendered, args, matched_afk)


if __name__ == "__main__":
    main()
