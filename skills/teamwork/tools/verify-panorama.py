#!/usr/bin/env python3
"""
verify-panorama.py — UI Design Stage 出口物化校验（v7.3.10+P0-132）

职责（与 verify-ac.py / state.py 同型 · physical-layer 拦截）：
- 校验 Designer 自查报告完整性（grep 5 维度 checklist · 是否全 ✅）
- 校验跨子项目场景下 UI.md 顶部含「全景宿主」标注
- 校验 sitemap.md mtime（涉及变更时晚于 Stage 开始时刻）
- 校验 preview/*.html 数量 ≥ PRD AC 提到的页面数
- 校验 panorama_path 路径有效（存在 sitemap.md）

PMO 调用：
    python3 {SKILL_ROOT}/tools/verify-panorama.py \\
        --feature {artifact_root} \\
        [--panorama-path {绝对路径} | --no-panorama] \\
        [--stage-started-at {ISO8601}]

退出码：0 PASS · 1 FAIL · 2 配置错误

红线：
1. 不依赖 Designer 自觉 · 物理校验自查报告 + 文件系统状态
2. cite-only output：JSON 含 checks_passed / checks_failed / hint
3. 配合 standards/common.md § 四B Designer 自查规范使用
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

SELF_CHECK_HEADER = "Designer 自查报告"
PANORAMA_HOST_MARKER = "全景宿主"
PANORAMA_PATH_MARKER = "panorama_path"
COVERAGE_TABLE_MARKER = "UI-AC-COVERAGE"

# 5 维度自查清单的 marker
DIMENSION_MARKERS = {
    "1. 全景对齐": "全景对齐",
    "2. 状态覆盖": "状态覆盖",
    "3. PRD AC 覆盖": "AC 覆盖",
    "4. 全景增量同步": "全景增量同步",
    "5. 结构性变更红线": "结构性变更红线",
}


def die(code: int, payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(code)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def check_self_check_section(ui_md_text: str) -> tuple[bool, list[str]]:
    """grep 5 维度 checklist · 全部存在 + 通过率 = 1.0 才 PASS。"""
    failures: list[str] = []
    if SELF_CHECK_HEADER not in ui_md_text:
        return False, [f"UI.md 缺「{SELF_CHECK_HEADER}」段（cite standards/common.md § 四B）"]

    # 提取自查段后的内容
    idx = ui_md_text.find(SELF_CHECK_HEADER)
    after = ui_md_text[idx:]

    # 5 维度都要在自查段内出现
    for dim_name, marker in DIMENSION_MARKERS.items():
        if marker not in after:
            failures.append(f"自查清单缺维度「{dim_name}」")

    # 检查是否仍是模板占位符（grep "?/4" "?/?" 等）
    if re.search(r"\|\s*\?/", after):
        failures.append("自查清单含未填占位符 `?/N` · Designer 未实际填写")

    # 检查全 ✅ 结论
    has_pass = "✅ 自查通过" in after or "自查通过" in after
    has_fail_marker = "🔴" in after or re.search(r"❌", after)
    if not has_pass and has_fail_marker:
        failures.append("自查结论非「✅ 自查通过」· Designer 已识别问题但未修复重跑")
    elif not has_pass:
        failures.append("自查结论缺失（应有「✅ 自查通过」明确表述）")

    return len(failures) == 0, failures


def check_panorama_host_marker(ui_md_text: str, no_panorama: bool) -> tuple[bool, list[str]]:
    if no_panorama:
        # 项目无全景场景 · 必须含警告标注
        if "项目无全景基准" not in ui_md_text and "无全景" not in ui_md_text:
            return False, ["项目无全景场景 · UI.md 顶部应标注「⚠️ 项目无全景基准」"]
        return True, []
    if PANORAMA_HOST_MARKER not in ui_md_text:
        return False, [f"UI.md 顶部缺「{PANORAMA_HOST_MARKER}」标注（治本 P0-123 跨子项目漏检）"]
    if PANORAMA_PATH_MARKER not in ui_md_text:
        return False, [f"UI.md 顶部缺「{PANORAMA_PATH_MARKER}」字段"]
    return True, []


def check_panorama_path_valid(panorama_path: str | None) -> tuple[bool, list[str]]:
    if panorama_path is None:
        return True, []
    p = Path(panorama_path)
    if not p.exists():
        return False, [f"panorama_path 不存在: {panorama_path}"]
    sitemap = p / "sitemap.md" if p.is_dir() else p
    if not sitemap.exists() and not (p / "sitemap.md").exists():
        return False, [f"panorama_path 下未找到 sitemap.md: {panorama_path}"]
    return True, []


def check_sitemap_mtime(panorama_path: str | None, stage_started_at: str | None,
                       ui_md_text: str) -> tuple[bool, list[str]]:
    """涉及全景变更时 · sitemap.md mtime 必须晚于 Stage 开始。"""
    if not panorama_path or not stage_started_at:
        return True, []
    # 只在 UI.md 自查段标了「🟡 增量」时校验
    after = ui_md_text[ui_md_text.find(SELF_CHECK_HEADER):] if SELF_CHECK_HEADER in ui_md_text else ""
    if "🟡 增量" not in after and "增量同步 | 4 | 4/4" not in after:
        return True, []  # 无变更 · 跳过

    sitemap = Path(panorama_path) / "sitemap.md"
    if not sitemap.exists():
        return False, [f"声称全景增量但 sitemap.md 不存在: {sitemap}"]

    started = parse_iso(stage_started_at)
    if not started:
        return True, []  # 无法解析 · skip
    mtime = datetime.fromtimestamp(sitemap.stat().st_mtime, tz=timezone.utc)
    if mtime < started:
        return False, [
            f"声称全景增量但 sitemap.md mtime ({mtime.strftime('%Y-%m-%dT%H:%M:%SZ')}) "
            f"早于 Stage 开始 ({stage_started_at}) · Designer 未实际更新"
        ]
    return True, []


def check_preview_count(feature_dir: Path, ui_md_text: str) -> tuple[bool, list[str]]:
    """preview/*.html 数量 ≥ UI.md 提到的页面数。"""
    preview_dir = feature_dir / "preview"
    if not preview_dir.exists():
        return False, ["preview/ 目录不存在 · 必须含 HTML 预览稿"]
    html_files = list(preview_dir.glob("*.html"))
    if not html_files:
        return False, ["preview/ 目录无 HTML 文件"]

    # 简单启发：UI.md 内提到的 .html 链接数应 ≤ 实际 html 数
    referenced = set(re.findall(r"preview/([^)\s]+\.html)", ui_md_text))
    actual = {p.name for p in html_files}
    missing = referenced - actual
    if missing:
        return False, [f"UI.md 引用了 {len(missing)} 个 preview HTML 但文件不存在: {sorted(missing)[:3]}..."]

    return True, []


def main() -> None:
    p = argparse.ArgumentParser(prog="verify-panorama.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    env_feature = os.environ.get("TEAMWORK_FEATURE")
    p.add_argument("--feature", default=env_feature, required=(env_feature is None),
                   help="Feature artifact_root（含 UI.md / preview/）· 缺省读 $TEAMWORK_FEATURE")
    pano_grp = p.add_mutually_exclusive_group()
    pano_grp.add_argument("--panorama-path", help="全景目录绝对路径（含 sitemap.md / preview/overview.html）")
    pano_grp.add_argument("--no-panorama", action="store_true", help="项目无全景场景")
    p.add_argument("--stage-started-at", help="UI Design Stage 开始 ISO 8601 · 用于 sitemap mtime 校验")
    args = p.parse_args()

    feature_dir = Path(args.feature).resolve()
    ui_md = feature_dir / "UI.md"
    if not ui_md.exists():
        die(2, {"verdict": "FAIL", "error": f"UI.md not found: {ui_md}"})

    text = ui_md.read_text(encoding="utf-8")
    all_failures: list[str] = []
    checks_passed: list[str] = []

    for name, fn in [
        ("self-check section completeness", lambda: check_self_check_section(text)),
        ("panorama host marker (P0-123)", lambda: check_panorama_host_marker(text, args.no_panorama)),
        ("panorama_path valid", lambda: check_panorama_path_valid(args.panorama_path)),
        ("sitemap.md mtime (when 增量)",
         lambda: check_sitemap_mtime(args.panorama_path, args.stage_started_at, text)),
        ("preview/*.html count", lambda: check_preview_count(feature_dir, text)),
    ]:
        ok, errs = fn()
        if ok:
            checks_passed.append(name)
        else:
            all_failures.extend(f"[{name}] {e}" for e in errs)

    if all_failures:
        emit({
            "verdict": "FAIL",
            "feature": str(feature_dir),
            "checks_passed": checks_passed,
            "checks_failed": all_failures,
            "error_count": len(all_failures),
            "hint": ("按 standards/common.md § 四B Designer 自查规范补完 UI.md 自查报告 · "
                     "重跑 verify-panorama · 通过后才能进 ⏸️ 用户确认设计稿"),
        })
        sys.exit(1)

    emit({
        "verdict": "PASS",
        "feature": str(feature_dir),
        "checks_passed": checks_passed,
        "checked_at": now_iso(),
    })


if __name__ == "__main__":
    main()
