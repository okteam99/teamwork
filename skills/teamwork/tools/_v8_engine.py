"""
_v8_engine.py — Teamwork v8.0 stage orchestration engine.

v8.0 范式:state.py 主动校验 + 主动告知,AI 不读 spec markdown,跑命令即知做什么。

本模块提供:
- StageSpec / StagePrerequisite / StageArtifactSpec / StageEvidenceCheck 数据类
- execute_stage_start / execute_stage_complete 通用引擎
- bypass 协议(--bypass --reason --user-confirmed --missing)
- next_action_brief 渲染

各 stage 具体 spec 定义见 _v8_stage_specs.py。

设计哲学见 docs/v8-redesign/00-MANIFESTO.md。
命令 schema 见 docs/v8-redesign/01-COMMAND-SCHEMA.md。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# ─── 数据类 ────────────────────────────────────────────────────────────


@dataclass
class StagePrerequisite:
    """Stage 入口前置条件 · xx-start 时校验。"""

    id: str
    """前置 ID · 失败时用作 missing_prerequisites[].id"""

    check_fn: Callable[[dict, argparse.Namespace], bool]
    """校验函数 · 接收 (state, args),返回 True=通过 / False=未满足"""

    hint: str
    """失败时的 hint · 告诉 AI 下一步做什么修复"""

    description: str = ""
    """前置含义描述(给人看)"""

    auto_fixable: bool = False
    """PMO 是否能自动修复(不需要用户)"""


@dataclass
class StageArtifactSpec:
    """Stage 产物校验 · xx-complete 时校验。"""

    path: Optional[str] = None
    """单文件路径(相对 feature 目录)"""

    glob: Optional[str] = None
    """或 glob 模式(如 'external-cross-review/*.md')"""

    frontmatter_required: list[str] = field(default_factory=list)
    """YAML frontmatter 必含字段列表"""

    body_min_lines: int = 0
    """body 部分最少行数(0 表示不校验)"""

    min_files: int = 1
    """glob 时最少匹配文件数"""

    must_be_in_commit: bool = True
    """是否必须在 --auto-commit changeset 内"""

    description: str = ""


@dataclass
class StageEvidenceCheck:
    """Stage 事实证据校验 · xx-complete 时校验。"""

    name: str
    """证据名称 · 失败时用作 error 标识"""

    check_fn: Callable[[dict, argparse.Namespace], tuple[bool, str]]
    """校验函数 · 返回 (passed, error_msg)"""

    description: str = ""


@dataclass
class StageSpec:
    """单个 stage 的完整契约。"""

    name: str
    """stage 名称 · 与 LEGAL_STAGES 对齐"""

    prerequisites: list[StagePrerequisite] = field(default_factory=list)
    """入口前置(xx-start 校验)"""

    artifacts: list[StageArtifactSpec] = field(default_factory=list)
    """出口产物(xx-complete 校验)"""

    evidence_checks: list[StageEvidenceCheck] = field(default_factory=list)
    """事实证据(xx-complete 校验)"""

    brief_template_fn: Callable[[dict], str] = lambda state: ""
    """next_action_brief 渲染函数 · 接收 state,返回 markdown"""

    auto_transition_fn: Optional[Callable[[dict], Optional[str]]] = None
    """自动转移函数 · 返回下一 stage 名或 None(多选/终态)"""

    allowed_flow_types: Optional[list[str]] = None
    """允许的 flow_type 列表 · None 表示所有 flow 通用"""

    authorized_pause_point: str = ""
    """本 stage 内唯一授权的用户暂停点描述。

    v8.0+P0-1 治本 PTR-F033 case · L2 substep 链内部 AI 自觉区物化兜底。
    execute_stage_start 自动 append "暂停点纪律" 段到 next_action_brief 末尾,
    让 AI 在执行那一刻就看到红线 · 不靠回头扫 CLAUDE.md。

    例:
      authorized_pause_point="Substep 6 · 用户最终确认(全员 review 通过后)"
      authorized_pause_point="无暂停 · 完成后自动转下一 stage"
      authorized_pause_point="verdict=NEEDS_REVISION 时 · 用户选回 dev 还是接受"
    """


# ─── 工具函数 ──────────────────────────────────────────────────────────


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def emit_json(payload: dict, exit_code: int = 0) -> None:
    """统一 stdout JSON 输出 + exit。"""
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(exit_code)


def load_state(feature_path: str) -> tuple[Path, dict]:
    """加载 state.json · 返回 (path, state dict)"""
    p = Path(feature_path) / "state.json"
    if not p.exists():
        emit_json({
            "verdict": "FAIL",
            "error": f"state.json not found: {p}",
            "hint": "先跑 state.py init-feature 创建",
        }, exit_code=2)
    return p, json.loads(p.read_text(encoding="utf-8"))


def compute_raw_write_audit(state: dict) -> Optional[dict]:
    """扫 state.concerns[] · 抓 raw-write 条目 · 返 audit dict(无 raw-write 返 None)。

    用途:state.py / _v8_engine emit 时附 raw_write_audit 字段 ·
    PMO 看到 → 复查状态机缺口(v8.x 后任何 raw-write 都应视作 bug 信号)。
    """
    concerns = state.get("concerns") or []
    rw_concerns = [c for c in concerns if isinstance(c, str) and "raw-write" in c]
    if not rw_concerns:
        return None
    return {
        "count": len(rw_concerns),
        "occurrences": rw_concerns[-5:],  # 最近 5 条 · 防 emit 过长
        "hint": (
            "⚠️ 状态机有 raw-write 历史 · v8.x 后任何 raw-write 都应视作 bug 信号 · "
            "复查 concerns 中每条 reason → 治本(命令补全 / 或报 bug)· "
            "跨 Feature 汇总:state.py audit-raw-writes"
        ),
    }


def detect_main_tree_pollution(feature_dir: Path, feature_id: str) -> list[str]:
    """worktree 模式下检测主工作区是否冒出当前 Feature 的文件。

    治本:部分宿主的 patch/写工具不继承 shell cwd(如 codex apply_patch)·
    用相对路径写文件会落到主工作区污染主分支。stage-complete 时物化检测。

    返回污染文件行列表(git status --porcelain 格式)· 空 = 无污染 / 不适用。
    仅检测路径含 feature_id 的文件(Feature 文档目录)· 代码源文件无 ID 标识不检。
    """
    import subprocess as _sp
    if not feature_id:
        return []
    try:
        r = _sp.run(["git", "rev-parse", "--git-dir"],
                    capture_output=True, text=True, check=True, cwd=feature_dir)
    except (_sp.CalledProcessError, FileNotFoundError, OSError):
        return []
    if "/worktrees/" not in r.stdout.strip():
        return []  # 不在 linked worktree · 无主/副之分 · 不检测
    try:
        r = _sp.run(["git", "worktree", "list", "--porcelain"],
                    capture_output=True, text=True, check=True, cwd=feature_dir)
    except (_sp.CalledProcessError, FileNotFoundError, OSError):
        return []
    main_root = None
    for line in r.stdout.splitlines():
        if line.startswith("worktree "):
            main_root = line.split(" ", 1)[1]
            break
    if not main_root:
        return []
    try:
        r = _sp.run(["git", "-C", main_root, "status", "--porcelain"],
                    capture_output=True, text=True, check=True)
    except (_sp.CalledProcessError, FileNotFoundError, OSError):
        return []
    return [ln.strip() for ln in r.stdout.splitlines() if feature_id in ln]


def save_state(path: Path, state: dict) -> None:
    """写 state.json · 自动 stamp `_state_checksum`(同 state.py atomic_write)。

    防止下次读时 _verify_checksum FAIL · 治本"v8 stage 命令写完后必 recover"噪音。
    算法必须与 state.py._compute_checksum 一致。
    """
    import hashlib

    state["updated_at"] = now_iso()
    state["updated_by"] = state.get("updated_by") or "pmo"

    # checksum 同 state.py CHECKSUM_FIELD 算法 · canonical sha256 (排除 _state_checksum 字段)
    cleaned = {k: v for k, v in state.items() if k != "_state_checksum"}
    canonical = json.dumps(
        cleaned, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    state["_state_checksum"] = (
        "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    )

    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def get_git_commit_changeset(commit_hash: str, cwd: Optional[str] = None) -> list[str]:
    """获取 commit 的 changeset 文件列表 · 不存在返回 []"""
    try:
        result = subprocess.run(
            ["git", "show", "--name-only", "--format=", commit_hash],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def commit_exists(commit_hash: str, cwd: Optional[str] = None) -> bool:
    """git cat-file -e 校验 commit 存在性"""
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", commit_hash],
            cwd=cwd,
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def git_head(cwd: Optional[str] = None) -> Optional[str]:
    """取当前 git HEAD commit hash · 失败返 None。

    用于 --auto-commit 未传时的默认值:AI 标准流程「产物落盘 → git commit →
    xx-complete」· HEAD 即本 stage 产出的 commit。
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _worktree_physically_exists(wt_path: str) -> bool:
    """检查 wt_path 是否在 `git worktree list` 输出内。

    v8.0+P0-2 治本 PTR-F033-type-2 case · stage-start 通用 worktree 校验。
    """
    if not wt_path:
        return False
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return True  # 不在 git repo · 跳过此校验(让 cwd-based 校验兜底)
        # 解析 porcelain 输出 · "worktree /abs/path" 形式
        for line in result.stdout.splitlines():
            if line.startswith("worktree ") and Path(line[9:].strip()) == Path(wt_path).resolve():
                return True
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return True  # git 不可用 · 跳过(避免因 git 缺失阻塞流程)


def parse_frontmatter(file_path: Path) -> Optional[dict]:
    """解析 markdown 文件的 YAML frontmatter · 失败返回 None"""
    if not file_path.exists():
        return None
    try:
        text = file_path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            return None
        end = text.find("\n---\n", 4)
        if end == -1:
            return None
        fm_text = text[4:end]
        # 简易 YAML 解析(只支持 key: value 和 key:\n  - list)
        result = {}
        current_key = None
        for line in fm_text.splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            if line.startswith("  - "):
                if current_key and isinstance(result.get(current_key), list):
                    result[current_key].append(line[4:].strip())
                continue
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip()
                if not val:
                    result[key] = []
                    current_key = key
                else:
                    result[key] = val
                    current_key = None
        return result
    except (OSError, UnicodeDecodeError):
        return None


# ─── bypass 协议 ──────────────────────────────────────────────────────


def require_user_confirmed(args: argparse.Namespace) -> None:
    """逃生时强制要求 --user-confirmed flag · 缺则拦截"""
    if not getattr(args, "user_confirmed", False):
        emit_json({
            "verdict": "FAIL",
            "error": "--bypass requires --user-confirmed flag(防 AI 自决逃生)",
            "hint": (
                "暂停点询问用户 · 用户明确确认后再调用此命令 · "
                "并加 --user-confirmed flag。"
                "审计时若发现 AI 自加此 flag 而对话历史无用户确认 = 红线违规。"
            ),
        }, exit_code=1)


def write_bypass_log(
    state: dict,
    stage: str,
    phase: str,
    missing: list[dict],
    args: argparse.Namespace,
    retry_count: int = 0,
) -> str:
    """写 bypass_log 到 state · 返回 concerns_id(时间戳)"""
    ts = now_iso()
    state.setdefault("bypass_log", []).append({
        "stage": stage,
        "phase": phase,
        "at": ts,
        "missing": [m["id"] if isinstance(m, dict) else m for m in missing],
        "reason": args.reason,
        "user_confirmed": True,
        "retry_count_before_bypass": retry_count,
        "concerns_id": ts,
    })
    # 同步写 concerns WARN
    state.setdefault("concerns", []).append(
        f"{ts} WARN {stage}-{phase} bypass · missing={','.join(m['id'] if isinstance(m, dict) else m for m in missing)} · reason: {args.reason}"
    )
    return ts


# ─── 通用引擎 ──────────────────────────────────────────────────────────


def execute_stage_start(
    stage_spec: StageSpec,
    args: argparse.Namespace,
    legal_transitions: dict[str, dict[str, list[str]]],
    flow_by_type: dict[str, dict],
) -> None:
    """xx-stage-start 通用执行流程。"""
    feature_path = args.feature
    path, state = load_state(feature_path)

    # 1. flow_type 校验
    if stage_spec.allowed_flow_types:
        flow = state.get("flow_type")
        if flow not in stage_spec.allowed_flow_types:
            emit_json({
                "verdict": "FAIL",
                "stage": stage_spec.name,
                "phase": "start",
                "error": f"flow_type={flow!r} 不允许进入 {stage_spec.name}",
                "allowed_flow_types": stage_spec.allowed_flow_types,
                "hint": "检查 state.flow_type 是否正确",
            }, exit_code=1)

    # 2. legal 转移校验
    current = state.get("current_stage")
    flow_type = state.get("flow_type")
    flow_graph = flow_by_type.get(flow_type, {})
    legal_next = flow_graph.get(current, [])
    is_initial_entry = current is None or current == stage_spec.name
    if not is_initial_entry and stage_spec.name not in legal_next:
        emit_json({
            "verdict": "FAIL",
            "stage": stage_spec.name,
            "phase": "start",
            "error": f"非法转移: {current!r} → {stage_spec.name!r}",
            "current_stage": current,
            "legal_next_stages": legal_next,
            "hint": (
                f"当前 stage {current!r} 不能直接进入 {stage_spec.name!r}。"
                f"合法下一 stage: {legal_next}。"
                "若刻意跳过/回炉 · 加 --bypass --reason ... --user-confirmed --missing legal_transition"
            ),
        }, exit_code=1 if not args.bypass else 0)

    # 2.5. 通用 worktree 物理存在校验(v8.0+P0-2 治本 PTR-F033-type-2 case)
    # 治本根因:init-feature 只写 worktree 元数据 · PMO 漏跑 git worktree add ·
    # 后续 stage 在主 tree 写代码 · 污染主分支。
    # 物化:state.worktree.path + state.worktree.strategy != "off" → 必须 git worktree list 含此 path。
    wt = state.get("worktree", {}) or {}
    wt_strategy = wt.get("strategy", "off")
    wt_path = wt.get("path")
    if wt_strategy != "off" and wt_path:
        if not _worktree_physically_exists(wt_path):
            wt_missing = {
                "id": "worktree_physical_exists",
                "description": "state.worktree.path 必须实际存在(git worktree list 含此 path)",
                "actual": False,
                "hint": (
                    f"state.json 说 worktree_mode={wt_strategy} path={wt_path} · "
                    f"但 git worktree list 未找到 · "
                    f"补建:`git worktree add -b {wt.get('branch', '<branch>')} "
                    f"{wt_path} origin/{state.get('merge_target', '<base>')}`"
                ),
                "auto_fixable": False,
            }
            if args.bypass:
                # bypass 路径需要 --missing 显式列出
                user_missing = set(args.missing.split(",")) if args.missing else set()
                if "worktree_physical_exists" not in user_missing:
                    emit_json({
                        "verdict": "FAIL",
                        "error": "worktree 物理不存在 + bypass 但 --missing 未含 worktree_physical_exists",
                        "hint": "加 --missing worktree_physical_exists 显式承认",
                    }, exit_code=1)
                require_user_confirmed(args)
                write_bypass_log(state, stage_spec.name, "start", [wt_missing], args)
            else:
                emit_json({
                    "verdict": "FAIL",
                    "stage": stage_spec.name,
                    "phase": "start",
                    "missing_prerequisites": [wt_missing],
                    "hint": "按 hint 补建 worktree · 重跑 stage-start · 或 bypass 显式承认",
                }, exit_code=1)

    # 3. 校验所有 prerequisites
    missing = []
    for prereq in stage_spec.prerequisites:
        try:
            passed = prereq.check_fn(state, args)
        except Exception as e:
            passed = False
            prereq_hint = f"{prereq.hint} (check raised: {e})"
        else:
            prereq_hint = prereq.hint

        if not passed:
            missing.append({
                "id": prereq.id,
                "description": prereq.description,
                "actual": False,
                "hint": prereq_hint,
                "auto_fixable": prereq.auto_fixable,
            })

    # 4. bypass 处理
    if missing and args.bypass:
        require_user_confirmed(args)
        # 用户声称跳过的 missing 必须与实际 missing 重叠
        user_missing = set(args.missing.split(",")) if args.missing else set()
        actual_missing_ids = set(m["id"] for m in missing)
        not_covered = actual_missing_ids - user_missing
        if not_covered:
            emit_json({
                "verdict": "FAIL",
                "error": "--missing 未覆盖所有实际 missing prerequisites",
                "actual_missing": list(actual_missing_ids),
                "user_specified_missing": list(user_missing),
                "not_covered": list(not_covered),
                "hint": f"--missing 必须包含: {','.join(actual_missing_ids)}",
            }, exit_code=1)

        # 通过 bypass
        write_bypass_log(state, stage_spec.name, "start", missing, args)
        missing = []  # 清空 missing,继续走 PASS 路径

    elif missing:
        emit_json({
            "verdict": "FAIL",
            "stage": stage_spec.name,
            "phase": "start",
            "missing_prerequisites": missing,
            "hint": "按 missing_prerequisites[*].hint 逐条修复 · 重试本命令 · 重试 3 次仍 FAIL 时给用户暂停点选择 bypass",
        }, exit_code=1)

    # 5. 转移 current_stage 到本 stage
    state["current_stage"] = stage_spec.name
    state["legal_next_stages"] = flow_graph.get(stage_spec.name, [])

    # 6. 初始化 stage_contract
    contracts = state.setdefault("stage_contracts", {})
    contract = contracts.setdefault(stage_spec.name, {
        "input_satisfied": False,
        "process_satisfied": False,
        "output_satisfied": False,
    })
    contract.setdefault("started_at", now_iso())

    # 6.5 v8.36:host 校准(治本 SVC-PLATFORM-F054 case · 全局 audit 跨 session 污染)
    # 用户传 --host → 与 state.json.host 比对 · 不一致 → 更新 + concerns 留痕
    host_change_warning = None
    new_host = getattr(args, "host", None)
    if new_host:
        old_host = state.get("host")
        if old_host and old_host != new_host:
            host_change_warning = (
                f"{now_iso()} WARN {stage_spec.name}-start host 切换: "
                f"{old_host!r} → {new_host!r} · "
                f"(v8.36 治本 v8.21 全局 audit 跨 session 污染 case · "
                f"用户跨 session 切宿主时显式覆盖 state.json.host)"
            )
            concerns = state.setdefault("concerns", [])
            concerns.append(host_change_warning)
        state["host"] = new_host
        # host_history append(audit · 不替换)
        history = state.setdefault("host_history", [])
        history.append({"host": new_host, "at": now_iso(),
                         "source": f"{stage_spec.name}-start",
                         "previous": old_host})

    save_state(path, state)

    # 7. 渲染 next_action_brief + 自动 append 建议评审角色 + 暂停点纪律 + 必读路径速查 + 状态行模板
    brief = stage_spec.brief_template_fn(state)
    brief += _render_review_roles_suggestion(state, stage_spec.name)
    if stage_spec.authorized_pause_point:
        brief += _render_pause_discipline(stage_spec.authorized_pause_point)
    # 必读路径速查(P0-4)
    brief += _render_required_paths(Path(args.feature).resolve(), stage_spec.name)
    # 状态行模板(P0-10:AI 每次主对话回复末尾必含)
    next_hint = f"按 brief 完成 stage 工作 → 跑 {stage_spec.name}-complete"
    brief += _render_status_line_block(state, next_hint)

    # 7.1 体量元规则:超 MAX_BRIEF_LINES 则截断 + 写完整版到磁盘
    brief_lines = brief.count("\n") + 1
    brief_overflow_path = None
    if brief_lines > MAX_BRIEF_LINES:
        full_path = Path(feature_path) / f"_brief_full_{stage_spec.name}.md"
        try:
            full_path.write_text(brief, encoding="utf-8")
            brief_overflow_path = str(full_path)
            # brief 留前 80 行 + 摘要尾巴
            head = brief.splitlines()[:80]
            brief = "\n".join(head) + (
                f"\n\n---\n\n⚠️ brief 共 {brief_lines} 行 > {MAX_BRIEF_LINES} · 截断 · "
                f"完整版见 [{full_path.name}]({full_path.name})"
            )
        except OSError:
            pass  # 写磁盘失败 · 用完整 brief

    rw_audit = compute_raw_write_audit(state)
    scaffold_hints = build_scaffold_hints(stage_spec.name)
    emit_json({
        "verdict": "PASS",
        "stage": stage_spec.name,
        "phase": "start",
        "transition": f"{current} → {stage_spec.name}",
        "started_at": contract["started_at"],
        "next_action_brief": brief,
        "status_line": render_status_line(state, f"按 brief 完成 → {stage_spec.name}-complete"),
        **({"scaffold_hints": scaffold_hints} if scaffold_hints else {}),
        **({"brief_overflow_path": brief_overflow_path} if brief_overflow_path else {}),
        **({"raw_write_audit": rw_audit} if rw_audit else {}),
        # v8.36:host 切换 / 校准信息暴露
        **({"host_change_warning": host_change_warning} if host_change_warning else {}),
        **({"current_host": state.get("host")} if state.get("host") else {}),
    })


def _find_project_root(feature_dir: Path) -> Path:
    """从 feature_dir 向上找项目根(含 .git)· 找不到回 feature_dir.parent。"""
    p = feature_dir.resolve()
    for _ in range(10):
        if (p / ".git").exists():
            return p
        if p.parent == p:
            return feature_dir.resolve()
        p = p.parent
    return feature_dir.resolve()


def _find_skill_root() -> Path:
    """SKILL_ROOT 路径(本模块所在目录的上一级)。"""
    return Path(__file__).resolve().parent.parent


# 各 stage 对应的 spec 文件名(stages/*.md)
STAGE_SPEC_FILES = {
    "goal": "goal-stage.md",
    "ui_design": "ui-design-stage.md",
    "panorama_sync": "panorama-sync-stage.md",
    "planning": "planning-stage.md",
    "blueprint": "blueprint-stage.md",
    "blueprint_lite": "blueprint-lite-stage.md",
    "dev": "dev-stage.md",
    "review": "review-stage.md",
    "test": "test-stage.md",
    "browser_e2e": "browser-e2e-stage.md",
    "pm_acceptance": "pm-acceptance-stage.md",  # 若不存在 fallback
    "ship": "ship-stage.md",
}


# v8.14:各 stage 起草模板 + 校验器映射 · 治本 PTR-F054 "AI 找历史 Feature 抄" case
# 设计:
# - stage-start emit 时返回 scaffold_hints · AI 第一时间知道模板路径 + 校验器
# - 避免 AI 退回 find 历史 Feature(已 ship 清理 / 介质不同 / 早期版本)
# - artifact_name → template_filename(相对 SKILL_ROOT/templates/)· None = 无模板
# - validators[artifact_name] = (script_filename, 一句话说明)
#
# 不要在此放 dev / ship(无文档模板)· 不要放 review-log.jsonl(state.py append)
STAGE_TEMPLATES: dict[str, dict] = {
    "goal": {
        "templates": {
            "PRD.md": "prd.md",
            "PRD-REVIEW.md": None,  # 无独立模板 · 按 reviewer 分段
            "external-cross-review/prd-{model}.md": "external-cross-review.md",
        },
        "validators": {},
    },
    "ui_design": {
        "templates": {
            "UI.md": "ui.md",
            "preview/*.html": None,  # static-html 介质 · 项目设计语言决定
            # same-stack 介质(v8.58):拷入 {panorama_path}/preview-project/ 根 · 按框架改 dev server 行
            "preview-project/preview.sh": "preview-project-preview.sh",
        },
        "validators": {},
    },
    "panorama_sync": {
        "templates": {
            "panorama-change-summary.md": None,
            "panorama_path/sitemap.md": None,
            "panorama_path/preview/overview.html": None,
        },
        "validators": {},
    },
    "blueprint": {
        "templates": {
            "TC.md": "tc.md",
            "TECH.md": "tech.md",
            "TECH-REVIEW.md": None,
            "external-cross-review/*.md": "external-cross-review.md",
        },
        "validators": {
            "TC.md": ("verify-ac.py",
                      "校验 PRD 每条 AC 在 TC.md tests[].covers_ac ≥1 引用 · 漏覆盖 FAIL"),
        },
    },
    "blueprint_lite": {
        "templates": {
            "TC.md": "tc.md",
            "TECH.md": "tech.md",
        },
        "validators": {
            "TC.md": ("verify-ac.py",
                      "校验 PRD 每条 AC 在 TC.md tests[].covers_ac ≥1 引用 · 漏覆盖 FAIL"),
        },
    },
    "dev": {
        "templates": {
            "bugfix/BUG-XXX.md": "bug-report.md",  # flow_type=Bug 时
        },
        "validators": {},
    },
    "review": {
        "templates": {
            "REVIEW.md": None,
            "REVIEW-arch.md": None,
            "REVIEW-qa.md": None,
            "external-cross-review/*.md": "external-cross-review.md",
        },
        "validators": {},
    },
    "test": {
        "templates": {
            "TEST-REPORT.md": "test-report.md",
            "e2e/*.py": None,  # 项目环境决定
        },
        "validators": {
            "TC.md": ("verify-ac.py",
                      "test-complete 复跑 verify-ac.py · 防 dev 阶段 TC 漏改"),
        },
    },
    "browser_e2e": {
        "templates": {
            "BROWSER-TEST-REPORT.md": "browser-test-report.md",
            "screenshots/*.png": None,  # 按 SOP 截图(含 viewport + URL bar)
        },
        "validators": {},
    },
    "pm_acceptance": {
        "templates": {
            "PM-NOTE.md": "pm-note.md",  # 可选 · rejected 时含 finding 列表
        },
        "validators": {},
    },
}


def build_scaffold_hints(stage_name: str) -> dict | None:
    """组装 stage 的 scaffold_hints emit 段(v8.14)。

    返回 None 表示该 stage 无模板/校验器(如 ship)· 调用方按需 spread 进 emit JSON。
    路径全 absolute(SKILL_ROOT/templates/<file>)· AI 直接 cat 不用拼。
    治本 PTR-F054 "AI 找历史 Feature 抄" case。
    """
    cfg = STAGE_TEMPLATES.get(stage_name)
    if not cfg:
        return None
    skill_root = _find_skill_root()
    templates_dir = skill_root / "templates"

    expected_artifacts = list(cfg.get("templates", {}).keys())
    templates_abs: dict[str, str | None] = {}
    for artifact, tmpl_name in cfg.get("templates", {}).items():
        if tmpl_name:
            templates_abs[artifact] = str(templates_dir / tmpl_name)
        else:
            templates_abs[artifact] = None  # 无独立模板(按 schema 自由分段)

    validators_abs: dict[str, str] = {}
    for artifact, (script_name, note) in cfg.get("validators", {}).items():
        script_path = templates_dir / script_name
        validators_abs[artifact] = f"{script_path}({note})"

    return {
        "expected_artifacts": expected_artifacts,
        "templates": templates_abs,
        "validators": validators_abs,
        "hint": (
            "起草前先 cat 模板(已含 frontmatter + body 骨架)· "
            "不要 find 历史 Feature 抄(可能已 ship 清理 / 介质不同 / 早期 schema)。"
            "无模板的产物(value=null)按 stage spec § Output Contract 的 schema 自由分段。"
        ),
    }


# 哪些 stage 在 brief 中渲染"评审角色"提示
# - 含 dev:本 stage 无 reviewer · 但可调后续 stage(治本 dev 评估代码后调 test 评审 case)
# - 排除 pm_acceptance(永远只有 pm 1 角色 · 无调整空间)/ ship / completed(无 reviewer · 无后续)
# - test 之后即关掉(用户洞察 · 实证)
STAGES_WITH_REVIEW_ROLES_HINT = {
    "goal", "ui_design", "panorama_sync", "blueprint", "blueprint_lite",
    "dev", "review", "test", "browser_e2e",
}


def _render_review_roles_suggestion(state: dict, stage_name: str) -> str:
    """渲染本 stage 评审角色 + 调整指引(覆盖本/后续 stage)。

    数据源:state.stage_review_roles(init-feature 已写入 · 各 stage 默认值)
    - 本 stage 有 reviewer → 显示"本 stage 角色 + 可调本/后续 stage"
    - 本 stage 无 reviewer(dev)→ 显示"本 stage 无评审 · 但可调后续 stage"(治本 dev 评估代码后调 test 评审 case)
    - state.stage_review_roles 整体空 → 返回空串(不渲染)
    - stage ∉ STAGES_WITH_REVIEW_ROLES_HINT(pm_acceptance / ship / completed)→ 返回空串
    """
    if stage_name not in STAGES_WITH_REVIEW_ROLES_HINT:
        return ""

    all_roles = state.get("stage_review_roles", {})
    if not all_roles:
        return ""

    own_roles = all_roles.get(stage_name, [])
    configured = sorted(all_roles.keys())

    adjustments = state.get("stage_review_roles_adjustments", []) or []
    has_adjustment = any(
        isinstance(a, dict) and a.get("stage") == stage_name for a in adjustments
    )
    suffix = " (已调整 · 见 state.stage_review_roles_adjustments audit)" if has_adjustment else ""

    own_line = (
        f"- 当前阶段评审角色:`{', '.join(own_roles)}`\n"
        if own_roles
        else f"- 当前阶段无评审角色\n"
    )
    return (
        f"\n\n## 📋 评审角色{suffix}\n\n"
        f"{own_line}"
        f"- 可根据实际复杂度调整当前及后续 stage 参与评审的角色:"
        f"`state.py change-review-roles --feature <path> --stage <{' / '.join(configured)}> --roles 'a,b,c' --reason '<理由>'`\n"
    )


def _render_required_paths(feature_dir: Path, stage_name: str) -> str:
    """渲染必读路径速查(绝对路径 · brief 末尾自动 append)。

    v8.0+P0-4 治本:brief 之前只列 "PROJECT.md (产品全景)" 文件名 · AI 要搜路径。
    现在直接给绝对路径 · AI 拿到即 Read。
    """
    project_root = _find_project_root(feature_dir)
    skill_root = _find_skill_root()

    sections = []

    # 1. 项目级元文档(只列已存在的)
    project_docs = []
    for fn, desc in [
        ("PROJECT.md", "产品全景"),
        ("ROADMAP.md", "Feature 优先级"),
        ("sitemap.md", "信息架构"),
    ]:
        p = project_root / fn
        if p.exists():
            project_docs.append(f"- `{p}` — {desc}")
    # workspace 级工程文档 · v8.3 收敛进 project-specs/(详 conventions.md §13)
    for fn, desc in [
        ("KNOWLEDGE.md", "项目级 Gotcha + Convention"),
        ("GLOSSARY.md", "业务术语"),
        ("TROUBLESHOOTING.md", "排查手册"),
    ]:
        p = project_root / "project-specs" / fn
        if p.exists():
            project_docs.append(f"- `{p}` — {desc}")
    arch = project_root / "docs/architecture/ARCHITECTURE.md"
    if arch.exists():
        project_docs.append(f"- `{arch}` — 系统架构")
    if project_docs:
        sections.append("**项目级文档**(按需 read):\n" + "\n".join(project_docs))

    # 2. Feature 内已存在的 artifact
    feature_artifacts = []
    for fn, desc in [
        ("PRD.md", "需求规范"),
        ("PRD-REVIEW.md", "PRD 评审"),
        ("TC.md", "测试用例"),
        ("TC-REVIEW.md", "TC 评审"),
        ("TECH.md", "技术方案"),
        ("TECH-REVIEW.md", "Tech Review"),
        ("UI.md", "UI 设计"),
        ("REVIEW.md", "代码评审总结"),
        ("REVIEW-arch.md", "架构师评审"),
        ("REVIEW-qa.md", "QA 评审"),
        ("TEST-REPORT.md", "测试报告"),
        ("BROWSER-TEST-REPORT.md", "浏览器测试报告"),
    ]:
        p = feature_dir / fn
        if p.exists():
            feature_artifacts.append(f"- `{p}` — {desc}")
    if feature_artifacts:
        sections.append("**Feature 内已存在 artifact**:\n" + "\n".join(feature_artifacts))

    # 3. 本 stage spec 文件(可选深读 · 不强制)
    spec_file = STAGE_SPEC_FILES.get(stage_name)
    if spec_file:
        spec_path = skill_root / "stages" / spec_file
        if spec_path.exists():
            sections.append(
                f"**Stage Telos + Rationale**(可选深读 · brief 不清晰时查):\n"
                f"- `{spec_path}` — 本 stage 设计 rationale"
            )

    # 4. state.json 自身
    state_json = feature_dir / "state.json"
    if state_json.exists():
        sections.append(
            f"**Feature 状态机**:\n- `{state_json}` — 状态机权威 · "
            f"用 `state.py snapshot --feature {feature_dir}` 查看(不要直接编辑)"
        )

    if not sections:
        return ""

    return "\n\n---\n\n### 📂 必读路径速查(绝对路径)\n\n" + "\n\n".join(sections) + "\n"


def _render_status_line_block(state: dict, next_action: str = "") -> str:
    """v8.0+P0-10:brief 末尾追加"状态行模板"段。

    给 AI 一个"复制粘贴到主对话回复末尾"的现成模板。
    """
    sl = render_status_line(state, next_action)
    return f"""

---

### 📊 状态行模板(R5+P0-10 · AI 每次主对话回复末尾必含)

```
{sl}
```

复制以上 3 行粘贴到回复末尾(用 `---` 隔开 brief 主体)·
让用户实时感知流程位置 + 路径 + 分支。
"""


def render_status_line(state: dict, next_action: str = "") -> str:
    """v8.0+P0-10:渲染 3 行状态行(替代 v7 STATUS-LINE.md · 物化版)。

    格式:
    ```
    🔄 {feature_id} ({flow_type} · {current_stage}) | 下一步:{next_action}
    📁 {artifact_root}
    🌿 {branch}(worktree: {wt_path · 与 artifact_root 不同时显示})
    ```

    用途:
    - brief 末尾自动 append(P0-10 物化 · AI 复制到回复末尾)
    - 暂停点 markdown 内嵌
    - AI 每次主对话回复末尾必含(R5+P0-10 软约束)

    Args:
        state: state.json dict
        next_action: 下一步描述(可选 · 不传则第 1 行不含"下一步:"段)
    """
    feature_id = state.get("feature_id", "?")
    flow_type = state.get("flow_type", "?")
    current = state.get("current_stage", "?")
    feature_dir = state.get("artifact_root", "?")
    worktree = state.get("worktree", {}) or {}
    branch = worktree.get("branch", "?")
    wt_path = worktree.get("path") or ""

    line1 = f"🔄 {feature_id} ({flow_type} · {current})"
    if next_action:
        line1 += f" | 下一步:{next_action}"

    line2 = f"📁 {feature_dir}"

    if wt_path and wt_path != feature_dir:
        line3 = f"🌿 {branch}(worktree: {wt_path})"
    else:
        line3 = f"🌿 {branch}"

    return f"{line1}\n{line2}\n{line3}"


def _render_pause_discipline(authorized_pause_point: str) -> str:
    """暂停点纪律段 · append 到 brief 末尾(紧凑版 · 8 行)。

    v8.0+P0-1 治本 PTR-F033 case · L2 substep 链 AI 自觉区。
    详细 rationale + 反模式黑名单见 docs/v8-redesign/04-PAUSE-POINT-DISCIPLINE.md
    (违规被 hint 时再读 · 不每次 inline 全文)。
    """
    return f"""

---

### 🔴 暂停点纪律(R5 物化)

唯一授权暂停:**{authorized_pause_point}**

- ⛔ Substep 中间禁 AskUserQuestion · Open Questions 写进 PRD/Review 评审
- ✅ 全部疑问到授权暂停点**一次性** escalate
- 🛡️ 兜底:state.py 校验 review mtime + frontmatter.revision_history
- 📖 详细:[docs/v8-redesign/04-PAUSE-POINT-DISCIPLINE.md](../docs/v8-redesign/04-PAUSE-POINT-DISCIPLINE.md)
"""


# ─── brief 体量元规则(防 Layer A 累积膨胀) ────────────────────────


# ─── v8.0+P0-9:review 角色 enum + 默认矩阵 ──────────────────────────


REVIEW_ROLE_ENUM = {"pm", "qa", "architect", "rd", "designer", "pl", "external"}
"""review 角色 7 闭集。

设计:
- pmo 不在内(PMO 是编排器 · 不 review 自己编排的工作)
- user 不在内(用户验收在 pm_acceptance 内的 ⏸️ 暂停点 · 不算 review 角色)
- rd 在内(默认不进 review 矩阵 · PMO 可显式调入 · 罕见 case)
- external = 异质模型(codex/claude/gemini)cross-review · 工具角色
"""

# (flow_type, stage) → 默认 review 角色清单
DEFAULT_REVIEW_ROLES: dict[tuple[str, str], list[str]] = {
    # Feature 流程
    ("Feature", "goal"): ["pm", "qa", "architect", "pl", "external"],
    ("Feature", "ui_design"): ["designer", "pm"],
    ("Feature", "panorama_sync"): ["pm", "architect"],
    ("Feature", "blueprint"): ["qa", "architect", "external"],
    ("Feature", "review"): ["architect", "qa", "external"],
    ("Feature", "test"): ["qa"],
    ("Feature", "browser_e2e"): ["qa", "designer"],
    ("Feature", "pm_acceptance"): ["pm"],

    # 敏捷需求
    ("敏捷需求", "goal"): ["pm", "qa", "architect"],
    ("敏捷需求", "blueprint_lite"): ["qa"],
    ("敏捷需求", "review"): ["architect", "qa", "external"],
    ("敏捷需求", "test"): ["qa"],
    ("敏捷需求", "pm_acceptance"): ["pm"],

    # Bug 流程
    ("Bug", "review"): ["architect", "qa", "external"],
    ("Bug", "test"): ["qa"],
    ("Bug", "pm_acceptance"): ["pm"],

    # Micro 流程
    ("Micro", "pm_acceptance"): ["pm"],

    # Feature Planning
    ("Feature Planning", "goal"): ["pm", "pl", "external"],
    ("Feature Planning", "planning"): ["pl", "pm", "external"],
}


def build_default_stage_review_roles(flow_type: str) -> dict[str, list[str]]:
    """按 flow_type 抽取默认 stage_review_roles dict。

    返回 {stage_name: [roles]} · 仅含该 flow_type 适用的 stage。
    """
    return {
        stage: roles[:]  # copy 防共享引用
        for (ft, stage), roles in DEFAULT_REVIEW_ROLES.items()
        if ft == flow_type
    }


# 各 flow_type 完整 stage chain(显式顺序 + optional 标识 + 评审建议理由)
# 用途:prepare-check --flow-type 渲染暂停点「📋 stage × 评审角色」预览表
# 与 FLOW_BY_TYPE(state.py)互补:那里是转移图(legal_next_stages 校验) · 这里是 chain 视图(顺序展示)
FLOW_STAGE_CHAIN: dict[str, list[tuple[str, bool, str, str]]] = {
    # (stage_name, optional, optional_trigger_note, review_reason_hint)
    "Feature": [
        ("goal", False, "", "PRD 需多视角把关:PM/QA/Architect/PL 各自专业领域 + External 异质模型 cross-review"),
        ("ui_design", True, "goal-complete --needs-ui=true 时启用", "Designer 视觉一致 + PM 流程合理"),
        ("panorama_sync", True, "ui_design-complete --panorama-changed=true 时启用", "PM 跨 Feature 视角 + Architect IA 影响"),
        ("blueprint", False, "", "TECH 选型与测试规划需 Architect/QA 把关 + External 异质 review"),
        ("dev", False, "", "无评审 · RD 自写 + commit(TDD 红绿循环 + 自查清单)"),
        ("review", False, "", "代码 Architect 看架构合理 + QA 看 AC 对照 + External 跨模型独立判断"),
        ("test", False, "", "QA 验收集成测试 + AC 全覆盖 + E2E 结果"),
        ("browser_e2e", True, "execution_hints.browser_e2e_needed=true 时启用", "QA 跑 E2E + Designer 视觉确认"),
        ("pm_acceptance", False, "", "PM 用户视角逐条 AC 验收 · 决定是否 ship"),
        ("ship", False, "", "无评审 · PMO 编排 push + MR + 合入 + cleanup"),
    ],
    "敏捷需求": [
        ("goal", False, "", "需求小但仍需 PM 清晰度 + QA 测试视角 + Architect 技术可行(无 PL/External)"),
        ("blueprint_lite", False, "", "QA 测试规划(TC 精简版)· 不要 TECH-REVIEW"),
        ("dev", False, "", "无评审 · RD 自写 + commit"),
        ("review", False, "", "Architect/QA + External cross-review(同 Feature)"),
        ("test", False, "", "QA 验收"),
        ("pm_acceptance", False, "", "PM 用户视角验收"),
        ("ship", False, "", "无评审 · PMO 编排"),
    ],
    "Bug": [
        ("dev", False, "", "无评审 · RD 起草 BUG 报告(模板 templates/bug-report.md)+ 写 fix + commit"),
        ("review", False, "", "修复方案 Architect + QA + External 把关(防 fix 引入新问题)"),
        ("test", False, "", "QA 验收回归测试(原 bug 不复发 + 周边无新错)"),
        ("pm_acceptance", False, "", "PM 验收(纯 infra/低风险 fix 可加快)"),
        ("ship", False, "", "无评审 · PMO 编排"),
    ],
    "Micro": [
        ("dev", False, "", "无评审 · RD 直接改(文案/样式/资源/配置 · 零逻辑)"),
        ("pm_acceptance", False, "", "PM 看效果即可(无 review/test 中间环节)"),
        ("ship", False, "", "无评审 · PMO 编排"),
    ],
}


def build_stage_chain_preview(flow_type: str) -> list[dict]:
    """返回 prepare-check 用的 stage chain preview · 每条含 reviewers + reason_hint。

    格式:[{"stage": str, "optional": bool, "trigger": str, "reviewers": [str], "reason": str}]
    - reviewers 来自 DEFAULT_REVIEW_ROLES · 不在则空列表(dev/ship 等无 reviewer stage)
    - reason 是评审建议理由(为什么选这些角色 · 给用户决策参考)
    - 顺序按 FLOW_STAGE_CHAIN 显式定义
    """
    chain = FLOW_STAGE_CHAIN.get(flow_type, [])
    return [
        {
            "stage": stage,
            "optional": optional,
            "trigger": trigger,
            "reviewers": DEFAULT_REVIEW_ROLES.get((flow_type, stage), []),
            "reason": reason,
        }
        for stage, optional, trigger, reason in chain
    ]


MAX_BRIEF_LINES = 100
"""单 stage brief 最大行数(含所有 append 的纪律段)。

未来 v8.0+P0-N 加新纪律段时:
- 先判断是否通用(所有 stage 适用)→ 进 _render_universal_discipline()
- stage 专属 → 改 stage 的 brief_template_fn
- 超 MAX_BRIEF_LINES → execute_stage_start 自动写完整版到磁盘 + brief 留摘要

设计动机:防 Layer A(brief inline 预防模式)累积膨胀。
每条新纪律默认压到 ≤8 行 · 详细 rationale 留磁盘文档。

参考 v7 教训:RULES.md(v8.15 已删 · 内容迁 SKILL.md / MANIFESTO)累积到 1883 行 · v8 不能在 brief 重蹈覆辙。
"""


def execute_stage_complete(
    stage_spec: StageSpec,
    args: argparse.Namespace,
    legal_transitions: dict[str, dict[str, list[str]]],
    flow_by_type: dict[str, dict],
    stage_specs_registry: dict,
) -> None:
    """xx-stage-complete 通用执行流程。"""
    feature_path = args.feature
    path, state = load_state(feature_path)

    # 1. current_stage 必须是本 stage
    if state.get("current_stage") != stage_spec.name:
        emit_json({
            "verdict": "FAIL",
            "stage": stage_spec.name,
            "phase": "complete",
            "error": f"current_stage={state.get('current_stage')!r} ≠ {stage_spec.name!r}",
            "hint": f"先跑 state.py {stage_spec.name}-start",
        }, exit_code=1)

    # 2. auto-commit 必检存在
    # cwd 用 feature_path 本身(让 git 自动向上找 .git · 不假设 parent 是 repo root)
    auto_commit = args.auto_commit
    feature_dir = Path(feature_path).resolve()
    git_cwd = str(feature_dir if feature_dir.is_dir() else feature_dir.parent)
    # --auto-commit 未传 → 默认取当前 HEAD(AI 标准流程:产物落盘 → git commit → xx-complete ·
    # HEAD 即本 stage 产出 commit · 治本"AI 漏传 --auto-commit"撞墙;artifacts-in-commit 校验仍兜底)
    if not auto_commit:
        auto_commit = git_head(cwd=git_cwd)
        if not auto_commit:
            emit_json({
                "verdict": "FAIL",
                "stage": stage_spec.name,
                "phase": "complete",
                "error": "--auto-commit 未传 · 且无法取 git HEAD(非 git repo?)",
                "hint": "在 git repo 内运行 · 或显式传 --auto-commit <hash>",
            }, exit_code=1)
    if not commit_exists(auto_commit, cwd=git_cwd):
        emit_json({
            "verdict": "FAIL",
            "stage": stage_spec.name,
            "phase": "complete",
            "error": f"auto-commit hash {auto_commit!r} 在 git history 中不存在(cwd={git_cwd})",
            "hint": "确认 git commit 已落库 · 或 hash 拼写正确 · 在 git repo 内运行",
        }, exit_code=1)

    # 3. 校验 artifacts
    artifacts_passed = []
    missing_artifacts = []
    commit_changeset = get_git_commit_changeset(
        auto_commit, cwd=git_cwd
    ) if auto_commit else []

    for art_spec in stage_spec.artifacts:
        if art_spec.path:
            target = feature_dir / art_spec.path
            if not target.exists():
                missing_artifacts.append({
                    "spec": art_spec.path,
                    "reason": "file not found",
                    "hint": f"创建 {art_spec.path}",
                })
                continue

            # frontmatter 校验
            if art_spec.frontmatter_required:
                fm = parse_frontmatter(target)
                if fm is None:
                    missing_artifacts.append({
                        "spec": art_spec.path,
                        "reason": "frontmatter parse failed",
                        "hint": "确保文件头部有 --- YAML frontmatter --- 块",
                    })
                    continue
                missing_fm = [k for k in art_spec.frontmatter_required if k not in fm]
                if missing_fm:
                    missing_artifacts.append({
                        "spec": art_spec.path,
                        "reason": f"frontmatter 缺字段: {missing_fm}",
                        "hint": f"补全 frontmatter 字段: {','.join(missing_fm)}",
                    })
                    continue

            # body 行数校验
            if art_spec.body_min_lines > 0:
                text = target.read_text(encoding="utf-8")
                body_lines = len(text.splitlines())
                if body_lines < art_spec.body_min_lines:
                    missing_artifacts.append({
                        "spec": art_spec.path,
                        "reason": f"body 行数 {body_lines} < {art_spec.body_min_lines}",
                        "hint": "扩充文档内容",
                    })
                    continue

            # commit 校验
            if art_spec.must_be_in_commit and commit_changeset:
                in_commit = any(art_spec.path in c for c in commit_changeset)
                if not in_commit:
                    missing_artifacts.append({
                        "spec": art_spec.path,
                        "reason": f"未在 commit {auto_commit} 内",
                        "hint": "把该文件加入 commit 或重新 commit",
                    })
                    continue

            artifacts_passed.append(art_spec.path)

        elif art_spec.glob:
            matches = list(feature_dir.glob(art_spec.glob))
            if len(matches) < art_spec.min_files:
                missing_artifacts.append({
                    "spec": art_spec.glob,
                    "reason": f"匹配 {len(matches)} 个 < min_files={art_spec.min_files}",
                    "hint": f"按 glob 模式产出至少 {art_spec.min_files} 个文件",
                })
                continue
            artifacts_passed.append(art_spec.glob)

    # 4. 校验 evidence
    failed_evidence = []
    for ev_check in stage_spec.evidence_checks:
        try:
            passed, err = ev_check.check_fn(state, args)
        except Exception as e:
            passed, err = False, f"check raised: {e}"
        if not passed:
            failed_evidence.append({
                "name": ev_check.name,
                "description": ev_check.description,
                "error": err,
            })

    # 5. bypass 处理
    issues = []
    if missing_artifacts:
        issues.extend(missing_artifacts)
    if failed_evidence:
        issues.extend(failed_evidence)

    if issues and args.bypass:
        require_user_confirmed(args)
        write_bypass_log(state, stage_spec.name, "complete", issues, args)
        issues = []
    elif issues:
        emit_json({
            "verdict": "FAIL",
            "stage": stage_spec.name,
            "phase": "complete",
            "missing_artifacts": missing_artifacts,
            "failed_evidence": failed_evidence,
            "hint": "按上述 hint 修复 · 重试本命令 · 重试 3 次仍 FAIL 给用户暂停点选 bypass",
        }, exit_code=1)

    # 6. 自动 satisfy 三 gate
    contracts = state.setdefault("stage_contracts", {})
    contract = contracts.setdefault(stage_spec.name, {})
    contract["input_satisfied"] = True
    contract["process_satisfied"] = True
    contract["output_satisfied"] = True
    contract["completed_at"] = now_iso()
    contract["auto_commit"] = auto_commit
    contract["artifacts"] = (args.artifacts or "").split(",") if args.artifacts else []
    contract["cited_specs"] = (args.cite or "").split(",") if args.cite else []

    # v8.28 · test stage --run-tests 物化跑测试(治本 F037 case-AI 自报 stdout 漏洞)
    # 必须在 evidence 写入之前 · 让自跑结果注入 args.integration_test_exit_code
    test_run_result = None
    if (stage_spec.name == "test" and getattr(args, "run_tests", False)):
        feature_id = state.get("feature_id") or feature_dir.name
        project_root = _find_project_root(feature_dir)
        cmd_str, source, timeout_sec, tail_lines, err = _resolve_test_cmd(
            args, feature_id, project_root)
        if err:
            emit_json({
                "verdict": "FAIL",
                "stage": "test",
                "phase": "complete",
                "error": f"--run-tests 但 {err}",
                "hint": "见 error 中的二选一",
                "rule": "v8.28 · test 验证物化 · 治本 F037 case-AI 自报 stdout 漏洞",
            }, exit_code=1)
        log_path = feature_dir / "test-stdout.log"
        # 在 git_cwd(repo)跑 · 不在 feature_dir(防 cargo test 找不到 Cargo.toml)
        test_run_result = run_tests_via_subprocess(
            cmd_str=cmd_str, cwd=git_cwd,
            timeout_sec=timeout_sec, log_path=log_path,
            tail_lines=tail_lines,
        )
        test_run_result["source"] = source
        # 自动注入 args(替代 PMO 自报 --integration-test-exit-code · 工具自跑权威)
        # 用 integration_test_exit_code 字段(test stage 默认 evidence 字段)
        # 若 cmd 实际跑的是 e2e · 用户可显式 --e2e-test-exit-code 覆盖
        args.integration_test_exit_code = test_run_result["exit_code"]

    # 6.5 持久化 stage 专属 args 到 contract.evidence(治本"PMO 必 raw-write 补 evidence")
    # 白名单字段(_add_stage_specific_args 中定义的 stage-complete 参数)
    evidence = contract.setdefault("evidence", {})
    _EVIDENCE_FIELDS = (
        "test_exit_code",            # dev
        "test_stdout",               # dev
        "integration_test_exit_code",  # test
        "e2e_test_exit_code",        # test
        "verdict",                   # review
        "external_review_files",     # review
        "decision",                  # pm_acceptance
        "note",                      # pm_acceptance
        "panorama_changed",          # ui_design(决定 panorama_sync 条件 stage 是否进入)
    )
    for field in _EVIDENCE_FIELDS:
        val = getattr(args, field, None)
        if val is None or val == "":
            continue
        evidence[field] = val

    # 6.6 stage 内 fix-retry 循环 · 维护 rounds[](review / test 等)
    if stage_spec.name in _STAGE_FIX_RETRY_CONFIG:
        cfg = _STAGE_FIX_RETRY_CONFIG[stage_spec.name]
        rounds = contract.setdefault("rounds", [])
        if not rounds:
            # 首次 complete · 创建 round 1
            rounds.append({
                "round": 1,
                "started_at": contract.get("started_at", now_iso()),
            })
        # 写当前 round 结果
        cur_round = rounds[-1]
        cur_round["completed_at"] = now_iso()
        cur_round[cfg["commit_field"]] = auto_commit
        # 写 stage 专属字段(从 args 拿)
        for key in cfg["round_init_fields"]:
            cur_round[key] = getattr(args, key, None)
        # review 专属:verdict
        if stage_spec.name == "review":
            cur_round["verdict"] = getattr(args, "verdict", None)

    # duration
    started = contract.get("started_at")
    if started:
        try:
            t0 = datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            t1 = datetime.strptime(contract["completed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            contract["duration_minutes"] = max(0, int((t1 - t0).total_seconds() // 60))
        except ValueError:
            pass

    # 7. 写 review-log
    write_review_log_entry(state, feature_dir, stage_spec.name, "completed", contract)

    # 8. 自动转移 / 暂停点
    transitioned_to = None
    next_brief = None
    next_stage_roles_audit = None

    if stage_spec.auto_transition_fn:
        next_stage = stage_spec.auto_transition_fn(state)

        if next_stage:
            # v8.0+P0-9:处理 --next-stage-roles 调整(若传)
            new_roles = getattr(args, "next_stage_roles", "") or ""
            new_roles_reason = getattr(args, "next_stage_roles_reason", "") or ""
            if new_roles:
                if not new_roles_reason:
                    emit_json({
                        "verdict": "FAIL",
                        "error": "--next-stage-roles 传时 · --next-stage-roles-reason 必传(audit)",
                    }, exit_code=1)
                roles_list = [r.strip() for r in new_roles.split(",") if r.strip()]
                invalid = [r for r in roles_list if r not in REVIEW_ROLE_ENUM]
                if invalid:
                    emit_json({
                        "verdict": "FAIL",
                        "error": f"--next-stage-roles 含非法角色: {invalid}",
                        "hint": f"REVIEW_ROLE_ENUM = {sorted(REVIEW_ROLE_ENUM)}",
                    }, exit_code=1)
                # 校验:next_stage 必须在 stage_review_roles 中(即有 review 配置)
                stage_review_roles = state.setdefault("stage_review_roles", {})
                if next_stage not in stage_review_roles:
                    emit_json({
                        "verdict": "FAIL",
                        "error": (
                            f"--next-stage-roles 试图调整 {next_stage!r} · "
                            f"但该 stage 默认无 review_roles 配置(flow_type 不适用)· "
                            f"调整无意义"
                        ),
                        "hint": "去掉 --next-stage-roles 让默认生效",
                    }, exit_code=1)
                # 写字段 + audit
                before = stage_review_roles.get(next_stage, [])[:]
                stage_review_roles[next_stage] = roles_list
                state.setdefault("stage_review_roles_adjustments", []).append({
                    "stage": next_stage,
                    "before": before,
                    "after": roles_list,
                    "reason": new_roles_reason,
                    "adjusted_at": now_iso(),
                    "adjusted_from_stage": stage_spec.name,
                })
                next_stage_roles_audit = {
                    "stage": next_stage,
                    "before": before,
                    "after": roles_list,
                    "reason": new_roles_reason,
                }

            # 自动进入下一 stage
            flow_type = state.get("flow_type")
            flow_graph = flow_by_type.get(flow_type, {})
            state["current_stage"] = next_stage
            state["legal_next_stages"] = flow_graph.get(next_stage, [])

            # 初始化下一 stage contract
            next_contract = contracts.setdefault(next_stage, {
                "input_satisfied": False,
                "process_satisfied": False,
                "output_satisfied": False,
            })
            next_contract.setdefault("started_at", now_iso())

            transitioned_to = next_stage

    # 加入 completed_stages(仅在真转移到下一 stage 时加 · 防 NEEDS_REVISION 误算完成)
    if transitioned_to is not None:
        completed = state.setdefault("completed_stages", [])
        if stage_spec.name not in completed:
            completed.append(stage_spec.name)
        # 渲染下一 stage brief(含建议评审角色)
        if next_stage in stage_specs_registry:
            next_spec = stage_specs_registry[next_stage]
            next_brief = next_spec.brief_template_fn(state)
            next_brief += _render_review_roles_suggestion(state, next_stage)

    # pm_acceptance rejected_with_feedback · 列回退选项暂停点(v8.10 + v8.11 jump-to-stage)
    pause_options_markdown = None
    if (stage_spec.name == "pm_acceptance"
            and transitioned_to is None
            and contract.get("evidence", {}).get("decision") == "rejected_with_feedback"):
        note = contract.get("evidence", {}).get("note", "")
        pause_options_markdown = (
            f"⏸️ pm_acceptance rejected_with_feedback · 反馈:\n  {note}\n\n"
            "请选回退方向(💡 推荐 1 · 最常见):\n"
            "  1. **代码 bug** → `state.py reset-prev --reason '...'` 退 dev "
            "→ dev 修 + review + test 完整重走\n"
            "  2. **AC / 需求改** → `state.py jump-to-stage --to goal --reason '...'` "
            "→ 改 PRD + 重 review\n"
            "  3. **UI 设计改** → `state.py jump-to-stage --to ui_design --reason '...'` "
            "→ 改 UI 设计\n"
            "  4. **放弃 Feature** → `state.py ship-phase --action close-unmerged "
            "--abandon=true`\n\n"
            "jump-to-stage / reset-prev 自动写 concerns WARN(audit 留痕)。"
        )

    # test/review 等 fix-retry stage · 失败时(transitioned_to=None)给提示
    fix_retry_hint = None
    if (stage_spec.name in _STAGE_FIX_RETRY_CONFIG
            and transitioned_to is None
            and stage_spec.name != "pm_acceptance"):
        fix_retry_hint = (
            f"⏸️ {stage_spec.name} 本轮未通过 · stage 内 fix-retry 循环:\n"
            f"  1. RD 修代码 + commit\n"
            f"  2. state.py {stage_spec.name}-fix --feature {args.feature} "
            "--auto-commit <hash> [--addresses-findings F1,F2]\n"
            f"  3. state.py {stage_spec.name}-retry --feature {args.feature}\n"
            f"  4. state.py {stage_spec.name}-complete ...(重新出 verdict / exit_code)"
        )

    # 物化检测:worktree 模式主工作区污染(治本宿主 patch 工具路径错落主 tree)
    pollution = detect_main_tree_pollution(feature_dir, state.get("feature_id", ""))
    if pollution:
        state.setdefault("concerns", []).append(
            f"[WARN] {stage_spec.name}-complete:主工作区检出 {len(pollution)} 个含 "
            f"Feature ID 的文件 · 疑似 patch/写工具路径错落主 tree(产物应在 worktree 内)· "
            f"复查并移到 worktree:{pollution[:5]}"
        )

    save_state(path, state)

    # status_line:基于已转移后的 state(当前 stage 已是 next_stage 或终态)
    next_hint = (
        f"按 brief 完成 → {transitioned_to}-complete" if transitioned_to
        else (f"走 {stage_spec.name}-fix → {stage_spec.name}-retry"
              if fix_retry_hint else "stage 链结束 / 等用户拍板下一步")
    )
    rw_audit = compute_raw_write_audit(state)
    # v8.14:转到 next_stage 时同步给 next_stage 的 scaffold_hints
    # AI complete 当前 stage 时就拿到下个 stage 的模板地图 · 不用再绕回 stage-start emit
    next_stage_scaffold_hints = (
        build_scaffold_hints(transitioned_to) if transitioned_to else None
    )
    emit_json({
        "verdict": "PASS",
        "stage": stage_spec.name,
        "phase": "complete",
        "completed_at": contract["completed_at"],
        "duration_minutes": contract.get("duration_minutes", 0),
        "satisfied_gates": ["input_satisfied", "process_satisfied", "output_satisfied"],
        "transitioned_to": transitioned_to,
        "next_stage_brief": next_brief,
        "status_line": render_status_line(state, next_hint),
        # v8.28 · test --run-tests 透明 emit(主 PMO context 仅 tail · 完整 log 落 log_path)
        **({"test_run_result": test_run_result} if test_run_result else {}),
        **({"next_stage_scaffold_hints": next_stage_scaffold_hints}
           if next_stage_scaffold_hints else {}),
        **({"next_stage_roles_adjusted": next_stage_roles_audit} if next_stage_roles_audit else {}),
        **({"pause_options_markdown": pause_options_markdown} if pause_options_markdown else {}),
        **({"fix_retry_hint": fix_retry_hint} if fix_retry_hint else {}),
        **({"raw_write_audit": rw_audit} if rw_audit else {}),
        **({"main_tree_pollution": {
            "count": len(pollution),
            "files": pollution[:10],
            "hint": "这些含 Feature ID 的文件落在主工作区(非 worktree)· "
                    "疑 patch 工具路径错 · 复查并 git mv 到 worktree 内对应路径",
        }} if pollution else {}),
    })


# ─── review-log 写入 ───────────────────────────────────────────────────


def write_review_log_entry(
    state: dict,
    feature_dir: Path,
    stage: str,
    event: str,
    contract: dict,
) -> None:
    """追加一条 review-log.jsonl 记录(v8 自动写)。"""
    log_path = feature_dir / "review-log.jsonl"
    entry = {
        "at": now_iso(),
        "event": f"stage_{event}",
        "stage": stage,
        "auto_commit": contract.get("auto_commit"),
        "duration_minutes": contract.get("duration_minutes"),
        "artifacts": contract.get("artifacts", []),
    }
    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # log 失败不阻塞主流程


# ─── argparse 帮助 ─────────────────────────────────────────────────────


def add_common_stage_start_args(parser: argparse.ArgumentParser) -> None:
    """所有 xx-stage-start 共用的参数。"""
    parser.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    parser.add_argument("--bypass", action="store_true",
                        help="逃生 · 跳过未满足前置 · 必须配合 --reason --user-confirmed --missing")
    parser.add_argument("--reason", default="", help="bypass 时必填 · 进 concerns WARN")
    parser.add_argument("--user-confirmed", action="store_true",
                        help="bypass 时必带 · 标记用户已确认逃生(防 AI 自决)")
    parser.add_argument("--missing", default="",
                        help="bypass 时必带 · 逗号分隔 · 明确跳过哪些前置 ID")
    # v8.36:host 校准(治本 SVC-PLATFORM-F054 case · 切 session 不感知)
    # 用户跨 session 切换宿主时 · 在 stage-start 显式覆盖 state.json.host · 不一致 → WARN 留痕
    parser.add_argument("--host",
                        choices=["claude-code", "codex-cli", "gemini-cli"],
                        help="[v8.36] 主对话宿主 · 校准 state.json.host(治本 v8.21 "
                             "全局 audit 跨 session 污染 case)· 不一致 → 更新 + concerns WARN")


def add_common_stage_complete_args(parser: argparse.ArgumentParser) -> None:
    """所有 xx-stage-complete 共用的参数。"""
    parser.add_argument("--feature", required=True, help="Feature artifact_root 路径")
    parser.add_argument("--auto-commit", default="",
                        help="本 stage 产出的 git commit hash · 不传则默认取当前 git HEAD")
    parser.add_argument("--artifacts", default="", help="逗号分隔 · 本 stage 实际产出文件")
    parser.add_argument("--cite", default="", help="逗号分隔 · AI 声明读了哪些 spec")
    parser.add_argument("--bypass", action="store_true", help="逃生 · 跳过 artifact/evidence 校验")
    parser.add_argument("--reason", default="", help="bypass 时必填")
    parser.add_argument("--user-confirmed", action="store_true",
                        help="bypass 时必带 · 标记用户已确认逃生")
    parser.add_argument("--missing", default="", help="bypass 时必带 · 逗号分隔")
    # v8.0+P0-9:调整下一 stage review 角色(可选 · 不传用默认矩阵)
    parser.add_argument(
        "--next-stage-roles",
        default="",
        help=(
            "可选 · 调整下一 stage 的 review 角色(逗号分隔)· "
            "覆盖默认矩阵 · 必须是 REVIEW_ROLE_ENUM 子集 · "
            "若传此参数 · --next-stage-roles-reason 必传"
        ),
    )
    parser.add_argument(
        "--next-stage-roles-reason",
        default="",
        help="--next-stage-roles 传时必填 · 调整理由 · 写入 audit",
    )


# ─── stage 专属参数 hook ────────────────────────────────────────────


def _add_stage_specific_args(parser: argparse.ArgumentParser, stage_name: str, phase: str) -> None:
    """各 stage 特殊参数 hook · 在通用参数之外追加。"""
    if stage_name == "goal" and phase == "complete":
        # v8.0+P0-6:--needs-ui 必传 · 决策下一 stage 走向(ui_design vs blueprint)
        # 不让 state.py emit 暂停点(默认无 UI 是常态)· 字段必有值
        parser.add_argument(
            "--needs-ui",
            choices=["true", "false"],
            required=True,
            help=(
                "是否需要独立 UI Design Stage · "
                "true → 下一 stage=ui_design / false → blueprint。"
                "敏捷需求/Planning 必传 false(若 true 应升级 Feature 流程)"
            ),
        )
    elif stage_name == "ui_design" and phase == "complete":
        # v8.x:--panorama-changed 必传 · 决定下一 stage 是否 panorama_sync(条件 stage)
        # 治本:panorama 同步原埋在 ui_design step 4 隐式动作 · 拆出后由本字段决策
        parser.add_argument(
            "--panorama-changed",
            choices=["true", "false"],
            required=True,
            help=(
                "本 Feature UI 改动是否影响 workspace 级 panorama(sitemap/overview/IA):"
                "true → 下一 stage=panorama_sync(更新 panorama 单源 + 跨 Feature 评审)/ "
                "false → 下一 stage=blueprint"
            ),
        )
    elif stage_name == "dev" and phase == "complete":
        parser.add_argument("--test-stdout", default="",
                            help="测试 stdout(文件路径或字符串)· 必须非空")
        parser.add_argument("--test-exit-code", type=int, default=None,
                            help="测试 exit code · 必须 = 0")
    elif stage_name == "review" and phase == "complete":
        parser.add_argument("--verdict", choices=["APPROVE", "NEEDS_REVISION"],
                            required=True, help="评审结论")
        parser.add_argument("--external-review-files", default="",
                            help="逗号分隔 · 外部评审 markdown 文件清单")
    elif stage_name == "test" and phase == "complete":
        parser.add_argument("--integration-test-exit-code", type=int, default=None,
                            help="[deprecated] 集成测试 exit code · v8.28 推荐 --run-tests 工具自跑")
        parser.add_argument("--e2e-test-exit-code", type=int, default=None,
                            help="[deprecated] API E2E exit code · v8.28 推荐 --run-tests 工具自跑")
        # v8.28:test 验证物化(治本 F037 case-AI 自报 stdout 漏洞 · 不污染主 context)
        parser.add_argument("--run-tests", action="store_true",
                            help=("[v8.28] 工具自 subprocess 跑测试 · capture exit_code · "
                                  "log 落 <feature_dir>/test-stdout.log(不污染主 context)· "
                                  "读 .teamwork_localconfig.json test_commands · "
                                  "AI 不能伪造 stdout · 不能借 'context 不够' 跳"))
        parser.add_argument("--test-cmd", default=None,
                            help=("[v8.28] 覆盖 config 中 test_commands · "
                                  "如 'cargo test --test f037_quality_gate_framework' · "
                                  "缺省读 .teamwork_localconfig.json test_commands.default 或 by_feature_id_pattern"))
    elif stage_name == "pm_acceptance" and phase == "complete":
        parser.add_argument(
            "--decision",
            choices=["approved_and_ship", "approved_no_ship", "rejected_with_feedback"],
            required=True,
            help="PM 验收决策",
        )
        parser.add_argument("--note", default="",
                            help="决策说明(rejected 时必填)")


# ─── v8.28 · test 验证物化(治本 F037 case · AI 自报 stdout 漏洞)─────────
#
# 设计:
# - state.py test-complete --run-tests · subprocess.run 跑测试 · capture exit_code
# - 完整 log 落盘 <feature_dir>/test-stdout.log(不进主 PMO context)
# - emit 仅 tail N 行 + exit_code + duration(主 context 几行 · 不污染)
# - 自动设 evidence(integration_test_exit_code / e2e_test_exit_code)
# - AI 不能伪造 stdout · 不能借 "context 不够" 跳
# - 为未来动态模型扩展留接口(类似 v8.20 external-review host→model 映射)
#
# config 优先级:--test-cmd > by_feature_id_pattern > default · 都无 → BLOCK

TEST_RUN_DEFAULT_TIMEOUT_SEC = 1800   # 30 min · 适合大型项目集成测试
TEST_RUN_DEFAULT_TAIL_LINES = 100     # emit tail · 平衡可读性 vs context 占用


def _resolve_test_cmd(args, feature_id: str, project_root: Path) -> tuple:
    """v8.28 · 按优先级选 test cmd · 返 (cmd_str, source, timeout_sec, tail_lines, error)。

    优先级:--test-cmd > config.by_feature_id_pattern > config.default
    都无 → (None, None, _, _, error_msg)
    """
    import fnmatch
    # 用 bootstrap 的 read_localconfig(避免循环 import · 这里复用)
    try:
        cfg_path = project_root / ".teamwork_localconfig.json"
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        else:
            cfg = {}
    except (OSError, json.JSONDecodeError):
        cfg = {}

    test_cfg = cfg.get("test_commands") or {}
    timeout_sec = cfg.get("test_timeout_sec") or TEST_RUN_DEFAULT_TIMEOUT_SEC
    tail_lines = cfg.get("test_log_tail_lines") or TEST_RUN_DEFAULT_TAIL_LINES

    # 1. --test-cmd 最优先
    cmd = getattr(args, "test_cmd", None)
    if cmd:
        return cmd, "args.test_cmd", timeout_sec, tail_lines, None

    # 2. by_feature_id_pattern(fnmatch)
    by_pattern = test_cfg.get("by_feature_id_pattern") or {}
    for pattern, c in by_pattern.items():
        if fnmatch.fnmatch(feature_id, pattern):
            return c, f"config.by_feature_id_pattern[{pattern}]", timeout_sec, tail_lines, None

    # 3. default
    if test_cfg.get("default"):
        return test_cfg["default"], "config.default", timeout_sec, tail_lines, None

    # 都无 · BLOCK
    return None, None, timeout_sec, tail_lines, (
        "无 test cmd · 二选一:\n"
        "  ① 项目根 .teamwork_localconfig.json 加 test_commands.default(推荐 · 一次配)\n"
        "       例:{\"test_commands\": {\"default\": \"cargo test --test '*'\"}}\n"
        "       支持 by_feature_id_pattern(fnmatch · 如 'SVC-CORE-F037-*' 覆盖)\n"
        "  ② 命令行 --test-cmd '...' 显式传(一次性)\n"
        "  ③ 临时回退 --integration-test-exit-code N(deprecated · 不推荐 · AI 自报)"
    )


def run_tests_via_subprocess(cmd_str: str, cwd: str, timeout_sec: int,
                              log_path: Path, tail_lines: int) -> dict:
    """v8.28 · 工具自跑测试 · 完整 log 落盘 · 返 tail + exit_code + duration。

    返 dict:
      - exit_code: int(0 = pass · 非 0 = fail)
      - stdout_tail: str(末 tail_lines 行 · 主 context 显)
      - stdout_total_lines: int
      - duration_sec: float
      - log_path: str(完整 log 落盘 · 主 PMO 可主动 read · 默认不读)
      - cmd: str(实际跑的 cmd)
      - timeout: bool(是否超时)
    """
    import time
    start = time.time()
    timed_out = False
    try:
        # subprocess.run 用 shell=True 支持 cmd 含 pipe / glob 等(便利)
        # capture stderr 也合并到 log(测试常 stderr 输出 PASS/FAIL 摘要)
        r = subprocess.run(
            cmd_str, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=timeout_sec,
        )
        exit_code = r.returncode
        full_stdout = r.stdout or ""
        full_stderr = r.stderr or ""
    except subprocess.TimeoutExpired as e:
        timed_out = True
        exit_code = 124
        full_stdout = (e.stdout or "").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        full_stderr = (e.stderr or "").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        full_stderr += f"\n\n[teamwork timeout {timeout_sec}s]"
    except (FileNotFoundError, OSError) as ex:
        exit_code = 127
        full_stdout = ""
        full_stderr = f"[teamwork test runner error] {ex}"

    duration = time.time() - start

    # 落完整 log(主 PMO 默认不 read · 想看主动 cat / Read)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        full_log = (
            f"=== teamwork test runner v8.28 ===\n"
            f"cmd: {cmd_str}\n"
            f"cwd: {cwd}\n"
            f"timeout_sec: {timeout_sec}\n"
            f"exit_code: {exit_code}\n"
            f"duration_sec: {duration:.2f}\n"
            f"timed_out: {timed_out}\n"
            f"\n=== stdout ===\n{full_stdout}\n"
            f"\n=== stderr ===\n{full_stderr}\n"
        )
        log_path.write_text(full_log, encoding="utf-8")
    except OSError:
        pass  # log 写失败不致命 · emit tail 仍 work

    # tail(末 N 行 · 用 stdout 优先 · 失败 fallback stderr)
    src = full_stdout if full_stdout.strip() else full_stderr
    lines = src.splitlines()
    tail = "\n".join(lines[-tail_lines:]) if lines else ""

    return {
        "exit_code": exit_code,
        "stdout_tail": tail,
        "stdout_total_lines": len(lines),
        "duration_sec": round(duration, 2),
        "log_path": str(log_path),
        "cmd": cmd_str,
        "timeout": timed_out,
    }


# ─── stage 内 fix-retry 循环(通用 · review/test 复用 · 治本回退切 stage)──


# stage 专属配置 · 加新 stage 在此扩 dict 即可
_STAGE_FIX_RETRY_CONFIG = {
    "review": {
        "commit_field": "review_commit",
        "is_failed_round": lambda r: r.get("verdict") == "NEEDS_REVISION",
        "evidence_keys_to_clear": ["verdict"],
        "round_init_fields": {"verdict": None},
        "complete_command_template": (
            "state.py review-complete --feature {feature} --auto-commit <REVIEW.md commit> "
            "--artifacts REVIEW.md,REVIEW-arch.md,REVIEW-qa.md "
            "--verdict {{APPROVE|NEEDS_REVISION}}"
        ),
        "retry_action_hint": "重新做评审(architect/qa/external)· 完成后:",
    },
    "test": {
        "commit_field": "test_commit",
        "is_failed_round": lambda r: (
            (r.get("integration_test_exit_code") not in (None, 0))
            or (r.get("e2e_test_exit_code") not in (None, 0))
        ),
        "evidence_keys_to_clear": ["integration_test_exit_code", "e2e_test_exit_code"],
        "round_init_fields": {
            "integration_test_exit_code": None,
            "e2e_test_exit_code": None,
        },
        "complete_command_template": (
            "state.py test-complete --feature {feature} --auto-commit <hash> "
            "--artifacts TEST-REPORT.md,e2e/ "
            "--integration-test-exit-code 0 --e2e-test-exit-code 0"
        ),
        "retry_action_hint": "重新跑 integration test + API E2E · 完成后:",
    },
}


def execute_stage_fix(stage_name: str, args: argparse.Namespace) -> None:
    """stage 内 fix:RD 修复 + 记录 fix commit 到 rounds[-1]。"""
    if stage_name not in _STAGE_FIX_RETRY_CONFIG:
        emit_json({
            "verdict": "FAIL",
            "error": f"stage {stage_name!r} 不支持 fix-retry · 仅 {list(_STAGE_FIX_RETRY_CONFIG)}",
        }, exit_code=1)

    cfg = _STAGE_FIX_RETRY_CONFIG[stage_name]
    path, state = load_state(args.feature)

    if state.get("current_stage") != stage_name:
        emit_json({
            "verdict": "FAIL",
            "stage": stage_name,
            "action": "fix",
            "error": f"current_stage={state.get('current_stage')!r} ≠ {stage_name!r}",
            "hint": f"{stage_name}-fix 仅在 {stage_name}-stage 内可用",
        }, exit_code=1)

    contract = state.setdefault("stage_contracts", {}).setdefault(stage_name, {})
    rounds = contract.setdefault("rounds", [])
    if not rounds:
        emit_json({
            "verdict": "FAIL",
            "stage": stage_name,
            "action": "fix",
            "error": f"{stage_name}.rounds[] 为空 · 必先跑 {stage_name}-complete(失败一轮)",
        }, exit_code=1)

    last_round = rounds[-1]
    if not cfg["is_failed_round"](last_round):
        emit_json({
            "verdict": "FAIL",
            "stage": stage_name,
            "action": "fix",
            "error": f"rounds[-1] 不在失败状态 · 无需 fix",
            "last_round": last_round,
        }, exit_code=1)
    if last_round.get("fix_commit"):
        emit_json({
            "verdict": "FAIL",
            "stage": stage_name,
            "action": "fix",
            "error": (
                f"rounds[-1].fix_commit={last_round['fix_commit']} 已记录 · "
                f"跑 {stage_name}-retry 进入下一轮"
            ),
        }, exit_code=1)

    feature_dir = Path(args.feature).resolve()
    git_cwd = str(feature_dir if feature_dir.is_dir() else feature_dir.parent)
    if not commit_exists(args.auto_commit, cwd=git_cwd):
        emit_json({
            "verdict": "FAIL",
            "stage": stage_name,
            "action": "fix",
            "error": f"auto-commit hash {args.auto_commit!r} 在 git history 中不存在",
            "hint": "确认 git commit 已落库 · 或 hash 拼写正确",
        }, exit_code=1)

    last_round["fix_commit"] = args.auto_commit
    last_round["fix_at"] = now_iso()
    if getattr(args, "addresses_findings", None):
        last_round["addresses_findings"] = [
            s.strip() for s in args.addresses_findings.split(",") if s.strip()
        ]

    save_state(path, state)

    emit_json({
        "verdict": "PASS",
        "stage": stage_name,
        "action": "fix",
        "round": last_round.get("round", len(rounds)),
        "fix_commit": args.auto_commit,
        "addresses_findings": last_round.get("addresses_findings", []),
        "next_action_brief": (
            "✅ fix 已记录。\n"
            f"下一步:state.py {stage_name}-retry --feature {args.feature}\n"
            f"(重新进入 {stage_name} 循环 · 重置 contract gates · 加新 round)"
        ),
    })


def execute_stage_retry(stage_name: str, args: argparse.Namespace) -> None:
    """stage 内 retry:fix 后开新一轮 · 重置 contract gates · 加新 round。"""
    if stage_name not in _STAGE_FIX_RETRY_CONFIG:
        emit_json({
            "verdict": "FAIL",
            "error": f"stage {stage_name!r} 不支持 fix-retry · 仅 {list(_STAGE_FIX_RETRY_CONFIG)}",
        }, exit_code=1)

    cfg = _STAGE_FIX_RETRY_CONFIG[stage_name]
    path, state = load_state(args.feature)

    if state.get("current_stage") != stage_name:
        emit_json({
            "verdict": "FAIL",
            "stage": stage_name,
            "action": "retry",
            "error": f"current_stage={state.get('current_stage')!r} ≠ {stage_name!r}",
        }, exit_code=1)

    contract = state.setdefault("stage_contracts", {}).setdefault(stage_name, {})
    rounds = contract.setdefault("rounds", [])
    if not rounds:
        emit_json({
            "verdict": "FAIL",
            "stage": stage_name,
            "action": "retry",
            "error": (
                f"{stage_name}.rounds[] 为空 · "
                f"必先跑 {stage_name}-complete(失败一轮)+ {stage_name}-fix"
            ),
        }, exit_code=1)

    last_round = rounds[-1]
    if not last_round.get("fix_commit"):
        emit_json({
            "verdict": "FAIL",
            "stage": stage_name,
            "action": "retry",
            "error": f"rounds[-1].fix_commit 为空 · 先跑 {stage_name}-fix --auto-commit <hash>",
        }, exit_code=1)

    new_round_num = len(rounds) + 1
    new_round = {
        "round": new_round_num,
        cfg["commit_field"]: None,
        "fix_commit": None,
        "started_at": now_iso(),
        **cfg["round_init_fields"],
    }
    rounds.append(new_round)

    contract["input_satisfied"] = False
    contract["process_satisfied"] = False
    contract["output_satisfied"] = False
    contract.pop("completed_at", None)
    contract.pop("duration_minutes", None)
    ev = contract.setdefault("evidence", {})
    for k in cfg["evidence_keys_to_clear"]:
        ev.pop(k, None)

    save_state(path, state)

    # 渲染 stage brief 重新引导
    from _v8_stage_specs import STAGE_SPECS
    spec = STAGE_SPECS.get(stage_name)
    next_brief = spec.brief_template_fn(state) if spec else ""

    complete_cmd = cfg["complete_command_template"].format(feature=args.feature)

    emit_json({
        "verdict": "PASS",
        "stage": stage_name,
        "action": "retry",
        "round": new_round_num,
        "next_action_brief": (
            f"✅ {stage_name} round {new_round_num} 已开启。\n"
            f"{cfg['retry_action_hint']}\n"
            f"  {complete_cmd}"
        ),
        "next_stage_brief": next_brief,
    })


# ─── register_v8_subparsers ────────────────────────────────────────────


def register_v8_subparsers(
    sub,
    stage_specs_registry: dict,
    flow_by_type: dict,
) -> None:
    """在 state.py 的 argparse subparsers 上注册 v8 命令。

    为 STAGE_SPECS 中每个 stage 注册 -start / -complete 子命令。

    Args:
        sub: argparse subparsers 对象(state.py build_parser 内)
        stage_specs_registry: STAGE_SPECS dict
        flow_by_type: FLOW_BY_TYPE dict(来自 state.py 常量)
    """
    for stage_name, stage_spec in stage_specs_registry.items():
        # xx-start
        start_parser = sub.add_parser(
            f"{stage_name}-start",
            help=f"[v8] {stage_name} stage 入口校验 + 渲染 next_action_brief",
        )
        add_common_stage_start_args(start_parser)
        _add_stage_specific_args(start_parser, stage_name, "start")

        # 闭包绑定 stage_spec
        def make_start_handler(spec):
            def handler(args):
                execute_stage_start(spec, args, {}, flow_by_type)

            return handler

        start_parser.set_defaults(func=make_start_handler(stage_spec))

        # xx-complete
        complete_parser = sub.add_parser(
            f"{stage_name}-complete",
            help=f"[v8] {stage_name} stage 产物校验 + 自动转移到下一 stage",
        )
        add_common_stage_complete_args(complete_parser)
        _add_stage_specific_args(complete_parser, stage_name, "complete")

        def make_complete_handler(spec):
            def handler(args):
                execute_stage_complete(spec, args, {}, flow_by_type, stage_specs_registry)

            return handler

        complete_parser.set_defaults(func=make_complete_handler(stage_spec))

    # stage 内 fix-retry 循环(review/test 等 · 治本回退切 stage 噪音)
    for stage_name in _STAGE_FIX_RETRY_CONFIG:
        if stage_name not in stage_specs_registry:
            continue

        # closure 绑定 stage_name
        def make_fix_handler(name):
            def handler(args):
                execute_stage_fix(name, args)
            return handler

        def make_retry_handler(name):
            def handler(args):
                execute_stage_retry(name, args)
            return handler

        fix_parser = sub.add_parser(
            f"{stage_name}-fix",
            help=f"[v8] {stage_name}-stage 内 fix · 记录 fix commit 到 rounds[-1]",
        )
        fix_parser.add_argument("--feature", required=True, help="Feature artifact_root")
        fix_parser.add_argument("--auto-commit", required=True, help="fix commit hash")
        fix_parser.add_argument(
            "--addresses-findings", default="",
            help="逗号分隔 · 本次 fix 解决的 finding ID(audit · 可选)",
        )
        fix_parser.set_defaults(func=make_fix_handler(stage_name))

        retry_parser = sub.add_parser(
            f"{stage_name}-retry",
            help=f"[v8] {stage_name}-stage fix 后重新跑一轮 · 加新 round + 重置 contract gates",
        )
        retry_parser.add_argument("--feature", required=True, help="Feature artifact_root")
        retry_parser.set_defaults(func=make_retry_handler(stage_name))
