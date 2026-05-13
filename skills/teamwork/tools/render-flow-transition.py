#!/usr/bin/env python3
"""
render-flow-transition.py — 阶段流转校验行 render-first 物化（v7.3.10+P0-143）

替代 spec 教 AI "怎么写 📋 阶段流转校验行" → 工具直接 read flow-transitions.md
找匹配行 → 输出含真实 L行号 + 原文 · 编造行号/原文不可能。

权威源：[rules/flow-transitions.md](../rules/flow-transitions.md) 阶段状态转移表。

用法：
    python3 tools/render-flow-transition.py --from "设计批 待确认" --to "Blueprint"

退出码（与 scripts-policy.md R-SP-5 一致）：
- 0 OK · stdout = `📋 {from} → {to}（📖 {🚀/⏸️/🔀}，来源：flow-transitions.md L{N} "{原文}"）`
- 2 FAIL · from/to 在转移表中未命中 / 多匹配歧义
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOL_VERSION = "v1.0"
TOOL_NAME = "render-flow-transition.py"

# flow-transitions.md 转移表行的识别：4 列管道分隔
# 格式：| {from} | {to} | {transition_type} | {note} |
# transition_type 含 🚀自动 / ⏸️暂停 / 🔀条件 / 组合（如 🚀自动 / 🔁回退）
ROW_RE = re.compile(
    r"^\|\s*(?P<from>[^|]+?)\s*\|\s*(?P<to>[^|]+?)\s*\|\s*"
    r"(?P<type>[^|]+?)\s*\|\s*(?P<note>[^|]+?)\s*\|\s*$"
)
# 表头分隔线（| --- | --- |）跳过
SEPARATOR_RE = re.compile(r"^\|\s*[-:]+\s*\|")


def _resolve_spec_path() -> Path:
    """优先用环境变量 TEAMWORK_SKILL_ROOT · 否则按相对位置定位。"""
    env_root = os.environ.get("TEAMWORK_SKILL_ROOT")
    if env_root:
        return Path(env_root) / "rules" / "flow-transitions.md"
    # 默认：本脚本在 tools/ · spec 在 ../rules/
    return Path(__file__).resolve().parent.parent / "rules" / "flow-transitions.md"


def _normalize(s: str) -> str:
    return s.replace(" ", "").replace("　", "").lower()


def _detect_type_icon(type_cell: str) -> str:
    """从 transition_type 字段提取主图标。"""
    if "🚀" in type_cell:
        return "🚀"
    if "⏸️" in type_cell:
        return "⏸️"
    if "🔀" in type_cell:
        return "🔀"
    return "❓"


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


def audit(matched_line_no: int, type_icon: str, args: argparse.Namespace,
          spec_path: Path) -> None:
    payload = {
        "verdict": "OK",
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "matched_line": matched_line_no,
        "type_icon": type_icon,
        "spec_path": str(spec_path),
        "params": {"from": args.from_, "to": args.to},
        "rendered_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)


def find_matches(spec_text: str, from_target: str, to_target: str
                 ) -> list[tuple[int, str, dict[str, str]]]:
    """返回 [(line_no, raw_line, parsed_groups)] 所有命中。"""
    matches: list[tuple[int, str, dict[str, str]]] = []
    from_n = _normalize(from_target)
    to_n = _normalize(to_target)
    for idx, line in enumerate(spec_text.splitlines(), start=1):
        if SEPARATOR_RE.match(line):
            continue
        m = ROW_RE.match(line)
        if not m:
            continue
        from_cell_n = _normalize(m.group("from"))
        to_cell_n = _normalize(m.group("to"))
        # 双向 substring 匹配（from / to 字段容错）
        from_hit = from_n in from_cell_n or from_cell_n in from_n
        to_hit = to_n in to_cell_n or to_cell_n in to_n
        if from_hit and to_hit:
            matches.append((idx, line, m.groupdict()))
    return matches


def main() -> None:
    p = argparse.ArgumentParser(
        prog="render-flow-transition.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--from", dest="from_", required=True,
                   help="起始阶段（必须能匹配 flow-transitions.md 表的 from 列）")
    p.add_argument("--to", required=True,
                   help="目标阶段（必须能匹配 to 列）")
    p.add_argument("--spec",
                   help="覆盖 flow-transitions.md 路径（测试用 · 默认按相对路径定位）")
    args = p.parse_args()

    spec_path = Path(args.spec) if args.spec else _resolve_spec_path()
    if not spec_path.exists():
        fail(f"flow-transitions.md 不存在: {spec_path}",
             cite="rules/flow-transitions.md",
             hint="export TEAMWORK_SKILL_ROOT=/abs/skill/path 或 --spec 覆盖")

    spec_text = spec_path.read_text(encoding="utf-8")
    matches = find_matches(spec_text, args.from_, args.to)

    if not matches:
        fail(
            f"未在 flow-transitions.md 找到匹配 '{args.from_}' → '{args.to}'",
            cite="rules/flow-transitions.md 阶段状态转移表",
            hint="先 cite 权威源确认转移合法性 · 不在表中 = 非法转移",
        )

    if len(matches) > 1:
        fail(
            f"匹配歧义：{len(matches)} 处命中",
            cite="rules/flow-transitions.md",
            ambiguous_lines=[ln for ln, _, _ in matches],
            hint="缩窄 --from / --to 关键词使匹配唯一",
        )

    line_no, raw_line, parsed = matches[0]
    type_icon = _detect_type_icon(parsed["type"])
    # 显示用的 from/to 取表格里的实际值（不是用户输入的近似值）
    from_actual = parsed["from"].strip()
    to_actual = parsed["to"].strip()

    rendered = (f'📋 {from_actual} → {to_actual}（📖 {type_icon}，'
                f'来源：flow-transitions.md L{line_no} "{raw_line.strip()}"）')
    print(rendered)
    audit(line_no, type_icon, args, spec_path)


if __name__ == "__main__":
    main()
