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

设计哲学见 docs/v8-redesign/00-MANIFESTO.md。
ship-phase schema 见 docs/v8-redesign/01-COMMAND-SCHEMA.md B11。
v8.W2 实现 · 取代 v7 ship-*(W3 减负时物理删除 v7 ship-* 子命令)。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from _v8_engine import emit_json, load_state, now_iso, save_state, require_user_confirmed


# ─── 常量 ──────────────────────────────────────────────────────────────


SHIP_ACTIONS = ("sanitize", "push", "confirm-merged", "cleanup", "close-unmerged")

SHIP_PHASE_ENUM = (None, "pushed", "merged", "closed_unmerged")
SHIP_SHIPPED_ENUM = (None, "pushed", "merged", "closed_unmerged", "abandoned", "failed")
SHIP_GIT_HOSTS = ("github", "gitlab", "gitlab-self-hosted", "gitee", "bitbucket", "unknown")
SHIP_MR_METHODS = ("cli-gh", "cli-glab", "url-fallback", "unknown-platform")
SHIP_DETECTION_METHODS = ("branch-contains", "user-reported")
SHIP_FINALIZE_PUSH_REASONS = ("conflict", "protect-rule", "network", "other")
SHIP_CLEANUP_ENUM = ("cleaned", "deferred", "n_a")


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


def _handle_ship_sanitize(state: dict, args: argparse.Namespace) -> dict:
    """Step 1:净化 commit 记录 · 不改 ship.phase。"""
    ship = state.setdefault("ship", {})
    ship.setdefault("started_at", now_iso())

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
        "warnings": warnings,
        "next_action_brief": (
            "✅ 净化完成。下一步:"
            "state.py ship-phase --action push --feature <path> "
            "--feature-head-commit <hash> --git-host <host> "
            "--mr-creation-method <method> --mr-url/mr-create-url <url>"
        ),
    }


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


# ─── argparse 注册 ──────────────────────────────────────────────


def register_v8_ship_subparser(sub) -> None:
    """在 state.py argparse subparsers 上注册 ship-phase 命令。"""
    sp = sub.add_parser(
        "ship-phase",
        help="[v8] ship 内部子动作 · 统一入口(替代 v7 ship-sanitize/push/confirm-merged/cleanup/closed)",
    )
    sp.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    sp.add_argument("--action", required=True, choices=list(SHIP_ACTIONS),
                    help="子动作 · 详细 schema 见 docs/v8-redesign/01-COMMAND-SCHEMA.md B11")

    # action=sanitize 参数
    sp.add_argument("--residual-commits",
                    help="[sanitize] JSON · [{commit,files,reason}] · 残留 commit 列表")
    sp.add_argument("--cleaned-files",
                    help="[sanitize] 逗号分隔 · 已净化文件白名单")
    sp.add_argument("--suspicious-files",
                    help="[sanitize] JSON · [{path,reason}] · 灰名单文件")

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
