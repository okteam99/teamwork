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
P4（已实现）：pm-decision / add-concern / bug-frontmatter / micro-validate
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
from typing import Any


# ─── 常量 ──────────────────────────────────────────────────────────────

LEGAL_STAGES = {
    "goal",
    "ui_design",
    "blueprint",
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

PM_DECISION_ENUM = {"approved_and_ship", "approved_no_ship", "rejected_with_feedback"}
CONCERN_SEVERITY = {"INFO", "WARN", "ERROR"}

# 各 flow_type 的 canonical 转移图（current_stage → legal_next_stages）
# 注：ui_design / browser_e2e 是可选 Stage（PMO 在 enter-stage 时按 spec 决策跳过 vs 启用）
FEATURE_FLOW: dict[str, list[str]] = {
    "goal": ["ui_design", "blueprint"],
    "ui_design": ["blueprint"],
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

# Feature Planning / 问题排查 不进状态机:由 PMO 主对话执行(详 docs/feature-planning.md)
FLOW_BY_TYPE = {
    "Feature": FEATURE_FLOW,
    "Bug": BUG_FLOW,
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


# ─── P4: pm-decision / add-concern ───────────────────────────────────


def cmd_pm_decision(args: argparse.Namespace) -> None:
    path = state_path(args.feature)
    state = json.loads(path.read_text(encoding="utf-8"))
    before = json.loads(json.dumps(state))

    if state.get("current_stage") != "pm_acceptance":
        die(1, json.dumps({"verdict": "FAIL",
                           "error": f"current_stage={state.get('current_stage')!r} ≠ 'pm_acceptance'"},
                          ensure_ascii=False, indent=2))
    if args.decision not in PM_DECISION_ENUM:
        die(1, _enum_err("--decision", args.decision, PM_DECISION_ENUM))

    contract = state.setdefault("stage_contracts", {}).setdefault("pm_acceptance", {})
    contract["decision"] = args.decision
    if args.note:
        contract["decision_note"] = args.note

    write_or_die(path, state)
    next_actions: list[str] = []
    if args.decision == "approved_and_ship":
        next_actions = ["satisfy-gate --stage pm_acceptance --gate output",
                        "complete-stage --stage pm_acceptance",
                        "enter-stage --stage ship"]
    elif args.decision == "approved_no_ship":
        next_actions = ["satisfy-gate --stage pm_acceptance --gate output",
                        "complete-stage --stage pm_acceptance",
                        "enter-stage --stage completed --allow-skip"]
    else:  # rejected_with_feedback
        next_actions = ["enter-stage --stage dev --allow-skip（按反馈派发修复）"]

    emit({
        "verdict": "PASS",
        "stage": "pm-decision",
        "updated_fields": diff_dotted(before, state, [
            "stage_contracts.pm_acceptance.decision",
            "stage_contracts.pm_acceptance.decision_note",
        ]),
        "cited_fields": collect_cited(state, args.cite),
        "next_actions": next_actions,
    })


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
    "敏捷需求": "blueprint_lite",
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
        "concerns": [],
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
                "rule": "TRIAGE.md §3.4 入口完成才进状态机",
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
        "next_action_brief": _init_feature_next_brief(args, initial_stage),
    })


def _init_feature_next_brief(args, initial_stage: str) -> str:
    """init-feature emit 后给 PMO 的 brief(v8.0+P0-5 简化)。

    triage 已确认 worktree · PMO 已显式建 + cd · init-feature 仅创建 state.json。
    所以 brief 直接告知"进下一步" · 不需要再讨论 worktree。
    """
    wt_note = ""
    if args.worktree_mode == "off":
        wt_note = "(worktree_mode=off · 在当前 tree 直接工作)"
    else:
        wt_note = f"(worktree_mode={args.worktree_mode} · cwd={Path.cwd()} 已通过 cwd 校验)"

    return f"""## init-feature 完成 · 下一步

{wt_note}

state.json 已落在:`{Path(args.feature).resolve()}/state.json`

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

    扫 --features-root 下已有 Feature 目录 · 抓 --feature-id-prefix 匹配的 ID ·
    返回 existing_ids + next_available_id · 让 prepare 暂停点直接填推荐。

    治本 case:PMO 启动 Feature 时不知 F040 已被 Planning 占用 · 临时改 F041 → 用户多确认一轮。
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

    # 扫匹配 <PREFIX>-F<NNN>* 目录
    pattern = re.compile(rf"^{re.escape(prefix)}-F(\d+)")
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
    next_id_stem = f"{prefix}-F{next_num:03d}"

    payload = {
        "verdict": "OK",
        "command": "prepare-check",
        "features_root": str(root),
        "feature_id_prefix": prefix,
        "existing_ids": existing_ids,
        "existing_count": len(existing_ids),
        "next_available_number": next_num,
        "next_available_id_stem": next_id_stem,
        "hint": (
            f"prepare 暂停点 Feature ID 默认填 {next_id_stem}-<Kebab-Case-名称> · "
            f"用户可改 · 但应避开 existing_ids 中已占编号"
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

    emit(payload)


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
    p = argparse.ArgumentParser(prog="state.py", description="Teamwork state.json tool (P1)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("snapshot", help="返回精简关注字段（cite-friendly）")
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
    # 上述 cmd_* 函数保留为内部 utility(可能被迁移工具调用),不再注册为子命令。

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
    pc = sub.add_parser(
        "prepare-check",
        help="[v8] prepare 子流程 ID 冲突预检 · 输出 next_available_id 给暂停点表格",
    )
    pc.add_argument("--features-root", default=None,
                    help="features 根目录 · 默认 docs/features(从 cwd 算)")
    pc.add_argument("--feature-id-prefix", required=True,
                    help="项目缩写(如 PTR / INFRA / SVC-PLATFORM)· 详 docs/conventions.md § 7")
    pc.add_argument("--flow-type", default=None,
                    choices=["Feature", "Bug", "Micro", "敏捷需求"],
                    help="可选 · 传则返回 stage_chain_preview(stage × 评审角色) · 让暂停点直接渲染表")
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
    #     入口分诊是 PMO 行为(按 TRIAGE.md 规范做)· 不在 state.py 范围。
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
