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
    "goal_plan",
    "ui_design",
    "panorama_design",
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
    "goal_plan": ["ui_design", "blueprint"],
    "ui_design": ["blueprint"],
    "panorama_design": ["blueprint"],
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

FLOW_BY_TYPE = {"Feature": FEATURE_FLOW, "Bug": BUG_FLOW}

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

    if args.tier == "full":
        emit({"verdict": "OK", "snapshot": state})
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
    """
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
    """
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
    if args.field:
        val = get_dotted(state, args.field)
        emit({"verdict": "OK", "field": args.field, "value": val})
        return
    emit({"verdict": "OK", "warning": "raw-read 全量返回 · 仅 debug/migration 使用", "state": state})


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
    "Feature": "goal_plan",
    "Bug": "dev",
    "Micro": "dev",
    "敏捷需求": "blueprint_lite",
    "Feature Planning": "planning",
    "问题排查": "triage",
}


def cmd_init_feature(args: argparse.Namespace) -> None:
    """Create initial state.json · 替代手工 Write（v7.3.10+P0-148 / +P0-149 fix）。

    v7.3.10+P0-149 修复（实战 case PTR-F032）：移除 --artifact-root 冗余参数 ·
    --feature 是单源（既是 state.json 落盘目录 · 又是 state.artifact_root 字段值）·
    防"双参数语义重叠导致 state.json 落错位置"。
    """
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
        args.flow_type, "goal_plan"
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
    atomic_write(state_file, state)
    emit({
        "verdict": "OK",
        "action": "init-feature",
        "feature_id": args.feature_id,
        "flow_type": args.flow_type,
        "current_stage": initial_stage,
        "state_path": str(state_file),
        "checksum_prefix": state[CHECKSUM_FIELD][:24],
        "created_at": state["created_at"],
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

    es = sub.add_parser("enter-stage", help="转移到目标 Stage（校验 legal_next_stages）")
    _add_feature_arg(es)
    es.add_argument("--stage", required=True)
    es.add_argument("--allow-skip", action="store_true",
                    help="🚪 跳过 / 回炉时显式声明 · 自动记 concerns WARN")
    es.add_argument("--cite", help="额外关注字段，逗号分隔的 dotted path")
    es.set_defaults(func=cmd_enter_stage)

    sg = sub.add_parser("satisfy-gate",
                        help="标记当前 Stage 的 input/process/output gate 为 satisfied")
    _add_feature_arg(sg)
    sg.add_argument("--stage", required=True)
    sg.add_argument("--gate", required=True, choices=["input", "process", "output"])
    sg.add_argument("--artifacts", help="逗号分隔 · 写入 stage_contracts.{stage}.artifacts")
    sg.add_argument("--auto-commit", help="auto-commit hash · 多次调用自动升数组")
    sg.add_argument("--cite", help="额外关注字段")
    sg.set_defaults(func=cmd_satisfy_gate)

    cs = sub.add_parser("complete-stage",
                        help="收尾当前 Stage（要求三 gate 全 satisfied）")
    _add_feature_arg(cs)
    cs.add_argument("--stage", required=True)
    cs.add_argument("--auto-commit",
                    help="若 satisfy-gate output 时未提供 · 此处补 · 已存在则忽略")
    cs.add_argument("--cite", help="额外关注字段")
    cs.set_defaults(func=cmd_complete_stage)

    # ship-* (P3)
    sz = sub.add_parser("ship-sanitize", help="Step 1：净化记录（不改 phase）")
    _add_feature_arg(sz)
    sz.add_argument("--residual-commits", help="JSON · 形如 [{commit,files,reason}]")
    sz.add_argument("--cleaned-files", help="逗号分隔白名单文件")
    sz.add_argument("--suspicious-files", help="JSON · 形如 [{path,reason}]")
    sz.add_argument("--cite")
    sz.set_defaults(func=cmd_ship_sanitize)

    sp = sub.add_parser("ship-push", help="Step 2-3：null/closed_unmerged → pushed · 必带 5 件套")
    _add_feature_arg(sp)
    sp.add_argument("--feature-head-commit", required=True)
    sp.add_argument("--git-host", required=True, choices=sorted(SHIP_GIT_HOSTS))
    sp.add_argument("--mr-creation-method", required=True, choices=sorted(SHIP_MR_METHODS))
    sp.add_argument("--mr-url", help="CLI 实创建 URL（cli-gh / cli-glab）· 与 --mr-create-url 二选一")
    sp.add_argument("--mr-create-url", help="兜底 URL（url-fallback / unknown-platform）· 二选一")
    sp.add_argument("--feature-pushed-at", help="ISO 8601 · 缺省取 now")
    sp.add_argument("--cite")
    sp.set_defaults(func=cmd_ship_push)

    sm = sub.add_parser("ship-confirm-merged",
                        help="Step 4-8：pushed → merged · 含合并 evidence + finalize-push 状态（治本 P0-124）")
    _add_feature_arg(sm)
    sm.add_argument("--merge-commit-hash", required=True)
    sm.add_argument("--merge-detection-method", required=True, choices=sorted(SHIP_DETECTION_METHODS))
    sm.add_argument("--mr-merged-at", help="ISO 8601 · 缺省取 now")
    sm.add_argument("--merge-target-pushed-at", help="Step 8 push 成功 · ISO 8601")
    sm.add_argument("--merge-target-push-failed", action="store_true",
                    help="Step 8 push 失败降级到 feature 分支 · 必带 --failed-reason")
    sm.add_argument("--failed-reason", choices=sorted(SHIP_FINALIZE_PUSH_REASONS))
    sm.add_argument("--cite")
    sm.set_defaults(func=cmd_ship_confirm_merged)

    sc = sub.add_parser("ship-cleanup",
                        help="Step 9：worktree 清理状态（cleaned 必须 phase=merged · 治本 P0-124）")
    _add_feature_arg(sc)
    sc.add_argument("--status", required=True, choices=sorted(SHIP_CLEANUP_ENUM))
    sc.add_argument("--cite")
    sc.set_defaults(func=cmd_ship_cleanup)

    scl = sub.add_parser("ship-closed", help="异常段：MR 被关闭未合并 → closed_unmerged 或 abandoned")
    _add_feature_arg(scl)
    scl.add_argument("--abandon", action="store_true", help="彻底放弃 Feature → shipped=abandoned")
    scl.add_argument("--reason", help="可选 · INFO concerns")
    scl.add_argument("--cite")
    scl.set_defaults(func=cmd_ship_closed)

    # P4
    pd = sub.add_parser("pm-decision",
                        help="PM 验收决策落库（替代 P3 临时 raw-write 兜底）")
    _add_feature_arg(pd)
    pd.add_argument("--decision", required=True, choices=sorted(PM_DECISION_ENUM))
    pd.add_argument("--note", help="可选 · 决策说明")
    pd.add_argument("--cite")
    pd.set_defaults(func=cmd_pm_decision)

    ac = sub.add_parser("add-concern", help="通用 concerns 追加（自动时间戳 + 去重）")
    _add_feature_arg(ac)
    ac.add_argument("--severity", required=True, choices=sorted(CONCERN_SEVERITY))
    ac.add_argument("--message", required=True)
    ac.set_defaults(func=cmd_add_concern)

    bf = sub.add_parser("bug-frontmatter",
                        help="Bug 流程：BUG-REPORT.md frontmatter 维护（YAML · 平铺 key:val）")
    _add_feature_arg(bf, help_text="Feature artifact_root")
    bf.add_argument("--bug-id", required=True, help="如 BUG-001 · 自动 glob bugfix/BUG-{id}-*.md")
    bf.add_argument("--set", action="append",
                    help="key=val · val 优先按 JSON 解析 · 可多次")
    bf.add_argument("--validate-ship", action="store_true",
                    help="启用 ship 状态机镜像校验（phase/shipped/merged 三件套）")
    bf.set_defaults(func=cmd_bug_frontmatter)

    mv = sub.add_parser("micro-validate",
                        help="Micro 流程：校验 commit 已合入 origin/{merge_target}")
    mv.add_argument("--commit", required=True, help="待校验 commit hash")
    mv.add_argument("--merge-target", required=True, help="如 staging / main")
    mv.add_argument("--cwd", help="可选 · git 命令工作目录")
    mv.set_defaults(func=cmd_micro_validate)

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
                     help="缺省按 flow_type 决定（Feature→goal_plan / Bug→dev / Micro→dev / ...）")
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

    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
