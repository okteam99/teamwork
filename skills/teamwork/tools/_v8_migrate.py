"""
_v8_migrate.py — Teamwork v7 → v8 state.json 迁移工具。

迁移规则:
- 添加 schema_version=v8.0
- 添加 bypass_log=[](v8 新字段)
- v7 字段 planned_execution / executor_history / detection_evidence 保留(可后续清理)
- stage_contracts.<stage>.evidence 字段补全(从 ship.* / 其他 v7 字段推断)
- 备份原 state.json 为 state.json.v7-backup
- 失败时不动原文件
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from _v8_engine import emit_json, now_iso


V8_SCHEMA_VERSION = "v8.0"  # v7 → v8 迁移目标
V8_1_SCHEMA_VERSION = "v8.1"  # v8.0 → v8.1 stage rename 目标

# v8.0 → v8.1 stage 改名映射
STAGE_RENAMES = {
    "goal_plan": "goal",
    "panorama_design": "planning",
}


def cmd_migrate_v7_to_v8(args: argparse.Namespace) -> None:
    """迁移 v7 state.json 到 v8 格式。"""
    feature_path = Path(args.feature).resolve()
    state_file = feature_path / "state.json"
    if not state_file.exists():
        emit_json({
            "verdict": "FAIL",
            "command": "migrate-v7-to-v8",
            "error": f"state.json 不存在: {state_file}",
        }, exit_code=1)

    state = json.loads(state_file.read_text(encoding="utf-8"))

    # 已迁移 → 拒绝
    if state.get("schema_version") == V8_SCHEMA_VERSION:
        emit_json({
            "verdict": "SKIP",
            "command": "migrate-v7-to-v8",
            "reason": f"已是 v8.0(schema_version={V8_SCHEMA_VERSION})",
        })

    changes = []

    # 1. 添加 schema_version
    state["schema_version"] = V8_SCHEMA_VERSION
    changes.append("schema_version=v8.0")

    # 2. 添加 bypass_log[]
    if "bypass_log" not in state:
        state["bypass_log"] = []
        changes.append("bypass_log=[]")

    # 3. stage_contracts.X.evidence 补全
    contracts = state.setdefault("stage_contracts", {})
    for stage_name, contract in contracts.items():
        if not isinstance(contract, dict):
            continue
        if "evidence" not in contract:
            contract["evidence"] = {}
            changes.append(f"stage_contracts.{stage_name}.evidence={{}}")

        # ship stage 从 ship.* 字段反向推断 evidence
        if stage_name == "ship":
            ship = state.get("ship", {})
            ev = contract["evidence"]
            if ship.get("phase") and "ship_phase" not in ev:
                ev["ship_phase"] = ship["phase"]
                changes.append(f"stage_contracts.ship.evidence.ship_phase={ship['phase']}")
            if ship.get("merge_commit_hash") and "merge_commit_hash" not in ev:
                ev["merge_commit_hash"] = ship["merge_commit_hash"]
                changes.append(f"stage_contracts.ship.evidence.merge_commit_hash={ship['merge_commit_hash'][:8]}")

        # pm_acceptance 从 pm_acceptance.decision 字段(v7)推断
        if stage_name == "pm_acceptance":
            pm_data = state.get("pm_acceptance", {})
            ev = contract["evidence"]
            if pm_data.get("decision") and "decision" not in ev:
                ev["decision"] = pm_data["decision"]
                ev["note"] = pm_data.get("decision_note", "")
                changes.append(f"stage_contracts.pm_acceptance.evidence.decision={pm_data['decision']}")

    # 4. 备份 + 写新文件
    if not args.dry_run:
        backup_path = state_file.with_suffix(".json.v7-backup")
        try:
            shutil.copy(state_file, backup_path)
        except OSError as e:
            emit_json({
                "verdict": "FAIL",
                "command": "migrate-v7-to-v8",
                "error": f"备份失败: {e}",
            }, exit_code=1)

        state["updated_at"] = now_iso()
        state["updated_by"] = "migrate-v7-to-v8"
        state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    # 5. 加 concerns
    state.setdefault("concerns", []).append(
        f"{now_iso()} INFO migrated v7 → v8 · {len(changes)} fields changed"
    )

    emit_json({
        "verdict": "PASS",
        "command": "migrate-v7-to-v8",
        "feature": str(feature_path),
        "dry_run": args.dry_run,
        "schema_version_before": "v7",
        "schema_version_after": V8_SCHEMA_VERSION,
        "changes": changes,
        "backup_path": (
            str(state_file.with_suffix(".json.v7-backup"))
            if not args.dry_run else "(dry-run · not created)"
        ),
    })


def cmd_migrate_v8_stage_rename(args: argparse.Namespace) -> None:
    """v8.0 → v8.1: stage 改名 goal_plan→goal · panorama_design→planning。"""
    feature_path = Path(args.feature).resolve()
    state_file = feature_path / "state.json"
    if not state_file.exists():
        emit_json({
            "verdict": "FAIL",
            "command": "migrate-v8-stage-rename",
            "error": f"state.json 不存在: {state_file}",
        }, exit_code=1)

    state = json.loads(state_file.read_text(encoding="utf-8"))
    if state.get("schema_version") == V8_1_SCHEMA_VERSION:
        emit_json({
            "verdict": "SKIP",
            "command": "migrate-v8-stage-rename",
            "reason": f"已是 {V8_1_SCHEMA_VERSION}",
        })

    changes = []

    # 1. current_stage
    cur = state.get("current_stage")
    if cur in STAGE_RENAMES:
        state["current_stage"] = STAGE_RENAMES[cur]
        changes.append(f"current_stage: {cur} → {STAGE_RENAMES[cur]}")

    # 2. completed_stages[]
    completed = state.get("completed_stages", [])
    new_completed = [STAGE_RENAMES.get(s, s) for s in completed]
    if new_completed != completed:
        state["completed_stages"] = new_completed
        changes.append(f"completed_stages: {completed} → {new_completed}")

    # 3. legal_next_stages[]
    legal = state.get("legal_next_stages", [])
    new_legal = [STAGE_RENAMES.get(s, s) for s in legal]
    if new_legal != legal:
        state["legal_next_stages"] = new_legal
        changes.append(f"legal_next_stages: {legal} → {new_legal}")

    # 4. stage_contracts dict keys
    contracts = state.get("stage_contracts", {})
    for old, new in STAGE_RENAMES.items():
        if old in contracts:
            contracts[new] = contracts.pop(old)
            changes.append(f"stage_contracts.{old} → stage_contracts.{new}")

    # 5. stage_review_roles dict keys(若存在)
    review_roles = state.get("stage_review_roles", {})
    for old, new in STAGE_RENAMES.items():
        if old in review_roles:
            review_roles[new] = review_roles.pop(old)
            changes.append(f"stage_review_roles.{old} → stage_review_roles.{new}")

    state["schema_version"] = V8_1_SCHEMA_VERSION

    if not args.dry_run:
        backup_path = state_file.with_suffix(".json.v8-0-backup")
        try:
            shutil.copy(state_file, backup_path)
        except OSError as e:
            emit_json({
                "verdict": "FAIL",
                "command": "migrate-v8-stage-rename",
                "error": f"备份失败: {e}",
            }, exit_code=1)

        state["updated_at"] = now_iso()
        state["updated_by"] = "migrate-v8-stage-rename"
        state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    state.setdefault("concerns", []).append(
        f"{now_iso()} INFO migrated v8.0 → v8.1 · {len(changes)} fields changed"
    )

    emit_json({
        "verdict": "PASS",
        "command": "migrate-v8-stage-rename",
        "feature": str(feature_path),
        "dry_run": args.dry_run,
        "schema_version_before": "v8.0",
        "schema_version_after": V8_1_SCHEMA_VERSION,
        "changes": changes,
        "backup_path": (
            str(state_file.with_suffix(".json.v8-0-backup"))
            if not args.dry_run else "(dry-run · not created)"
        ),
    })


def register_v8_migrate_subparser(sub) -> None:
    """在 state.py argparse subparsers 上注册 migrate 命令。"""
    mp = sub.add_parser(
        "migrate-v7-to-v8",
        help="[v8] 一次性迁移老 state.json 从 v7 → v8 schema",
    )
    mp.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    mp.add_argument("--dry-run", action="store_true",
                    help="只输出变更预览 · 不动文件")
    mp.set_defaults(func=cmd_migrate_v7_to_v8)

    mp2 = sub.add_parser(
        "migrate-v8-stage-rename",
        help="[v8.1] stage 改名 goal_plan→goal / panorama_design→planning",
    )
    mp2.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    mp2.add_argument("--dry-run", action="store_true",
                     help="只输出变更预览 · 不动文件")
    mp2.set_defaults(func=cmd_migrate_v8_stage_rename)
