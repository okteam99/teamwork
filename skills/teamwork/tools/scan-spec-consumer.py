#!/usr/bin/env python3
"""
scan-spec-consumer.py — 扫描 spec 中"writer-only 规则"（v7.3.10+P0-146）

实战洞察（4.6 自承）：AI 跳过的 spec 规则普遍缺「下游消费者」标注 ——
仅写"🔴 必须"但没说"跳了谁会发现 / 哪个下游会失败" · AI 内部评估为
"只是仪式"而跳掉。

权威源：[standards/scripts-policy.md § R-SP-8](../standards/scripts-policy.md)
「每条 🔴 规则必须含下游消费者标注」原则。

本工具职责：
- 扫所有 spec markdown 文件
- 提取每条"🔴 + 必须/必填/必读/不得/禁止/强制"规则行
- 在同段内 grep 下游消费者标志（exit 1 / 重审 / 实证 case / state.concerns 等）
- 命中 → has_consumer · 未命中 → missing_consumer（候选修复目标）
- 输出 JSON 清单 · PMO / patch 起草者按清单批量补标注

用法：
    python3 tools/scan-spec-consumer.py
    python3 tools/scan-spec-consumer.py --skill-root /abs/path
    python3 tools/scan-spec-consumer.py --output-format markdown  # 给人看
    python3 tools/scan-spec-consumer.py --limit 30                # 只输出前 N

退出码：
- 0 OK · stdout = JSON / markdown 列表
- 2 FAIL · 参数非法 / spec root 不存在
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOL_VERSION = "v1.0"
TOOL_NAME = "scan-spec-consumer.py"

# 规则触发模式：🔴 line 含 "必须 / 必填 / 必读 / 不得 / 禁止 / 强制 / 必出 / 不允许"
RULE_KEYWORDS = ["必须", "必填", "必读", "不得", "禁止", "强制", "必出", "不允许", "必经"]
RULE_TRIGGER_RE = re.compile(
    r"🔴.*(?:" + "|".join(RULE_KEYWORDS) + r")",
)

# 下游消费者标志：跳了之后谁/哪个下游会发现 / 失败 / 拒绝
# 这些是 has-consumer 的强信号
CONSUMER_PATTERNS = [
    r"exit\s*[12]",
    r"BLOCKED",
    r"BLOCKER",
    r"reject|拒绝|打回|退回|重审",
    r"实证.*(?:case|PTR|ADMIN|INFRA|F\d+)",
    r"用户无法",
    r"评审.*(?:退化|失败|漂移)",
    r"伪造证据",
    r"会(?:被|有|失败|拒绝|发现|提示|阻断|暂停)",
    r"自动.*(?:打回|拒绝|降级|补救)",
    r"工具.*(?:校验|拦截|拒绝)",
    r"hook.*reject",
    r"verify.*(?:fail|拦截)",
    r"audit.*(?:WARN|失败)",
    r"state\.concerns",
    r"下游.*Stage",
    r"入口.*(?:校验|拒绝|gate)",
    r"(?:render|verify|scan|enforce|audit)-[\w-]+\.py",
    r"physical.*intercept|物理.*拦截",
    r"R7\(c\)|evidence-binding",
    r"漂移",
    r"反模式|anti-pattern",
    r"治本 P0-\d+",
    r"流程偏离",
]
CONSUMER_RE = re.compile("|".join(CONSUMER_PATTERNS), re.IGNORECASE)

# 默认扫描的 spec 文件 glob（相对 SKILL_ROOT）
# v8.x:清掉已删 spec(STATUS-LINE.md / REVIEWS.md / CONTEXT-RECOVERY.md / RULES.md / rules/)
DEFAULT_SPEC_PATHS = [
    "SKILL.md", "FLOWS.md",
    "ROLES.md", "TEMPLATES.md", "STANDARDS.md",
    "PRODUCT-OVERVIEW-INTEGRATION.md",
]
DEFAULT_SPEC_DIRS = ["stages", "standards", "roles", "docs"]


@dataclass
class RuleHit:
    file: str
    line_number: int
    line_text: str
    has_consumer: bool
    consumer_evidence: str | None
    section_title: str | None


def find_section_title(lines: list[str], current_line_idx: int) -> str | None:
    """向上查找最近的 markdown header 当作 section context。"""
    for i in range(current_line_idx - 1, max(0, current_line_idx - 50), -1):
        line = lines[i].rstrip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return None


def scan_paragraph(lines: list[str], rule_line_idx: int, window: int = 8) -> tuple[bool, str | None]:
    """在规则行所在段（前后 window 行内）查找消费者标志。

    返回 (has_consumer, evidence_snippet)。
    """
    start = max(0, rule_line_idx - window)
    end = min(len(lines), rule_line_idx + window + 1)
    for i in range(start, end):
        m = CONSUMER_RE.search(lines[i])
        if m:
            return True, lines[i].strip()[:200]
    return False, None


def scan_file(path: Path) -> list[RuleHit]:
    """扫描单文件 · 返回所有规则命中。"""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []

    lines = text.splitlines()
    hits: list[RuleHit] = []
    for idx, line in enumerate(lines):
        if not RULE_TRIGGER_RE.search(line):
            continue
        has_consumer, evidence = scan_paragraph(lines, idx)
        section = find_section_title(lines, idx)
        hits.append(RuleHit(
            file=str(path),
            line_number=idx + 1,
            line_text=line.strip()[:240],
            has_consumer=has_consumer,
            consumer_evidence=evidence,
            section_title=section,
        ))
    return hits


def discover_spec_files(skill_root: Path) -> list[Path]:
    files: list[Path] = []
    for name in DEFAULT_SPEC_PATHS:
        p = skill_root / name
        if p.exists():
            files.append(p)
    for dirname in DEFAULT_SPEC_DIRS:
        d = skill_root / dirname
        if d.exists():
            files.extend(sorted(d.glob("*.md")))
    return files


def fail(error: str, **extra: Any) -> None:
    payload: dict[str, Any] = {
        "verdict": "FAIL",
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "error": error,
    }
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(2)


def emit_json(hits: list[RuleHit], skill_root: Path, limit: int | None) -> None:
    missing = [h for h in hits if not h.has_consumer]
    has = [h for h in hits if h.has_consumer]
    payload = {
        "verdict": "OK",
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "skill_root": str(skill_root),
        "scanned_files": len({h.file for h in hits}),
        "total_rules": len(hits),
        "with_consumer": len(has),
        "missing_consumer": len(missing),
        "ratio_missing": round(len(missing) / max(1, len(hits)), 3),
        "missing": [asdict(h) for h in (missing[:limit] if limit else missing)],
        "rendered_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if limit and len(missing) > limit:
        payload["truncated"] = True
        payload["truncated_count"] = len(missing) - limit
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def emit_markdown(hits: list[RuleHit], skill_root: Path, limit: int | None) -> None:
    missing = [h for h in hits if not h.has_consumer]
    has = [h for h in hits if h.has_consumer]
    print(f"# Spec Consumer Coverage Report\n")
    print(f"- Skill root: `{skill_root}`")
    print(f"- Total 🔴/必须 rules: **{len(hits)}**")
    print(f"- ✅ Has consumer: **{len(has)}** ({len(has)/max(1,len(hits)):.1%})")
    print(f"- ❌ Missing consumer: **{len(missing)}** ({len(missing)/max(1,len(hits)):.1%})")
    print()
    if missing:
        print("## ❌ Writer-only rules (修复候选)\n")
        for i, h in enumerate(missing[:limit] if limit else missing, 1):
            rel = Path(h.file).relative_to(skill_root) if h.file.startswith(str(skill_root)) else Path(h.file)
            print(f"### {i}. `{rel}:{h.line_number}`")
            if h.section_title:
                print(f"**Section**: {h.section_title}")
            print(f"```\n{h.line_text}\n```\n")
        if limit and len(missing) > limit:
            print(f"\n_…还有 {len(missing) - limit} 条未列出 · 用 `--limit 0` 或更大值查看全部_\n")


def main() -> None:
    p = argparse.ArgumentParser(
        prog=TOOL_NAME, description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--skill-root",
                   help="teamwork skill 根目录绝对路径 · 默认自动定位（脚本同 tools/ 上层）")
    p.add_argument("--output-format", choices=["json", "markdown"], default="json",
                   help="输出格式")
    p.add_argument("--limit", type=int, default=30,
                   help="missing_consumer 列表上限（0=全部）· 默认 30")
    args = p.parse_args()

    skill_root = (Path(args.skill_root).resolve() if args.skill_root
                  else Path(__file__).resolve().parent.parent)
    if not (skill_root / "SKILL.md").exists():
        fail(f"skill-root 不含 SKILL.md: {skill_root}",
             hint="加 --skill-root /abs/teamwork/skill 显式指定")

    files = discover_spec_files(skill_root)
    if not files:
        fail("未发现任何 spec 文件",
             hint=f"检查 {skill_root} 下 stages/ standards/ roles/ rules/")

    all_hits: list[RuleHit] = []
    for f in files:
        all_hits.extend(scan_file(f))

    # missing 排序：先按文件，再按行号
    all_hits.sort(key=lambda h: (h.file, h.line_number))

    limit = args.limit if args.limit > 0 else None
    if args.output_format == "markdown":
        emit_markdown(all_hits, skill_root, limit)
    else:
        emit_json(all_hits, skill_root, limit)


if __name__ == "__main__":
    main()
