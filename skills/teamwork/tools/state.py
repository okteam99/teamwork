#!/usr/bin/env python3
"""
state.py — Teamwork Feature state.json maintenance tool.

红线：
1. 声明式接口：禁止暴露 jq path / json patch / dot-notation；每个改动语义化命名子命令。
2. cite-only output：默认返回 updated_fields + cited_fields，不返回全 state.json。
3. R3 自动满足：每次调用 = 一次原子 read-modify-write，不留中段。
4. 逃生舱有代价：raw-write 自动追加 concerns WARN「raw-write 跳过校验」。

P1（已实现）：snapshot / validate / raw-read / raw-write
P2（已实现）：enter-stage / satisfy-gate / complete-stage
P3（已实现）：ship-sanitize / ship-push / ship-confirm-merged / ship-cleanup / ship-closed
P4（已实现）：add-concern / bug-frontmatter / micro-validate（pm-decision 已物理删除 · v7 fossil 写错 schema · v8 用 pm_acceptance-complete --decision）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ─── 常量 ──────────────────────────────────────────────────────────────

LEGAL_STAGES = {
    "goal",
    "ui_design",
    "panorama_sync",
    "blueprint",
    "blueprint_lite",
    "dev",
    "review",
    "test",
    "browser_e2e",
    "pm_acceptance",
    "ship",
    "completed",
}

GATE_NAMES = ("input_satisfied", "process_satisfied", "output_satisfied")

SHIP_PHASE_ENUM = {None, "pushed", "merged", "closed_unmerged"}
SHIP_SHIPPED_ENUM = {None, "pushed", "merged", "closed_unmerged", "abandoned", "failed"}
SHIP_GIT_HOSTS = {"github", "gitlab", "gitlab-self-hosted", "gitee", "bitbucket", "unknown"}
SHIP_MR_METHODS = {"cli-gh", "cli-glab", "url-fallback", "unknown-platform"}
SHIP_DETECTION_METHODS = {"branch-contains", "user-reported"}
SHIP_FINALIZE_PUSH_REASONS = {"conflict", "protect-rule", "network", "other"}
SHIP_CLEANUP_ENUM = {"cleaned", "deferred", "n_a"}

CONCERN_SEVERITY = {"INFO", "WARN", "ERROR"}

# 各 flow_type 的 canonical 转移图（current_stage → legal_next_stages）
# 注：ui_design / browser_e2e 是可选 Stage（PMO 在 enter-stage 时按 spec 决策跳过 vs 启用）
FEATURE_FLOW: dict[str, list[str]] = {
    "goal": ["ui_design", "blueprint"],
    "ui_design": ["panorama_sync", "blueprint"],   # 条件:--panorama-changed=true → panorama_sync · false → blueprint
    "panorama_sync": ["blueprint"],
    "blueprint": ["dev"],
    "dev": ["review"],
    "review": ["test", "dev"],          # review 失败回 dev
    "test": ["browser_e2e", "pm_acceptance"],
    "browser_e2e": ["pm_acceptance"],
    "pm_acceptance": ["ship", "dev"],   # 拒绝回 dev
    "ship": ["completed"],
    "completed": [],
}

BUG_FLOW: dict[str, list[str]] = {
    "dev": ["review"],
    "review": ["test", "dev"],
    "test": ["pm_acceptance"],
    "pm_acceptance": ["ship", "dev"],
    "ship": ["completed"],
    "completed": [],
}

# Micro:最轻流程(改文案 / 改配置)· dev → pm_acceptance → ship
MICRO_FLOW: dict[str, list[str]] = {
    "dev": ["pm_acceptance"],
    "pm_acceptance": ["ship", "dev"],
    "ship": ["completed"],
    "completed": [],
}

# 敏捷需求:Feature 砍 blueprint 版 · goal → blueprint_lite → dev → review → test → pm_acceptance → ship
AGILE_FLOW: dict[str, list[str]] = {
    "goal": ["blueprint_lite"],
    "blueprint_lite": ["dev"],
    "dev": ["review"],
    "review": ["test", "dev"],
    "test": ["pm_acceptance"],
    "pm_acceptance": ["ship", "dev"],
    "ship": ["completed"],
    "completed": [],
}

# Feature Planning / 问题排查 不进状态机:由 PMO 主对话执行(详 docs/feature-planning.md)
FLOW_BY_TYPE = {
    "Feature": FEATURE_FLOW,
    "Bug": BUG_FLOW,
    "Micro": MICRO_FLOW,
    "敏捷需求": AGILE_FLOW,
}

# 不进状态机的流程类型(init-feature 拒绝创建 state.json · PMO 主对话直接执行)
NON_STATE_MACHINE_FLOWS = {"Feature Planning", "问题排查"}

# snapshot tier 字段集
SNAPSHOT_CORE_FIELDS = (
    "feature_id",
    "sub_project",
    "flow_type",
    "current_stage",
    "completed_stages",
    "legal_next_stages",
    "ship.phase",
    "ship.shipped",
    "ship.merge_target_push_failed",
    "blocking.pending_user_confirmations",
    "blocking.pending_external_deps",
    "updated_at",
)

SNAPSHOT_STAGE_FIELDS = SNAPSHOT_CORE_FIELDS + (
    "stage_contracts",
    "planned_execution",
    "executor_history",
    "environment_config.merge_target",
    "environment_config.branch",
    "worktree.path",
    "worktree.branch",
)


# ─── IO ────────────────────────────────────────────────────────────────


def state_path(feature: str) -> Path:
    p = Path(feature) / "state.json"
    if not p.exists():
        die(2, f"state.json not found: {p}")
    return p


# ─── Linked-worktree guard (v7.3.10+P0-156) ──────────────────────────
# 治本 ADMIN-F013 case：ship-confirm-merged / ship-cleanup 误在 feature
# worktree 跑 → state.json 写到 worktree → worktree remove --force 时丢失.
# ship-stage.md Step 6 明文要求"cd 到 merge_target 主工作区"再跑这两命令.
# 这里加物化拦截 · 不依赖 agent 自觉.
#
# 旁路：TEAMWORK_BYPASS_MAIN_WORKTREE=1（migration / debug）
# 测试模拟：TEAMWORK_FORCE_LINKED_WORKTREE=<git_dir_value>

MAIN_WORKTREE_BYPASS_ENV = "TEAMWORK_BYPASS_MAIN_WORKTREE"
MAIN_WORKTREE_FORCE_ENV = "TEAMWORK_FORCE_LINKED_WORKTREE"


def _check_main_worktree() -> str | None:
    """检测 cwd 是否在 linked worktree（非 main worktree）.

    Returns: linked worktree git_dir 字符串 if linked · None if main / 非 git repo / 旁路.
    """
    if os.environ.get(MAIN_WORKTREE_BYPASS_ENV):
        return None
    forced = os.environ.get(MAIN_WORKTREE_FORCE_ENV)
    if forced:
        return forced
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True, text=True, check=True, cwd=os.getcwd(),
        )
        git_dir = result.stdout.strip()
        # linked worktree 形如：/path/main/.git/worktrees/{name}
        if "/worktrees/" in git_dir:
            return git_dir
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def _enforce_main_worktree(command: str) -> None:
    """Ship Step 6-9 类命令的 cwd 物化拦截 · linked worktree 直接 die."""
    linked = _check_main_worktree()
    if not linked:
        return
    die(2, json.dumps({
        "verdict": "FAIL",
        "error": f"{command} 必须在主工作区运行 · 当前 cwd 在 linked worktree",
        "cwd": os.getcwd(),
        "linked_worktree_git_dir": linked,
        "hint": (
            "cd 到 merge_target 主工作区（git clone 原仓库位置 · 不是 git worktree add 的 linked 路径）· "
            "git checkout {merge_target} + git pull --ff-only · 再跑此命令"
        ),
        "rule": "v7.3.10+P0-156 物化拦截 · 治本 ADMIN-F013 case state.json 在 worktree 被删丢失",
        "cite": "ship-stage.md § Step 6 切到 merge_target 主工作区",
        "bypass": f"如确需 linked worktree 运行（极少 · 调试场景）· export {MAIN_WORKTREE_BYPASS_ENV}=1",
    }, ensure_ascii=False, indent=2))


# ─── Checksum guard (v7.3.10+P0-148) ───────────────────────────────────
# state.json checksum 自防护 · 跨宿主物理拦截直写 state.json。
# 设计：state.py 每次写都更新 `_state_checksum` · 每次读先 verify · 不一致 → fail。
# 旁路：TEAMWORK_BYPASS_CHECKSUM=1（仅 recover 子命令 / migration / debug）。

CHECKSUM_FIELD = "_state_checksum"
CHECKSUM_BYPASS_ENV = "TEAMWORK_BYPASS_CHECKSUM"


def _compute_checksum(state: dict[str, Any]) -> str:
    """canonical sha256(state without _state_checksum field)."""
    cleaned = {k: v for k, v in state.items() if k != CHECKSUM_FIELD}
    canonical = json.dumps(cleaned, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _verify_checksum(state: dict[str, Any], path: Path) -> None:
    """Verify state.json checksum · die(2) on mismatch (unless bypassed)."""
    if os.environ.get(CHECKSUM_BYPASS_ENV):
        return
    stored = state.get(CHECKSUM_FIELD)
    if stored is None:
        # Legacy state.json (pre-P0-148) — accept silently · 下次写自动 stamp
        return
    expected = _compute_checksum(state)
    if stored != expected:
        die(2, json.dumps({
            "verdict": "FAIL",
            "error": "state.json checksum mismatch · 检测到 state.py 之外的直接修改",
            "path": str(path),
            "stored_prefix": stored[:24],
            "expected_prefix": expected[:24],
            "hint": (
                "选项 1: 用 `state.py recover --feature {path} --reason \"...\"` "
                "重新认证 checksum（追加 concerns WARN audit）\n"
                "选项 2: 设 TEAMWORK_BYPASS_CHECKSUM=1 旁路（仅 debug / migration · 不留 audit）\n"
                "选项 3: `git checkout {path}` 从 git 恢复"
            ),
            "ref": "scripts-policy.md § R7(c) evidence-binding · v7.3.10+P0-148",
        }, ensure_ascii=False, indent=2))


def load_state(feature: str) -> dict[str, Any]:
    path = state_path(feature)
    state = json.loads(path.read_text(encoding="utf-8"))
    _verify_checksum(state, path)
    return state


def die(code: int, msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def get_dotted(obj: Any, dotted: str) -> Any:
    cur = obj
    for seg in dotted.split("."):
        if isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        else:
            return None
    return cur


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_write(path: Path, state: dict[str, Any]) -> None:
    """同目录 temp file + os.replace · 同分区原子。"""
    state["updated_at"] = now_iso()
    state["updated_by"] = state.get("updated_by") or "pmo"
    # v7.3.10+P0-148 checksum guard：每次写后 stamp 新 checksum（基于 _state_checksum 外字段）
    state[CHECKSUM_FIELD] = _compute_checksum(state)
    fd, tmp = tempfile.mkstemp(prefix=".state.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def collect_cited(state: dict[str, Any], cite: str | None) -> dict[str, Any]:
    if not cite:
        return {}
    out = {}
    for f in cite.split(","):
        f = f.strip()
        if f:
            out[f] = get_dotted(state, f)
    return out


def write_or_die(path: Path, state: dict[str, Any]) -> None:
    """写入前 full validate · 任一错误即拒绝（治本）。"""
    errors = validate_state(state)
    if errors:
        die(1, json.dumps({"verdict": "FAIL", "errors": errors, "stage": "pre-write validate"},
                          ensure_ascii=False, indent=2))
    atomic_write(path, state)


def diff_dotted(before: dict, after: dict, fields: list[str]) -> dict[str, Any]:
    """计算指定 dotted 字段的前后差异（用于 updated_fields 输出）。"""
    out = {}
    for f in fields:
        b = get_dotted(before, f)
        a = get_dotted(after, f)
        if b != a:
            out[f] = a
    return out


def compute_legal_next(state: dict[str, Any], current: str) -> list[str]:
    flow_type = state.get("flow_type") or "Feature"
    flow = FLOW_BY_TYPE.get(flow_type, FEATURE_FLOW)
    return list(flow.get(current, []))


# ─── snapshot ──────────────────────────────────────────────────────────


def cmd_snapshot(args: argparse.Namespace) -> None:
    state = load_state(args.feature)

    # raw-write 主动告警(v8.12 · 治本"raw-write 出现 = 状态机缺口"无 PMO 提示)
    from _v8_engine import compute_raw_write_audit
    rw_audit = compute_raw_write_audit(state)

    if args.tier == "full":
        emit({
            "verdict": "OK",
            "snapshot": state,
            **({"raw_write_audit": rw_audit} if rw_audit else {}),
        })
        return

    fields = SNAPSHOT_CORE_FIELDS if args.tier == "core" else SNAPSHOT_STAGE_FIELDS
    snap = {f: get_dotted(state, f) for f in fields}

    extra = {}
    if args.cite:
        for f in args.cite.split(","):
            f = f.strip()
            if f and f not in snap:
                extra[f] = get_dotted(state, f)

    emit(
        {
            "verdict": "OK",
            "tier": args.tier,
            "snapshot": snap,
            **({"cited_extra": extra} if extra else {}),
            **({"raw_write_audit": rw_audit} if rw_audit else {}),
        }
    )


# ─── validate ──────────────────────────────────────────────────────────


def validate_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    cur = state.get("current_stage")
    if cur not in LEGAL_STAGES:
        errors.append(f"current_stage 非法值: {cur!r} ∉ {sorted(LEGAL_STAGES)}")

    completed = state.get("completed_stages") or []
    if not isinstance(completed, list):
        errors.append("completed_stages 必须是数组")
    else:
        for s in completed:
            if s not in LEGAL_STAGES:
                errors.append(f"completed_stages 含非法值: {s!r}")

    legal_next = state.get("legal_next_stages") or []
    if not isinstance(legal_next, list):
        errors.append("legal_next_stages 必须是数组")

    contracts = state.get("stage_contracts") or {}
    if not isinstance(contracts, dict):
        errors.append("stage_contracts 必须是对象")
    else:
        for stage_name, c in contracts.items():
            if not isinstance(c, dict):
                errors.append(f"stage_contracts.{stage_name} 必须是对象")
                continue
            for gate in GATE_NAMES:
                if gate not in c:
                    errors.append(f"stage_contracts.{stage_name}.{gate} 缺失")
            # gate 顺序：output 不能在 process 前 / process 不能在 input 前
            i_ok = c.get("input_satisfied") is True
            p_ok = c.get("process_satisfied") is True
            o_ok = c.get("output_satisfied") is True
            if p_ok and not i_ok:
                errors.append(
                    f"stage_contracts.{stage_name}: process_satisfied=true 但 input_satisfied=false"
                )
            if o_ok and not p_ok:
                errors.append(
                    f"stage_contracts.{stage_name}: output_satisfied=true 但 process_satisfied=false"
                )

    # ship 状态机
    ship = state.get("ship") or {}
    phase = ship.get("phase")
    if phase not in SHIP_PHASE_ENUM:
        errors.append(f"ship.phase 非法值: {phase!r} ∉ {sorted(x for x in SHIP_PHASE_ENUM if x)}")
    shipped = ship.get("shipped")
    if shipped not in SHIP_SHIPPED_ENUM:
        errors.append(
            f"ship.shipped 非法值: {shipped!r} ∉ {sorted(x for x in SHIP_SHIPPED_ENUM if x)}"
        )
    if phase == "merged":
        if not ship.get("merge_commit_hash"):
            errors.append("ship.phase=merged 但 merge_commit_hash 缺失（治本 P0-124）")
        if not ship.get("merge_detection_method"):
            errors.append("ship.phase=merged 但 merge_detection_method 缺失（治本 P0-124）")
        if not ship.get("mr_merged_at"):
            errors.append("ship.phase=merged 但 mr_merged_at 缺失")
    if phase == "pushed" and not ship.get("feature_head_commit"):
        errors.append("ship.phase=pushed 但 feature_head_commit 缺失（第二段 finalize 依赖）")

    # evidence-binding（治本 P0-101 / P0-119）
    ecr = state.get("external_cross_review", {}) or {}
    avail = ecr.get("available_external_clis")
    evidence = ecr.get("detection_evidence")
    # 仅当数组非空（已探测出至少一项）或已 decided 时强校验 evidence
    has_detection_signal = (isinstance(avail, list) and len(avail) > 0) or ecr.get("decided_at")
    if has_detection_signal and not evidence:
        errors.append(
            "external_cross_review 已声明探测结果但 detection_evidence 缺失（P0-101）"
        )

    schema_docs = state.get("global_schema_docs")
    schema_evidence = state.get("global_schema_docs_evidence")
    if isinstance(schema_docs, list) and len(schema_docs) > 0 and not schema_evidence:
        errors.append("global_schema_docs 已填但 global_schema_docs_evidence 缺失（P0-119）")

    # artifact_root 一致性
    root = state.get("artifact_root")
    if not root:
        errors.append("artifact_root 缺失（P0-41 写操作硬门禁前提）")

    return errors


def cmd_validate(args: argparse.Namespace) -> None:
    state = load_state(args.feature)
    errors = validate_state(state)
    if errors:
        emit({"verdict": "FAIL", "errors": errors, "error_count": len(errors)})
        sys.exit(1)
    emit(
        {
            "verdict": "PASS",
            "checks_passed": [
                "stage enum",
                "stage_contracts gate ordering",
                "ship phase/shipped enum",
                "ship merged completeness",
                "evidence-binding (P0-101 / P0-119)",
                "artifact_root present",
            ],
        }
    )


# ─── raw-read ──────────────────────────────────────────────────────────


# ─── enter-stage / satisfy-gate / complete-stage（P2 写） ─────────────


def cmd_enter_stage(args: argparse.Namespace) -> None:
    path = state_path(args.feature)
    state = json.loads(path.read_text(encoding="utf-8"))
    before = json.loads(json.dumps(state))  # deep copy

    target = args.stage
    current = state.get("current_stage")
    legal = state.get("legal_next_stages") or compute_legal_next(state, current)

    if target == current:
        die(3, json.dumps({"verdict": "FAIL",
                           "error": f"already in stage {target!r} · 不重入",
                           "current_stage": current}, ensure_ascii=False, indent=2))

    if target not in LEGAL_STAGES:
        die(3, json.dumps({"verdict": "FAIL",
                           "error": f"非法 stage: {target!r}",
                           "legal_stages": sorted(LEGAL_STAGES)}, ensure_ascii=False, indent=2))

    if not args.allow_skip and target not in legal:
        die(3, json.dumps({
            "verdict": "FAIL",
            "error": f"非法转移: {current!r} → {target!r}",
            "current_stage": current,
            "legal_next_stages": legal,
            "hint": "若刻意跳过 / 回炉 · 加 --allow-skip · 自动记 concerns WARN",
        }, ensure_ascii=False, indent=2))

    # 旧 stage output_satisfied 才能进 completed_stages
    completed = state.setdefault("completed_stages", [])
    if current and current not in completed and current not in ("completed",):
        cur_contract = (state.get("stage_contracts") or {}).get(current) or {}
        if cur_contract.get("output_satisfied") is True:
            completed.append(current)

    state["current_stage"] = target
    state["legal_next_stages"] = compute_legal_next(state, target)

    # 初始化目标 stage_contract 三 gate（不存在则建）
    contracts = state.setdefault("stage_contracts", {})
    contract = contracts.setdefault(target, {
        "input_satisfied": False,
        "process_satisfied": False,
        "output_satisfied": False,
    })
    contract.setdefault("started_at", now_iso())

    if args.allow_skip and target not in legal:
        concerns = state.setdefault("concerns", [])
        concerns.append(f"{now_iso()} WARN enter-stage --allow-skip: {current!r} → {target!r}")

    write_or_die(path, state)

    tracked = ["current_stage", "completed_stages", "legal_next_stages",
               f"stage_contracts.{target}.started_at"]
    emit({
        "verdict": "PASS",
        "transition": f"{current} → {target}",
        "updated_fields": diff_dotted(before, state, tracked),
        "cited_fields": collect_cited(state, args.cite),
        "next_actions": [
            f"satisfy-gate --stage {target} --gate input",
            f"satisfy-gate --stage {target} --gate process",
            f"satisfy-gate --stage {target} --gate output --auto-commit ...",
        ],
    })


EXTERNAL_REVIEW_STAGES = ("blueprint", "review")


def _check_external_review_artifact(state: dict[str, Any], stage: str) -> str | None:
    """v7.3.10+P0-154: 治本 SVC-PLATFORM-F043 跳 codex CR case · 物化拦截.

    当 stage ∈ (blueprint, review) AND {stage}_substeps_config.review_roles[] 显式含 external 时 ·
    校验 {artifact_root}/external-cross-review/ 含 ≥1 *.md 文件.

    Returns: error JSON string if missing, None if PASS / N/A (跳过校验).

    跳过校验场景：
    - stage 不在 (blueprint, review) → 不适用
    - {stage}_substeps_config 不存在（未做 Stage 入口实例化）→ 不能判 opt-in/opt-out · 跳
    - review_roles[] 不含 external → 用户已显式 opt-out · 跳
    - artifact_root 缺失 → 没有可校验路径 · 跳
    """
    if stage not in EXTERNAL_REVIEW_STAGES:
        return None
    config = state.get(f"{stage}_substeps_config") or {}
    if not config:
        return None
    review_roles = config.get("review_roles") or []
    role_names = [r.get("role") if isinstance(r, dict) else r for r in review_roles]
    if "external" not in role_names:
        return None

    artifact_root = state.get("artifact_root")
    if not artifact_root:
        return None

    ext_dir = Path(artifact_root) / "external-cross-review"
    if not ext_dir.is_dir():
        return json.dumps({
            "verdict": "FAIL",
            "error": f"review_roles[] 含 external · 但 external-cross-review/ 目录不存在 · codex CR 未跑",
            "stage": stage,
            "expected_dir": str(ext_dir),
            "hint": "跑 codex CR · 产物落 external-cross-review/{stage}-{model}.md · 或显式 opt-out（review_roles[] 移除 external）",
            "rule": "v7.3.10+P0-154 物化拦截 · 治本 SVC-PLATFORM-F043 跳 codex CR case",
        }, ensure_ascii=False, indent=2)

    md_files = list(ext_dir.glob("*.md"))
    if not md_files:
        return json.dumps({
            "verdict": "FAIL",
            "error": f"review_roles[] 含 external · 但 external-cross-review/*.md 不存在 · codex 产物缺失",
            "stage": stage,
            "expected_pattern": f"{ext_dir}/*.md",
            "hint": "跑 codex CR · 产物落 external-cross-review/{stage}-{model}.md · 或显式 opt-out（review_roles[] 移除 external）",
            "rule": "v7.3.10+P0-154 物化拦截 · 治本 SVC-PLATFORM-F043 跳 codex CR case",
        }, ensure_ascii=False, indent=2)

    return None


def cmd_satisfy_gate(args: argparse.Namespace) -> None:
    path = state_path(args.feature)
    state = json.loads(path.read_text(encoding="utf-8"))
    before = json.loads(json.dumps(state))

    stage = args.stage
    gate = args.gate  # input / process / output

    if state.get("current_stage") != stage:
        die(1, json.dumps({"verdict": "FAIL",
                           "error": f"current_stage={state.get('current_stage')!r} ≠ {stage!r}",
                           "hint": "先 enter-stage 再 satisfy-gate"}, ensure_ascii=False, indent=2))

    contracts = state.setdefault("stage_contracts", {})
    contract = contracts.setdefault(stage, {
        "input_satisfied": False, "process_satisfied": False, "output_satisfied": False,
    })

    # gate 顺序硬约束
    if gate == "process" and contract.get("input_satisfied") is not True:
        die(1, _gate_order_err(stage, gate, "input_satisfied"))
    if gate == "output" and contract.get("process_satisfied") is not True:
        die(1, _gate_order_err(stage, gate, "process_satisfied"))

    # v7.3.10+P0-154: external review artifact 物化拦截（治本 SVC-PLATFORM-F043 跳 codex CR）
    if gate == "output":
        err = _check_external_review_artifact(state, stage)
        if err:
            die(1, err)

    contract[f"{gate}_satisfied"] = True

    if args.artifacts:
        art_obj = contract.setdefault("artifacts", {})
        for a in args.artifacts.split(","):
            a = a.strip()
            if a:
                art_obj[a] = "done"

    if args.auto_commit:
        existing = contract.get("auto_commit")
        if isinstance(existing, list):
            existing.append(args.auto_commit)
        elif existing in (None, ""):
            contract["auto_commit"] = args.auto_commit
        else:
            # 已有单值 + 又来一个 → 自动升数组
            contract["auto_commit"] = [existing, args.auto_commit]

    write_or_die(path, state)

    tracked = [
        f"stage_contracts.{stage}.{gate}_satisfied",
        f"stage_contracts.{stage}.artifacts",
        f"stage_contracts.{stage}.auto_commit",
    ]
    emit({
        "verdict": "PASS",
        "stage": stage,
        "gate": gate,
        "updated_fields": diff_dotted(before, state, tracked),
        "cited_fields": collect_cited(state, args.cite),
        "remaining_gates": [g for g in GATE_NAMES
                            if contract.get(g) is not True],
    })


def _gate_order_err(stage: str, gate: str, missing: str) -> str:
    return json.dumps({
        "verdict": "FAIL",
        "error": f"stage_contracts.{stage}: 不能 satisfy {gate} · 前置 {missing}=false",
        "hint": "按 input → process → output 顺序",
    }, ensure_ascii=False, indent=2)


def cmd_complete_stage(args: argparse.Namespace) -> None:
    """收尾 = output gate satisfied + completed_at + duration_minutes + 准备转移。"""
    path = state_path(args.feature)
    state = json.loads(path.read_text(encoding="utf-8"))
    before = json.loads(json.dumps(state))

    stage = args.stage
    if state.get("current_stage") != stage:
        die(1, json.dumps({"verdict": "FAIL",
                           "error": f"current_stage={state.get('current_stage')!r} ≠ {stage!r}"},
                          ensure_ascii=False, indent=2))

    contract = (state.get("stage_contracts") or {}).get(stage)
    if not contract:
        die(1, json.dumps({"verdict": "FAIL",
                           "error": f"stage_contracts.{stage} 不存在"},
                          ensure_ascii=False, indent=2))

    # 三 gate 必须全 true（complete = 终结判定）
    missing = [g for g in GATE_NAMES if contract.get(g) is not True]
    if missing:
        die(1, json.dumps({
            "verdict": "FAIL",
            "error": f"stage_contracts.{stage} 三 gate 未全部 satisfied",
            "missing_gates": missing,
            "hint": "先 satisfy-gate 把缺的补齐",
        }, ensure_ascii=False, indent=2))

    if args.auto_commit and not contract.get("auto_commit"):
        contract["auto_commit"] = args.auto_commit

    completed_at = now_iso()
    contract["completed_at"] = completed_at
    started_at = contract.get("started_at")
    if started_at:
        try:
            t0 = datetime.strptime(started_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            t1 = datetime.strptime(completed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            contract["duration_minutes"] = max(0, int((t1 - t0).total_seconds() // 60))
        except ValueError:
            pass

    write_or_die(path, state)

    tracked = [
        f"stage_contracts.{stage}.completed_at",
        f"stage_contracts.{stage}.duration_minutes",
        f"stage_contracts.{stage}.auto_commit",
    ]
    next_legal = compute_legal_next(state, stage)
    emit({
        "verdict": "PASS",
        "stage": stage,
        "updated_fields": diff_dotted(before, state, tracked),
        "cited_fields": collect_cited(state, args.cite),
        "next_actions": [f"enter-stage --stage {s}" for s in next_legal] or
                        ["流程结束 · 无后续 stage"],
    })


# ─── ship-* (P3) ──────────────────────────────────────────────────────


def _ship_load(args: argparse.Namespace) -> tuple[Path, dict, dict, dict]:
    """加载 state · 校验 current_stage=ship · 返回 (path, state, before-snapshot, ship-子对象)。"""
    path = state_path(args.feature)
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("current_stage") != "ship":
        die(1, json.dumps({"verdict": "FAIL",
                           "error": f"current_stage={state.get('current_stage')!r} ≠ 'ship' · 先 enter-stage --stage ship"},
                          ensure_ascii=False, indent=2))
    before = json.loads(json.dumps(state))
    ship = state.setdefault("ship", {})
    ship.setdefault("started_at", now_iso())
    return path, state, before, ship


def cmd_ship_sanitize(args: argparse.Namespace) -> None:
    """Step 1：净化记录（不改 phase）。"""
    path, state, before, ship = _ship_load(args)
    log = ship.setdefault("sanitize_log", {
        "residual_commits": [], "cleaned_files": [], "suspicious_files": [],
    })
    if args.residual_commits:
        log["residual_commits"] = json.loads(args.residual_commits)
    if args.cleaned_files:
        log["cleaned_files"] = [s.strip() for s in args.cleaned_files.split(",") if s.strip()]
    if args.suspicious_files:
        log["suspicious_files"] = json.loads(args.suspicious_files)

    write_or_die(path, state)
    emit({
        "verdict": "PASS",
        "stage": "ship-sanitize",
        "updated_fields": diff_dotted(before, state, [
            "ship.sanitize_log.residual_commits",
            "ship.sanitize_log.cleaned_files",
            "ship.sanitize_log.suspicious_files",
        ]),
        "cited_fields": collect_cited(state, args.cite),
        "warnings": (["sanitize_log.residual_commits 非空 · PMO 完成报告必须高亮（前序 Stage 漏 commit）"]
                     if log["residual_commits"] else []) +
                    (["sanitize_log.suspicious_files 非空 · PMO 完成报告必须列出灰名单 · 不自动处理"]
                     if log["suspicious_files"] else []),
    })


def cmd_ship_push(args: argparse.Namespace) -> None:
    """Step 2-3：phase=null → phase=pushed · 必带 5 件套 evidence。"""
    path, state, before, ship = _ship_load(args)
    cur_phase = ship.get("phase")
    # 允许 null → pushed · 也允许 closed_unmerged → pushed（重开 MR 重 push）
    if cur_phase not in (None, "closed_unmerged"):
        die(1, _ship_phase_err(cur_phase, "pushed",
                               "ship-push 仅允许 null → pushed 或 closed_unmerged → pushed"))

    if args.git_host not in SHIP_GIT_HOSTS:
        die(1, _enum_err("--git-host", args.git_host, SHIP_GIT_HOSTS))
    if args.mr_creation_method not in SHIP_MR_METHODS:
        die(1, _enum_err("--mr-creation-method", args.mr_creation_method, SHIP_MR_METHODS))
    if not args.mr_url and not args.mr_create_url:
        die(1, json.dumps({"verdict": "FAIL",
                           "error": "--mr-url 与 --mr-create-url 必至少一个非空"},
                          ensure_ascii=False, indent=2))
    if args.mr_creation_method.startswith("cli-") and not args.mr_url:
        die(1, json.dumps({"verdict": "FAIL",
                           "error": f"mr_creation_method={args.mr_creation_method} 必带 --mr-url（CLI 实创建）"},
                          ensure_ascii=False, indent=2))
    if args.mr_creation_method in {"url-fallback", "unknown-platform"} and not args.mr_create_url:
        die(1, json.dumps({"verdict": "FAIL",
                           "error": f"mr_creation_method={args.mr_creation_method} 必带 --mr-create-url（兜底链接）"},
                          ensure_ascii=False, indent=2))

    ship["phase"] = "pushed"
    ship["shipped"] = "pushed"
    ship["feature_head_commit"] = args.feature_head_commit
    ship["git_host"] = args.git_host
    ship["mr_creation_method"] = args.mr_creation_method
    ship["mr_url"] = args.mr_url
    ship["mr_create_url"] = args.mr_create_url
    ship["feature_pushed_at"] = args.feature_pushed_at or now_iso()

    write_or_die(path, state)
    emit({
        "verdict": "PASS",
        "stage": "ship-push",
        "transition": f"{cur_phase} → pushed",
        "updated_fields": diff_dotted(before, state, [
            "ship.phase", "ship.shipped", "ship.feature_head_commit",
            "ship.git_host", "ship.mr_creation_method",
            "ship.mr_url", "ship.mr_create_url", "ship.feature_pushed_at",
        ]),
        "cited_fields": collect_cited(state, args.cite),
        "next_actions": [
            "等用户在平台合并 MR · 选 1 后执行 `ship-confirm-merged`",
            "用户选 3 关闭未合并 → `ship-closed`",
        ],
    })


def cmd_ship_confirm_merged(args: argparse.Namespace) -> None:
    """Step 4-8：pushed → merged · 含合并 evidence + 可选 finalize-push 状态。

    🔴 P0-124 治本：必带 merge_commit_hash + merge_detection_method。
    🔴 P0-156 治本：必须在主工作区运行（非 linked worktree）· 治本 ADMIN-F013 case。
    """
    _enforce_main_worktree("ship-confirm-merged")
    path, state, before, ship = _ship_load(args)
    if ship.get("phase") != "pushed":
        die(1, _ship_phase_err(ship.get("phase"), "merged",
                               "ship-confirm-merged 仅允许 pushed → merged"))

    if args.merge_detection_method not in SHIP_DETECTION_METHODS:
        die(1, _enum_err("--merge-detection-method", args.merge_detection_method, SHIP_DETECTION_METHODS))

    ship["phase"] = "merged"
    ship["shipped"] = "merged"
    ship["merge_commit_hash"] = args.merge_commit_hash
    ship["merge_detection_method"] = args.merge_detection_method
    ship["mr_merged_at"] = args.mr_merged_at or now_iso()

    # finalize-push 状态（Step 8 push merge_target）· 二选一可选
    if args.merge_target_pushed_at:
        ship["merge_target_pushed_at"] = args.merge_target_pushed_at
        ship["merge_target_push_failed"] = False
        ship["merge_target_push_failed_reason"] = None
    elif args.merge_target_push_failed:
        if not args.failed_reason or args.failed_reason not in SHIP_FINALIZE_PUSH_REASONS:
            die(1, _enum_err("--failed-reason", args.failed_reason, SHIP_FINALIZE_PUSH_REASONS))
        ship["merge_target_pushed_at"] = None
        ship["merge_target_push_failed"] = True
        ship["merge_target_push_failed_reason"] = args.failed_reason
        # 自动追加 concerns
        concerns = state.setdefault("concerns", [])
        concerns.append(
            f"{now_iso()} WARN ship-finalize-push 失败（{args.failed_reason}）→ "
            f"降级到 feature 分支 push · merge_target 上 state.json 仍为 phase=pushed · "
            f"用户可手动 cherry-pick 同步状态"
        )

    warnings = []
    if args.merge_detection_method == "user-reported":
        warnings.append("merge_detection_method=user-reported · 用户自报 · 自动 git 校验未通过 · concerns 已加 INFO")
        concerns = state.setdefault("concerns", [])
        concerns.append(
            f"{now_iso()} INFO ship-confirm-merged: user-reported merge_commit={args.merge_commit_hash}"
        )

    write_or_die(path, state)
    emit({
        "verdict": "PASS",
        "stage": "ship-confirm-merged",
        "transition": "pushed → merged",
        "updated_fields": diff_dotted(before, state, [
            "ship.phase", "ship.shipped", "ship.merge_commit_hash",
            "ship.merge_detection_method", "ship.mr_merged_at",
            "ship.merge_target_pushed_at", "ship.merge_target_push_failed",
            "ship.merge_target_push_failed_reason",
        ]),
        "cited_fields": collect_cited(state, args.cite),
        "warnings": warnings,
        "next_actions": ["ship-cleanup --status {cleaned|deferred|n_a}"],
    })


def cmd_ship_cleanup(args: argparse.Namespace) -> None:
    """Step 9：worktree 清理状态记录。

    🔴 P0-124 治本硬门禁：destructive op 前必须 phase=merged + shipped=merged。
    🔴 P0-156 治本：必须在主工作区运行（非 linked worktree）· 治本 ADMIN-F013 case。
    """
    _enforce_main_worktree("ship-cleanup")
    path, state, before, ship = _ship_load(args)
    if args.status not in SHIP_CLEANUP_ENUM:
        die(1, _enum_err("--status", args.status, SHIP_CLEANUP_ENUM))

    # 🔴 hard gate：cleanup 前 phase 必须 merged（worktree=off 时 status=n_a 例外）
    if args.status == "cleaned":
        if ship.get("phase") != "merged" or ship.get("shipped") != "merged":
            die(1, json.dumps({
                "verdict": "BLOCKED",
                "error": "ship-cleanup --status cleaned 被拒：合并未确认（治本 P0-124）",
                "current_ship_phase": ship.get("phase"),
                "current_ship_shipped": ship.get("shipped"),
                "hint": "先 `ship-confirm-merged` · 或 worktree=off 时用 --status n_a",
            }, ensure_ascii=False, indent=2))
        if not ship.get("merge_commit_hash"):
            die(1, json.dumps({
                "verdict": "BLOCKED",
                "error": "ship-cleanup 被拒：merge_commit_hash 缺失（治本 P0-124）",
            }, ensure_ascii=False, indent=2))

    ship["worktree_cleanup"] = args.status

    # cleanup=cleaned 时即可视为 Stage 完结（PMO 后续走 enter-stage --stage completed）
    if args.status == "cleaned":
        ship["completed_at"] = now_iso()

    write_or_die(path, state)
    emit({
        "verdict": "PASS",
        "stage": "ship-cleanup",
        "updated_fields": diff_dotted(before, state, [
            "ship.worktree_cleanup", "ship.completed_at",
        ]),
        "cited_fields": collect_cited(state, args.cite),
        "next_actions": ["satisfy-gate --stage ship --gate output", "complete-stage --stage ship",
                         "enter-stage --stage completed"]
        if args.status in ("cleaned", "n_a") else
        ["待 worktree 清理后再次 ship-cleanup --status cleaned"],
    })


def cmd_ship_closed(args: argparse.Namespace) -> None:
    """异常段：MR 被关闭未合并 → phase=closed_unmerged。"""
    path, state, before, ship = _ship_load(args)
    if ship.get("phase") not in ("pushed", None):
        die(1, _ship_phase_err(ship.get("phase"), "closed_unmerged",
                               "ship-closed 仅允许 null/pushed → closed_unmerged"))
    ship["phase"] = "closed_unmerged"
    ship["shipped"] = "closed_unmerged" if not args.abandon else "abandoned"
    if args.abandon:
        ship["completed_at"] = now_iso()
    if args.reason:
        concerns = state.setdefault("concerns", [])
        concerns.append(f"{now_iso()} INFO ship-closed: {args.reason}")

    write_or_die(path, state)
    emit({
        "verdict": "PASS",
        "stage": "ship-closed",
        "transition": f"pushed → {'abandoned' if args.abandon else 'closed_unmerged'}",
        "updated_fields": diff_dotted(before, state, [
            "ship.phase", "ship.shipped", "ship.completed_at",
        ]),
        "cited_fields": collect_cited(state, args.cite),
        "next_actions": (["enter-stage --stage completed"] if args.abandon else
                         ["ship-push（重开 MR 重新 push）",
                          "ship-closed --abandon（彻底放弃 Feature）",
                          "保持现状 · 用户后续决策"]),
    })


def _ship_phase_err(cur: str | None, target: str, hint: str) -> str:
    return json.dumps({
        "verdict": "FAIL",
        "error": f"ship.phase 非法转移: {cur!r} → {target!r}",
        "hint": hint,
    }, ensure_ascii=False, indent=2)


def _enum_err(name: str, val: Any, enum: set) -> str:
    return json.dumps({
        "verdict": "FAIL",
        "error": f"{name} 非法值: {val!r} ∉ {sorted(enum)}",
    }, ensure_ascii=False, indent=2)


def cmd_raw_read(args: argparse.Namespace) -> None:
    state = load_state(args.feature)
    from _v8_engine import compute_raw_write_audit
    rw_audit = compute_raw_write_audit(state)

    if args.field:
        val = get_dotted(state, args.field)
        emit({
            "verdict": "OK",
            "field": args.field,
            "value": val,
            **({"raw_write_audit": rw_audit} if rw_audit else {}),
        })
        return
    emit({
        "verdict": "OK",
        "warning": "raw-read 全量返回 · 仅 debug/migration 使用",
        "state": state,
        **({"raw_write_audit": rw_audit} if rw_audit else {}),
    })


def cmd_raw_write(args: argparse.Namespace) -> None:
    """🚪 逃生舱：跳过 schema/状态机校验直写 · 自动追加 concerns WARN。

    每条 --set key=val · val 优先按 JSON 解析（true/false/null/number/array/object）失败则当字符串。
    """
    if not args.set:
        die(2, json.dumps({"verdict": "FAIL", "error": "至少一个 --set key=val"},
                          ensure_ascii=False, indent=2))
    if not args.reason:
        die(2, json.dumps({"verdict": "FAIL",
                           "error": "raw-write 必带 --reason · 该理由会自动写入 concerns"},
                          ensure_ascii=False, indent=2))
    path = state_path(args.feature)
    state = json.loads(path.read_text(encoding="utf-8"))

    applied: list[tuple[str, Any]] = []
    for kv in args.set:
        if "=" not in kv:
            die(2, json.dumps({"verdict": "FAIL", "error": f"--set 需 key=val 形式: {kv!r}"},
                              ensure_ascii=False, indent=2))
        k, _, raw = kv.partition("=")
        try:
            val = json.loads(raw)
        except json.JSONDecodeError:
            val = raw
        # 写入 dotted path · 自动建中间 dict
        cur = state
        segs = k.split(".")
        for seg in segs[:-1]:
            cur = cur.setdefault(seg, {})
            if not isinstance(cur, dict):
                die(2, json.dumps({"verdict": "FAIL",
                                   "error": f"--set {k}: 中段 {seg!r} 非 dict 无法下钻"},
                                  ensure_ascii=False, indent=2))
        cur[segs[-1]] = val
        applied.append((k, val))

    state.setdefault("concerns", []).append(
        f"{now_iso()} WARN raw-write 跳过校验 · 改动 {len(applied)} 字段 · 理由：{args.reason}"
    )

    # 不调 write_or_die · raw-write 明确允许 invalid state
    atomic_write(path, state)
    emit({
        "verdict": "OK",
        "warning": "raw-write 跳过 schema/状态机校验 · 已记 concerns WARN",
        "applied": [{"path": k, "value": v} for k, v in applied],
        "reason": args.reason,
    })


# ─── P4: add-concern ─────────────────────────────────────────────────
#
# 注:cmd_pm_decision(v7 fossil · 写 stage_contracts.pm_acceptance.decision
# 顶层位 · v8 规范是 evidence.decision)已物理删除 —— 是 landmine,留着会
# 让 reader 漂移(治本 ADMIN-F013 case · 详 _v8_stage_specs._pm_decision_value)。


def cmd_add_concern(args: argparse.Namespace) -> None:
    path = state_path(args.feature)
    state = json.loads(path.read_text(encoding="utf-8"))
    if args.severity not in CONCERN_SEVERITY:
        die(1, _enum_err("--severity", args.severity, CONCERN_SEVERITY))

    line = f"{now_iso()} {args.severity} {args.message}"
    concerns = state.setdefault("concerns", [])
    if line in concerns:
        emit({"verdict": "OK", "skipped": "重复 concern · 不重复追加"})
        return
    concerns.append(line)
    # add-concern 不触发 full validate（concerns 本身常用于记 invalid 状态的 audit trail）
    atomic_write(path, state)
    emit({
        "verdict": "PASS",
        "stage": "add-concern",
        "appended": line,
        "concerns_count": len(concerns),
    })


# ─── P4: bug-frontmatter（YAML frontmatter 维护） ─────────────────────


def _bug_locate(feature: str, bug_id: str) -> Path:
    """{feature}/bugfix/BUG-{id}-*.md · id 不区分大小写。"""
    base = Path(feature) / "bugfix"
    if not base.exists():
        die(2, json.dumps({"verdict": "FAIL", "error": f"bugfix dir 不存在: {base}"},
                          ensure_ascii=False, indent=2))
    pattern = re.compile(rf"^{re.escape(bug_id)}(-.*)?\.md$", re.IGNORECASE)
    matches = sorted(p for p in base.iterdir() if p.is_file() and pattern.match(p.name))
    if not matches:
        die(2, json.dumps({"verdict": "FAIL",
                           "error": f"未找到 BUG 文件: {base}/{bug_id}-*.md"},
                          ensure_ascii=False, indent=2))
    if len(matches) > 1:
        die(2, json.dumps({"verdict": "FAIL",
                           "error": f"BUG id 多重匹配 · 请用全名: {[p.name for p in matches]}"},
                          ensure_ascii=False, indent=2))
    return matches[0]


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """简易 YAML frontmatter 解析：仅支持平铺 key: value（值按 JSON 解析失败则当字符串）。"""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n---", 2)
    if len(parts) < 2:
        return {}, text
    fm_text = parts[0][3:].lstrip("\n")  # 去掉首 "---\n"
    body = parts[1].lstrip("\n")
    fm: dict[str, Any] = {}
    for line in fm_text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, _, raw = line.partition(":")
        k = k.strip()
        raw = raw.strip()
        if raw == "" or raw.lower() == "null" or raw == "~":
            fm[k] = None
        else:
            try:
                fm[k] = json.loads(raw)
            except json.JSONDecodeError:
                fm[k] = raw.strip('"').strip("'")
    return fm, body


def _dump_frontmatter(fm: dict[str, Any], body: str) -> str:
    lines = ["---"]
    for k, v in fm.items():
        if v is None:
            lines.append(f"{k}: null")
        elif isinstance(v, (str, bool, int, float)):
            # 字符串若含特殊字符则 JSON 引号
            if isinstance(v, str) and (":" in v or "#" in v or v.startswith(("[", "{", "&", "*"))):
                lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
            else:
                lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        else:
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + body


def _bug_validate_ship_machine(fm: dict[str, Any]) -> list[str]:
    """对 BUG-REPORT.md frontmatter 应用与 ship 同形态的状态机校验。"""
    errors: list[str] = []
    phase = fm.get("phase")
    if phase not in {None, "summarized", "shipping", "pushed", "merged", "closed_unmerged", "shipped"}:
        errors.append(f"frontmatter.phase 非法值: {phase!r}")
    shipped = fm.get("shipped")
    if shipped not in {None, "pushed", "merged", "closed_unmerged", "abandoned", "failed", False}:
        errors.append(f"frontmatter.shipped 非法值: {shipped!r}")
    if phase in {"merged", "shipped"} or shipped == "merged":
        for req in ("merge_commit_hash", "mr_merged_at"):
            if not fm.get(req):
                errors.append(f"phase=merged/shipped 但 {req} 缺失（治本 P0-124 镜像）")
    if phase == "pushed" and not fm.get("feature_head_commit"):
        errors.append("phase=pushed 但 feature_head_commit 缺失")
    return errors


def cmd_bug_frontmatter(args: argparse.Namespace) -> None:
    path = _bug_locate(args.feature, args.bug_id)
    text = path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)
    before = dict(fm)

    applied: list[tuple[str, Any]] = []
    for kv in (args.set or []):
        if "=" not in kv:
            die(2, json.dumps({"verdict": "FAIL", "error": f"--set 需 key=val: {kv!r}"},
                              ensure_ascii=False, indent=2))
        k, _, raw = kv.partition("=")
        try:
            val = json.loads(raw)
        except json.JSONDecodeError:
            val = raw
        fm[k.strip()] = val
        applied.append((k.strip(), val))

    if args.validate_ship:
        errs = _bug_validate_ship_machine(fm)
        if errs:
            die(1, json.dumps({"verdict": "FAIL", "errors": errs,
                               "stage": "bug-frontmatter validate"},
                              ensure_ascii=False, indent=2))

    fm.pop("updated_at", None)  # 移到末尾保持人读直觉
    fm["updated_at"] = now_iso()
    new_text = _dump_frontmatter(fm, body)
    # 原子写
    fd, tmp = tempfile.mkstemp(prefix=".bug.", suffix=".tmp", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(new_text)
    os.replace(tmp, path)

    diff = {k: v for k, v in fm.items() if before.get(k) != v and k != "updated_at"}
    emit({
        "verdict": "PASS",
        "stage": "bug-frontmatter",
        "file": str(path),
        "applied": [{"path": k, "value": v} for k, v in applied],
        "frontmatter_diff": diff,
        "validate_ship": bool(args.validate_ship),
    })


# ─── P4: micro-validate ──────────────────────────────────────────────


def cmd_micro_validate(args: argparse.Namespace) -> None:
    """Micro 流程无元数据载体 · 只校验 commit 已合入 origin/{merge_target}。"""
    cmd = ["git", "merge-base", "--is-ancestor", args.commit, f"origin/{args.merge_target}"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=args.cwd or None)
    except FileNotFoundError:
        die(2, json.dumps({"verdict": "FAIL", "error": "git not found in PATH"},
                          ensure_ascii=False, indent=2))

    if result.returncode == 0:
        emit({
            "verdict": "PASS",
            "stage": "micro-validate",
            "commit": args.commit,
            "merged_into": f"origin/{args.merge_target}",
            "evidence": {
                "command": " ".join(cmd),
                "exit_code": 0,
                "checked_at": now_iso(),
            },
        })
        return
    if result.returncode == 1:
        emit({
            "verdict": "BLOCKED",
            "stage": "micro-validate",
            "commit": args.commit,
            "error": f"commit {args.commit} 不在 origin/{args.merge_target} 中",
            "evidence": {
                "command": " ".join(cmd),
                "exit_code": 1,
                "stderr": result.stderr.strip(),
                "checked_at": now_iso(),
            },
            "hint": "用户尚未在平台合并 / 拉错 merge_target / commit hash 错",
        })
        sys.exit(1)
    # 其他错误（commit 不存在 / fetch 没跑）
    die(1, json.dumps({
        "verdict": "FAIL",
        "stage": "micro-validate",
        "error": f"git 检测异常 exit {result.returncode}",
        "stderr": result.stderr.strip(),
        "hint": "先 `git fetch origin {merge_target}` · 或检查 commit hash",
    }, ensure_ascii=False, indent=2))


# ─── argparse ──────────────────────────────────────────────────────────



# ─── init-feature / recover (v7.3.10+P0-148) ──────────────────────────


DEFAULT_INITIAL_STAGE = {
    "Feature": "goal",
    "Bug": "dev",
    "Micro": "dev",
    "敏捷需求": "goal",  # 敏捷需求 FLOW = goal → blueprint_lite → ... · blueprint_lite-start 前置要 goal 完成
}


def _parse_workspace_registry(ws_path: Path) -> dict:
    """解析 teamwork-space.md 子项目清单表 → {prefix: docs_root}。

    按列名(缩写 / docs_root)定位 · 容忍列序差异 / 多余列。解析不出返回 {}。
    """
    try:
        lines = ws_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    reg: dict = {}
    abbr_i = None
    root_i = None
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            abbr_i = None
            root_i = None
            continue
        cells = [c.strip().strip("`").strip() for c in s.strip("|").split("|")]
        if abbr_i is None:
            if any("缩写" in c for c in cells) and any("docs_root" in c for c in cells):
                for i, c in enumerate(cells):
                    if "缩写" in c:
                        abbr_i = i
                    if "docs_root" in c:
                        root_i = i
            continue
        if cells and all(set(c) <= set("-: ") for c in cells if c):
            continue  # 分隔行 |---|---|
        if abbr_i < len(cells) and root_i < len(cells):
            abbr = cells[abbr_i]
            root = cells[root_i].rstrip("/")
            if abbr and root:
                reg[abbr] = root
    return reg


def _git_toplevel(start: Path):
    """git rev-parse --show-toplevel · 失败返 None。"""
    try:
        r = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _check_artifact_routing(feature_dir: Path, feature_id: str) -> dict:
    """校验 Feature artifact 路径 + ID 前缀 落在 teamwork-space.md 注册的 docs_root 下。

    治本 F049 case:代码在 apps/partner/(属 PTR)· artifact 却建成 SVC-PLATFORM
    前缀 + 落在仓库根 docs/features/ · 错前缀 + 错路径无任何拦截照样 PASS。
    docs_root 是 teamwork-space.md 路由权威(conventions.md §8)。

    返回 {verdict: PASS|FAIL|WARN|SKIP, ...}。
    """
    import re as _re
    if os.environ.get("TEAMWORK_BYPASS_ROUTING_CHECK") == "1":
        return {"verdict": "SKIP", "reason": "TEAMWORK_BYPASS_ROUTING_CHECK=1"}
    top = _git_toplevel(Path.cwd())
    if not top:
        return {"verdict": "SKIP", "reason": "cwd 不在 git 仓库"}
    ws = top / "teamwork-space.md"
    if not ws.exists():
        ws = top / "teamwork_space.md"  # 容错 legacy 下划线名
    if not ws.exists():
        return {"verdict": "SKIP", "reason": "无 teamwork-space.md(单项目仓库)"}
    reg = _parse_workspace_registry(ws)
    if not reg:
        return {"verdict": "SKIP", "reason": "teamwork-space.md 子项目清单解析为空"}
    m = _re.match(r"^(.+?)-[FBM]\d+", feature_id)
    if not m:
        return {"verdict": "SKIP", "reason": f"feature_id {feature_id!r} 抽不出前缀"}
    prefix = m.group(1)
    if prefix not in reg:
        return {
            "verdict": "WARN",
            "prefix": prefix,
            "known_prefixes": sorted(reg),
            "message": (
                f"前缀 {prefix!r} 未在 teamwork-space.md 子项目清单注册 · "
                f"新子项目请先注册 · 或前缀拼错"
            ),
        }
    expected = reg[prefix].rstrip("/")
    try:
        actual = str(feature_dir.resolve().relative_to(top.resolve()).parent)
    except ValueError:
        return {"verdict": "SKIP", "reason": "feature 路径不在仓库内"}
    actual = actual.rstrip("/")
    if actual != expected:
        return {
            "verdict": "FAIL",
            "prefix": prefix,
            "expected_docs_root": expected,
            "actual_path": actual,
        }
    return {"verdict": "PASS", "prefix": prefix, "docs_root": expected}


# ─── prepare-check audit 门禁(v8.14)─────────────────────────────────────
# 治本 PTR-F054 case:AI 跳过 prepare 子流程 直接 init-feature → 用错 prefix /
# 选错 features_root / 漏 ID 冲突预检。已物化的 prepare-check 命令不被调用 =
# 等同没物化。
#
# 设计:
# - prepare-check 每次跑成功 → 追写 jsonl audit(~/.teamwork/prepare_check_audit.jsonl)
# - init-feature 校验:从 --feature-id 抽 prefix → 扫 audit jsonl 近 PREPARE_CHECK_WINDOW_SEC
#   秒内匹配该 prefix 的 record → 命中 PASS / 未命中 BLOCKED
# - 旁路:TEAMWORK_BYPASS_PREPARE_CHECK=1(仅 debug / migration / 极端场景)
# - 测试 override:TEAMWORK_PREPARE_AUDIT_PATH=<path> 覆盖 audit 文件路径
#
# 为什么 60min:Feature prepare → 用户思考拍板 → init-feature 通常 5-30min ·
# 60min 给 buffer · 防"几天前跑过一次就一直绕过"

PREPARE_CHECK_AUDIT_ENV = "TEAMWORK_PREPARE_AUDIT_PATH"
PREPARE_CHECK_BYPASS_ENV = "TEAMWORK_BYPASS_PREPARE_CHECK"
PREPARE_CHECK_WINDOW_SEC = 3600  # 60 min


def _prepare_audit_path() -> Path:
    """audit jsonl 落位 · 用户级跨项目(主工作区 prepare → worktree init-feature 可通)。

    覆盖路径:TEAMWORK_PREPARE_AUDIT_PATH=<path>(测试用)。
    """
    override = os.environ.get(PREPARE_CHECK_AUDIT_ENV)
    if override:
        return Path(override)
    return Path.home() / ".teamwork" / "prepare_check_audit.jsonl"


def _write_prepare_audit(record: dict) -> None:
    """append-only jsonl 写 · 父目录自动创建 · 失败不阻塞 prepare-check 主输出。"""
    try:
        p = _prepare_audit_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        # audit 写失败不致命(jsonl 是兜底审计 · 主功能不依赖它)
        pass


def _parse_iso_utc(s: str):
    """容忍 'Z' 后缀的 ISO 8601 解析 · 失败返 None。"""
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _check_prepare_audit(feature_id: str) -> dict:
    """从 feature_id 抽 prefix · 扫 audit jsonl · 找近 PREPARE_CHECK_WINDOW_SEC 内匹配 record。

    返回 {verdict: PASS|FAIL|SKIP, ...}。SKIP = bypass 环境变量 / 抽不出 prefix。
    """
    if os.environ.get(PREPARE_CHECK_BYPASS_ENV) == "1":
        return {"verdict": "SKIP", "reason": f"{PREPARE_CHECK_BYPASS_ENV}=1"}
    m = re.match(r"^(.+?)-[FBM]\d+", feature_id)
    if not m:
        return {"verdict": "SKIP", "reason": f"feature_id {feature_id!r} 抽不出前缀"}
    prefix = m.group(1)
    audit_path = _prepare_audit_path()
    if not audit_path.exists():
        return {
            "verdict": "FAIL",
            "prefix": prefix,
            "audit_path": str(audit_path),
            "reason": "audit 文件不存在 · 未跑过 prepare-check",
        }
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - PREPARE_CHECK_WINDOW_SEC
    try:
        lines = audit_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return {"verdict": "SKIP", "reason": f"audit 读失败: {e}"}
    # 倒序扫(最新在末尾 · 找到一条匹配即返 PASS)
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("feature_id_prefix") != prefix:
            continue
        ts = _parse_iso_utc(rec.get("timestamp", ""))
        if ts is None:
            continue
        if ts.timestamp() < cutoff:
            # 倒序找到的最新匹配也过期 = 全部过期
            return {
                "verdict": "FAIL",
                "prefix": prefix,
                "audit_path": str(audit_path),
                "latest_match_age_sec": int(now.timestamp() - ts.timestamp()),
                "window_sec": PREPARE_CHECK_WINDOW_SEC,
                "reason": "最近一次匹配 prepare-check 超出 60min 窗口",
            }
        # v8.15:return 整条 audit record(含 admission_judgment / consistency / recommended_flow_type)
        # 供 init-feature 跨字段校验(如 audit consistency=MISMATCH vs init --flow-type)
        return {
            "verdict": "PASS",
            "prefix": prefix,
            "match_timestamp": rec.get("timestamp"),
            "age_sec": int(now.timestamp() - ts.timestamp()),
            "audit_record": rec,
        }
    return {
        "verdict": "FAIL",
        "prefix": prefix,
        "audit_path": str(audit_path),
        "reason": f"audit 中无匹配 prefix={prefix!r} 的 record",
    }


def cmd_init_feature(args: argparse.Namespace) -> None:
    """Create initial state.json · 替代手工 Write。"""
    # Feature Planning / 问题排查 不进状态机 · 拒绝
    if args.flow_type in NON_STATE_MACHINE_FLOWS:
        die(2, json.dumps({
            "verdict": "FAIL",
            "error": f"flow_type='{args.flow_type}' 不进状态机 · init-feature 拒绝",
            "hint": (
                f"{args.flow_type} 流程由 PMO 主对话直接执行 · 不创建 state.json。"
                if args.flow_type == "Feature Planning"
                else "问题排查由 PMO 直接 grep/Read 答 · 不创建 state.json。"
            ),
            "spec": (
                "docs/feature-planning.md"
                if args.flow_type == "Feature Planning"
                else "FLOWS.md § 问题排查"
            ),
        }, ensure_ascii=False, indent=2))

    feature_dir = Path(args.feature)
    state_file = feature_dir / "state.json"

    # v8.14:prepare-check audit 门禁(治本 PTR-F054 case · AI 跳 prepare 直裸跑 init-feature)
    # prepare-check 已物化但被绕过 = 等同没物化 · 这里加下游硬墙
    audit = _check_prepare_audit(args.feature_id)
    if audit["verdict"] == "FAIL":
        die(2, json.dumps({
            "verdict": "FAIL",
            "action": "init-feature",
            "error": (
                f"prepare-check audit 缺失或过期 · 无法证明 prepare 子流程已跑完 "
                f"(prefix={audit.get('prefix')!r})"
            ),
            "audit_detail": audit,
            "hint": (
                "先跑 prepare-check · 再 init-feature:\n"
                f"  python3 {{SKILL_ROOT}}/tools/state.py prepare-check "
                f"--feature-id-prefix {audit.get('prefix')} "
                f"--features-root <绝对路径> --flow-type {args.flow_type}\n"
                "→ prepare-check 写 audit jsonl · init-feature 60min 窗内复跑即放行。\n"
                "若已跑过 prepare-check 仍 FAIL:可能①超 60min 窗 → 重跑一次;"
                "②prefix 拼错 → 对齐 prepare-check 时的 --feature-id-prefix。"
            ),
            "rule": "v8.14 prepare-check audit 门禁 · 治本 PTR-F054 AI 跳 prepare case",
            "bypass": f"调试 / migration · export {PREPARE_CHECK_BYPASS_ENV}=1",
            "spec": "docs/prepare.md § 0",
        }, ensure_ascii=False, indent=2))

    # v8.15:admission consistency 校验(治本 F001 GCP gateway case · AI 选错 flow_type)
    # audit 里若 consistency=MISMATCH(AI judgment 推荐 flow_type ≠ init --flow-type)→ WARN
    # 不 BLOCK(R0 兜底:可能合理例外 · 给 AI/用户数据 + 警告 · 决策权留人)
    admission_warning = None
    rec = audit.get("audit_record") or {}
    audit_consistency = rec.get("consistency")
    audit_recommended = rec.get("recommended_flow_type")
    if audit_consistency == "MISMATCH" and audit_recommended:
        admission_warning = (
            f"[WARN] admission MISMATCH:prepare-check 时 AI judgment 推荐 "
            f"flow_type={audit_recommended!r} · 但 init-feature --flow-type={args.flow_type!r} · "
            f"audit at {rec.get('timestamp')} · 若 admission_judgment.ai_rationale "
            f"信号强(如「方向级业务变更」「跨独立部署服务」)· 建议取消本次 init · "
            f"用 --flow-type={audit_recommended!r} 重走 prepare-check + Feature Planning 或对应流程"
        )

    # v8.x:artifact 路由物化校验(治本 F049 子项目错位 case)
    # teamwork-space.md docs_root 是路由权威 · 校验 --feature 路径 + ID 前缀一致
    routing = _check_artifact_routing(feature_dir, args.feature_id)
    if routing["verdict"] == "FAIL":
        die(2, json.dumps({
            "verdict": "FAIL",
            "action": "init-feature",
            "error": (
                f"artifact 路径违背 teamwork-space.md 路由权威:前缀 {routing['prefix']} "
                f"注册 docs_root={routing['expected_docs_root']!r} · "
                f"但 --feature 落在 {routing['actual_path']!r}"
            ),
            "hint": (
                "二选一修正:\n"
                f"  ① 路径错 → --feature 改到 {routing['expected_docs_root']}/{feature_dir.name}\n"
                "  ② 前缀错 → 该改动属哪个子项目?用该子项目注册的前缀 + docs_root "
                "(代码在 apps/partner/ → PTR · services/ → SVC-* · 查 teamwork-space.md 子项目清单)"
            ),
            "rule": "conventions.md §8 docs_root 路由权威 · v8.x 物化拦截 · 治本 F049 case",
            "bypass": "确属特例:export TEAMWORK_BYPASS_ROUTING_CHECK=1",
        }, ensure_ascii=False, indent=2))

    if state_file.exists() and not args.force:
        die(2, json.dumps({
            "verdict": "FAIL",
            "error": f"state.json already exists: {state_file}",
            "hint": "Use --force to overwrite (自动 backup .bak.<ts>)",
        }, ensure_ascii=False, indent=2))

    if state_file.exists() and args.force:
        ts = now_iso().replace(":", "_")
        backup = state_file.with_suffix(f".json.bak.{ts}")
        state_file.rename(backup)

    feature_dir.mkdir(parents=True, exist_ok=True)
    initial_stage = args.initial_stage or DEFAULT_INITIAL_STAGE.get(
        args.flow_type, "goal"
    )

    # 启发式校验：basename 应含 feature_id（防 --feature 传了 slug 而不是完整路径）
    if args.feature_id not in feature_dir.name:
        # 不强阻 · 但 stderr 提示一行警告
        print(
            f"WARNING: --feature basename '{feature_dir.name}' does not contain "
            f"--feature-id '{args.feature_id}' · 确认 --feature 是完整路径（如 "
            f"apps/{{sub_project}}/docs/features/{args.feature_id}）而非仅 feature 名",
            file=sys.stderr,
        )

    state: dict[str, Any] = {
        "feature_id": args.feature_id,
        "sub_project": args.sub_project or "",
        "flow_type": args.flow_type,
        "artifact_root": str(feature_dir),  # v7.3.10+P0-149: 单源 · 不再独立 --artifact-root
        # v8.36:host per-feature(治本 SVC-PLATFORM-F054 case · 全局 audit 跨 session 污染)
        # 不传 → None · external-review fallback 读全局 audit(deprecated)+ emit WARN
        "host": args.host or None,
        "host_history": ([{"host": args.host, "at": now_iso(), "source": "init-feature"}]
                          if args.host else []),
        "current_stage": initial_stage,
        "merge_target": args.merge_target,
        "worktree": {
            "strategy": args.worktree_mode,
            "branch": args.branch,
            "path": args.worktree_path,
            "base_branch": f"origin/{args.merge_target}",
            "created_at": now_iso(),
        },
        "environment_config": {
            "worktree_mode": args.worktree_mode,
            "branch": args.branch,
            "merge_target": args.merge_target,
            "base": f"origin/{args.merge_target}",
            "executed_at": now_iso(),
        },
        "auto_mode": args.auto_mode,
        # v8.15:admission MISMATCH WARN(audit consistency=MISMATCH 时 init-feature 留痕)
        "concerns": [admission_warning] if admission_warning else [],
        "review_round": 0,
        "stage_contracts": {},
        "completed_stages": [],
        "created_at": now_iso(),
    }
    # v8.0+P0-9:按 flow_type 填默认 stage_review_roles + adjustments audit list
    try:
        from _v8_engine import build_default_stage_review_roles
        state["stage_review_roles"] = build_default_stage_review_roles(args.flow_type)
        state["stage_review_roles_adjustments"] = []
    except ImportError:
        pass
    # ── v8.0+P0-3:cwd 物化校验(治本 PTR-F033 主 tree 污染 case)──
    # 根因:即使 init-feature 自动建了 worktree · 若 PMO 在主 tree cwd 运行 ·
    # state.json 仍落主 tree · worktree 是空的 · 主 tree 污染依旧。
    # 修复:worktree_mode != off 且 --worktree-path 提供时 · 校验:
    #   - 当前 cwd 必须在 --worktree-path 内
    #   - feature_dir(state.json 落位)必须在 cwd 内(防绝对路径反向落主 tree)
    # 不一致 → FAIL + hint 引导 cd
    cwd_warning = None
    bypass_cwd = os.environ.get("TEAMWORK_BYPASS_CWD_WORKTREE") == "1"
    if not bypass_cwd and args.worktree_mode != "off" and args.worktree_path:
        cwd_real = Path.cwd().resolve()
        wt_real = Path(args.worktree_path).resolve()
        feat_real = Path(args.feature).resolve()
        if wt_real.exists():
            # cwd 必须在 worktree 内
            try:
                cwd_real.relative_to(wt_real)
                cwd_in_wt = True
            except ValueError:
                cwd_in_wt = False
            # feature_dir 必须在 worktree 内(防绝对路径反向落主 tree)
            try:
                feat_real.relative_to(wt_real)
                feat_in_wt = True
            except ValueError:
                feat_in_wt = False

            if not cwd_in_wt or not feat_in_wt:
                die(2, json.dumps({
                    "verdict": "FAIL",
                    "action": "init-feature",
                    "error": "cwd 或 --feature 路径未在 worktree 内 · state.json 会落主 tree(治本 PTR-F033)",
                    "current_cwd": str(cwd_real),
                    "worktree_path": str(wt_real),
                    "feature_path": str(feat_real),
                    "cwd_in_worktree": cwd_in_wt,
                    "feature_in_worktree": feat_in_wt,
                    "hint": (
                        f"先 `cd {wt_real}` · 再用相对路径 `--feature docs/features/...` "
                        f"或确认 --feature 是 worktree 内的绝对路径 · 重跑 init-feature"
                    ),
                    "bypass": "调试场景 export TEAMWORK_BYPASS_CWD_WORKTREE=1",
                }, ensure_ascii=False, indent=2))
        else:
            cwd_warning = (
                f"worktree path {wt_real} 尚不存在 · init-feature 将尝试自动创建 · "
                "建议:先显式 `git worktree add` + `cd` 再跑 init-feature"
            )

    # v8.0+P0-5:worktree 物理存在硬校验(替代 P0-2 自动建)
    # 单一职责:init-feature 只创建 state.json · 不动 git
    # 正路径(triage 拍板):PMO 用户确认后显式 git worktree add → cd → init-feature
    # 漏建 → FAIL(物化拦截 · 不静默兜底)
    if (
        not bypass_cwd
        and args.worktree_mode != "off"
        and args.worktree_path
    ):
        wt_real = Path(args.worktree_path).resolve()
        if not wt_real.exists():
            die(2, json.dumps({
                "verdict": "FAIL",
                "action": "init-feature",
                "error": (
                    f"worktree path {wt_real} 不存在 · "
                    f"init-feature 不再自动创建(v8.0+P0-5 单一职责)"
                ),
                "hint": (
                    f"按 triage emit 的 pause_for_user 指引:\n"
                    f"  1. git worktree add -b {args.branch} {wt_real} origin/{args.merge_target}\n"
                    f"  2. cd {wt_real}\n"
                    f"  3. 重跑 state.py init-feature"
                ),
                "rule": "SKILL.md § Triage 入口规范 §3.4 入口完成才进状态机",
                "bypass": "调试场景 export TEAMWORK_BYPASS_CWD_WORKTREE=1",
            }, ensure_ascii=False, indent=2))

    # v8.x+P0-N:worktree path 约定校验(治本 PTR-F041 静默错位)
    # 规则(可枚举 · 进脚本):期望 path = main_project_root / worktree_root_path / feature_id
    #   - main_project_root 从 `git worktree list --porcelain` 第一条解析(linked worktree → main)
    #   - worktree_root_path 从 main_project_root/.teamwork_localconfig.json 读 · 默认 ".worktree"
    # 不匹配 → FAIL(治本 AI 抄 SKILL.md 状态行示例 / 自由发挥路径反模式)
    if (
        not bypass_cwd
        and not os.environ.get("TEAMWORK_BYPASS_WORKTREE_PATH_CHECK")
        and args.worktree_mode != "off"
        and args.worktree_path
    ):
        wt_real = Path(args.worktree_path).resolve()
        main_root: Path | None = None
        try:
            result = subprocess.run(
                ["git", "-C", str(wt_real), "worktree", "list", "--porcelain"],
                capture_output=True, text=True, check=True, timeout=10,
            )
            for line in result.stdout.splitlines():
                if line.startswith("worktree "):
                    main_root = Path(line.split(" ", 1)[1]).resolve()
                    break
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            main_root = None

        if main_root is not None:
            localconfig = main_root / ".teamwork_localconfig.json"
            worktree_root_path = ".worktree"
            config_source = "默认(无 .teamwork_localconfig.json)"
            if localconfig.exists():
                try:
                    cfg = json.loads(localconfig.read_text(encoding="utf-8"))
                    worktree_root_path = cfg.get("worktree_root_path", ".worktree")
                    config_source = str(localconfig)
                except (OSError, json.JSONDecodeError):
                    pass
            expected = (main_root / worktree_root_path / args.feature_id).resolve()
            if wt_real != expected:
                die(2, json.dumps({
                    "verdict": "FAIL",
                    "action": "init-feature",
                    "error": "worktree path 不符合 worktree_root_path 约定",
                    "actual": str(wt_real),
                    "expected": str(expected),
                    "main_project_root": str(main_root),
                    "worktree_root_path_config": worktree_root_path,
                    "config_source": config_source,
                    "hint": (
                        f"修复二选一:\n"
                        f"  A. 移到期望路径(推荐):\n"
                        f"     cd {main_root}\n"
                        f"     git worktree remove {wt_real}\n"
                        f"     git worktree add -b {args.branch} {expected} origin/{args.merge_target}\n"
                        f"     cd {expected} && 重跑 state.py init-feature\n"
                        f"  B. 修改配置匹配现状(若有意自定义 worktree 根):\n"
                        f"     编辑 {localconfig}\n"
                        f"     设 worktree_root_path 字段为 wt 父目录相对 main_root 的路径"
                    ),
                    "rule": "conventions.md §9-12 worktree path 规范",
                    "bypass": "应急 · export TEAMWORK_BYPASS_WORKTREE_PATH_CHECK=1",
                }, ensure_ascii=False, indent=2))

    atomic_write(state_file, state)

    # v8.0+P0-13:项目级系统维护已挪到 session-bootstrap(session 级 · 不是 Feature 级)
    # init-feature 只管 Feature 级状态机操作

    emit({
        "verdict": "OK",
        "action": "init-feature",
        "feature_id": args.feature_id,
        "flow_type": args.flow_type,
        "current_stage": initial_stage,
        "state_path": str(state_file),
        "checksum_prefix": state[CHECKSUM_FIELD][:24],
        "created_at": state["created_at"],
        "routing_check": routing,
        "next_action_brief": _init_feature_next_brief(args, initial_stage),
        # v8.15:admission MISMATCH 时 emit 顶层显警告(AI 一定看到)+ state.concerns 已留痕
        **({"admission_warning": admission_warning} if admission_warning else {}),
    })


def _init_feature_next_brief(args, initial_stage: str) -> str:
    """init-feature emit 后给 PMO 的 brief(v8.0+P0-5 简化)。

    triage 已确认 worktree · PMO 已显式建 + cd · init-feature 仅创建 state.json。
    所以 brief 直接告知"进下一步" · 不需要再讨论 worktree。

    Bug 流程额外提示:dev-start 物化拦截要求 bugfix/BUG-*.md 必须先存在 ·
    所以 brief 明示"先起草 BUG 单 · 再 dev-start" · 治本 AI 撞拦截后才补的反模式。
    """
    wt_note = ""
    if args.worktree_mode == "off":
        wt_note = "(worktree_mode=off · 在当前 tree 直接工作)"
    else:
        wt_note = f"(worktree_mode={args.worktree_mode} · cwd={Path.cwd()} 已通过 cwd 校验)"

    # Bug 流程前置:起草 BUG 单(治本 dev-start 物化拦截鸡生蛋)
    pre_stage_action = ""
    if args.flow_type == "Bug":
        pre_stage_action = f"""
🔴 **Bug 流程前置(在 {initial_stage}-start 之前必做)**:
   起草 `{Path(args.feature)}/bugfix/BUG-<bug-id>.md`(模板 `templates/bug-report.md`)·
   含 frontmatter `bug_id/symptom/root_cause/fix_summary` + body §现象/§根因/§修复方案/§回归测试。
   不起草 → {initial_stage}-start 物化拦截 FAIL。
"""

    return f"""## init-feature 完成 · 下一步

{wt_note}

state.json 已落在:`{Path(args.feature).resolve()}/state.json`
{pre_stage_action}
直接进入首 stage(prepare 子流程已在 init-feature 之前完成 · 见 docs/prepare.md):

1. `state.py {initial_stage}-start --feature {args.feature}`
   - emit 本 stage 详细 brief(必读 / 必产物 / 完成方式)

2. AI 按 brief 完成 stage 工作 → `{initial_stage}-complete`

📎 物化兜底:各 stage-start 校验 worktree 物理存在 + cwd 校验
   不一致 → FAIL + hint(治本 PTR-F033)
📎 项目骨架(KNOWLEDGE / TROUBLESHOOTING / GLOSSARY)由 bootstrap.py 在 session 启动时维护 · 不在 init-feature 后做。
"""


def cmd_reset_prev(args: argparse.Namespace) -> None:
    """v8.0+P0-6:状态机回退一步(治本 raw-write 滥用)。

    安全语义化命令 · 替代 raw-write 修改 current_stage 的场景:
    - 状态机内回退(completed_stages[-1] 回到 current_stage)
    - 清除已转移到的 stage 的 contract(防脏数据)
    - last_completed 的 gate 重置(允许重跑 complete)
    - 自动追 concerns WARN

    硬门禁:
    - Ship 后(ship.phase ∈ {pushed, merged})不可回 · 远程已动 · 状态不可逆
    - completed_stages 为空 → 无可回退
    """
    saved = os.environ.get(CHECKSUM_BYPASS_ENV)
    os.environ[CHECKSUM_BYPASS_ENV] = "1"
    try:
        path = state_path(args.feature)
        state = json.loads(path.read_text(encoding="utf-8"))
    finally:
        if saved is None:
            del os.environ[CHECKSUM_BYPASS_ENV]
        else:
            os.environ[CHECKSUM_BYPASS_ENV] = saved

    before = json.loads(json.dumps(state))

    # 硬门禁 1:Ship 后不可回
    ship_phase = (state.get("ship") or {}).get("phase")
    if ship_phase in ("pushed", "merged"):
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "reset-prev",
            "error": f"Ship 后不可回退 · ship.phase={ship_phase!r} · 远程已动 · 状态不可逆",
            "hint": (
                "若需要修复:reset-prev 不可用 · 走 ship-phase --action close-unmerged "
                "或新开 Feature 修复 · 或用 raw-write(留 concerns WARN)"
            ),
        }, ensure_ascii=False, indent=2))

    # 硬门禁 2:completed_stages 为空
    completed = state.get("completed_stages") or []
    if not completed:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "reset-prev",
            "error": "completed_stages 为空 · 无可回退的 stage",
            "current_stage": state.get("current_stage"),
            "hint": "若需调整 current_stage 初值 · 用 init-feature --force 或 raw-write",
        }, ensure_ascii=False, indent=2))

    last_completed = completed[-1]
    current = state.get("current_stage")

    # 硬门禁 3:current_stage 与 last_completed 相等(异常/无意义)
    # 典型 case:旧版 review NEEDS_REVISION bug 错误地把 review 加 completed_stages ·
    # 已被 v8.x review-complete 回退路径检测修复 · 此处兜底剩余异常
    if last_completed == current:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "reset-prev",
            "error": (
                f"current_stage={current!r} 与 last_completed 相等 · "
                "状态自洽 · reset-prev 无效"
            ),
            "hint": (
                "排查:state.json 是否被外部修改 / review-complete NEEDS_REVISION 应自动转 dev "
                "(v8.x 已修)· 若状态确需手工调整 · 用 raw-write 显式改 current_stage(留 concerns WARN)"
            ),
        }, ensure_ascii=False, indent=2))

    # 1. current_stage 改回 last_completed
    state["current_stage"] = last_completed

    # 2. completed_stages 移除 last_completed
    state["completed_stages"] = completed[:-1]

    # 3. 清除"已转移到的 stage" 的 contract(防脏数据)
    if current and current != last_completed:
        contracts = state.get("stage_contracts") or {}
        contracts.pop(current, None)

    # 4. last_completed 的 gate 重置 · 允许重跑 complete
    contracts = state.setdefault("stage_contracts", {})
    c = contracts.setdefault(last_completed, {})
    c["input_satisfied"] = False
    c["process_satisfied"] = False
    c["output_satisfied"] = False
    c.pop("completed_at", None)
    c.pop("duration_minutes", None)
    # started_at 保留(stage 开始时间不变)

    # 5. legal_next_stages 重算
    flow_graph = FLOW_BY_TYPE.get(state.get("flow_type"), {})
    state["legal_next_stages"] = flow_graph.get(last_completed, [])

    # 6. 自动 concerns WARN(audit 透明)
    state.setdefault("concerns", []).append(
        f"{now_iso()} WARN reset-prev: {current!r} → {last_completed!r} · "
        f"reason: {args.reason}"
    )

    state["updated_at"] = now_iso()
    state["updated_by"] = "reset-prev"
    atomic_write(path, state)

    emit({
        "verdict": "OK",
        "action": "reset-prev",
        "from_stage": current,
        "to_stage": last_completed,
        "reason": args.reason,
        "legal_next_stages": state["legal_next_stages"],
        "completed_stages_after": state["completed_stages"],
        "next_action_brief": (
            f"## reset-prev 完成\n\n"
            f"已回退:{current!r} → {last_completed!r}\n"
            f"contract 重置:{last_completed} 三 gate 全 false · 可重跑 complete。\n\n"
            f"下一步:跑 `state.py {last_completed}-complete --feature {args.feature} ...` 重新推进。\n\n"
            f"⚠️ 已自动追 concerns WARN(audit 透明)。"
        ),
    })


def cmd_prepare_check(args: argparse.Namespace) -> None:
    """v8.13:prepare 子流程 ID 冲突预检 · 推荐 next_available_id。

    按 --flow-type 定 artifact ID 字母(Feature/敏捷需求=F · Bug=B · Micro=M ·
    详 docs/conventions.md §1)· 扫 --features-root 下该字母的已有 artifact 目录 ·
    抓 --feature-id-prefix 匹配的 ID · 返回 existing_ids + next_available_id。

    治本 case:① PMO 启动 Feature 不知 F040 已被 Planning 占用 → 临时改号多确认一轮;
    ② Bug 流程错推 PREFIX-F(应 PREFIX-B)· flow_type 原本没参与 ID 字母。
    """
    import re

    root = Path(args.features_root or "docs/features").resolve()
    if not root.exists():
        emit({
            "verdict": "FAIL",
            "command": "prepare-check",
            "error": f"features_root 不存在: {root}",
            "hint": "用 --features-root <绝对路径> 指定 · 默认 docs/features",
        })
        return

    prefix = args.feature_id_prefix
    if not prefix:
        emit({
            "verdict": "FAIL",
            "command": "prepare-check",
            "error": "--feature-id-prefix 必填(如 PTR / INFRA / SVC-PLATFORM)",
        })
        return

    # flow_type → artifact ID 字母(详 docs/conventions.md §1)
    # Feature / 敏捷需求 共用 F · Bug=B · Micro=M · 缺省 F(--flow-type 漏传时向后兼容)
    _FLOW_ID_LETTER = {"Feature": "F", "敏捷需求": "F", "Bug": "B", "Micro": "M"}
    id_letter = _FLOW_ID_LETTER.get(args.flow_type or "", "F")

    # 扫匹配 <PREFIX>-<字母><NNN>* 目录(字母由 flow_type 定)
    pattern = re.compile(rf"^{re.escape(prefix)}-{id_letter}(\d+)")
    existing: list[tuple[int, str]] = []  # (number, full_id)
    for child in root.iterdir():
        if not child.is_dir():
            continue
        m = pattern.match(child.name)
        if m:
            existing.append((int(m.group(1)), child.name))

    existing.sort()
    existing_ids = [name for _, name in existing]
    used_numbers = {n for n, _ in existing}

    # 推荐下一可用编号 = max + 1(连续递增 · 不填空洞 · 详 docs/conventions.md § 1 "项目内独立递增")
    next_num = (max(used_numbers) + 1) if used_numbers else 1
    next_id_stem = f"{prefix}-{id_letter}{next_num:03d}"

    payload = {
        "verdict": "OK",
        "command": "prepare-check",
        "features_root": str(root),
        "feature_id_prefix": prefix,
        "id_letter": id_letter,
        "existing_ids": existing_ids,
        "existing_count": len(existing_ids),
        "next_available_number": next_num,
        "next_available_id_stem": next_id_stem,
        "hint": (
            f"prepare 暂停点 artifact ID 默认填 {next_id_stem}-<Kebab-Case-名称> · "
            f"用户可改 · 但应避开 existing_ids 中已占编号"
            + ("" if args.flow_type
               else " · ⚠️ 未传 --flow-type · ID 字母默认 F · Bug/Micro 务必补 --flow-type")
        ),
    }

    # v8.x:--flow-type 可选 · 返回 stage_chain_preview(stage × 评审角色)
    # 让 PMO 在 prepare 暂停点直接渲染「📋 各 stage 评审角色」子表 · 不凭手工查 spec
    if args.flow_type:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from _v8_engine import build_stage_chain_preview, FLOW_STAGE_CHAIN
        except ImportError as e:
            payload["stage_chain_preview_error"] = str(e)
        else:
            if args.flow_type not in FLOW_STAGE_CHAIN:
                payload["stage_chain_preview_error"] = (
                    f"flow_type '{args.flow_type}' 不支持 stage chain 预览 · "
                    f"支持: {sorted(FLOW_STAGE_CHAIN)}(Feature Planning / 问题排查 不进状态机 · 无 chain)"
                )
            else:
                payload["flow_type"] = args.flow_type
                payload["stage_chain_preview"] = build_stage_chain_preview(args.flow_type)

    # v8.15:admission 校验(治本 F001 GCP gateway case · AI 不读 prepare.md §2.1/§2.2)
    # 设计:工具不扫关键词 regex(伪枚举 · 死板 · 误判)· 而是强制 AI 必传判断结果(judgment)
    # R0 哲学拆分:
    # - 可枚举:judgment 字段必填(工具 BLOCK if missing) + consistency 校验
    # - 不可枚举:judgment 内容(AI 自由判断 · audit 留痕)
    admission = _validate_admission_judgment(args)
    if admission["verdict"] == "FAIL":
        emit({
            "verdict": "FAIL",
            "command": "prepare-check",
            "error": admission["error"],
            "hint": admission["hint"],
            "spec": "docs/prepare.md § 2.1(复杂度升级判据)+ § 2.2(敏捷需求/Micro 准入)",
        })
        return
    # 注入 payload(consistency / admission_judgment / user_intent / warning if MISMATCH)
    payload.update(admission["payload_extras"])

    # v8.27:reviewer 思考清单(治本 F-Bv2-8 case · PMO 直接抄 stage_chain_preview 默认 reviewers)
    # 4 个核心问题 · 软提示 AI 在 emit prepare 暂停点时基于此给思考后的 reviewer 预估
    # 不强制 JSON 必传(Option A · 用户拍板)· 不像 v8.15 admission_judgment 物化
    payload["reviewer_thinking_checklist"] = REVIEWER_THINKING_CHECKLIST
    payload["reviewer_thinking_hint"] = (
        "🔴 PMO emit prepare 暂停点 「建议评审角色」段 · 必基于此 checklist 4 问思考 + "
        "给出加减预估 · 不要直接抄 stage_chain_preview 默认值。"
        "case 实证(F-Bv2-8 · 2026-05-25):PMO 第一次直接抄默认 · 经用户提示后二次思考才识别 "
        "goal 去 pl(无 ROADMAP 拆分)/ ui_design 跳过(后端先行)/ blueprint 强 external"
        "(跨 5 module 触发点)等调整。"
    )

    # v8.14 + v8.15:写 prepare_check_audit jsonl(init-feature 门禁读这个)
    # 治本 PTR-F054:prepare-check 物化但 AI 不调用 → 下游门禁兜底
    # v8.15:audit 加 admission_judgment / consistency · 治本 F001(选错 flow_type)
    audit_record = {
        "timestamp": now_iso(),
        "feature_id_prefix": prefix,
        "features_root": str(root),
        "flow_type": args.flow_type or "",
        "id_letter": id_letter,
        "next_available_id_stem": next_id_stem,
        "existing_count": len(existing_ids),
        "user_intent": args.user_intent or "",
        "admission_judgment": admission["judgment"],  # parsed JSON or None
        "consistency": admission["consistency"],     # OK / MISMATCH / FAIL(v8.34 删 SKIPPED)
        "recommended_flow_type": admission["recommended_flow_type"],
    }
    _write_prepare_audit(audit_record)
    payload["audit_recorded"] = True

    emit(payload)


# v8.27:reviewer 思考清单(prepare-check 输出 · 治本 F-Bv2-8 PMO 直接抄默认 case)
# 用户决策:Option A(checklist 提示 · 不物化 JSON 必传)· 核心 4 问(不过载)
REVIEWER_THINKING_CHECKLIST = [
    {
        "question": "本 Feature 是否涉及 ROADMAP 拆分 / Feature 优先级决策?",
        "if_no": "goal stage 去 pl(无 ROADMAP 决策 · PL 评审价值低)",
        "if_yes": "goal stage 保留 pl",
    },
    {
        "question": "本 Feature 是否含 UI 改动?",
        "if_no": "ui_design 跳过(--needs-ui=false)· 节省 designer 一轮 + browser_e2e 跳过",
        "if_yes": "ui_design 启用 · reviewers [designer, pm]",
    },
    {
        "question": "本 Feature 跨 ≥3 个 module 触发点 / 调用方?(如跨多 stage / 多 service)",
        "if_yes": "blueprint / review 强调 external(异质模型查漏触发 · F-Bv2-8 实证有效)",
        "if_no": "blueprint / review external 默认即可",
    },
    {
        "question": "本 Feature 是否数据模型重构?(删/改老字段 · 表结构变 · 索引变)",
        "if_yes": "blueprint 强 architect + (若项目配置)加 dba 评审",
        "if_no": "blueprint architect 默认即可",
    },
]


def _validate_admission_judgment(args) -> dict:
    """v8.15:校验 --user-intent + --admission-judgment(治本 F001 case)。
    v8.34:删 SKIPPED 兼容路径 · 全局强制必传(治本 SVC-CORE-M001 case · AI 钻 SKIPPED 空子不思考)。

    返回 {verdict, error?, hint?, payload_extras, judgment, consistency, recommended_flow_type}。
    consistency: OK(judgment 推荐 == --flow-type) / MISMATCH(不一致 · WARN) / FAIL(BLOCK)

    R0 哲学:工具不解析 user_intent 语义 · 仅校验 admission_judgment JSON 4 字段必填。
    AI 必须真读 prepare.md §2.1/§2.2 才能写出合理 judgment(伪造 ai_rationale 会在 retro
    被复盘到 · 心理成本高)。

    v8.34 删 SKIPPED 兼容路径 ROI:
    - 风险:破坏旧脚本 / debug / migration 路径 · 老 case 调 prepare-check 不传两参 → BLOCK
    - 收益:case 实证(SVC-CORE-M001 Micro 2026-05-26)PMO 不传 admission_judgment 跳过思考 ·
      v8.15 物化「你必须想这件事」被 SKIPPED 兜底架空 · 必须删
    """
    has_intent = bool(args.user_intent)
    has_judgment = bool(args.admission_judgment)

    # v8.34:两者都不传 = BLOCK(治本 SVC-CORE-M001 · 删 v8.15 SKIPPED 兼容口子)
    # 旧调试/migration 路径仍可走 TEAMWORK_BYPASS_PREPARE_CHECK=1(SKILL.md § 暂停点协议)
    if not has_intent and not has_judgment:
        return {
            "verdict": "FAIL",
            "error": (
                "--user-intent + --admission-judgment 必传(v8.34 全局强制 · "
                "删 v8.15 SKIPPED 兼容口子 · 治本 SVC-CORE-M001 AI 跳过思考 case)"
            ),
            "hint": (
                "用法:state.py prepare-check ... "
                "--user-intent '<用户原话>' "
                "--admission-judgment '{"
                "\"sections_reviewed\":[\"§2.1\",\"§2.2\"],"
                "\"matched_signals\":[{\"section\":\"§2.1\",\"signal\":\"...\",\"evidence\":\"...\"}],"
                "\"recommended_flow_type\":\"Feature/Feature Planning/敏捷需求/Bug/Micro\","
                "\"ai_rationale\":\"为什么这么判\"}'  "
                "· AI 必读 prepare.md §2.1/§2.2 才能写出 matched_signals + ai_rationale "
                "· 调试 bypass:TEAMWORK_BYPASS_PREPARE_CHECK=1"
            ),
            "payload_extras": {},
            "judgment": None,
            "consistency": "FAIL",
            "recommended_flow_type": None,
        }

    # 部分传 = 不一致 · BLOCK
    if has_intent != has_judgment:
        missing = "--admission-judgment" if has_intent else "--user-intent"
        return {
            "verdict": "FAIL",
            "error": f"--user-intent + --admission-judgment 必同传 · 缺 {missing}",
            "hint": (
                "两者一起才有意义:user-intent 是用户原话(留痕)· admission-judgment "
                "是 AI 读 prepare.md §2.1/§2.2 后的判断(matched_signals + recommended_flow_type)"
            ),
            "payload_extras": {},
            "judgment": None,
            "consistency": "FAIL",
            "recommended_flow_type": None,
        }

    # 都传了 · 校验 admission_judgment JSON schema
    try:
        judgment = json.loads(args.admission_judgment)
    except json.JSONDecodeError as e:
        return {
            "verdict": "FAIL",
            "error": f"--admission-judgment 不是合法 JSON: {e}",
            "hint": (
                "示例:--admission-judgment '{\"sections_reviewed\":[\"§2.1\",\"§2.2\"],"
                "\"matched_signals\":[{\"section\":\"§2.1\",\"signal\":\"方向级业务变更\","
                "\"evidence\":\"想做一个服务\"}],\"recommended_flow_type\":\"Feature Planning\","
                "\"ai_rationale\":\"...\"}'"
            ),
            "payload_extras": {},
            "judgment": None,
            "consistency": "FAIL",
            "recommended_flow_type": None,
        }

    # 校验 4 必填字段
    required_fields = [
        "sections_reviewed",       # list · ["§2.1", "§2.2"]
        "matched_signals",         # list · [{section, signal, evidence}]
        "recommended_flow_type",   # str · Feature / Feature Planning / 敏捷需求 / Bug / Micro
        "ai_rationale",            # str · 自由文本 · AI 解释为什么这么判
    ]
    missing_fields = [f for f in required_fields if f not in judgment]
    if missing_fields:
        return {
            "verdict": "FAIL",
            "error": f"--admission-judgment 缺必填字段: {missing_fields}",
            "hint": (
                f"4 字段全需要(R0 物化:'你必须想这件事')· "
                f"sections_reviewed[](读了 prepare.md 哪些段)· "
                f"matched_signals[](命中信号 · 含 evidence)· "
                f"recommended_flow_type(你推荐什么 flow_type · 含 'Feature Planning')· "
                f"ai_rationale(为什么这么判 · 给用户/retro 复盘看)"
            ),
            "payload_extras": {},
            "judgment": judgment,
            "consistency": "FAIL",
            "recommended_flow_type": None,
        }

    # 校验 recommended_flow_type 是合法值
    legal_recommended = {
        "Feature", "Feature Planning", "敏捷需求", "Bug", "Micro", "问题排查",
    }
    rec = judgment.get("recommended_flow_type")
    if rec not in legal_recommended:
        return {
            "verdict": "FAIL",
            "error": f"admission_judgment.recommended_flow_type={rec!r} 非法",
            "hint": f"合法值: {sorted(legal_recommended)}",
            "payload_extras": {},
            "judgment": judgment,
            "consistency": "FAIL",
            "recommended_flow_type": rec,
        }

    # 校验 matched_signals 是 list of dict(基本 schema)· 内容由 AI 自由判
    sigs = judgment.get("matched_signals", [])
    if not isinstance(sigs, list):
        return {
            "verdict": "FAIL",
            "error": "admission_judgment.matched_signals 必须是 list",
            "hint": "格式:[{section: '§2.1', signal: '...', evidence: '...'}, ...]",
            "payload_extras": {},
            "judgment": judgment,
            "consistency": "FAIL",
            "recommended_flow_type": rec,
        }

    # consistency 校验:recommended_flow_type vs --flow-type
    extras: dict = {
        "user_intent": args.user_intent,
        "admission_judgment": judgment,
        "recommended_flow_type": rec,
    }
    if not args.flow_type:
        # --flow-type 未传 · 无法 consistency 校验 · 当 OK(向后兼容)· 留 audit
        extras["admission_consistency"] = "OK"
        extras["admission_consistency_note"] = (
            "未传 --flow-type · 无法 consistency 校验 · 推荐: " + rec
        )
        return {
            "verdict": "OK",
            "payload_extras": extras,
            "judgment": judgment,
            "consistency": "OK",
            "recommended_flow_type": rec,
        }

    if rec == args.flow_type:
        extras["admission_consistency"] = "OK"
        return {
            "verdict": "OK",
            "payload_extras": extras,
            "judgment": judgment,
            "consistency": "OK",
            "recommended_flow_type": rec,
        }

    # MISMATCH:WARN(不 BLOCK · R0 兜底)
    extras["admission_consistency"] = "MISMATCH"
    extras["admission_consistency_warning"] = (
        f"⚠️ admission_judgment.recommended_flow_type={rec!r} 与 --flow-type={args.flow_type!r} 不一致 · "
        f"AI 读 §2.1/§2.2 后判 {rec} · 但你选 {args.flow_type} · "
        f"在 prepare 暂停点必加 §2.1/§2.2 三选项让用户拍板(不要默认选 {args.flow_type} 跳过判据) · "
        f"audit 已留痕 · retro 可复盘"
    )
    return {
        "verdict": "OK",  # 不 BLOCK · 仅 WARN(R0:可能有合理例外)
        "payload_extras": extras,
        "judgment": judgment,
        "consistency": "MISMATCH",
        "recommended_flow_type": rec,
    }


def cmd_change_review_roles(args: argparse.Namespace) -> None:
    """v8.x:调整 stage_review_roles · 治本 raw-write 滥用(可枚举进脚本 · R0 哲学)。

    校验:
    - state.json 存在
    - stage 必在 LEGAL_STAGES
    - stage 必在 state.stage_review_roles(只能改已配置 stage · dev/ship 等无 review 配置 reject)
    - roles 必属 REVIEW_ROLE_ENUM(非空 · 至少 1 个)
    - reason 必填(audit)

    写入:
    - state.stage_review_roles[stage] = roles
    - state.stage_review_roles_adjustments append 一条 audit
    - 复用 stage-complete --next-stage-roles 的 audit 结构 · adjusted_via 字段区分来源

    NOOP:新值 == 现值 → 不写不 audit · 输出 verdict=NOOP。
    """
    state = load_state(args.feature)
    state_file = state_path(args.feature)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _v8_engine import REVIEW_ROLE_ENUM

    if args.stage not in LEGAL_STAGES:
        die(2, json.dumps({
            "verdict": "FAIL",
            "command": "change-review-roles",
            "error": f"--stage '{args.stage}' 不在 LEGAL_STAGES",
            "legal_stages": sorted(LEGAL_STAGES),
        }, ensure_ascii=False, indent=2))

    review_roles = state.setdefault("stage_review_roles", {})
    if args.stage not in review_roles:
        die(2, json.dumps({
            "verdict": "FAIL",
            "command": "change-review-roles",
            "error": (
                f"stage '{args.stage}' 不在 state.stage_review_roles · "
                f"该 stage 默认无 review 配置(无意义)"
            ),
            "hint": f"已配置 stages: {sorted(review_roles.keys())}",
        }, ensure_ascii=False, indent=2))

    roles_list = [r.strip() for r in args.roles.split(",") if r.strip()]
    if not roles_list:
        die(2, json.dumps({
            "verdict": "FAIL",
            "command": "change-review-roles",
            "error": "--roles 不能为空 · 至少 1 个角色",
        }, ensure_ascii=False, indent=2))

    invalid = [r for r in roles_list if r not in REVIEW_ROLE_ENUM]
    if invalid:
        die(2, json.dumps({
            "verdict": "FAIL",
            "command": "change-review-roles",
            "error": f"--roles 含非法角色: {invalid}",
            "hint": f"REVIEW_ROLE_ENUM = {sorted(REVIEW_ROLE_ENUM)}",
        }, ensure_ascii=False, indent=2))

    before = review_roles[args.stage][:]
    if before == roles_list:
        emit({
            "verdict": "NOOP",
            "command": "change-review-roles",
            "stage": args.stage,
            "current_roles": roles_list,
            "hint": "新值 == 现值 · 不写不 audit",
        })
        return

    review_roles[args.stage] = roles_list
    audit_entry = {
        "stage": args.stage,
        "before": before,
        "after": roles_list,
        "reason": args.reason,
        "adjusted_at": now_iso(),
        "adjusted_via": "change-review-roles",
    }
    state.setdefault("stage_review_roles_adjustments", []).append(audit_entry)

    atomic_write(state_file, state)

    emit({
        "verdict": "OK",
        "command": "change-review-roles",
        "stage": args.stage,
        "before": before,
        "after": roles_list,
        "reason": args.reason,
        "next_action_hint": (
            f"已更新 state.stage_review_roles.{args.stage} · "
            f"后续 {args.stage}-complete 校验 reviewers 必含 {sorted(roles_list)}"
        ),
    })


# ─── v8.20 · external-review(异质模型评审自动调起 · 治本 F034 PMO 自己拼命令 case)─
# ─── v8.21:host 自动探测(PMO 心智 -1 参数 · 只需 --feature + --stage) ─────

# 宿主 → 异质模型自动映射(R3 + standards/external-model-usage.md §7.1)
# claude-code 主对话 → 跑 codex(异质)
# codex-cli 主对话 → 跑 claude(异质)
# gemini-cli 主对话 → 默认 codex(异质 · 也可 --model claude)
EXTERNAL_HOST_TO_MODEL = {
    "claude-code": "codex",
    "codex-cli": "claude",
    "gemini-cli": "codex",  # 默认 · 可 --model 覆盖
}


# v8.21:host audit 路径(与 bootstrap.py write_host_audit 对齐 · 跨进程同源读)
# v8.36:deprecated · 主路径改 per-feature state.json · audit 仅 fallback 兼容
HOST_AUDIT_PATH_ENV = "TEAMWORK_HOST_AUDIT_PATH"


def _detect_host(feature: Optional[str] = None) -> tuple[Optional[str], str]:
    """探测主对话宿主。

    v8.36 优先级(case SVC-PLATFORM-F054 治本 · per-feature 隔离):
      ① state.json.host(per-feature · 主路径 · 必带 --feature)
      ② ~/.teamwork/host_audit.json(deprecated · 跨 session 共享 · v8.21 兼容路径)
      ③ env fallback(占位)

    返回 (host, source):
      - host:claude-code / codex-cli / gemini-cli / None
      - source:"state_json" / "audit_deprecated" / "env" / "none"

    v8.21 → v8.36 演进理由:
    - case SVC-PLATFORM-F054(2026-05-27):全局 audit 跨 session 残留 · PMO 切到 Codex CLI
      但 audit 残留 claude-code · 推出 model=codex 同源 → 异质失效 · 用户手动覆盖才补救
    - 治本:host 是 per-feature 属性 · 不是全局属性(同一项目不同 feature 可能用不同 host)
    """
    # ① state.json.host(v8.36 主路径)
    if feature:
        try:
            feature_dir = Path(feature)
            sp = feature_dir / "state.json"
            if sp.exists():
                data = json.loads(sp.read_text(encoding="utf-8"))
                host = data.get("host")
                if host in EXTERNAL_HOST_TO_MODEL:
                    return host, "state_json"
        except (OSError, json.JSONDecodeError):
            pass
    # ② audit 文件(v8.21 fallback · v8.36 deprecated)
    override = os.environ.get(HOST_AUDIT_PATH_ENV)
    audit_path = (Path(override) if override
                  else Path.home() / ".teamwork" / "host_audit.json")
    if audit_path.exists():
        try:
            data = json.loads(audit_path.read_text(encoding="utf-8"))
            host = data.get("host")
            if host in EXTERNAL_HOST_TO_MODEL:
                return host, "audit_deprecated"
        except (OSError, json.JSONDecodeError):
            pass
    # ③ env fallback(可扩 · 当前仅占位)
    return None, "none"

# stage → reviewer profile 映射(codex profile / claude prompt template 文件名)
# codex-agents/*.toml · claude-agents/*.md
EXTERNAL_STAGE_TO_PROFILE = {
    "goal": {"codex": "prd-reviewer.toml", "claude": "reviewer.md"},
    "blueprint": {"codex": "blueprint-reviewer.toml", "claude": "reviewer.md"},
    "review": {"codex": "reviewer.toml", "claude": "reviewer.md"},
}

EXTERNAL_REVIEW_TIMEOUT_SEC = 300  # codex review 通常 30s-3min · 给 5min buffer


def _detect_cli_version(cli_name: str) -> str:
    """探测 CLI 版本字符串(用于 frontmatter review_model 字段)。"""
    try:
        r = subprocess.run([cli_name, "--version"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return r.stdout.strip().splitlines()[0] if r.stdout.strip() else cli_name
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return cli_name  # fallback


def _build_codex_prompt(stage: str, feature_dir_rel: str, commit: str,
                         base: str, profile_filename: str) -> str:
    """v8.25:按 stage 内置 codex exec PROMPT(治本 v8.23 codex review --base+[PROMPT] 互斥)。

    各 stage review 对象不同 · 全用 codex exec 通用 agent 模式(不用 codex review 子命令):
    - goal:review PRD.md(文档)
    - blueprint:review TC.md + TECH.md(文档)
    - review:review code diff at commit X vs base Y(diff · 由 PROMPT 描述)

    PROMPT 自带完整 review 指令(stage / 文件 / commit / base / 输出格式)·
    cite profile filename 让 codex 加载 reviewer prompt 模板。
    """
    if stage == "goal":
        return (
            f"You are an external PRD reviewer (codex / GPT) providing heterogeneous "
            f"perspective. Read PRD.md in `{feature_dir_rel}/` and conduct PRD review "
            f"per checklist (see templates/external-cross-review.md §3.1 PRD variant). "
            f"Profile reference: codex-agents/{profile_filename}. "
            f"Output: YAML frontmatter (perspective/target/files_read/findings) + body."
        )
    elif stage == "blueprint":
        return (
            f"You are an external blueprint reviewer (codex / GPT) providing "
            f"heterogeneous perspective. Read TC.md and TECH.md in `{feature_dir_rel}/` "
            f"and conduct blueprint review per checklist "
            f"(templates/external-cross-review.md §3.2 TC+TECH variant). "
            f"Profile reference: codex-agents/{profile_filename}. "
            f"Output: YAML frontmatter + findings body."
        )
    elif stage == "review":
        return (
            f"You are an external code reviewer (codex / GPT) providing heterogeneous "
            f"perspective. Review code changes at commit `{commit}` (diff against base "
            f"branch `{base}`) in `{feature_dir_rel}/`. "
            f"Use `git diff {base}..{commit} -- {feature_dir_rel}` to inspect changes. "
            f"Focus: correctness, security, performance, edge cases. "
            f"Profile reference: codex-agents/{profile_filename}. "
            f"Output: YAML frontmatter + findings body with file:line cite."
        )
    # 兜底(其他 stage 走 prompt 模式)
    return (
        f"External review for stage={stage} in `{feature_dir_rel}/`. "
        f"Profile reference: codex-agents/{profile_filename}."
    )


def _run_codex_review(stage: str, commit: str, base: str, title: str,
                      profile_filename: str, feature_dir: Path, cwd: str,
                      codex_model: Optional[str] = None) -> tuple[int, str, str]:
    """跑 codex CLI 评审 · 返 (returncode, stdout, stderr)。

    v8.26 设计:按 stage 选 codex 子命令(各司其职 · 用户洞察):
    - **review stage(代码 diff)** → `codex review --commit X --title Z --config "model=..."`
      · 用 codex review 子命令(专业 diff review · 内置 review prompt 优化)
      · 只传 --commit(避开 --commit/--base/--uncommitted 三选一互斥)
      · 不带 [PROMPT](避开 [PROMPT] 与 review 对象 flag 的新版互斥)
    - **goal / blueprint stage(文档 review)** → `codex exec --config "model=..." [PROMPT]`
      · 用 codex exec 通用 agent(prompt 自描述 Read PRD/TC/TECH)
      · review 子命令是 diff-only · 无法 review markdown 文件

    演进:
    - v8.20 codex review --commit + --base + --title(--commit/--base 互斥)→ FAIL
    - v8.23 codex review --base + --title + [PROMPT](--base/[PROMPT] 互斥)→ FAIL
    - v8.25 全 codex exec [PROMPT](统一但 review stage 损失专业 prompt)→ work but suboptimal
    - v8.26 按 stage 分(review→codex review · goal/blueprint→codex exec)→ 各司其职
    """
    # 算 feature_dir 相对 cwd · 让 prompt 用相对路径(codex 在 cwd=git root 跑)
    try:
        feature_dir_rel = str(feature_dir.relative_to(Path(cwd)))
    except ValueError:
        feature_dir_rel = str(feature_dir)

    # v8.29:codex_model 非空才传 --config model=...(治本 ChatGPT 订阅 case · 默认模型限制)
    model_args = ["--config", f"model={codex_model}"] if codex_model else []

    if stage == "review":
        # ── 代码 diff review · codex review 子命令(专业默认 prompt · 不带 [PROMPT]) ──
        # 只传 --commit(精确)· 不传 --base 避免 --commit/--base 互斥
        # 不传 [PROMPT] 避免 [PROMPT] 与 review 对象 flag 新版互斥
        cmd = ["codex", "review",
               "--commit", commit,
               "--title", title,
               *model_args]
    else:
        # ── 文档 review(goal / blueprint)· codex exec [PROMPT] ──
        body_prompt = _build_codex_prompt(
            stage, feature_dir_rel, commit, base, profile_filename)
        # title 信息嵌进 PROMPT 顶部(codex exec 没 --title flag)
        prompt = f"[Review title: {title}]\n\n{body_prompt}"
        cmd = ["codex", "exec", *model_args, prompt]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=EXTERNAL_REVIEW_TIMEOUT_SEC, cwd=cwd)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"codex 超时({EXTERNAL_REVIEW_TIMEOUT_SEC}s)"
    except (FileNotFoundError, OSError) as e:
        return 127, "", f"codex CLI 不可用:{e}"


def _run_claude_review(prompt_text: str, model_name: str = "claude-sonnet-4-6"
                       ) -> tuple[int, str, str]:
    """跑 claude --print --output-format text · 返 (rc, stdout, stderr)。

    实现细节:cat <prompt> | claude --print --model <model> --output-format text。
    PMO 不需读 · 走 state.py external-review 主路径(v8.20+)。
    """
    cmd = ["claude", "--print", "--model", model_name, "--output-format", "text"]
    try:
        r = subprocess.run(cmd, input=prompt_text, capture_output=True,
                           text=True, timeout=EXTERNAL_REVIEW_TIMEOUT_SEC)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"claude --print 超时({EXTERNAL_REVIEW_TIMEOUT_SEC}s)"
    except (FileNotFoundError, OSError) as e:
        return 127, "", f"claude CLI 不可用:{e}"


def cmd_external_review(args: argparse.Namespace) -> None:
    """v8.20:state.py external-review · 异质模型评审一条命令调起。

    治本 SVC-CORE-F034 case:case-AI 5 层根因第 1/2/3 层(没 which / 没 cite F033 范式 /
    选 Agent subagent substitute)本质是「调用本身没物化」· PMO 要自己判断该不该跑 /
    怎么跑 / 用什么 profile。物化后这 3 层全消除。

    流程:
      Step 1 · 宿主→异质 model 自动映射(--host claude-code → model=codex)
      Step 2 · which <cli> 验工具在(不在 BLOCK + hint · 绝不 substitute)
      Step 3 · stage→profile 自动选(prd-reviewer / blueprint-reviewer / reviewer)
      Step 4 · 算 commit / base(state.json fallback)
      Step 5 · 跑 CLI(同步 · 5min timeout · capture stdout)
      Step 6 · 落 external-cross-review/<stage>-<model>.md(自动 frontmatter + body)
      Step 7 · emit JSON 含 file_path + model_version + 命令实际跑的内容

    R3 异质硬约束(v8.19 文件名校验是兜底 · v8.20 是主路径):
    - model 必 ≠ host 同源(claude-code 不能选 claude · codex-cli 不能选 codex)
    - 文件命名 + frontmatter review_model 自动用合规字面(白名单)
    """
    # ── Step 1 · host + model 校验 + 自动映射 ──
    # v8.36:host 主路径 = state.json.host(per-feature · 治本 SVC-PLATFORM-F054 case)
    #         · audit fallback 仅兼容(deprecated · WARN)· 治本全局 audit 跨 session 污染
    host_source = "explicit"
    host = args.host
    deprecation_warning = None
    if not host:
        host, source = _detect_host(args.feature)
        host_source = source  # state_json / audit_deprecated / env / none
        if source == "audit_deprecated":
            deprecation_warning = (
                "[DEPRECATED] host 来自全局 ~/.teamwork/host_audit.json · v8.36 主路径改 "
                "per-feature state.json.host · 建议:① init-feature 加 --host 显式写入 / "
                "② 跨 session 切宿主时 stage-start 加 --host 校准 · 删全局依赖。"
                "audit fallback v8.37 将删除。"
            )
        if not host:
            emit({
                "verdict": "FAIL",
                "command": "external-review",
                "error": (
                    "--host 未传 + state.json 无 host + 全局 audit 也无 · 无法确定主对话宿主"
                ),
                "hint": (
                    "三选一(推荐 ①):\n"
                    "  ① [v8.36 主路径] 显式传 --host <claude-code|codex-cli|gemini-cli> · "
                    "顺带写到 state.json:\n"
                    "     state.py <stage>-start --feature ... --host <host>\n"
                    "  ② 在 external-review 命令显式传 --host\n"
                    "  ③ [兼容路径 deprecated] 跑 bootstrap 一次"
                    "(python3 {SKILL_ROOT}/tools/bootstrap.py --host <host>)· "
                    "写全局 audit · 但跨 session 易污染 · v8.37 将删\n\n"
                    "v8.36 设计:host 是 per-feature 属性(同一项目不同 feature 可不同宿主)· "
                    "不再是全局共享 · 治本 SVC-PLATFORM-F054 case 全局 audit 跨 session 污染"
                ),
                "spec": "standards/external-model-usage.md § 7.5 v8.36 per-feature host",
            })
            return
    if host not in EXTERNAL_HOST_TO_MODEL:
        emit({
            "verdict": "FAIL",
            "command": "external-review",
            "error": f"host={host!r} 非法 · 合法值: {sorted(EXTERNAL_HOST_TO_MODEL)}",
            "hint": f"host 即主对话宿主标识 · 与 bootstrap --host 一致 · 来源: {host_source}",
        })
        return

    if args.model:
        model = args.model
        # 异质校验:model 不能与 host 同源
        host_keyword = host.split("-")[0]  # claude-code → claude · codex-cli → codex
        if host_keyword in model.lower():
            emit({
                "verdict": "FAIL",
                "command": "external-review",
                "error": f"--model={model!r} 与 --host={host!r} 同源 · 违 R3 异质约束",
                "hint": (
                    f"host={host} 主对话宿主 = {host_keyword} · external 必跑异质 · "
                    f"推荐 --model {EXTERNAL_HOST_TO_MODEL[host]}(自动映射 · 留空即默认)"
                ),
                "spec": "standards/external-model-usage.md § 7.1 异质性定义",
            })
            return
    else:
        model = EXTERNAL_HOST_TO_MODEL[host]

    if model not in ("codex", "claude"):
        emit({
            "verdict": "FAIL",
            "command": "external-review",
            "error": f"--model={model!r} 暂不支持(v8.20 仅 codex/claude)",
            "hint": "其他白名单 CLI(gemini/deepseek 等)未来 case 实证再扩",
        })
        return

    # ── Step 2 · which <cli> 验工具在(治本 case-AI 第 3 层根因) ──
    cli_name = model  # "codex" 或 "claude"
    which_r = subprocess.run(["which", cli_name], capture_output=True, text=True)
    if which_r.returncode != 0:
        emit({
            "verdict": "FAIL",
            "command": "external-review",
            "error": f"{cli_name} CLI 不在(`which {cli_name}` 失败)",
            "hint": (
                f"二选一(绝不 substitute · 不可用 Agent subagent 自审):\n"
                f"  ① 安装 {cli_name} CLI(codex: https://github.com/openai/codex · "
                f"claude: https://claude.com/claude-code)\n"
                f"  ② state.py change-review-roles --feature {args.feature} "
                f"--stage {args.stage} --roles '<不含 external>' --reason "
                f"'{cli_name} CLI 不在本机' · 留 audit 后继续 stage-complete"
            ),
            "rule": "standards/external-model-usage.md § 7.3 · R3 异质硬约束",
        })
        return

    # ── Step 3 · stage→profile 自动选 ──
    if args.stage not in EXTERNAL_STAGE_TO_PROFILE:
        emit({
            "verdict": "FAIL",
            "command": "external-review",
            "error": f"--stage={args.stage!r} 不支持 external review",
            "hint": f"仅 {sorted(EXTERNAL_STAGE_TO_PROFILE)} 支持 · "
                    "其他 stage 走 change-review-roles 移除 external",
        })
        return

    skill_root = Path(__file__).resolve().parent.parent
    profile_filename = EXTERNAL_STAGE_TO_PROFILE[args.stage][model]
    if model == "codex":
        profile_path = skill_root / "codex-agents" / profile_filename
    else:
        profile_path = skill_root / "claude-agents" / profile_filename
    if not profile_path.exists():
        emit({
            "verdict": "FAIL",
            "command": "external-review",
            "error": f"reviewer profile 不存在: {profile_path}",
            "hint": f"检查 skill_root={skill_root} · 是否缺 {model}-agents/{profile_filename}",
        })
        return

    # ── Step 4 · 算 commit / base(state.json fallback) ──
    feature_dir = Path(args.feature).resolve()
    try:
        state = load_state(args.feature)  # state.py.load_state 返 dict(非 tuple)
    except SystemExit:
        # load_state 自己 die 了 · 不重 emit
        raise

    commit = args.commit
    if not commit:
        # fallback:state.stage_contracts.<stage>.auto_commit / git HEAD
        commit = (state.get("stage_contracts", {}).get(args.stage, {}).get("auto_commit")
                  or state.get("stage_contracts", {}).get("dev", {}).get("auto_commit"))
        if not commit:
            try:
                r = subprocess.run(["git", "rev-parse", "HEAD"],
                                   capture_output=True, text=True, cwd=str(feature_dir))
                if r.returncode == 0:
                    commit = r.stdout.strip()
            except (FileNotFoundError, OSError):
                pass
    if not commit:
        emit({
            "verdict": "FAIL",
            "command": "external-review",
            "error": "无法算 commit(--commit 未传 + state.stage_contracts 无 auto_commit + git HEAD 失败)",
            "hint": "显式传 --commit <SHA>",
        })
        return

    base = args.base or state.get("merge_target")
    if not base:
        emit({
            "verdict": "FAIL",
            "command": "external-review",
            "error": "无法算 base(--base 未传 + state.merge_target 缺)",
            "hint": "显式传 --base <branch>",
        })
        return

    feature_id = state.get("feature_id") or feature_dir.name
    title = args.title or f"{feature_id} · {args.stage} stage external review"

    # v8.23:cwd = git root(让 codex 在仓库根跑 · 能读 prompt 内的相对路径)
    git_root = _git_toplevel(feature_dir) or feature_dir
    # v8.29:codex_model 优先级:--codex-model > config.external_review.codex_model > None(不传)
    # 治本 ChatGPT 订阅 case:--config model=... 在 ChatGPT 订阅下 400 · 默认必须空让 codex 用账号允许的默认模型
    codex_model = getattr(args, "codex_model", None)
    if not codex_model:
        # 从项目根 .teamwork_localconfig.json 读 fallback
        try:
            cfg_path = git_root / ".teamwork_localconfig.json"
            if cfg_path.exists():
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                codex_model = (cfg.get("external_review") or {}).get("codex_model")
        except (OSError, json.JSONDecodeError):
            pass
    # codex_model 此时可能 None(ChatGPT 订阅默认行为)/ config 配字面 / 显式覆盖值

    # ── dry-run · 仅输出将跑的命令 + 校验信息 ──
    output_dir = feature_dir / "external-cross-review"
    output_file = output_dir / f"{args.stage}-{model}.md"
    preview_prompt_full = None
    if args.dry_run:
        if model == "codex":
            # v8.26 按 stage 分:review→codex review · goal/blueprint→codex exec(各司其职)
            # v8.29:codex_model 非空才显 --config(治本 ChatGPT 订阅死锁)
            try:
                fd_rel = str(feature_dir.relative_to(git_root))
            except ValueError:
                fd_rel = str(feature_dir)
            model_part = f"--config 'model={codex_model}' " if codex_model else ""
            if args.stage == "review":
                # 代码 diff review · 不带 [PROMPT](codex review 内置专业 prompt)
                preview_cmd = (
                    f"codex review --commit {commit} --title '{title}' "
                    f"{model_part}"
                ).strip()
                preview_prompt_full = None  # review 模式无 PROMPT
            else:
                # 文档 review · codex exec [PROMPT]
                preview_prompt_full = (
                    f"[Review title: {title}]\n\n"
                    + _build_codex_prompt(args.stage, fd_rel, commit, base, profile_path.name)
                )
                preview_cmd = (
                    f"codex exec {model_part}"
                    f"'{preview_prompt_full[:80]}...'"
                )
        else:
            preview_cmd = (
                f"cat {profile_path} | claude --print "
                f"--model claude-sonnet-4-6 --output-format text"
            )
        emit({
            "verdict": "OK",
            "command": "external-review",
            "dry_run": True,
            "host": host,
            "host_source": host_source,  # v8.21
            "model": model,
            "stage": args.stage,
            "profile": str(profile_path),
            "commit": commit,
            "base": base,
            "title": title,
            "codex_model": codex_model if model == "codex" else None,
            "cwd": str(git_root),
            "output_file": str(output_file),
            "preview_command": preview_cmd,
            # v8.23:完整 prompt 透明 emit(preview_command 截断到 80 · 此字段无截断)
            "codex_prompt": preview_prompt_full,
            "next": "去掉 --dry-run 实际跑 · 30s-3min 等",
            # v8.36:host audit deprecation warning(dry-run 也需暴露)
            **({"deprecation_warning": deprecation_warning} if deprecation_warning else {}),
        })
        return

    # ── Step 5 · 跑 CLI ──
    output_dir.mkdir(parents=True, exist_ok=True)
    if model == "codex":
        rc, stdout, stderr = _run_codex_review(
            stage=args.stage, commit=commit, base=base, title=title,
            profile_filename=profile_path.name,
            feature_dir=feature_dir, cwd=str(git_root),
            codex_model=codex_model,
        )
    else:
        # claude 路径:读 prompt template + pipe 给 claude --print
        # 占位符替换(基础版):{{stage}} / {{commit}} / {{base}} / {{feature_id}}
        prompt_template = profile_path.read_text(encoding="utf-8")
        prompt_text = (
            prompt_template
            .replace("{{stage}}", args.stage)
            .replace("{{commit}}", commit)
            .replace("{{base}}", base)
            .replace("{{feature_id}}", feature_id)
        )
        rc, stdout, stderr = _run_claude_review(prompt_text)

    if rc != 0:
        emit({
            "verdict": "FAIL",
            "command": "external-review",
            "error": f"{cli_name} 执行失败(exit={rc}): {stderr[:300]}",
            "hint": (
                f"排查 ① 网络 / token(setup-token / OAuth)· "
                f"② {cli_name} --version 验本地工具 · ③ 重跑 state.py external-review"
            ),
            "host": host,
            "model": model,
            "cli_exit_code": rc,
            "cli_stderr": stderr[:500],
        })
        return

    if not stdout.strip():
        emit({
            "verdict": "FAIL",
            "command": "external-review",
            "error": f"{cli_name} 返回空 stdout · 视作 review 失败",
            "hint": f"检查 {cli_name} 配置 · 或重跑(网络抖动可能)",
        })
        return

    # ── Step 6 · 落产物(合规 frontmatter + body=stdout) ──
    model_version = _detect_cli_version(cli_name)
    frontmatter_lines = [
        "---",
        f"review_model: {model_version}",
        f"review_role: external",
        f"review_stage: {args.stage}",
        f"target_commit: {commit}",
        f"target_base: {base}",
        f"title: \"{title}\"",
        f"generated_at: \"{now_iso()}\"",
        f"invoked_by: state.py external-review (v8.20)",
        f"host: {host}",
        "---",
        "",
    ]
    output_file.write_text("\n".join(frontmatter_lines) + stdout, encoding="utf-8")

    # ── Step 6.5 · v8.36 内容质量轻校验(治本 SVC-PLATFORM-F054 Bug 2 case)──
    # case:Claude reviewer 收到 prompt 后只 echo template 不真 review
    # 用户决策(Option "只校验空内容/空模板"):不语义判 reviewer 质量 · 只校验明显空/模板
    # WARN 不 BLOCK · 决策权留用户
    quality_warnings = _check_external_review_quality(stdout, args.stage, model)

    # ── Step 7 · emit ──
    # finding 数粗估(grep "^###" 或 "Finding" · 仅参考)
    finding_count = max(
        stdout.count("### Finding"),
        stdout.count("#### Finding"),
        stdout.lower().count("finding "),
    )
    emit({
        "verdict": "OK",
        "command": "external-review",
        "host": host,
        "host_source": host_source,  # v8.36:state_json / audit_deprecated / explicit
        "model": model,
        "model_version": model_version,
        "stage": args.stage,
        "profile": str(profile_path),
        "commit": commit,
        "base": base,
        "codex_model": codex_model if model == "codex" else None,  # v8.23
        "cwd": str(git_root),  # v8.23:codex 实际跑的 cwd
        "file_path": str(output_file),
        "finding_count_estimate": finding_count,
        "stdout_bytes": len(stdout),
        "next_hint": (
            f"file 已落盘 · PMO 整合 finding 到 REVIEW.md · "
            f"然后跑 state.py {args.stage}-complete --artifacts ..."
        ),
        # v8.36:host 来源 deprecated 警告 + 内容质量轻校验 WARN(不 BLOCK · R0 兜底)
        **({"deprecation_warning": deprecation_warning} if deprecation_warning else {}),
        **({"quality_warnings": quality_warnings} if quality_warnings else {}),
    })


# v8.36:external review 内容质量轻校验(治本 SVC-PLATFORM-F054 Bug 2)
# 用户决策:不语义判 reviewer 质量 · 只校验明显空/模板回声(template echo)
# 触发 WARN(不 BLOCK)· 决策权留用户
EXTERNAL_REVIEW_MIN_BYTES = 200  # 小于此 → empty WARN
EXTERNAL_REVIEW_TEMPLATE_ECHO_SIGNATURES = [
    # reviewer 自述"我没真 review · 只是收到了 prompt"的特征字符串
    "你给了我",
    "你给了我 reviewer prompt",
    "reviewer prompt template",
    "I received the prompt",
    "I received your prompt",
    "你只是给我了 template",
    "i only got a template",
    "i was only given the prompt",
    "只是模板",
    "{{stage}}",  # 占位符未替换 = template echo
    "{{commit}}",
    "{{feature_id}}",
]


def _check_external_review_quality(stdout: str, stage: str, model: str) -> list[dict]:
    """v8.36 治本 SVC-PLATFORM-F054 Bug 2:reviewer 只 echo template 不真 review case。

    返回 warnings list · 每条 {type, message, severity}:
      - empty_content:stdout < EXTERNAL_REVIEW_MIN_BYTES bytes
      - template_echo:命中 EXTERNAL_REVIEW_TEMPLATE_ECHO_SIGNATURES

    WARN 不 BLOCK(用户决策 · R0 兜底)· PMO 自行判是否重跑或接受。
    """
    warnings: list[dict] = []
    body = stdout.strip()
    body_bytes = len(body.encode("utf-8"))

    # ① 空内容 WARN
    if body_bytes < EXTERNAL_REVIEW_MIN_BYTES:
        warnings.append({
            "type": "empty_content",
            "severity": "WARN",
            "message": (
                f"⚠️ reviewer 内容仅 {body_bytes} 字节(< {EXTERNAL_REVIEW_MIN_BYTES} "
                f"阈值)· 可能 model={model!r} 没真评审 · 建议复查 file 内容 · "
                f"必要时重跑 external-review(也可能是 reviewer 故意精简 · 用户判)"
            ),
            "actual_bytes": body_bytes,
            "threshold_bytes": EXTERNAL_REVIEW_MIN_BYTES,
        })

    # ② template echo WARN(reviewer 自述"我没真评审"或占位符未替换)
    body_lower = body.lower()
    matched_sigs = [s for s in EXTERNAL_REVIEW_TEMPLATE_ECHO_SIGNATURES
                    if s.lower() in body_lower]
    if matched_sigs:
        warnings.append({
            "type": "template_echo",
            "severity": "WARN",
            "message": (
                f"⚠️ reviewer 内容含 template echo 特征({len(matched_sigs)} 条命中)· "
                f"model={model!r} 可能只复述了 prompt 而不是真评审 · "
                f"治本 SVC-PLATFORM-F054 Bug 2 case · 建议复查 file 内容 · "
                f"必要时调整 prompt 或重跑 external-review(用户判)"
            ),
            "matched_signatures": matched_sigs[:5],
        })

    return warnings


# ─── v8.24 · update-skill(自更新 · bootstrap 检测后用户回 1 触发)──────


def cmd_update_skill(args: argparse.Namespace) -> None:
    """v8.24:state.py update-skill · git pull skill repo(用户显式 · 不自动突袭)。

    设计:bootstrap 自动检测线上版本 · 落后 emit R5 1/2 选项 · 用户回 1 跑此命令。
    流程:
      1. 检测 $SKILL_ROOT 是否 git repo(不是 → BLOCK with hint zip 重装)
      2. git status --porcelain 检测脏树(脏 → BLOCK 防覆盖本地定制)
      3. git fetch origin main · 算 ahead/behind
      4. git pull --ff-only origin main(失败 → BLOCK with hint 手动 rebase)
      5. emit old_version / new_version / changed_files 摘要 + changelog hint
    """
    # skill_root:从 state.py 文件位置反推(同 bootstrap)
    skill_root = Path(__file__).resolve().parent.parent

    # ── Step 1:检测 git repo ──
    r = subprocess.run(["git", "-C", str(skill_root), "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        emit({
            "verdict": "FAIL",
            "command": "update-skill",
            "error": f"{skill_root} 不是 git repo · 无法自动 update",
            "hint": (
                f"skill 是 zip 安装 · 不支持自动 update。\n"
                f"  手动:① 备份本地定制 ② rm -rf {skill_root} · "
                f"git clone https://github.com/okteam99/teamwork.git {skill_root}"
            ),
            "skill_root": str(skill_root),
        })
        return
    git_root = Path(r.stdout.strip())

    # ── Step 2:检测脏树 ──
    s = subprocess.run(["git", "-C", str(git_root), "status", "--porcelain"],
                       capture_output=True, text=True, timeout=10)
    dirty_files = [ln.strip() for ln in s.stdout.splitlines() if ln.strip()]
    if dirty_files and not args.force:
        emit({
            "verdict": "FAIL",
            "command": "update-skill",
            "error": f"git 工作树不干净({len(dirty_files)} 个改动)· 拒绝 pull 防覆盖本地定制",
            "dirty_files": dirty_files[:10],
            "hint": (
                f"二选一:\n"
                f"  ① 提交 / stash 本地改动后重跑:cd {git_root} · git stash\n"
                f"  ② 确认本地改动可丢弃 · 加 --force 强制 pull(慎用 · 会覆盖)\n"
                f"  注:若 dirty 是 bootstrap auto-maintain 的 .gitignore 改动 "
                f"(v8.31 加的 harness locks 等)· v8.35 已修(bootstrap 不再改 SKILL_ROOT 自己 .gitignore)· "
                f"先 git checkout -- .gitignore 丢弃后重跑"
            ),
            "git_root": str(git_root),
        })
        return

    # ── Step 3:读 old version(pull 前) ──
    skill_md = skill_root / "SKILL.md"
    old_version = None
    if skill_md.exists():
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^version:\s*(\S+)\s*$", text, re.MULTILINE)
        if m:
            old_version = m.group(1).strip()

    # ── Step 4:git fetch + pull --ff-only ──
    f = subprocess.run(["git", "-C", str(git_root), "fetch", "origin", "main"],
                       capture_output=True, text=True, timeout=60)
    if f.returncode != 0:
        emit({
            "verdict": "FAIL",
            "command": "update-skill",
            "error": f"git fetch origin main 失败:{f.stderr.strip()[:200]}",
            "hint": "检查网络 / origin remote · 修复后重跑",
        })
        return

    p = subprocess.run(["git", "-C", str(git_root), "pull", "--ff-only", "origin", "main"],
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        emit({
            "verdict": "FAIL",
            "command": "update-skill",
            "error": f"git pull --ff-only failed:{p.stderr.strip()[:200]}",
            "hint": (
                "本地分叉 / 冲突 · 手动 rebase 或 reset:\n"
                f"  cd {git_root} · git status · git log HEAD..origin/main · "
                "评估后 git rebase origin/main 或丢弃本地 git reset --hard origin/main(慎)"
            ),
        })
        return

    # ── Step 5:读 new version + diff 摘要 ──
    new_version = None
    if skill_md.exists():
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^version:\s*(\S+)\s*$", text, re.MULTILINE)
        if m:
            new_version = m.group(1).strip()

    # 算 changed files(老 HEAD vs 新 HEAD · pull 前后 diff)
    # pull 之后 HEAD 已变 · 用 ORIG_HEAD 拿 pull 前的 commit
    d = subprocess.run(["git", "-C", str(git_root), "diff", "--stat",
                        "ORIG_HEAD..HEAD"],
                       capture_output=True, text=True, timeout=15)
    changed_files_stat = d.stdout.strip() if d.returncode == 0 else ""
    # 算 commit 数(pull 拉了多少新 commit)
    c = subprocess.run(["git", "-C", str(git_root), "rev-list", "--count",
                        "ORIG_HEAD..HEAD"],
                       capture_output=True, text=True, timeout=15)
    new_commit_count = int(c.stdout.strip()) if c.returncode == 0 and c.stdout.strip().isdigit() else 0

    same_version = old_version == new_version
    emit({
        "verdict": "OK",
        "command": "update-skill",
        "old_version": old_version,
        "new_version": new_version,
        "version_changed": not same_version,
        "new_commit_count": new_commit_count,
        "changed_files_stat": changed_files_stat[-2000:] if changed_files_stat else "",
        "git_root": str(git_root),
        "next_hint": (
            f"✅ 升级 {old_version} → {new_version}({new_commit_count} 个新 commit)· "
            f"查 {git_root}/skills/teamwork/docs/CHANGELOG.md 顶部新版本段了解变更。"
            if not same_version else
            f"已在最新版本 {new_version} · 无变化"
        ),
    })


def cmd_audit_raw_writes(args: argparse.Namespace) -> None:
    """v8.12:跨 Feature 汇总所有 raw-write 历史 · 帮助识别状态机缺口。

    扫 --features-root 下所有 state.json · 抓 concerns 中 raw-write 条目 · 聚合统计。
    """
    import re

    root = Path(args.features_root or "docs/features").resolve()
    if not root.exists():
        die(1, json.dumps({
            "verdict": "FAIL",
            "command": "audit-raw-writes",
            "error": f"features_root 不存在: {root}",
            "hint": "用 --features-root <绝对路径> 指定 · 默认 docs/features",
        }, ensure_ascii=False, indent=2))

    by_feature: dict[str, dict] = {}
    by_field: dict[str, int] = {}
    total = 0
    saved = os.environ.get(CHECKSUM_BYPASS_ENV)
    os.environ[CHECKSUM_BYPASS_ENV] = "1"
    try:
        for state_json in root.rglob("state.json"):
            try:
                state = json.loads(state_json.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            feature_name = state_json.parent.name
            concerns = state.get("concerns") or []
            rw = [c for c in concerns if isinstance(c, str) and "raw-write" in c]
            if not rw:
                continue
            by_feature[feature_name] = {
                "count": len(rw),
                "occurrences": rw,
            }
            total += len(rw)
            # 粗 extract 字段(reason 中"current_stage" 等)
            for c in rw:
                # raw-write 自身写的:"raw-write 跳过校验 · 改动 N 字段 · 理由:..."
                # 不含字段名 · 但 reason 可能含 · 简单抓 typical fields
                for field_hint in (
                    "current_stage", "legal_next_stages", "completed_stages",
                    "stage_contracts", "ship", "evidence", "rounds",
                ):
                    if field_hint in c:
                        by_field[field_hint] = by_field.get(field_hint, 0) + 1
    finally:
        if saved is None:
            del os.environ[CHECKSUM_BYPASS_ENV]
        else:
            os.environ[CHECKSUM_BYPASS_ENV] = saved

    # frequency hint
    freq_alert = []
    for field, cnt in sorted(by_field.items(), key=lambda x: -x[1]):
        if cnt >= 2:
            freq_alert.append(
                f"{field}: {cnt} 次 · 频次 ≥2 → 提示状态机有专用命令缺口"
            )

    emit({
        "verdict": "OK",
        "command": "audit-raw-writes",
        "features_root": str(root),
        "total_raw_writes": total,
        "feature_count": len(by_feature),
        "by_feature": by_feature,
        "by_field_frequency": dict(sorted(by_field.items(), key=lambda x: -x[1])),
        "frequency_alert": freq_alert,
        "hint": (
            "v8.x 后任何 raw-write 都应视作状态机缺口信号 · 复查每条 reason → 治本:\n"
            "  - current_stage → state.py jump-to-stage(v8.11+)\n"
            "  - stage_contracts.X.evidence → 检查 stage-complete 是否漏持久化(v8.8 治本通用)\n"
            "  - legal_next_stages → 一般是 jump-to-stage 后副产物\n"
            "  - 其他 → 报 bug 或确认是否真异常"
        ),
    })


def cmd_jump_to_stage(args: argparse.Namespace) -> None:
    """v8.11:跳到任意合法 stage · 替代 raw-write current_stage 滥用。

    典型 case:pm_acceptance rejected_with_feedback · 用户选回 goal 改 PRD / 回 ui_design 改 UI。

    校验:
    - --to 必须在 LEGAL_STAGES
    - --to 必须在当前 flow_type 的 FLOW 表(防跳到该 flow 不存在的 stage)
    - --to != current_stage(防 no-op)
    - ship 后(ship.phase ∈ {pushed, merged})不可跳 · 状态不可逆

    动作:
    - current_stage = --to
    - legal_next_stages = flow_graph[--to]
    - --to 的 contract gates 重置(允许重做)+ restarted_at / restarted_from / restarted_reason
    - 加 concerns WARN(audit)
    - completed_stages 不动(保留历史)
    """
    saved = os.environ.get(CHECKSUM_BYPASS_ENV)
    os.environ[CHECKSUM_BYPASS_ENV] = "1"
    try:
        path = state_path(args.feature)
        state = json.loads(path.read_text(encoding="utf-8"))
    finally:
        if saved is None:
            del os.environ[CHECKSUM_BYPASS_ENV]
        else:
            os.environ[CHECKSUM_BYPASS_ENV] = saved

    target = args.to
    current = state.get("current_stage")

    # 1. enum 校验
    if target not in LEGAL_STAGES:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "jump-to-stage",
            "error": f"--to={target!r} 不在 LEGAL_STAGES",
            "legal_stages": sorted(LEGAL_STAGES),
        }, ensure_ascii=False, indent=2))

    # 2. 当前 flow_type 必须含 target stage
    flow_type = state.get("flow_type")
    flow_graph = FLOW_BY_TYPE.get(flow_type, {})
    if not flow_graph:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "jump-to-stage",
            "error": f"flow_type={flow_type!r} 无 FLOW 表(不进状态机的流程不支持 jump)",
        }, ensure_ascii=False, indent=2))
    if target not in flow_graph:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "jump-to-stage",
            "error": f"--to={target!r} 不在 flow_type={flow_type!r} 的 FLOW 表",
            "valid_stages_for_flow": sorted(flow_graph.keys()),
        }, ensure_ascii=False, indent=2))

    # 3. ship 后不可跳
    ship_phase = (state.get("ship") or {}).get("phase")
    if ship_phase in ("pushed", "merged"):
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "jump-to-stage",
            "error": f"Ship 后不可跳 · ship.phase={ship_phase!r} · 状态不可逆",
            "hint": (
                "若需修复 · 走 ship-phase --action close-unmerged 或开新 Feature"
            ),
        }, ensure_ascii=False, indent=2))

    # 4. target == current(no-op)
    if target == current:
        die(1, json.dumps({
            "verdict": "FAIL",
            "action": "jump-to-stage",
            "error": f"--to={target!r} 与 current_stage 相同 · no-op",
        }, ensure_ascii=False, indent=2))

    # 5. 改 current_stage + legal_next_stages
    state["current_stage"] = target
    state["legal_next_stages"] = flow_graph.get(target, [])

    # 6. 重置 target stage contract gates(允许重做 + audit 留痕)
    contracts = state.setdefault("stage_contracts", {})
    target_contract = contracts.setdefault(target, {})
    target_contract["input_satisfied"] = False
    target_contract["process_satisfied"] = False
    target_contract["output_satisfied"] = False
    target_contract.pop("completed_at", None)
    target_contract.pop("duration_minutes", None)
    target_contract["restarted_at"] = now_iso()
    target_contract["restarted_from_stage"] = current
    target_contract["restarted_reason"] = args.reason

    # 7. 加 concerns WARN
    state.setdefault("concerns", []).append(
        f"{now_iso()} WARN jump-to-stage: {current!r} → {target!r} · reason: {args.reason}"
    )

    # 8. completed_stages 不动(保留历史 · 不像 reset-prev 去尾)
    state["updated_at"] = now_iso()
    state["updated_by"] = "jump-to-stage"
    atomic_write(path, state)

    emit({
        "verdict": "OK",
        "action": "jump-to-stage",
        "from_stage": current,
        "to_stage": target,
        "reason": args.reason,
        "legal_next_stages": state["legal_next_stages"],
        "completed_stages": state.get("completed_stages", []),
        "next_action_brief": (
            f"## jump-to-stage 完成\n\n"
            f"已跳:{current!r} → {target!r}\n"
            f"contract 重置:{target} 三 gate 全 false · 可跑 {target}-start 重做。\n\n"
            f"下一步:`state.py {target}-start --feature {args.feature}`\n\n"
            f"⚠️ 已自动追 concerns WARN(audit 透明)· completed_stages 不变。"
        ),
    })


def cmd_recover(args: argparse.Namespace) -> None:
    """Re-checksum after manual edit · adds concern WARN · 留 audit trail."""
    saved = os.environ.get(CHECKSUM_BYPASS_ENV)
    os.environ[CHECKSUM_BYPASS_ENV] = "1"
    try:
        path = state_path(args.feature)
        state = json.loads(path.read_text(encoding="utf-8"))
    finally:
        if saved is None:
            del os.environ[CHECKSUM_BYPASS_ENV]
        else:
            os.environ[CHECKSUM_BYPASS_ENV] = saved

    old_cs = state.get(CHECKSUM_FIELD)
    concerns = state.setdefault("concerns", [])
    concerns.append({
        "severity": "WARN",
        "message": f"state.json checksum recovered after manual edit · reason: {args.reason}",
        "timestamp": now_iso(),
    })
    atomic_write(path, state)
    emit({
        "verdict": "OK",
        "action": "recover",
        "feature": args.feature,
        "old_checksum_prefix": old_cs[:24] if old_cs else None,
        "new_checksum_prefix": state[CHECKSUM_FIELD][:24],
        "reason": args.reason,
        "concerns_appended": True,
    })


class JsonErrorArgumentParser(argparse.ArgumentParser):
    """argparse 参数错误也 emit JSON(治本 AI `state.py xxx | json.load` 管道遇参数错误炸 Traceback)。

    argparse 默认 error() 打 usage 到 stderr(非 JSON)· state.py 其它输出都是 JSON ·
    此子类让参数错误也结构化 · 保证 state.py 全部输出可被 json.load。
    add_subparsers 默认 parser_class = type(主 parser) · 所有子命令自动继承。
    """

    def error(self, message: str):  # noqa: D102
        payload = {
            "verdict": "FAIL",
            "error": f"参数错误: {message}",
            "command": self.prog,
            "usage": self.format_usage().strip(),
            "hint": "补全缺失 / 修正参数后重试 · 各参数说明见 `<command> --help`",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(2)


def _add_feature_arg(parser: argparse.ArgumentParser, *, help_text: str | None = None) -> None:
    """统一注册 --feature · 缺省时从 TEAMWORK_FEATURE 环境变量读取（v7.3.10+P0-130 ergonomics）。"""
    env = os.environ.get("TEAMWORK_FEATURE")
    parser.add_argument(
        "--feature",
        required=(env is None),
        default=env,
        help=help_text or ("artifact_root（含 state.json 的目录）"
                           + (f" · 默认从 $TEAMWORK_FEATURE={env}" if env else "")),
    )

def build_parser() -> argparse.ArgumentParser:
    p = JsonErrorArgumentParser(prog="state.py", description="Teamwork state.json tool (P1)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("snapshot", aliases=["status"],
                        help="返回精简关注字段（cite-friendly · 看当前 stage/下一步 · 别名 status · compact 恢复用）")
    _add_feature_arg(sp)
    sp.add_argument("--tier", choices=["core", "stage", "full"], default="core")
    sp.add_argument("--cite", help="额外关注字段，逗号分隔的 dotted path")
    sp.set_defaults(func=cmd_snapshot)

    vp = sub.add_parser("validate", help="schema + 状态机 + evidence-binding 全量校验")
    _add_feature_arg(vp)
    vp.set_defaults(func=cmd_validate)

    rp = sub.add_parser(
        "raw-read",
        help="🚪 逃生舱：读全 state.json 或指定 dotted path（仅 debug/migration）",
    )
    _add_feature_arg(rp)
    rp.add_argument("--field", help="可选 · dotted path · 缺省返回全 JSON")
    rp.set_defaults(func=cmd_raw_read)

    rw = sub.add_parser(
        "raw-write",
        help="🚪 逃生舱：跳过 schema/状态机校验直写 · 自动追加 concerns WARN（必带 --reason）",
    )
    _add_feature_arg(rw)
    rw.add_argument("--set", action="append", required=True,
                    help="key=val · val 优先按 JSON 解析 · 可多次")
    rw.add_argument("--reason", required=True, help="必填 · 写入 concerns WARN")
    rw.set_defaults(func=cmd_raw_write)

    # v8.0:enter-stage / satisfy-gate / complete-stage / ship-* / pm-decision /
    # add-concern / bug-frontmatter / micro-validate 全部已物理删除(v8 用各 stage
    # -start/-complete + ship-phase --action 替代)。
    # 上述 cmd_* 函数中 add_concern / bug_frontmatter / micro_validate 保留为内部
    # utility(可能被迁移工具调用)· cmd_pm_decision **已物理删除** —— v7 fossil
    # 写 contract.decision(v8 用 evidence.decision)· 留着是 landmine。

    # P5 (v7.3.10+P0-148): init-feature + recover
    ifp = sub.add_parser(
        "init-feature",
        help="创建 Feature state.json · 替代手工 Write（v7.3.10+P0-148）",
    )
    ifp.add_argument("--feature", required=True,
                     help="🔴 目标 feature 目录的**完整路径**（绝对或相对 CWD）· "
                          "如 apps/admin/docs/features/ADMIN-F013-x · "
                          "**不是仅 feature 名**（v7.3.10+P0-149 修复 PTR-F032 实战 bug）· "
                          "state.json 落此处 · 同时作为 state.artifact_root 字段值")
    ifp.add_argument("--feature-id", required=True,
                     help="如 ADMIN-F013-tax-billing · 应是 --feature basename")
    ifp.add_argument("--flow-type", required=True,
                     choices=["Feature", "Bug", "Micro", "敏捷需求",
                              "Feature Planning", "问题排查"])
    ifp.add_argument("--sub-project", help="如 admin / api-server")
    # v7.3.10+P0-149: 删 --artifact-root 冗余参数 · --feature 单源（既是落盘目录又是 artifact_root 字段值）
    ifp.add_argument("--initial-stage",
                     help="缺省按 flow_type 决定（Feature→goal / Bug→dev / Micro→dev / ...）")
    ifp.add_argument("--merge-target", required=True, help="如 staging / main")
    ifp.add_argument("--branch", required=True, help="如 feat/admin-f013-x")
    ifp.add_argument("--worktree-mode", choices=["auto", "manual", "off"],
                     default="off")
    ifp.add_argument("--worktree-path",
                     help="worktree 绝对路径 · worktree-mode != off 时建议提供")
    ifp.add_argument("--auto-mode", action="store_true", help="启用 AUTO_MODE")
    ifp.add_argument("--force", action="store_true",
                     help="覆盖现有 state.json（自动 backup .bak.<ts>）")
    # v8.36:host 改 per-feature(治本 v8.21 全局 audit 跨 session 污染 case)
    ifp.add_argument("--host",
                     choices=["claude-code", "codex-cli", "gemini-cli"],
                     help="[v8.36] 主对话宿主 · 写到 state.json.host · external-review 等下游"
                          "读 per-feature host(不再读全局 ~/.teamwork/host_audit.json)· "
                          "可选 · 不传则 fallback 读全局 audit(deprecated · 兼容)")
    ifp.set_defaults(func=cmd_init_feature)

    rcv = sub.add_parser(
        "recover",
        help="重新认证 checksum（state.json 被外部修改后）· 追加 concerns WARN（v7.3.10+P0-148）",
    )
    _add_feature_arg(rcv)
    rcv.add_argument("--reason", required=True,
                     help="必填 · 解释为什么手动改了 state.json · 入 audit")
    rcv.set_defaults(func=cmd_recover)

    # v8.0+P0-6:reset-prev 状态机回退一步(替代 raw-write 滥用)
    rp = sub.add_parser(
        "reset-prev",
        help="[v8] 状态机回退一步 · 治本 raw-write 滥用(Ship 后不可回 · 自动 concerns WARN)",
    )
    _add_feature_arg(rp)
    rp.add_argument("--reason", required=True,
                    help="必填 · 回退原因 · 自动追 concerns WARN")
    rp.set_defaults(func=cmd_reset_prev)

    # v8.11:jump-to-stage 跳任意合法 stage(替代 raw-write current_stage)
    jp = sub.add_parser(
        "jump-to-stage",
        help="[v8] 跳到任意合法 stage · 治本 raw-write 滥用 · 自动 audit(典型 case:pm_acceptance rejected 跳 goal/ui_design)",
    )
    _add_feature_arg(jp)
    jp.add_argument("--to", required=True,
                    help="目标 stage(必须在 LEGAL_STAGES + 当前 flow_type FLOW 表)")
    jp.add_argument("--reason", required=True,
                    help="必填 · 跳转原因 · 自动追 concerns WARN")
    jp.set_defaults(func=cmd_jump_to_stage)

    # v8.12:audit-raw-writes 跨 Feature 汇总 raw-write 历史(治本 raw-write 缺口识别)
    arw = sub.add_parser(
        "audit-raw-writes",
        help="[v8] 跨 Feature 汇总 raw-write 历史 · 识别状态机缺口(频次 ≥2 = 应有专用命令)",
    )
    arw.add_argument("--features-root", default=None,
                     help="features 根目录 · 默认 docs/features(从 cwd 算)")
    arw.set_defaults(func=cmd_audit_raw_writes)

    # v8.13:prepare-check ID 冲突预检(prepare 子流程 §1.5.4 调)
    # v8.15:加 --user-intent + --admission-judgment(物化 AI 必读 §2.1/§2.2 · 治本 F001 GCP gateway case)
    pc = sub.add_parser(
        "prepare-check",
        help="[v8] prepare 子流程 ID 冲突预检 + admission 校验 · 输出 next_available_id + consistency",
    )
    pc.add_argument("--features-root", default=None,
                    help="features 根目录 · 默认 docs/features(从 cwd 算)")
    pc.add_argument("--feature-id-prefix", required=True,
                    help="项目缩写(如 PTR / INFRA / SVC-PLATFORM)· 详 docs/conventions.md § 7")
    pc.add_argument("--flow-type", default=None,
                    choices=["Feature", "Bug", "Micro", "敏捷需求"],
                    help=("决定 artifact ID 字母(F/B/M · 详 conventions.md §1)+ "
                          "返回 stage_chain_preview · Bug/Micro 必传(漏传退回 F)"))
    # v8.15:admission(AI judgment 模式 · 不用 regex 关键词)
    pc.add_argument("--user-intent", default=None,
                    help=("[v8.15] 用户原话(原文 · 不要 paraphrase)· "
                          "工具不解析 · 仅留痕到 audit jsonl · 供 retro 复盘"))
    pc.add_argument("--admission-judgment", default=None,
                    help=("[v8.15] AI 读 prepare.md §2.1/§2.2 后的判断(JSON · 必含 "
                          "sections_reviewed[] · matched_signals[] · recommended_flow_type · "
                          "ai_rationale 4 字段)· 强制 AI 真读 §2.1/§2.2 而非凭概览 · "
                          "工具校验 recommended_flow_type vs --flow-type · MISMATCH → WARN(不 BLOCK)"))
    pc.set_defaults(func=cmd_prepare_check)

    # v8.x:change-review-roles · 治本 raw-write 滥用(可枚举进脚本 · R0 哲学)
    crr = sub.add_parser(
        "change-review-roles",
        help="[v8] 调整某 stage 的 review_roles · 自动写 audit · 替代 raw-write",
    )
    crr.add_argument("--feature", required=True,
                     help="Feature/Bug 目录(含 state.json)")
    crr.add_argument("--stage", required=True,
                     help="目标 stage(必在 state.stage_review_roles 已配置之列)")
    crr.add_argument("--roles", required=True,
                     help="逗号分隔的角色列表(如 'qa,architect,external') · 必属 REVIEW_ROLE_ENUM")
    crr.add_argument("--reason", required=True,
                     help="调整理由(必填 · 写 stage_review_roles_adjustments audit)")
    crr.set_defaults(func=cmd_change_review_roles)

    # v8.20:external-review · 异质模型评审一条命令调起(治本 SVC-CORE-F034 case)
    er = sub.add_parser(
        "external-review",
        help=(
            "[v8.20] 调起异质模型(codex/claude)做外部 review · 按宿主自动选模型 · "
            "落合规 external-cross-review/<stage>-<model>.md(治本 PMO 自己拼命令 / "
            "用 Agent subagent 自审 case)"
        ),
    )
    er.add_argument("--feature", required=True,
                    help="Feature 目录(含 state.json)")
    er.add_argument("--stage", required=True,
                    choices=["goal", "blueprint", "review"],
                    help=("review 阶段:goal=PRD / blueprint=TC+TECH / review=代码 · "
                          "工具按 stage 自动选 reviewer profile"))
    er.add_argument("--host", default=None,
                    choices=["claude-code", "codex-cli", "gemini-cli"],
                    help=("[v8.21 可选]主对话宿主 · 缺省自动从 ~/.teamwork/host_audit.json "
                          "读取(bootstrap 跑过一次即可)· 决定异质 model:claude-code→codex · "
                          "codex-cli→claude · gemini-cli→codex(默认)"))
    er.add_argument("--model", default=None,
                    choices=["codex", "claude"],
                    help=("显式指定异质模型(覆盖按 host 自动映射)· "
                          "校验:必 ≠ host 同源 · 违 R3 直接 BLOCK"))
    er.add_argument("--commit", default=None,
                    help=("review 目标 commit SHA · 缺省从 state.stage_contracts."
                          "<stage>.auto_commit 取 · 再缺从 git HEAD"))
    er.add_argument("--base", default=None,
                    help="diff base 分支 · 缺省 state.merge_target")
    er.add_argument("--title", default=None,
                    help="review 标题 · 缺省 '<feature_id> · <stage> stage external review'")
    er.add_argument("--codex-model", default=None,
                    help=("[v8.30] codex CLI 用的具体模型(传给 codex --config 'model=<this>')· "
                          "优先级:--codex-model > .teamwork_localconfig.json external_review.codex_model > "
                          "**不传**(用 codex CLI 默认 · 兼容 ChatGPT 订阅 · 治本 ChatGPT 账号不允许显式模型 case)。"
                          "🔴 模型字面 **不假设** —— codex CLI 版本迭代会换模型名 · 跑 `codex` 交互界面选 / "
                          "或 `codex --help` 查 ChatGPT 订阅可能拒绝任何显式 model · 仅 API key 模式可显式。"))
    er.add_argument("--dry-run", action="store_true",
                    help="只输出将跑的命令 + 校验 · 不实际调 CLI(供 debug / preview)")
    er.set_defaults(func=cmd_external_review)

    # v8.24:update-skill · 自更新(bootstrap 检测后用户回 1 触发)
    us = sub.add_parser(
        "update-skill",
        help=("[v8.24] git pull skill repo · 升级到 GitHub 最新版本 · "
              "脏树 BLOCK 防覆盖本地定制 · 用户显式跑(bootstrap 检测后回 1 触发)"),
    )
    us.add_argument("--force", action="store_true",
                    help="脏树时强制 pull(慎用 · 会覆盖本地未提交改动)")
    us.set_defaults(func=cmd_update_skill)

    # ─── v8.0 stage 命令注册(Code-driven Orchestration) ─────────────
    # 设计文档:docs/v8-redesign/00-MANIFESTO.md
    # 命令 schema:docs/v8-redesign/01-COMMAND-SCHEMA.md
    # 引擎模块:
    # - _v8_engine.py   通用 stage start/complete + bypass 协议
    # - _v8_stage_specs.py  11 stage 完整契约
    # - _v8_ship.py     ship-phase 子动作(替代 v7 ship-*)
    # - _v8_migrate.py  migrate-v7-to-v8 一次性迁移
    #
    # 注:v8.0+P0-12 删除 _v8_init.py(triage + prepare 命令)·
    #     入口分诊是 PMO 行为(按 SKILL.md § Triage 入口规范 规范做)· 不在 state.py 范围。
    try:
        from _v8_engine import register_v8_subparsers
        from _v8_stage_specs import STAGE_SPECS as V8_STAGE_SPECS
        from _v8_ship import register_v8_ship_subparser
        from _v8_migrate import register_v8_migrate_subparser

        register_v8_subparsers(sub, V8_STAGE_SPECS, FLOW_BY_TYPE)
        register_v8_ship_subparser(sub)
        register_v8_migrate_subparser(sub)
    except ImportError as _e:
        # v8 模块不可用 · 不影响 v7 命令 · 不打印警告(silent execution)
        pass

    # v8.0+P0-13:session-bootstrap 是独立脚本 tools/bootstrap.py · 不在 state.py 域

    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
