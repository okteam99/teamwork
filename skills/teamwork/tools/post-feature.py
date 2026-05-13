#!/usr/bin/env python3
"""
post-feature.py — Feature 收尾后置脚本（v7.3.10+P0-137）

取代 hooks/post-feature.sh · 用 python 实现跨宿主可执行 + JSON 输出 + 测试覆盖。

职责（与 state.py / sync-drift.py / verify-panorama.py 同型 L3 物化）：
- KNOWLEDGE.md 检查：是否含 feature_id 记录（warn · 不阻断）
- ROADMAP.md 派生段渲染：AUTO-GENERATED marker 之间扫 state.json 输出统计 + Feature 表
- 语义段（marker 外）永不动 · 用户/PL 维护

ROADMAP marker 协议（与 sync-drift.py 同款 marker-aware）：

    <!-- TEAMWORK_ROADMAP_BEGIN:auto-generated -->
    （此段由 post-feature.py 自动渲染，请勿手编）
    ...
    <!-- TEAMWORK_ROADMAP_END:auto-generated -->

用法：

    python3 tools/post-feature.py \\
        --project-dir /path/to/project \\
        --features-dir docs/features \\
        --feature-id F042 \\
        [--roadmap docs/ROADMAP.md] [--knowledge docs/KNOWLEDGE.md] \\
        [--dry-run]

退出码（与 scripts-policy.md R-SP-5 一致）：
- 0 OK · 派生段已渲染（或已是最新）
- 1 WARN · KNOWLEDGE 未含 feature_id / ROADMAP 不存在 / marker 缺失 · 非阻断
- 2 FAIL · state.json 真值损坏 / 不一致 · 阻断
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

ROADMAP_MARKER_BEGIN = "<!-- TEAMWORK_ROADMAP_BEGIN:auto-generated -->"
ROADMAP_MARKER_END = "<!-- TEAMWORK_ROADMAP_END:auto-generated -->"
ROADMAP_MARKER_RE = re.compile(
    re.escape(ROADMAP_MARKER_BEGIN) + r"\n(.*?)\n" + re.escape(ROADMAP_MARKER_END),
    re.DOTALL,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def atomic_write(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(prefix=".post-feature.", suffix=".tmp", dir=str(path.parent))
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


def scan_features(features_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """扫描 features_dir 下所有 state.json，返回 (features, errors)。"""
    features: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if not features_dir.exists():
        return features, errors

    for entry in sorted(features_dir.iterdir()):
        if not entry.is_dir():
            continue
        state_path = entry / "state.json"
        if not state_path.exists():
            continue
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append({"path": str(state_path), "error": f"JSON parse: {e}"})
            continue

        feature_id = (
            data.get("feature_id") or data.get("id") or entry.name
        )
        name = (
            data.get("feature_name") or data.get("name") or data.get("title") or ""
        )
        current_stage = data.get("current_stage", "")
        ship = data.get("ship", {}) if isinstance(data.get("ship"), dict) else {}
        shipped = ship.get("shipped", "")
        phase = ship.get("phase", "")
        merge_commit = ship.get("merge_commit_hash", "") or ship.get("merge_commit", "")
        shipped_at = ship.get("shipped_at", "") or ship.get("merged_at", "")

        # 状态归一
        if current_stage == "completed" or shipped == "merged":
            status = "completed"
        elif current_stage in ("triage", ""):
            status = "pending"
        else:
            status = "in_progress"

        features.append({
            "feature_id": feature_id,
            "name": name,
            "current_stage": current_stage,
            "status": status,
            "phase": phase,
            "shipped": shipped,
            "merge_commit": merge_commit[:12] if merge_commit else "",
            "shipped_at": shipped_at,
            "dir": entry.name,
        })
    return features, errors


def render_roadmap_section(features: list[dict[str, Any]]) -> str:
    """渲染 ROADMAP AUTO-GENERATED 段内容（不含 marker）。"""
    completed = [f for f in features if f["status"] == "completed"]
    in_progress = [f for f in features if f["status"] == "in_progress"]
    pending = [f for f in features if f["status"] == "pending"]

    lines: list[str] = []
    lines.append(f"<!-- generated-at: {now_iso()} · by tools/post-feature.py -->")
    lines.append("")
    lines.append("### 状态总览（自动生成 · 派生自 state.json）")
    lines.append("")
    lines.append(f"- 总 Feature：**{len(features)}**")
    lines.append(f"- ✅ 已完成：**{len(completed)}**")
    lines.append(f"- 🔄 进行中：**{len(in_progress)}**")
    lines.append(f"- ⏳ 待启动：**{len(pending)}**")
    lines.append("")
    lines.append("### Feature 列表（自动生成）")
    lines.append("")
    lines.append("| Feature | 名称 | 状态 | Stage | Ship | Merge Commit |")
    lines.append("|---|---|---|---|---|---|")
    for f in features:
        status_icon = {
            "completed": "✅",
            "in_progress": "🔄",
            "pending": "⏳",
        }.get(f["status"], "—")
        merge = f["merge_commit"] or "—"
        shipped = f["shipped"] or "—"
        name = f["name"] or "—"
        lines.append(
            f"| {f['feature_id']} | {name} | {status_icon} {f['status']} "
            f"| {f['current_stage'] or '—'} | {shipped} | `{merge}` |"
        )
    lines.append("")
    lines.append("> 🔴 本段由 `tools/post-feature.py` 自动渲染，请勿手编。语义注解（切片关系/优先级/规划）写在 marker 段之外。")
    return "\n".join(lines)


def update_roadmap(
    roadmap_path: Path, section: str, dry_run: bool = False
) -> dict[str, Any]:
    """更新 ROADMAP marker 段。返回结果 dict。"""
    if not roadmap_path.exists():
        return {
            "roadmap": "not_found",
            "path": str(roadmap_path),
            "hint": "ROADMAP.md 不存在 · 跳过派生段渲染（可能非 Planning 产出的项目）",
        }

    text = roadmap_path.read_text(encoding="utf-8")
    rendered = f"{ROADMAP_MARKER_BEGIN}\n{section}\n{ROADMAP_MARKER_END}"

    if ROADMAP_MARKER_BEGIN not in text or ROADMAP_MARKER_END not in text:
        return {
            "roadmap": "marker_missing",
            "path": str(roadmap_path),
            "hint": (
                f"ROADMAP.md 缺 marker · 请人工首次插入两行到合适位置：\n"
                f"  {ROADMAP_MARKER_BEGIN}\n"
                f"  {ROADMAP_MARKER_END}\n"
                "后续派生段会在 marker 之间自动渲染 · marker 外内容永不动。"
            ),
        }

    new_text = ROADMAP_MARKER_RE.sub(
        # 保护 re.sub 反向引用：rendered 内不应含 \1 \g<...> 等模式
        lambda _m: rendered,
        text,
        count=1,
    )

    if new_text == text:
        return {"roadmap": "unchanged", "path": str(roadmap_path)}

    if dry_run:
        return {
            "roadmap": "would_update",
            "path": str(roadmap_path),
            "section_lines": len(section.splitlines()),
        }

    atomic_write(roadmap_path, new_text)
    return {
        "roadmap": "updated",
        "path": str(roadmap_path),
        "section_lines": len(section.splitlines()),
        "wrote_at": now_iso(),
    }


def check_knowledge(knowledge_path: Path, feature_id: str) -> dict[str, Any]:
    """检查 KNOWLEDGE.md 是否含 feature_id（warn-level · 不阻断）。"""
    if not knowledge_path.exists():
        return {
            "knowledge": "not_found",
            "path": str(knowledge_path),
            "hint": "KNOWLEDGE.md 不存在 · PMO 需评估是否需要创建",
        }
    text = knowledge_path.read_text(encoding="utf-8")
    if feature_id and feature_id in text:
        return {"knowledge": "present", "path": str(knowledge_path), "feature_id": feature_id}
    return {
        "knowledge": "missing_feature_id",
        "path": str(knowledge_path),
        "feature_id": feature_id,
        "hint": f"KNOWLEDGE.md 未含 {feature_id} 记录 · PMO 需评估是否补充经验",
    }


def main() -> int:
    p = argparse.ArgumentParser(
        prog="post-feature.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--project-dir", required=True, help="项目根目录绝对路径")
    p.add_argument(
        "--features-dir",
        default="docs/features",
        help="相对 project-dir 的 features 目录（默认 docs/features）",
    )
    p.add_argument("--feature-id", required=True, help="本次完成的 Feature ID（如 F042 / PTR-F042）")
    p.add_argument(
        "--roadmap",
        default="docs/ROADMAP.md",
        help="相对 project-dir 的 ROADMAP 路径（默认 docs/ROADMAP.md）",
    )
    p.add_argument(
        "--knowledge",
        default="docs/KNOWLEDGE.md",
        help="相对 project-dir 的 KNOWLEDGE 路径（默认 docs/KNOWLEDGE.md）",
    )
    p.add_argument("--dry-run", action="store_true", help="只输出 diff · 不写")
    args = p.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        emit({"verdict": "FAIL", "error": f"project-dir 不存在: {project_dir}"})
        return 2

    features_dir = project_dir / args.features_dir
    roadmap_path = project_dir / args.roadmap
    knowledge_path = project_dir / args.knowledge

    # 1. 扫描 state.json
    features, errors = scan_features(features_dir)
    if errors:
        emit({
            "verdict": "FAIL",
            "error": "state.json parse errors · 真值损坏",
            "errors": errors,
            "features_scanned": len(features),
        })
        return 2

    # 2. KNOWLEDGE check（warn-level）
    knowledge_result = check_knowledge(knowledge_path, args.feature_id)

    # 3. ROADMAP render
    section = render_roadmap_section(features)
    roadmap_result = update_roadmap(roadmap_path, section, dry_run=args.dry_run)

    # 4. 汇总 verdict
    warnings: list[str] = []
    if knowledge_result["knowledge"] in ("not_found", "missing_feature_id"):
        warnings.append(f"knowledge:{knowledge_result['knowledge']}")
    if roadmap_result["roadmap"] in ("not_found", "marker_missing"):
        warnings.append(f"roadmap:{roadmap_result['roadmap']}")

    verdict = "WARN" if warnings else "OK"
    exit_code = 1 if warnings else 0

    payload: dict[str, Any] = {
        "verdict": verdict,
        "feature_id": args.feature_id,
        "project_dir": str(project_dir),
        "features_scanned": len(features),
        "features_completed": sum(1 for f in features if f["status"] == "completed"),
        "features_in_progress": sum(1 for f in features if f["status"] == "in_progress"),
        "features_pending": sum(1 for f in features if f["status"] == "pending"),
        "knowledge": knowledge_result,
        "roadmap": roadmap_result,
        "warnings": warnings,
        "ran_at": now_iso(),
    }
    if args.dry_run:
        payload["dry_run"] = True
    emit(payload)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
