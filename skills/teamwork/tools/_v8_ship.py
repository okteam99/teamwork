"""
_v8_ship.py — Teamwork v8.0 ship-phase 子动作实现。

替代 v7 的 5 个独立 ship-* 命令(ship-sanitize / ship-push / ship-confirm-merged /
ship-cleanup / ship-closed),改为统一的 `ship-phase --action <name>`。

action 枚举:
- sanitize:           净化 commit 记录(不改 phase)
- push:               null/closed_unmerged → pushed · 含 git-host + MR 创建
- confirm-merged:     pushed → merged · 含主工作区拦截 + finalize-push 状态
- cleanup:            worktree 清理 · 必须 phase=merged
- close-unmerged:     pushed → closed_unmerged 或 abandoned

设计哲学见 docs/archive/v8-redesign/00-MANIFESTO.md(rationale · 历史归档)。
ship-phase schema 现行权威 = state.py --help + _v8_stage_specs.py SHIP_SPEC
(01-COMMAND-SCHEMA.md B11 为 v8.0 归档快照 · 勿当现行)。
v8.W2 实现 · 取代 v7 ship-*(W3 减负时物理删除 v7 ship-* 子命令)。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from _v8_engine import (
    emit_json,
    git_head,
    load_state,
    now_iso,
    require_user_confirmed,
    save_state,
    write_review_log_entry,
)


# ─── 常量 ──────────────────────────────────────────────────────────────


SHIP_ACTIONS = ("sanitize", "push", "confirm-merged", "cleanup", "close-unmerged")

# v8.70:main-sync 净化策略(ship 后主工作区 user-dirty 决策的执行选项)
MAIN_SYNC_STRATEGIES = ("commit-push", "stash-pull", "skip")

SHIP_PHASE_ENUM = (None, "pushed", "merged", "closed_unmerged")
SHIP_SHIPPED_ENUM = (None, "pushed", "merged", "closed_unmerged", "abandoned", "failed")
SHIP_GIT_HOSTS = ("github", "gitlab", "gitlab-self-hosted", "gitee", "bitbucket", "unknown")
SHIP_MR_METHODS = ("cli-gh", "cli-glab", "url-fallback", "unknown-platform")
SHIP_DETECTION_METHODS = ("branch-contains", "user-reported")
SHIP_FINALIZE_PUSH_REASONS = ("conflict", "protect-rule", "network", "other")
SHIP_CLEANUP_ENUM = ("cleaned", "deferred", "n_a")

# v8.81:ship1 知识沉淀闸门 · 知识层 6 项(随 feature MR graduate · 详 stages/ship-stage.md §13)
# 「描述代码的文档随代码进 MR」· 每项 sanitize 前必记一条决策(updated / none)· 强制走一遍。
DISTILL_KEYS = ("knowledge", "adr", "reg", "retro", "architecture", "db_schema")

# v8.82:ship2 归档本体 · 过程层 feature 目录交付后 zip 进 features/_archive/ · 原目录从
# merge_target 删(防 AI 检索过时 feature 信息 · 代码是唯一真相)· 随收尾 MR 一起合(MR 合入后)。
# archive_on_ship(localconfig · 默认 true)· false → 退回 v8.80(收尾 MR 只同步终态 state.json)。
ARCHIVE_DIR_NAME = "_archive"


# ─── 主工作区拦截(沿用 v7 P0-156 治本) ─────────────────────────────


def _enforce_main_worktree(action_name: str) -> None:
    """ship-phase --action {confirm-merged, cleanup} 必须在主工作区跑。

    治本 v7.3.10+P0-156:state.json 在 linked worktree 被删丢失。
    Bypass:TEAMWORK_BYPASS_MAIN_WORKTREE=1(调试/迁移场景)
    """
    if os.environ.get("TEAMWORK_BYPASS_MAIN_WORKTREE") == "1":
        return

    # 测试 hook
    forced = os.environ.get("TEAMWORK_FORCE_LINKED_WORKTREE")
    if forced:
        emit_json({
            "verdict": "FAIL",
            "error": f"ship-phase --action {action_name} 必须在主工作区运行 · 当前 cwd 在 linked worktree",
            "cwd": os.getcwd(),
            "linked_worktree_git_dir": forced,
            "hint": (
                "cd 到 merge_target 主工作区(git clone 原仓库位置 · 不是 git worktree add 的 linked 路径)· "
                "git checkout {merge_target} + git pull --ff-only · 再跑此命令"
            ),
            "rule": "v7.3.10+P0-156 物化拦截 · v8 沿用 · 治本 ADMIN-F013 case",
            "bypass": "调试场景设 TEAMWORK_BYPASS_MAIN_WORKTREE=1",
        }, exit_code=1)
        return

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return  # 不在 git 仓库 · 跳过
        git_dir = result.stdout.strip()
        if "/worktrees/" in git_dir:
            emit_json({
                "verdict": "FAIL",
                "error": f"ship-phase --action {action_name} 必须在主工作区运行 · 当前 cwd 在 linked worktree",
                "cwd": os.getcwd(),
                "linked_worktree_git_dir": git_dir,
                "hint": (
                    "cd 到主工作区(原 git clone 位置)· "
                    "git checkout {merge_target} + git pull --ff-only · 再跑此命令"
                ),
                "rule": "v7.3.10+P0-156 物化拦截 · v8 沿用",
                "bypass": "调试场景设 TEAMWORK_BYPASS_MAIN_WORKTREE=1",
            }, exit_code=1)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return  # git 不可用 · 跳过


# ─── 工具函数 ──────────────────────────────────────────────────────────


def _enum_err(arg_name: str, got: Any, valid: tuple) -> dict:
    return {
        "verdict": "FAIL",
        "error": f"{arg_name}={got!r} 非法",
        "valid_values": list(valid),
    }


def _phase_err(current: Any, target: str, allowed_msg: str) -> dict:
    return {
        "verdict": "FAIL",
        "error": f"ship.phase 非法转移: {current!r} → {target!r}",
        "hint": allowed_msg,
    }


def _require_ship_stage(state: dict, action: str) -> None:
    """current_stage 必须是 ship · 否则 FAIL"""
    if state.get("current_stage") != "ship":
        emit_json({
            "verdict": "FAIL",
            "error": f"current_stage={state.get('current_stage')!r} · 不是 ship",
            "hint": "先跑 state.py ship-start · 进 ship stage",
            "action": action,
        }, exit_code=1)


# ─── action 1:sanitize ────────────────────────────────────────────


def _check_migration_schema(feature_dir: str, merge_target: str, distill: dict) -> None:
    """v8.81:迁移↔schema 文档一致性硬校验(R0)。

    feature diff 含 migration 文件 + distill.db_schema 声明「无变更」+ database-schema.md 未更
    → 矛盾 → BLOCK。best-effort:无法 diff(无 merge_target ref 等)则跳过。
    """
    if not merge_target:
        return
    db = (distill.get("db_schema") or "").lower()
    declares_no_db = any(k in db for k in
                         ("no-change", "no_db", "no-db", "无变更", "无库", "无 db", "n/a", "none"))
    if not declares_no_db:
        return  # 已声明有 schema 变更 → 不矛盾 · 放行
    dr = _git(["diff", "--name-only", f"origin/{merge_target}...HEAD"], cwd=feature_dir)
    if dr.returncode != 0:
        dr = _git(["diff", "--name-only", f"{merge_target}...HEAD"], cwd=feature_dir)
    if dr.returncode != 0:
        return  # 无法判定 → 跳过(best-effort)
    files = [f for f in dr.stdout.splitlines() if f.strip()]
    mig = [f for f in files if "migration" in f.lower()]
    touched_schema = any("database-schema.md" in f for f in files)
    if mig and not touched_schema:
        emit_json({
            "verdict": "FAIL", "stage": "ship", "action": "sanitize",
            "error": ("distill.db_schema 声明无 DB 变更 · 但 feature diff 含 migration 文件 · "
                      "且 docs/architecture/database-schema.md 未更新 —— 矛盾"),
            "hint": ("迁移改了表结构 → 必须同步 docs/architecture/database-schema.md"
                     "(表/字段/ORM 引用点)· 并把 --distill 的 db_schema 改为 'updated <表>'。"
                     "确属无需更新(纯数据迁移 backfill)→ db_schema 写明 'data-only migration'。"),
            "migration_files": mig[:10],
            "rule": "v8.81 迁移↔schema 一致性硬校验(R0)· 治本 schema 文档 drift",
        }, exit_code=1)


def _validate_distill(args: argparse.Namespace, state: dict) -> dict:
    """v8.81:校验 ship1 知识沉淀 --distill(知识层 6 项决策)· 缺/非法 → BLOCK · 返回记录。

    R0:强制 AI 逐项走一遍知识层(每项记 promoted/none · 证明已沉淀)· 质量留 AI ·
    「走没走」进脚本。+ 迁移↔schema 机械校验。详 stages/ship-stage.md §13。
    """
    raw = getattr(args, "distill", None)
    if not raw:
        emit_json({
            "verdict": "FAIL", "stage": "ship", "action": "sanitize",
            "error": "缺 --distill(ship1 知识沉淀闸门 · v8.81)",
            "hint": ("ship 前必把「描述代码」的知识 graduate 到知识层(随本次 feature MR)· "
                     "逐项决策 --distill '"
                     + json.dumps({k: "..." for k in DISTILL_KEYS}, ensure_ascii=False)
                     + "'(每项填 'updated/promoted <what>' 或 'none'/'n/a' · 无则显式 none · "
                     "详 ship-stage.md §13)"),
            "distill_keys": list(DISTILL_KEYS),
        }, exit_code=1)
    try:
        d = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        emit_json({"verdict": "FAIL", "stage": "ship", "action": "sanitize",
                   "error": f"--distill 不是合法 JSON:{e}"}, exit_code=1)
    if not isinstance(d, dict):
        emit_json({"verdict": "FAIL", "stage": "ship", "action": "sanitize",
                   "error": "--distill 必须是 JSON 对象(知识层 6 项决策)"}, exit_code=1)
    missing = [k for k in DISTILL_KEYS
               if not (isinstance(d.get(k), str) and d[k].strip())]
    if missing:
        emit_json({
            "verdict": "FAIL", "stage": "ship", "action": "sanitize",
            "error": f"--distill 缺项 / 空值:{missing}",
            "hint": "6 项全填(无则 'none'/'n/a' · 证明已逐项判断):" + " / ".join(DISTILL_KEYS),
        }, exit_code=1)
    _check_migration_schema(args.feature, state.get("merge_target") or "", d)
    rec = {k: d[k].strip() for k in DISTILL_KEYS}
    rec["distilled_at"] = now_iso()
    return rec


def _handle_ship_sanitize(state: dict, args: argparse.Namespace) -> dict:
    """Step 1:净化 commit 记录 + ship1 知识沉淀闸门(v8.81)· 不改 ship.phase。"""
    ship = state.setdefault("ship", {})
    ship.setdefault("started_at", now_iso())

    # v8.81:ship1 知识沉淀硬闸门 —— 知识层 6 项随 feature MR graduate(缺/非法/迁移↔schema 矛盾 → BLOCK)
    ship["distill"] = _validate_distill(args, state)

    log = ship.setdefault("sanitize_log", {
        "residual_commits": [],
        "cleaned_files": [],
        "suspicious_files": [],
    })

    if args.residual_commits:
        try:
            log["residual_commits"] = json.loads(args.residual_commits)
        except json.JSONDecodeError as e:
            emit_json({
                "verdict": "FAIL",
                "error": f"--residual-commits 不是合法 JSON: {e}",
            }, exit_code=1)

    if args.cleaned_files:
        log["cleaned_files"] = [s.strip() for s in args.cleaned_files.split(",") if s.strip()]

    if args.suspicious_files:
        try:
            log["suspicious_files"] = json.loads(args.suspicious_files)
        except json.JSONDecodeError as e:
            emit_json({
                "verdict": "FAIL",
                "error": f"--suspicious-files 不是合法 JSON: {e}",
            }, exit_code=1)

    warnings = []
    if log["residual_commits"]:
        warnings.append("sanitize_log.residual_commits 非空 · PMO 完成报告必须高亮(前序 Stage 漏 commit)")
    if log["suspicious_files"]:
        warnings.append("sanitize_log.suspicious_files 非空 · PMO 完成报告必须列出灰名单 · 不自动处理")

    return {
        "verdict": "PASS",
        "stage": "ship",
        "action": "sanitize",
        "phase": ship.get("phase"),  # 不变
        "sanitize_log": log,
        "distill": ship["distill"],  # v8.81:知识层 6 项沉淀决策(随 feature MR graduate)
        "warnings": warnings,
        "next_action_brief": (
            "✅ 净化 + 知识沉淀(distill)完成。🔴 确保 distill 涉及的知识层文件"
            "(KNOWLEDGE/ADR/REG/retro/ARCHITECTURE/database-schema)已在 worktree commit · "
            "随本次 feature MR 一起合。下一步:"
            "state.py ship-phase --action push --feature <path> "
            "--feature-head-commit <hash> --git-host <host> "
            "--mr-creation-method <method> --mr-url/mr-create-url <url>"
        ),
    }


# ─── v8.37 · CLI 可用性检测(治本 SVC-CORE-B007 case · url-fallback 退化拦截)──

# git_host → CLI name 映射(用于"已装 CLI 时禁止退化"校验)
SHIP_GIT_HOST_TO_CLI = {
    "github":             "gh",
    "gitlab":             "glab",
    "gitlab-self-hosted": "glab",
    # gitee / bitbucket / unknown:无主流 CLI · 退化合理 · 不强校
}


def _check_cli_available_for_host(git_host: str) -> dict:
    """v8.37:检测 git_host 对应的 MR CLI 是否可用(治本 SVC-CORE-B007 case)。

    检测顺序:
      ① 查表 git_host → CLI name(github→gh / gitlab*→glab) · 不在表内 → no_cli_for_host
      ② which <cli> → 没装 → not_installed
      ③ <cli> auth status → 未登录 / 失败 → not_authenticated

    返回 {available, cli_name, reason}:
      - available=True:CLI 装好 + 已认证 · url-fallback 退化将被拦截
      - available=False + reason:不可用原因(供 hint 透明)
    """
    cli_name = SHIP_GIT_HOST_TO_CLI.get(git_host)
    if not cli_name:
        return {"available": False, "cli_name": None,
                "reason": f"no_cli_mapping_for_host({git_host})"}

    # which <cli>
    try:
        w = subprocess.run(["which", cli_name], capture_output=True, text=True, timeout=5)
        if w.returncode != 0:
            return {"available": False, "cli_name": cli_name,
                    "reason": f"{cli_name}_not_installed",
                    "hint_install": (
                        f"brew install {cli_name}" if cli_name in ("gh", "glab")
                        else f"安装 {cli_name} CLI"
                    )}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {"available": False, "cli_name": cli_name,
                "reason": "which_command_unavailable"}

    # <cli> auth status
    try:
        a = subprocess.run([cli_name, "auth", "status"],
                            capture_output=True, text=True, timeout=10)
        if a.returncode != 0:
            return {"available": False, "cli_name": cli_name,
                    "reason": f"{cli_name}_not_authenticated",
                    "auth_stderr_tail": (a.stderr or a.stdout or "").strip()[-200:],
                    "hint_auth": f"跑 `{cli_name} auth login` 完成认证 · 再重试 push"}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {"available": False, "cli_name": cli_name,
                "reason": f"{cli_name}_auth_check_failed"}

    return {"available": True, "cli_name": cli_name, "reason": "installed_and_authenticated"}


# ─── action 2:push ────────────────────────────────────────────────


def _handle_ship_push(state: dict, args: argparse.Namespace) -> dict:
    """Step 2-3:phase null/closed_unmerged → pushed · 含 git-host + MR 创建。"""
    ship = state.setdefault("ship", {})
    ship.setdefault("started_at", now_iso())

    cur_phase = ship.get("phase")
    if cur_phase not in (None, "closed_unmerged"):
        emit_json(
            _phase_err(cur_phase, "pushed", "push 仅允许 null → pushed 或 closed_unmerged → pushed"),
            exit_code=1,
        )

    # enum 校验
    if args.git_host not in SHIP_GIT_HOSTS:
        emit_json(_enum_err("--git-host", args.git_host, SHIP_GIT_HOSTS), exit_code=1)
    if args.mr_creation_method not in SHIP_MR_METHODS:
        emit_json(_enum_err("--mr-creation-method", args.mr_creation_method, SHIP_MR_METHODS), exit_code=1)

    # mr-url / mr-create-url 二选一(治本 P0-113 CLI-first)
    if not args.mr_url and not args.mr_create_url:
        emit_json({
            "verdict": "FAIL",
            "error": "--mr-url 与 --mr-create-url 必至少一个非空",
            "hint": "CLI 实创建用 --mr-url · 兜底 URL 用 --mr-create-url",
        }, exit_code=1)

    if args.mr_creation_method.startswith("cli-") and not args.mr_url:
        emit_json({
            "verdict": "FAIL",
            "error": f"mr_creation_method={args.mr_creation_method} 必带 --mr-url(CLI 实创建)",
            "hint": "跑 gh/glab CLI 创 MR 拿真实 URL · 或用 url-fallback method",
        }, exit_code=1)

    if args.mr_creation_method in ("url-fallback", "unknown-platform") and not args.mr_create_url:
        emit_json({
            "verdict": "FAIL",
            "error": f"mr_creation_method={args.mr_creation_method} 必带 --mr-create-url(兜底链接)",
        }, exit_code=1)

    # ── v8.37 url-fallback 退化拦截(治本 SVC-CORE-B007 case)──
    # AI 把 git push 输出的 MR 创建表单 URL 直接当 mr_create_url + url-fallback method ·
    # 但 glab 已装且认证 OK 应该跑 `glab mr create` 拿真实 MR URL(规范 P0-113 CLI-first)·
    # 这里物化拦截:CLI 可用且 git_host 匹配 → BLOCK · 除非显式 --accept-cli-unavailable
    # + --reason + --user-confirmed(走 bypass log + concerns WARN)
    fallback_bypass_warning = None
    if args.mr_creation_method == "url-fallback":
        cli_check = _check_cli_available_for_host(args.git_host)
        if cli_check["available"]:
            cli = cli_check["cli_name"]
            accept_unavail = getattr(args, "accept_cli_unavailable", False)
            if not accept_unavail:
                emit_json({
                    "verdict": "FAIL",
                    "error": (
                        f"--mr-creation-method=url-fallback 但 {cli} CLI 已装+已认证 · "
                        f"违 P0-113 CLI-first(治本 SVC-CORE-B007 case · AI 退化用 git push hint URL)"
                    ),
                    "cli_check": cli_check,
                    "hint": (
                        f"二选一:\n"
                        f"  ① [推荐] 跑 `{cli} mr create` (或 `{cli} pr create`) 拿真实 MR URL · "
                        f"然后 --mr-creation-method cli-{cli} --mr-url <真 URL>\n"
                        f"  ② 显式承认 CLI 不可用(网络隔离 / token 范围不够 / 强制内部流程):\n"
                        f"     加 --accept-cli-unavailable --reason '<具体原因>' --user-confirmed\n"
                        f"     (走 bypass log + concerns WARN 留痕 · retro 复盘)"
                    ),
                    "spec": ("stages/ship-stage.md L17/L109 + P0-113 CLI-first"
                             " · v8.37 物化拦截 · 治本 SVC-CORE-B007"),
                }, exit_code=1)

            # bypass 路径:--accept-cli-unavailable 通过 · 必带 reason + user-confirmed
            require_user_confirmed(args, yolo=state.get("yolo", False))  # 强制 --user-confirmed(yolo 例外)
            reason = (getattr(args, "reason", "") or "").strip()
            if not reason:
                emit_json({
                    "verdict": "FAIL",
                    "error": ("--accept-cli-unavailable 必带 --reason '<原因>' "
                              "(写 concerns + bypass log · 退化必留痕)"),
                    "hint": "示例 --reason '网络隔离不能访问 GitLab API' / 'glab token 无 mr_create scope'",
                }, exit_code=1)

            fallback_bypass_warning = (
                f"{now_iso()} WARN ship-push url-fallback bypass: "
                f"{cli} 已装+已认证 但 --accept-cli-unavailable={reason!r} · "
                f"(v8.37 治本 SVC-CORE-B007 case · CLI 可用时退化必显式确认)"
            )
            concerns = state.setdefault("concerns", [])
            concerns.append(fallback_bypass_warning)
            # 写 bypass log(audit 留痕)
            bypass_log = ship.setdefault("bypass_log", [])
            bypass_log.append({
                "at": now_iso(),
                "action": "push",
                "type": "url_fallback_when_cli_available",
                "cli_name": cli,
                "cli_check": cli_check,
                "reason": reason,
            })

    if not args.feature_head_commit:
        emit_json({
            "verdict": "FAIL",
            "error": "--feature-head-commit 必传(push 后的 commit hash)",
        }, exit_code=1)

    # 更新 ship 字段
    ship["phase"] = "pushed"
    ship["shipped"] = "pushed"
    ship["feature_head_commit"] = args.feature_head_commit
    ship["git_host"] = args.git_host
    ship["mr_creation_method"] = args.mr_creation_method
    ship["mr_url"] = args.mr_url
    ship["mr_create_url"] = args.mr_create_url
    ship["feature_pushed_at"] = args.feature_pushed_at or now_iso()

    return {
        "verdict": "PASS",
        "stage": "ship",
        "action": "push",
        "transition": f"{cur_phase} → pushed",
        "phase": "pushed",
        "mr_url": ship["mr_url"],
        "mr_create_url": ship["mr_create_url"],
        "next_action_brief": (
            "✅ Push + MR 创建完成。\n\n"
            "⏸️ 等用户在平台合并 MR。\n\n"
            "用户合并后:\n"
            "1. cd 到主工作区(非 linked worktree · 治本 P0-156)\n"
            "2. git fetch origin <merge_target>; git pull --ff-only\n"
            "3. state.py ship-phase --action confirm-merged "
            "--feature <path> --merge-commit-hash <hash> "
            "--merge-detection-method branch-contains\n\n"
            "用户关闭未合并:\n"
            "state.py ship-phase --action close-unmerged --feature <path>"
        ),
        # v8.37:url-fallback 退化 bypass 的 WARN(治本 SVC-CORE-B007)
        **({"fallback_bypass_warning": fallback_bypass_warning}
            if fallback_bypass_warning else {}),
    }


# ─── action 3:confirm-merged ────────────────────────────────────


def _handle_ship_confirm_merged(state: dict, args: argparse.Namespace) -> dict:
    """Step 4-8:phase pushed → merged · 含主工作区拦截。"""
    _enforce_main_worktree("confirm-merged")

    ship = state.setdefault("ship", {})

    if ship.get("phase") != "pushed":
        emit_json(
            _phase_err(ship.get("phase"), "merged", "confirm-merged 仅允许 pushed → merged"),
            exit_code=1,
        )

    if not args.merge_commit_hash:
        emit_json({"verdict": "FAIL", "error": "--merge-commit-hash 必传"}, exit_code=1)

    if args.merge_detection_method not in SHIP_DETECTION_METHODS:
        emit_json(_enum_err("--merge-detection-method", args.merge_detection_method, SHIP_DETECTION_METHODS), exit_code=1)

    ship["phase"] = "merged"
    ship["shipped"] = "merged"
    ship["merge_commit_hash"] = args.merge_commit_hash
    ship["merge_detection_method"] = args.merge_detection_method
    ship["mr_merged_at"] = args.mr_merged_at or now_iso()

    warnings = []

    # finalize-push 状态(可选 · push merge_target 同步 state.json)
    if args.merge_target_pushed_at:
        ship["merge_target_pushed_at"] = args.merge_target_pushed_at
        ship["merge_target_push_failed"] = False
        ship["merge_target_push_failed_reason"] = None
    elif args.merge_target_push_failed:
        if not args.failed_reason or args.failed_reason not in SHIP_FINALIZE_PUSH_REASONS:
            emit_json(
                _enum_err("--failed-reason", args.failed_reason, SHIP_FINALIZE_PUSH_REASONS),
                exit_code=1,
            )
        ship["merge_target_pushed_at"] = None
        ship["merge_target_push_failed"] = True
        ship["merge_target_push_failed_reason"] = args.failed_reason
        # 自动追加 concerns
        state.setdefault("concerns", []).append(
            f"{now_iso()} WARN ship-finalize-push 失败({args.failed_reason})→ "
            f"降级到 feature 分支 push · merge_target 上 state.json 仍为 phase=pushed · "
            f"用户可手动 cherry-pick 同步状态"
        )

    if args.merge_detection_method == "user-reported":
        warnings.append(
            "merge_detection_method=user-reported · 用户自报 · 自动 git 校验未通过 · concerns 已加 INFO"
        )
        state.setdefault("concerns", []).append(
            f"{now_iso()} INFO ship-confirm-merged: user-reported merge_commit={args.merge_commit_hash}"
        )

    return {
        "verdict": "PASS",
        "stage": "ship",
        "action": "confirm-merged",
        "transition": "pushed → merged",
        "phase": "merged",
        "merge_commit_hash": ship["merge_commit_hash"],
        "warnings": warnings,
        "next_action_brief": (
            "✅ 合入已确认。\n\n"
            "🔴 state.json finalize 直推(合法例外 · 详 ship-stage.md §11):\n"
            "  - merge_target 上 state.json 仍是 Phase 1 phase=pushed · 需 push 同步\n"
            "  - 走直推 · **不创 MR**(单文件 + 仅状态字段 + 零业务影响)\n"
            "  - 同类例外:Bug 流程 BUG-REPORT.md frontmatter 直推\n"
            "  - 禁止:业务文件 / state.json 业务字段 / BUG-REPORT.md 正文 · 这些必走 MR\n\n"
            "下一步:\n"
            "0. 二次验证合入(防 user-reported 误报 / 时间间隔后状态变化):\n"
            "   git fetch origin <merge-target>\n"
            "   git branch -r --contains "
            f"{ship['merge_commit_hash']} | grep origin/<merge-target>   "
            "# 命中 = 真合入 · 空 = 未合入(BLOCKED · 排查 MR 状态)\n"
            "1. git push origin <merge-target>(state.json finalize 直推)\n"
            "   失败:--merge-target-push-failed --failed-reason {conflict|protect-rule|network|other}\n"
            "2. git worktree remove <worktree-path>(如有 worktree)\n"
            "3. git branch -d <feature-branch>\n"
            "4. state.py ship-phase --action cleanup "
            "--feature <path> --status cleaned\n"
            "5. state.py ship-complete --feature <path> --auto-commit <hash>"
        ),
    }


# ─── action 4:cleanup ───────────────────────────────────────────


def _handle_ship_cleanup(state: dict, args: argparse.Namespace) -> dict:
    """Step 9:worktree 清理状态 · cleaned 必须 phase=merged(治本 P0-124)。"""
    _enforce_main_worktree("cleanup")

    ship = state.setdefault("ship", {})

    if args.status not in SHIP_CLEANUP_ENUM:
        emit_json(_enum_err("--status", args.status, SHIP_CLEANUP_ENUM), exit_code=1)

    # 🔴 hard gate(治本 P0-124):cleanup --status cleaned 时 phase 必须 merged
    if args.status == "cleaned":
        if ship.get("phase") != "merged" or ship.get("shipped") != "merged":
            emit_json({
                "verdict": "BLOCKED",
                "error": "ship-phase --action cleanup --status cleaned 被拒:合并未确认(治本 P0-124)",
                "current_ship_phase": ship.get("phase"),
                "current_ship_shipped": ship.get("shipped"),
                "hint": (
                    "先跑 ship-phase --action confirm-merged · "
                    "或 worktree=off 时用 --status n_a"
                ),
            }, exit_code=1)
        if not ship.get("merge_commit_hash"):
            emit_json({
                "verdict": "BLOCKED",
                "error": "ship-phase --action cleanup 被拒:merge_commit_hash 缺失(治本 P0-124)",
            }, exit_code=1)

    ship["worktree_cleanup"] = args.status

    if args.status == "cleaned":
        ship["completed_at"] = now_iso()

    next_brief = (
        "✅ 清理完成。下一步:state.py ship-complete --feature <path> --auto-commit <hash>"
        if args.status in ("cleaned", "n_a")
        else "⏸️ 待 worktree 清理后再次 ship-phase --action cleanup --status cleaned"
    )

    return {
        "verdict": "PASS",
        "stage": "ship",
        "action": "cleanup",
        "phase": ship.get("phase"),
        "worktree_cleanup": args.status,
        "next_action_brief": next_brief,
    }


# ─── action 5:close-unmerged ──────────────────────────────────


def _handle_ship_close_unmerged(state: dict, args: argparse.Namespace) -> dict:
    """异常段:MR 被关闭未合并 → phase=closed_unmerged 或 abandoned。"""
    ship = state.setdefault("ship", {})

    cur_phase = ship.get("phase")
    if cur_phase not in ("pushed", None):
        emit_json(
            _phase_err(cur_phase, "closed_unmerged", "close-unmerged 仅允许 null/pushed → closed_unmerged"),
            exit_code=1,
        )

    if args.abandon:
        ship["phase"] = "closed_unmerged"
        ship["shipped"] = "abandoned"
    else:
        ship["phase"] = "closed_unmerged"
        ship["shipped"] = "closed_unmerged"

    ship["closed_at"] = now_iso()

    if args.reason:
        state.setdefault("concerns", []).append(
            f"{now_iso()} INFO ship-close-unmerged: {args.reason}"
        )

    return {
        "verdict": "PASS",
        "stage": "ship",
        "action": "close-unmerged",
        "transition": f"{cur_phase} → closed_unmerged",
        "phase": "closed_unmerged",
        "shipped": ship["shipped"],
        "next_action_brief": (
            "❌ MR 已关闭未合并。\n\n"
            "Feature 终止路径:\n"
            "- 放弃:跑 ship-complete --bypass --reason ... --user-confirmed(进 abandoned 终态)\n"
            "- 重开:跑 ship-phase --action push(重 push 重 MR · null → pushed 反向转移)"
        ),
    }


# ─── ship-phase 主入口 ─────────────────────────────────────────


def cmd_ship_phase(args: argparse.Namespace) -> None:
    """ship-phase --action <name> 主入口分发。"""
    feature_path = args.feature
    path, state = load_state(feature_path)

    _require_ship_stage(state, args.action)

    if args.action not in SHIP_ACTIONS:
        emit_json(_enum_err("--action", args.action, SHIP_ACTIONS), exit_code=1)

    handlers = {
        "sanitize": _handle_ship_sanitize,
        "push": _handle_ship_push,
        "confirm-merged": _handle_ship_confirm_merged,
        "cleanup": _handle_ship_cleanup,
        "close-unmerged": _handle_ship_close_unmerged,
    }

    result = handlers[args.action](state, args)
    save_state(path, state)
    emit_json(result)


# ─── ship-finalize:Phase 2 全自动编排 ─────────────────────────────
#
# 治本:Phase 2(confirm-merged → cleanup → ship-complete → finalize 直推 →
# worktree 清理 → 主工作区 fetch)原本是 6+ 条命令 + 1 次 cd · PMO 手工编排 ·
# 易漏步 / 漏 cd / 漏 finalize 直推。ship-finalize 把可枚举的 7 步收进脚本 ·
# 一条命令跑完 · 仅在「MR 未合并」这类不可枚举判断点 FAIL 让 AI 干预。
#
# 7 步:
#   1. verify-merge    git fetch + merge-base 验证 feature_head 已进 merge_target
#   2. confirm-merged  ship.phase pushed → merged
#   3. cleanup         ship.worktree_cleanup = cleaned / n_a(状态字段)
#   4. ship-complete   current_stage → completed
#   5. finalize-deliver(v8.80 去直推)state.py 暂存收尾 commit 到 ship-finalize/<id> 分支 →
#      交接 AI 用 gh/glab 创 MR + 自动合并 → 重跑 ancestor-check 验证已合(未合 emit PENDING)
#   6. worktree-remove 物理删 feature worktree(收尾 MR 已合 · state.json 在 merge_target · 不丢)
#   7. main-sync       主工作区 git fetch + 安全 pull --ff-only(让本地跟上 ship 结果)
#
# 可重入:每步先查 state · 已完成则跳过(skipped_steps)。
# 必须在主工作区跑(step 6 不能删自身所在 worktree · 沿用 P0-156)。


SHIP_FINALIZE_STEPS = (
    # v8.16:state-sync 是 step 0(治本 SVC-CORE-B006 case)
    # ① fetch+ff-pull merge_target(主工作区拉下 MR 合并后的 features dir)
    # ② 检测主工作区 state.json:不存在/缺 ship.feature_head_commit → 从 worktree 同步完整态
    # 理由:Phase 1 sanitize/push 写 state.json 但不 commit · push 到 feature 的 commit
    # 不含完整 state.json · merge 后主工作区拉下的是合并前快照 · verify-merge 会 FAIL
    "state-sync",
    "verify-merge", "confirm-merged", "cleanup",
    "ship-complete", "finalize-deliver", "worktree-remove", "main-sync",
)


class _GitResult:
    """轻量 CompletedProcess 替身 · 把 timeout / git-missing 归一为 returncode。"""

    __slots__ = ("returncode", "stdout", "stderr")

    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _git(git_args: list, cwd: Optional[str] = None,
         timeout: int = 60, env: Optional[dict] = None) -> "_GitResult":
    """跑 git · 异常归一为 _GitResult(returncode 124=timeout / 127=git 不可用)。"""
    try:
        r = subprocess.run(
            ["git", *git_args], cwd=cwd, env=env,
            capture_output=True, text=True, timeout=timeout,
        )
        return _GitResult(r.returncode, r.stdout, r.stderr)
    except subprocess.TimeoutExpired:
        return _GitResult(124, "", f"git {git_args[0] if git_args else ''} 超时({timeout}s)")
    except (FileNotFoundError, OSError) as e:
        return _GitResult(127, "", f"git 不可用:{e}")


def _list_worktrees(cwd: Optional[str]) -> list:
    """git worktree list --porcelain → [{path, branch?}, ...] · 首条 = 主工作区。"""
    r = _git(["worktree", "list", "--porcelain"], cwd=cwd)
    if r.returncode != 0:
        return []
    out: list = []
    cur: dict = {}
    for line in r.stdout.splitlines():
        if line.startswith("worktree "):
            if cur:
                out.append(cur)
            cur = {"path": line.split(" ", 1)[1]}
        elif line.startswith("branch "):
            cur["branch"] = line.split(" ", 1)[1]
    if cur:
        out.append(cur)
    return out


def _same_path(a: Optional[str], b: Optional[str]) -> bool:
    """两路径 resolve 后相等(容错 · 解析失败退化为字符串比较)。"""
    if not a or not b:
        return False
    try:
        return Path(a).resolve() == Path(b).resolve()
    except (OSError, ValueError):
        return a == b


def _ship_finalize_precheck() -> str:
    """ship-finalize 必须在主工作区跑 · 返回主工作区路径。

    治本沿用 P0-156:step 6 worktree-remove 不能删自身所在 worktree ·
    且 Phase 2 状态同步语义上属于 merge_target 主工作区。
    在 linked worktree 跑 → FAIL · hint 给精确 cd 目标。
    """
    if os.environ.get("TEAMWORK_BYPASS_MAIN_WORKTREE") == "1":
        return os.getcwd()
    gd = _git(["rev-parse", "--git-dir"])
    if gd.returncode != 0:
        return os.getcwd()  # 不在 git 仓库 · 交后续步骤报错
    wts = _list_worktrees(None)
    main_path = wts[0]["path"] if wts else None
    if "/worktrees/" in gd.stdout.strip():
        emit_json({
            "verdict": "FAIL",
            "command": "ship-finalize",
            "completed_steps": [],
            "failed_step": "precheck",
            "error": "ship-finalize 必须在主工作区运行 · 当前 cwd 在 linked worktree",
            "hint": (
                f"cd {main_path} · 再跑 state.py ship-finalize"
                if main_path else
                "cd 到主工作区(原 git clone 位置)· 再跑 state.py ship-finalize"
            ),
            "main_worktree": main_path,
            "rule": "P0-156 物化拦截 · ship-finalize 沿用(worktree-remove 不能删自身)",
            "bypass": "调试场景设 TEAMWORK_BYPASS_MAIN_WORKTREE=1",
        }, exit_code=1)
    return main_path or os.getcwd()


def _ship_finalize_fail(step: str, error: str, hint: str,
                        completed: list, skipped: list,
                        extra: Optional[dict] = None) -> None:
    """ship-finalize 硬失败 · emit FAIL + 可重入提示 · exit 1。"""
    payload = {
        "verdict": "FAIL",
        "command": "ship-finalize",
        "completed_steps": completed,
        "skipped_steps": skipped,
        "failed_step": step,
        "error": error,
        "hint": hint,
        "resume": (
            "修复后重跑 state.py ship-finalize --feature <path> · "
            "可重入(已完成步骤自动跳过)"
        ),
    }
    if extra:
        payload.update(extra)
    emit_json(payload, exit_code=1)


def _ship_finalize_planning_pending(feature_path: str, merge_target: str,
                                    completed: list, skipped: list,
                                    warnings: list) -> None:
    """v8.93:收尾交付前的「规划层 back-ref 翻牌」暂停点(gate)。

    治本 case:旧 §5.5 在 ship-finalize 全跑完(收尾 MR 已合 + worktree 已清)**之后**才提
    规划层翻牌 · 且用**直推 merge_target**(与 v8.80「去直推」自相矛盾 · 保护分支会被拒 · 且
    收尾 MR 早已关闭 → 规划层物理上塞不进去 → 非原子 + 直推隐患)。
    现在改成:finalize-deliver **暂存收尾分支前**先停在此 · 让 AI 判断 WS/ROADMAP/teamwork-space.md
    (+ 项目变更单)哪些要翻「已交付」· 改完用 `--planning-artifacts <files>` 重跑 → 这些文件
    随 {archive zip + 删目录 + state.json} **同一收尾 MR** 合入(原子 · 走 MR · 兼容保护分支)。
    确无可翻(ad-hoc Bug/Micro 无关联 BL)→ `--no-planning-changes` 显式跳过。
    emit PENDING + exit 0(非失败 · 待 AI 翻牌)。
    """
    payload: dict = {
        "verdict": "PENDING",
        "command": "ship-finalize",
        "completed_steps": completed,
        "skipped_steps": skipped,
        "pending_step": "planning-backref",
        "next_action": (
            "🔴 收尾交付前 · 先翻规划层 back-reference(feature = 某 BL 的落地 · 落地完不翻牌 → "
            "规划层与执行层永久脱节 · 进度统计失真):\n"
            "  ① 判断这几处哪些需翻「📋 规划中/可启动 → ✅ 已交付」(只改相关的 · AI 自决):\n"
            "     - ROADMAP.md 对应 BL(若是 WS 最后一个 BL → WS 标完成)\n"
            "     - product-overview/workstream/WS-NN.md(WS 进度)\n"
            "     - teamwork-space.md(工作区级索引 · 按需)\n"
            "     - 项目变更单(如 BG-NNN.md 的对应阶段状态 · 按需)\n"
            "  ② 在**主工作区**改好这些文件(不要 commit · ship-finalize 会随收尾 MR 一起带走)\n"
            "  ③ 重跑把它们随收尾 MR 一起合入 · 同时给本 feature 一句 **≤50 字**极简描述"
            "(写进归档 INDEX.md · 便于日后不解压识别):\n"
            f"     state.py ship-finalize --feature {feature_path} "
            "--planning-artifacts <逗号分隔的相对路径> --archive-desc '<≤50 字描述>'\n"
            "  确无可翻(ad-hoc Bug/Micro · 无关联 BL)→ 显式跳过(仍可给 --archive-desc):\n"
            f"     state.py ship-finalize --feature {feature_path} --no-planning-changes "
            "--archive-desc '<≤50 字描述>'"
        ),
        "resume": (
            "翻牌(或确认无需翻)后重跑带 --planning-artifacts / --no-planning-changes · "
            "state.py 会把规划层改动 + 归档 zip 暂存进同一收尾分支 → 你创建并合并**一个** MR → "
            "再重跑 ship-finalize 续清理 worktree + 主分支 pull。"
        ),
    }
    if warnings:
        payload["warnings"] = warnings
    emit_json(payload, exit_code=0)


def _ship_finalize_deliver_pending(feature_path: str, merge_target: str,
                                   sf_branch: str, commit: str,
                                   completed: list, skipped: list,
                                   warnings: list, archived: bool = False,
                                   planning_bundled: Optional[list] = None) -> None:
    """v8.80:收尾改动已暂存到 ship-finalize 分支 · 待 AI 用 gh/glab 创 MR + 自动合并。

    去直推后 merge_target 全程只经 MR(兼容保护分支 · 主工作区只 pull)。
    emit PENDING + 交接(state.py 不代跑 gh/glab · AI 来跑 · 与 Phase 1 创 MR 同模型)·
    exit 0(非失败 · 是「待 AI 动作」)。收尾 MR 合并后重跑 ship-finalize ·
    检测已合(zip/ancestor)→ 续 worktree-remove + main-sync。
    v8.82:archived=True 时收尾分支含「feature 目录 zip 进 _archive/ + 删原目录」· MR 文案点明归档。
    """
    plan_n = len(planning_bundled or [])
    plan_seg = (f" + 规划层翻牌 {plan_n} 文件({', '.join(planning_bundled)})"
                if plan_n else "")
    deliver_desc = (
        ("收尾改动(过程层 feature 目录已 zip 进 _archive/ + 删原目录 + 终态 state.json/INDEX"
         + plan_seg + ")"
         if archived else "收尾改动(终态 state.json 等" + plan_seg + ")")
    )
    title = (f"chore: ship-finalize archive {sf_branch}" if archived
             else f"chore: ship-finalize {sf_branch}")
    body = ("teamwork ship-finalize 收尾 · 归档过程层 feature 目录(代码是唯一真相)"
            if archived else "teamwork ship-finalize 收尾")
    if plan_n:
        body += f" + 规划层 back-ref 翻牌(BL/WS → 已交付 · {plan_n} 文件)"
    payload: dict = {
        "verdict": "PENDING",
        "command": "ship-finalize",
        "completed_steps": completed,
        "skipped_steps": skipped,
        "pending_step": "finalize-deliver",
        "finalize_mr": {"branch": sf_branch, "head_commit": commit,
                        "merge_target": merge_target, "archived": archived,
                        **({"planning_bundled": planning_bundled} if plan_n else {})},
        "next_action": (
            f"收尾分支已暂存:{sf_branch}(commit {commit[:12]}) → 目标 {merge_target}。\n"
            + (f"✅ 规划层 back-ref({plan_n} 文件)已随同一收尾分支暂存 · "
               "与归档 zip 同一个 MR 原子合入。\n" if plan_n else "")
            + f"🔴 去直推(v8.80):{deliver_desc}必须经 MR 合入 merge_target。"
            "用 gh/glab 创建 MR 并自动合并(state.py 不代跑 CLI · 由你执行 · 同 Phase 1):\n"
            f"  GitHub:gh pr create --base {merge_target} --head {sf_branch} "
            f"--title '{title}' --body '{body}' "
            f"&& gh pr merge {sf_branch} --merge --delete-branch\n"
            f"  GitLab:glab mr create --source-branch {sf_branch} "
            f"--target-branch {merge_target} --title '{title}' --yes "
            f"&& glab mr merge {sf_branch} --yes --remove-source-branch\n"
            "降级:\n"
            "  - gh/glab 不可用(未登录 / token 无 scope / 网络隔离)→ 报明确原因给用户 · "
            "用户解决后重跑 ship-finalize\n"
            "  - 无法自动合 → 用上面 create 命令拿 MR 链接给用户手动合 → 合后重跑 ship-finalize"
        ),
        "resume": (
            f"收尾 MR 合并后重跑:state.py ship-finalize --feature {feature_path}"
            "(可重入 · 检测已合 → 续删 worktree + 主分支 pull"
            + (" + 清本地已归档 feature 目录" if archived else "") + ")"
        ),
    }
    if warnings:
        payload["warnings"] = warnings
    emit_json(payload, exit_code=0)


def _remote_finalize_delivered(main_wt: str, artifact_root: Path,
                               merge_target: str) -> bool:
    """v8.80:origin/merge_target 上本 feature 的 state.json 是否已是终态(交付完成)。

    语义判定 current_stage == "completed":抗 squash 合并 + save_state 非确定性
    (不依赖 commit ancestor / 字节级 no-delta)· 收尾 MR 合并后 merge_target 上即为终态。
    调用前应已 fetch origin/merge_target。
    """
    pre = _git(["rev-parse", "--show-prefix"], cwd=str(artifact_root))
    if pre.returncode != 0:
        return False
    repo_rel = (pre.stdout.strip() + "state.json").lstrip("/")
    rs = _git(["show", f"origin/{merge_target}:{repo_rel}"], cwd=main_wt)
    if rs.returncode != 0:
        return False
    try:
        return json.loads(rs.stdout).get("current_stage") == "completed"
    except (ValueError, json.JSONDecodeError):
        return False


# ─── v8.82:ship2 归档本体(过程层 feature 目录 zip + 从 merge_target 删 · 随收尾 MR)──


def _read_archive_on_ship(start: str) -> bool:
    """v8.82:读项目根 .teamwork_localconfig.json 的 archive_on_ship(默认 true)。

    true(默认):ship2 收尾 MR 把交付 feature 目录 zip 进 features/_archive/<id>.zip ·
                原目录从 merge_target 删(防 AI 检索过时 feature 信息 · 代码是唯一真相)。
    false:退回 v8.80(收尾 MR 只同步终态 state.json · 不归档 · feature 目录留存)。
    从 start 向上找 · 到 .git 边界止(同 state.py._read_id_strategy 模式)。
    """
    try:
        node = Path(start).resolve()
    except OSError:
        return True
    for d in [node, *node.parents]:
        cfg = d / ".teamwork_localconfig.json"
        if cfg.exists():
            try:
                val = json.loads(cfg.read_text(encoding="utf-8")).get("archive_on_ship")
            except (OSError, json.JSONDecodeError):
                return True
            return bool(val) if isinstance(val, bool) else True
        if (d / ".git").exists():
            break
    return True


def _archive_repo_paths(repo_cwd: str, artifact_root: Path,
                        feature_id: str) -> Optional[tuple]:
    """v8.82:算归档相关 repo 相对路径 · 返 (feature_rel, zip_rel, index_rel) 或 None。

    feature_rel: docs/features/<dir-name>      (无尾 /)
    zip_rel:     docs/features/_archive/<id>.zip
    index_rel:   docs/features/_archive/INDEX.md
    用 features 根(artifact_root 父目录)算 show-prefix · 兼容 feature 目录已删(3rd-run)。
    """
    features_root = artifact_root.parent
    pre = _git(["rev-parse", "--show-prefix"], cwd=str(features_root))
    if pre.returncode == 0:
        features_prefix = pre.stdout.strip().rstrip("/")  # 如 docs/features
    else:
        # features 根也不在工作区(罕见)· 退而用 artifact_root 自身的 prefix
        pre2 = _git(["rev-parse", "--show-prefix"], cwd=str(artifact_root))
        if pre2.returncode != 0:
            return None
        feat_prefix = pre2.stdout.strip().rstrip("/")  # docs/features/<id>
        features_prefix = feat_prefix.rsplit("/", 1)[0] if "/" in feat_prefix else ""
    base = (features_prefix + "/") if features_prefix else ""
    feature_rel = f"{base}{artifact_root.name}"
    zip_rel = f"{base}{ARCHIVE_DIR_NAME}/{feature_id}.zip"
    index_rel = f"{base}{ARCHIVE_DIR_NAME}/INDEX.md"
    return feature_rel, zip_rel, index_rel


def _remote_archive_delivered(main_wt: str, artifact_root: Path,
                              feature_id: str, merge_target: str) -> bool:
    """v8.82:origin/merge_target 上是否已有本 feature 的归档 zip(= 已交付 + 归档)。

    zip 存在 = 收尾 MR(含归档)已合 · 抗 squash。调用前应已 fetch origin/merge_target。
    """
    paths = _archive_repo_paths(main_wt, artifact_root, feature_id)
    if not paths:
        return False
    _feat_rel, zip_rel, _index_rel = paths
    r = _git(["cat-file", "-e", f"origin/{merge_target}:{zip_rel}"], cwd=main_wt)
    return r.returncode == 0


def _build_archive_zip(artifact_root: Path) -> bytes:
    """v8.82:把 feature 目录打包为 zip bytes · arcname=<dir>/<rel>(自描述)· 固定 mtime 可复现。"""
    import io
    import zipfile
    buf = io.BytesIO()
    fixed = (1980, 1, 1, 0, 0, 0)
    files = sorted((p for p in artifact_root.rglob("*") if p.is_file()),
                   key=lambda p: p.as_posix())
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            rel = p.relative_to(artifact_root).as_posix()
            zi = zipfile.ZipInfo(f"{artifact_root.name}/{rel}", date_time=fixed)
            zi.external_attr = 0o644 << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, p.read_bytes())
    return buf.getvalue()


def _clean_archive_desc(raw: Optional[str]) -> str:
    """v8.94:极简 feature 描述净化 —— 折叠空白 + 去 markdown 表格危险字符(`|`/换行)+
    ≤50 字(超则截 49 + `…`)。空 → `—`(占位 · 表格不塌)。"""
    if not raw:
        return "—"
    s = " ".join(str(raw).split()).replace("|", "/")
    if len(s) > 50:
        s = s[:49] + "…"
    return s or "—"


def _build_archive_index(repo_cwd: str, base_commit: str, index_rel: str,
                         feature_id: str, when: str,
                         archive_desc: Optional[str] = None) -> str:
    """v8.82:读 base 上现有 INDEX.md(若有)· 去本 feature 旧行 · 追加新行 · 返回新内容。

    v8.94:加「描述」列(≤50 字极简 feature 描述 · AI 在 planning-backref 暂停点经
    `--archive-desc` 提供 · 便于日后不解压就能识别归档内容)· 旧 3 列行自动迁移为 4 列(补 `—`)。
    """
    header = (
        "# Feature 归档索引\n\n"
        "> teamwork ship-finalize 自动维护 · 每个交付 Feature 的**过程层**产物归档为 "
        "`<id>.zip`(含 state.json / 各 stage 产物)· **代码是唯一真相** · 此处仅留可追溯快照。\n"
        "> 需要历史细节时 `unzip <id>.zip`。\n\n"
        "| Feature | 描述 | 交付归档时间 | 归档物 |\n"
        "| --- | --- | --- | --- |\n"
    )
    rows: list = []
    show = _git(["show", f"{base_commit}:{index_rel}"], cwd=repo_cwd)
    if show.returncode == 0:
        for line in show.stdout.splitlines():
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not cells or cells[0] in ("Feature", "---", ""):
                continue  # 跳过表头 / 分隔行
            if cells[0] == feature_id:
                continue  # 去重旧行(re-archive 覆盖)
            # v8.94:旧 3 列(Feature|时间|归档物)→ 迁移为 4 列(补描述占位 `—`)
            if len(cells) == 3:
                rows.append(f"| {cells[0]} | — | {cells[1]} | {cells[2]} |")
            else:
                rows.append(s)
    rows.append(f"| {feature_id} | {_clean_archive_desc(archive_desc)} | "
                f"{when} | `{feature_id}.zip` |")
    return header + "\n".join(rows) + "\n"


def _stage_archive_commit(repo_cwd: str, artifact_root: Path, feature_id: str,
                          merge_target: str, sf_ref: str,
                          planning_files: Optional[list] = None,
                          archive_desc: Optional[str] = None) -> tuple:
    """v8.82:构建归档收尾 commit(add zip + INDEX.md · rm feature 目录)· push 到 sf_ref(force)。

    base = origin/<merge_target>。零 checkout(临时 GIT_INDEX_FILE)。feature 目录(过程层)的
    终态产物已在本地 artifact_root(step 1-4 save_state 写入)· 一并打进 zip。
    v8.93:planning_files=[(repo_rel, abs_path), ...] —— 规划层 back-ref 翻牌文件
    (WS/ROADMAP/teamwork-space.md + 变更单)随**同一收尾 MR** 合入(去 §5.5 post-step 直推)·
    hash 工作树内容(AI 刚翻牌的版本)→ update-index --add 进收尾 commit。
    返回 (ok: bool, warn: str, commit_hash: str)。无 delta → (True, "", "")。
    """
    paths = _archive_repo_paths(repo_cwd, artifact_root, feature_id)
    if not paths:
        return False, "无法解析归档 repo 相对路径(rev-parse --show-prefix 失败)", ""
    feature_rel, zip_rel, index_rel = paths

    base = _git(["rev-parse", f"origin/{merge_target}"], cwd=repo_cwd)
    if base.returncode != 0:
        return False, f"无法解析 origin/{merge_target}:{base.stderr.strip()}", ""
    base_commit = base.stdout.strip()
    bt = _git(["rev-parse", f"{base_commit}^{{tree}}"], cwd=repo_cwd)
    if bt.returncode != 0:
        return False, f"无法解析 base tree:{bt.stderr.strip()}", ""
    base_tree = bt.stdout.strip()

    # zip blob(二进制 · 走 subprocess input · _git text 模式不收二进制)
    zip_bytes = _build_archive_zip(artifact_root)
    try:
        hz = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=repo_cwd,
                            input=zip_bytes, capture_output=True, timeout=60)
    except (subprocess.TimeoutExpired, OSError) as e:
        return False, f"hash-object zip 异常:{e}", ""
    if hz.returncode != 0:
        return False, ("hash-object zip 失败:"
                       + hz.stderr.decode("utf-8", "replace").strip()), ""
    zip_blob = hz.stdout.decode().strip()

    # INDEX.md blob
    index_content = _build_archive_index(repo_cwd, base_commit, index_rel,
                                         feature_id, now_iso(),
                                         archive_desc=archive_desc)
    try:
        hi = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=repo_cwd,
                            input=index_content.encode("utf-8"),
                            capture_output=True, timeout=30)
    except (subprocess.TimeoutExpired, OSError) as e:
        return False, f"hash-object INDEX.md 异常:{e}", ""
    if hi.returncode != 0:
        return False, ("hash-object INDEX.md 失败:"
                       + hi.stderr.decode("utf-8", "replace").strip()), ""
    index_blob = hi.stdout.decode().strip()

    # v8.93:规划层 back-ref 文件 blob(hash 工作树内容 · AI 刚翻牌的版本)· 随收尾 MR 一起合入
    planning_blobs: list = []  # [(repo_rel, blob), ...]
    for prel, pabs in (planning_files or []):
        hp = _git(["hash-object", "-w", str(pabs)], cwd=repo_cwd)
        if hp.returncode != 0:
            return False, f"hash-object 规划层文件 {prel} 失败:{hp.stderr.strip()}", ""
        planning_blobs.append((prel, hp.stdout.strip()))

    # 列出 base tree 上 feature 目录的所有条目(逐条 --force-remove)
    ls = _git(["ls-tree", "-r", "--name-only", base_tree, "--", feature_rel],
              cwd=repo_cwd)
    feature_entries = ([ln.strip() for ln in ls.stdout.splitlines() if ln.strip()]
                       if ls.returncode == 0 else [])

    tmp_dir = tempfile.mkdtemp(prefix="tw-ship-archive-")
    idx_path = os.path.join(tmp_dir, "index")
    env = {**os.environ, "GIT_INDEX_FILE": idx_path}
    try:
        rt = _git(["read-tree", base_tree], cwd=repo_cwd, env=env)
        if rt.returncode != 0:
            return False, f"read-tree 失败:{rt.stderr.strip()}", ""
        for blob, rel in ((zip_blob, zip_rel), (index_blob, index_rel)):
            ui = _git(["update-index", "--add", "--cacheinfo", f"100644,{blob},{rel}"],
                      cwd=repo_cwd, env=env)
            if ui.returncode != 0:
                return False, f"update-index add {rel} 失败:{ui.stderr.strip()}", ""
        for entry in feature_entries:
            ur = _git(["update-index", "--force-remove", entry], cwd=repo_cwd, env=env)
            if ur.returncode != 0:
                return False, f"update-index --force-remove {entry} 失败:{ur.stderr.strip()}", ""
        # v8.93:规划层翻牌文件加进同一收尾 commit(在 force-remove 之后 · 防被误删)
        for prel, blob in planning_blobs:
            up = _git(["update-index", "--add", "--cacheinfo", f"100644,{blob},{prel}"],
                      cwd=repo_cwd, env=env)
            if up.returncode != 0:
                return False, f"update-index add 规划层文件 {prel} 失败:{up.stderr.strip()}", ""
        wtr = _git(["write-tree"], cwd=repo_cwd, env=env)
        if wtr.returncode != 0:
            return False, f"write-tree 失败:{wtr.stderr.strip()}", ""
        new_tree = wtr.stdout.strip()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    if new_tree == base_tree:
        return True, "", ""  # 无变化(罕见 · 已归档)→ 视作已交付

    plan_note = (f" + 规划层翻牌 {len(planning_blobs)} 文件" if planning_blobs else "")
    msg = (f"chore({feature_id}): archive feature 过程层 → "
           f"{ARCHIVE_DIR_NAME}/{feature_id}.zip + rm 目录{plan_note} [teamwork ship-finalize]")
    ct = _git(["commit-tree", new_tree, "-p", base_commit, "-m", msg], cwd=repo_cwd)
    if ct.returncode != 0:
        return False, f"commit-tree 失败:{ct.stderr.strip()}", ""
    new_commit = ct.stdout.strip()

    pr = _git(["push", "--force", "origin", f"{new_commit}:{sf_ref}"],
              cwd=repo_cwd, timeout=120)
    if pr.returncode != 0:
        return False, f"push {sf_ref} 失败:{pr.stderr.strip()[:200]}", ""
    return True, "", new_commit


def _purge_local_feature_dir_for_archive(main_wt: str, feature_rel: str) -> list:
    """v8.82:归档已交付 · 把本地 feature 目录恢复到 HEAD 干净态(restore tracked + clean untracked)·
    使后续 ff-pull 能干净删除该目录(origin 已删)· 返回 warnings。"""
    warns: list = []
    # restore tracked 文件到 HEAD(丢弃 step 1-4 写入的本地终态改动 · 内容已进 zip)
    _git(["checkout", "HEAD", "--", feature_rel], cwd=main_wt, timeout=30)
    # 清 feature 目录内 untracked(如未 commit 的 review-log.jsonl · 内容已进 zip)
    cl = _git(["clean", "-fdq", "--", feature_rel], cwd=main_wt, timeout=30)
    if cl.returncode != 0:
        warns.append(f"git clean {feature_rel} 失败(非致命):{cl.stderr.strip()[:80]}")
    return warns


def _archive_idempotent_zip(main_wt: str, feature_path: str) -> Optional[str]:
    """v8.82:feature 目录已不在(被归档删)· 检查 origin/<当前分支> 是否已有归档 zip。

    返回 zip_rel(已归档 · 幂等成功)或 None。用于 ship-finalize 3rd-run:目录被删后重跑 ·
    state-sync 找不到 state.json 会 BLOCK · 此处先判「已归档」→ 幂等 PASS。
    """
    artifact_root = Path(feature_path)
    feature_id = artifact_root.name
    cur = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=main_wt)
    mt = cur.stdout.strip() if cur.returncode == 0 else ""
    if not mt or mt == "HEAD":
        return None
    _git(["fetch", "origin", mt], cwd=main_wt, timeout=60)
    paths = _archive_repo_paths(main_wt, artifact_root, feature_id)
    if not paths:
        return None
    _feat_rel, zip_rel, _index_rel = paths
    r = _git(["cat-file", "-e", f"origin/{mt}:{zip_rel}"], cwd=main_wt)
    return zip_rel if r.returncode == 0 else None


def _step_state_sync(main_wt: str, feature_path: str) -> dict:
    """v8.16 ship-finalize step 0:把 worktree 内完整态 state.json 桥接到主工作区。

    治本 case SVC-CORE-B006(2026-05-21):
    Phase 1 ship-phase sanitize / push 写 state.json 后不自动 commit(by design ·
    防 MR 被 chore commit 弄脏)· 所以 push 到 feature 分支的 commit 不含完整
    state.json(缺 ship.phase=pushed / feature_head_commit 等)。
    用户 merge MR 后 · 主工作区 git pull 拉下的 state.json 是合并前快照(不全)·
    ship-finalize step 1 verify-merge 读不到 feature_head_commit → FAIL。
    完整态 state.json 永远在 **worktree 内工作树**(sanitize/push 写入但未 commit)·
    必须自动同步到主工作区 · step 5 finalize-push 才能直推完整态到 merge_target。

    流程:
      ① 主工作区 git fetch + ff-pull merge_target(若在 merge_target 分支 + 工作树干净)
      ② 检测主工作区 state.json:
         - 不存在 + worktree 内存在 → 复制(不 commit · step 5 finalize-push 直推)
         - 存在但缺 ship.feature_head_commit + worktree 内完整 → 用 worktree 内覆盖
         - 主工作区已完整 → skip(可重入)
      ③ emit sync_action 字段告诉 AI 干了啥(transparent · 不静默)

    返回 {ok: bool, sync_action: str, error?: str, hint?: str}。
    """
    feature_dir_abs = Path(feature_path).resolve()
    state_json_path = feature_dir_abs / "state.json"

    # 算 worktree 内对应 state.json 路径(从主工作区 state.worktree.path + feature_dir 相对路径)
    # 优先用 worktree 内已存在的 state.json(完整态)· 失败则尝试主工作区现状
    main_wt_path = Path(main_wt).resolve()

    # 提前算 main_wt 的 merge_target 名(后续 fetch + 主工作区 state.json 都要)
    # 没法从 state.json 读(可能不存在)· 用 main_wt 当前分支猜
    cur = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=main_wt)
    main_branch = cur.stdout.strip() if cur.returncode == 0 else ""

    # ① 主工作区先 fetch + 安全 ff-pull(让本地拿到 MR 合并后的 features dir)
    sync_actions: list = []
    fetched = False
    if main_branch:
        f = _git(["fetch", "origin", main_branch], cwd=main_wt, timeout=120)
        if f.returncode == 0:
            fetched = True
            sync_actions.append(f"fetched origin/{main_branch}")
            dirty = _git(["status", "--porcelain"], cwd=main_wt)
            is_dirty = bool(dirty.stdout.strip()) if dirty.returncode == 0 else False
            if not is_dirty:
                pl = _git(["pull", "--ff-only", "origin", main_branch],
                          cwd=main_wt, timeout=120)
                if pl.returncode == 0:
                    sync_actions.append(f"ff-pulled origin/{main_branch}")
                else:
                    # 分叉 · ff 失败 · 不致命 · 后续 step 0.5 检查 state.json
                    sync_actions.append(
                        f"ff-pull skipped(分叉:{pl.stderr.strip()[:80]})")
            else:
                sync_actions.append("ff-pull skipped(工作树脏)")
        else:
            sync_actions.append(
                f"fetch FAIL(non-fatal):{f.stderr.strip()[:80]}")

    # ② 主工作区 state.json 是否完整?
    main_state_complete = False
    if state_json_path.exists():
        try:
            with state_json_path.open("r", encoding="utf-8") as fp:
                main_state = json.load(fp)
            ship = main_state.get("ship") or {}
            # 完整态判据:有 ship.feature_head_commit(Phase 1 push 写入)
            if ship.get("feature_head_commit"):
                main_state_complete = True
        except (OSError, json.JSONDecodeError):
            pass

    # 主工作区已完整 → skip · 可重入
    if main_state_complete:
        sync_actions.append("main state.json 完整 · skip sync")
        return {"ok": True, "sync_action": " · ".join(sync_actions)}

    # ③ 主工作区不全 / 缺 → 找 worktree 内 state.json
    # 先读已有 state.json(主工作区或不全) → 拿 state.worktree.path
    # 若主工作区 state.json 不存在 → 退而求其次扫所有 linked worktree 找 state.json
    wt_state_path = None
    if state_json_path.exists():
        # 读不全的主工作区 state.json 拿 worktree.path 字段(state.worktree.path 是相对主工作区 OR 绝对)
        try:
            with state_json_path.open("r", encoding="utf-8") as fp:
                tmp_state = json.load(fp)
            wt_info = tmp_state.get("worktree") or {}
            wt_path_raw = wt_info.get("path") or ""
            if wt_path_raw:
                wt_path = Path(wt_path_raw)
                if not wt_path.is_absolute():
                    wt_path = (main_wt_path / wt_path_raw).resolve()
                else:
                    wt_path = wt_path.resolve()
                # 算 worktree 内对应 state.json:wt_path + (feature_dir 相对 main_wt 的 path)
                try:
                    feat_rel = feature_dir_abs.relative_to(main_wt_path)
                    candidate = wt_path / feat_rel / "state.json"
                    if candidate.exists():
                        wt_state_path = candidate
                except ValueError:
                    pass
        except (OSError, json.JSONDecodeError):
            pass

    # 主工作区 state.json 不存在或无法读出 wt path → 扫 git worktree list 找含 state.json 的
    if wt_state_path is None:
        for w in _list_worktrees(main_wt):
            wp = Path(w.get("path") or "")
            if not wp.exists() or wp.resolve() == main_wt_path:
                continue
            try:
                feat_rel = feature_dir_abs.relative_to(main_wt_path)
                candidate = wp / feat_rel / "state.json"
                if candidate.exists():
                    wt_state_path = candidate
                    break
            except ValueError:
                pass

    if wt_state_path is None:
        # 完全找不到 worktree state.json · BLOCK
        return {
            "ok": False,
            "sync_action": " · ".join(sync_actions),
            "error": (
                f"state.json not found in main workspace ({state_json_path}) · "
                f"也未找到 worktree 内副本 · 无法同步完整态"
            ),
            "hint": (
                "可能原因:① worktree 已被手工删 · ② --feature 路径错 · "
                "③ 用户未在主工作区 merge_target 分支(当前分支:"
                f"{main_branch!r} · 应在 merge_target 分支跑 ship-finalize) · "
                "排查后重跑 · 或 export TEAMWORK_BYPASS_MAIN_WORKTREE=1 跳过物化校验后手工 finalize"
            ),
        }

    # 验证 worktree 内 state.json 是否完整(有 feature_head_commit)
    try:
        with wt_state_path.open("r", encoding="utf-8") as fp:
            wt_state = json.load(fp)
    except (OSError, json.JSONDecodeError) as e:
        return {
            "ok": False,
            "sync_action": " · ".join(sync_actions),
            "error": f"worktree state.json 读失败({wt_state_path}): {e}",
            "hint": "排查 worktree state.json 完整性 · 修复后重跑",
        }
    wt_ship = wt_state.get("ship") or {}
    if not wt_ship.get("feature_head_commit"):
        return {
            "ok": False,
            "sync_action": " · ".join(sync_actions),
            "error": (
                f"worktree state.json({wt_state_path})也缺 ship.feature_head_commit · "
                "Phase 1 push 未完成 · 无法 finalize"
            ),
            "hint": (
                "回 worktree 跑 state.py ship-phase --action push(push feature 分支 + 创 MR)· "
                "再回主工作区重跑 ship-finalize"
            ),
        }

    # ④ 复制 worktree 内完整态 → 主工作区(不 commit · step 5 finalize-push 直推完整态)
    try:
        feature_dir_abs.mkdir(parents=True, exist_ok=True)
        shutil.copy2(wt_state_path, state_json_path)
        sync_actions.append(
            f"synced state.json from worktree:{wt_state_path} → {state_json_path}"
        )
    except OSError as e:
        return {
            "ok": False,
            "sync_action": " · ".join(sync_actions),
            "error": f"复制 worktree state.json 失败: {e}",
            "hint": "排查文件权限 / 磁盘 · 修复后重跑",
        }

    return {"ok": True, "sync_action": " · ".join(sync_actions)}


def _classify_main_sync_dirty(main_wt: str, feature_dir: Path, state: dict) -> dict:
    """v8.31:step 7 main-sync 前 · 分类 dirty 文件(治本主工作区残留 case)。

    返回:
      - is_dirty:bool(整体是否 dirty)
      - all_files:list[str](全 dirty 文件 · 相对 main_wt)
      - feature_artifacts:list(本 Feature 内 state.json / review-log.jsonl · 工具副产物)
      - bootstrap_pointers:list(AGENTS.md / CLAUDE.md / GEMINI.md · bootstrap 注入段)
      - harness_locks:list(.claude/*.lock 等 harness 锁 · 理想该 gitignore)
      - other_files:list(用户真改动 · 不该自动处理)
      - safe_to_stash:bool(other_files 为空 · 全部副产物 · 可 stash+ff-pull+unstash)
      - categories_present:list[str]("feature_artifacts" / "bootstrap_pointers" / "harness_locks")
    """
    r = _git(["status", "--porcelain"], cwd=main_wt, timeout=30)
    if r.returncode != 0 or not r.stdout.strip():
        return {
            "is_dirty": False, "all_files": [],
            "feature_artifacts": [], "bootstrap_pointers": [],
            "harness_locks": [], "other_files": [],
            "safe_to_stash": True, "categories_present": [],
        }

    # 算 feature_dir 相对 main_wt 的路径(用来识别本 Feature artifacts)
    # v8.62:resolve 后再 relative_to(归一 symlink · macOS /var→/private/var)·
    # 否则 relative_to 抛 ValueError → feature_rel="" → state.json/review-log.jsonl
    # 落 other_files → safe_to_stash=False → main-sync 整段跳过(治本"总是残留")
    try:
        feature_rel = str(feature_dir.resolve().relative_to(Path(main_wt).resolve()))
    except (ValueError, OSError):
        feature_rel = ""

    feature_artifacts: list = []
    bootstrap_pointers: list = []
    harness_locks: list = []
    other_files: list = []
    all_files: list = []

    for line in r.stdout.splitlines():
        # git status --porcelain 格式:"XY <path>"(X=index status · Y=worktree status)
        if len(line) < 4:
            continue
        path = line[3:].strip()
        # 处理 rename 格式 "old -> new"
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        all_files.append(path)

        # 分类
        if feature_rel and path.startswith(feature_rel + "/"):
            basename = path.rsplit("/", 1)[-1]
            if basename in ("state.json", "review-log.jsonl"):
                feature_artifacts.append(path)
                continue
            # 本 Feature 内其他文件 = 用户改动(代码 / 文档)· 不自动处理
            other_files.append(path)
        elif path in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
            bootstrap_pointers.append(path)
        elif path.startswith(".claude/") and (
            path.endswith(".lock") or path.endswith("_tasks.lock")
        ):
            harness_locks.append(path)
        else:
            other_files.append(path)

    categories = []
    if feature_artifacts:
        categories.append("feature_artifacts")
    if bootstrap_pointers:
        categories.append("bootstrap_pointers")
    if harness_locks:
        categories.append("harness_locks")

    return {
        "is_dirty": True,
        "all_files": all_files,
        "feature_artifacts": feature_artifacts,
        "bootstrap_pointers": bootstrap_pointers,
        "harness_locks": harness_locks,
        "other_files": other_files,
        "safe_to_stash": not other_files,
        "categories_present": categories,
    }


def _main_sync_clean_feature_artifacts(
        main_wt: str, merge_target: str, dirty_result: dict) -> list:
    """v8.70:用 origin 版覆盖本 Feature 的 state.json/review-log.jsonl(总是安全 ·
    ship-finalize 是最权威推送 · origin 已有终态)· 返回 checkout 失败列表。"""
    failed = []
    for f in dirty_result.get("feature_artifacts", []):
        co = _git(["checkout", f"origin/{merge_target}", "--", f],
                  cwd=main_wt, timeout=15)
        if co.returncode != 0:
            failed.append(f)
    return failed


def _main_sync_apply_strategy(
        main_wt: str, merge_target: str, artifact_root: Path, state: dict,
        strategy: str, message: Optional[str] = None) -> dict:
    """v8.70:对主工作区 merge_target 应用 main-sync 净化策略 · 返回结果 dict。

    前置:调用方已确保 cwd/main_wt 在主工作区 · 当前分支 = merge_target。
    所有策略都先清 feature_artifacts(origin 版 · 总安全)· 再:
      - commit-push:git add -A → commit → pull --rebase → push(把改动推到 merge_target)
      - stash-pull :git stash -u → pull --ff-only(改动留 stash · 可 pop 恢复 · 不推送)
      - skip       :尽力 ff-pull · 保留用户改动(用户自处理)

    返回 {status, note, warnings:[...], pushed:bool, stash_ref:str|None, pulled:bool}
    """
    warnings: list = []
    dirty = _classify_main_sync_dirty(main_wt, artifact_root, state)
    fa_failed = _main_sync_clean_feature_artifacts(main_wt, merge_target, dirty)
    if fa_failed:
        warnings.append(
            f"feature_artifacts checkout origin/{merge_target} 失败"
            f"({len(fa_failed)}):{', '.join(fa_failed[:5])}")
    feature_id = state.get("feature_id") or "feature"

    if strategy == "commit-push":
        _git(["add", "-A"], cwd=main_wt, timeout=30)
        # git diff --cached --quiet:有暂存改动则 returncode!=0
        staged = _git(["diff", "--cached", "--quiet"], cwd=main_wt, timeout=15)
        committed = False
        if staged.returncode != 0:
            msg = message or (
                f"chore(main-sync): 净化主工作区遗留改动 · ship 后 · {feature_id}")
            cm = _git(["commit", "-m", msg], cwd=main_wt, timeout=30)
            if cm.returncode != 0:
                warnings.append(
                    f"git commit 失败:{cm.stderr.strip()[:100]} · 改动仍在暂存区")
                return {"status": "commit_failed",
                        "note": "commit 失败 · 改动保留暂存区",
                        "warnings": warnings, "pushed": False,
                        "stash_ref": None, "pulled": False}
            committed = True
        # pull --rebase:拿最新 · 把本地 commit 叠到 origin 之上(local 落后时 ff-only 会失败)
        pr = _git(["pull", "--rebase", "origin", merge_target],
                  cwd=main_wt, timeout=120)
        if pr.returncode != 0:
            _git(["rebase", "--abort"], cwd=main_wt, timeout=30)
            warnings.append(
                f"git pull --rebase 冲突/失败:{pr.stderr.strip()[:100]} · 已 abort · "
                f"本地 commit 保留 · 手动 rebase 后 git push origin {merge_target}")
            return {"status": "commit_rebase_conflict",
                    "note": "commit 成功 · pull --rebase 冲突已 abort · commit 保留本地",
                    "warnings": warnings, "pushed": False,
                    "stash_ref": None, "pulled": False}
        ph = _git(["push", "origin", merge_target], cwd=main_wt, timeout=120)
        if ph.returncode != 0:
            warnings.append(
                f"git push origin {merge_target} 失败(分支保护?):"
                f"{ph.stderr.strip()[:120]} · 本地已 commit + 最新 · 手动 push / 走 MR")
            return {"status": "committed_pulled_push_rejected",
                    "note": "commit + pull 成功 · push 被拒(分支保护?)· 本地已最新",
                    "warnings": warnings, "pushed": False,
                    "stash_ref": None, "pulled": True}
        note = ("已 commit 用户改动 + pull --rebase 最新 + push origin · 主工作区干净+最新+已推"
                if committed else
                "无新增改动可 commit · 已 pull --rebase 最新 + push · 主工作区干净+最新")
        return {"status": "committed_pulled_pushed", "note": note,
                "warnings": warnings, "pushed": True,
                "stash_ref": None, "pulled": True}

    if strategy == "stash-pull":
        stash_ref = None
        st_status = _git(["status", "--porcelain"], cwd=main_wt, timeout=30)
        if st_status.stdout.strip():
            msg = message or f"teamwork main-sync stash · ship 后 · {feature_id}"
            st = _git(["stash", "push", "-u", "-m", msg], cwd=main_wt, timeout=30)
            if st.returncode != 0:
                warnings.append(f"git stash 失败:{st.stderr.strip()[:100]} · 改动保留")
                return {"status": "stash_failed",
                        "note": "stash 失败 · 改动保留工作区",
                        "warnings": warnings, "pushed": False,
                        "stash_ref": None, "pulled": False}
            stash_ref = "stash@{0}"
        pl = _git(["pull", "--ff-only", "origin", merge_target],
                  cwd=main_wt, timeout=120)
        if pl.returncode != 0:
            warnings.append(
                f"git pull --ff-only 未通过(分叉):{pl.stderr.strip()[:100]} · "
                f"已 fetch · 需手动 rebase/merge")
            return {"status": "stashed_diverged" if stash_ref else "diverged",
                    "note": ("改动已 stash · 但 ff-pull 分叉 · 需手动 rebase"
                             if stash_ref else "ff-pull 分叉 · 需手动 rebase"),
                    "warnings": warnings, "pushed": False,
                    "stash_ref": stash_ref, "pulled": False}
        if stash_ref:
            warnings.append(
                f"用户改动已 stash({stash_ref})· 主工作区已 ff-pull 最新 · "
                f"git stash pop 恢复改动")
        note = (f"用户改动已 stash({stash_ref})+ ff-pull 最新 · 主工作区干净+最新 · "
                f"改动可 git stash pop 恢复" if stash_ref else
                "无用户改动 · 已 ff-pull 最新 · 主工作区干净+最新")
        return {"status": "stashed_pulled" if stash_ref else "ff_pulled",
                "note": note, "warnings": warnings, "pushed": False,
                "stash_ref": stash_ref, "pulled": True}

    # strategy == "skip":只清 feature_artifacts + 尽力 ff-pull · 保留用户改动
    pl = _git(["pull", "--ff-only", "origin", merge_target],
              cwd=main_wt, timeout=120)
    pulled = pl.returncode == 0
    if not pulled:
        warnings.append(
            f"主工作区有用户改动 · feature_artifacts 已清 · ff-pull 未通过 · "
            f"自行 commit/stash 后 git pull --ff-only origin {merge_target}")
    note = ("feature_artifacts 已清 · ff-pull 最新 · 保留用户改动(用户自处理)"
            if pulled else
            "feature_artifacts 已清 · ff-pull 未通过 · 保留用户改动")
    return {"status": "skipped_user_handles" if pulled else "skipped_no_pull",
            "note": note, "warnings": warnings, "pushed": False,
            "stash_ref": None, "pulled": pulled}


def _build_main_sync_decision(
        feature_path: str, merge_target: str, state: dict,
        dirty_result: dict, pulled: bool) -> dict:
    """v8.70:普通模式主工作区 user-dirty · 构造「是否净化」决策结构 ·
    PMO 转成 SKILL.md R5(b) 暂停点给用户。"""
    other = dirty_result.get("other_files", [])
    is_main = merge_target.split("/")[-1] in ("main", "master")
    # 推荐:用户本意是「push 当前改动」→ commit-push;但 merge_target 是主分支时
    # 推送绕 MR review 有风险 → 改荐 stash-pull(安全 · 不推任意改动)。
    recommended = "stash-pull" if is_main else "commit-push"
    fcmd = f"state.py main-sync --feature {feature_path} --strategy"
    return {
        "reason": ("主工作区(merge_target)有用户未提交改动 · ship 已完成 · "
                   "是否净化以保持主工作区干净 + 最新"),
        "merge_target": merge_target,
        "is_main_branch": is_main,
        "already_pulled_latest": pulled,
        "dirty_count": len(other),
        "dirty_files": other[:20],
        "recommended": recommended,
        "options": [
            {"id": "commit-push", "label": "净化并推送",
             "desc": ("git add -A + commit + pull --rebase + push · 把改动推到 "
                      f"{merge_target} · 主工作区干净+最新+已推"
                      + ("(⚠️ merge_target 是主分支 · 推送绕过 MR review · 慎选)"
                         if is_main else "")),
             "command": f"{fcmd} commit-push [--message '<commit msg>']"},
            {"id": "stash-pull", "label": "暂存后拉取",
             "desc": ("git stash -u + pull --ff-only · 改动留 stash"
                      "(可 git stash pop 恢复)· 不推送 · 主工作区干净+最新"),
             "command": f"{fcmd} stash-pull"},
            {"id": "skip", "label": "暂不处理",
             "desc": ("保留现状 · 用户自行 commit/stash/pull"
                      "(feature_artifacts 已自动清)"),
             "command": f"{fcmd} skip"},
        ],
        "note": ("PMO 按 SKILL.md R5(b) 转暂停点给用户 · "
                 "用户选项后跑对应 state.py main-sync 命令"),
    }


def _main_sync_brief(state: dict, strategy: str, res: dict) -> str:
    """v8.70:main-sync 命令完成 brief。"""
    fid = state.get("feature_id") or "Feature"
    clean_status = (
        "committed_pulled_pushed", "stashed_pulled", "ff_pulled",
        "skipped_user_handles")
    if not res["warnings"] and res["status"] in clean_status:
        return (f"✅ {fid} 主工作区 main-sync({strategy})完成 · {res['note']}")
    lines = [f"⚠️ {fid} 主工作区 main-sync({strategy})有降级项 · PMO 须说明:"]
    lines.append(f"  - {res['note']}")
    for w in res["warnings"]:
        lines.append(f"  - {w}")
    return "\n".join(lines)


def cmd_main_sync(args: argparse.Namespace) -> None:
    """v8.70:主工作区净化(ship 后 user-dirty 决策的执行入口)。

    治本:ship-finalize step 7 发现主工作区有用户改动时 · 旧逻辑仅「保留 + WARN」·
    停在脏态 · 不 pull 不处理。现在 ship-finalize 会 surface「是否净化」决策 ·
    用户拍板后跑本命令执行选定策略 —— 尽最大努力安全保持主工作区干净 + 最新。

    必在主工作区跑 · 对 merge_target 应用 --strategy:commit-push/stash-pull/skip。
    """
    main_wt = _ship_finalize_precheck()  # 复用主工作区校验(linked worktree → FAIL)
    _, state = load_state(args.feature)
    merge_target = state.get("merge_target") or ""
    if not merge_target:
        emit_json({
            "verdict": "FAIL", "command": "main-sync",
            "error": "state.merge_target 为空 · 无法 main-sync",
            "hint": "确认 Feature 已 init-feature 设 merge_target",
        }, exit_code=1)
    if args.strategy not in MAIN_SYNC_STRATEGIES:
        emit_json(_enum_err("--strategy", args.strategy, MAIN_SYNC_STRATEGIES),
                  exit_code=1)
    artifact_root = Path(args.feature).resolve()

    cur = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=main_wt)
    cur_branch = cur.stdout.strip() if cur.returncode == 0 else ""
    if cur_branch != merge_target:
        emit_json({
            "verdict": "FAIL", "command": "main-sync",
            "error": f"主工作区当前在 {cur_branch!r} 分支 · 非 merge_target {merge_target!r}",
            "hint": f"git checkout {merge_target} · 再跑 state.py main-sync",
        }, exit_code=1)

    f = _git(["fetch", "origin", merge_target], cwd=main_wt, timeout=120)
    if f.returncode != 0:
        emit_json({
            "verdict": "FAIL", "command": "main-sync",
            "error": f"git fetch origin {merge_target} 失败:{f.stderr.strip()[:120]}",
            "hint": "检查网络 / remote 配置 · 修复后重跑",
        }, exit_code=1)

    res = _main_sync_apply_strategy(
        main_wt, merge_target, artifact_root, state, args.strategy,
        message=getattr(args, "message", None))

    emit_json({
        "verdict": "PASS",
        "command": "main-sync",
        "feature_id": state.get("feature_id"),
        "strategy": args.strategy,
        "merge_target": merge_target,
        "main_sync_status": res["status"],
        "main_sync_note": res["note"],
        "pushed": res.get("pushed", False),
        **({"stash_ref": res["stash_ref"]} if res.get("stash_ref") else {}),
        **({"warnings": res["warnings"]} if res["warnings"] else {}),
        "next_action_brief": _main_sync_brief(state, args.strategy, res),
    })


def _finalize_push_fail(ship: dict, reason: str, msg: str) -> tuple:
    """记录 finalize-push 失败到 ship 字段 · 返回 (False, msg)。"""
    ship["merge_target_pushed_at"] = None
    ship["merge_target_push_failed"] = True
    ship["merge_target_push_failed_reason"] = reason
    return False, msg


def _finalize_push_plumbing(repo_cwd: str, artifact_root: Path,
                            state_json_path: Path, merge_target: str,
                            state: dict, ship: dict,
                            extra_files: Optional[list] = None,
                            push_ref: Optional[str] = None,
                            force: bool = False,
                            planning_files: Optional[list] = None) -> tuple:
    """git plumbing 把 state.json(+ extra_files)推到 origin/<merge_target> · 零 checkout。

    v8.18 治本 SVC-CORE-F028 case · 改进:
    - **multi-file 支持**:extra_files=[(repo_rel: str, abs_path: Path), ...] · 一并推
      (典型:review-log.jsonl)· 推完后 worktree 内这些文件与 commit 一致 · 无 delta
    - **去自引用**:不再回写 ship.merge_target_finalize_commit(自引用字段)·
      调用方需要 commit hash 用 emit JSON 顶层 / git log 反查
    - **预设字段**:调用方应在调本函数前预设 ship.merge_target_pushed_at /
      merge_target_push_failed=false · 这样它们已含在推的 commit 里 · 推完无 delta

    流程:hash-object 建 blob → 临时 GIT_INDEX_FILE read-tree base + update-index
    换条目 → write-tree → commit-tree → push <commit>:<merge_target>。
    全程不碰真实 index / 工作区 / HEAD · 不需要 checkout merge_target。

    返回 (ok: bool, warn: str, commit_hash: str)。失败时 commit_hash="" · 已写
    ship.merge_target_push_failed*(失败路径仍写 · 用户/AI 能看到失败状态)。
    """
    feature_id = state.get("feature_id") or "feature"
    extra_files = extra_files or []

    # 1. state.json 的 repo 相对路径(feature worktree 与 merge_target 同仓 · 路径一致)
    pre = _git(["rev-parse", "--show-prefix"], cwd=str(artifact_root))
    if pre.returncode != 0:
        ok, m = _finalize_push_fail(
            ship, "other",
            f"无法解析 state.json repo 相对路径:{pre.stderr.strip()}")
        return ok, m, ""
    repo_prefix = pre.stdout.strip()  # 如 "services/core/docs/features/F028/"
    repo_rel = (repo_prefix + "state.json").lstrip("/")

    # 整理 push entries:state.json + extra_files(每条算绝对路径 + repo 相对)
    push_entries: list = [(repo_rel, state_json_path)]
    for ef_rel_or_abs, ef_abs in extra_files:
        if ef_abs.exists():
            # 若 caller 给的是相对(如 "review-log.jsonl") · 拼 repo_prefix
            if not ef_rel_or_abs.startswith(repo_prefix.lstrip("/")):
                push_entries.append((repo_prefix + ef_rel_or_abs, ef_abs))
            else:
                push_entries.append((ef_rel_or_abs.lstrip("/"), ef_abs))
    # v8.93:规划层 back-ref 文件(已是 repo-root 相对 · 在仓根/其他目录 · 不在 feature 目录下 ·
    # 不拼 feature prefix)随**同一收尾 MR** 合入(archive_on_ship=false 路径也支持)
    for pf_rel, pf_abs in (planning_files or []):
        if pf_abs.exists():
            push_entries.append((pf_rel, pf_abs))

    # 2. base = origin/<merge_target>
    base = _git(["rev-parse", f"origin/{merge_target}"], cwd=repo_cwd)
    if base.returncode != 0:
        ok, m = _finalize_push_fail(
            ship, "other",
            f"无法解析 origin/{merge_target}:{base.stderr.strip()}")
        return ok, m, ""
    base_commit = base.stdout.strip()
    bt = _git(["rev-parse", f"{base_commit}^{{tree}}"], cwd=repo_cwd)
    if bt.returncode != 0:
        ok, m = _finalize_push_fail(
            ship, "other", f"无法解析 base tree:{bt.stderr.strip()}")
        return ok, m, ""
    base_tree = bt.stdout.strip()

    # 3. hash-object 每个文件 → 共享 object DB
    blobs: list = []  # [(repo_rel, blob_hash), ...]
    for prel, pabs in push_entries:
        ho = _git(["hash-object", "-w", str(pabs)], cwd=repo_cwd)
        if ho.returncode != 0:
            ok, m = _finalize_push_fail(
                ship, "other", f"hash-object {prel} 失败:{ho.stderr.strip()}")
            return ok, m, ""
        blobs.append((prel, ho.stdout.strip()))

    # 4. 临时 index 构建新 tree(零 checkout · 不碰真实 index / 工作区)
    tmp_dir = tempfile.mkdtemp(prefix="tw-ship-finalize-")
    idx_path = os.path.join(tmp_dir, "index")  # git 自动创建
    env = {**os.environ, "GIT_INDEX_FILE": idx_path}
    try:
        rt = _git(["read-tree", base_tree], cwd=repo_cwd, env=env)
        if rt.returncode != 0:
            ok, m = _finalize_push_fail(
                ship, "other", f"read-tree 失败:{rt.stderr.strip()}")
            return ok, m, ""
        for prel, blob in blobs:
            ui = _git(["update-index", "--add", "--cacheinfo",
                       f"100644,{blob},{prel}"], cwd=repo_cwd, env=env)
            if ui.returncode != 0:
                ok, m = _finalize_push_fail(
                    ship, "other",
                    f"update-index {prel} 失败:{ui.stderr.strip()}")
                return ok, m, ""
        wtr = _git(["write-tree"], cwd=repo_cwd, env=env)
        if wtr.returncode != 0:
            ok, m = _finalize_push_fail(
                ship, "other", f"write-tree 失败:{wtr.stderr.strip()}")
            return ok, m, ""
        new_tree = wtr.stdout.strip()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # 5. tree 无变化 → merge_target 上已是终态 · 视作已同步
    # ship.merge_target_pushed_at / failed=false 已由 caller 预设 · 此处不再写
    if new_tree == base_tree:
        return True, "", ""

    # 6. commit-tree(单文件 state.json + 状态档 · §12 直推例外)
    extra_note = f" + {len(extra_files)} state file(s)" if extra_files else ""
    plan_note = f" + {len(planning_files)} 规划层文件" if planning_files else ""
    msg = (f"chore({feature_id}): finalize ship state.json{extra_note}{plan_note} "
           f"[teamwork ship-finalize]")
    ct = _git(["commit-tree", new_tree, "-p", base_commit, "-m", msg], cwd=repo_cwd)
    if ct.returncode != 0:
        ok, m = _finalize_push_fail(
            ship, "other", f"commit-tree 失败:{ct.stderr.strip()}")
        return ok, m, ""
    new_commit = ct.stdout.strip()

    # 7. push <commit>:<target_ref>(v8.80:push_ref=收尾分支 时 force · throwaway branch)
    target_ref = push_ref or merge_target
    _push_args = ["push"] + (["--force"] if force else []) + \
        ["origin", f"{new_commit}:{target_ref}"]
    pr = _git(_push_args, cwd=repo_cwd, timeout=120)
    if pr.returncode != 0:
        err = (pr.stderr or "").lower()
        if any(k in err for k in ("protected", "pre-receive", "hook declined", "denied")):
            reason = "protect-rule"
        elif any(k in err for k in ("non-fast-forward", "fetch first", "rejected", "stale info")):
            reason = "conflict"
        elif any(k in err for k in ("could not resolve", "timed out", "timeout", "network", "connection")):
            reason = "network"
        else:
            reason = "other"
        ok, m = _finalize_push_fail(
            ship, reason,
            f"push origin {target_ref} 失败({reason}):{pr.stderr.strip()[:200]}")
        state.setdefault("concerns", []).append(
            f"{now_iso()} WARN ship-finalize finalize-push 失败({reason})· "
            f"merge_target 上 state.json 仍为合并前快照(phase=pushed)· "
            f"重跑 ship-finalize 可重试 · 或手动同步"
        )
        return ok, m, ""

    # 成功:**不再回写自引用字段** · pushed_at / failed=false 已由 caller 预设
    # 返 commit hash 给 caller(emit JSON 顶层用 · 不持久化 state.json · 治本 v8.18)
    return True, "", new_commit


def _ship_finalize_brief(state: dict, ship: dict, finalize_ok: bool,
                         wt_removed: bool, warnings: list,
                         main_sync_decision: Optional[dict] = None,
                         archived: bool = False) -> str:
    """ship-finalize 完成 brief · 全绿一句话 / 有降级则逐条列。

    v8.70:主工作区有用户改动时(main_sync_decision)· 追加「是否净化」暂停点指引 ·
    PMO 须按 SKILL.md R5(b) 转成编号选项暂停点给用户。
    v8.93:规划层 back-ref 翻牌已前移到 finalize-deliver 的 planning-backref 暂停点 · 随收尾 MR
    一起原子合入(治本旧 v8.77 post-step 直推 merge_target 与 v8.80 去直推自相矛盾的隐患)·
    故 PASS 不再追加 post-step 收尾提醒(翻牌此刻已在合入的 MR 里)。
    v8.82:archived=True 时点明过程层 feature 目录已归档(zip)+ 本地已清。
    """
    fid = state.get("feature_id") or "Feature"
    delivered_what = ("过程层 feature 目录已归档(zip 进 _archive/)+ 原目录删 + 本地已清"
                      if archived else "state.json 已同步 merge_target")
    if finalize_ok and wt_removed and not warnings and not main_sync_decision:
        return (
            f"✅ {fid} 已完整 ship · MR 合入已验证 + {delivered_what} "
            f"+ 规划层 back-ref 已随收尾 MR 合入(或已 --no-planning-changes 声明无需翻)"
            f"+ worktree 已清理 · 流程终态 completed。\n"
            f"PMO 向用户汇报 Feature 全流程完成。"
        )
    lines = [f"⚠️ {fid} ship-finalize 完成 · 但有降级项 · PMO 须向用户说明:"]
    for w in warnings:
        lines.append(f"  - {w}")
    if not finalize_ok:
        lines.append(
            "  🔴 state.json 未同步到 merge_target · Feature 已合入但状态记录滞后 · "
            "网络/冲突修复后重跑 state.py ship-finalize(可重入 · 自动跳过已完成步骤)"
        )
    if main_sync_decision:
        rec = main_sync_decision.get("recommended", "stash-pull")
        n = main_sync_decision.get("dirty_count", 0)
        lines.append(
            f"  ⏸️ 主工作区有 {n} 个用户未提交改动 · ship 已完成 · "
            f"PMO 须按 R5(b) 暂停点问用户【是否净化主工作区(保持干净+最新)】· "
            f"选项见 emit.main_sync_decision.options(推荐 {rec})· "
            f"用户拍板后跑对应 state.py main-sync --strategy <id>"
        )
    return "\n".join(lines)


def _resolve_planning_artifacts(main_wt: str, raw_arg: Optional[str],
                                completed: list, skipped: list) -> list:
    """v8.93:解析 --planning-artifacts 逗号分隔路径 → [(repo_rel, abs_path), ...]。

    路径相对主工作区 cwd(或绝对)· 必须**存在** + **在 git 仓内**(随收尾 MR 合入)·
    否则 _ship_finalize_fail(不静默跳过 · 防漏翻 AI 想翻的 back-ref)。空参 → []。
    """
    if not raw_arg:
        return []
    top = _git(["rev-parse", "--show-toplevel"], cwd=main_wt)
    toplevel = Path(top.stdout.strip()).resolve() if top.returncode == 0 else Path(main_wt).resolve()
    resolved: list = []
    for raw in raw_arg.split(","):
        raw = raw.strip()
        if not raw:
            continue
        abs_p = (Path(raw) if os.path.isabs(raw) else (Path(main_wt) / raw)).resolve()
        if not abs_p.exists():
            _ship_finalize_fail(
                "planning-backref",
                f"--planning-artifacts 文件不存在:{raw}",
                "在主工作区改好规划层文件(ROADMAP/WS/teamwork-space.md 等)后再传 · "
                "路径相对主工作区根 · 或用 --no-planning-changes 显式跳过",
                completed, skipped)
        try:
            rel = str(abs_p.relative_to(toplevel))
        except ValueError:
            _ship_finalize_fail(
                "planning-backref",
                f"--planning-artifacts 文件在 git 仓库外:{raw}",
                "规划层文件须在当前 git 仓库内(随收尾 MR 合入 merge_target)",
                completed, skipped)
        resolved.append((rel, abs_p))
    return resolved


def _restore_planning_worktree(main_wt: str, planning_files: list) -> None:
    """v8.93:规划层文件内容已 hash 进收尾分支 → 把主工作区工作树这些文件恢复 HEAD 干净态
    (tracked → checkout HEAD;新建未跟踪 → 删)· 使后续 step7 ff-pull 能干净拉回收尾 MR 的
    最终内容(否则未提交改动会让 ff-pull「would be overwritten by merge」失败)。"""
    for rel, abs_p in planning_files:
        co = _git(["checkout", "HEAD", "--", rel], cwd=main_wt, timeout=15)
        if co.returncode != 0:
            # 不在 HEAD(新建文件)→ 删工作树副本(内容已进收尾分支 · MR 合并后 pull 拉回)
            try:
                if abs_p.exists():
                    abs_p.unlink()
            except OSError:
                pass


def cmd_ship_finalize(args: argparse.Namespace) -> None:
    """ship-finalize:ship Phase 2 全自动编排(8 步 · 可重入 · 失败 AI 干预)。

    v8.16:加 step 0 state-sync(治本 SVC-CORE-B006 case · 把 worktree 内完整态
    state.json 桥接到主工作区 · 详 _step_state_sync 注释)。
    """
    main_wt = _ship_finalize_precheck()
    feature_path = args.feature

    # ── Step 0:state-sync(v8.16 治本)──────────────────────────────
    # 必须在 load_state 之前 · 因为 load_state 会读主工作区 state.json(可能不全 / 不存在)
    sync = _step_state_sync(main_wt, feature_path)
    if not sync["ok"]:
        # v8.82:feature 目录已被归档删除(3rd-run · zip 在 merge_target)→ 幂等成功
        # (state.json 已随目录删 · state-sync 必然 not-found · 但本就是「已交付+已归档」终态)
        if _read_archive_on_ship(feature_path):
            zip_rel = _archive_idempotent_zip(main_wt, feature_path)
            if zip_rel:
                fid = Path(feature_path).name
                # v8.87:幂等也兜底清残留(state.json 没了但 review-log.jsonl 等 untracked 可能残留)
                idem_warn = None
                feat_abs = Path(feature_path).resolve()
                if feat_abs.exists():
                    shutil.rmtree(feat_abs, ignore_errors=True)
                    idem_warn = f"清除残留本地 feature 目录 {feat_abs.name}/(已归档 · zip 是真相)"
                emit_json({
                    "verdict": "PASS",
                    "command": "ship-finalize",
                    "feature_id": fid,
                    "completed_steps": [],
                    "skipped_steps": list(SHIP_FINALIZE_STEPS),
                    "idempotent": True,
                    "archive": zip_rel,
                    "note": ("feature 过程层目录已归档(zip 在 merge_target)· 目录已删 · "
                             "本次 ship-finalize 无需动作(幂等 · 已交付终态)"),
                    **({"warnings": [idem_warn]} if idem_warn else {}),
                    "next_action_brief": (
                        f"✅ {fid} 已完整 ship + 归档(归档物:{zip_rel})· "
                        "流程终态 · 无后续动作。"),
                }, exit_code=0)
        emit_json({
            "verdict": "FAIL",
            "command": "ship-finalize",
            "completed_steps": [],
            "failed_step": "state-sync",
            "error": sync["error"],
            "hint": sync["hint"],
            "sync_action": sync["sync_action"],
            "resume": (
                "修复后重跑 state.py ship-finalize --feature <path> · "
                "可重入(已完成步骤自动跳过)"
            ),
        }, exit_code=1)
    state_sync_action = sync["sync_action"]

    _, state = load_state(feature_path)

    artifact_root = Path(feature_path).resolve()
    state_json_path = artifact_root / "state.json"

    cur_stage = state.get("current_stage")
    if cur_stage not in ("ship", "completed"):
        emit_json({
            "verdict": "FAIL",
            "command": "ship-finalize",
            "error": f"current_stage={cur_stage!r} · 不是 ship",
            "hint": (
                "ship-finalize 是 ship stage Phase 2 编排 · "
                "先确认 pm_acceptance 通过 + ship-start + Phase 1(sanitize/push)完成"
            ),
        }, exit_code=1)

    ship = state.setdefault("ship", {})
    # v8.16:state-sync 已在 step 0 跑完(load_state 之前)· 这里记入 completed
    completed: list = ["state-sync"]
    skipped: list = []
    warnings: list = []

    merge_target = state.get("merge_target") or ""
    feature_head = ship.get("feature_head_commit") or ""
    wt_info = state.get("worktree") or {}
    wt_strategy = wt_info.get("strategy") or "off"
    wt_path_raw = wt_info.get("path") or ""
    wt_branch = (wt_info.get("branch") or "").replace("refs/heads/", "")
    wt_path = (
        str((Path(main_wt) / wt_path_raw).resolve()) if wt_path_raw else ""
    )

    # ── Step 1 + 2:verify-merge → confirm-merged ──────────────────
    if ship.get("phase") == "merged":
        skipped += ["verify-merge", "confirm-merged"]
    else:
        if ship.get("phase") not in (None, "pushed"):
            _ship_finalize_fail(
                "verify-merge",
                f"ship.phase={ship.get('phase')!r} · 非 pushed · 无法 finalize",
                "phase=closed_unmerged → MR 已关闭 · 走 ship-phase --action push "
                "重开 · 或放弃 Feature",
                completed, skipped,
            )
        if not feature_head:
            _ship_finalize_fail(
                "verify-merge", "ship.feature_head_commit 缺失",
                "Phase 1 未完成 · 先跑 ship-phase --action push(push feature 分支 + 创 MR)",
                completed, skipped,
            )
        if not merge_target:
            _ship_finalize_fail(
                "verify-merge", "state.merge_target 缺失",
                "state.json 无 merge_target · 检查 init-feature 参数",
                completed, skipped,
            )

        # git fetch
        fr = _git(["fetch", "origin", merge_target], cwd=main_wt, timeout=120)
        if fr.returncode != 0:
            _ship_finalize_fail(
                "verify-merge",
                f"git fetch origin {merge_target} 失败:{fr.stderr.strip()[:200]}",
                "检查网络 / origin 远程 / merge_target 分支名 · 修复后重跑",
                completed, skipped,
            )

        # 合入检测
        if args.merge_commit_hash:
            merge_commit = args.merge_commit_hash
            detection = "user-reported"
        else:
            anc = _git(["merge-base", "--is-ancestor", feature_head,
                        f"origin/{merge_target}"], cwd=main_wt)
            if anc.returncode != 0:
                _ship_finalize_fail(
                    "verify-merge",
                    f"feature_head_commit {feature_head[:12]} 不在 "
                    f"origin/{merge_target} 中 · 自动检测未确认合入",
                    (
                        "两种可能 · 请向用户确认后处理:\n"
                        "  ① MR 尚未合并 → 等用户在平台合并后 · 重跑 state.py ship-finalize\n"
                        "  ② squash / rebase 合并(commit hash 已变 · branch-contains 检测不到)\n"
                        "     → 用户确认已合并后 · 重跑 state.py ship-finalize "
                        "--feature <path> --merge-commit-hash <merge_target 上的合并 commit>"
                    ),
                    completed, skipped,
                )
            detection = "branch-contains"
            mc = _git(["rev-list", "--merges", "--ancestry-path",
                       f"{feature_head}..origin/{merge_target}"], cwd=main_wt)
            merges = [ln.strip() for ln in mc.stdout.splitlines() if ln.strip()]
            merge_commit = merges[-1] if merges else feature_head

        completed.append("verify-merge")

        # confirm-merged
        ship["phase"] = "merged"
        ship["shipped"] = "merged"
        ship["merge_commit_hash"] = merge_commit
        ship["merge_detection_method"] = detection
        ship["mr_merged_at"] = ship.get("mr_merged_at") or now_iso()
        if detection == "user-reported":
            warnings.append(
                f"merge_detection_method=user-reported · 用户自报合并"
                f"(merge_commit={merge_commit[:12]})· 自动 git 校验未执行"
            )
            state.setdefault("concerns", []).append(
                f"{now_iso()} INFO ship-finalize: user-reported "
                f"merge_commit={merge_commit}"
            )
        completed.append("confirm-merged")

    # ── Step 3:cleanup(状态字段 · 物理删在 step 6)─────────────────
    if ship.get("worktree_cleanup") in ("cleaned", "n_a"):
        skipped.append("cleanup")
    else:
        if wt_strategy == "off" or not wt_path:
            ship["worktree_cleanup"] = "n_a"
        else:
            ship["worktree_cleanup"] = "cleaned"  # step 6 物理删 · 失败则降级 deferred
        completed.append("cleanup")

    # ── Step 4:ship-complete ───────────────────────────────────────
    if state.get("current_stage") == "completed":
        skipped.append("ship-complete")
    else:
        contracts = state.setdefault("stage_contracts", {})
        contract = contracts.setdefault("ship", {})
        contract.setdefault("started_at", ship.get("started_at") or now_iso())
        contract["input_satisfied"] = True
        contract["process_satisfied"] = True
        contract["output_satisfied"] = True
        contract["completed_at"] = now_iso()
        contract["auto_commit"] = feature_head or git_head(cwd=main_wt) or ""
        contract.setdefault("artifacts", [])
        state["current_stage"] = "completed"
        state["legal_next_stages"] = []
        cs = state.setdefault("completed_stages", [])
        if "ship" not in cs:
            cs.append("ship")
        try:
            write_review_log_entry(state, artifact_root, "ship", "completed", contract)
        except Exception:
            pass
        completed.append("ship-complete")

    # ── Step 5:finalize-deliver(v8.80 去直推 · v8.82 加归档本体)──
    # 旧(≤v8.79):plumbing 直推 state.json 到 merge_target(§12 例外)。
    # v8.80:终态暂存到 ship-finalize/<id> 分支 → 交接 AI 用 gh/glab 创 MR + 自动合 → 重跑续 step6/7。
    # v8.82(archive_on_ship · 默认 true):收尾分支不止同步 state.json · 而是把交付的**过程层**
    #   feature 目录 zip 进 features/_archive/<id>.zip(+ INDEX.md)· 并从 merge_target 删原目录
    #   (防 AI 检索过时 feature 信息 · 代码是唯一真相)· 随同一收尾 MR 合入。
    #   已交付判定 = zip 在 origin/merge_target 存在(抗 squash)。archive_on_ship=false → 退回 v8.80
    #   行为(state.json 终态同步 · current_stage==completed 判定 · 目录留存)。
    # 🔴 不持久化额外字段:本地 state.json(step 1-4 终态)== 交付内容 → step 7 pull 不分叉冲突。
    finalize_ok = True
    finalize_commit_hash = ""
    archive_delivered = False  # v8.82:archive 模式 + 已交付 → step 7 需清本地 feature 目录
    feature_id = state.get("feature_id") or artifact_root.name
    sf_branch = f"ship-finalize/{feature_id}"
    sf_ref = f"refs/heads/{sf_branch}"
    archive_on = _read_archive_on_ship(str(artifact_root))
    save_state(state_json_path, state)  # 落盘终态(step 1-4 字段)
    _git(["fetch", "origin", merge_target], cwd=main_wt, timeout=120)
    if archive_on:
        delivered = _remote_archive_delivered(main_wt, artifact_root, feature_id, merge_target)
    else:
        delivered = _remote_finalize_delivered(main_wt, artifact_root, merge_target)
    if delivered:
        # 收尾 MR 已合 → 交付 · 清理残留收尾分支(best-effort)
        archive_delivered = archive_on
        _git(["push", "origin", "--delete", sf_branch], cwd=main_wt, timeout=60)
        completed.append("finalize-deliver")
    else:
        # v8.93:收尾交付前先翻规划层 back-ref · 随**同一收尾 MR** 合入(治本旧 §5.5 post-step
        # 直推 merge_target —— 与 v8.80「去直推」自相矛盾 · 保护分支被拒 · 且收尾 MR 早已关闭 →
        # 规划层物理塞不进 → 非原子 + 直推隐患)。三态:① 收尾分支已暂存 → reuse(不 amend)·
        # ② 规划未决定且未暂存 → planning gate · ③ 规划已决定 → 暂存 {zip + 规划文件} 一次。
        planning_files = _resolve_planning_artifacts(
            main_wt, getattr(args, "planning_artifacts", None), completed, skipped)
        planning_decided = bool(planning_files) or getattr(args, "no_planning_changes", False)
        _git(["fetch", "origin", sf_branch], cwd=main_wt, timeout=60)  # 收尾分支(可能不存在)
        sf_remote = _git(["rev-parse", "--verify", "--quiet", f"origin/{sf_branch}"],
                         cwd=main_wt)
        sf_exists = sf_remote.returncode == 0 and bool(sf_remote.stdout.strip())
        if sf_exists:
            # 已暂存但未合(上一轮已含规划决定)→ reuse · 🔴 不 amend(一次打包一个 MR)
            finalize_commit_hash = sf_remote.stdout.strip()
            if planning_files:
                warnings.append(
                    f"收尾分支 {sf_branch} 已存在(上一轮暂存)· 本次 --planning-artifacts 未重新打包"
                    f"(本设计不 amend 已暂存分支)· 如需变更收尾内容:先 "
                    f"git push origin --delete {sf_branch} 再重跑 --planning-artifacts")
            _ship_finalize_deliver_pending(
                feature_path, merge_target, sf_branch, finalize_commit_hash,
                completed, skipped, warnings, archived=archive_on)  # emit PENDING + exit
        elif not planning_decided:
            # gate:收尾分支未暂存 + 规划决定未给 → 先翻规划层 back-ref(judgment 活 · AI 自决)
            _ship_finalize_planning_pending(
                feature_path, merge_target, completed, skipped, warnings)  # emit PENDING + exit
        else:
            # 规划已决定(翻牌文件 或 --no-planning-changes)→ 暂存收尾 commit(含规划文件)+ push
            planning_rels = [rel for rel, _ in planning_files]
            # v8.94:极简 feature 描述(≤50 字)写入归档 INDEX.md(便于不解压识别归档内容)
            raw_desc = getattr(args, "archive_desc", None)
            archive_desc = _clean_archive_desc(raw_desc)
            if raw_desc and len(" ".join(str(raw_desc).split()).replace("|", "/")) > 50:
                warnings.append(
                    f"--archive-desc 超 50 字 · 已截断为「{archive_desc}」写入 INDEX.md")
            if archive_on:
                ok, warn, commit = _stage_archive_commit(
                    main_wt, artifact_root, feature_id, merge_target, sf_ref,
                    planning_files=planning_files, archive_desc=archive_desc)
            else:
                review_log_path = artifact_root / "review-log.jsonl"
                extra = ([("review-log.jsonl", review_log_path)]
                         if review_log_path.exists() else [])
                ok, warn, commit = _finalize_push_plumbing(
                    main_wt, artifact_root, state_json_path, merge_target, state, ship,
                    extra_files=extra, push_ref=sf_ref, force=True,
                    planning_files=planning_files)
            if not ok:
                _ship_finalize_fail(
                    "finalize-deliver",
                    f"暂存收尾分支 {sf_branch} 失败:{warn}",
                    "检查网络 / origin 远程 / 推送权限 · 修复后重跑 ship-finalize",
                    completed, skipped)
            # 规划层内容已 hash 进收尾分支 → 还原工作树(防 step7 ff-pull「would be overwritten」冲突)
            if planning_files:
                _restore_planning_worktree(main_wt, planning_files)
            if not commit:
                # 无 delta(罕见)→ 终态已在 merge_target → 已交付
                completed.append("finalize-deliver")
            else:
                finalize_commit_hash = commit
                _ship_finalize_deliver_pending(
                    feature_path, merge_target, sf_branch, commit,
                    completed, skipped, warnings, archived=archive_on,
                    planning_bundled=planning_rels)  # emit PENDING + exit

    # ── Step 6:worktree-remove(物理删 · state.json 已推远端 · 不丢)──
    # v8.80:走到这步即收尾 MR 已合并(未合并时 step 5 已 emit PENDING + return)·
    # 故 worktree-remove + main-sync 必在「收尾 MR 合并之后」· 不再有 finalize-push 失败保留分支
    wt_removed = False
    if wt_strategy == "off" or not wt_path:
        skipped.append("worktree-remove")
        wt_removed = True
    else:
        still_there = any(
            _same_path(w.get("path"), wt_path) for w in _list_worktrees(main_wt)
        )
        if not still_there:
            skipped.append("worktree-remove")
            wt_removed = True
        else:
            rm = _git(["worktree", "remove", "--force", wt_path],
                      cwd=main_wt, timeout=60)
            if rm.returncode != 0:
                warnings.append(
                    f"git worktree remove 失败:{rm.stderr.strip()[:150]} · "
                    f"state.json 已 finalize 到 merge_target(不丢)· "
                    f"手动 git worktree remove --force {wt_path}"
                )
                ship["worktree_cleanup"] = "deferred"
                save_state(state_json_path, state)
            else:
                wt_removed = True
                completed.append("worktree-remove")
                if wt_branch:
                    bd = _git(["branch", "-d", wt_branch], cwd=main_wt)
                    if bd.returncode != 0:
                        warnings.append(
                            f"本地 feature 分支 {wt_branch} 未删(可能未完全合并)· "
                            f"确认已合入后手动 git branch -D {wt_branch}"
                        )

    # ── Step 7:main-sync(v8.31 智能 dirty 处理 · 治本主工作区残留 case)──
    # 治本:ship Phase 2 完成后 · 主工作区本地 merge_target 分支仍停在旧 commit ·
    # 与 origin/merge_target(已含 MR 合并 + finalize-push)脱节。
    # v8.16:能快进则快进 · 分叉/脏树则安全跳过 + WARN · 不强 merge。
    # v8.31:dirty 分类 · 若 dirty 全是工具副产物(feature artifacts + bootstrap
    # 注入段 + harness 锁)→ stash+ff-pull+unstash 安全自动同步;若含用户真改动 → 跳过。
    main_sync_status = "skipped"
    main_sync_note = ""
    main_sync_decision: Optional[dict] = None  # v8.70:普通模式 user-dirty 时的「是否净化」决策
    f2 = _git(["fetch", "origin", merge_target], cwd=main_wt, timeout=120)
    if f2.returncode != 0:
        warnings.append(
            f"主工作区 git fetch origin {merge_target} 失败:"
            f"{f2.stderr.strip()[:120]} · 非致命 · 手动 git fetch 即可"
        )
        main_sync_status = "fetch_failed"
        main_sync_note = f"fetch fail · 网络/remote 问题:{f2.stderr.strip()[:80]}"
    else:
        completed.append("main-sync")
        cur = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=main_wt)
        cur_branch = cur.stdout.strip() if cur.returncode == 0 else ""
        if cur_branch != merge_target:
            warnings.append(
                f"主工作区当前在 {cur_branch!r} 分支(非 {merge_target})· 已 fetch 未 pull · "
                f"需要时自行 git checkout {merge_target} && git pull --ff-only"
            )
            main_sync_status = "wrong_branch"
            main_sync_note = (f"在 {cur_branch!r} 分支 · 非 {merge_target} · "
                              f"已 fetch · 需要时自行切分支 + pull")
        else:
            # v8.82:归档已交付 → 先把本地 feature 目录恢复 HEAD 干净态(restore tracked +
            # clean untracked)· 内容已进 zip · 让随后的 ff-pull 能干净删除该目录(origin 已删)·
            # 否则本地终态改动会让 ff-pull「would be overwritten by merge」失败 / 残留脏目录。
            if archive_delivered:
                feat_paths = _archive_repo_paths(main_wt, artifact_root, feature_id)
                if feat_paths:
                    warnings.extend(
                        _purge_local_feature_dir_for_archive(main_wt, feat_paths[0]))
            # v8.31 dirty 分类 + 智能 stash 处理
            # v8.33 fix:用 artifact_root(line 1097 已定义)· v8.31 误传 feature_dir(NameError)
            dirty_result = _classify_main_sync_dirty(main_wt, artifact_root, state)
            if not dirty_result["is_dirty"]:
                # clean · 直接 ff-pull(原 v8.16 路径)
                pl = _git(["pull", "--ff-only", "origin", merge_target],
                          cwd=main_wt, timeout=120)
                if pl.returncode != 0:
                    warnings.append(
                        f"主工作区 {merge_target} 与 origin 分叉 · git pull --ff-only 未通过 · "
                        f"已 fetch · 需手动 rebase/merge:{pl.stderr.strip()[:120]}"
                    )
                    main_sync_status = "diverged"
                    main_sync_note = f"分叉 · 需手动 rebase:{pl.stderr.strip()[:80]}"
                else:
                    main_sync_status = "ff_pulled"
                    main_sync_note = "主工作区已 ff-pull 到最新"
            elif dirty_result["safe_to_stash"]:
                # v8.32 治本(修 v8.31 stash 全部撞 feature_artifacts pop 冲突 bug):
                # 分类型处理 · 不一刀切 stash 全部
                # ① feature_artifacts:本地必旧(ship-finalize 是最权威推送 · origin 有新版)
                #    → git checkout origin/<merge_target> -- <files>(丢本地 · 用 origin 新版)
                # ② bootstrap_pointers + harness_locks:origin 不改这些文件 · stash 仅这些 + pop 安全
                checkout_failed = []
                for f in dirty_result["feature_artifacts"]:
                    co = _git(["checkout", f"origin/{merge_target}", "--", f],
                              cwd=main_wt, timeout=15)
                    if co.returncode != 0:
                        checkout_failed.append((f, co.stderr.strip()[:80]))

                if checkout_failed:
                    warnings.append(
                        f"git checkout origin/{merge_target} -- 失败"
                        f"({len(checkout_failed)} 文件)· 跳过 ff-pull · 手动处理:"
                        f"{', '.join(f for f, _ in checkout_failed)}"
                    )
                    main_sync_status = "checkout_failed"
                    main_sync_note = "feature_artifacts checkout 失败 · 未 ff-pull"
                else:
                    # feature_artifacts 已用 origin 版本覆盖 · 现 dirty 只剩 bootstrap + locks
                    remaining = (dirty_result["bootstrap_pointers"]
                                 + dirty_result["harness_locks"])
                    if not remaining:
                        # working tree 等价 clean(checkout 后本地 = origin 新版)
                        pl = _git(["pull", "--ff-only", "origin", merge_target],
                                  cwd=main_wt, timeout=120)
                        if pl.returncode != 0:
                            warnings.append(
                                f"feature_artifacts 已 checkout · 但 ff-pull 失败(分叉):"
                                f"{pl.stderr.strip()[:120]}"
                            )
                            main_sync_status = "diverged"
                            main_sync_note = (
                                "feature_artifacts 已用 origin 覆盖 · 但分叉 · 需手动 rebase")
                        else:
                            main_sync_status = "checkout_pulled"
                            main_sync_note = (
                                f"v8.32:checkout {len(dirty_result['feature_artifacts'])} "
                                f"个 feature_artifacts(本地旧 → origin 新)· ff-pull · "
                                f"主工作区 clean 且最新"
                            )
                    else:
                        # stash 仅 bootstrap + locks(不含 feature_artifacts · 已 checkout)
                        # git stash push -u -m <msg> -- <pathspec>(stash 指定路径 · 含 untracked)
                        stash_msg = "teamwork ship-finalize v8.32 step 7 auto-stash"
                        st = _git(["stash", "push", "-u", "-m", stash_msg, "--",
                                   *remaining], cwd=main_wt, timeout=30)
                        if st.returncode != 0:
                            warnings.append(
                                f"git stash 失败:{st.stderr.strip()[:100]} · "
                                f"feature_artifacts 已 checkout · 但 stash 剩余失败 · "
                                f"手动处理:{', '.join(remaining[:5])}"
                            )
                            main_sync_status = "stash_failed_after_checkout"
                            main_sync_note = "feature_artifacts checkout 成功 · 但剩余 stash 失败"
                        else:
                            pl = _git(["pull", "--ff-only", "origin", merge_target],
                                      cwd=main_wt, timeout=120)
                            pop = _git(["stash", "pop"], cwd=main_wt, timeout=30)
                            if pl.returncode != 0:
                                warnings.append(
                                    f"feature_artifacts checkout 成功 · ff-pull 失败(分叉)· "
                                    f"stash 已 pop · 需手动 rebase:{pl.stderr.strip()[:120]}"
                                )
                                main_sync_status = "diverged_stash_popped"
                                main_sync_note = "分叉 · 需手动 rebase"
                            elif pop.returncode != 0:
                                # bootstrap/lock pop 冲突极罕(origin 通常不改这些)
                                warnings.append(
                                    f"feature_artifacts checkout + ff-pull 成功 · "
                                    f"但 bootstrap/lock stash pop 冲突 · stash 保留 · "
                                    f"git stash list / git stash pop 手动:"
                                    f"{pop.stderr.strip()[:120]}"
                                )
                                main_sync_status = "pulled_unstash_conflict"
                                main_sync_note = (
                                    "已 ff-pull · bootstrap/lock unstash 冲突 stash 保留(罕见)"
                                )
                            else:
                                main_sync_status = "checkout_stashed_pulled_unstashed"
                                main_sync_note = (
                                    f"v8.32:checkout {len(dirty_result['feature_artifacts'])} "
                                    f"个 feature_artifacts(本地旧 → origin 新)+ "
                                    f"stash {len(remaining)} 个 bootstrap/lock + ff-pull + pop · "
                                    f"feature_artifacts clean · bootstrap/lock 保留原 dirty"
                                    f"(等用户 commit / G2 ignore)"
                                )
            else:
                # v8.70 治本(用户实证):主工作区有用户真改动时 · 旧逻辑(v8.62)是
                # 「清 feature_artifacts + 尽力 ff-pull + 静默保留用户改动 + WARN」——
                # 主工作区停在脏态 · 不主动处理 · 用户得手动 commit/stash/pull。改为:
                #   auto/yolo(无人值守)→ 安全自动净化 stash-pull(改动留 stash · 无数据丢失 ·
                #                          不推任意改动到集成分支 · 保持干净+最新);
                #   普通模式 → surface「是否净化」决策(提示)· 用户拍板后跑 state.py main-sync。
                # 两路都先清 feature_artifacts(origin 版 · 总安全)· 见 _main_sync_apply_strategy。
                if state.get("auto_mode") or state.get("yolo"):
                    res = _main_sync_apply_strategy(
                        main_wt, merge_target, artifact_root, state, "stash-pull")
                    main_sync_status = f"auto_{res['status']}"
                    main_sync_note = "无人值守自动净化(stash-pull)· " + res["note"]
                    warnings.extend(res["warnings"])
                else:
                    # 仍做安全清理(feature_artifacts + 尽力 ff-pull · 同 v8.62)· 但不动用户改动
                    res = _main_sync_apply_strategy(
                        main_wt, merge_target, artifact_root, state, "skip")
                    warnings.extend(res["warnings"])
                    main_sync_status = "user_dirty_decision"
                    main_sync_note = (
                        f"主工作区有 {len(dirty_result['other_files'])} 个用户改动 · "
                        + res["note"]
                        + " · ⏸️ 等用户决策是否净化(见 main_sync_decision)")
                    main_sync_decision = _build_main_sync_decision(
                        feature_path, merge_target, state, dirty_result,
                        res.get("pulled", False))

    # ── v8.87:archive 已交付的最终保证 —— 本地 feature 目录绝不残留 ──
    # 治本:ff-pull 被跳过(主工作区脏 / 分叉 / 非 merge_target)或 lingering worktree 把
    # state.json resurrect 回来 → 主工作区残留 `<feature_dir>/{state.json,review-log.jsonl}`
    # (实证 SVC-F001:_archive/<id>.zip 已在 · 但原 feature 目录仍带 state/review-log)。
    # zip 是真相 → 在 merge_target 上强制物理清除残留目录(git rm staged · 下次 pull 自愈)。
    if archive_delivered:
        cb = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=main_wt)
        on_mt = cb.returncode == 0 and cb.stdout.strip() == merge_target
        fp = _archive_repo_paths(main_wt, artifact_root, feature_id)
        if on_mt and fp:
            feat_abs = Path(main_wt) / fp[0]
            if feat_abs.exists():
                # tracked → git rm(index+worktree · staged 删)· 残余 untracked → rmtree
                _git(["rm", "-r", "-f", "--quiet", "--ignore-unmatch", fp[0]], cwd=main_wt)
                if feat_abs.exists():
                    shutil.rmtree(feat_abs, ignore_errors=True)
                warnings.append(
                    f"archive 已交付 · 本地 feature 目录 {fp[0]} 残留(ff-pull 未删/被跳过)→ "
                    f"已强制清除(zip 是真相 · 防主工作区残留 state.json/review-log.jsonl)")

    emit_json({
        "verdict": "PASS",
        "command": "ship-finalize",
        "feature_id": state.get("feature_id"),
        "completed_steps": completed,
        "skipped_steps": skipped,
        "ship_phase": ship.get("phase"),
        "ship_shipped": ship.get("shipped"),
        "merge_commit_hash": ship.get("merge_commit_hash"),
        "current_stage": state.get("current_stage"),
        "finalize_push": ("ok" if finalize_ok
                          else f"failed:{ship.get('merge_target_push_failed_reason')}"),
        # v8.18:finalize_commit 放 emit 顶层(不持久化 state.json · 治本 SVC-CORE-F028 自引用残留)
        # AI 想查 audit · 从 emit 看 / git log origin/<merge_target> 反查
        **({"finalize_commit": finalize_commit_hash} if finalize_commit_hash else {}),
        # v8.82:归档已交付(过程层 feature 目录已 zip 进 _archive/ + 删原目录 + 本地已清)
        **({"archived": True} if archive_delivered else {}),
        "worktree_removed": wt_removed,
        # v8.16:state-sync 透明留痕(干了啥)· 治本 SVC-CORE-B006 case
        "state_sync_action": state_sync_action,
        # v8.31 · step 7 智能 dirty 处理透明留痕(治本 G4 主工作区残留误判)
        "main_sync_status": main_sync_status,
        **({"main_sync_note": main_sync_note} if main_sync_note else {}),
        # v8.70 · 普通模式 user-dirty 时的「是否净化」决策(PMO 转 R5(b) 暂停点)
        **({"main_sync_decision": main_sync_decision} if main_sync_decision else {}),
        # v8.93 · 规划层 back-ref 已前移到 finalize-deliver 的 planning-backref 暂停点(随收尾 MR
        # 合入)· 此处不再 emit planning_backref_pending(翻牌此刻已在已合的 MR 里 · 非 post-step)
        **({"warnings": warnings} if warnings else {}),
        "next_action_brief": _ship_finalize_brief(
            state, ship, finalize_ok, wt_removed, warnings,
            main_sync_decision, archived=archive_delivered),
    })


# ─── argparse 注册 ──────────────────────────────────────────────


def register_v8_ship_subparser(sub) -> None:
    """在 state.py argparse subparsers 上注册 ship-phase 命令。"""
    sp = sub.add_parser(
        "ship-phase",
        help="[v8] ship 内部子动作 · 统一入口(替代 v7 ship-sanitize/push/confirm-merged/cleanup/closed)",
    )
    sp.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    sp.add_argument("--action", required=True, choices=list(SHIP_ACTIONS),
                    help="子动作 · schema 见 state.py --help + _v8_stage_specs.py SHIP_SPEC")

    # action=sanitize 参数
    sp.add_argument("--residual-commits",
                    help="[sanitize] JSON · [{commit,files,reason}] · 残留 commit 列表")
    sp.add_argument("--cleaned-files",
                    help="[sanitize] 逗号分隔 · 已净化文件白名单")
    sp.add_argument("--suspicious-files",
                    help="[sanitize] JSON · [{path,reason}] · 灰名单文件")
    sp.add_argument("--distill",
                    help=("[sanitize · v8.81 必填] JSON · ship1 知识沉淀 6 项决策 "
                          "{knowledge,adr,reg,retro,architecture,db_schema} · "
                          "每项 'updated/promoted <what>' 或 'none'/'n/a' · 详 ship-stage.md §13"))

    # action=push 参数
    sp.add_argument("--feature-head-commit",
                    help="[push] push 后的 feature 分支 head commit hash")
    sp.add_argument("--git-host", choices=list(SHIP_GIT_HOSTS),
                    help="[push] git host enum")
    sp.add_argument("--mr-creation-method", choices=list(SHIP_MR_METHODS),
                    help="[push] MR 创建方式")
    sp.add_argument("--mr-url",
                    help="[push] CLI 实创建 URL(cli-* method 必传)")
    sp.add_argument("--mr-create-url",
                    help="[push] 兜底 URL(url-fallback / unknown-platform 必传)")
    sp.add_argument("--feature-pushed-at",
                    help="[push] ISO 8601 · 缺省 now")
    # v8.37 url-fallback 退化逃生口(治本 SVC-CORE-B007 case)
    sp.add_argument("--accept-cli-unavailable", action="store_true",
                    help=("[push] v8.37 逃生口 · 显式承认 git_host 对应 CLI 不可用 "
                          "(否则 CLI 装好+认证 OK 时 url-fallback 会 BLOCK)· "
                          "必带 --reason '<原因>' --user-confirmed"))
    sp.add_argument("--user-confirmed", action="store_true",
                    help=("[push] v8.37 bypass 时必带 · 标记用户已确认逃生 "
                          "(防 AI 自决)· 与 stage-start --user-confirmed pattern 一致"))

    # action=confirm-merged 参数
    sp.add_argument("--merge-commit-hash",
                    help="[confirm-merged] 合入到 merge_target 的 merge commit hash")
    sp.add_argument("--merge-detection-method", choices=list(SHIP_DETECTION_METHODS),
                    help="[confirm-merged] 合入检测方式")
    sp.add_argument("--mr-merged-at",
                    help="[confirm-merged] ISO 8601 · 缺省 now")
    sp.add_argument("--merge-target-pushed-at",
                    help="[confirm-merged] finalize-push 成功时间")
    sp.add_argument("--merge-target-push-failed", action="store_true",
                    help="[confirm-merged] finalize-push 失败")
    sp.add_argument("--failed-reason", choices=list(SHIP_FINALIZE_PUSH_REASONS),
                    help="[confirm-merged] 失败原因 · 失败时必传")

    # action=cleanup 参数
    sp.add_argument("--status", choices=list(SHIP_CLEANUP_ENUM),
                    help="[cleanup] worktree 清理状态 · cleaned 必须 phase=merged")

    # action=close-unmerged 参数
    sp.add_argument("--abandon", action="store_true",
                    help="[close-unmerged] 彻底放弃 Feature → shipped=abandoned")
    sp.add_argument("--reason",
                    help="[close-unmerged] INFO concerns 说明")

    sp.set_defaults(func=cmd_ship_phase)

    # ─── ship-finalize:Phase 2 全自动编排(7 步一条命令)───────────
    fp = sub.add_parser(
        "ship-finalize",
        help=("[v8] ship Phase 2 全自动编排 · 一条命令跑 7 步"
              "(验证合入→confirm-merged→cleanup→ship-complete→finalize 直推"
              "→worktree 删→主工作区 fetch)· 可重入 · 必在主工作区跑"),
    )
    fp.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    fp.add_argument("--merge-commit-hash",
                    help=("squash / rebase 合并(branch-contains 自动检测不到)时 · "
                          "用户确认的 merge_target 上合并 commit hash · "
                          "传则检测方式记为 user-reported"))
    fp.add_argument("--planning-artifacts",
                    help=("[v8.93] 逗号分隔 · 规划层 back-ref 翻牌文件相对路径"
                          "(ROADMAP.md / workstream/WS-NN.md / teamwork-space.md / 变更单 等)· "
                          "随**同一收尾 MR** 与归档 zip 原子合入(去 §5.5 直推)· "
                          "AI 在 planning-backref 暂停点判断哪些要翻 · 改好后传入"))
    fp.add_argument("--no-planning-changes", action="store_true",
                    help=("[v8.93] 显式声明本 Feature 无规划层 back-ref 可翻"
                          "(ad-hoc Bug/Micro · 无关联 BL)· 跳过 planning-backref 暂停点 · "
                          "收尾 MR 只含归档 zip + state.json"))
    fp.add_argument("--archive-desc",
                    help=("[v8.94] 极简 feature 描述(**≤50 字** · 超则截断)· 写入归档 "
                          "_archive/INDEX.md 的「描述」列 · 便于日后不解压就识别归档内容 · "
                          "AI 在 planning-backref 暂停点连同 --planning-artifacts 一起给"))
    fp.set_defaults(func=cmd_ship_finalize)

    # ─── main-sync:主工作区净化(v8.70)─────────────────────────────
    # 治本:ship-finalize step 7 发现主工作区有用户改动时 · 旧逻辑仅「保留 + WARN」·
    # 停在脏态。现在 ship-finalize surface「是否净化」决策 · 用户拍板后跑本命令执行。
    ms = sub.add_parser(
        "main-sync",
        help=("[v8.70] 主工作区净化 · ship 后 user-dirty 决策执行入口 · "
              "--strategy commit-push/stash-pull/skip · 必在主工作区跑"),
    )
    ms.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    ms.add_argument("--strategy", required=True, choices=list(MAIN_SYNC_STRATEGIES),
                    help=("净化策略:commit-push(git add -A + commit + pull --rebase + "
                          "push · 推改动到 merge_target)/ stash-pull(stash + ff-pull · "
                          "改动留 stash 可恢复 · 不推送)/ skip(保留改动 · 仅清 "
                          "feature_artifacts + 尽力 ff-pull)"))
    ms.add_argument("--message",
                    help="[commit-push] 自定义 commit message(缺省自动生成)")
    ms.set_defaults(func=cmd_main_sync)
