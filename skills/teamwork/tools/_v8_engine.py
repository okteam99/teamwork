"""
_v8_engine.py — Teamwork v8.0 stage orchestration engine.

v8.0 范式:state.py 主动校验 + 主动告知,AI 不读 spec markdown,跑命令即知做什么。

本模块提供:
- StageSpec / StagePrerequisite / StageArtifactSpec / StageEvidenceCheck 数据类
- execute_stage_start / execute_stage_complete 通用引擎
- bypass 协议(--bypass --reason --user-confirmed --missing)
- next_action_brief 渲染

各 stage 具体 spec 定义见 _v8_stage_specs.py。

设计哲学:v8.0 设计稿已清理(git 历史可溯)。
命令 schema 现行权威 = state.py --help + _v8_stage_specs.py
(v8.0 命令 schema 快照已清理 · git 历史可溯)。
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

    review_artifact: bool = False
    """v8.260:评审类产物标记 —— state.fast_mode=true 时跳过校验(fast mode 去掉所有评审环节)"""

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


def _worktree_physically_exists(wt_path: str, cwd: Optional[str] = None) -> bool:
    """检查 wt_path 是否在 `git worktree list` 输出内。

    cwd 传 feature 目录(state.json 所在仓)· 保证查询的是该仓的 worktree 清单 ·
    不受调用进程 cwd 恰好落在别的仓影响。
    """
    if not wt_path:
        return False
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True, text=True, timeout=10, cwd=cwd,
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
        # v8.x:机读契约优先读 <!-- TEAMWORK-MACHINE ... --> 注释块(预览隐藏 · 所有渲染器都不显)·
        # 兜底文件头 --- frontmatter(旧 PRD / 其他产物 TC/REVIEW 仍用 frontmatter)。
        fm_text = None
        _ms = "<!-- TEAMWORK-MACHINE"
        if text.startswith(_ms):                               # 仅行首 marker(防正文 prose 里字面引用误命中)
            marker = 0
        else:
            _i = text.find("\n" + _ms)
            marker = _i + 1 if _i != -1 else -1
        if marker != -1:
            nl = text.find("\n", marker)                       # 跳过 marker 行(可带说明)
            close = text.find("\n-->", nl) if nl != -1 else -1
            if nl != -1 and close != -1:
                fm_text = text[nl + 1:close]
        if fm_text is None:
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


def require_user_confirmed(args: argparse.Namespace, yolo: bool = False) -> None:
    """逃生时强制要求 --user-confirmed flag · 缺则拦截。

    v8.64:yolo 模式 = 用户已 blanket 委托(init-feature --yolo · 见 SKILL.md § yolo)→
    视作已 confirmed · 不再拦人工确认 —— 实现 yolo「AI 自主解决所有问题 · 零人工干预」核心目标。
    🔴 但 yolo 优先级是「**解决 > 绕过**」:bypass 只是穷尽自主解决(更多轮 / 换思路 / 深挖根因)
    后的兜底 · 不是遇错就推。每次 bypass 仍 write_bypass_log + concerns WARN 留痕(详 SKILL.md § yolo 自主解决)。
    """
    if getattr(args, "user_confirmed", False) or yolo:
        return
    emit_json({
        "verdict": "FAIL",
        "error": "--bypass requires --user-confirmed flag(防 AI 自决逃生)",
        "hint": (
            "暂停点询问用户 · 用户明确确认后再调用此命令 · "
            "并加 --user-confirmed flag。"
            "审计时若发现 AI 自加此 flag 而对话历史无用户确认 = 红线违规。"
            "(yolo 模式例外:--yolo 即用户 blanket 委托 · 无需 --user-confirmed · 见 SKILL.md § yolo)"
        ),
    }, exit_code=1)


def require_bypass_reason(args: argparse.Namespace) -> None:
    """bypass 必带非空 --reason(concerns WARN / bypass_log 的 audit 依据)· 空白串同缺失。"""
    if (getattr(args, "reason", "") or "").strip():
        return
    emit_json({
        "verdict": "FAIL",
        "error": "--bypass 必带非空 --reason(空串/空白不算)",
        "hint": "补 --reason '<为什么必须逃生>' · 该理由写入 bypass_log + concerns WARN(audit 单源)",
    }, exit_code=1)


def _issue_label(m) -> str:
    """bypass 条目标识:prerequisite 用 id · artifact 用 spec · evidence 用 name。"""
    if isinstance(m, dict):
        return str(m.get("id") or m.get("spec") or m.get("name") or "unknown")
    return str(m)


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
        "missing": [_issue_label(m) for m in missing],
        "reason": args.reason,
        "user_confirmed": True,
        "retry_count_before_bypass": retry_count,
        "concerns_id": ts,
    })
    # 同步写 concerns WARN
    state.setdefault("concerns", []).append(
        f"{ts} WARN {stage}-{phase} bypass · "
        f"missing={','.join(_issue_label(m) for m in missing)} · reason: {args.reason}"
    )
    return ts


# ─── 通用引擎 ──────────────────────────────────────────────────────────



def close_open_pause(state: dict) -> None:
    """v8.192:闭合 open_pause · 把等待墙钟累计进该 stage 的 await_minutes(计时排毒)。

    治本:stage 内 R5 暂停(PRD 确认/预览确认/DB 确认)的等用户墙钟全算成「工作」·
    goal 均值 157m vs 中位 22m(max 128h)· 每次耗时归因都要人肉排毒。
    打点:AI emit 暂停点时跑 `state.py pause-mark` 写 open_pause;本函数在下一个流程
    命令(start/complete/fix/retry)自动闭合 —— resume 侧零纪律要求。
    """
    op = state.get("open_pause")
    if not isinstance(op, dict) or not op.get("started_at"):
        return
    try:
        t0 = datetime.fromisoformat(op["started_at"].replace("Z", "+00:00"))
        mins = max(0, int((datetime.now(timezone.utc) - t0).total_seconds() // 60))
    except (ValueError, TypeError):
        mins = 0
    stage = op.get("stage") or state.get("current_stage") or ""
    if stage and mins:
        c = state.setdefault("stage_contracts", {}).setdefault(stage, {})
        c["await_minutes"] = int(c.get("await_minutes") or 0) + mins
    state.pop("open_pause", None)


# ─── v8.276:活动时间戳挖掘 —— 从墙钟 span 里扣跨 session 空闲 ──────────────
# 治本:duration = completed_at − started_at 是纯墙钟;AI 干活期间 state.py 不被调用
# (dev 只有 start/complete 两次打点)· 中途合上电脑过夜 = 不是 R5 暂停 · pause-mark 抓不到
# → 整段空闲被算成「AI 自主」(实证 aon-core goal 1012m / await +3m · 起草完过夜次日才 complete)。
# 信号:干活其实留了时间戳痕迹 —— git commit(committer-date)+ 产物 mtime(PRD/TECH/REVIEW/
# dispatch_log)。取 stage 窗口 [started, completed] 内所有活动时间戳排序 · 相邻间隔 ≤ 阈值
# (默认 30m · localconfig idle_threshold_minutes 可调)累加为 active_minutes · 间隔 > 阈值判空闲扣除。
# 🔴 best-effort:任何异常 / 窗口内无中间活动信号 → 返 None(回退 duration−await · 不硬伤)。
DEFAULT_IDLE_THRESHOLD_MINUTES = 30


def _parse_iso_flexible(s):
    """宽松解析 ISO 时间戳 → aware datetime(UTC)· 失败返 None。

    治 P3:duration 曾用严格 strptime("%Y-%m-%dT%H:%M:%SZ") + except pass · 格式变体
    (小数秒 / 偏移量)静默丢 duration → 该 stage 从计时消失。与 close_open_pause 口径统一。
    """
    if not isinstance(s, str) or not s.strip():
        return None
    try:
        dt = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _idle_threshold_minutes(feature_dir) -> int:
    """localconfig `idle_threshold_minutes`(默认 30 · 向上找 .git 边界)· 非法值→默认。"""
    try:
        node = Path(feature_dir).resolve()
    except (TypeError, OSError):
        return DEFAULT_IDLE_THRESHOLD_MINUTES
    for d in [node, *node.parents]:
        cfg = d / ".teamwork_localconfig.json"
        if cfg.exists():
            try:
                v = json.loads(cfg.read_text(encoding="utf-8")).get("idle_threshold_minutes")
            except (OSError, ValueError):
                return DEFAULT_IDLE_THRESHOLD_MINUTES
            if isinstance(v, (int, float)) and not isinstance(v, bool) and int(v) >= 1:
                return int(v)
            return DEFAULT_IDLE_THRESHOLD_MINUTES
        if (d / ".git").exists():
            break
    return DEFAULT_IDLE_THRESHOLD_MINUTES


def _git_commit_times(feature_dir, t0, t1) -> set:
    """stage 窗口内 git commit 的 committer-date(活动信号 · dev/TDD 高密度打点)。"""
    stamps = set()
    try:
        r = subprocess.run(
            ["git", "-C", str(feature_dir), "log",
             f"--since={t0.isoformat()}", f"--until={t1.isoformat()}",
             "--format=%cI", "-n", "500"],
            capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                dt = _parse_iso_flexible(line.strip())
                if dt and t0 <= dt <= t1:
                    stamps.add(dt)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return stamps


def _artifact_activity_mtimes(feature_dir, t0, t1) -> set:
    """stage 窗口内 feature 产物 mtime(PRD/TECH/REVIEW/dispatch_log 等 · 无 commit 的起草也留痕)。"""
    stamps = set()
    try:
        root = Path(feature_dir)
        if not root.is_dir():
            return stamps
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in (".md", ".log", ".json", ".yaml", ".yml"):
                continue
            try:
                dt = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            except (OSError, ValueError, OverflowError):
                continue
            if t0 <= dt <= t1:
                stamps.add(dt)
    except (OSError, ValueError):
        pass
    return stamps


def _mine_active_minutes(feature_dir, started_iso, completed_iso, contract) -> "int | None":
    """活动时间戳挖掘:窗口内 git commit + 产物 mtime + round 边界 · 相邻间隔 ≤ 阈值累加。

    返 active_minutes(已排跨 session / 未标记空闲);无中间活动信号或异常 → None(回退墙钟)。
    """
    t0 = _parse_iso_flexible(started_iso)
    t1 = _parse_iso_flexible(completed_iso)
    if not t0 or not t1 or t1 <= t0:
        return None
    threshold = _idle_threshold_minutes(feature_dir)
    intermediate = set()
    for rnd in contract.get("rounds", []) or []:
        if isinstance(rnd, dict):
            for k in ("started_at", "completed_at"):
                dt = _parse_iso_flexible(rnd.get(k))
                if dt and t0 < dt < t1:
                    intermediate.add(dt)
    intermediate |= {d for d in _git_commit_times(feature_dir, t0, t1) if t0 < d < t1}
    intermediate |= {d for d in _artifact_activity_mtimes(feature_dir, t0, t1) if t0 < d < t1}
    if not intermediate:
        return None  # 无活动信号可锚 → 不敢判空闲 · 回退墙钟(duration−await)
    ordered = sorted({t0, t1} | intermediate)
    active = 0.0
    for a, b in zip(ordered, ordered[1:]):
        gap = (b - a).total_seconds() / 60.0
        if gap <= threshold:
            active += gap
    span = (t1 - t0).total_seconds() / 60.0
    return max(0, min(int(active), int(span)))


# v8.238:派发档位声明提醒(单源常量 · 每个 stage-start emit 附带 · 消费时点覆盖)——
# 实证 case:goal 三路冷审全跑主对话模型(QA 本应验证档)且零声明 · SKILL 全局规则只在 session 早期被读。
DISPATCH_TIER_REMINDER = (
    "🎚️ 本 stage 若派 subagent/teammate/workflow:每个派发**声明 model + 一句为什么**"
    "(校验/枚举型〔QA 冷审/TC 对照/测试执行/机械外化〕→ 验证档 sonnet/haiku · "
    "判断/创造型〔Architect/PL/方案/裁决〕→ 不降档)· 未声明 = 继承会话模型(台账计 unspecified)· 🎭 评审模型错开:双路 = 外审路 ≠ 主审路 · 单路(fast 合并等)= **该路 ≠ 会话主模型**(如 fable5 会话 → 评审 opus · v8.268/269)· "
    "单源详 SKILL 🎚️ / agents/README §一。"
)

# v8.246:自动流转防歇脚提醒(每次 auto-transition 的 complete emit 附带 · 消费时点覆盖)——
# 实证 case:test→browser_e2e 流转后 AI 汇报完即结束回合(把回合边界当暂停点)· 用户被迫问
# 「为什么暂停了」;R4「回合边界不构成暂停理由」规则早在 SKILL · 流转时刻无提醒 = 读过≠在场。
AUTO_TRANSITION_CONTINUE_REMINDER = (
    "🔴 自动流转 · **非暂停点**:本回合**立即继续执行 {next_stage} stage**"
    "(汇报/总结完不停 —— 回合边界 / 容量预算 / 让用户看进度都不是暂停理由 · R4 不膨胀)· "
    "合法停点仅【SKILL § 授权暂停点清单】· auto/yolo 同理。"
)


# v8.280:preset-aware 流键/图解析 —— 治 micro 链走不通(实证 case:aifriends 4 行合规 bump 走
# micro · execute-start 直接 FAIL)。根因:generic gate 用 **raw `state.flow_type="Feature"`** 比
# `EXECUTE_SPEC.allowed_flow_types=["Micro"]`(legacy 内部键)→ 恒 FAIL;且图查 `flow_by_type.get("Feature")`
# 拿到 **full 图**(即便过①·execute→ship 转移错路由)。resolve_flow_graph/internal_flow_key 在 state.py
# 有 · 但 engine 通用 gate 从没用 · 现有 micro 测试只断言 spec 常量、从没真跑 gate → 漏网。
# 本地实现(engine 不能 import state.py · 循环)· 与 state.py resolve_flow_graph / internal_flow_key、
# specs _flow_key 严格同口径。
_LEGACY_FLOW_ALIASES = {"敏捷需求": ("Feature", "lite"), "Micro": ("Feature", "micro")}


def _internal_flow_key(state: dict) -> str:
    """(state.flow_type, preset) → allowed_flow_types 比对用的内部键(Feature+preset → 敏捷需求/Micro)。"""
    ft = state.get("flow_type") or ""
    pre = state.get("preset") or "full"
    if ft in _LEGACY_FLOW_ALIASES:          # 存量 legacy 值原样(兼容旧 state.json)
        return ft
    if ft == "Feature" and pre == "lite":
        return "敏捷需求"
    if ft == "Feature" and pre == "micro":
        return "Micro"
    return ft


def _resolve_flow_graph(state: dict, flow_by_type: dict) -> dict:
    """(state.flow_type, preset) → 转移图 · 复合键 Feature:micro/Feature:lite · 与 state.py 同口径。"""
    ft = state.get("flow_type") or ""
    pre = state.get("preset") or "full"
    if ft in _LEGACY_FLOW_ALIASES:
        ft, pre = _LEGACY_FLOW_ALIASES[ft]
    if ft == "Feature" and pre in ("lite", "micro"):
        return flow_by_type.get(f"Feature:{pre}", {})
    return flow_by_type.get(ft, {})


def execute_stage_start(
    stage_spec: StageSpec,
    args: argparse.Namespace,
    flow_by_type: dict[str, dict],
) -> None:
    """xx-stage-start 通用执行流程。"""
    feature_path = args.feature
    path, state = load_state(feature_path)
    close_open_pause(state)  # v8.192:闭合 stage 内暂停等待

    # 1. flow_type 校验(v8.280:preset-aware · Feature·micro → 内部键 "Micro" 匹配 EXECUTE_SPEC)
    if stage_spec.allowed_flow_types:
        flow_key = _internal_flow_key(state)
        if flow_key not in stage_spec.allowed_flow_types:
            emit_json({
                "verdict": "FAIL",
                "stage": stage_spec.name,
                "phase": "start",
                "error": (f"flow_type={state.get('flow_type')!r}(preset={state.get('preset')!r}"
                          f" · 内部键 {flow_key!r})不允许进入 {stage_spec.name}"),
                "allowed_flow_types": stage_spec.allowed_flow_types,
                "hint": "检查 state.flow_type / preset 是否正确",
            }, exit_code=1)

    # 2. legal 转移校验(v8.280:按 (flow_type, preset) 解析图 · 非 raw flow_type.get)
    current = state.get("current_stage")
    flow_graph = _resolve_flow_graph(state, flow_by_type)
    if not flow_graph:
        # 解析不到流程图(未知 flow_type/preset)· 显式 FAIL(不静默回退空图误导排查)
        emit_json({
            "verdict": "FAIL",
            "stage": stage_spec.name,
            "phase": "start",
            "error": (f"flow_type={state.get('flow_type')!r}/preset={state.get('preset')!r}"
                      f" 解析不到转移图 · 不在已知流程表"),
            "known_flow_types": sorted(flow_by_type),
            "hint": "state.flow_type / preset 被外改或损坏 · 核对 state.json(不可枚举的流程不进状态机)",
        }, exit_code=1)
    legal_next = flow_graph.get(current, [])
    is_initial_entry = current is None or current == stage_spec.name
    if not is_initial_entry and stage_spec.name not in legal_next:
        # 非法转移无 bypass 出口:stage-start 不做跨 stage 改道 ·
        # 显式改道走 jump-to-stage(写 concerns WARN + 重置目标 contract)。
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
                f"若确需跳过/回炉 · 走显式改道命令:"
                f"state.py jump-to-stage --feature {args.feature} "
                f"--to {stage_spec.name} --reason '<改道原因>'(自动 concerns WARN 留痕)"
            ),
        }, exit_code=1)

    # 2.5. 通用 worktree 物理存在校验(v8.0+P0-2 治本 PTR-F033-type-2 case)
    # 治本根因:init-feature 只写 worktree 元数据 · PMO 漏跑 git worktree add ·
    # 后续 stage 在主 tree 写代码 · 污染主分支。
    # 物化:state.worktree.path + state.worktree.strategy != "off" → 必须 git worktree list 含此 path。
    wt = state.get("worktree", {}) or {}
    wt_strategy = wt.get("strategy", "off")
    wt_path = wt.get("path")
    if wt_strategy != "off" and wt_path:
        _feature_dir_for_git = Path(feature_path).resolve()
        _wt_query_cwd = str(_feature_dir_for_git) if _feature_dir_for_git.is_dir() else None
        if not _worktree_physically_exists(wt_path, cwd=_wt_query_cwd):
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
                require_bypass_reason(args)
                require_user_confirmed(args, yolo=state.get("yolo", False))
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
        require_bypass_reason(args)
        require_user_confirmed(args, yolo=state.get("yolo", False))
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
        brief += _render_pause_discipline(
            stage_spec.authorized_pause_point,
            has_review_convergence_evidence=_has_review_convergence_evidence(stage_spec),
        )
    # 必读路径速查(P0-4)
    brief += _render_required_paths(Path(args.feature).resolve(), stage_spec.name)
    # 状态行模板(P0-10:AI 每次主对话回复末尾必含)
    next_hint = f"按 brief 完成 stage 工作 → 跑 {stage_spec.name}-complete"
    brief += _render_status_line_block(state, next_hint)

    # 7.1 体量元规则:超 MAX_BRIEF_LINES 则截中段 + 写完整版到磁盘
    # (头部 + 尾部纪律段/状态行模板段强制保留 · 尾部红线不被截断吃掉)
    brief_lines = brief.count("\n") + 1
    brief_overflow_path = None
    if brief_lines > MAX_BRIEF_LINES:
        full_path = Path(feature_path) / f"_brief_full_{stage_spec.name}.md"
        try:
            full_path.write_text(brief, encoding="utf-8")
            brief_overflow_path = str(full_path)
            brief = truncate_brief(brief, full_path.name)
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
        "dispatch_tier_reminder": DISPATCH_TIER_REMINDER,  # v8.238:派发声明制 · 消费时点提醒
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
    "blueprint": "blueprint-stage.md",
    "blueprint_lite": "blueprint-lite-stage.md",
    "diagnose": "diagnose-stage.md",
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
# 不要在此放 ship(无文档模板)· 不要放 review-log.jsonl(state.py append)
# dev 仅 Bug 流程有 bugfix/BUG-XXX.md 模板 · 代码产物本身无模板
STAGE_TEMPLATES: dict[str, dict] = {
    "goal": {
        "templates": {
            "PRD.md": "prd.md",
            "PRD-REVIEW.md": None,  # 无独立模板 · 按 reviewer 分段
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
    "diagnose": {
        "templates": {
            "bugfix/BUG-XXX.md": "bug-report.md",  # v8.202:diagnose 产 §现象/根因/修复方案(原漏 · Bug 模板 start 时不给)
        },
        "validators": {},
    },
    "dev": {
        "templates": {
            "bugfix/BUG-XXX.md": "bug-report.md",  # flow_type=Bug 时(追加 §回归测试/§修复记录)
        },
        "validators": {},
    },
    "review": {
        "templates": {
            "REVIEW.md": None,
            "REVIEW-arch.md": None,
            "REVIEW-qa.md": None,
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
        "usage": ("🔴 照上列模板**绝对路径**起草 · **别抄项目里同名旧产物**"
                  "(旧文件可能是旧版模板快照 · 实测 PRD canonical 到达率 2/11 · 抄旧 = 新机制到达不了)"),
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


def _has_review_convergence_evidence(stage_spec: "StageSpec") -> bool:
    """本 stage spec 是否真配了 review 收敛类 evidence(mtime 先后 / revision_history)。

    暂停点纪律段的「state.py 校验兜底」行只对真有此类校验的 stage 渲染 · 不过度声称。
    """
    return any(
        ("review_after" in c.name) or ("revision_history" in c.name)
        for c in stage_spec.evidence_checks
    )


def _render_pause_discipline(authorized_pause_point: str,
                             has_review_convergence_evidence: bool = False) -> str:
    """暂停点纪律段 · append 到 brief 末尾(紧凑版)。

    v8.0+P0-1 治本 PTR-F033 case · L2 substep 链 AI 自觉区。
    v8.71→v8.72 治本 SDK-F038 case(AI 在 blueprint→dev 自造「如何推进 / 落地节奏」
    伪暂停 · 把改动大/破坏式/不可逆/用户参与设计当暂停理由 · 实为 R4 违规):
      - **通用红线(所有 stage)**:禁执行节奏伪决策暂停 + 体量大派 subagent 自决 ——
        有授权暂停点的 stage 也可能在「那一个」授权暂停之外自造执行节奏伪暂停。
      - **无暂停 stage 额外抬头**:连续执行 · 任何暂停都违规。
    has_review_convergence_evidence:本 stage 的 spec 真有 review mtime /
    revision_history evidence 校验时才渲染「state.py 校验兜底」行(不对所有 stage 过度声称)。
    详细 rationale 原载 v8.0 设计稿 04-PAUSE-POINT-DISCIPLINE(已清理 · git 历史可溯)。
    """
    head = f"""

---

### 🔴 暂停点纪律(R5 物化)

唯一授权暂停:**{authorized_pause_point}**
"""
    # v8.72:无暂停 stage(dev/blueprint/blueprint_lite/test)= 连续执行 · 加「任何暂停都违规」抬头
    if "无暂停" in authorized_pause_point:
        head += """
🔴 **本 stage 无授权暂停点 = 连续执行到 stage 完成 · 自动转下一 stage · 任何暂停都是违规**
"""
    # v8.72:执行节奏伪决策 + subagent 自决 = **通用红线**(所有 stage · 治本 SDK-F038)。
    # 有授权暂停点的 stage(goal/ui_design/review/...)也可能在「那一个」授权暂停**之外**
    # 自造执行节奏伪暂停(如"PRD 16 AC 要分批起草给你看吗") · 故不限无暂停 stage。
    head += """
- ⛔ 禁自造"如何推进 / 落地节奏 / 先做一层给你看 / 一次性还是分批 / 要不要先停"等**执行节奏伪决策暂停**(R4 不膨胀 · 执行细节 AI 自决 · **非用户决策**)· "改动大 / 破坏式 / 不可逆 / 文件多 / 用户全程参与设计"**都不是**暂停理由
- ✅ 规模 / 节奏是 AI 自决的执行问题 → 自己组织(可按需派 subagent 并行 · 详 SKILL.md R4)· **不停下问用户怎么干**
- ⛔ Substep 中间禁 AskUserQuestion · 疑问/待决策项写进本 stage 评审产物 · 不中途抛给用户
- ✅ 全部疑问到授权暂停点**一次性** escalate
"""
    if has_review_convergence_evidence:
        head += """- 🛡️ 兜底:state.py 校验 review mtime + frontmatter.revision_history
"""
    head += """- 📖 详细:SKILL.md § R5(b) 暂停点标准格式(现行权威)
"""
    return head


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
    ("Feature", "goal"): ["pl", "external"],  # v8.243:3 冷审→2 路并行 —— PL 对抗质疑 + 覆盖方向制外审(QA 可验证/ARCH 可实现并入外审必覆盖方向 + AI 自主方向 ≥1 · 物化门 external_coverage_present);复杂 feature change-review-roles 加回独立 qa/architect。史:v8.155 三角色隔离冷审防鼓掌 · v8.149 去 external opt-in
    ("Feature", "ui_design"): ["designer", "pm"],
    ("Feature", "panorama_sync"): ["pm", "architect"],
    ("Feature", "blueprint"): ["architect", "external"],  # v8.244:3→2 —— Architect 主审(TECH-REVIEW · 简洁性 counter-lens)+ 覆盖方向制外审(QA 可测试视角并入 · 物化门 cross_review_coverage);复杂 feature 加回独立 qa
    ("Feature", "review"): ["architect", "external"],  # v8.244:3→2 —— Architect 主审(REVIEW-arch · 实现↔设计一致性)+ 覆盖方向制外审(QA 测试真实性视角并入);review 从严:外审必覆盖清单比 blueprint 重一档
    ("Feature", "test"): ["qa"],
    ("Feature", "browser_e2e"): ["qa", "designer"],
    ("Feature", "pm_acceptance"): ["pm"],

    # 敏捷需求(流程减负:冷审 2→1 + pl 保对抗质疑门禁;review 去 external = opt-in 加回)
    ("敏捷需求", "goal"): ["qa", "pl"],  # 1 冷审(QA)+ PL challenge(_evidence_pl_challenge_present 门禁)
    ("敏捷需求", "blueprint_lite"): ["qa"],
    ("敏捷需求", "review"): ["architect", "qa"],  # external 默认关 · change-review-roles 可加回
    ("敏捷需求", "test"): ["qa"],
    ("敏捷需求", "pm_acceptance"): ["pm"],

    # Bug 流程
    ("Bug", "review"): ["external"],  # v8.270:单路 external(diagnose 已经用户确认方案 · review 聚焦 fix↔方案一致 + 不引入新问题 · Architect/QA 视角并入外审覆盖方向 · 错开模型冷审天然满足 v8.269 单路不变式 · change-review-roles 可加回)。史:v8.244 两路制
    ("Bug", "test"): ["qa"],
    ("Bug", "pm_acceptance"): ["pm"],

    # Micro 流程
    # v8.250:Micro 链 = execute → ship(execute 零门禁无评审 · ship 无评审)· 无 roster 条目

    # Feature Planning / 问题排查 不进状态机(init-feature 拒建 state.json)· 无默认矩阵
}


def build_default_stage_review_roles(flow_type: str, preset: str = "full") -> dict[str, list[str]]:
    """按 (flow_type, preset) 抽取默认 stage_review_roles dict(v8.220 preset-aware)。

    内部矩阵键沿用旧 flow 名(敏捷需求/Micro)—— 对外已收缩为 Feature+preset · 此处做映射。
    """
    _key = flow_type
    if flow_type == "Feature" and preset == "lite":
        _key = "敏捷需求"
    elif flow_type == "Feature" and preset == "micro":
        _key = "Micro"
    return {
        stage: roles[:]  # copy 防共享引用
        for (ft, stage), roles in DEFAULT_REVIEW_ROLES.items()
        if ft == _key
    }


# 各 flow_type 完整 stage chain(显式顺序 + optional 标识 + 评审建议理由)
# 用途:prepare-check --flow-type 渲染暂停点「📋 stage × 评审角色」预览表
# 与 FLOW_BY_TYPE(state.py)互补:那里是转移图(legal_next_stages 校验) · 这里是 chain 视图(顺序展示)
FLOW_STAGE_CHAIN: dict[str, list[tuple[str, bool, str, str]]] = {
    # (stage_name, optional, optional_trigger_note, review_reason_hint)
    "Feature": [
        ("goal", False, "", "PRD 业务目标对齐(用户审):草稿后并行派 QA/Architect/PL 三个隔离 subagent 冷审(防鼓掌锚定)· PM 整合 · 无 External(细节归 blueprint · opt-in 保留)"),
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
        ("goal", False, "", "需求小:QA 隔离 subagent 冷审 + PL 对抗质疑(无 External · PM 整合)"),
        ("blueprint_lite", False, "", "QA 测试规划(TC 精简版)· 不要 TECH-REVIEW"),
        ("dev", False, "", "无评审 · RD 自写 + commit"),
        ("review", False, "", "Architect/QA 双视角(external 默认关 · change-review-roles 可 opt-in 加回)"),
        ("test", False, "", "QA 验收"),
        ("pm_acceptance", False, "", "PM 用户视角验收"),
        ("ship", False, "", "无评审 · PMO 编排"),
    ],
    "Bug": [
        ("diagnose", False, "", "🔴 根因细查(深读代码)+ 修复方案 · 用户确认后才进 dev(防 fix 修偏)· 无评审角色"),
        ("dev", False, "", "无评审 · RD 按**已确认的修复方案**写 fix + commit(BUG 报告根因/方案 diagnose 已出)"),
        ("review", False, "", "单路 external 评审(v8.270 · 错开模型冷审 · 覆盖 修复↔diagnose 方案一致 + 测试真实性 + 质量盲区 · 防 fix 引入新问题)"),
        ("test", False, "", "QA 验收回归测试(原 bug 不复发 + 周边无新错)"),
        ("pm_acceptance", False, "", "PM 验收(纯 infra/低风险 fix 可加快)"),
        ("ship", False, "", "无评审 · PMO 编排"),
    ],
    "Micro": [
        ("execute", False, "", "自由执行 · 无规范限制(自选 model/subagent/workflow/测试)· 目标=完成任务 · 只守 worktree 路径 + 准入白名单 · v8.250"),
        ("ship", False, "", "无评审 · PMO 编排(用户验收在 ship1 MR diff)"),
    ],
}


def build_stage_chain_preview(flow_type: str) -> list[dict]:
    """返回 prepare-check 用的 stage chain preview · 每条含 reviewers + reason_hint。

    格式:[{"stage": str, "optional": bool, "trigger": str, "reviewers": [str], "reason": str}]
    - reviewers 来自 DEFAULT_REVIEW_ROLES · 不在则空列表(dev/ship 等无 reviewer stage)
    - reason 是评审建议理由(为什么选这些角色 · 给用户决策参考)
    - 顺序按 FLOW_STAGE_CHAIN 显式定义
    """
    # v8.221:Feature+preset 归一到内部旧键(敏捷需求/Micro 图键保留 · 对外语言已收缩)
    _key = flow_type
    if flow_type == "Feature:lite":
        _key = "敏捷需求"
    elif flow_type == "Feature:micro":
        _key = "Micro"
    chain = FLOW_STAGE_CHAIN.get(_key, [])
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


# brief 截断时强制保留的尾部段标记(暂停点纪律 / 状态行模板 · 命中最早者起整段保留)
_BRIEF_TAIL_KEEP_MARKERS = ("### 🔴 暂停点纪律", "### 📊 状态行模板")
_BRIEF_TRUNCATE_HEAD_LINES = 60
"""截断时保留的头部行数(其余头尾之间的中段折叠成一行标记)。"""


def truncate_brief(brief: str, full_name: str) -> str:
    """brief 超限时截中段:保头部 + 强制保留尾部纪律段/状态行模板段。

    尾部段(暂停点纪律 → 必读路径 → 状态行模板)是 append 的红线/模板 · 不能被
    "只留前 N 行"吃掉。找不到尾部标记时回退老行为(留头 80 行 + 摘要尾巴)。
    full_name = 完整版落盘文件名(标记行引导 AI 需要时去读)。
    """
    lines = brief.splitlines()
    total = len(lines)
    tail_start = next(
        (i for i, ln in enumerate(lines)
         if any(m in ln for m in _BRIEF_TAIL_KEEP_MARKERS)),
        None,
    )
    if tail_start is not None:
        # 尾部段(纪律/状态行)整段保留 · 只截"头部保留区 → 尾部段"之间的中段
        head_end = min(_BRIEF_TRUNCATE_HEAD_LINES, tail_start)
        cut_marker = (
            f"\n\n……(中段截断 · 完整见 [{full_name}]({full_name}))\n\n---\n"
            if tail_start > head_end else "\n"
        )
        return (
            "\n".join(lines[:head_end])
            + cut_marker
            + "\n".join(lines[tail_start:])
            + (f"\n\n---\n\n⚠️ brief 共 {total} 行 > {MAX_BRIEF_LINES} · "
               f"已截中段(头部 + 尾部纪律/状态行段保留)· 完整版见 [{full_name}]({full_name})")
        )
    # 回退:全文无尾部标记 · 留头 80 行
    return "\n".join(lines[:80]) + (
        f"\n\n---\n\n⚠️ brief 共 {total} 行 > {MAX_BRIEF_LINES} · 截断 · "
        f"完整版见 [{full_name}]({full_name})"
    )


def maybe_freeze_review_base(state: dict, next_stage: str,
                             pre_dev_commit: Optional[str]) -> bool:
    """v8.161:首次进 dev 时把 pre-dev HEAD 冻结进 state.review_base_commit。

    review-stage external-review 用它作增量 diff base(评 base...HEAD = 本 feature 的 dev
    增量)· 而非 merge_target...HEAD —— 后者在长 WS / stacked 分支上随 deliverable 累积 →
    跨 feature 串味 + 600s 超时(实证 aifriend yolo/ws02)。pre_dev_commit = 完成 stage
    (blueprint / diagnose / blueprint_lite)的 commit · 在 commit graph 上是 dev HEAD 的祖先
    → base...HEAD 天然排除 prior features(拓扑无关)。

    仅 next_stage==dev 且尚未冻结且 commit 非空时设(review→dev 回退不覆盖 · 再审仍覆盖全部
    dev 增量)。返回是否本次设置(便于测试 / audit)。
    """
    if next_stage == "dev" and not state.get("review_base_commit") and pre_dev_commit:
        state["review_base_commit"] = pre_dev_commit
        return True
    return False


def execute_stage_complete(
    stage_spec: StageSpec,
    args: argparse.Namespace,
    flow_by_type: dict[str, dict],
    stage_specs_registry: dict,
) -> None:
    """xx-stage-complete 通用执行流程。"""
    feature_path = args.feature
    path, state = load_state(feature_path)
    close_open_pause(state)  # v8.192:闭合 stage 内暂停等待

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

    # 2.4. v8.28 · test stage --run-tests 物化跑测试(治本 F037 case-AI 自报 stdout 漏洞)
    # 结果注入 args.integration_test_exit_code · 🔴 必须在 persist / evidence 校验**之前**跑:
    # 单独 --run-tests(不带 --integration-test-exit-code)才不会先撞「缺参数」FAIL ·
    # persist 步(红 base 差分)与 evidence 校验消费的都是注入后的值。
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

    # 2.5. 决策参数显式落库(evidence/execution_hints)· 在校验之前统一执行
    # 校验函数是纯谓词(不写 state/args)· bypass 跳过校验时决策字段照样落库 ·
    # 防「bypass → 副作用不发生 → 转移静默走默认分支」。FAIL 路径不 save_state · 落库不外泄。
    from _v8_stage_specs import persist_args_to_evidence
    persist_args_to_evidence(stage_spec.name, state, args)

    # 3. 校验 artifacts
    artifacts_passed = []
    missing_artifacts = []
    commit_changeset = get_git_commit_changeset(
        auto_commit, cwd=git_cwd
    ) if auto_commit else []

    for art_spec in stage_spec.artifacts:
        # v8.260 fast mode:评审类产物(PRD-REVIEW/TECH-REVIEW)不产 · 跳过校验
        if art_spec.review_artifact and state.get("fast_mode"):
            continue
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
                        "hint": "确保文件头部有 `<!-- TEAMWORK-MACHINE ... -->` 机读块(PRD)或 `--- ... ---` frontmatter(TC/REVIEW 等)",
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

            # commit 校验(精确路径匹配 · changeset 是相对仓库根路径 · artifact 路径相对 feature 目录
            # → 全等或以 "/<artifact 路径>" 结尾才算命中 · 防子串误判如 "a/PRD.md" 命中 "PRD.md.bak")
            if art_spec.must_be_in_commit:
                if not commit_changeset:
                    missing_artifacts.append({
                        "spec": art_spec.path,
                        "reason": f"无法获取 commit {auto_commit} changeset(git 失败或空 commit)",
                        "hint": "确认 auto-commit 正确且真含该文件 · git 环境可用后重试",
                    })
                    continue
                in_commit = any(
                    c == art_spec.path or c.endswith("/" + art_spec.path)
                    for c in commit_changeset
                )
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
        require_bypass_reason(args)
        require_user_confirmed(args, yolo=state.get("yolo", False))
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

    # (v8.28 --run-tests 块已前移至 2.4 · 注入发生在 persist/evidence 校验之前)

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
        "needs_browser_e2e",         # goal/ui_design(可选 · 决定 test 后是否进 browser_e2e)
        "current_failures",          # test/dev:红 base 差分基线的当前失败集
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
        # 写 stage 专属字段(args 优先 · 派生字段〔如 integration_diff_clean〕
        # 由 persist 步落在 contract.evidence · 从那里兜底)
        for key in cfg["round_init_fields"]:
            val = getattr(args, key, None)
            if val is None:
                val = evidence.get(key)
            cur_round[key] = val
        # review 专属:verdict + findings 台账(review 收敛协议)
        if stage_spec.name == "review":
            cur_round["verdict"] = getattr(args, "verdict", None)
            # findings 快照 → 跨轮台账(按 id 合并 · 后轮状态覆盖前轮 · 保 round_opened)·
            # 同时在本轮 round 记 new_findings_count / carried_open_count(收敛审计)。
            from _v8_stage_specs import merge_findings_ledger, parse_review_findings
            snapshot, _findings_err = parse_review_findings(feature_dir)
            merge_findings_ledger(contract, snapshot or [], cur_round)

    # duration(墙钟 span · 保留作审计基线)+ active_minutes(挖掘扣空闲 · v8.276)
    started = contract.get("started_at")
    if started:
        t0 = _parse_iso_flexible(started)                     # v8.276 P3:宽松解析(格式变体不再静默丢)
        t1 = _parse_iso_flexible(contract.get("completed_at"))
        if t0 and t1 and t1 >= t0:
            contract["duration_minutes"] = max(0, int((t1 - t0).total_seconds() // 60))
            try:
                active = _mine_active_minutes(feature_dir, started, contract["completed_at"], contract)
            except Exception:
                active = None                                 # best-effort · 失败回退墙钟
            if active is not None:
                contract["active_minutes"] = active

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

            # 自动进入下一 stage(v8.280:preset-aware 图解析 · micro Feature 拿 Micro 图非 full)
            flow_graph = _resolve_flow_graph(state, flow_by_type)
            if not flow_graph:
                # 解析不到图(未知 flow_type/preset)· 显式 FAIL(不静默回退空图卡死后续)
                emit_json({
                    "verdict": "FAIL",
                    "stage": stage_spec.name,
                    "phase": "complete",
                    "error": (f"flow_type={state.get('flow_type')!r}/preset={state.get('preset')!r}"
                              f" 解析不到转移图 · 不在已知流程表 · 无法计算下一 stage"),
                    "known_flow_types": sorted(flow_by_type),
                    "hint": "state.flow_type / preset 被外改或损坏 · 核对 state.json 后重试",
                }, exit_code=1)
            state["current_stage"] = next_stage
            state["legal_next_stages"] = flow_graph.get(next_stage, [])

            # v8.161:进 dev 那一刻冻结 pre-dev HEAD 作 review-stage 外审的增量 diff 基线。
            maybe_freeze_review_base(state, next_stage, auto_commit)

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
        # 下一 stage 只给 3 行摘要 · 完整 brief 由 {next}-start 渲染(单源)——
        # 消除 complete/start 双份全文渲染 · 且引导必过 {next}-start 前置校验。
        # 摘要仍带暂停点一行:AI 在转移那一刻即见「无暂停/授权暂停点」红线(不等 start)。
        if next_stage in stage_specs_registry:
            next_spec = stage_specs_registry[next_stage]
            pause_line = next_spec.authorized_pause_point or "见 stage brief"
            next_brief = (
                f"## 下一 stage:{next_stage}\n"
                f"- 唯一授权暂停:{pause_line}\n"
                f"- 跑 `state.py {next_stage}-start --feature {args.feature}` "
                f"获取完整 brief 并过前置校验(🔴 不要跳过 {next_stage}-start 直接 -complete)"
            )

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
    # 下一步指向 {next}-start(先过前置校验拿完整 brief)· 不引导直接 -complete
    if transitioned_to and transitioned_to in stage_specs_registry:
        next_hint = f"跑 state.py {transitioned_to}-start"
    elif transitioned_to:
        next_hint = f"已转 {transitioned_to} · 流程终态"
    elif fix_retry_hint:
        next_hint = f"走 {stage_spec.name}-fix → {stage_spec.name}-retry"
    else:
        next_hint = "stage 链结束 / 等用户拍板下一步"
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
        # v8.246:自动流转 = 非暂停点 · 机械提醒立即继续(治「汇报完歇脚」)
        **({"continue_reminder": AUTO_TRANSITION_CONTINUE_REMINDER.format(next_stage=transitioned_to)}
           if transitioned_to else {}),
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
        parser.add_argument(
            "--needs-browser-e2e",
            choices=["true", "false"],
            default=None,
            help=(
                "可选 · 是否启用 browser_e2e stage(test 通过后转 browser_e2e 而非 pm_acceptance)· "
                "写 state.execution_hints.browser_e2e_needed · 不传则不改(默认不启用)"
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
        parser.add_argument(
            "--needs-browser-e2e",
            choices=["true", "false"],
            default=None,
            help=(
                "可选 · 是否启用 browser_e2e stage(test 通过后转 browser_e2e 而非 pm_acceptance)· "
                "写 state.execution_hints.browser_e2e_needed · 不传则不改(UI feature 建议 true)"
            ),
        )
    elif stage_name == "dev" and phase == "complete":
        parser.add_argument("--test-stdout", default="",
                            help="测试 stdout(文件路径或字符串)· 必须非空")
        parser.add_argument("--test-exit-code", type=int, default=None,
                            help="测试 exit code · 必须 = 0")
        parser.add_argument("--current-failures", default="",
                            help="[v8.178] 红 base 差分基线:逗号/换行分隔的当前失败用例 id · "
                                 "工具对照 project-specs/test-baseline.md 算新增(0 新增 → 红 base 也放行)")
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
        parser.add_argument("--current-failures", default="",
                            help="[v8.178] 红 base 差分基线:逗号/换行分隔的当前(integration)失败用例 id · "
                                 "对照 project-specs/test-baseline.md 算新增 · 0 新增 → 红 base 也转 pm_acceptance")
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


# review 轮次预算(review 收敛协议):开新轮 > 预算 → R5 升级暂停点(用户拍板)
DEFAULT_MAX_REVIEW_ROUNDS = 3
FAST_MAX_REVIEW_ROUNDS = 2  # v8.267 fast 模式评审预算封顶(localconfig 更小则从小)

# finding severity 展示顺序(暂停点分组 · 与 specs FINDING_SEVERITIES 同序)
_FINDING_SEVERITY_ORDER = ("BLOCKER", "MAJOR", "MINOR", "NIT")


def _localconfig_max_review_rounds(feature_dir: Path) -> int:
    """读 localconfig `max_review_rounds`(默认 3)· 向上找到 .git 边界。

    非法值(非正整数)→ 默认。与 specs._localconfig_disable_external 同遍历口径。
    """
    try:
        node = Path(feature_dir).resolve()
    except (TypeError, OSError):
        return DEFAULT_MAX_REVIEW_ROUNDS
    for d in [node, *node.parents]:
        cfg = d / ".teamwork_localconfig.json"
        if cfg.exists():
            try:
                v = json.loads(cfg.read_text(encoding="utf-8")).get("max_review_rounds")
            except (OSError, ValueError):
                return DEFAULT_MAX_REVIEW_ROUNDS
            if isinstance(v, (int, float)) and not isinstance(v, bool) and int(v) >= 1:
                return int(v)
            return DEFAULT_MAX_REVIEW_ROUNDS
        if (d / ".git").exists():
            break
    return DEFAULT_MAX_REVIEW_ROUNDS


def _build_review_budget_pause(rounds_done: int, max_rounds: int, ledger: list,
                               fast: bool = False) -> str:
    """review 超预算 R5 升级暂停点 markdown(编号 1/2/3 · SKILL.md § R5(b) 格式)。"""
    open_items = [e for e in ledger if isinstance(e, dict) and e.get("status") == "open"]
    lines = [
        f"⏸️ review 已 {rounds_done} 轮未收敛(超过 max_review_rounds={max_rounds}"
        f"{' · ⚡ fast 模式封顶' if fast else ''})· "
        f"剩余 open finding:{len(open_items)} 条 —— 以下即未收敛决策点 · 请你拍板"
    ]
    for sev in _FINDING_SEVERITY_ORDER:
        group = [e for e in open_items if e.get("severity") == sev]
        if group:
            lines.append(
                f"- {sev}:" + " · ".join(
                    f"{e.get('id')}({e.get('title', '')})" for e in group))
    if not open_items:
        lines.append("- (findings_ledger 无 open 项 · 核对 REVIEW.md frontmatter findings 是否维护)")
    lines.append("请选择:")
    lines.append("1. 仅修 BLOCKER/MAJOR 后收口 💡 推荐(动作:MINOR/NIT 全部 deferred → PENDING 池 · 修完走验证轮 APPROVE)")
    lines.append("2. 继续完整修复(动作:review-retry --user-confirmed --reason '<用户拍板>' 开新一轮)")
    lines.append("3. 按现状 APPROVE(动作:open 项全部 deferred + concerns WARN 留痕)")
    return "\n".join(lines)


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
        "retry_action_hint": (
            "验证轮(范围锁定 · 🔴 禁全量重扫):① 逐条裁决上轮 open finding "
            "fixed/not-fixed ② 只回归审查修复 diff · 拟 APPROVE 且有 fix → 先跑 "
            "external-review --verify-fixes · 完成后:"
        ),
    },
    "test": {
        "commit_field": "test_commit",
        # v8.178:integration 红但差分干净(integration_diff_clean=True)不算失败轮(预存在 ⊆ 基线)
        "is_failed_round": lambda r: (
            (r.get("integration_test_exit_code") not in (None, 0)
             and r.get("integration_diff_clean") is not True)
            or (r.get("e2e_test_exit_code") not in (None, 0))
        ),
        "evidence_keys_to_clear": ["integration_test_exit_code", "e2e_test_exit_code",
                                   "integration_diff_clean", "current_failures"],
        "round_init_fields": {
            "integration_test_exit_code": None,
            "e2e_test_exit_code": None,
            "integration_diff_clean": None,
            "current_failures": None,
        },
        "complete_command_template": (
            "state.py test-complete --feature {feature} --auto-commit <hash> "
            "--artifacts TEST-REPORT.md,e2e/ "
            "--integration-test-exit-code 0 --e2e-test-exit-code 0"
        ),
        "retry_action_hint": "重新跑 integration test + API E2E · 完成后:",
    },
}



YOLO_MAX_FIX_ROUNDS = 10  # v8.198:yolo 同 stage fix-retry 收敛上限(goal-based max-attempts · 防 runaway)


def yolo_rounds_exceeded(state: dict, stage_name: str, max_rounds: int = YOLO_MAX_FIX_ROUNDS) -> bool:
    """v8.198:yolo 下同一 stage 的 fix-retry 轮数达上限 → True(硬停止损 · 真·硬停的合法扩展:
    不是「该问人」而是「收敛失败」—— 继续烧 token 死磕修不动的问题没有意义)。非 yolo 返 False
    (普通模式有「3 次 FAIL → 问用户」的既有协议)。"""
    if not state.get("yolo"):
        return False
    rounds = state.get("stage_contracts", {}).get(stage_name, {}).get("rounds") or []
    return len(rounds) >= max_rounds


def execute_stage_fix(stage_name: str, args: argparse.Namespace) -> None:
    """stage 内 fix:RD 修复 + 记录 fix commit 到 rounds[-1]。"""
    if stage_name not in _STAGE_FIX_RETRY_CONFIG:
        emit_json({
            "verdict": "FAIL",
            "error": f"stage {stage_name!r} 不支持 fix-retry · 仅 {list(_STAGE_FIX_RETRY_CONFIG)}",
        }, exit_code=1)

    cfg = _STAGE_FIX_RETRY_CONFIG[stage_name]
    path, state = load_state(args.feature)
    close_open_pause(state)  # v8.192:闭合 stage 内暂停等待
    if yolo_rounds_exceeded(state, stage_name):
        emit_json({
            "verdict": "FAIL", "command": f"{stage_name}-fix",
            "error": f"yolo 收敛止损:{stage_name} fix-retry 已 {len(state['stage_contracts'][stage_name]['rounds'])} 轮未收敛(上限 {YOLO_MAX_FIX_ROUNDS})",
            "hint": ("🔴 硬停 surface(真·硬停扩展 · 收敛失败 ≠ 该继续死磕):向用户汇报 ① 反复失败的具体问题 "
                     "② 已试过的思路 ③ 建议(回上游 stage 重设计 / 缩范围 / 人工介入)· 不再自动重试"),
        }, exit_code=1)

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
    # v8.172:推进本 stage 的 review target 到 fix commit —— 否则下轮 external-review 默认锚
    # stage_contracts.<stage>.auto_commit(= pre-fix 树)· 评旧代码报 stale finding 引旧行号
    # (实证 audit ×3:ADMIN-Offer-Detail / ANDROID-F017 / INFRA-F018 都要手动 --commit HEAD)。
    state.setdefault("stage_contracts", {}).setdefault(stage_name, {})["auto_commit"] = args.auto_commit
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
    close_open_pause(state)  # v8.192:闭合 stage 内暂停等待

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

    # review 轮次预算(review 收敛协议):开新轮 > max_review_rounds → R5 升级暂停点。
    # 逃生 = --user-confirmed + 非空 --reason(用户拍板 · 写 concerns WARN 留痕);
    # yolo = blanket 委托视作已确认(同 require_user_confirmed 语义)· reason 仍必填(audit)。
    max_review_rounds = None
    if stage_name == "review":
        max_review_rounds = _localconfig_max_review_rounds(Path(args.feature))
        if state.get("fast_mode"):
            # v8.267 fast:评审最多 2 轮 · 轮尽未收敛决策点抛用户(localconfig 更小则从小)
            max_review_rounds = min(max_review_rounds, FAST_MAX_REVIEW_ROUNDS)
        if new_round_num > max_review_rounds:
            confirmed = getattr(args, "user_confirmed", False) or bool(state.get("yolo"))
            reason = (getattr(args, "reason", "") or "").strip()
            if not confirmed:
                emit_json({
                    "verdict": "FAIL",
                    "stage": stage_name,
                    "action": "retry",
                    "error": (
                        f"review 已 {len(rounds)} 轮未收敛 · 开启 round {new_round_num} "
                        f"超预算(max_review_rounds={max_review_rounds})"
                    ),
                    "pause_options_markdown": _build_review_budget_pause(
                        len(rounds), max_review_rounds,
                        contract.get("findings_ledger") or [],
                        fast=bool(state.get("fast_mode"))),
                    "hint": (
                        "⏸️ 把 pause_options_markdown 原样 emit 给用户拍板(R5)· "
                        "选 2 → review-retry --user-confirmed --reason '<用户拍板>' 放行;"
                        "选 1/3 → 先把 open MINOR/NIT 在 REVIEW.md findings 改 deferred(→ PENDING 池)"
                        "再按对应动作收口"
                    ),
                }, exit_code=1)
            if not reason:
                emit_json({
                    "verdict": "FAIL",
                    "stage": stage_name,
                    "action": "retry",
                    "error": "--user-confirmed 超预算放行必带非空 --reason(空串/空白不算)",
                    "hint": "补 --reason '<用户拍板内容>' · 写入 concerns WARN(audit 单源)",
                }, exit_code=1)
            state.setdefault("concerns", []).append(
                f"{now_iso()} WARN review-retry 超预算放行 · round {new_round_num} > "
                f"max_review_rounds={max_review_rounds} · reason: {reason}")

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
    contract.pop("active_minutes", None)     # v8.276:随 duration 一并失效 · 重算
    # v8.276 ②:restart 重置计时锚 —— 新一轮从 now 起算(旧 started_at 会让 duration
    # 跨越已废弃的首次尝试);await_minutes 归零(旧累计属上一轮 · 否则残留污染 duration−await)。
    contract["started_at"] = now_iso()
    contract["await_minutes"] = 0
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
        **({"max_review_rounds": max_review_rounds}
           if max_review_rounds is not None else {}),
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
                execute_stage_start(spec, args, flow_by_type)

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
                execute_stage_complete(spec, args, flow_by_type, stage_specs_registry)

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
        retry_parser.add_argument(
            "--user-confirmed", action="store_true",
            help="[review] 超 max_review_rounds 预算的放行标记 · 须用户在升级暂停点拍板"
                 "(审计发现 AI 自加 = 红线违规)· 必配非空 --reason",
        )
        retry_parser.add_argument(
            "--reason", default="",
            help="[review] --user-confirmed 超预算放行必填 · 用户拍板内容 · 写 concerns WARN(audit)",
        )
        retry_parser.set_defaults(func=make_retry_handler(stage_name))
