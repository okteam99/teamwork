#!/usr/bin/env python3
"""
_feature_context.py — Feature 上下文发现与加载（v7.3.10+P0-144）

降低 PMO 调 render-* / verify-* 工具的负担：state.json 已含 feature_id / flow_type /
current_stage / worktree.{path,branch} / merge_target / external_cross_review.model
等"每次调用基本不变"的参数 · 工具自动 read state.json · PMO 只传 per-call 语义参数
（--next-step / --pause-point / --decision 等）。

发现优先级：
1. explicit_dir 参数（工具 --feature-dir 显式传入 · 最高优先级）
2. $TEAMWORK_FEATURE 环境变量（绝对路径 · 推荐）
3. 从 CWD 向上 walk · 找含 state.json 且 parent 路径含 'features/' 段的目录
4. 找不到 → return None（工具按显式参数走 · 不强制要求 context）

参数权重（显式 > context · 配合 audit JSON 记 override 留痕）：
- 工具调用者传了显式参数 → 用显式值 · 但 audit JSON 记 `overrides_from_context: {field}`
- 未传显式参数 → 用 context 值 · audit JSON 记 `source: state.json`

权威源：[templates/feature-state.json](../templates/feature-state.json) state.json schema。
配套规范：[standards/scripts-policy.md § R-SP-7](../standards/scripts-policy.md) feature context auto-fill 原则。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FeatureContext:
    """Feature 级上下文 · 字段缺失时为 None · 工具自行决定是否要求。"""

    feature_dir: Path
    state_json_path: Path
    feature_id: str | None = None
    flow_type: str | None = None
    current_stage: str | None = None
    branch: str | None = None
    worktree_path: str | None = None
    merge_target: str | None = None
    ext_model: str | None = None
    sub_project: str | None = None
    artifact_root: str | None = None
    # 原始 state dict · 便于工具按需提取其他字段
    raw: dict[str, Any] | None = None
    # 发现来源 · 用于 audit JSON
    discovery_source: str = "unknown"

    def to_audit_dict(self) -> dict[str, Any]:
        """audit JSON 用 · 摘要 context 关键字段。"""
        return {
            "feature_dir": str(self.feature_dir),
            "state_json": str(self.state_json_path),
            "discovery_source": self.discovery_source,
            "feature_id": self.feature_id,
            "flow_type": self.flow_type,
            "current_stage": self.current_stage,
            "branch": self.branch,
            "worktree_path": self.worktree_path,
            "merge_target": self.merge_target,
            "ext_model": self.ext_model,
        }


def _walk_up_for_state(start: Path, max_levels: int = 8) -> Path | None:
    """从 start 向上 walk · 找含 state.json 的目录（限制层级防失控）。"""
    current = start.resolve()
    for _ in range(max_levels):
        candidate = current / "state.json"
        if candidate.exists():
            # 启发式：parent 路径含 'features' 段 · 大概率是 Feature 目录
            if "features" in str(current.parent).split("/"):
                return current
        if current.parent == current:
            break
        current = current.parent
    return None


def _resolve_feature_dir(explicit: Path | None) -> tuple[Path | None, str]:
    """返回 (feature_dir, discovery_source)。找不到返回 (None, ...)."""
    if explicit:
        p = Path(explicit).resolve()
        if not (p / "state.json").exists():
            return None, f"explicit_not_found:{p}"
        return p, "explicit"

    env_val = os.environ.get("TEAMWORK_FEATURE")
    if env_val:
        p = Path(env_val).resolve()
        if not (p / "state.json").exists():
            return None, f"env_not_found:{p}"
        return p, "env_TEAMWORK_FEATURE"

    found = _walk_up_for_state(Path.cwd())
    if found:
        return found, "walk_cwd"

    return None, "not_found"


def _safe_get(d: dict[str, Any], *keys: str) -> Any:
    """嵌套 dict get · 任一层缺失返回 None。"""
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
        if cur is None:
            return None
    return cur


def load(explicit_dir: Path | None = None) -> FeatureContext | None:
    """加载 Feature 上下文 · 找不到 state.json 返回 None。

    工具调用模式：
        ctx = _feature_context.load(args.feature_dir)
        feature_id = args.feature or (ctx.feature_id if ctx else None)
        if not feature_id:
            fail("...必填 / 或在 Feature 目录下设 TEAMWORK_FEATURE")
    """
    feature_dir, source = _resolve_feature_dir(explicit_dir)
    if feature_dir is None:
        return None

    state_path = feature_dir / "state.json"
    try:
        raw = json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    if not isinstance(raw, dict):
        return None

    return FeatureContext(
        feature_dir=feature_dir,
        state_json_path=state_path,
        feature_id=raw.get("feature_id"),
        flow_type=raw.get("flow_type"),
        current_stage=raw.get("current_stage"),
        branch=(_safe_get(raw, "worktree", "branch")
                or _safe_get(raw, "environment_config", "branch")),
        worktree_path=_safe_get(raw, "worktree", "path"),
        merge_target=(raw.get("merge_target")
                      or _safe_get(raw, "environment_config", "merge_target")),
        ext_model=_safe_get(raw, "external_cross_review", "model"),
        sub_project=raw.get("sub_project"),
        artifact_root=raw.get("artifact_root"),
        raw=raw,
        discovery_source=source,
    )


def merge_param(explicit: Any, context_value: Any) -> tuple[Any, bool]:
    """参数合并：返回 (effective_value, was_overridden_from_context)。

    - explicit 非空 → 用 explicit · 若 context 也有值且不同 → was_overridden=True
    - explicit 为 None / 空 → 用 context · was_overridden=False
    """
    if explicit is not None and explicit != "":
        if context_value is not None and context_value != explicit:
            return explicit, True
        return explicit, False
    return context_value, False
