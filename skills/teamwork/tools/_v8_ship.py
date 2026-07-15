"""
_v8_ship.py — Teamwork v8.0 ship-phase 子动作实现。

替代 v7 的 5 个独立 ship-* 命令(ship-sanitize / ship-push / ship-confirm-merged /
ship-cleanup / ship-closed),改为统一的 `ship-phase --action <name>`。

action 枚举:
- sanitize:           净化 commit 记录(不改 phase)
- push:               null/closed_unmerged → pushed · 含 git-host + MR 创建
- archive(v8.145):  ship1 终幕 · 归档+翻牌进 feature 分支(null → archived)
- close-unmerged:     pushed → closed_unmerged 或 abandoned

设计哲学:v8.0 设计稿已清理(git 历史可溯)。
ship-phase schema 现行权威 = state.py --help + _v8_stage_specs.py SHIP_SPEC
(v8.0 命令 schema 快照已清理 · git 历史可溯)。
v8.W2 实现 · 取代 v7 ship-*(W3 减负时物理删除 v7 ship-* 子命令)。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
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


SHIP_ACTIONS = ("sanitize", "archive", "push", "close-unmerged")
# v8.145 ship 重构(用户拍板):ship1 全交付(worktree 内 · sanitize → archive → push ·
# 终点 = feature MR 提交)· ship2(ship-finalize)零内容只清场(删 worktree · 净化主工作区)。
# confirm-merged / cleanup 子动作随旧 Phase 2 链路一并删除(不留兼容期)。

# v8.70:main-sync 净化策略(ship 后主工作区 user-dirty 决策的执行选项)
MAIN_SYNC_STRATEGIES = ("commit-push", "stash-pull", "skip")

# ship.phase / ship.shipped 枚举单源在 state.py(SHIP_PHASE_ENUM / SHIP_SHIPPED_ENUM ·
# 校验发生在那边)· 本文件不再重复定义。
SHIP_GIT_HOSTS = ("github", "gitlab", "gitlab-self-hosted", "gitee", "bitbucket", "unknown")
SHIP_MR_METHODS = ("cli-gh", "cli-glab", "url-fallback", "unknown-platform")

# v8.81:ship1 知识沉淀闸门 · 知识层 6 项(随 feature MR graduate · 详 stages/ship-stage.md §13)
# 「描述代码的文档随代码进 MR」· 每项 sanitize 前必记一条决策(updated / none)· 强制走一遍。
DISTILL_KEYS = ("knowledge", "adr", "reg", "retro", "architecture", "db_schema")

# 流程减负:Micro(文案/样式/配置 · 零逻辑)distill 简表 —— 只强制 knowledge 一键
# (gotcha 沉淀 · 最可能有信号的一项)· 其余 5 键缺省自动填 MICRO_DISTILL_AUTO。
MICRO_DISTILL_REQUIRED = ("knowledge",)
MICRO_DISTILL_AUTO = "无(Micro)"

# v8.82:ship2 归档本体 · 过程层 feature 目录交付后 zip 进 features/_archive/ · 原目录从
# merge_target 删(防 AI 检索过时 feature 信息 · 代码是唯一真相)· 随收尾 MR 一起合(MR 合入后)。
# archive_on_ship(localconfig · 默认 true)· false → 退回 v8.80(收尾 MR 只同步终态 state.json)。
ARCHIVE_DIR_NAME = "_archive"


# ─── 主工作区拦截(沿用 v7 P0-156 治本) ─────────────────────────────


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
    """current_stage 必须是 ship · 否则 FAIL。

    v8.145 例外:archive 把 current_stage 写成 completed(终态进 zip)· 工作树接力卡
    随之是 completed —— archive 幂等重跑 / push 记录 / close-unmerged 仍须可跑。
    v8.241 例外:close-unmerged(放弃)可从任意 stage 走 —— pm_acceptance rejected
    的「放弃 Feature」选项此前是死路(emit 给的命令必被本门拒)· 幂等门仍由
    _handle_ship_close_unmerged 的 phase 检查(null/pushed → closed_unmerged)把守。
    """
    if action == "close-unmerged":
        return
    cur = state.get("current_stage")
    if cur == "ship":
        return
    if (cur == "completed"
            and state.get("ship", {}).get("phase") in ("archived", "pushed")
            and action in ("archive", "push", "close-unmerged")):
        return
    emit_json({
        "verdict": "FAIL",
        "error": f"current_stage={cur!r} · 不是 ship",
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

    流程减负 · Micro 简表:flow_type=Micro 只强制 knowledge 一键(gotcha)· 其余 5 键
    缺省自动填「无(Micro)」(零逻辑改动 · 逐项走 6 键是无信号仪式)。其他 flow 行为不变。
    """
    is_micro = (state.get("flow_type") == "Micro"
                or (state.get("flow_type") == "Feature" and state.get("preset") == "micro"))  # v8.222
    required_keys = MICRO_DISTILL_REQUIRED if is_micro else DISTILL_KEYS
    raw = getattr(args, "distill", None)
    if not raw:
        micro_hint = (
            "Micro 简表:--distill '" + json.dumps({"knowledge": "..."}, ensure_ascii=False)
            + "'(只强制 knowledge 一键 · 填 gotcha 或 'none' · 其余 5 键自动填「无(Micro)」)"
        )
        full_hint = ("ship 前必把「描述代码」的知识 graduate 到知识层(随本次 feature MR)· "
                     "逐项决策 --distill '"
                     + json.dumps({k: "..." for k in DISTILL_KEYS}, ensure_ascii=False)
                     + "'(每项填 'updated/promoted <what>' 或 'none'/'n/a' · 无则显式 none · "
                     "详 ship-stage.md §13)")
        emit_json({
            "verdict": "FAIL", "stage": "ship", "action": "sanitize",
            "error": "缺 --distill(ship1 知识沉淀闸门 · v8.81)",
            "hint": micro_hint if is_micro else full_hint,
            "distill_keys": list(required_keys),
        }, exit_code=1)
    try:
        d = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        emit_json({"verdict": "FAIL", "stage": "ship", "action": "sanitize",
                   "error": f"--distill 不是合法 JSON:{e}"}, exit_code=1)
    if not isinstance(d, dict):
        emit_json({"verdict": "FAIL", "stage": "ship", "action": "sanitize",
                   "error": "--distill 必须是 JSON 对象(知识层 6 项决策)"}, exit_code=1)
    missing = [k for k in required_keys
               if not (isinstance(d.get(k), str) and d[k].strip())]
    if missing:
        emit_json({
            "verdict": "FAIL", "stage": "ship", "action": "sanitize",
            "error": f"--distill 缺项 / 空值:{missing}",
            "hint": ("Micro 只强制 knowledge 一键(gotcha 或 'none' · 其余自动填「无(Micro)」)"
                     if is_micro else
                     "6 项全填(无则 'none'/'n/a' · 证明已逐项判断):" + " / ".join(DISTILL_KEYS)),
        }, exit_code=1)
    if is_micro:
        for k in DISTILL_KEYS:
            if not (isinstance(d.get(k), str) and d[k].strip()):
                d[k] = MICRO_DISTILL_AUTO
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
            "随本次 feature MR 一起合。下一步(v8.145 ship1 终幕):"
            "state.py ship-phase --action archive --feature <path> "
            "--planning-artifacts <规划翻牌文件>|--no-planning-changes "
            "--archive-desc '<业务摘要 ≤200 字 · 只业务不过程>'(归档+翻牌进 feature 分支)· 然后 push + MR"
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
    if cur_phase not in ("archived", "pushed"):
        emit_json(
            _phase_err(cur_phase, "pushed",
                       "push 仅允许 archived → pushed(pushed 重跑 = 幂等重录 · 覆盖登记)"
                       "—— 先跑 ship-phase --action archive"
                       "(归档+翻牌进 feature 分支 · ship1 全交付)再 push + MR"),
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

    # pushed → pushed:幂等重录(MR 重开 / URL·head 修正)· 允许覆盖登记 · concerns 留痕
    if cur_phase == "pushed":
        state.setdefault("concerns", []).append(
            f"{now_iso()} WARN ship-push 重录:phase 已是 pushed · "
            f"覆盖 feature_head_commit/mr_url 登记(旧 mr_url={ship.get('mr_url')!r})")

    # 更新 ship 字段
    ship["phase"] = "pushed"
    ship["shipped"] = "pushed"
    ship["feature_head_commit"] = args.feature_head_commit
    ship["git_host"] = args.git_host
    ship["mr_creation_method"] = args.mr_creation_method
    ship["mr_url"] = args.mr_url
    ship["mr_create_url"] = args.mr_create_url
    ship["feature_pushed_at"] = args.feature_pushed_at or now_iso()

    # v8.232:ship1 终点用户卡片(工具确定性生成 · AI 🔴 原样贴给用户 · 不自由发挥总结)——
    # 治实证 case:AI 写「本轮总结」长段 · MR URL 埋在段落里 · 用户被迫问「地址发出来啊」。
    _mr_link = ship["mr_url"] or ship["mr_create_url"] or "<MR URL 缺失 · 检查 push 记录>"
    _feat_path = getattr(args, "feature", None)
    _branch = "<feature 分支>"
    if _feat_path:
        _r = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=str(Path(_feat_path)), timeout=10)
        if _r.returncode == 0 and _r.stdout.strip():
            _branch = _r.stdout.strip()
    user_card = (
        f"⏸️ **ship1 完成 · 请合并 MR**\n"
        f"\n"
        f"🔗 {_mr_link}\n"
        f"\n"
        f"- 分支:`{_branch}` → `{state.get('merge_target') or '<merge_target>'}`\n"
        f"- 包含:代码 + 归档 + 规划翻牌(随本 MR 原子合入)\n"
        f"- 监控:我将跑 `await-merge` 30s 轮询 —— **你只需在平台点合并** · 合并后自动清场(删 worktree + 净化主工作区)\n"
        f"- 异常口令:平台报冲突 → 回「冲突」(我回 worktree 重跑 archive 解)· 不想合了 → 回「撤回」"
    )
    # v8.240:user_card 防截断三重物化 —— 治实证 case(KA-PAGES-F260714041628):主对话用
    # python key-filter 读本 emit,`user_card` 字段被过滤丢弃 → 手写卡片把 URL 包进 markdown
    # 加粗 → 用户「没看到链接」。v8.233 纯 prose 防线挡得住 head 截断挡不住 key-filter:
    # ① pmo_must_read 置字段首位(survive head)② user_card 落盘 SHIP-USER-CARD.md
    #    (untracked · 随 worktree 消亡 · stdout 丢失时 cat 兜底)
    # ③ hint 字段冗余同一指令(key-filter 惯选 verdict/hint —— 实证 case 的过滤器就选了 hint)。
    _card_file = None
    if _feat_path:
        try:
            _card_path = (Path(_feat_path) / "SHIP-USER-CARD.md").resolve()
            _card_path.write_text(user_card + "\n", encoding="utf-8")
            _card_file = str(_card_path)
        except OSError:
            _card_file = None
    _card_must_read = (
        "🔴 `user_card` 字段必须**原样**贴给用户(URL 置顶独立行 · 不转写/不加 markdown 包裹)"
        "· 禁 key-filter/截断本 JSON;"
        + (f"卡片已落盘 {_card_file}(stdout 丢失时 cat 它原样贴)"
           if _card_file else "卡片落盘失败 · 只能从本 JSON 的 user_card 取")
    )
    return {
        "verdict": "PASS",
        "pmo_must_read": _card_must_read,
        "user_card": user_card,
        "user_card_file": _card_file,
        "stage": "ship",
        "action": "push",
        "transition": f"{cur_phase} → pushed",
        "phase": "pushed",
        **({"rerecorded": True} if cur_phase == "pushed" else {}),
        "mr_url": ship["mr_url"],
        "mr_create_url": ship["mr_create_url"],
        "hint": _card_must_read,
        "next_action_brief": (
            "✅ Push + MR 记录完成 —— **feature 的 ship 到此结束**(v8.145 ship1 全交付)。\n\n"
            "🔴 v8.233 输出格式(两段定序 · 都必含):① 先贴本 emit 的 **`user_card`**(URL 置顶独立行)"
            "② 随后附 **📦 交付总结**(三槽:链路一行 / 关键决策与遗留 / 合并后解锁 · 照实写)。"
            "🔴 次序不可倒 —— 总结在前会把 MR 地址埋进段落(实证 case)。\n\n"
            "🔴 v8.234 贴完后**立即跑** `state.py await-merge --feature <本路径>`(30s 轮询)——"
            "**所有模式(普通/auto/yolo)都跑**:「停」= 不能替用户点合并 · **不是停止监控**"
            "(实证 case:auto 停在 pushed · 用户 5 分钟后合了没人收尾 · worktree 残留)。"
            "MERGED → 自动 ship-finalize;WAITING → 重跑续等;普通模式用户随时打断改人工。\n\n"
            "await-merge 不可用时的手动兜底(用户合并后):\n"
            "1. cd 到主工作区(非 linked worktree · 治本 P0-156)\n"
            "2. state.py ship-finalize --feature <worktree 内 feature 路径>"
            "(验已交付 → 删 worktree → 净化主工作区 · 可重入)\n\n"
            "用户关闭未合并:\n"
            "state.py ship-phase --action close-unmerged --feature <path>"
        ),
        # v8.37:url-fallback 退化 bypass 的 WARN(治本 SVC-CORE-B007)
        **({"fallback_bypass_warning": fallback_bypass_warning}
            if fallback_bypass_warning else {}),
    }



# ─── action 2.5:archive(v8.145 ship1 终幕 · tool-executed)────────


def _resolve_planning_paths(repo_root: str, raw_arg: Optional[str]) -> tuple:
    """v8.145:解析 --planning-artifacts(worktree 内路径)→ ([(rel, abs)], err)。

    路径相对 worktree 根(或绝对)· 必须存在 + 在仓内。err 非 None = 校验失败信息。
    """
    if not raw_arg:
        return [], None
    toplevel = Path(repo_root).resolve()
    resolved = []
    for raw in raw_arg.split(","):
        raw = raw.strip()
        if not raw:
            continue
        abs_p = (Path(raw) if os.path.isabs(raw) else (toplevel / raw)).resolve()
        if not abs_p.exists():
            return [], f"--planning-artifacts 文件不存在:{raw}(路径相对 worktree 根 · 先在 worktree 内翻牌再传)"
        try:
            rel = str(abs_p.relative_to(toplevel))
        except ValueError:
            return [], f"--planning-artifacts 文件在 worktree 仓库外:{raw}(规划层文件须随 feature MR 合入)"
        resolved.append((rel, abs_p))
    return resolved, None


def _merge_in_progress(wt_root: str) -> bool:
    """worktree 是否有未完成 merge(MERGE_HEAD 存在)。"""
    r = _git(["rev-parse", "-q", "--verify", "MERGE_HEAD"], cwd=wt_root)
    return r.returncode == 0


def _conflicted_files(wt_root: str) -> list:
    """当前 merge 冲突文件清单(git diff --name-only --diff-filter=U)。"""
    r = _git(["diff", "--name-only", "--diff-filter=U"], cwd=wt_root, timeout=30)
    if r.returncode != 0:
        return []
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]


def _own_index_row(wt_root: str, index_rel: str, feature_id: str) -> Optional[str]:
    """从本分支 HEAD 的 INDEX.md 抽本 feature 的行(冲突自动解时重放用)。"""
    r = _git(["show", f"HEAD:{index_rel}"], cwd=wt_root)
    if r.returncode != 0:
        return None
    for line in r.stdout.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == feature_id:
            return line.strip()
    return None


def _index_has_row(content: str, feature_id: str) -> bool:
    """INDEX 内容里是否已有本 feature 的行 —— 表格首列单元格精确匹配
    (子串判断会把 F001 误认成 F0012 的行 · 导致本 feature 行漏重放)。"""
    for line in content.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cells and cells[0] == feature_id:
            return True
    return False


def _try_append_union_resolve(wt_root: str, rel: str) -> bool:
    """v8.147:追加型冲突机械 union(实战 case:SVC-CORE-B260612051432 重跑 archive ·
    PROCESS-LEDGER 三行追加冲突 · AI 的处置 = 删标记保双方行 —— 零判断纯机械 · 该进脚本)。

    安全前提(物化):三方对比 base(:1:)/ours(:2:)/theirs(:3:)· **双方相对 base 都是
    纯增行**(base 行序列是两侧的保序子序列)才自动解;任何一方有删/改 → 返 False 留 AI。
    union = theirs 全文 + ours 新增行(去重)—— origin 侧(已合事实)为基 · 本侧增量后置。
    """
    def _show(stage: int) -> Optional[str]:
        r = _git(["show", f":{stage}:{rel}"], cwd=wt_root)
        return r.stdout if r.returncode == 0 else None

    base, ours, theirs = _show(1), _show(2), _show(3)
    if base is None or ours is None or theirs is None:
        return False
    base_lines = base.splitlines()

    def _added_only(side_text: str) -> Optional[list]:
        """base 是 side 的保序子序列 → 返回 side 的新增行;否则 None(有删/改)。"""
        b = 0
        added = []
        for ln in side_text.splitlines():
            if b < len(base_lines) and ln == base_lines[b]:
                b += 1
            else:
                added.append(ln)
        return added if b == len(base_lines) else None

    ours_add = _added_only(ours)
    theirs_add = _added_only(theirs)
    if ours_add is None or theirs_add is None:
        return False
    theirs_lines = theirs.splitlines()
    theirs_set = set(theirs_lines)
    extra = [ln for ln in ours_add if ln not in theirs_set]
    content = "\n".join(theirs_lines + extra)
    if not content.endswith("\n"):
        content += "\n"
    try:
        (Path(wt_root) / rel).write_text(content, encoding="utf-8")
    except OSError:
        return False
    ad = _git(["add", "--", rel], cwd=wt_root)
    return ad.returncode == 0



def _sync_feature_branch(wt_root: str, merge_target: str, index_rel: str,
                         feature_id: str) -> dict:
    """v8.146:ship1 冲突防线 —— feature 分支与 origin/<mt> 同步(merge · 不 rebase 已推分支)。

    背景:v8.145 把共享追加文件(INDEX/LEDGER/ROADMAP 翻牌)放进 feature 分支 ·
    并行 feature 的 MR 窗口重叠时后合者**必然**撞行冲突(设计时低估为「可能」·
    用户指出「大概率」属实)。三层防线:
      ① behind → 自动 merge(干净则无感 · MR 开出来即可合)
      ② INDEX.md 冲突**机械自动解**(确定性再生成:origin 侧为基 + 重放本 feature 行 ·
         追加表语义明确 · 可枚举进脚本)
      ③ 其余冲突(代码/规划文件)→ 留 AI 在 worktree 评估处理(不可枚举 ·
         LEDGER 类提示 union)
    返回 {status: up_to_date|merged_clean|auto_resolved|conflict|merge_in_progress|
          local_dirty|fetch_failed, conflict_files: [...], behind: int}
    (local_dirty = 本地未提交改动挡住 merge · git 拒绝启动 · 非冲突)。
    """
    if _merge_in_progress(wt_root):
        return {"status": "merge_in_progress",
                "conflict_files": _conflicted_files(wt_root), "behind": -1}
    f = _git(["fetch", "origin", merge_target], cwd=wt_root, timeout=120)
    if f.returncode != 0:
        return {"status": "fetch_failed", "conflict_files": [], "behind": -1,
                "error": f.stderr.strip()[:120]}
    ba = _behind_ahead(wt_root, merge_target)
    behind = ba[0] if ba else 0
    if behind == 0:
        return {"status": "up_to_date", "conflict_files": [], "behind": 0}
    mg = _git(["merge", "--no-edit", f"origin/{merge_target}"], cwd=wt_root, timeout=120)
    if mg.returncode == 0:
        return {"status": "merged_clean", "conflict_files": [], "behind": behind}
    # merge 因本地未提交改动被 git 拒绝(根本没启动 · 非冲突):U 列表为空 ·
    # 走冲突路径会误 commit / 误诊 —— 单列 status 由调用方给对症指引
    blob = (mg.stderr or "") + "\n" + (mg.stdout or "")
    if not _merge_in_progress(wt_root) and (
            "would be overwritten" in blob
            or "Please commit your changes or stash them" in blob):
        return {"status": "local_dirty", "conflict_files": [], "behind": behind,
                "detail": blob.strip()[:400]}
    conflicts = _conflicted_files(wt_root)
    auto_resolved: list = []
    # ② INDEX.md 机械自动解:origin 侧为基(最新已合状态)+ 重放本 feature 行
    if index_rel in conflicts:
        own_row = _own_index_row(wt_root, index_rel, feature_id)
        base = _git(["show", f"origin/{merge_target}:{index_rel}"], cwd=wt_root)
        if own_row and base.returncode == 0:
            content = base.stdout
            if not content.endswith("\n"):
                content += "\n"
            if not _index_has_row(content, feature_id):
                content += own_row + "\n"
            (Path(wt_root) / index_rel).write_text(content, encoding="utf-8")
            _git(["add", "--", index_rel], cwd=wt_root)
            conflicts = [c for c in conflicts if c != index_rel]
            auto_resolved.append(index_rel)
    # ②b v8.147:追加型台账冲突机械 union(三方对比 · 双方纯增行才解 · 否则留 AI)
    APPEND_UNION_BASENAMES = ("PROCESS-LEDGER.md",)
    for rel in list(conflicts):
        if rel.rsplit("/", 1)[-1] in APPEND_UNION_BASENAMES \
                and _try_append_union_resolve(wt_root, rel):
            conflicts.remove(rel)
            auto_resolved.append(rel)
    if not conflicts:
        cm = _git(["commit", "--no-edit"], cwd=wt_root, timeout=30)
        if cm.returncode == 0:
            return {"status": "auto_resolved", "conflict_files": [],
                    "auto_resolved_files": auto_resolved, "behind": behind}
        return {"status": "conflict", "conflict_files": ["(commit 失败:%s)" % cm.stderr.strip()[:80]],
                "behind": behind}
    return {"status": "conflict", "conflict_files": conflicts, "behind": behind}


def _sync_conflict_pending(action: str, sync: dict, feature_path: str) -> None:
    """冲突留 AI:emit PENDING + 处置指引 · exit 0。"""
    files = sync.get("conflict_files", [])
    emit_json({
        "verdict": "PENDING", "stage": "ship", "action": action,
        "pending_step": "merge-conflict",
        "conflict_files": files,
        "next_action": (
            ("⏸️ worktree 有未完成 merge —— 先收尾:解完冲突 `git add` → `git commit` → 重跑。\n"
             if sync["status"] == "merge_in_progress" else
             f"🔴 与 origin 同步发生冲突({len(files)} 文件)—— worktree 是解决冲突的合法场所"
             "(v8.145:内容性工作在可控环境):\n")
            + "  ① 逐文件评估处理(AI 自决 · 业务歧义大再上抛用户):\n"
            + "".join(f"     - {f}" + ("(台账类但非纯增行 · 机械 union 不敢动 · 人工合)"
                                        if f.endswith("PROCESS-LEDGER.md") else "") + "\n"
                       for f in files[:10])
            + "  ② `git add <已解文件>` → `git commit --no-edit`(完成 merge)\n"
            + f"  ③ 重跑 state.py ship-phase --action {action} --feature {feature_path}"
            "(幂等 · 已归档则同步后给 push 指引)"
        ),
    }, exit_code=0)



def _handle_ship_archive(state: dict, args: argparse.Namespace) -> dict:
    """v8.145 ship1 终幕(tool-executed · worktree 内):规划翻牌 gate → 终态 state.json →
    zip + INDEX → `git rm --cached` 过程目录 → 单 commit 进 feature 分支。

    架构(用户拍板):ship1 全交付 —— 归档/翻牌/台账全部发生在可控环境(worktree · 自己的
    分支)· 随 **feature MR 原子合入**(不再有第二条 ship-finalize 分支 + 第二个 MR)。
    - MR diff 干净:过程目录在分支历史里「加了又删」· 对 merge_target 净零 · diff 只剩
      代码 + zip + INDEX 行 + 规划翻牌行
    - 翻牌随 MR 原子生效:MR 不合 · ROADMAP 不显示已交付;MR revert · 翻牌同退
    - 工作树保留目录(`git rm --cached` 只删 index)→ state.json 转 untracked =
      **ship2 接力卡**(push 记录 MR 用 · ship2 读元数据 · 随 worktree 删除消亡)
    - zip 内 state.json = 终态墓碑(current_stage=completed)· 它与「completed 宣称」
      随 MR 合入同刻可见 —— 宣称与落地原子
    """
    ship = state.setdefault("ship", {})
    ship.setdefault("started_at", now_iso())
    cur_phase = ship.get("phase")
    if cur_phase not in (None, "closed_unmerged", "archived"):
        emit_json(_phase_err(cur_phase, "archived",
                             "archive 仅允许 null/archived(幂等)→ archived · 或 closed_unmerged 重开"),
                  exit_code=1)

    artifact_root = Path(args.feature).resolve()
    feature_id = state.get("feature_id") or artifact_root.name
    top = _git(["rev-parse", "--show-toplevel"], cwd=str(artifact_root))
    if top.returncode != 0:
        emit_json({"verdict": "FAIL", "action": "archive",
                   "error": f"--feature 不在 git 仓内:{top.stderr.strip()[:120]}"},
                  exit_code=1)
    wt_root = top.stdout.strip()
    paths = _archive_repo_paths(wt_root, artifact_root, feature_id)
    if not paths:
        emit_json({"verdict": "FAIL", "action": "archive",
                   "error": "无法解析归档 repo 相对路径(rev-parse --show-prefix 失败)"},
                  exit_code=1)
    feature_rel, zip_rel, index_rel = paths

    # ── v8.146 冲突防线:与 origin/<mt> 同步(首跑防开 MR 即冲突 · 重跑 = MR 窗口期
    # 冲突修复入口)· INDEX.md 冲突机械自动解 · 其余留 AI(详 _sync_feature_branch)──
    merge_target = state.get("merge_target") or ""
    sync_note = None
    if merge_target:
        sync = _sync_feature_branch(wt_root, merge_target, index_rel, feature_id)
        if sync["status"] in ("conflict", "merge_in_progress"):
            _sync_conflict_pending("archive", sync, args.feature)  # emit PENDING + exit
        if sync["status"] == "local_dirty":
            emit_json({
                "verdict": "PENDING", "stage": "ship", "action": "archive",
                "pending_step": "local-dirty",
                "detail": sync.get("detail", ""),
                "next_action": (
                    "🔴 worktree 有未提交本地改动挡住与 origin 的同步(git 拒绝启动 merge · "
                    "非冲突 · 文件清单见 detail):\n"
                    "  ① 内容性改动(规划翻牌等)→ `git add` + `git commit`"
                    "(它们本该进 feature 分支);纯临时文件 → `git stash -u` 或移出 worktree\n"
                    f"  ② 重跑 state.py ship-phase --action archive --feature {args.feature}"
                    "(幂等)"
                ),
            }, exit_code=0)
        if sync["status"] == "fetch_failed":
            sync_note = (f"⚠️ sync fetch 失败({sync.get('error', '')})· 冲突防线降级 · "
                         "MR 若报冲突 → 网络恢复后重跑 archive 同步")
        elif sync["status"] == "merged_clean":
            sync_note = (f"已自动合入 origin/{merge_target}(落后 {sync['behind']} commit · "
                         "无冲突 · 记得重新 git push)")
        elif sync["status"] == "auto_resolved":
            files = "、".join(sync.get("auto_resolved_files", [])) or "追加型台账"
            sync_note = (f"已合入 origin/{merge_target} · 冲突已机械自动解({files} · "
                         "origin 为基 + 重放本侧增量 · 记得重新 git push)")

    # 幂等:HEAD 已含 zip 且不含过程目录 → 已归档(重跑 = 同步后直接给 push 指引)
    zin = _git(["cat-file", "-e", f"HEAD:{zip_rel}"], cwd=wt_root)
    din = _git(["cat-file", "-e", f"HEAD:{feature_rel}/state.json"], cwd=wt_root)
    if zin.returncode == 0 and din.returncode != 0:
        ship["phase"] = "archived"  # closed_unmerged 重开:归档已在分支 · 直接续 push
        return {
            "verdict": "PASS", "stage": "ship", "action": "archive",
            "already_archived": True, "zip": zip_rel,
            **({"sync": sync_note} if sync_note else {}),
            "next_action_brief": _ship1_push_brief(feature_id, args.feature),
        }

    # v8.93 规划翻牌 gate(前移自旧 finalize-deliver):翻牌随 feature MR 原子合入
    planning_files, perr = _resolve_planning_paths(wt_root, getattr(args, "planning_artifacts", None))
    if perr:
        emit_json({"verdict": "FAIL", "action": "archive", "error": perr}, exit_code=1)
    if not planning_files and not getattr(args, "no_planning_changes", False):
        emit_json({
            "verdict": "PENDING", "stage": "ship", "action": "archive",
            "pending_step": "planning-backref",
            "next_action": (
                "🔴 归档前先翻规划层 back-reference(feature = 某 BL 的落地 · 不翻牌 → "
                "规划层与执行层脱节 · 进度统计失真):\n"
                "  ① 判断哪些需翻「📋 → ✅ 已交付」(只改相关的 · AI 自决):"
                "ROADMAP.md 对应 BL(翻状态 + 🔴 填「对应 F编号」= 本 feature 的 F-id · archive 靠它自解析所属 WS)"
                " / teamwork-space.md / 项目变更单;"
                "🔴 WS 的 §feature 总览进度块**别手改、也不必手动跑 ws-progress** —— archive 会从本 feature "
                "自解析 WS + 自刷 + 纳进归档 commit(v8.180 · emit ws_progress_refreshed)\n"
                "  ② 🔴 在 **worktree 内**改好(不 commit · archive 会随归档 commit 一起带走 · "
                "随 feature MR 原子合入 —— MR 不合翻牌不生效 · revert 同退)\n"
                f"  ③ 重跑:state.py ship-phase --action archive --feature {args.feature} "
                "--planning-artifacts <逗号分隔 worktree 相对路径> --archive-desc '<业务摘要 ≤200 字>'\n"
                f"  确无可翻(ad-hoc Bug/Micro)→ state.py ship-phase --action archive "
                f"--feature {args.feature} --no-planning-changes --archive-desc '<业务摘要 ≤200 字>'\n"
                "  🔴 **--archive-desc = 业务摘要**(这需求是什么 · 做了什么 · 业务影响/对外契约)· "
                "**只业务不过程** —— 不写评审轮次/bug 数/测试数/「全绿」/external 独家/code review 等"
                "过程信息(那些在 zip 内 state.json/REVIEW.md · 不进业务索引)。"
            ),
        }, exit_code=0)

    # v8.113 描述门禁(≤200 字 · 写 INDEX.md)
    raw_desc = getattr(args, "archive_desc", None)
    archive_desc = _clean_archive_desc(raw_desc)
    if raw_desc and len(archive_desc) > 200:
        emit_json({
            "verdict": "FAIL", "action": "archive",
            "error": f"--archive-desc 净化后 {len(archive_desc)} 字 · 超 200 字上限",
            "hint": "压缩表达方式重写到 ≤200 字后重跑(不靠截断丢尾 · archive 可重入)",
        }, exit_code=1)
    # v8.156:过程信息嗅探(INDEX 是业务索引 · 不该灌评审/测试过程数据)· WARN 不 BLOCK
    desc_warn = _archive_desc_process_smell(archive_desc)

    # 终态 state.json(zip 快照 = 墓碑 · 宣称随 MR 合入与落地原子可见)。
    # 🔴 终态只为 zip 打包临时落盘 · 打包完即恢复原文件:终态的持久化推迟到归档 commit
    # 成功之后(cmd_ship_phase 出口统一 save_state)—— commit 失败时磁盘不留
    # completed/archived 假象(宣称不得先于归档落地)。
    state_path = artifact_root / "state.json"
    try:
        _orig_state_raw = state_path.read_text(encoding="utf-8")
    except OSError:
        _orig_state_raw = None
    _orig_state = json.loads(json.dumps(state))

    def _restore_orig_state_file() -> None:
        if _orig_state_raw is not None:
            try:
                state_path.write_text(_orig_state_raw, encoding="utf-8")
            except OSError:
                pass

    def _rollback_archive_fail(payload: dict) -> None:
        """归档 commit 未成 → 内存/磁盘回到进入时状态 · emit FAIL(可重入重跑)。"""
        state.clear()
        state.update(_orig_state)
        _restore_orig_state_file()
        emit_json(payload, exit_code=1)

    ship["phase"] = "archived"
    ship["shipped"] = "archived"
    ship["archived_at"] = now_iso()
    contracts = state.setdefault("stage_contracts", {})
    contract = contracts.setdefault("ship", {})
    contract.setdefault("started_at", ship.get("started_at") or now_iso())
    contract["input_satisfied"] = True
    contract["process_satisfied"] = True
    contract["output_satisfied"] = True
    contract["completed_at"] = now_iso()
    contract["auto_commit"] = git_head(cwd=wt_root) or ""
    contract.setdefault("artifacts", [])
    state["current_stage"] = "completed"
    state["legal_next_stages"] = []
    cs = state.setdefault("completed_stages", [])
    if "ship" not in cs:
        cs.append("ship")
    save_state(state_path, state)
    try:
        write_review_log_entry(state, artifact_root, "ship", "completed", contract)
    except Exception:
        pass

    # zip + INDEX(物理写工作树)· 磁盘 IO 失败按 JSON 契约报错(不裸 traceback)并回滚
    try:
        zip_bytes = _build_archive_zip(artifact_root)
        zip_abs = Path(wt_root) / zip_rel
        zip_abs.parent.mkdir(parents=True, exist_ok=True)
        zip_abs.write_bytes(zip_bytes)
        index_abs = Path(wt_root) / index_rel
        index_abs.write_text(
            _build_archive_index(wt_root, "HEAD", index_rel, feature_id, now_iso(),
                                 archive_desc=archive_desc),
            encoding="utf-8")
    except OSError as e:
        _rollback_archive_fail({
            "verdict": "FAIL", "action": "archive",
            "error": f"归档产物写入失败:{e}",
            "hint": "检查磁盘空间 / 路径权限 · 修复后重跑(可重入 · state 已回滚)"})

    # zip 已含终态墓碑 → 磁盘接力卡先恢复原状态(终态落盘等归档 commit 成功后由出口 save)
    _restore_orig_state_file()

    # v8.180:确定性自刷 WS 进度块 —— 翻牌后从 feature 自解析所属 WS(F-id→ROADMAP 对应F编号→关联WS)
    # + 跑 ws-progress --write · 纳进归档 commit。治本:WS 进度块更新原是软指令(§3.5)· yolo 自主
    # 无人接住 → routinely stale。best-effort:解析不到(feature 不属 WS / 对应F编号 没填)则静默跳过。
    ws_refreshed = None
    try:
        _r = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "state.py"),
             "ws-progress", "--feature", str(artifact_root), "--write"],
            cwd=wt_root, capture_output=True, text=True, timeout=60)
        if _r.stdout.strip().startswith("{"):
            _d = json.loads(_r.stdout)
            if _d.get("verdict") == "OK" and _d.get("written_to"):
                ws_refreshed = _d["written_to"]
    except (subprocess.SubprocessError, OSError, ValueError):
        pass

    # git rm --cached(index only · 工作树保留 = ship2 接力卡)→ add → 单 commit
    rm = _git(["rm", "-r", "-q", "--cached", "--ignore-unmatch", feature_rel], cwd=wt_root)
    if rm.returncode != 0:
        _rollback_archive_fail({
            "verdict": "FAIL", "action": "archive",
            "error": f"git rm --cached {feature_rel} 失败:{rm.stderr.strip()[:150]}"})
    adds = [zip_rel, index_rel] + [rel for rel, _ in planning_files]
    if ws_refreshed and ws_refreshed not in adds:
        adds.append(ws_refreshed)        # v8.180:自刷的 WS 进度块文档纳进归档 commit
    ad = _git(["add", "--", *adds], cwd=wt_root)
    if ad.returncode != 0:
        _rollback_archive_fail({
            "verdict": "FAIL", "action": "archive",
            "error": f"git add 归档产物失败:{ad.stderr.strip()[:150]}"})
    plan_seg = (f" + 规划翻牌 {len(planning_files)} 文件" if planning_files else "")
    cm = _git(["commit", "-m",
               f"chore({feature_id}): ship1 archive · 过程层 → _archive/{feature_id}.zip{plan_seg}"],
              cwd=wt_root)
    if cm.returncode != 0:
        _rollback_archive_fail({
            "verdict": "FAIL", "action": "archive",
            "error": f"归档 commit 失败:{cm.stderr.strip()[:200]}",
            "hint": ("检查 git user 配置 / hooks · 修复后重跑(可重入)· "
                     "终态未持久化(state 已回滚到进入时状态)")})
    head = git_head(cwd=wt_root) or ""

    _lt_ai, _lt_wait = _timing_split(state)  # v8.208:台账/审计时长细化(AI 自主 vs 等待用户)
    _lt_bd, _ = _stage_durations(state)
    return {
        "verdict": "PASS", "stage": "ship", "action": "archive",
        "transition": f"{cur_phase} → archived",
        "phase": "archived",
        **({"sync": sync_note} if sync_note else {}),
        "archive_commit": head,
        "zip": zip_rel,
        "planning_bundled": [rel for rel, _ in planning_files],
        # v8.208/v8.209:PROCESS-LEDGER 行采写数据(台账在 ship1 archive 采写 · 见 §3.5/§16)——
        # AI 照抄进台账「宿主」+「时长(总·AI自主·待)」+「各阶段耗时」+「用户邮箱」列 · 确定性 · 不肉眼算 state。
        # v8.217:分诊校准束(预测 clarity/roster vs 实际 diff/轮次)· 台账「分诊校准」列照抄 · 年检算准确率
        "triage_calibration": _triage_calibration(state, wt_root, merge_target),
        "ledger_timing": {
            "host": state.get("host") or "unknown",  # v8.209:AI 宿主(claude-code/codex-cli/gemini-cli)
            "total_wall": _feature_duration_h(state),
            "ai_autonomous_min": _lt_ai,
            "await_user_min": _lt_wait,
            "per_stage": _lt_bd,
            "user_email": _git_user_email(wt_root),
        },
        # v8.180:WS 进度块确定性自刷结果(None = feature 不属 WS / 对应F编号 未填 → 未刷 · 见 §3.5)
        "ws_progress_refreshed": ws_refreshed,
        "warnings": [
            "过程目录已转 untracked 接力卡(工作树保留 · 分支树已删)· "
            "🔴 此后勿在 worktree 跑 `git add -A`(会把目录加回来)",
        ] + ([desc_warn] if desc_warn else []),
        "next_action_brief": _ship1_push_brief(feature_id, args.feature),
    }


def _ship1_push_brief(feature_id: str, feature_path: str) -> str:
    """archive 后的 push + MR 指引(P0-113 CLI-first)。"""
    return (
        "✅ 归档已进 feature 分支(MR diff 干净:过程文件加了又删 = 净零 · 只剩 "
        "代码 + zip + INDEX + 翻牌行)。接下来:\n"
        "  ① git push origin <feature 分支>\n"
        "  ② CLI-first 创建 feature MR(P0-113):gh pr create / glab mr create "
        "(拿真实 MR URL · 不退化用 push hint 表单链接)\n"
        f"  ③ 记录:state.py ship-phase --action push --feature {feature_path} "
        "--feature-head-commit <push 后 HEAD> --git-host <host> "
        "--mr-creation-method cli-<gh|glab> --mr-url <真实 URL>\n"
        "  ⏸️ 然后提示用户合并 MR —— **feature 的 ship 到此结束**(worktree 留给 ship2 清场)"
    )


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
            "- 重开:跑 ship-phase --action archive → push(v8.145 · 重归档重 MR)"
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
        "archive": _handle_ship_archive,
        "push": _handle_ship_push,
        "close-unmerged": _handle_ship_close_unmerged,
    }

    result = handlers[args.action](state, args)
    save_state(path, state)
    emit_json(result)


# ─── ship-finalize:ship2 主工作区清场(v8.145 重构 · 零内容修改)────
#
# 用户拍板架构:ship1 全交付(worktree 内 · sanitize → archive → push · 终点 = feature
# MR 提交 · 归档/翻牌/终态全随 feature MR 原子合入);ship2 不修改任何内容 · 只清理:
#   1. verify-delivered  zip 在 origin/<merge_target>(= MR 已合)· 未合 PENDING 绝不删 worktree
#   2. worktree-remove   删 feature worktree + 本地分支(接力卡 state.json 随之消亡)
#   3. tmp-cleanup       删 ${TMPDIR:-/tmp}/teamwork/<feature_id>/ scratch(v8.247 · cargo target/
#                        测试日志等 · 内容已上岸零对账价值 · 实证 CI 机 48GB 打满磁盘)
#   4. main-sync         净化主工作区:副产物(注入块/锁)自动 commit · 用户真改动决策 ·
#                        pull(--rebase 若有本地 commit)· push(被保护分支拒 → 提示)
# 旧 Phase 2 链路(state-sync / verify-merge / confirm-merged / cleanup / ship-complete /
# finalize-deliver 第二分支第二 MR / 零 checkout plumbing)v8.145 整体删除 · 不留兼容期。
# 十二个版本(v8.16→v8.144)反复修补的根因 = 在不可控的主工作区做内容性工作 · 现已移除。


SHIP_FINALIZE_STEPS = ("verify-delivered", "worktree-remove", "tmp-cleanup", "main-sync")


# ─── feature scratch 回收(standards/common.md § 临时产物目录 · v8.247)──────

TEAMWORK_TMP_ROOT_ENV = "TEAMWORK_TMP_ROOT"  # 测试覆盖用


def _teamwork_tmp_root() -> Path:
    """scratch 根 = ${TMPDIR:-/tmp}/teamwork(与 conventions §12.5 截图约定同根)。"""
    override = os.environ.get(TEAMWORK_TMP_ROOT_ENV)
    if override:
        return Path(override)
    return Path(os.environ.get("TMPDIR") or "/tmp") / "teamwork"


def _prune_feature_tmp(feature_id: str) -> dict:
    """删 scratch 根下 <feature_id>/ 整树(ship2 · verify-delivered 通过后)。

    🔴 时序:必须在 verify-delivered PASS 之后 —— 归档 zip 已确认在 origin ·
    日志/构建产物无对账价值 · 删除零风险。整目录删除(cargo target 是原子单元 ·
    按文件删会打碎 fingerprint 一致性)。失败不阻塞(warnings 记录)。
    """
    if not feature_id:
        return {"status": "n_a", "reason": "no_feature_id"}
    d = _teamwork_tmp_root() / feature_id
    if not d.is_dir():
        return {"status": "n_a", "pruned_bytes": 0}
    try:
        size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
    except OSError:
        size = 0
    try:
        shutil.rmtree(d)
        return {"status": "ok", "pruned_bytes": size, "path": str(d)}
    except OSError as e:
        return {"status": "failed", "error": str(e)[:120], "path": str(d)}


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

    路径前缀 = 子项目 docs_root(features 根 git show-prefix)· 多子项目时如 `svc/docs/features`:
    feature_rel: {prefix}/<dir-name>           (无尾 / · 如 svc/docs/features/<id>)
    zip_rel:     {prefix}/_archive/<id>.zip     (如 svc/docs/features/_archive/<id>.zip)
    index_rel:   {prefix}/_archive/INDEX.md     (单项目=repo 根 → docs/features/_archive/INDEX.md)
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
    """v8.94:极简 feature **业务**描述净化 —— 折叠空白 + 去 markdown 表格危险字符(`|`/换行)。
    空 → `—`(占位 · 表格不塌)。
    v8.113:**不再截断** —— 长度上限(≤200 字)改由 `cmd_ship_finalize` 前置门禁强制
    (超则 FAIL · 要求 AI 压缩表达方式重写到 ≤200 重跑 · 不靠截断丢尾)· 本函数只做
    表格安全净化(任意长度照原样返 · 经门禁后到这里必 ≤200)。
    v8.156:INDEX = **业务索引**(需求是什么/做了什么/影响)· 非过程数据(过程信息嗅探见
    `_archive_desc_process_smell`)。"""
    if not raw:
        return "—"
    s = " ".join(str(raw).split()).replace("|", "/")
    return s or "—"


# v8.156:INDEX 描述列业务-only 嗅探 —— 命中明显过程信号 → WARN(不 BLOCK · 过程信息检测不可枚举 ·
# 只逮无歧义的强信号:评审/测试/全绿/回归 N/external 独家/code review/money bug/N 轮)
_ARCHIVE_DESC_PROCESS_PATTERNS = (
    "评审", "全绿", "code review", "回归", "external 异质", "external 独家",
    "money bug", "真bug", "真 bug", "视角 review", "轮 external", "集成测试通过", "测试全",
)


def _archive_desc_process_smell(desc: str) -> Optional[str]:
    """命中过程信号词 → 返 WARN 提示;否则 None。INDEX 是业务索引 · 过程数据在 zip 内 state/REVIEW。"""
    if not desc or desc == "—":
        return None
    low = desc.lower()
    hits = [p for p in _ARCHIVE_DESC_PROCESS_PATTERNS if p.lower() in low]
    # 「N轮」「N 视角」「拦 N」等计数式过程描述
    import re as _re
    if _re.search(r"\d+\s*轮|\d+\s*视角|拦\s*\d+|\d+\s*真", desc):
        hits.append("过程计数")
    if not hits:
        return None
    return (f"--archive-desc 疑含过程信息({'、'.join(hits[:4])})· INDEX 是**业务索引**"
            "(需求是什么/做了什么/业务影响)· 过程数据(评审轮次/bug 数/测试/全绿)在 zip 内 "
            "state.json/REVIEW.md · 不进业务索引 · 建议重写为纯业务摘要(WARN 不阻塞)")


def _build_archive_index(repo_cwd: str, base_commit: str, index_rel: str,
                         feature_id: str, when: str,
                         archive_desc: Optional[str] = None) -> str:
    """v8.82:读 base 上现有 INDEX.md(若有)· 去本 feature 旧行 · 追加新行 · 返回新内容。

    v8.94:加「描述」列(≤200 字极简 feature 描述 · AI 在 planning-backref 暂停点经
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


def _behind_ahead(main_wt: str, merge_target: str) -> Optional[tuple]:
    """v8.144:本地 HEAD vs origin/<mt> 的 (behind, ahead)。失败返 None。

    治本 step 7 把一切 pull 失败都喊「分叉 · 需手动 rebase」—— 实证 case
    (SVC-PLATFORM-B260611083636):仅落后 + 脏 index · 被误导成 ~20 条手工
    git 手术 · 实际一条 `git pull --ff-only` 即愈(沙箱 E2 实测:staged 删除
    + 无关 M 文件不阻塞 ff-pull)。
    """
    r = _git(["rev-list", "--left-right", "--count",
              f"origin/{merge_target}...HEAD"], cwd=main_wt, timeout=30)
    if r.returncode != 0:
        return None
    parts = r.stdout.split()
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])  # (behind, ahead)
    except ValueError:
        return None


def _pull_failure_remedy(main_wt: str, merge_target: str) -> str:
    """v8.144:pull --ff-only 失败后的真相判别 + 对症 remedy(不再一律喊 rebase)。"""
    ba = _behind_ahead(main_wt, merge_target)
    if ba is None:
        return "无法判别落后/分叉(rev-list 失败)· 手动 git fetch origin 后检查"
    behind, ahead = ba
    if ahead == 0:
        return (f"本地仅落后 {behind} commit · 无分叉 —— 脏文件/staged 删除不阻塞 ff-pull · "
                f"直接 `git pull --ff-only origin {merge_target}`(或重跑 ship-finalize 幂等)")
    return (f"真分叉(落后 {behind} · 本地多 {ahead} commit)· 需处理本地 commit:"
            f"`git rebase origin/{merge_target}` 后 pull · 或与用户确认本地 commit 去留")


def _list_teamwork_stashes(main_wt: str) -> list:
    """v8.144:盘点 teamwork 系自动 stash 残留(被埋改动 / 跨 feature 陈旧)。

    实证 case:3 个 teamwork stash 跨 2 个 feature 堆积 · 其中一个埋着
    bootstrap 注入块改动 → AI 以为改动丢了 · 手工重写 = 与 stash 双份地雷。
    """
    r = _git(["stash", "list", "--format=%gd %s"], cwd=main_wt, timeout=15)
    if r.returncode != 0:
        return []
    return [ln.strip() for ln in r.stdout.splitlines() if "teamwork" in ln.lower()]


def _audit_dir() -> Path:
    """流程质量审计回收目录 · 默认 `~/.teamwork/audit/` · env TEAMWORK_AUDIT_DIR 可 override(测试用)。

    🔴 本机所有 consuming 项目共享的回收点 —— 框架层面跨项目搜集流程质量。
    与 backups / prepare_check_audit 同域(~/.teamwork)· 运行时数据不落 skill 安装目录
    (审计只写不读 · 无需从旧位置 docs/audit/ 迁移)。
    """
    env = os.environ.get("TEAMWORK_AUDIT_DIR")
    if env:
        return Path(env)
    return Path.home() / ".teamwork" / "audit"


def _feature_duration_h(state: dict) -> Optional[str]:
    """从 stage_contracts 时间戳算总时长(最早 started_at → 最晚 completed_at)· 小时 1 位。"""
    contracts = state.get("stage_contracts", {})
    starts, ends = [], []
    for c in contracts.values():
        for key, bucket in (("started_at", starts), ("completed_at", ends)):
            v = c.get(key)
            if not v:
                continue
            try:
                bucket.append(datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc))
            except (ValueError, TypeError):
                pass
    if not starts or not ends:
        return None
    secs = (max(ends) - min(starts)).total_seconds()
    return f"{secs / 3600:.1f}h" if secs >= 0 else None


# v8.172:纯用户决策等待 stage —— 其 duration = 等用户拍板的墙钟 · 非阶段内工作 ·
# 不能计入「最耗时(工作)」(实证 audit ×5:pm_acceptance 占 84%/87%/73% 全是等用户)。
_AWAIT_USER_STAGES = {"pm_acceptance"}


def _stage_durations(state: dict):
    """从 stage_contracts 抽各 stage `duration_minutes`(确定性)· 返 (breakdown, analysis)。

    breakdown = "goal 12m · blueprint 25m · …"(completed_stages 顺序 · 全列)
    analysis  = "工作阶段总和 Nm · 最耗时(工作)X Ym(P%)" + 用户决策等待 stage 单列
      —— 🔴 pm_acceptance 等纯等用户的墙钟**不计入最耗时**(否则把「等用户」误判成「阶段慢」)。
    无 duration 数据返 (None, None)。
    """
    contracts = state.get("stage_contracts", {}) or {}
    order = state.get("completed_stages", []) or list(contracts.keys())
    # v8.192:duration 扣 stage 内暂停等待(await_minutes · pause-mark 打点)→ 工作时长为真
    def _wa(s):
        c = contracts.get(s, {})
        d, a = c.get("duration_minutes"), int(c.get("await_minutes") or 0)
        return (max(0, d - a), a) if isinstance(d, int) else (None, a)
    items = [(s, *_wa(s)) for s in order]
    items = [(s, m, a) for s, m, a in items if isinstance(m, int)]
    if not items:
        return None, None
    breakdown = " · ".join(f"{s} {m}m" + (f"(+等待{a}m)" if a else "") for s, m, a in items)
    work = [(s, m) for s, m, a in items if s not in _AWAIT_USER_STAGES]
    awaiting = [(s, m + a) for s, m, a in items if s in _AWAIT_USER_STAGES]
    if work:
        wtotal = sum(m for _, m in work)
        ls, lm = max(work, key=lambda x: x[1])
        pct = f"{round(100 * lm / wtotal)}%" if wtotal else "?"
        analysis = f"工作阶段总和 {wtotal}m · 最耗时(工作){ls} {lm}m({pct})"
    else:
        analysis = "无工作阶段时长数据"
    if awaiting:
        aw = " + ".join(f"{s} {m}m" for s, m in awaiting)
        analysis += f" · ⏸️ {aw}=用户决策等待(墙钟 · 非工作 · 不计入最耗时)"
    return breakdown, analysis


def _timing_split(state: dict):
    """v8.208:把墙钟耗时拆成 **AI 自主运行** vs **等待用户** 两块(分离人工等待)。

    - ai_min   = Σ 工作 stage 的(duration − await_minutes)—— AI 真正在跑的时长(扣 stage 内暂停)
    - wait_min = Σ 工作 stage 的 await_minutes + Σ 纯等待 stage(_AWAIT_USER_STAGES · 如 pm_acceptance)的 duration
                 —— 全部人工等待(stage 内暂停 pause-mark 打点 + 纯等用户 stage 的墙钟)
    返 (ai_min, wait_min);无 duration 数据 → (None, None)。
    """
    contracts = state.get("stage_contracts", {}) or {}
    order = state.get("completed_stages", []) or list(contracts.keys())
    ai = wait = 0
    any_dur = False
    for s in order:
        c = contracts.get(s, {})
        d = c.get("duration_minutes")
        if not isinstance(d, int):
            continue
        any_dur = True
        a = int(c.get("await_minutes") or 0)
        if s in _AWAIT_USER_STAGES:
            wait += d                 # 纯等待 stage → 整段算等待
        else:
            ai += max(0, d - a)       # AI 工作 = 时长扣 stage 内暂停
            wait += a                 # stage 内暂停(等用户拍板)算等待
    return (ai, wait) if any_dur else (None, None)


def _git_user_email(cwd: Optional[str]) -> str:
    """v8.208:当前 git 环境用户邮箱(`git config user.email`)· 取不到返 ""。"""
    r = _git(["config", "user.email"], cwd=cwd, timeout=10)
    return r.stdout.strip() if r.returncode == 0 else ""


def _dispatch_model_distribution(feature_dir) -> dict:
    """v8.231:从 dispatch_log/*.md 汇总 per-agent model 分布(档位建议采纳率的观测原料)。

    dispatch 文件 Meta 段有 model 字段(agents/README)· 容错解析(AI 手写 markdown · 宽松匹配
    首个 `model: xxx` 行)。覆盖面 = 文件化 dispatch(可审计路径);未记 model 的计 unspecified
    (= 继承会话模型 · 正是要观测的「没分档」信号)。无 dispatch_log → {}。
    """
    import re as _re
    d = Path(feature_dir) / "dispatch_log"
    if not d.is_dir():
        return {}
    dist: dict = {}
    for f in sorted(d.glob("*.md")):
        if f.name.upper() == "INDEX.MD":
            continue
        try:
            head = f.read_text(encoding="utf-8", errors="replace")[:2000]
        except OSError:
            continue
        m = _re.search(r"(?im)^\s*[-*]?\s*model\s*[::]\s*([^\s|,()]+)", head)
        key = m.group(1).strip().lower() if m else "unspecified(继承会话)"
        dist[key] = dist.get(key, 0) + 1
    return dist


def _triage_calibration(state: dict, wt_root: str, merge_target: str) -> dict:
    """v8.217(智能分诊 v2):分诊「预测 vs 实际」校准束 —— 台账/年检数据源。

    预测侧:clarity(prepare 判定)+ roster 调整摘要(去了哪些角色 · 审计已留);
    实际侧:diff 文件数(git 确定性)+ goal 修订轮数(PRD 被打回?)+ review 轮数(评审拦没拦住东西)。
    年检据此算分诊准确率:explicit 判定的 feature 若 PRD 常被打回 / review 高轮次 → 判据收紧。
    """
    contracts = state.get("stage_contracts", {}) or {}
    adjustments = state.get("stage_review_roles_adjustments", []) or []
    adj = "; ".join(f"{a.get('stage')}→{','.join(a.get('roles', []))}"
                    for a in adjustments if isinstance(a, dict)) or "默认矩阵"
    diff_files = None
    r = _git(["diff", "--name-only", f"origin/{merge_target}...HEAD"], cwd=wt_root, timeout=30)
    if r.returncode == 0:
        diff_files = len([l for l in r.stdout.splitlines() if l.strip()])
    # v8.231:dispatch 模型分布(档位建议采纳观测 —— unspecified 占比高 = 没分档 · 年检校准原料)
    dispatch_models = _dispatch_model_distribution(state.get("artifact_root") or "")
    return {
        "clarity": state.get("clarity") or "normal",
        "roster": adj,
        "actual_diff_files": diff_files,
        "goal_rounds": len(contracts.get("goal", {}).get("rounds") or []),
        "review_rounds": len(contracts.get("review", {}).get("rounds") or []),
        **({"dispatch_models": dispatch_models} if dispatch_models else {}),
    }


def _capture_audit_sources(feature_dir: Path, max_chars: int = 4000) -> str:
    """v8.207:worktree-remove **前**抓 audit 三段判断的源材料(REVIEW*.md + TEST-REPORT.md)·
    压成紧凑摘录 · 供 _write_audit_record 嵌进草稿(治 AI 事后 unzip 反读归档)。

    只抽三段判断真正要看的:REVIEW verdict/findings + TEST 结论/AC 覆盖。读失败静默返 ""(绝不阻塞 ship2)。
    """
    try:
        chunks: list = []
        review_files = sorted(feature_dir.glob("REVIEW*.md"))
        for rf in review_files:
            try:
                txt = rf.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                continue
            if txt:
                chunks.append(f"### {rf.name}\n{txt[:max_chars]}")
        tr = feature_dir / "TEST-REPORT.md"
        if tr.is_file():
            try:
                txt = tr.read_text(encoding="utf-8", errors="replace").strip()
                if txt:
                    chunks.append(f"### TEST-REPORT.md\n{txt[:max_chars]}")
            except OSError:
                pass
        return "\n\n".join(chunks)
    except OSError:
        return ""


def _write_audit_record(state: dict, feature_id: str, merge_target: str,
                        main_wt: str, main_model: Optional[str] = None,
                        audit_sources: str = "") -> Optional[str]:
    """ship2 后落「流程质量审计」到 ~/.teamwork/audit/<id>.md(_audit_dir)·
    框架层面跨项目搜集流程质量。

    机器数据(实走 stages / 时长 / concerns / bypass)工具确定性抽(喂 kill-criteria 决策
    不可幻觉);三段判断(做的好的 / 发现的问题 / 待优化的)留占位 · 由 AI **静默**补完
    (零暂停 · 不等确认)。写失败静默降级(绝不阻塞 ship2)· 返回文件路径或 None。
    已存在(AI 已填)→ 不覆盖。
    """
    try:
        audit_dir = _audit_dir()
        audit_dir.mkdir(parents=True, exist_ok=True)
        out = audit_dir / f"{feature_id}.md"
        if out.exists():
            return str(out)  # 已落(含 AI 已填判断)· 幂等不覆盖

        # 来源项目(跨项目回收时区分哪个项目)
        rr = _git(["remote", "get-url", "origin"], cwd=main_wt, timeout=10)
        if rr.returncode == 0 and rr.stdout.strip():
            source = rr.stdout.strip().rstrip("/").rsplit("/", 1)[-1]
            source = source[:-4] if source.endswith(".git") else source
        else:
            source = Path(main_wt).name

        stages = "→".join(state.get("completed_stages", [])) or "?"
        dur = _feature_duration_h(state) or "?"
        concerns = state.get("concerns", []) or []
        warn_n = sum(1 for c in concerns if isinstance(c, str) and "WARN" in c)
        bypass_n = len(state.get("ship", {}).get("bypass_log", []) or [])
        flow = state.get("flow_type") or "?"
        stage_dur, stage_analysis = _stage_durations(state)
        ai_min, wait_min = _timing_split(state)   # v8.208:AI 自主 vs 等待用户
        user_email = _git_user_email(main_wt)     # v8.208:git 用户邮箱
        host = state.get("host") or "未记录"
        model_suffix = (f" · 模型 {main_model}" if main_model
                        else " · 模型(未声明 · ship-finalize 传 --main-model 记录)")
        _dm = _dispatch_model_distribution(state.get("artifact_root") or "")  # v8.231

        body = (
            f"---\n"
            f"feature_id: {feature_id}\n"
            f"source_project: {source}\n"
            f"flow_type: {flow}\n"
            f"merge_target: {merge_target}\n"
            f"host: {state.get('host') or 'unknown'}\n"  # v8.209:AI 宿主(harvest 按宿主分析 codex/claude)
            f"user_email: {user_email or 'unknown'}\n"  # v8.208:git 用户邮箱(harvest 按人分析)
            f"generated_at: \"{now_iso()}\"\n"
            f"audit_status: pending\n"  # AI 填完判断 → 改 done(harvest 时筛)
            f"---\n\n"
            f"# 流程质量审计 · {feature_id}\n\n"
            f"## 实际数据(工具自动抽 · 勿改)\n"
            f"- 来源项目:{source}\n"
            f"- flow:{flow}\n"
            f"- 实走 stages:{stages}\n"
            f"- 总时长(墙钟):{dur}(init → archive · 不含 MR 等待)\n"
            f"- 🔴 AI 自主运行:{f'{ai_min}m' if ai_min is not None else '?'}"
            f" · 等待用户:{f'{wait_min}m' if wait_min is not None else '?'}"
            f"(v8.208 · 墙钟里的人工等待已分离 · stage 内 pause-mark 暂停 + 纯等待 stage)\n"
            f"- 各阶段耗时:{stage_dur or '(无 duration 数据)'}\n"
            f"- 耗时分析:{stage_analysis or '?'}(总时长含阶段间等待 · 阶段总和=纯在阶段内)\n"
            f"- 用户邮箱:{user_email or '未取到'}\n"
            + (f"- dispatch 模型分布:{_dm}(unspecified=未分档继承会话 · 档位采纳观测 · v8.231)\n"
               if _dm else "")
            + f"- 主对话:host={host}{model_suffix}\n"
            f"- concerns:{len(concerns)}(WARN {warn_n})· bypass:{bypass_n}\n"
            f"- 细数据源:本 feature `project-specs/PROCESS-LEDGER.md` 行"
            f"(external 总/采/驳 · 角色真 finding · 暂停点 改:默)\n\n"
            + (f"## 源材料摘录(v8.207 · worktree 删除前自动抽 · 供三段判断 · 勿改)\n"
               f"> 🔴 三段判断照实抄本段 + 上方实际数据 · **无需 unzip 归档**(worktree 已删 · 源已在此)。\n\n"
               f"{audit_sources}\n\n" if audit_sources else "")
            + f"## 做的好的\n"
            f"<!-- AI 静默填:本 feature 流程上真正有效的环节(external 拦真 bug / "
            f"test 抓回归 / diagnose 改修复方向)· 照实抄**上方『源材料摘录』段** + 实际数据 · 无则写「无」 -->\n\n"
            f"## 发现的问题\n"
            f"<!-- AI 静默填:流程摩擦 / 工具判例 / 框架级 bug(= 该反馈 teamwork 的)· "
            f"照实 · 无则写「无」 -->\n\n"
            f"## 待优化的\n"
            f"<!-- AI 静默填:本 feature 暴露的可优化点(纯过场环节 / 成本异常)· "
            f"仅记录不自改 spec · 无则写「无」 -->\n"
        )
        out.write_text(body, encoding="utf-8")
        return str(out)
    except OSError:
        return None


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
    if paths:
        _feat_rel, zip_rel, _index_rel = paths
        r = _git(["cat-file", "-e", f"origin/{mt}:{zip_rel}"], cwd=main_wt)
        return zip_rel if r.returncode == 0 else None
    # v8.145:worktree(含 feature 路径)已物理删除 → rev-parse --show-prefix 不可用 ·
    # 退化:在 origin/<mt> 全树搜 `**/_archive/<feature_id>.zip`
    ls = _git(["ls-tree", "-r", "--name-only", f"origin/{mt}"], cwd=main_wt, timeout=60)
    if ls.returncode != 0:
        return None
    suffix = f"_archive/{feature_id}.zip"
    for line in ls.stdout.splitlines():
        if line.strip().endswith(suffix):
            return line.strip()
    return None


def _classify_main_sync_dirty(main_wt: str, feature_dir: Optional[Path], state: dict) -> dict:
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
        feature_rel = (str(feature_dir.resolve().relative_to(Path(main_wt).resolve()))
                       if feature_dir is not None else "")
    except (ValueError, OSError, AttributeError):
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
        main_wt: str, merge_target: str, artifact_root: Optional[Path], state: dict,
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
    # v8.145:worktree(含接力卡)此刻已删 · main-sync 不再依赖 --feature
    fcmd = f"state.py main-sync --merge-target {merge_target} --strategy"
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


def _stash_hashes(main_wt) -> set:
    """当前全部 stash 的 commit hash 集(净化策略执行前快照用)· 列取失败返空集
    (空集 = drop_all 全部按「新建」排除 · 只保不删 · 安全方向)。"""
    r = _git(["stash", "list", "--format=%H"], cwd=main_wt, timeout=15)
    if r.returncode != 0:
        return set()
    return {ln.strip() for ln in r.stdout.splitlines() if ln.strip()}


def _reclaim_stashes(main_wt, drop_all: bool = False,
                     preexisting: Optional[set] = None) -> dict:
    """v8.190:回收 teamwork main-sync auto-stash(治本 harvest 26×:stash-pull 每次备份不 pop ·
    跨 feature/session 累积 11+ · human 难判哪些可 drop)。

    🔴 只认 **teamwork 自建**的 main-sync stash(消息含标识)· 绝不碰用户自己的 stash。
    默认(drop_all=False):只 drop **可证冗余的**(空 / 内容已在分支 · `git apply --reverse --check` 通过)·
    其余含未合内容的 surface。drop_all=True(用户 --drop-stashes 确认)→ 全清 teamwork main-sync stash。
    preexisting:本次净化策略执行前的 stash hash 快照 —— drop_all 只清快照中已存在的 ·
    本次策略(stash-pull)刚建的备份不在快照 → 排除不 drop(否则「全清」把新备份一起清掉)。
    None = 不排除(直接调用场景)。
    """
    def _tw_stashes():
        r = _git(["stash", "list", "--format=%gd%x09%H%x09%s"], cwd=main_wt, timeout=15)
        out = []
        for ln in (r.stdout or "").splitlines():
            parts = ln.split("\t", 2)
            if len(parts) != 3:
                continue
            ref, sha, subj = parts
            m = re.match(r"stash@\{(\d+)\}", ref.strip())
            if m and ("teamwork main-sync stash" in subj or "净化主工作区遗留" in subj
                      or re.search(r"\bmain-sync\b", subj)):
                out.append((int(m.group(1)), ref.strip(), sha.strip(), subj.strip()))
        return out

    tw = _tw_stashes()
    if not tw:
        return {"teamwork_stashes": 0, "dropped": 0, "remaining_count": 0, "remaining": []}

    def _redundant(ref):
        # 🔴 --include-untracked:含新增文件(否则只 stash 了 untracked 的会被误判为空 diff)
        show = _git(["stash", "show", "-p", "--include-untracked", ref],
                    cwd=main_wt, timeout=20)
        if show.returncode != 0:
            return False  # 取不到 diff(timeout / 老 git 不支持等)→ 不可证冗余 · 保留
        diff = show.stdout or ""
        if not diff.strip():
            return True   # 真空 stash(returncode==0 且 diff 空)→ 安全 drop
        try:
            chk = subprocess.run(["git", "-C", str(main_wt), "apply", "--reverse", "--check"],
                                 input=diff, capture_output=True, text=True, timeout=20)
        except (subprocess.SubprocessError, OSError):
            return False  # 校验跑不起来 → 不可证冗余 · 保留
        return chk.returncode == 0   # 反向 patch 可 apply = 内容已在树 → 安全 drop

    excluded_new = 0
    drop_idx = []
    for idx, ref, sha, _subj in tw:
        if drop_all:
            if preexisting is not None and sha not in preexisting:
                excluded_new += 1   # 本次策略新建的备份 · 全清也不碰
                continue
            drop_idx.append(idx)
        elif _redundant(ref):
            drop_idx.append(idx)
    for idx in sorted(drop_idx, reverse=True):   # 高 index 先 drop · 低 ref 不移位
        _git(["stash", "drop", f"stash@{{{idx}}}"], cwd=main_wt, timeout=15)

    def _label(subj):
        m = re.search(r"·\s*([\w.-]+)\s*$", subj)
        return m.group(1) if m else subj[:40]
    rem = [{"ref": r, "feature": _label(s)} for _, r, _, s in _tw_stashes()]  # 重列拿新 ref
    out = {"teamwork_stashes": len(tw), "dropped": len(drop_idx),
           "dropped_reason": (("--drop-stashes(用户确认全清"
                               + (f" · 排除本次新建 {excluded_new} 个)" if excluded_new else ")"))
                              if drop_all
                              else "空 / 内容已在分支(可证冗余 · 安全)"),
           "remaining_count": len(rem), "remaining": rem}
    if excluded_new:
        out["excluded_new"] = excluded_new
    if rem:
        out["hint"] = (f"剩 {len(rem)} 个 teamwork main-sync stash 含**未合内容** · 逐个 "
                       "`git stash show -p <ref>` 核 · 确不需要 → `main-sync --drop-stashes` 全清")
    return out


def cmd_main_sync(args: argparse.Namespace) -> None:
    """v8.70:主工作区净化(ship 后 user-dirty 决策的执行入口)。

    治本:ship-finalize step 7 发现主工作区有用户改动时 · 旧逻辑仅「保留 + WARN」·
    停在脏态 · 不 pull 不处理。现在 ship-finalize 会 surface「是否净化」决策 ·
    用户拍板后跑本命令执行选定策略 —— 尽最大努力安全保持主工作区干净 + 最新。

    必在主工作区跑 · 对 merge_target 应用 --strategy:commit-push/stash-pull/skip。
    """
    main_wt = _ship_finalize_precheck()  # 复用主工作区校验(linked worktree → FAIL)
    # v8.145:--feature 可选(worktree/接力卡可能已删)· merge_target 来源三级:
    # --merge-target > state.json(若 --feature 可读)> 主工作区当前分支
    state: dict = {}
    artifact_root = None
    if getattr(args, "feature", None) and (Path(args.feature) / "state.json").exists():
        _, state = load_state(args.feature)
        artifact_root = Path(args.feature).resolve()
    merge_target = (getattr(args, "merge_target", None)
                    or state.get("merge_target") or "")
    if not merge_target:
        cur0 = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=main_wt)
        merge_target = cur0.stdout.strip() if cur0.returncode == 0 else ""
    if not merge_target:
        emit_json({
            "verdict": "FAIL", "command": "main-sync",
            "error": "无法确定 merge_target(--merge-target 未传 · 无接力卡 · 分支名解析失败)",
            "hint": "显式传 --merge-target <branch>",
        }, exit_code=1)
    if args.strategy not in MAIN_SYNC_STRATEGIES:
        emit_json(_enum_err("--strategy", args.strategy, MAIN_SYNC_STRATEGIES),
                  exit_code=1)

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

    # 策略执行前快照现有 stash(hash)—— --drop-stashes 全清只清快照内的 ·
    # 本次 stash-pull 新建的备份排除(刚备份就被「全清」删掉 = 数据丢失)
    pre_stashes = _stash_hashes(main_wt)

    res = _main_sync_apply_strategy(
        main_wt, merge_target, artifact_root, state, args.strategy,
        message=getattr(args, "message", None))

    # v8.190:回收 teamwork main-sync auto-stash(治 harvest 26× 累积无回收)· 默认只 drop 可证冗余的
    reclaim = _reclaim_stashes(main_wt, drop_all=getattr(args, "drop_stashes", False),
                               preexisting=pre_stashes)

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
        # v8.190:teamwork stash 回收结果(盘点 · drop 冗余 · surface 未合)
        **({"stash_reclaim": reclaim} if reclaim.get("teamwork_stashes") else {}),
        "next_action_brief": _main_sync_brief(state, args.strategy, res),
    })


def cmd_ship_finalize(args: argparse.Namespace) -> None:
    """v8.145 ship2 · 主工作区清场(零内容修改 · 用户拍板)。

    ship1(worktree 内)已全交付:归档 zip + 规划翻牌 + 终态 state.json 全在 feature MR。
    本命令不写 state · 不产内容 · 只清理:
      1. verify-delivered  fetch 后验 zip 在 origin/<merge_target>(= feature MR 已合)·
                           未合 → PENDING(🔴 绝不在合并前删 worktree)
      2. worktree-remove   删 feature worktree + 本地分支(接力卡随之消亡)+ fetch --prune
      3. main-sync         副产物(bootstrap 注入块/harness 锁)自动 commit ·
                           用户真改动 → 影响评估 + 决策面板 · pull / push
    尾随:teamwork stash 盘点(v8.144)+ digest 指引(stages/ship-stage.md §16)。
    幂等:接力卡已消亡(worktree 已删)→ zip-on-origin 判已交付 → PASS noop。
    """
    main_wt = _ship_finalize_precheck()
    feature_dir = Path(args.feature).resolve()
    completed: list = []
    skipped: list = []
    warnings: list = []

    # ── 接力卡(worktree 内 untracked state.json · ship1 archive 留下)──
    state: dict = {}
    if (feature_dir / "state.json").exists():
        _, state = load_state(args.feature)
    feature_id = state.get("feature_id") or feature_dir.name
    # v8.207:🔴 worktree-remove **之前**抓 REVIEW/TEST 摘录 —— 治本(实证 case):audit 三段
    # 判断需 REVIEW.md/TEST-REPORT.md,但它们随 worktree 删除只剩 zip 内 → AI 被迫 unzip 反读。
    # 此刻 feature_dir 尚在 · 抓成摘录嵌进 audit 草稿 · AI 读草稿即可填三段(不再 unzip)。
    audit_sources = _capture_audit_sources(feature_dir)
    merge_target = state.get("merge_target") or ""
    if not merge_target:
        # 接力卡消亡(worktree 已删 / 手清)→ 幂等:zip-on-origin 判已交付
        zip_rel = _archive_idempotent_zip(main_wt, args.feature)
        if zip_rel:
            emit_json({
                "verdict": "PASS", "command": "ship-finalize",
                "feature_id": feature_id, "idempotent": True,
                "completed_steps": ["verify-delivered"],
                "skipped_steps": ["worktree-remove", "main-sync"],
                "note": f"归档已在 origin({zip_rel})· worktree/接力卡已消亡 · 无事可做",
                "next_action_brief": (
                    "✅ ship2 幂等确认:已交付已清场。主工作区如有脏内容需净化 · "
                    "单独跑 state.py main-sync --strategy <commit-push|stash-pull|skip>"),
            })
            return
        _ship_finalize_fail(
            "verify-delivered",
            f"接力卡缺失({feature_dir}/state.json 不存在)且 origin 未见归档 zip",
            "确认 --feature 指向 worktree 内 feature 目录 · ship1(sanitize → archive → push)是否完成",
            completed, skipped)

    ship = state.get("ship", {}) or {}
    wt_info = state.get("worktree") or {}
    wt_strategy = wt_info.get("strategy") or "off"
    wt_path_raw = wt_info.get("path") or ""
    wt_branch = (wt_info.get("branch") or "").replace("refs/heads/", "")
    wt_path = (str((Path(main_wt) / wt_path_raw).resolve()) if wt_path_raw else "")

    if not _read_archive_on_ship(str(feature_dir)):
        warnings.append(
            "localconfig archive_on_ship=false 已废弃(v8.145 起 ship1 统一归档)· 配置被忽略")

    # ── Step 1:verify-delivered(安全闸)──────────────────────────
    fr = _git(["fetch", "origin", merge_target], cwd=main_wt, timeout=120)
    if fr.returncode != 0:
        _ship_finalize_fail(
            "verify-delivered",
            f"git fetch origin {merge_target} 失败:{fr.stderr.strip()[:200]}",
            "检查网络 / origin 远程 / merge_target 分支名 · 修复后重跑(可重入)",
            completed, skipped)
    if not _remote_archive_delivered(main_wt, feature_dir, feature_id, merge_target):
        if ship.get("phase") != "pushed":
            hint = (f"ship1 未完成(ship.phase={ship.get('phase')!r} · 应为 pushed):"
                    "回 worktree 跑 ship-phase --action archive → git push + MR → --action push 记录")
        else:
            hint = ("feature MR 尚未合并 —— 等用户在平台合并后重跑本命令(可重入)。"
                    "🔴 未合并前绝不删 worktree(内容还没上岸)")
        emit_json({
            "verdict": "PENDING", "command": "ship-finalize",
            "pending_step": "verify-delivered",
            "feature_id": feature_id,
            "mr_url": ship.get("mr_url"),
            "next_action": hint,
            **({"warnings": warnings} if warnings else {}),
        }, exit_code=0)
    completed.append("verify-delivered")

    # ── Step 2:worktree-remove(内容已上岸 · 接力卡随之消亡)──────
    wt_removed = False
    if wt_strategy == "off" or not wt_path:
        skipped.append("worktree-remove")
        wt_removed = True
    else:
        still_there = any(
            _same_path(w.get("path"), wt_path) for w in _list_worktrees(main_wt))
        if not still_there:
            skipped.append("worktree-remove")
            wt_removed = True
        else:
            # --force 删除前置检查:worktree 内除接力卡(feature 目录及其子路径)外
            # 仍有 dirty/untracked → 不删(--force 会连带销毁)· PENDING 交 AI/用户处置。
            # 已 commit 未 push 的分支内容由下方 branch -d(未合并即拒删)兜底 · 不在此检查。
            st = _git(["status", "--porcelain"], cwd=wt_path, timeout=30)
            if st.returncode != 0:
                emit_json({
                    "verdict": "PENDING", "command": "ship-finalize",
                    "pending_step": "worktree-remove",
                    "feature_id": feature_id,
                    "completed_steps": completed,
                    "error": f"worktree 内 git status 失败:{st.stderr.strip()[:150]}",
                    "next_action": (
                        "无法确认 worktree 是否干净 · 不执行删除。修复后重跑 "
                        f"state.py ship-finalize --feature {args.feature}(可重入)"),
                    **({"warnings": warnings} if warnings else {}),
                }, exit_code=0)
            try:
                feat_rel_wt = str(feature_dir.relative_to(Path(wt_path)))
            except ValueError:
                try:
                    feat_rel_wt = str(
                        feature_dir.resolve().relative_to(Path(wt_path).resolve()))
                except (ValueError, OSError):
                    feat_rel_wt = None
            leftover = []
            for line in st.stdout.splitlines():
                if len(line) < 4:
                    continue
                p = line[3:].strip()
                if " -> " in p:
                    p = p.split(" -> ", 1)[1].strip()
                p = p.strip('"').rstrip("/")
                if feat_rel_wt and (p == feat_rel_wt
                                    or p.startswith(feat_rel_wt + "/")):
                    continue  # 接力卡目录 archive 后本就 untracked · 属预期
                leftover.append(p)
            if leftover:
                emit_json({
                    "verdict": "PENDING", "command": "ship-finalize",
                    "pending_step": "worktree-remove",
                    "feature_id": feature_id,
                    "completed_steps": completed,
                    "dirty_count": len(leftover),
                    "dirty_files": leftover[:20],
                    "next_action": (
                        f"🔴 worktree 内有接力卡之外的未提交内容({len(leftover)} 个 · "
                        "见 dirty_files)· --force 删 worktree 会连带销毁 —— 逐个核:\n"
                        "  · 要保留 → 移出 worktree(MR 已合 · 后续内容走新分支/MR)\n"
                        "  · 确认丢弃 → 在 worktree 内删除/还原这些文件\n"
                        f"  然后重跑 state.py ship-finalize --feature {args.feature}(可重入)"),
                    **({"warnings": warnings} if warnings else {}),
                }, exit_code=0)
            rm = _git(["worktree", "remove", "--force", wt_path],
                      cwd=main_wt, timeout=60)
            if rm.returncode != 0:
                warnings.append(
                    f"git worktree remove 失败:{rm.stderr.strip()[:150]} · "
                    f"内容已上岸(zip 在 origin)不丢 · 手动 git worktree remove --force {wt_path}")
            else:
                wt_removed = True
                completed.append("worktree-remove")
                if wt_branch:
                    bd = _git(["branch", "-d", wt_branch], cwd=main_wt)
                    if bd.returncode != 0:
                        warnings.append(
                            f"本地 feature 分支 {wt_branch} 未删(可能未完全合并)· "
                            f"确认已合入后手动 git branch -D {wt_branch}")
    # ── Step 3:tmp-cleanup(scratch 回收 · 内容已上岸零风险 · v8.247)────
    tmp_res = _prune_feature_tmp(feature_id)
    if tmp_res["status"] == "ok":
        completed.append("tmp-cleanup")
    elif tmp_res["status"] == "failed":
        skipped.append("tmp-cleanup")
        warnings.append(
            f"scratch 清理失败:{tmp_res['error']} · 不影响交付 · "
            f"手动 rm -rf {tmp_res['path']}")
    else:
        skipped.append("tmp-cleanup")

    _git(["fetch", "--prune", "origin"], cwd=main_wt, timeout=60)  # remote-tracking 残影清理

    # ── Step 4:main-sync(纯清理 · 零内容)─────────────────────────
    main_sync_status = "skipped"
    main_sync_note = ""
    main_sync_decision: Optional[dict] = None
    byproduct_commit = None
    cur = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=main_wt)
    cur_branch = cur.stdout.strip() if cur.returncode == 0 else ""
    if cur_branch != merge_target:
        warnings.append(
            f"主工作区当前在 {cur_branch!r} 分支(非 {merge_target})· 已 fetch 未 pull · "
            f"需要时自行 git checkout {merge_target} && git pull --ff-only")
        main_sync_status = "wrong_branch"
        main_sync_note = f"在 {cur_branch!r} 分支 · 非 {merge_target}"
    else:
        completed.append("main-sync")
        dirty = _classify_main_sync_dirty(main_wt, None, state)
        # 防御:主工作区理论上不再出现 feature artifacts(新架构从未物化)· 出现即清
        if dirty["feature_artifacts"]:
            failed = _main_sync_clean_feature_artifacts(main_wt, merge_target, dirty)
            if failed:
                warnings.append(
                    f"feature_artifacts checkout origin 失败({len(failed)}):"
                    f"{', '.join(failed[:5])}")
        # 副产物自动 commit(用户拍板:注入块/锁 不走 stash 大戏 · 直接安顿)
        byproducts = dirty["bootstrap_pointers"] + dirty["harness_locks"]
        if byproducts:
            _git(["add", "--", *byproducts], cwd=main_wt, timeout=30)
            cm = _git(["commit", "-m",
                       f"chore(teamwork): ship2 净化 · bootstrap 注入块/锁({feature_id})"],
                      cwd=main_wt, timeout=30)
            if cm.returncode == 0:
                byproduct_commit = git_head(cwd=main_wt) or ""
            else:
                warnings.append(
                    f"副产物自动 commit 失败:{cm.stderr.strip()[:100]} · 文件保留工作区")
        # 用户真改动:auto/yolo 自动净化(stash-pull)· 普通模式决策面板
        if dirty["other_files"]:
            if state.get("auto_mode") or state.get("yolo"):
                res = _main_sync_apply_strategy(
                    main_wt, merge_target, None, state, "stash-pull")
                main_sync_status = f"auto_{res['status']}"
                main_sync_note = "无人值守自动净化(stash-pull)· " + res["note"]
                warnings.extend(res["warnings"])
            else:
                main_sync_status = "user_dirty_decision"
                main_sync_note = (
                    f"主工作区有 {len(dirty['other_files'])} 个用户改动 · "
                    "⏸️ 等用户决策是否净化(见 main_sync_decision)")
                main_sync_decision = _build_main_sync_decision(
                    args.feature, merge_target, state, dirty, pulled=False)
        # 同步:有本地 commit(副产物/用户先前的)→ pull --rebase + push;否则 ff-pull
        ba = _behind_ahead(main_wt, merge_target)
        ahead = ba[1] if ba else 0
        if main_sync_status != "user_dirty_decision":
            if ahead > 0:
                pl = _git(["pull", "--rebase", "origin", merge_target],
                          cwd=main_wt, timeout=120)
                if pl.returncode != 0:
                    _git(["rebase", "--abort"], cwd=main_wt, timeout=30)
                    warnings.append(
                        f"git pull --rebase 失败(已 abort):{pl.stderr.strip()[:100]} · "
                        f"{_pull_failure_remedy(main_wt, merge_target)}")
                    main_sync_status = "rebase_failed"
                else:
                    ps = _git(["push", "origin", merge_target], cwd=main_wt, timeout=120)
                    if ps.returncode != 0:
                        warnings.append(
                            f"git push 被拒(保护分支?):{ps.stderr.strip()[:120]} · "
                            f"本地 commit 保留 · 走 MR 合入或按分支策略处理")
                        main_sync_status = "pulled_push_rejected"
                        main_sync_note = "已 pull --rebase · push 被拒 · 本地 commit 待走 MR"
                    else:
                        main_sync_status = "cleaned_pulled_pushed"
                        main_sync_note = "副产物已 commit · pull --rebase · push · 主工作区干净+最新"
            else:
                pl = _git(["pull", "--ff-only", "origin", merge_target],
                          cwd=main_wt, timeout=120)
                if pl.returncode != 0:
                    remedy = _pull_failure_remedy(main_wt, merge_target)
                    warnings.append(f"git pull --ff-only 未通过 · {remedy} · "
                                    f"原始错误:{pl.stderr.strip()[:100]}")
                    main_sync_status = "diverged"
                    main_sync_note = remedy
                elif main_sync_status == "skipped":
                    main_sync_status = "ff_pulled"
                    main_sync_note = "主工作区已 ff-pull 到最新"

    # ── teamwork stash 盘点(v8.144)──
    tw_stashes = _list_teamwork_stashes(main_wt)
    if tw_stashes:
        warnings.append(
            f"主工作区残留 {len(tw_stashes)} 个 teamwork 自动 stash:"
            f"{';'.join(tw_stashes[:4])}{' …' if len(tw_stashes) > 4 else ''} · "
            f"逐个 `git stash show -p <ref>` 核对:要恢复 → pop;确认冗余 → drop")

    zip_hint = ""
    fp = _archive_repo_paths(main_wt, feature_dir, feature_id)
    if fp:
        zip_hint = fp[1]

    # ── 流程质量审计落 ~/.teamwork/audit/(框架跨项目搜集)· AI 静默补判断 ──
    audit_record = _write_audit_record(state, feature_id, merge_target, main_wt,
                                       getattr(args, "main_model", None), audit_sources)

    emit_json({
        "verdict": "PASS",
        "command": "ship-finalize",
        "feature_id": feature_id,
        "merge_target": merge_target,
        "completed_steps": completed,
        "skipped_steps": skipped,
        "tmp_cleanup": tmp_res,
        "worktree_removed": wt_removed,
        "main_sync_status": main_sync_status,
        **({"main_sync_note": main_sync_note} if main_sync_note else {}),
        **({"main_sync_decision": main_sync_decision} if main_sync_decision else {}),
        **({"byproduct_commit": byproduct_commit} if byproduct_commit else {}),
        **({"teamwork_stashes": tw_stashes} if tw_stashes else {}),
        **({"archive_zip": zip_hint} if zip_hint else {}),
        **({"audit_record": audit_record} if audit_record else {}),
        **({"warnings": warnings} if warnings else {}),
        "next_action_brief": (
            f"✅ ship2 清场完成({feature_id})。"
            + (f"\n⏸️ 主工作区有用户改动待决策(见 main_sync_decision · PMO 转 R5(b) 暂停点)。"
               if main_sync_decision else "")
            + (f"\n📊 流程质量审计草稿已落 {audit_record}(框架跨项目搜集用)· "
               f"🔴 **静默补完三段判断**(做的好的 / 发现的问题 / 待优化的 · 照实抄草稿内"
               f"**『源材料摘录』段 + 实际数据** · 🔴 **无需 unzip 归档**〔worktree 删除前已抽入草稿〕· "
               f"空写「无」)· 改 frontmatter audit_status: done · **不暂停不等确认 · 写完即结束**。"
               if audit_record else "")
            + (f"\n📋 收尾 digest(纯输出 · 不暂停):按 stages/ship-stage.md §16 读 "
               f"{zip_hint or '_archive/<id>.zip'} 出 ≤10 行流程价值反思。" )
        ),
    })


# ─── argparse 注册 ──────────────────────────────────────────────



def _mr_state(mr_url: str) -> str:
    """查 MR/PR 状态 → 'MERGED' / 'OPEN' / 'CLOSED' / 'UNKNOWN'(命令失败)。GitHub gh / GitLab glab。"""
    try:
        if "github.com" in mr_url:
            r = _git_run(["gh", "pr", "view", mr_url, "--json", "state"], timeout=30)
            if r.returncode == 0:
                return (json.loads(r.stdout).get("state") or "UNKNOWN").upper()
        else:
            r = _git_run(["glab", "mr", "view", mr_url, "-F", "json"], timeout=30)
            if r.returncode == 0:
                st = (json.loads(r.stdout).get("state") or "").lower()
                return {"merged": "MERGED", "opened": "OPEN", "closed": "CLOSED"}.get(st, "UNKNOWN")
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return "UNKNOWN"


def _git_run(cmd, timeout=30):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def cmd_await_merge(args: argparse.Namespace) -> None:
    """v8.198:MR 等待窗轮询(30s)· 合并即自动进下一步(ship-finalize / 规划 finalize)。

    治本(loops 对照):ship1/规划收尾停在「等用户合并」是无人看的结构性等待窗(实证 132h 长尾 ·
    CI 红无人接)。本命令把等待窗变成 time-based loop:每 --interval 查一次 · MERGED → emit 下一步;
    一轮 --max-checks 用尽仍 OPEN → emit WAITING(AI 重跑本命令续等 · 用户随时可打断)。
    """
    mr_url = (getattr(args, "mr_url", None) or "").strip()
    feature = getattr(args, "feature", None)
    if not mr_url and feature:
        try:
            _, st = load_state(feature)
            mr_url = (st.get("ship", {}) or {}).get("mr_url") or ""
        except Exception:
            pass
    if not mr_url:
        emit_json({"verdict": "FAIL", "command": "await-merge",
                   "error": "无 MR URL(--mr-url 直传 · 或 --feature 的 state.ship.mr_url)"}, exit_code=1)
    interval = max(5, int(getattr(args, "interval", 30) or 30))
    max_checks = max(1, int(getattr(args, "max_checks", 18) or 18))
    unknown_streak = 0
    for i in range(max_checks):
        stt = _mr_state(mr_url)
        if stt == "MERGED":
            nxt = ("state.py ship-finalize --feature <worktree 内 feature 路径>(ship2 清场)"
                   if feature else
                   "规划 finalize:cd 主工作区 → git worktree remove <planning-worktree> → "
                   "state.py main-sync --merge-target <mt>")
            emit_json({"verdict": "MERGED", "command": "await-merge", "mr_url": mr_url,
                       "checks": i + 1,
                       "next_action": f"🔴 已合并 · 自动进下一步:{nxt}"})
        if stt == "CLOSED":
            emit_json({"verdict": "CLOSED", "command": "await-merge", "mr_url": mr_url,
                       "hint": "MR 被关闭未合并 · surface 用户(close-unmerged / 重开)"}, exit_code=1)
        unknown_streak = unknown_streak + 1 if stt == "UNKNOWN" else 0
        if unknown_streak >= 3:
            emit_json({"verdict": "FAIL", "command": "await-merge", "mr_url": mr_url,
                       "error": "连续 3 次查询失败(gh/glab 未装或未登录?)",
                       "hint": "修环境后重跑 · 或退回人工「合并后告诉我」"}, exit_code=1)
        if i < max_checks - 1:
            time.sleep(interval)
    emit_json({"verdict": "WAITING", "command": "await-merge", "mr_url": mr_url,
               "checks": max_checks, "interval_sec": interval,
               "next_action": "仍未合并 · 重跑本命令续等(AI 应自动重跑 · 用户随时可打断改人工)"})


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

    # action=archive 参数(v8.145 ship1 终幕 · 归档+翻牌进 feature 分支)
    sp.add_argument("--planning-artifacts",
                    help=("[archive] 逗号分隔 · 规划层 back-ref 翻牌文件(worktree 相对路径)· "
                          "随 feature MR 原子合入 · AI 先在 worktree 内翻牌再传"))
    sp.add_argument("--no-planning-changes", action="store_true",
                    help="[archive] 显式声明无规划层可翻(ad-hoc Bug/Micro · 无关联 BL)")
    sp.add_argument("--archive-desc",
                    help="[archive] ≤200 字极简 feature 描述 · 写归档 INDEX.md · 超长 FAIL")

    # action=close-unmerged 参数
    sp.add_argument("--abandon", action="store_true",
                    help="[close-unmerged] 彻底放弃 Feature → shipped=abandoned")
    sp.add_argument("--reason",
                    help="[close-unmerged] INFO concerns 说明")

    sp.set_defaults(func=cmd_ship_phase)

    # ─── ship-finalize:ship2 主工作区清场(v8.145 · 零内容修改)──────
    fp = sub.add_parser(
        "ship-finalize",
        help=("[v8.145] ship2 主工作区清场(零内容):verify-delivered(zip 在 origin)"
              "→ worktree 删 → main-sync(副产物自动 commit · 用户改动决策 · pull/push)· "
              "可重入 · 必在主工作区跑 · ship1 交付全在 worktree(archive+push)"),
    )
    fp.add_argument("--feature", required=True,
                    help="worktree 内 feature 目录路径(接力卡 state.json 所在 · 已删则幂等判定)")
    fp.add_argument("--main-model", default=None,
                    help="主对话(PMO)模型 · PMO 声明(它知道自身 model · 如 claude-opus-4-8)· "
                         "写入 audit 实际数据 · 缺省只记 host · 供 harvest 按模型分析流程质量")
    fp.set_defaults(func=cmd_ship_finalize)

    # ─── main-sync:主工作区净化(v8.70)─────────────────────────────
    # 治本:ship-finalize step 7 发现主工作区有用户改动时 · 旧逻辑仅「保留 + WARN」·
    # 停在脏态。现在 ship-finalize surface「是否净化」决策 · 用户拍板后跑本命令执行。
    ms = sub.add_parser(
        "main-sync",
        help=("[v8.70/v8.145] 主工作区净化(ship2 user-dirty 决策执行)· "
              "--strategy commit-push|stash-pull|skip · 必在主工作区跑 · "
              "v8.145 起不依赖 feature(接力卡可已消亡)"),
    )
    ms.add_argument("--feature", required=False,
                    help="(可选)feature 目录 · 接力卡在则读 merge_target/feature_id")
    ms.add_argument("--merge-target",
                    help="(可选)目标分支 · 缺省:接力卡 → 主工作区当前分支")
    ms.add_argument("--strategy", required=True,
                    help="净化策略:commit-push / stash-pull / skip")
    ms.add_argument("--message", help="commit-push 时的 commit message(可选)")
    ms.add_argument("--drop-stashes", action="store_true",
                    help="[v8.190] 全清 teamwork main-sync auto-stash(用户确认不需要任何备份)· "
                         "默认只 drop 可证冗余的(空/内容已在分支)")
    ms.set_defaults(func=cmd_main_sync)

    # v8.198:await-merge MR 等待窗轮询(30s · 合并自动下一步 · time-based loop)
    am = sub.add_parser("await-merge",
                        help="[v8.198] 轮询 MR 状态(默认 30s×18)· MERGED→emit 下一步(ship-finalize/规划 finalize)· WAITING→重跑续等")
    am.add_argument("--feature", help="feature 路径(读 state.ship.mr_url)· 与 --mr-url 二选一")
    am.add_argument("--mr-url", help="MR/PR URL 直传(规划收尾等无 state 场景)")
    am.add_argument("--interval", type=int, default=30, help="轮询间隔秒(默认 30)")
    am.add_argument("--max-checks", type=int, default=18, help="单次命令最多查几轮(默认 18≈9min · 用尽 emit WAITING 重跑)")
    am.set_defaults(func=cmd_await_merge)
