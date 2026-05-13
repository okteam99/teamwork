#!/usr/bin/env python3
"""
render-decision-pause.py — HITL 决策类暂停点 render-first 物化（v7.3.10+P0-143）

替代 spec 教 AI "怎么写 ⏸️ 决策暂停块" → 工具持单源 · AI 传参 · 工具回吐：
- 📚 决策参考块（强制 N 条绝对路径 · cite STATUS-LINE.md 决策类清单）
- 决策菜单（编号 + 💡 推荐 + 末项「其他指示」）

权威源：[STATUS-LINE.md § 决策类暂停点清单](../STATUS-LINE.md) 10 类。

用法：
    python3 tools/render-decision-pause.py \\
      --decision-class 6 \\
      --pause-point "PM 验收三选项" \\
      --refs /abs/PRD.md,/abs/TC.md,/abs/test-report.md \\
      --options "1=通过+Ship,2=通过不Ship,3=不通过+建议" \\
      --recommended 1

退出码：
- 0 OK · stdout = 多行决策暂停块
- 2 FAIL · 参数非法 / refs 非绝对路径 / recommended 不在 options 编号 / decision-class 不在 1-10
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

TOOL_VERSION = "v1.0"
TOOL_NAME = "render-decision-pause.py"

# STATUS-LINE.md § 决策类暂停点清单 10 类 · 含每类期望的 ref 关键词（substring 匹配）
DECISION_CLASSES: dict[int, dict[str, Any]] = {
    1: {
        "name": "Review Stage QUALITY_ISSUE 决策（A/B/C/D 修哪些 finding）",
        "expected_refs": ["REVIEW.md", "代码文件", "测试文件"],
    },
    2: {
        "name": "PRD 评审 verdict（PASS / NEEDS_REVISION / 用户对 finding 处理）",
        "expected_refs": ["PRD.md", "PRD-REVIEW.md"],
    },
    3: {
        "name": "流程类型识别歧义（Bug 升级 / Micro 升级 / 多候选）",
        "expected_refs": ["BUG-REPORT.md", "用户原始消息", "准入条件"],
    },
    4: {
        "name": "评审组合智能推荐用户改选",
        "expected_refs": ["roles/pmo.md", "PRD-REVIEW.md"],
    },
    5: {
        "name": "PL-PM 业务方向分歧（discuss）",
        "expected_refs": ["PRD-REVIEW.md", "product-overview.md", "ADR"],
    },
    6: {
        "name": "PM 验收三选项",
        "expected_refs": ["PRD.md", "TC.md", "测试报告"],
    },
    7: {
        "name": "Stage 入口偏差判定",
        "expected_refs": ["state.json", "上一 Stage 产物"],
    },
    8: {
        "name": "升级确认（Micro → 敏捷 / Bug 简单 → Bug 复杂 / 敏捷 → Feature）",
        "expected_refs": ["准入条件", "升级 finding"],
    },
    9: {
        "name": "ADR 候选方案选择",
        "expected_refs": ["ADR", "候选方案"],
    },
    10: {
        "name": "技术评审分歧（Blueprint Stage TECH 评审 NEEDS_REVISION）",
        "expected_refs": ["TECH.md", "TECH-REVIEW.md", "ARCHITECTURE.md"],
    },
}


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


def audit(rendered: str, args: argparse.Namespace, refs: list[str],
          options: list[tuple[int, str]]) -> None:
    payload = {
        "verdict": "OK",
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "rendered_chars": len(rendered),
        "decision_class": args.decision_class,
        "class_name": DECISION_CLASSES[args.decision_class]["name"],
        "refs_count": len(refs),
        "options_count": len(options),
        "recommended": args.recommended,
        "params": {
            "pause_point": args.pause_point,
            "refs": refs,
            "raw_options": args.options,
        },
        "rendered_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)


def parse_options(raw: str) -> list[tuple[int, str]]:
    """解析 '1=A,2=B,3=C' → [(1,'A'),(2,'B'),(3,'C')]。"""
    out: list[tuple[int, str]] = []
    seen: set[int] = set()
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            fail(f"option '{item}' 缺 '=' · 格式应为 'N=描述'",
                 cite="STATUS-LINE.md § 暂停点编号规范 R5(b)")
        num_str, _, text = item.partition("=")
        num_str = num_str.strip()
        text = text.strip()
        if not num_str.isdigit():
            fail(f"option 编号 '{num_str}' 非数字",
                 cite="STATUS-LINE.md § 暂停点编号规范 · 禁止 ①②③")
        n = int(num_str)
        if n in seen:
            fail(f"option 编号 {n} 重复",
                 cite="STATUS-LINE.md § 暂停点编号规范")
        if not text:
            fail(f"option {n} 描述不可为空")
        seen.add(n)
        out.append((n, text))
    if not out:
        fail("--options 必须含至少 1 条 · 格式 '1=A,2=B,...'",
             cite="STATUS-LINE.md § 暂停点编号规范")
    # 编号必须从 1 连续递增
    nums = [n for n, _ in out]
    if nums != list(range(1, len(nums) + 1)):
        fail(f"option 编号不连续递增（实际 {nums}）· 必须 1/2/3/...",
             cite="STATUS-LINE.md § 暂停点编号规范")
    return out


def validate(args: argparse.Namespace) -> tuple[list[str], list[tuple[int, str]]]:
    if args.decision_class not in DECISION_CLASSES:
        fail(
            f"decision-class={args.decision_class} 不在 1-10",
            cite="STATUS-LINE.md § 决策类暂停点清单 L169-190",
            valid_classes={k: v["name"] for k, v in DECISION_CLASSES.items()},
        )
    if not args.pause_point.strip():
        fail("--pause-point 必填")

    # refs 校验：逗号分隔 · 全部必须绝对路径
    refs = [r.strip() for r in args.refs.split(",") if r.strip()]
    if not refs:
        fail(
            "--refs 必填 · 至少 1 条绝对路径",
            cite="STATUS-LINE.md § 决策点参考文档绝对路径硬规则",
        )
    for r in refs:
        if not r.startswith("/"):
            fail(
                f"ref '{r}' 必须绝对路径（以 / 开头）",
                cite="STATUS-LINE.md L60 + 决策点参考绝对路径硬规则",
            )

    # 期望 ref 类型 educational check（不强阻断 · 命中数 < 期望数时 hint）
    expected = DECISION_CLASSES[args.decision_class]["expected_refs"]
    matched_expected = [
        e for e in expected
        if any(e.lower() in r.lower() for r in refs)
    ]
    # 若 0 命中 expected · 直接 fail（refs 类型与 class 完全不符）
    if expected and not matched_expected:
        fail(
            f"refs 未命中任何期望类型（class {args.decision_class}）",
            cite=f"STATUS-LINE.md § 决策类暂停点清单 类{args.decision_class}",
            expected_ref_keywords=expected,
            actual_refs=refs,
            hint="确认 --decision-class 是否选对 · 或补 refs",
        )

    options = parse_options(args.options)
    if args.recommended not in [n for n, _ in options]:
        fail(
            f"--recommended={args.recommended} 不在 options 编号 {[n for n, _ in options]}",
            cite="STATUS-LINE.md § 暂停点编号规范 · 💡 推荐项",
        )
    return refs, options


def render(args: argparse.Namespace, refs: list[str],
           options: list[tuple[int, str]]) -> str:
    lines: list[str] = []
    lines.append(f"⏸️ {args.pause_point.strip()}")
    lines.append("")
    lines.append("📚 决策参考：")
    for r in refs:
        lines.append(f"- {r}")
    lines.append("")
    if args.narrative:
        lines.append(args.narrative.strip())
        lines.append("")
    lines.append("请选（回数字）：")
    has_other = any("其他指示" in text or "其他" == text.strip()
                    for _, text in options)
    for n, text in options:
        if n == args.recommended:
            lines.append(f"{n}. 💡 {text}（推荐）")
        else:
            lines.append(f"{n}. {text}")
    if not has_other:
        last_n = options[-1][0] + 1
        lines.append(f"{last_n}. 其他指示")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(
        prog="render-decision-pause.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--decision-class", type=int, required=True,
                   help="决策类暂停点 1-10（cite STATUS-LINE.md § 决策类暂停点清单）")
    p.add_argument("--pause-point", required=True, help="暂停点名称")
    p.add_argument("--refs", required=True,
                   help="决策参考绝对路径 · 逗号分隔（如 /abs/PRD.md,/abs/TC.md）")
    p.add_argument("--options", required=True,
                   help="决策菜单 · 格式 '1=A,2=B,3=C' · 末项「其他指示」自动补")
    p.add_argument("--recommended", type=int, required=True,
                   help="💡 推荐项编号（须在 options 编号中）")
    p.add_argument("--narrative",
                   help="可选自由文本段（暂停点上下文说明 · 在 📚 后、菜单前）")
    args = p.parse_args()

    refs, options = validate(args)
    rendered = render(args, refs, options)
    print(rendered)
    audit(rendered, args, refs, options)


if __name__ == "__main__":
    main()
