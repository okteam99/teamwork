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


def _is_main_branch(branch: str, repo_cwd: Optional[str] = None) -> bool:
    """branch 是否是主分支(yolo 硬约束:自动 merge 不得直接进 main)。
    判定:名字 ∈ {main, master} · 或 == 远端默认分支(origin/HEAD 指向)。"""
    if not branch:
        return False
    b = branch.strip().lower()
    if b in ("main", "master"):
        return True
    try:
        r = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=repo_cwd, capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            default = r.stdout.strip().rsplit("/", 1)[-1].lower()  # refs/remotes/origin/main → main
            if default and default == b:
                return True
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return False


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

    # v8.65:yolo 可携带 merge_target 分支(--yolo <branch>)· 覆盖 --merge-target / localconfig 默认
    # nargs='?':args.yolo = None(未传)/ True(--yolo 无值)/ str(--yolo <branch>)
    yolo_branch = args.yolo if isinstance(args.yolo, str) and args.yolo.strip() else None
    yolo_enabled = args.yolo is not None
    merge_target = yolo_branch or args.merge_target
    if not merge_target:
        die(2, json.dumps({
            "verdict": "FAIL",
            "action": "init-feature",
            "error": "缺 merge_target",
            "hint": ("传 --merge-target <branch> · 或 yolo 用 --yolo <branch>"
                     "(该分支即本需求 merge_target · 覆盖 localconfig 默认)"),
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

    # v8.63:yolo 模式硬约束 —— merge_target 必须非主分支(自动 merge 不得直接进 main)
    # v8.65:merge_target 可来自 --yolo <branch>(已 resolve 进 merge_target)
    if yolo_enabled and _is_main_branch(merge_target):
        die(2, json.dumps({
            "verdict": "FAIL",
            "action": "init-feature",
            "error": (
                f"yolo 模式禁止 merge_target 是主分支({merge_target!r})—— "
                f"yolo 会**无人 review 自动 merge MR** · 不得直接合进 main/master/远端默认分支"
            ),
            "hint": (
                "yolo 必须合到**非主分支**(如 dev / staging / integration)· 再由人工 gate "
                "该分支 → main 的提升。改 --merge-target <非主分支> 重跑;若确需合 main · "
                "别用 --yolo(改 --auto-mode · 保留 MR merge 人工 stop)。"
            ),
            "rule": "v8.63 yolo 硬约束 · 自动 merge 不进 main(防 AI 错误/幻觉特性直接进 main)",
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

    # v8.79:撞号硬校验(R0 物化 · 治本 AON 13 组实测撞号 · 分布式 max+1 race 兜底)
    # 目标 {PREFIX}-{字母}{number} 已被**另一**兄弟目录占用 → FAIL(同 clone 内兜;跨 clone 靠 utc 策略)
    _collision = _detect_id_collision(feature_dir, args.feature_id)
    if _collision and not args.force:
        die(2, json.dumps({
            "verdict": "FAIL",
            "action": "init-feature",
            "error": (
                f"artifact 号段撞号:{_collision['number_id']} 已被现存目录 "
                f"{_collision['existing']!r} 占用 · 与本次 {feature_dir.name!r} 同号"
            ),
            "hint": (
                "另一 feature 已占该号段(多 agent/多机并行 race)· 换号重建:\n"
                "  重跑 prepare-check 取新 next_available_id_stem · 改 --feature / --feature-id 后再 init。\n"
                "  (utc 时间戳策略:重跑即得新秒级号 · sequential 策略:取 max+1 避让 existing_ids)"
            ),
            "collision": _collision,
            "rule": "v8.79 撞号硬校验 · 可枚举规则进脚本(R0)· 治本分布式 max+1 race",
            "bypass": "确属同号续作(罕见):--force 跳过撞号校验",
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
        "merge_target": merge_target,
        "worktree": {
            "strategy": args.worktree_mode,
            "branch": args.branch,
            "path": args.worktree_path,
            "base_branch": f"origin/{merge_target}",
            "created_at": now_iso(),
        },
        "environment_config": {
            "worktree_mode": args.worktree_mode,
            "branch": args.branch,
            "merge_target": merge_target,
            "base": f"origin/{merge_target}",
            "executed_at": now_iso(),
        },
        # v8.63:yolo implies auto_mode(完全自动是 auto_mode 的超集)· v8.65:yolo_enabled(nargs='?')
        "auto_mode": args.auto_mode or yolo_enabled,
        "yolo": yolo_enabled,
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
                    f"  1. git worktree add -b {args.branch} {wt_real} origin/{merge_target}\n"
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


def _read_id_strategy(start: Path) -> str:
    """读项目根 `.teamwork_localconfig.json` 的 `id_strategy`(v8.79)。

    从 `start` 向上逐级找 `.teamwork_localconfig.json`(到 `.git` 项目边界为止)·
    命中且值合法则用之 · 否则用默认。
    - 默认 = `utc-yymmddhhmmss`(v8.79 起 · 治本分布式 `max+1` 撞号 · 详 docs/conventions.md §1)。
    - opt-out = `sequential`(旧顺序号 `max+1` · 单 clone 项目可保留好念的短序号)。
    """
    DEFAULT = "utc-yymmddhhmmss"
    VALID = {"sequential", "utc-yymmddhhmmss"}
    try:
        node = start.resolve()
    except OSError:
        return DEFAULT
    for d in [node, *node.parents]:
        cfg = d / ".teamwork_localconfig.json"
        if cfg.exists():
            try:
                strat = json.loads(cfg.read_text(encoding="utf-8")).get("id_strategy")
            except (OSError, json.JSONDecodeError):
                return DEFAULT
            return strat if strat in VALID else DEFAULT
        if (d / ".git").exists():
            break  # 到项目边界仍无配置 → 默认
    return DEFAULT


def _read_disable_heterogeneous_review(start) -> bool:
    """读项目根 `.teamwork_localconfig.json` 的 `disable_heterogeneous_review`(v8.90)。

    从 `start` 向上找 `.teamwork_localconfig.json`(到 `.git` 边界止)· 默认 **false**(异质开)。
    true = 单模型用户主动禁用异质评审 → external-review 自动用宿主自身模型 exec 自审(降级 ·
    写 external-cross-review/ 满足 P0-154 但 frontmatter 标 degraded)· 每次 bootstrap 启动 WARN。
    与 v8.88 `--self-review-fallback`(异质暂时不可用的临时 stopgap · 落 self-review/ · 不满足门禁)
    区分:本项是**项目级长期策略**(用户接受质量下降 · 已被 startup WARN 持续提醒)。
    """
    try:
        node = Path(start).resolve()
    except OSError:
        return False
    for d in [node, *node.parents]:
        cfg = d / ".teamwork_localconfig.json"
        if cfg.exists():
            try:
                val = json.loads(cfg.read_text(encoding="utf-8")).get("disable_heterogeneous_review")
            except (OSError, json.JSONDecodeError):
                return False
            return bool(val) if isinstance(val, bool) else False
        if (d / ".git").exists():
            break
    return False


def _detect_id_collision(feature_dir: Path, feature_id: str) -> "dict | None":
    """撞号硬校验(v8.79 · R0 物化 · 治本 AON 13 组实测撞号)。

    扫 `feature_dir` 的兄弟目录 · 若有**另一**目录共享同 `{PREFIX}-{字母}{number}`
    号段(同名 = 自身 · re-init/force · 不算撞)→ 返回撞号详情 · 否则 None。
    注:仅兜**同 clone** race;跨 clone(各自看不到对方在途目录)的撞号此处兜不住 —— 合并时才现 ·
    故 `utc-yymmddhhmmss` 才是跨 clone 的根治。两层互补 · 详 docs/conventions.md §1。
    """
    import re as _re
    m = _re.match(r"^(.+?-[FBM]\d+)", feature_id)
    if not m:
        return None
    number_id = m.group(1)  # e.g. PTR-F045 / SVC-PLATFORM-F260601143012
    root = feature_dir.parent
    if not root.exists():
        return None
    self_name = feature_dir.name
    # number_id 后必接非数字或结尾(防 PTR-F045 误匹配 PTR-F0451-*)
    pat = _re.compile(rf"^{_re.escape(number_id)}(?:\D|$)")
    for child in root.iterdir():
        if child.is_dir() and child.name != self_name and pat.match(child.name):
            return {"number_id": number_id, "existing": child.name}
    return None


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

    # v8.79:号段分配按 id_strategy(默认 utc 时间戳 · opt-out sequential · 详 docs/conventions.md §1)
    id_strategy = _read_id_strategy(root)
    if id_strategy == "sequential":
        # 顺序号 max+1(连续递增 · 不填空洞)· ⚠️ 分布式 race 隐患 · 靠 init-feature 撞号硬校验兜
        next_num = (max(used_numbers) + 1) if used_numbers else 1
        next_id_stem = f"{prefix}-{id_letter}{next_num:03d}"
    else:  # utc-yymmddhhmmss(默认 v8.79)· UTC0 秒级时间戳 · 跨机分布式免协调
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%y%m%d%H%M%S")
        next_num = int(ts)
        next_id_stem = f"{prefix}-{id_letter}{ts}"

    payload = {
        "verdict": "OK",
        "command": "prepare-check",
        "features_root": str(root),
        "feature_id_prefix": prefix,
        "id_letter": id_letter,
        "existing_ids": existing_ids,
        "existing_count": len(existing_ids),
        "id_strategy": id_strategy,
        "next_available_number": next_num,
        "next_available_id_stem": next_id_stem,
        "hint": (
            f"prepare 暂停点 artifact ID 默认填 {next_id_stem}-<Kebab-Case-名称> · "
            f"用户可改 · 但应避开 existing_ids 中已占编号"
            + (" · 🕐 id_strategy=utc-yymmddhhmmss(UTC 秒级时间戳 · 已生成勿手算 · 重跑得新号)"
               if id_strategy != "sequential"
               else " · id_strategy=sequential(顺序号 max+1)")
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
        "⚠️ 加减须有**本 Feature 特定理由** · 不是套路化删角色 —— 尤其 **pl 默认保留**"
        "(产品方向视角)·『无 ROADMAP』**不是**去 pl 的理由(ROADMAP=规划层 · 与 PRD 产品方向"
        "评审无关)· 仅纯内部/技术重构无产品面才去 pl。"
        "case 实证(F-Bv2-8 · 2026-05-25):PMO 第一次直接抄默认 · 经用户提示后二次思考才识别 "
        "ui_design 跳过(后端先行)/ blueprint 强 external(跨 5 module 触发点)等调整。"
    )

    # v8.44.4:host-aware 输出风格 hint(治本 case 2026-05-28 codex-cli 渲染 markdown 表格失败)
    # case:AI emit markdown 表格 · codex-cli terminal 显示成 raw 字符 · 用户提示后才改 box-drawing
    # 治本:prepare-check 物化 host 检测 · emit 风格 hint · PMO 看 hint 决定默认表达方式
    detected_host, host_source = _detect_host(None)  # prepare-check 无 feature · 仅看 audit/env
    payload["output_style_hint"] = _build_output_style_hint(detected_host)

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
        "question": ("本 Feature 有无产品方向影响?(业务目标 / 用户可见行为 / 商业模式 / "
                     "跨项目一致性 / 变更级联 Level≥2 —— 任一即『有』)"),
        "if_yes": ("goal **保留 pl**(默认 · 常态)· PL 审产品方向对齐 —— "
                   "telos:防『做了一堆 Feature 但偏离产品方向』"),
        "if_no": ("仅『纯内部 / 技术重构 · 零产品面 · 零跨项目 · 变更级联 Level-1 局部』"
                  "才去 pl(少数例外)· ⚠️ **别拿『无 ROADMAP』当借口去 pl** —— "
                  "ROADMAP 是规划层产物 · 与 PL 的 PRD 评审价值(产品方向)无关 · "
                  "二者不是一回事"),
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


# v8.44.4:host-aware 输出风格 hint(治本 case 2026-05-28 codex-cli 渲染 markdown 表格失败)
# - claude-code:rich markdown 渲染 OK · 表格 / 加粗 / emoji 都好
# - codex-cli / gemini-cli / unknown:terminal renderer 对复杂 markdown 表格容易破
#   推荐 box-drawing(┌─┬─┐│├─┤└─┘)绘制表格 / 纯文本列表 · 避免 raw 字符显示
HOST_OUTPUT_STYLE_PROFILES = {
    "claude-code": {
        "style_id": "markdown_ok",
        "description": "Rich markdown 渲染 OK · 表格 / 加粗 / emoji / code block 都好",
        "table_format": "markdown",  # | col | col | + |---|---|
        "list_format": "markdown",
        "emphasis": "markdown",      # **粗** / *斜* / `code`
        "emoji_safe": True,
    },
    "codex-cli": {
        "style_id": "box_drawing_or_plain",
        "description": ("Terminal renderer 对复杂 markdown 表格容易破(raw 字符显示)· "
                        "推荐 box-drawing(┌─┬─┐│├─┤└─┘)绘制表格 / 纯文本 key: value 列表"),
        "table_format": "box_drawing",  # ┌─┬─┐│├─┤└─┘
        "list_format": "plain",         # "- " / "1. " · 不嵌套粗体
        "emphasis": "plain",            # 不用 ** 加粗 · 改用 "🔴 " 前缀 / 大写 / 缩进
        "emoji_safe": True,             # emoji 可用(case 实证)
    },
    "gemini-cli": {
        "style_id": "box_drawing_or_plain",  # 保守同 codex-cli
        "description": "未实测 · 保守用 box-drawing(同 codex-cli profile)",
        "table_format": "box_drawing",
        "list_format": "plain",
        "emphasis": "plain",
        "emoji_safe": True,
    },
    "unknown": {
        "style_id": "box_drawing_or_plain",  # 默认保守
        "description": "host 未知 · 保守用 box-drawing(最大兼容)",
        "table_format": "box_drawing",
        "list_format": "plain",
        "emphasis": "plain",
        "emoji_safe": True,
    },
}


def _build_output_style_hint(host: Optional[str]) -> dict:
    """v8.44.4:按 host 返回输出风格 hint dict · PMO emit 暂停点时按此风格。

    返:
      {host, style_id, description, table_format, list_format, emphasis, emoji_safe, rationale}

    PMO 看 hint 决定:
    - codex-cli host → 表格用 box-drawing · 不用 markdown · 避免 raw 字符显示
    - claude-code host → markdown 表格 OK · 用 markdown 更紧凑
    """
    h = host or "unknown"
    profile = HOST_OUTPUT_STYLE_PROFILES.get(h, HOST_OUTPUT_STYLE_PROFILES["unknown"])
    return {
        "host": h,
        "style_id": profile["style_id"],
        "description": profile["description"],
        "table_format": profile["table_format"],
        "list_format": profile["list_format"],
        "emphasis": profile["emphasis"],
        "emoji_safe": profile["emoji_safe"],
        "rationale": (
            "treat host 渲染能力为客观信号 · prepare-check 物化检测 + emit hint · "
            "PMO 按 hint 选默认表达方式 · 避免每次被用户提示后才改"
            "(治本 case 2026-05-28 codex-cli markdown 表格失败)"
        ),
    }


# v8.46 C:Feature Planning 物化入口(治本未物化漏洞 · 用户洞察 2026-05-28)
# 根因:Feature Planning 不进状态机 · 无 state.py 兜底 · PRODUCT-OVERVIEW-INTEGRATION.md / feature-planning.md
# 纯靠 AI 自觉读 → AI 没读就不按规范(不维护规划状态表 / 草稿态误影响下游)。
# planning-check 不进状态机(不写 state.json)· 纯 emit checklist + 必读规范 · 物化「你必须想这件事」。
PLANNING_CHECKLIST = [
    {"item": "🔴 拆 BL/WS 前调研实际代码现状:每个候选 BL 核验「已做什么 / 真缺口在哪」· 反映真实完成度(不把已完成列 todo · 不把有脚手架的当 greenfield)· decisive 前提(数据是否真入库 / 能力是否真生效)核验实际代码 · 不轻信 Explore/sub-agent 摘要 · 🔴 需 live 数据(查 DB/log)先读 project-specs/TROUBLESHOOTING.md 拿连法,别凭 .env/启动脚本瞎试",
     "spec": "feature-planning.md §2 Step 1"},
    {"item": "范围判定:工作区级(改 teamwork-space.md + 多 PROJECT.md)vs 子项目级(单 PROJECT.md + ROADMAP.md + sitemap.md)",
     "spec": "feature-planning.md §2 Step 2"},
    {"item": "🎨 全景UI初步规划(本轮涉 UI 时 · 🔴 拆 WS 之前出):在 {子项目}/docs/design/preview-project/ 出/扩 design system + 本轮关键页(初步 · 系统+代表页 · 非每页 · 防瀑布 · 跑 preview.sh 看)+ 同步 sitemap.md(IA 地图 · 只写层级/导航不写视觉)· 完成产生 git diff = 拆 WS 的输入;非 UI 轮跳过(下游 WS 标 全景初规:N-A)",
     "spec": "feature-planning.md §2 Step 5"},
    {"item": "核心产出 WS(product-overview/workstream/WS-NN.md · 1..N 个 · 输入=全景diff+业务目标 · 承接 1+ 执行线 · 拆一组 feature · 🔴 每 WS 记 全景初规状态(✅/N-A)+ 覆盖的全景页清单)· 0-1 时含业务架构与产品规划.md(愿景+执行线列表)· 🔴 不出代码(R6)· 不进 stage 链",
     "spec": "feature-planning.md §2 Step 6 + templates/workstream.md"},
    {"item": "WS 拆出的 feature 写入 ROADMAP(BL-NNN · 关联 WS)· feature 全写入 = WS ✅ 规划完成 · 每个 BL 后续用户拍板走 prepare 启动 Feature",
     "spec": "conventions.md §4 + prepare.md §5"},
    {"item": "🔴 规划完成必 emit R5 暂停点问用户是否提交 push(WS + ROADMAP 登记是未提交工作树改动 · 不擅自 commit 也不放任悬着)· 主工作区直推或开 MR · 不走 ship 流程",
     "spec": "feature-planning.md §2 Step 8"},
]


def cmd_planning_check(args: argparse.Namespace) -> None:
    """v8.46:Feature Planning 物化入口 · emit 规划 checklist + 必读规范(不进状态机)。

    治本 Feature Planning 未物化漏洞:规划路径无 stage 兜底 · PRODUCT-OVERVIEW-INTEGRATION /
    feature-planning 纯靠 AI 自觉读。本命令物化"你必须想这件事"(像 prepare-check)·
    检测 product-overview/ 存在 → emit 规划状态机 + 必读 · 不存在 → 仍 emit 基础 checklist。
    """
    # project_root:--project-root 显式 · 否则 find_project_root(cwd)
    project_root = None
    if getattr(args, "project_root", None):
        project_root = Path(args.project_root).expanduser().resolve()
    else:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from bootstrap import find_project_root
            project_root = find_project_root(Path.cwd())
        except Exception:
            project_root = Path.cwd()

    po_dir = project_root / "product-overview"
    po_exists = po_dir.is_dir()

    # v8.48:PRODUCT-OVERVIEW-INTEGRATION.md 是产品规划权威 · 总 must_read
    #   (无 po 时学怎么冷启动初创 · 有 po 时学状态管理 + 与 teamwork-space 派生关系)
    must_read = ["PRODUCT-OVERVIEW-INTEGRATION.md", "docs/feature-planning.md"]

    payload = {
        "verdict": "OK",
        "command": "planning-check",
        "project_root": str(project_root),
        "product_overview_exists": po_exists,
        "must_read": must_read,
        "entry_criteria": {
            "keyword": "规划 / 拆 roadmap / 路线图 / 全景 / 商业模式调整 / 做电商 / 做 SaaS",
            "complexity_force_upgrade": (
                "关键词命中 Feature/敏捷需求/Micro 时 · 命中任一强制升 Feature Planning:"
                "跨仓库联动(≥2)/ 数据模型重构 / 老需求架构性废弃 / 影响 ≥2 BL / 方向级业务变更"
            ),
        },
        "planning_checklist": PLANNING_CHECKLIST,
        "planning_order": (
            "🔴 权威链路(详 SKILL.md § teamwork 业务流程架构):业务架构与产品规划(愿景+执行线列表)"
            "→ ✅确认派生 teamwork-space.md →(涉 UI)全景UI初步规划(preview-project + sitemap · 拆 WS 前)"
            "→ WS(workstream/ · 1..N · 承接 1+ 执行线 · 拆一组 feature · 每 WS 记 全景初规状态)"
            "→ feature 写入 ROADMAP(BL · 关联 WS · 全写入=WS✅规划完成)→ 用户拍板 BL → prepare+init-feature → F。"
            "teamwork-space.md **不是** Feature Planning 产出 · 由 product-overview「✅ 已确认」内容派生"
        ),
        "key_constraints": [
            "🔴 不进状态机:init-feature --flow-type 'Feature Planning' 会被 reject",
            "🔴 不出代码(R6 红线)· 产出仅项目级文档",
            "BL-NNN 在规划期分配 · 不是 Feature ID(无 PRD/TC/TECH)",
        ],
        "next_hint": (
            f"先读 {' + '.join(must_read)} · 按 checklist 在主对话执行 Feature Planning"
            f"(不进状态机 · PMO 直接做)· 完成后拆出的 BL 用户拍板再走 prepare 启动 Feature"
        ),
    }

    if po_exists:
        # 项目有 product-overview/ → emit 规划状态机(治本"草稿态误影响下游")
        payload["planning_state_machine"] = {
            "states": ["📝 草稿", "🔄 讨论中", "⏸️ 待确认", "✅ 已确认"],
            "downstream_rule": (
                "🔴 仅「✅ 已确认」内容才影响 teamwork-space.md / 下游执行 · "
                "草稿/讨论中/待确认 都不更新 teamwork-space.md"
            ),
            "required_tables": [
                "每份 product-overview 文档头部:规划状态表(文档状态 / 最近更新 / 待决议题)",
                "文档末尾:规划议题追踪表(编号 / 议题 / 状态 / 结论 / 影响章节 / 日期)",
            ],
        }
        payload["product_overview_hint"] = (
            f"本项目有 product-overview/({po_dir})· 规划必维护规划状态表 + 议题追踪 · "
            f"详 PRODUCT-OVERVIEW-INTEGRATION.md(加载规则 + 状态管理 + 与 teamwork-space 关系)"
        )
    else:
        # v8.48:无 product-overview → 产品规划优先(不再说"可直接拆 ROADMAP" · 那把上游当 optional)
        payload["product_overview_hint"] = (
            f"本项目无 product-overview/ · 🔴 冷启动权威顺序 = 产品规划优先:先建 product-overview"
            f"(PL 引导模式 · 产品定位/业务架构/执行手册 · 见 PRODUCT-OVERVIEW-INTEGRATION.md 建议章节 + 裁剪规则)"
            f"→ ✅确认派生 teamwork-space.md → 再拆 ROADMAP。单 Feature 极简项目用户可拍板跳过 · 直接拆 ROADMAP"
        )

    emit(payload)


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

    # v8.66:yolo 去 external 评审 = 拆无人值守唯一安全网 → 默认禁止(非必要不得去)
    # 治本 case(WS-002 yolo):AI 把 yolo 当"简化/提速" · change-review-roles 去 goal/blueprint
    # external 美其名"集中到 review stage" —— 无人值守下这是拆掉唯一跨模型把关 · 反了。
    if (state.get("yolo") and "external" in before and "external" not in roles_list
            and not getattr(args, "accept_external_removal", False)):
        die(2, json.dumps({
            "verdict": "FAIL",
            "command": "change-review-roles",
            "error": (
                f"yolo 模式禁止从 {args.stage} 去掉 external 异质模型评审 —— "
                f"无人值守下 external 是**唯一安全网** · 非必要不得去"
            ),
            "hint": (
                "🔴 yolo 不是简化/提速 · 是无人值守下**更严**的自动把关:\n"
                "  ① 优先:别去 external · 让 external 评审照常跑(CLI 真不可用先重试 / 修环境)\n"
                "  ② 仅当 external CLI 客观不可用(未装 / 网络死 · 已重试失败)才加 "
                "--accept-external-removal --reason '<具体技术原因 + 重试失败证据>'\n"
                "  🔴 不得以「集中到 review 代码 stage」「效率」「价值低」为由去 external "
                "(= 擅自简化 · 违 yolo 加重审核原则)"
            ),
            "rule": "v8.66 yolo 加重审核 · 非必要不得去 external(SKILL.md § yolo)",
        }, ensure_ascii=False, indent=2))

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

    # v8.66:yolo 去 external(已 --accept-external-removal 放行)→ concern WARN 留痕(retro 复盘拆安全网)
    if state.get("yolo") and "external" in before and "external" not in roles_list:
        state.setdefault("concerns", []).append(
            f"{now_iso()} WARN yolo 去 external@{args.stage}(无人值守拆唯一跨模型安全网)· "
            f"reason: {args.reason}"
        )

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

EXTERNAL_REVIEW_TIMEOUT_SEC = 600  # v8.55:5min→10min(用户 case codex 偶尔卡 / 长 review · 给足 buffer)
CLAUDE_REVIEW_ARGV_LIMIT = 200  # v8.85:claude argv prompt 超此长度 → 落 doc · argv 只发短引用句(治本长 argv)


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


# v8.43:claude reviewer 需要 inline 文件内容(stateless one-shot · 无文件系统访问)
# stage → 待评审文件清单(与 reviewer.md "你需要读取的文件" 段对齐)
STAGE_REVIEW_FILES = {
    "goal":      ["PRD.md"],
    "blueprint": ["TC.md", "TECH.md"],
    "review":    [],  # review 模式靠 git diff · 不 inline 文件
}

# stage → reviewer target type(reviewer.md {target} 占位符)
STAGE_TO_REVIEW_TARGET = {
    "goal":      "prd",
    "blueprint": "blueprint",
    "review":    "code",
}

# v8.43:防 argv ARG_MAX 超限 · 单文件最大 inline 字节数
EXTERNAL_REVIEW_INLINE_MAX_BYTES_PER_FILE = 60 * 1024  # 60KB


def _gather_review_files_for_claude(stage: str, feature_dir: Path) -> tuple[str, list[dict]]:
    """v8.43:把 stage 待评审文件内容 inline 成单 str(填充 reviewer.md {file_list} 占位符)。

    返 (inline_block, files_meta):
      - inline_block:" ### PRD.md\\n```\\n<content>\\n```\\n\\n### TC.md\\n..."
      - files_meta:[{name, exists, bytes, truncated?}] · 供 emit audit

    设计:
    - 超 60KB 单文件 truncate + emit metadata 告诉 reviewer 截断了
    - 缺失文件 emit 警告但不 BLOCK(reviewer 自己决定如何处理)
    - review stage 不 inline 文件(走 git diff 模式 · 由 codex 路径处理 · claude 路径目前不支持)
    """
    targets = STAGE_REVIEW_FILES.get(stage, [])
    if not targets:
        return ("(本 stage 不 inline 文件 · 由 reviewer 按外部 context 判断)", [])
    blocks: list[str] = []
    meta: list[dict] = []
    for fname in targets:
        fpath = feature_dir / fname
        info: dict = {"name": fname, "exists": fpath.exists()}
        if not fpath.exists():
            blocks.append(f"### {fname}\n_(文件不存在 · reviewer 视情况处理)_\n")
            info["bytes"] = 0
            meta.append(info)
            continue
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            blocks.append(f"### {fname}\n_(读取失败:{e})_\n")
            info["bytes"] = 0
            info["read_error"] = str(e)
            meta.append(info)
            continue
        info["bytes"] = len(content.encode("utf-8"))
        if info["bytes"] > EXTERNAL_REVIEW_INLINE_MAX_BYTES_PER_FILE:
            # 按 byte 截断 + 标记 truncated(reviewer 看到提示自行判断完整性)
            truncated = content.encode("utf-8")[
                :EXTERNAL_REVIEW_INLINE_MAX_BYTES_PER_FILE
            ].decode("utf-8", errors="ignore")
            content = (truncated + f"\n\n... [v8.43 truncated · 原文 {info['bytes']} bytes "
                                    f"超 {EXTERNAL_REVIEW_INLINE_MAX_BYTES_PER_FILE} bytes 阈值] ...")
            info["truncated"] = True
        blocks.append(f"### {fname}\n```\n{content}\n```\n")
        meta.append(info)
    return ("\n".join(blocks), meta)


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
            f"perspective. Review the FULL code changes this feature introduces vs base "
            f"branch `{base}`. Run `git diff {base}...{commit}` (PR-style; fall back to "
            f"`git show {commit}` if the base ref is unavailable) to inspect the complete "
            f"diff across ALL changed files —— 🔴 the implementation lives OUTSIDE "
            f"`{feature_dir_rel}/`(that folder is only Feature docs)· do NOT restrict the "
            f"review to it. "
            f"Focus: correctness, security, performance, edge cases, regressions. "
            f"Profile reference: codex-agents/{profile_filename}. "
            f"Output: YAML frontmatter (perspective/target/files_read/findings) + findings "
            f"body with file:line cite. End with verdict APPROVE or NEEDS_REVISION."
        )
    # 兜底(其他 stage 走 prompt 模式)
    return (
        f"External review for stage={stage} in `{feature_dir_rel}/`. "
        f"Profile reference: codex-agents/{profile_filename}."
    )


def _log_external_run(feature_dir: Optional[Path], label: str, cmd: list,
                      cwd: str, rc, stdout, stderr, dur_sec: float) -> Optional[str]:
    """v8.55:默认把 external review(codex/claude)执行过程写日志 ·
    方便排查"卡住 / 跑不起来"(看到 codex 升级提示 / 鉴权失败 / 网络 / 超时前的部分输出)。

    落 `~/.teamwork/external-review-logs/<feature_name>/<label>-<ts>.log`(出仓 · 不污染 ship ·
    与 host_audit / prepare_check_audit 同处)· 含 cmd/rc/耗时/stdout/stderr。
    写失败或 feature_dir 缺失 → 返 None(绝不阻塞 review)。
    """
    if feature_dir is None:
        return None

    def _s(x):
        if isinstance(x, bytes):
            return x.decode("utf-8", "replace")
        return x if isinstance(x, str) else ("" if x is None else str(x))

    try:
        feat_name = Path(feature_dir).name or "unknown"
        log_dir = Path.home() / ".teamwork" / "external-review-logs" / feat_name
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        log_path = log_dir / f"{label}-{ts}.log"
        cmd_disp = " ".join(
            (a[:800] + "…<truncated>") if isinstance(a, str) and len(a) > 800 else str(a)
            for a in cmd
        )
        body = (
            f"# external-review 执行日志 · {label} · {ts}\n"
            f"returncode: {rc}\n"
            f"duration_sec: {dur_sec:.1f}\n"
            f"timeout_sec: {EXTERNAL_REVIEW_TIMEOUT_SEC}\n"
            f"cwd: {cwd}\n"
            f"cmd: {cmd_disp}\n\n"
            f"===== STDOUT =====\n{_s(stdout)}\n\n"
            f"===== STDERR =====\n{_s(stderr)}\n"
        )
        log_path.write_text(body, encoding="utf-8")
        return str(log_path)
    except OSError:
        return None


def _run_codex_review(stage: str, commit: str, base: str, title: str,
                      profile_filename: str, feature_dir: Path, cwd: str,
                      codex_model: Optional[str] = None) -> tuple[int, str, str]:
    """跑 codex CLI 评审 · 返 (returncode, stdout, stderr)。

    v8.59(用户 case · 本地实测):**全 stage 统一 `codex exec [PROMPT]`**。
    治本 review stage `codex review` 子命令 headless 卡死 —— 本地实测
    `codex review --commit X --title Y`(stdin=DEVNULL)跑满 220s 产 **0 字节 stdout**
    (超时 · exit 124)· 与用户 AON SVC-PLATFORM-F057 现象一致(goal/blueprint 走 exec
    早成功 · 唯独 review 走 codex review 持续超时)。codex exec 是稳定 headless 路径
    (goal/blueprint 已验证)· review 对象差异(代码 diff vs 文档)全由
    `_build_codex_prompt` 内置 prompt 描述。
    (codex review↔exec 反复横跳演进史见 docs/CHANGELOG-ARCHIVE.md · v8.23-26)
    """
    # 算 feature_dir 相对 cwd · 让 prompt 用相对路径(codex 在 cwd=git root 跑)
    try:
        feature_dir_rel = str(feature_dir.relative_to(Path(cwd)))
    except ValueError:
        feature_dir_rel = str(feature_dir)

    # v8.29:codex_model 非空才传 --config model=...(治本 ChatGPT 订阅 case · 默认模型限制)
    model_args = ["--config", f"model={codex_model}"] if codex_model else []

    # v8.59:统一 codex exec [PROMPT] —— review 对象差异由 _build_codex_prompt 描述
    # (删 stage==review 的 codex review 子命令分支 · 它 headless 卡死)
    body_prompt = _build_codex_prompt(
        stage, feature_dir_rel, commit, base, profile_filename)
    # title 信息嵌进 PROMPT 顶部(codex exec 没 --title flag)
    prompt = f"[Review title: {title}]\n\n{body_prompt}"
    cmd = ["codex", "exec", *model_args, prompt]

    t0 = datetime.now(timezone.utc)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=EXTERNAL_REVIEW_TIMEOUT_SEC, cwd=cwd,
                           stdin=subprocess.DEVNULL)  # v8.55:闭 stdin · 防 codex 交互/升级提示等输入卡住
        dur = (datetime.now(timezone.utc) - t0).total_seconds()
        _log_external_run(feature_dir, f"codex-{stage}", cmd, cwd,
                          r.returncode, r.stdout, r.stderr, dur)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as e:
        dur = (datetime.now(timezone.utc) - t0).total_seconds()
        log_path = _log_external_run(feature_dir, f"codex-{stage}", cmd, cwd,
                                     "TIMEOUT", e.stdout, e.stderr, dur)
        tail = f" · 见日志 {log_path}(看是否 codex 升级提示/鉴权/网络卡住)" if log_path else ""
        return 124, "", f"codex 超时({EXTERNAL_REVIEW_TIMEOUT_SEC}s){tail}"
    except (FileNotFoundError, OSError) as e:
        dur = (datetime.now(timezone.utc) - t0).total_seconds()
        log_path = _log_external_run(feature_dir, f"codex-{stage}", cmd, cwd,
                                     "ERROR", "", str(e), dur)
        tail = f" · 见日志 {log_path}" if log_path else ""
        return 127, "", f"codex CLI 不可用:{e}{tail}"


def _build_claude_review_cmd(prompt_text: str, feature_dir: Optional[Path],
                             prompt_doc: Optional[Path]
                             ) -> tuple[list, Optional[str]]:
    """v8.85:按 prompt 长度选 inline / doc 模式 · 返 (cmd, cwd)。

    - 短(≤200 字符):argv inline · `claude -p <prompt> --bare --output-format text`(纯文本 · 无工具 · 快)。
    - 长(>200):prompt 落 doc · argv 只发 ≤200 字符短句「先写 review_start.log · 再读 <doc> 做 review」·
      `--bare`(🔴 跳宿主项目 MCP/hooks/CLAUDE.md/skills 自动发现 · 治本:带工具的 headless claude 会
      spawn 消费项目 `.mcp.json` 里的长跑 dev-server MCP → 卡死至 timeout)· `--permission-mode dontAsk`
      (非白名单工具自动拒 · 不 abort 不挂)· `--allowedTools Read Grep Glob Write`(读+导航 + 写 liveness ·
      不放 Bash/Edit · 守只读评审)· cwd=feature_dir(review_start.log + doc 相对路径都落 feature 目录)。
    🔴 external review 必须 **hermetic** —— 不加载消费项目的 MCP/hooks/CLAUDE.md(防卡死 + 防上下文污染)。
    单测可直接调本函数断言 cmd(不真跑 CLI)。
    """
    use_doc = (prompt_doc is not None and feature_dir is not None
               and len(prompt_text) > CLAUDE_REVIEW_ARGV_LIMIT)
    if use_doc:
        try:
            prompt_doc.parent.mkdir(parents=True, exist_ok=True)
            if not prompt_doc.exists():
                # fallback inline 模式也物化 doc(可审计 + 可复跑)
                prompt_doc.write_text(prompt_text, encoding="utf-8")
            rel = prompt_doc.resolve().relative_to(Path(feature_dir).resolve()).as_posix()
        except (OSError, ValueError):
            use_doc = False
    if use_doc:
        # ≤200 字符短 argv(rel 短 · 总长受控):liveness 日志 + 读 doc
        short = (f"First write review_start.log (UTC timestamp) in cwd (liveness), "
                 f"then read {rel} and follow it; output only the review, no other writes.")
        # v8.103:--bare 跳宿主项目 MCP/hooks/CLAUDE.md 自动发现(治本消费项目 .mcp.json 长跑
        #   dev-server MCP 卡死 headless claude)· dontAsk 非白名单工具自动拒(不挂)·
        #   白名单 Read/Grep/Glob(读+导航)+ Write(仅 liveness)· 不放 Bash/Edit。
        cmd = ["claude", "-p", short, "--bare",
               "--permission-mode", "dontAsk",
               "--allowedTools", "Read", "Grep", "Glob", "Write",
               "--output-format", "text"]
        return cmd, str(feature_dir)
    # inline 短 prompt 也加 --bare(hermetic · 不让消费项目 CLAUDE.md/MCP 污染或拖慢)
    return ["claude", "-p", prompt_text, "--bare", "--output-format", "text"], None


def _run_claude_review(prompt_text: str,
                       feature_dir: Optional[Path] = None, stage: str = "review",
                       prompt_doc: Optional[Path] = None) -> tuple[int, str, str]:
    """跑 claude review · 返 (rc, stdout, stderr)。

    v8.38(用户拍板 2026-05-27):用 `-p`(short)替代 `--print`(long)。
    v8.43(case SVC-PLATFORM-F054 blueprint round 3):prompt 从 stdin 改 argv ·
    治本 Claude CLI 2.1.153 在 stdin 模式触发 "Not logged in · Please run /login" bug。
    v8.84(用户拍板):**不再 --model 指定模型 · 用 claude CLI 默认值**。
    v8.85(用户拍板):**短 prompt 走 argv inline;长 prompt(>200)落 doc · argv 只发
    短引用句 + 让 reviewer 先写 review_start.log 时间戳证明在工作**(详 _build_claude_review_cmd)·
    治本长 argv 卡 / 把模板当问题 / 调用方无法判断模型是否卡死。
    """
    cmd, cwd = _build_claude_review_cmd(prompt_text, feature_dir, prompt_doc)
    label = f"claude-{stage}"
    t0 = datetime.now(timezone.utc)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=EXTERNAL_REVIEW_TIMEOUT_SEC,
                           stdin=subprocess.DEVNULL, cwd=cwd)  # v8.55:闭 stdin · 防交互卡住
        dur = (datetime.now(timezone.utc) - t0).total_seconds()
        _log_external_run(feature_dir, label, cmd, cwd or "(inherit)",
                          r.returncode, r.stdout, r.stderr, dur)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as e:
        dur = (datetime.now(timezone.utc) - t0).total_seconds()
        log_path = _log_external_run(feature_dir, label, cmd, cwd or "(inherit)",
                                     "TIMEOUT", e.stdout, e.stderr, dur)
        tail = f" · 见日志 {log_path}" if log_path else ""
        return 124, "", f"claude -p 超时({EXTERNAL_REVIEW_TIMEOUT_SEC}s){tail}"
    except OSError as e:
        if getattr(e, "errno", None) == 7:  # E2BIG · argument list too long
            return 127, "", (
                f"claude -p prompt 过长(ARG_MAX 超限 · prompt_bytes={len(prompt_text)})· "
                f"应已落 doc 模式 · 检查 prompt_doc 是否可写"
            )
        return 127, "", f"claude CLI 不可用:{e}"
    except FileNotFoundError as e:
        return 127, "", f"claude CLI 不可用:{e}"


# ─── v8.44:scaffold-review-prompt(doc-based external review · 治本 case round 4)─
# 用户拍板:把 prompt 写到 doc · AI 主对话填 compact summary · state.py 读 doc 作 prompt
# 解决 v8.43 inline 全 PRD/TC/TECH 卡 claude -p 长 prompt 问题


def _default_prompt_doc_path(feature_dir: Path, stage: str, model: str) -> Path:
    """v8.44:prompt-doc 默认路径 `<feature_dir>/external-review-prompts/<stage>-<model>.md`。"""
    return feature_dir / "external-review-prompts" / f"{stage}-{model}.md"


SCAFFOLD_PROMPT_DOC_TEMPLATE = """# {model_cap} {stage_cap} External Review Prompt

> v8.44 scaffold(治本 case round 4 长 prompt 卡):
> AI 主对话填 PRD/TC/TECH 关键摘要到 "Summary" 段(不复制全文 · 提炼契约+边界+known facts)
> state.py external-review 检测此 doc → 优先用它作 prompt(不再 inline 全文)
> 文档可审计 / 可编辑 / 可复跑

You are Teamwork `external-{model}` reviewer.

## Strict Constraints

- READ-ONLY reviewer.
- Do not write files.
- Do not execute commands.
- Do not ask follow-up questions.
- Review only the {stage} summarized in this document.
- Output only legal YAML frontmatter plus Markdown body.

## Target

- Feature: `{feature_id}`
- Target: `{target}`
- Stage: `{stage}`
- Reviewer perspective: `external-{model}`

## Output Schema

```yaml
---
perspective: external-{model}
target: {target}
generated_at: "<ISO 8601 UTC>"
model: "<actual model version>"
findings:
  - id: CR-1
    checklist: C1
    severity: blocker | high | low | info
    location: "<artifact and section>"
    issue: "<1-2 sentence issue>"
    rationale: "<1-2 sentence evidence/risk>"
    suggestion: "<actionable fix>"
findings_summary:
  blocker: 0
  high: 0
  low: 0
  info: 0
  total: 0
---
```

If there are no findings, output `findings: []` and `findings_summary.total: 0`.

## Review Checklist

{checklist_block}

## TODO · AI 主对话填以下 Summary 段(compact · 不复制全文)

### {primary_artifact} Summary

<!-- AI 填:关键契约 / 边界 / 信号 / known facts(代码现状 vs spec 声明) -->
<!-- 不复制全文 · 提炼到 reviewer 可独立判断的最小集 -->

### Required Judgment

<!-- AI 填:reviewer 应特别关注的盲区 · 让 reviewer 不浪费 token 在低优先级 -->
"""

STAGE_TO_REVIEW_CHECKLIST = {
    "goal": (
        "- C1 PRD scope clarity / acceptance criteria atomicity.\n"
        "- C2 Edge cases / boundary completeness.\n"
        "- C3 Existing contract / cross-module impact.\n"
        "- C4 Stakeholder communication clarity (UI/ADMIN/SVC/DBA roles)."
    ),
    "blueprint": (
        "- C1 TC to AC mapping completeness.\n"
        "- C2 TC executability (function names / file paths actually exist).\n"
        "- C3 Boundary and failure coverage.\n"
        "- C4 TECH architecture consistency.\n"
        "- C5 TECH feasibility and risk.\n"
        "- C6 TC to TECH alignment."
    ),
    "review": (
        "- C1 Code correctness / logic bugs.\n"
        "- C2 Security / injection / boundary checks.\n"
        "- C3 Performance / N+1 / scaling.\n"
        "- C4 Edge cases / error handling.\n"
        "- C5 Test coverage gaps."
    ),
}


def cmd_set_mode(args: argparse.Namespace) -> None:
    """v8.69:语义化设 auto_mode / yolo(替代 raw-write · 物化 + audit)。

    治本 case(SVC-PLATFORM-F060 · Codex agent 提):改 auto_mode 只能 raw-write ·
    audit 里出现 raw-write 不理想。本命令把开关 + yolo 非主分支 gate + audit 收进脚本。

    flag:
      --auto-mode / --no-auto-mode    开/关 auto_mode(互斥)
      --yolo [<branch>] / --no-yolo    开/关 yolo(互斥)· yolo implies auto_mode ·
                                       <branch> = 专属 merge_target(覆盖 · 非主分支 gate)
      --reason 必填(audit)
    """
    state = load_state(args.feature)
    state_file = state_path(args.feature)

    if args.auto_mode and args.no_auto_mode:
        die(2, json.dumps({"verdict": "FAIL", "command": "set-mode",
                           "error": "--auto-mode 与 --no-auto-mode 互斥"},
                          ensure_ascii=False, indent=2))
    if args.yolo is not None and args.no_yolo:
        die(2, json.dumps({"verdict": "FAIL", "command": "set-mode",
                           "error": "--yolo 与 --no-yolo 互斥"},
                          ensure_ascii=False, indent=2))
    if not (args.auto_mode or args.no_auto_mode
            or args.yolo is not None or args.no_yolo):
        die(2, json.dumps({
            "verdict": "FAIL", "command": "set-mode",
            "error": "未指定任何变更",
            "hint": "至少一个:--auto-mode / --no-auto-mode / --yolo [<branch>] / --no-yolo",
        }, ensure_ascii=False, indent=2))

    before = {"auto_mode": bool(state.get("auto_mode")),
              "yolo": bool(state.get("yolo")),
              "merge_target": state.get("merge_target")}
    new_auto, new_yolo, new_mt = (before["auto_mode"], before["yolo"],
                                  before["merge_target"])

    # yolo
    yolo_branch = (args.yolo if isinstance(args.yolo, str) and args.yolo.strip()
                   else None)
    if args.yolo is not None:  # 开 yolo
        new_yolo = True
        new_auto = True  # yolo implies auto_mode
        if yolo_branch:
            new_mt = yolo_branch
        if _is_main_branch(new_mt):
            die(2, json.dumps({
                "verdict": "FAIL", "command": "set-mode",
                "error": f"yolo merge_target 必须非主分支(当前 {new_mt!r})—— "
                         f"yolo 无人 review 自动 merge · 不得直接进 main/master/默认分支",
                "hint": "用 --yolo <非主分支>(如 dev/staging)· 或先改 merge_target",
                "rule": "v8.63/69 yolo 硬约束 · 自动 merge 不进 main",
            }, ensure_ascii=False, indent=2))
    elif args.no_yolo:
        new_yolo = False

    # auto_mode(yolo=True 强制 auto=True)
    if args.auto_mode:
        new_auto = True
    if args.no_auto_mode:
        if new_yolo:
            die(2, json.dumps({
                "verdict": "FAIL", "command": "set-mode",
                "error": "yolo 开启时不能关 auto_mode(yolo implies auto_mode)",
                "hint": "先 --no-yolo · 再 --no-auto-mode",
            }, ensure_ascii=False, indent=2))
        new_auto = False

    after = {"auto_mode": new_auto, "yolo": new_yolo, "merge_target": new_mt}
    if after == before:
        emit({"verdict": "NOOP", "command": "set-mode",
              "current": before, "hint": "新值 == 现值 · 不写不 audit"})
        return

    state["auto_mode"] = new_auto
    state["yolo"] = new_yolo
    if new_mt != before["merge_target"]:
        state["merge_target"] = new_mt
        state.setdefault("worktree", {})["base_branch"] = f"origin/{new_mt}"
        ec = state.setdefault("environment_config", {})
        ec["merge_target"] = new_mt
        ec["base"] = f"origin/{new_mt}"

    state.setdefault("mode_changes", []).append({
        "at": now_iso(), "before": before, "after": after,
        "reason": args.reason, "via": "set-mode",
    })
    # yolo 开启 = 高风险 · 额外 concern WARN(audit 显著)
    if new_yolo and not before["yolo"]:
        state.setdefault("concerns", []).append(
            f"{now_iso()} WARN yolo 开启 via set-mode · merge_target={new_mt} · "
            f"reason: {args.reason}")

    atomic_write(state_file, state)
    emit({
        "verdict": "OK", "command": "set-mode",
        "before": before, "after": after, "reason": args.reason,
        "next_action_hint": (
            "yolo 开启 · 严格按流程 · 不得简化/内化(详 SKILL.md § yolo)"
            if new_yolo and not before["yolo"]
            else "auto_mode/yolo 已更新 · audit 写入 state.mode_changes"),
    })


def cmd_scaffold_review_prompt(args: argparse.Namespace) -> None:
    """v8.44:生成 prompt-doc skeleton 到 feature_dir/external-review-prompts/<stage>-<model>.md。

    AI 主对话跑此命令拿到 skeleton · 填 PRD/TC/TECH compact summary · 再跑 external-review。

    幂等:doc 已存在 → 不覆盖(防覆盖用户编辑)· emit hint。--force 强制覆盖。
    """
    feature_dir = Path(args.feature).resolve()
    if not feature_dir.exists():
        emit({
            "verdict": "FAIL",
            "command": "scaffold-review-prompt",
            "error": f"feature 路径不存在:{feature_dir}",
        })
        return

    stage = args.stage
    model = args.model
    doc_path = _default_prompt_doc_path(feature_dir, stage, model)

    if doc_path.exists() and not getattr(args, "force", False):
        emit({
            "verdict": "FAIL",
            "command": "scaffold-review-prompt",
            "error": f"prompt-doc 已存在 · 拒绝覆盖防丢失编辑:{doc_path}",
            "hint": ("二选一:\n"
                     f"  ① 直接编辑现有 doc:{doc_path}\n"
                     f"  ② 加 --force 覆盖重生(本地编辑丢失 · 慎用)"),
        })
        return

    # 推 feature_id 从路径(basename 即 ID-Name)
    feature_id = feature_dir.name
    target = STAGE_TO_REVIEW_TARGET.get(stage, stage)
    checklist_block = STAGE_TO_REVIEW_CHECKLIST.get(stage, "- C1 ...\n- C2 ...")
    primary_artifact = {
        "goal": "PRD",
        "blueprint": "TC + TECH",
        "review": "Code Diff",
    }.get(stage, stage.title())

    body = SCAFFOLD_PROMPT_DOC_TEMPLATE.format(
        model_cap=model.title(),
        stage_cap=stage.title(),
        model=model,
        stage=stage,
        feature_id=feature_id,
        target=target,
        checklist_block=checklist_block,
        primary_artifact=primary_artifact,
    )

    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(body, encoding="utf-8")

    emit({
        "verdict": "OK",
        "command": "scaffold-review-prompt",
        "feature_id": feature_id,
        "stage": stage,
        "model": model,
        "prompt_doc": str(doc_path),
        "bytes_written": len(body.encode("utf-8")),
        "next_hint": (
            f"✅ Skeleton 已写 · 接下来:\n"
            f"  ① AI 主对话读 PRD/TC/TECH · 填 doc 内 'TODO · 填以下 Summary 段' "
            f"(compact summary · 提炼契约+边界+known facts · 不复制全文)\n"
            f"  ② 跑 state.py external-review --feature <path> --stage {stage} "
            f"(--model {model})· state.py 自动读取此 doc 作 prompt"
        ),
    })


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

    # v8.88:诚实降级自审兜底 —— 异质模型客观不可用(未装/未登录/配额满·已重试失败)时 ·
    # 跑**同模型 fresh exec** 自审(非异质 · 只隔离对话历史不隔离权重 · 同盲点)· 作弱安全网。
    # 🔴 落 self-review/(不进 external-cross-review/)· **不满足 P0-154 异质门禁** ·
    # 仍需修环境重跑真异质 或 change-review-roles 显式移除 external(本产物作降级 evidence)。
    self_fallback = getattr(args, "self_review_fallback", False)
    sr_reason = (getattr(args, "reason", "") or "").strip()
    # v8.90:localconfig 禁用异质评审(单模型用户)→ 自动用宿主自身模型 exec 自审(降级 · 满足门禁)
    het_disabled = _read_disable_heterogeneous_review(args.feature)
    degraded_self = False  # True → config-disabled 降级自审(落 external-cross-review/ · 满足 P0-154)
    if self_fallback:
        # v8.88 临时 stopgap:异质暂不可用 · 落 self-review/ · **不满足 P0-154**(异质仍是目标)
        if not sr_reason:
            emit({
                "verdict": "FAIL",
                "command": "external-review",
                "error": "--self-review-fallback 必带 --reason(异质为何不可用 + 已重试证据)",
                "hint": "示例 --reason '异质 claude 未登录·已 retry 失败·降级同模型自审兜底'",
            })
            return
        model = host.split("-")[0]  # claude-code→claude · codex-cli→codex(故意同源 · 降级)
        if model not in ("codex", "claude"):
            emit({
                "verdict": "FAIL",
                "command": "external-review",
                "error": f"--self-review-fallback 暂仅支持 claude/codex 宿主自审(host={host})",
                "hint": "gemini 等宿主无 self-review runner · 改 change-review-roles 移除 external",
            })
            return
    elif het_disabled:
        # v8.90 项目级长期策略:用户禁异质(单模型)→ 自动宿主自身模型 exec 自审 ·
        # 落 external-cross-review/(满足 P0-154 · 让单模型用户能走完流程)· frontmatter 标 degraded ·
        # 每次 bootstrap 启动 WARN 持续提醒「交叉 review 质量下降 · 建议恢复异质」。
        model = host.split("-")[0]  # 宿主自身模型(故意同源)
        if model not in ("codex", "claude"):
            emit({
                "verdict": "FAIL",
                "command": "external-review",
                "error": f"disable_heterogeneous_review=true 但宿主 {host} 无 self-exec runner(仅 claude/codex)",
                "hint": ("改回异质(删 localconfig disable_heterogeneous_review)· "
                         "或 change-review-roles 移除 external"),
            })
            return
        degraded_self = True
        sr_reason = (sr_reason or "localconfig disable_heterogeneous_review=true"
                     "(单模型 · 异质评审降级为同模型 exec 自审 · 已 startup WARN)")
    elif args.model:
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
                    f"推荐 --model {EXTERNAL_HOST_TO_MODEL[host]}(自动映射 · 留空即默认)· "
                    f"或异质客观不可用时 --self-review-fallback --reason '...' 降级自审(不满足门禁)"
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
    # v8.88:self-review 降级落 self-review/(不进 external-cross-review/ · 不满足 P0-154 门禁)
    output_dir = feature_dir / ("self-review" if self_fallback else "external-cross-review")
    output_file = output_dir / f"{args.stage}-{model}.md"
    preview_prompt_full = None
    if args.dry_run:
        if model == "codex":
            # v8.59:全 stage 统一 codex exec [PROMPT](删 review→codex review 分支 · 它 headless 卡死)
            # v8.29:codex_model 非空才显 --config(治本 ChatGPT 订阅死锁)
            try:
                fd_rel = str(feature_dir.relative_to(git_root))
            except ValueError:
                fd_rel = str(feature_dir)
            model_part = f"--config 'model={codex_model}' " if codex_model else ""
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
                # v8.38 -p · v8.84 不 --model · v8.85 doc 模式 · v8.103 --bare(跳宿主 MCP/hooks/CLAUDE.md
                # · 治本消费项目长跑 dev-server MCP 卡死)+ --permission-mode dontAsk + 白名单 Read/Grep/Glob/Write
                "cd <feature_dir> && claude -p "
                "'First write review_start.log (UTC timestamp) in cwd (liveness), then read "
                f"external-review-prompts/{args.stage}-{model}.md and follow it; output only the review' "
                "--bare --permission-mode dontAsk --allowedTools Read Grep Glob Write --output-format text"
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
        # claude 路径:v8.44 doc-based default(治本 case round 4 长 prompt 卡 claude -p)
        # 优先:读 feature_dir/external-review-prompts/<stage>-<model>.md · 作 claude argv prompt
        #   - AI 主对话填 compact summary(提炼契约 · 不复制全文)
        #   - prompt 可审计 / 可编辑 / 可复跑 · 短不卡
        # Fallback:doc 不存在 → v8.43 inline 全文模式 + emit WARN 提示 scaffold
        prompt_doc_override = getattr(args, "prompt_doc", None)
        if prompt_doc_override:
            prompt_doc = Path(prompt_doc_override).expanduser().resolve()
            prompt_doc_source = "args"
        else:
            prompt_doc = _default_prompt_doc_path(feature_dir, args.stage, model)
            prompt_doc_source = "default"

        files_inline_meta: list[dict] = []
        fallback_warning = None
        if prompt_doc.exists():
            try:
                prompt_text = prompt_doc.read_text(encoding="utf-8")
                prompt_doc_used = str(prompt_doc)
            except OSError as e:
                emit({
                    "verdict": "FAIL",
                    "command": "external-review",
                    "error": f"读 prompt-doc 失败:{prompt_doc}: {e}",
                })
                return
        else:
            # v8.44 fallback:v8.43 inline 模式 + WARN 提示 scaffold
            prompt_template = profile_path.read_text(encoding="utf-8")
            file_list_block, files_inline_meta = _gather_review_files_for_claude(
                args.stage, feature_dir
            )
            prompt_text = (
                prompt_template
                .replace("{stage}", args.stage)
                .replace("{target}", STAGE_TO_REVIEW_TARGET.get(args.stage, args.stage))
                .replace("{feature_name}", feature_id)
                .replace("{file_list}", file_list_block)
                .replace("{{stage}}", args.stage)
                .replace("{{commit}}", commit)
                .replace("{{base}}", base)
                .replace("{{feature_id}}", feature_id)
            )
            prompt_doc_used = None
            fallback_warning = (
                f"⚠️ prompt-doc 不存在({prompt_doc})· 走 v8.43 inline 模式 fallback。"
                f" 推荐:跑 state.py scaffold-review-prompt --feature {feature_dir} "
                f"--stage {args.stage} --model {model} 生成 skeleton · "
                f"AI 主对话填 compact summary 后重跑 external-review("
                f"治本长 prompt 卡 + 不可审计 · v8.44 推荐路径)"
            )
        rc, stdout, stderr = _run_claude_review(
            prompt_text, feature_dir=feature_dir, stage=args.stage,
            prompt_doc=prompt_doc)

    # v8.85:claude doc 模式 reviewer 会先写 review_start.log(时间戳)证明在工作 ·
    # 读取作 liveness 留痕 + 清理(不污染 feature 目录)· codex 路径无此文件(read-only sandbox)
    liveness_at = None
    _rsl = feature_dir / "review_start.log"
    if _rsl.exists():
        try:
            liveness_at = (_rsl.read_text(encoding="utf-8").strip()[:80] or "present")
        except OSError:
            liveness_at = "present"
        try:
            _rsl.unlink()
        except OSError:
            pass

    if rc != 0:
        # v8.85:liveness 区分「模型从未响应」vs「启动了但没跑完(慢/限流)」
        if liveness_at:
            live_hint = (f"reviewer 已写 review_start.log({liveness_at})· 即模型**已启动但未跑完** · "
                         f"多半是慢 / 限流 · 直接重跑(并发跑多个 claude 会限流 · 串行重试)· "
                         f"🔴 切勿伪造 tool_error 文件或自列 external 通过门禁")
        else:
            live_hint = (f"无 review_start.log · 模型**可能从未响应** · 查 ① 网络 / token"
                         f"(setup-token / OAuth)· ② {cli_name} --version · ③ 是否并发限流 · 再重跑")
        emit({
            "verdict": "FAIL",
            "command": "external-review",
            "error": f"{cli_name} 执行失败(exit={rc}): {stderr[:300]}",
            "hint": live_hint,
            "host": host,
            "model": model,
            "cli_exit_code": rc,
            "cli_stderr": stderr[:500],
            **({"liveness_confirmed_at": liveness_at} if liveness_at else {}),
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
        f"review_role: {'self-degraded' if (self_fallback or degraded_self) else 'external'}",
        f"review_stage: {args.stage}",
        f"target_commit: {commit}",
        f"target_base: {base}",
        f"title: \"{title}\"",
        f"generated_at: \"{now_iso()}\"",
        f"invoked_by: state.py external-review (v8.20)",
        f"host: {host}",
    ]
    if self_fallback or degraded_self:
        # v8.88/v8.90:诚实标注 —— 同模型自审 · 非异质 · 同盲点
        frontmatter_lines += [
            "heterogeneous: false",
            "degraded: true",
            f"degraded_mode: {'self-review-fallback' if self_fallback else 'config-disabled'}",
            f"degraded_reason: \"{sr_reason}\"",
        ]
    frontmatter_lines += ["---", ""]
    body = stdout
    if self_fallback:
        # 正文顶 banner · 任何人打开都立刻知道这是降级自审(非异质 · 不可当 external 通过证据)
        body = (
            "> ⚠️ **同模型自审(self-review · 降级)· 非异质 external** —— 只隔离对话历史不隔离"
            "模型权重 · 同盲点 · **不满足 P0-154 异质门禁** · 仅作异质不可用时的弱安全网。\n"
            f"> 降级理由:{sr_reason}\n\n"
        ) + stdout
    elif degraded_self:
        # v8.90 config-disabled:本项目禁异质 · 此自审是「该项目的 review of record」(满足门禁)·
        # 但仍非异质 · 同盲点 · 交叉 review 质量下降 —— banner + startup WARN 持续提醒。
        body = (
            "> ⚠️ **同模型自审(config 禁用异质 · 降级)** —— `disable_heterogeneous_review=true` ·"
            "只隔离对话历史不隔离模型权重 · 同盲点 · 交叉 review 质量下降。删 localconfig 该项可恢复异质。\n"
            f"> 降级理由:{sr_reason}\n\n"
        ) + stdout
    output_file.write_text("\n".join(frontmatter_lines) + body, encoding="utf-8")

    # ── Step 6.5 · v8.36 内容质量轻校验 → v8.43 升级 template_echo 为 BLOCK ──
    # v8.36 决策 WARN 不 BLOCK · 但 case SVC-PLATFORM-F054 blueprint round 3 实证:
    # AI 看到产物存在就继续 · WARN 走过场 · 用户手动读 file 才发现无效
    # v8.43 治本(用户拍板 A 全治):template_echo BLOCK(强信号 100% 无效)·
    # empty_content 仍 WARN(可能合理精简)· 逃生口 --accept-quality-warnings
    quality_warnings = _check_external_review_quality(stdout, args.stage, model)

    template_echo_hit = [w for w in quality_warnings if w.get("type") == "template_echo"]
    if template_echo_hit and not getattr(args, "accept_quality_warnings", False):
        # 写入 file(保留产物供审查)· 但 BLOCK 不让流程继续
        # 文件已经在 Step 6 写了 · 这里只 emit FAIL with hint
        emit({
            "verdict": "FAIL",
            "command": "external-review",
            "error": (
                f"reviewer 产物含 template echo 特征 · 视作无效评审(v8.43 BLOCK · "
                f"治本 SVC-PLATFORM-F054 blueprint round 3 case)"
            ),
            "file_path": str(output_file),
            "quality_warnings": quality_warnings,
            "matched_signatures": template_echo_hit[0].get("matched_signatures", []),
            "hint": (
                "二选一:\n"
                "  ① [推荐] 检查 prompt 与 reviewer 真实输出 · 修 prompt 或重跑 external-review:\n"
                "       state.py external-review --feature <path> --stage <stage>(必要时换 --model)\n"
                "  ② [慎用] 评估认为评审实质 OK(误报)· 加 --accept-quality-warnings 通过:\n"
                "       state.py external-review --feature <path> --stage <stage> --accept-quality-warnings\n"
                "       (走 bypass log + concerns WARN 留痕 · retro 复盘可见)"
            ),
            "spec": ("v8.43 治本 · template_echo 100% 是无效评审 · 不再 WARN 走过场。"
                     " v8.36 留 WARN 兜底被 AI 钻空子 · v8.43 升级 BLOCK"),
        })
        return

    # ── Step 7 · emit ──
    # finding 数粗估(grep "^###" 或 "Finding" · 仅参考)
    finding_count = max(
        stdout.count("### Finding"),
        stdout.count("#### Finding"),
        stdout.lower().count("finding "),
    )
    # v8.43:若走 bypass(--accept-quality-warnings 通过 template_echo)· emit 标记 + audit
    bypass_warning = None
    if template_echo_hit and getattr(args, "accept_quality_warnings", False):
        bypass_warning = (
            f"{now_iso()} WARN external-review quality bypass: "
            f"stage={args.stage} model={model} template_echo signatures="
            f"{template_echo_hit[0].get('matched_signatures', [])[:3]} · "
            f"--accept-quality-warnings 通过(v8.43 治本 case · 用户认知误报)· "
            f"file={output_file}"
        )

    # v8.88/v8.90:self-review 降级 → 写 concern WARN(audit · retro 可见 · 降级必留痕)
    if self_fallback or degraded_self:
        try:
            _mode = "self-review-fallback·不满足 P0-154" if self_fallback else \
                    "config-disabled·满足门禁但同盲点"
            state.setdefault("concerns", []).append(
                f"{now_iso()} WARN self-review 降级@{args.stage}(同模型 {model} 自审 · "
                f"非异质 · {_mode})· reason: {sr_reason} · file={output_file}"
            )
            atomic_write(state_path(args.feature), state)
        except Exception:
            pass

    if self_fallback:
        next_hint = (
            f"⚠️ 降级自审已落 {output_file}(self-review/ · **非异质 · 不满足 P0-154 门禁**)。"
            f"两条路继续:① [首选] 修环境(装/登录/等配额)→ 重跑真异质 external-review;"
            f"② 异质确实修不了 → state.py change-review-roles --feature {args.feature} "
            f"--stage {args.stage} --roles '<不含 external>' --reason '异质不可用·已自审降级' "
            f"(本自审产物作 audit evidence)· yolo 下还需 --accept-external-removal。"
            f"🔴 不得把本 self-review 当 external 通过证据。"
        )
    elif degraded_self:
        next_hint = (
            f"⚠️ 异质评审已被 localconfig 禁用(disable_heterogeneous_review=true)· 已用同模型 "
            f"{model} exec 自审落 {output_file}(满足 P0-154 · 但**非异质 · 同盲点 · 交叉 review 质量下降**)。"
            f"PMO 整合 finding 到 REVIEW.md → {args.stage}-complete。"
            f"🔴 想恢复异质评审质量:删 .teamwork_localconfig.json 的 disable_heterogeneous_review。"
        )
    else:
        next_hint = (f"file 已落盘 · PMO 整合 finding 到 REVIEW.md · "
                     f"然后跑 state.py {args.stage}-complete --artifacts ...")

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
        # v8.88/v8.90:self-review 降级标记(诚实 · 调用方/审计一眼可辨 · 不冒充异质)
        # self-review-fallback(临时):不满足 P0-154 · config-disabled(项目策略):满足门禁但同盲点
        **({"degraded": True, "heterogeneous": False, "review_role": "self-degraded",
            "degraded_mode": ("self-review-fallback" if self_fallback else "config-disabled"),
            "satisfies_p0_154": (False if self_fallback else True)}
            if (self_fallback or degraded_self) else {}),
        "next_hint": next_hint,
        # v8.36:host 来源 deprecated 警告 + 内容质量轻校验 WARN(不 BLOCK · R0 兜底)
        **({"deprecation_warning": deprecation_warning} if deprecation_warning else {}),
        **({"quality_warnings": quality_warnings} if quality_warnings else {}),
        # v8.43:claude 路径 inline 文件 meta(PMO 可验 reviewer 真拿到内容 · v8.44 fallback 时仍出)
        **({"files_inlined": files_inline_meta}
            if model == "claude" and files_inline_meta else {}),
        # v8.43:bypass quality_warnings(template_echo)留痕
        **({"quality_bypass_warning": bypass_warning} if bypass_warning else {}),
        # v8.44:doc-based prompt 路径(治本 case round 4 长 prompt 卡)
        **({"prompt_doc": prompt_doc_used,
            "prompt_doc_source": prompt_doc_source}
            if model == "claude" and prompt_doc_used else {}),
        **({"prompt_doc_fallback_warning": fallback_warning}
            if model == "claude" and fallback_warning else {}),
        # v8.85:claude doc 模式 reviewer 写的 review_start.log 时间戳(liveness 留痕)
        **({"liveness_confirmed_at": liveness_at} if liveness_at else {}),
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


# ─── v8.24-v8.41 · update-skill → v8.42 已抽到独立 tools/update.py ────────
# 历史:v8.24 加 cmd_update_skill in state.py(git pull) · v8.41 重写 tarball download
# v8.42(用户拍板 2026-05-27 · "更新文件本身是否有必要单独一个 python"):
# - 抽到独立 tools/update.py(职责分离 · 与 bootstrap.py pattern 对齐)
# - 治本"元工具混运行时"+ chicken-and-egg(state.py 坏掉 · update.py 仍能救命)
# - 用法:python3 SKILL_ROOT/tools/update.py [--channel <branch>] [--accept-overwrite]


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
    ifp.add_argument("--merge-target", required=False,
                     help="如 staging / dev · yolo 可改用 --yolo <branch> 指定(二选一)")
    ifp.add_argument("--branch", required=True, help="如 feat/admin-f013-x")
    ifp.add_argument("--worktree-mode", choices=["auto", "manual", "off"],
                     default="off")
    ifp.add_argument("--worktree-path",
                     help="worktree 绝对路径 · worktree-mode != off 时建议提供")
    ifp.add_argument("--auto-mode", action="store_true", help="启用 AUTO_MODE")
    ifp.add_argument("--yolo", nargs="?", const=True, default=None, metavar="BRANCH",
                     help="[v8.63/65] 完全自动(YOLO)· implies --auto-mode + 自动 approve "
                          "pm_acceptance + 自动 merge MR(gh/glab)+ 自动 ship-finalize · 零 stop · "
                          "可选 <BRANCH> = 本需求专属 merge_target(指定则覆盖 --merge-target / "
                          "localconfig 默认 · 不指定则用 --merge-target)· 🔴 该分支必须非 "
                          "main/master/默认(防无人 review 直接进 main)")
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

    # v8.46 C:planning-check · Feature Planning 物化入口(治本规划路径未物化漏洞)
    plc = sub.add_parser(
        "planning-check",
        help=("[v8.46] Feature Planning 物化入口 · emit 规划 checklist + 必读规范 + "
              "(若有 product-overview)规划状态机 · 不进状态机 · 治本规划路径靠 AI 自觉读 spec"),
    )
    plc.add_argument("--project-root", default=None,
                     help="项目根(检测 product-overview/)· 默认从 cwd 找 git 根")
    plc.set_defaults(func=cmd_planning_check)

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
    crr.add_argument("--accept-external-removal", action="store_true",
                     help="[v8.66] yolo 模式去 external 评审的显式逃生口 · 仅限 external CLI "
                          "客观不可用(未装/网络死·已重试失败)· 不得为效率/集中到 review stage 用 · "
                          "用了写 concern WARN 留痕")
    crr.set_defaults(func=cmd_change_review_roles)

    # v8.69:set-mode · 语义化设 auto_mode / yolo(替代 raw-write · 物化 + audit)
    sm = sub.add_parser(
        "set-mode",
        help="[v8.69] 设 auto_mode / yolo · 写 mode_changes audit · 替代 raw-write",
    )
    sm.add_argument("--feature", required=True, help="Feature 目录(含 state.json)")
    sm.add_argument("--reason", required=True, help="变更理由(必填 · 写 mode_changes audit)")
    sm.add_argument("--auto-mode", action="store_true", help="开启 auto_mode")
    sm.add_argument("--no-auto-mode", action="store_true", help="关闭 auto_mode")
    sm.add_argument("--yolo", nargs="?", const=True, default=None, metavar="BRANCH",
                    help="开启 yolo(implies auto_mode)· 可选 <BRANCH> = 专属 merge_target"
                         "(覆盖 · 必非 main/master/默认)")
    sm.add_argument("--no-yolo", action="store_true", help="关闭 yolo")
    sm.set_defaults(func=cmd_set_mode)

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
    # v8.43:template_echo 升 BLOCK 后的逃生口(治本 SVC-PLATFORM-F054 blueprint round 3)
    er.add_argument("--accept-quality-warnings", action="store_true",
                    help=("[v8.43] template_echo BLOCK 时显式承认评审实质 OK(误报) · "
                          "走 bypass log + concerns WARN 留痕 · retro 复盘可见。"
                          "用户应先实际读 file 验证再加此 flag"))
    # v8.44:doc-based prompt(治本 case round 4 长 prompt 卡 + 不可审计)
    er.add_argument("--prompt-doc",
                    help=("[v8.44] 显式 prompt-doc 路径 · 不传则默认 "
                          "<feature>/external-review-prompts/<stage>-<model>.md。"
                          "doc 不存在 → fallback v8.43 inline + emit WARN 提示 scaffold"))
    # v8.88:诚实降级自审兜底(异质客观不可用·已重试失败 时的弱安全网)
    er.add_argument("--self-review-fallback", action="store_true",
                    help=("[v8.88] 异质模型客观不可用(未装/未登录/配额满·已重试失败)时 · "
                          "跑**同模型 fresh exec** 自审 · 落 self-review/(非异质 · **不满足 "
                          "P0-154 异质门禁** · 仅弱安全网)· 必带 --reason。仍需修环境重跑真异质 "
                          "或 change-review-roles 移除 external(本产物作降级 evidence)"))
    er.add_argument("--reason",
                    help="[v8.88] --self-review-fallback 必带 · 异质为何不可用 + 已重试证据")
    er.set_defaults(func=cmd_external_review)

    # v8.44:scaffold-review-prompt · 生成 prompt-doc skeleton(AI 主对话填 compact summary)
    sp = sub.add_parser(
        "scaffold-review-prompt",
        help=("[v8.44] 生成 external-review prompt-doc skeleton · 让 AI 主对话填 "
              "compact summary · 治本 case round 4 长 prompt 卡 + 不可审计"),
    )
    sp.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    sp.add_argument("--stage", required=True, choices=["goal", "blueprint", "review"],
                    help="评审 stage(goal/blueprint/review · 各自 checklist 不同)")
    sp.add_argument("--model", required=True, choices=["claude", "codex"],
                    help="reviewer 模型(影响 doc 文件名 + perspective)")
    sp.add_argument("--force", action="store_true",
                    help="doc 已存在时覆盖(慎用 · 会丢失本地编辑)")
    sp.set_defaults(func=cmd_scaffold_review_prompt)

    # v8.24-v8.41:update-skill · 自更新 → v8.42 抽到独立 tools/update.py
    # 用法:python3 SKILL_ROOT/tools/update.py [--channel <branch>] [--accept-overwrite]
    # 不再在 state.py 注册 subparser(治本"元工具混运行时"+ chicken-and-egg)

    # ─── v8.0 stage 命令注册(Code-driven Orchestration) ─────────────
    # 设计文档:docs/archive/v8-redesign/00-MANIFESTO.md(rationale · 历史归档)
    # 命令 schema 现行权威:state.py --help + _v8_stage_specs.py
    #   (01-COMMAND-SCHEMA.md 为 v8.0 归档快照 · 命令已大幅演进)
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
