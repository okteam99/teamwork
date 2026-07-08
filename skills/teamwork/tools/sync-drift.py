#!/usr/bin/env python3
"""
sync-drift.py — CLAUDE.md / AGENTS.md teamwork 注入段同步引擎（v7.3.10+P0-134）

职责（与 verify-panorama.py / state.py 同型物化拦截）：
- marker-aware 同步：仅更新 `<!-- TEAMWORK_BEGIN:X -->` ... `<!-- TEAMWORK_END:X -->` 之间内容
- 用户编辑的 marker 外内容**永不动**
- idempotent：同 source + target 重跑 = 无 diff
- 内容敏感：内容相同即 unchanged 不重写（marker 版本号不参与比对 · 仅在内容变化时随之更新 ·
  避免每次 patch bump 无谓重写宿主文件）

用法：
    # 首次注入（marker 不存在 → 插入到目标文件顶部）
    python3 tools/sync-drift.py --target ./CLAUDE.md \\
        --source {SKILL_ROOT}/templates/host-instruction-injection.md \\
        --skill-version v7.3.10+P0-134 --init

    # 升级（marker 存在但内容变化 → 替换 marker 之间内容 + version 标签随之更新）
    python3 tools/sync-drift.py --target ./CLAUDE.md --source ... --skill-version ...

    # dry-run（只看 diff · 不写）
    python3 tools/sync-drift.py --target ... --source ... --skill-version ... --dry-run

退出码（R-SP-5 契约）：0 PASS（含 unchanged noop / dry-run）· 2 FAIL 阻断（source/target 缺失 · 缺 marker 未加 --init）

红线：
1. 仅动 marker 之间内容（用户外部段绝对保护）
2. cite-only output：JSON 含 sections_updated / sections_unchanged / 用户内容保留行数
3. --init 才允许首次插入 marker（防误注入到不该有 teamwork 段的文件）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# marker 正则：捕获 section 名 + 版本 + 内容
SECTION_RE = re.compile(
    r"<!-- TEAMWORK_BEGIN:([\w-]+)\s+([^\s]+?)\s*-->\n(.*?)\n<!-- TEAMWORK_END:\1\s*-->",
    re.DOTALL,
)

# 从 source（host-instruction-injection.md）提取 section · 容错性强
SOURCE_SECTION_RE = re.compile(
    r"<!-- TEAMWORK_BEGIN:([\w-]+)\s+([^\s]+?)\s*-->\n(.*?)\n<!-- TEAMWORK_END:\1\s*-->",
    re.DOTALL,
)


def die(code: int, payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(code)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_sections(text: str, regex: re.Pattern) -> dict[str, dict[str, str]]:
    """提取 {section_name: {version, content, full_match}}。"""
    out: dict[str, dict[str, str]] = {}
    for m in regex.finditer(text):
        name, version, content = m.group(1), m.group(2), m.group(3)
        out[name] = {
            "version": version,
            "content": content,
            "full_match": m.group(0),
        }
    return out


def render_section(name: str, version: str, content: str) -> str:
    return (f"<!-- TEAMWORK_BEGIN:{name} {version} -->\n"
            f"{content}\n"
            f"<!-- TEAMWORK_END:{name} -->")


def atomic_write(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(prefix=".sync.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def main() -> None:
    p = argparse.ArgumentParser(prog="sync-drift.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--target", required=True, help="CLAUDE.md / AGENTS.md 绝对路径")
    p.add_argument("--source", required=True,
                   help="canonical 注入模板（默认 SKILL_ROOT/templates/host-instruction-injection.md）")
    p.add_argument("--skill-version", required=True,
                   help="用作 marker 版本标签（PMO 注入 · 同 bootstrap.py 协议）")
    p.add_argument("--init", action="store_true",
                   help="首次注入：marker 不存在则插入到目标文件顶部 · 否则只允许升级既有 marker")
    p.add_argument("--dry-run", action="store_true", help="只输出 diff · 不写")
    args = p.parse_args()

    src_path = Path(args.source)
    tgt_path = Path(args.target)
    if not src_path.exists():
        die(2, {"verdict": "FAIL", "error": f"source 不存在: {src_path}"})

    # 解析 source 中的所有 section
    src_text = src_path.read_text(encoding="utf-8")
    src_sections = parse_sections(src_text, SOURCE_SECTION_RE)
    if not src_sections:
        die(2, {"verdict": "FAIL",
                "error": f"source 中无 TEAMWORK_BEGIN section: {src_path}"})

    # target 不存在场景
    if not tgt_path.exists():
        if not args.init:
            die(2, {"verdict": "FAIL",
                    "error": f"target 不存在: {tgt_path} · 加 --init 首次创建"})
        new_content = "\n\n".join(
            render_section(n, args.skill_version, s["content"])
            for n, s in src_sections.items()
        ) + "\n"
        if args.dry_run:
            emit({
                "verdict": "DRY_RUN", "target": str(tgt_path),
                "would_create": True,
                "sections_to_insert": list(src_sections.keys()),
                "lines": len(new_content.splitlines()),
            })
            return
        atomic_write(tgt_path, new_content)
        emit({
            "verdict": "OK", "target": str(tgt_path),
            "action": "created",
            "sections_inserted": list(src_sections.keys()),
            "skill_version": args.skill_version,
            "wrote_at": now_iso(),
        })
        return

    # target 存在 · 解析既有 sections
    tgt_text = tgt_path.read_text(encoding="utf-8")
    tgt_sections = parse_sections(tgt_text, SECTION_RE)

    sections_updated: list[dict[str, str]] = []
    sections_unchanged: list[str] = []
    sections_inserted: list[str] = []
    new_text = tgt_text

    for name, src in src_sections.items():
        canonical = render_section(name, args.skill_version, src["content"])
        if name in tgt_sections:
            tgt = tgt_sections[name]
            # 内容一致 → unchanged(版本号不参与比对 · 仅内容变化时随之更新 ·
            # 否则每次 patch bump 都会无谓重写宿主文件)
            if tgt["content"] == src["content"]:
                sections_unchanged.append(name)
                continue
            # 替换整段（保留 marker 外用户内容）
            new_text = new_text.replace(tgt["full_match"], canonical, 1)
            sections_updated.append({
                "name": name, "from_version": tgt["version"], "to_version": args.skill_version,
            })
        else:
            # 不存在 marker(阻断错误 · R-SP-5 exit 2)
            if not args.init:
                die(2, {
                    "verdict": "FAIL",
                    "error": f"target 缺 section '{name}' marker · 加 --init 首次插入",
                    "hint": ("teamwork 注入段未在 target 找到 · 用户可能编辑过 / "
                             "或本次首次升级 · 加 --init 安全插入到顶部"),
                })
            # 插入到顶部
            new_text = canonical + "\n\n" + new_text
            sections_inserted.append(name)

    # 用户外部内容保留行数（diff snapshot）
    # 精确统计:总行数 − 各 marker 块行数(块在 target 中唯一出现 · 由 parse 保证)。
    # 不能用「行 in 块」子串判断——空行/短行是任意块的子串 → 统计失真。
    marker_lines = sum(s["full_match"].count("\n") + 1 for s in tgt_sections.values())
    user_lines = max(0, len(tgt_text.splitlines()) - marker_lines)

    if not sections_updated and not sections_inserted:
        emit({
            "verdict": "OK", "target": str(tgt_path),
            "action": "noop", "sections_unchanged": sections_unchanged,
            "user_content_preserved_lines": user_lines,
            "checked_at": now_iso(),
        })
        return

    if args.dry_run:
        emit({
            "verdict": "DRY_RUN", "target": str(tgt_path),
            "sections_updated": sections_updated,
            "sections_inserted": sections_inserted,
            "sections_unchanged": sections_unchanged,
            "user_content_preserved_lines": user_lines,
            "diff_summary": (f"+{len(sections_inserted)} sections inserted, "
                             f"{len(sections_updated)} sections version-bumped"),
        })
        return

    atomic_write(tgt_path, new_text)
    emit({
        "verdict": "OK", "target": str(tgt_path),
        "action": "updated",
        "sections_updated": sections_updated,
        "sections_inserted": sections_inserted,
        "sections_unchanged": sections_unchanged,
        "user_content_preserved_lines": user_lines,
        "skill_version": args.skill_version,
        "wrote_at": now_iso(),
    })


if __name__ == "__main__":
    main()
