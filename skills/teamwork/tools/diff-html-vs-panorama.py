#!/usr/bin/env python3
"""
diff-html-vs-panorama.py — Feature HTML vs panorama overview HTML 结构对齐校验
（v7.3.10+P0-147）

实战触发：Designer 自查写"✅ 全景对齐"但实际 HTML 框架 / 配色 / 字号与 panorama
overview.html 漂移 · markdown 层校验（verify-panorama.py）无法 catch · 用户每次
都要肉眼对比。

本工具职责：
- 解析 panorama overview.html 提取"设计 token 集合"（颜色 / 字号 / 布局 / landmark）
- 解析 feature preview/*.html 提取同样维度
- diff：feature 引入了 panorama 没有的 token → WARN（潜在漂移）
- diff：feature 缺关键 landmark（main 等）→ FAIL（HTML 损坏）

权威源：[stages/ui-design-stage.md § 过程硬规则](../stages/ui-design-stage.md)
「Feature UI 必须与全景风格/配色/布局/语言一致」。

依赖：仅 Python stdlib（html.parser）· 跨宿主零依赖。

用法：
    python3 tools/diff-html-vs-panorama.py \\
      --panorama design/preview/overview.html \\
      --feature docs/features/F042/preview/page1.html

    # 批量校验 feature 下所有 preview/*.html
    python3 tools/diff-html-vs-panorama.py \\
      --panorama design/preview/overview.html \\
      --feature-dir docs/features/F042

退出码（与 scripts-policy.md R-SP-5 一致）：
- 0 OK · feature 使用 panorama token 子集
- 1 WARN · feature 引入 panorama 不含的 token（可能视觉漂移）
- 2 FAIL · feature 缺关键 landmark / HTML 解析失败 / 文件不存在
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

TOOL_VERSION = "v1.0"
TOOL_NAME = "diff-html-vs-panorama.py"

# Landmark 标签 · 页面框架核心元素
LANDMARK_TAGS = {"nav", "header", "aside", "main", "footer", "section"}
# 必备 landmark · feature 缺则 BLOCKER
REQUIRED_LANDMARKS = {"main"}  # main 是 single-page 最基本要求

# Tailwind utility class 前缀分类
COLOR_PREFIXES = ("bg-", "border-", "ring-", "divide-", "placeholder-",
                  "caret-", "accent-", "from-", "via-", "to-", "fill-",
                  "stroke-", "decoration-", "outline-")
FONT_SIZES = {f"text-{s}" for s in
              ("xs", "sm", "base", "lg", "xl", "2xl", "3xl",
               "4xl", "5xl", "6xl", "7xl", "8xl", "9xl")}
LAYOUT_PREFIXES = ("flex", "grid", "block", "inline", "hidden",
                   "gap-", "space-x-", "space-y-",
                   "p-", "px-", "py-", "pt-", "pb-", "pl-", "pr-",
                   "m-", "mx-", "my-", "mt-", "mb-", "ml-", "mr-",
                   "w-", "h-", "min-w-", "max-w-", "min-h-", "max-h-")


class HTMLProfileExtractor(HTMLParser):
    """提取 HTML 设计 profile · 含 landmarks / classes / 各维度 token 集合。"""

    def __init__(self) -> None:
        super().__init__()
        self.landmarks: set[str] = set()
        self.all_classes: set[str] = set()
        self.tag_count: dict[str, int] = defaultdict(int)
        self.parse_error: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tag_count[tag] += 1
        if tag in LANDMARK_TAGS:
            self.landmarks.add(tag)
        for name, value in attrs:
            if name == "class" and value:
                for cls in value.split():
                    self.all_classes.add(cls)

    def error(self, message: str) -> None:  # type: ignore[override]
        # html.parser 不严格抛错 · 但若有问题可记录
        self.parse_error = message


def categorize_classes(classes: set[str]) -> dict[str, set[str]]:
    """按 Tailwind utility 类型分类。"""
    out: dict[str, set[str]] = {
        "color": set(),
        "font_size": set(),
        "layout": set(),
        "other": set(),
    }
    for c in classes:
        # text-* 拆 font_size vs color/font-weight
        if c in FONT_SIZES:
            out["font_size"].add(c)
            continue
        if c.startswith(COLOR_PREFIXES):
            out["color"].add(c)
            continue
        if c.startswith("text-") and not c.startswith(("text-left", "text-right", "text-center", "text-justify")):
            # text-{color}-{shade} like text-slate-900 / text-red-500 → color
            # text-{align} above is layout-ish · 已被排除
            out["color"].add(c)
            continue
        if c.startswith(LAYOUT_PREFIXES):
            out["layout"].add(c)
            continue
        out["other"].add(c)
    return out


def extract_profile(html_text: str) -> tuple[dict[str, Any], str | None]:
    parser = HTMLProfileExtractor()
    try:
        parser.feed(html_text)
    except Exception as e:  # noqa: BLE001
        return {}, f"HTML parse error: {e}"

    categorized = categorize_classes(parser.all_classes)
    profile = {
        "landmarks": parser.landmarks,
        "tag_count": dict(parser.tag_count),
        "all_classes_count": len(parser.all_classes),
        "color_classes": categorized["color"],
        "font_size_classes": categorized["font_size"],
        "layout_classes": categorized["layout"],
        "other_classes": categorized["other"],
    }
    return profile, parser.parse_error


def diff_profiles(panorama: dict[str, Any], feature: dict[str, Any]
                  ) -> dict[str, Any]:
    """对比 panorama / feature profile · 生成 diff 结构。"""
    missing_landmarks = panorama["landmarks"] - feature["landmarks"]
    missing_required = REQUIRED_LANDMARKS - feature["landmarks"]
    extra_landmarks = feature["landmarks"] - panorama["landmarks"]

    # token 维度 diff: feature 引入 panorama 没有的 → 潜在漂移
    extra_colors = feature["color_classes"] - panorama["color_classes"]
    extra_font_sizes = feature["font_size_classes"] - panorama["font_size_classes"]
    extra_layouts = feature["layout_classes"] - panorama["layout_classes"]

    # 计算 token 共用率（feature 用到的 panorama tokens / feature 总 tokens）
    feature_color_count = len(feature["color_classes"])
    shared_colors = feature["color_classes"] & panorama["color_classes"]
    color_alignment_pct = (
        (len(shared_colors) / feature_color_count * 100)
        if feature_color_count else 100.0
    )

    return {
        "missing_required_landmarks": sorted(missing_required),
        "missing_landmarks": sorted(missing_landmarks),
        "extra_landmarks": sorted(extra_landmarks),
        "extra_colors": sorted(extra_colors),
        "extra_font_sizes": sorted(extra_font_sizes),
        "extra_layouts": sorted(extra_layouts),
        "color_alignment_pct": round(color_alignment_pct, 1),
        "panorama_total_colors": len(panorama["color_classes"]),
        "feature_total_colors": feature_color_count,
    }


def determine_verdict(diff: dict[str, Any]) -> tuple[str, int, list[str]]:
    """根据 diff 决定 verdict + exit code + reasons。"""
    reasons: list[str] = []
    # BLOCKER
    if diff["missing_required_landmarks"]:
        reasons.append(
            f"缺必备 landmark: {diff['missing_required_landmarks']} "
            f"(REQUIRED_LANDMARKS={sorted(REQUIRED_LANDMARKS)})"
        )
        return "FAIL", 2, reasons
    # WARN
    warn_signals = (
        diff["extra_colors"], diff["extra_font_sizes"], diff["extra_layouts"]
    )
    if any(warn_signals):
        if diff["extra_colors"]:
            reasons.append(
                f"feature 引入 panorama 不含的 {len(diff['extra_colors'])} 个 color tokens"
            )
        if diff["extra_font_sizes"]:
            reasons.append(
                f"feature 引入 panorama 不含的字号: {diff['extra_font_sizes']}"
            )
        if diff["extra_layouts"]:
            reasons.append(
                f"feature 引入 panorama 不含的 {len(diff['extra_layouts'])} 个 layout tokens"
            )
        return "WARN", 1, reasons
    return "OK", 0, reasons


def serialize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """profile sets → 可序列化 lists。"""
    return {
        "landmarks": sorted(profile["landmarks"]),
        "all_classes_count": profile["all_classes_count"],
        "color_classes_count": len(profile["color_classes"]),
        "font_size_classes": sorted(profile["font_size_classes"]),
        "layout_classes_count": len(profile["layout_classes"]),
    }


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


def diff_one(panorama_profile: dict[str, Any], panorama_path: Path,
             feature_path: Path) -> tuple[dict[str, Any], int]:
    try:
        feature_html = feature_path.read_text(encoding="utf-8")
    except OSError as e:
        return {
            "verdict": "FAIL",
            "feature": str(feature_path),
            "error": f"read failed: {e}",
        }, 2
    feature_profile, parse_err = extract_profile(feature_html)
    if parse_err:
        return {
            "verdict": "FAIL",
            "feature": str(feature_path),
            "error": parse_err,
        }, 2
    diff = diff_profiles(panorama_profile, feature_profile)
    verdict, exit_code, reasons = determine_verdict(diff)
    return {
        "verdict": verdict,
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "panorama": str(panorama_path),
        "feature": str(feature_path),
        "reasons": reasons,
        "diff": diff,
        "panorama_profile": serialize_profile(panorama_profile),
        "feature_profile": serialize_profile(feature_profile),
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }, exit_code


def main() -> None:
    p = argparse.ArgumentParser(
        prog=TOOL_NAME, description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--panorama", required=True,
                   help="panorama overview.html 绝对/相对路径")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--feature", help="单个 feature preview HTML")
    g.add_argument("--feature-dir",
                   help="feature preview 目录 · 扫描所有 *.html")
    p.add_argument("--strict", action="store_true",
                   help="WARN 升 FAIL (exit 2) · 严格模式")
    args = p.parse_args()

    panorama_path = Path(args.panorama).resolve()
    if not panorama_path.exists():
        fail(f"panorama 不存在: {panorama_path}",
             hint="检查路径 · 或 cd 到项目根再跑")

    try:
        panorama_html = panorama_path.read_text(encoding="utf-8")
    except OSError as e:
        fail(f"panorama 读失败: {e}")

    panorama_profile, panorama_err = extract_profile(panorama_html)
    if panorama_err:
        fail(f"panorama HTML parse 失败: {panorama_err}")
    if not panorama_profile["all_classes_count"]:
        fail(
            "panorama 未解析出任何 class · 检查 panorama HTML 质量",
            hint="确认 panorama 是 Tailwind/utility-first 设计稿 · 含 class names",
        )

    # 单文件 vs 目录
    feature_paths: list[Path]
    if args.feature:
        p_feat = Path(args.feature).resolve()
        if not p_feat.exists():
            fail(f"feature 不存在: {p_feat}")
        feature_paths = [p_feat]
    else:
        d_feat = Path(args.feature_dir).resolve()
        if not d_feat.exists():
            fail(f"feature-dir 不存在: {d_feat}")
        feature_paths = sorted(d_feat.glob("*.html"))
        if not feature_paths:
            fail(f"feature-dir 无 .html 文件: {d_feat}")

    results: list[dict[str, Any]] = []
    worst_exit = 0
    for fp in feature_paths:
        result, exit_code = diff_one(panorama_profile, panorama_path, fp)
        results.append(result)
        if args.strict and exit_code == 1:
            exit_code = 2
        worst_exit = max(worst_exit, exit_code)

    # 输出
    if len(results) == 1:
        print(json.dumps(results[0], ensure_ascii=False, indent=2))
    else:
        summary = {
            "verdict": ("OK" if worst_exit == 0
                        else "WARN" if worst_exit == 1 else "FAIL"),
            "tool": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "panorama": str(panorama_path),
            "feature_count": len(results),
            "results": results,
            "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    sys.exit(worst_exit)


if __name__ == "__main__":
    main()
