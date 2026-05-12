#!/usr/bin/env python3
"""
init_triage.py — Teamwork triage 入口的物化 bootstrap 脚本。

职责（PMO 在 triage 入口跑一次 · 拿 JSON 决策）：
- 幂等创建项目根空骨架文件（TROUBLESHOOTING.md / GLOSSARY.md）
- 检测既有空骨架 vs 已填（硬编码标识符 · 不依赖 PMO grep）
- 探测项目级文件存在性（teamwork_space.md / .teamwork_localconfig.md）
- find 全局 schema 文档（P0-119 evidence-binding）
- worktree 环境只读探测（不创建）
- 比对 skill_version vs local_version（PMO 注入 · 脚本只判等）

PMO 必须注入（脚本不探测）：
- --host       PMO 自报宿主（claude-code / codex-cli / gemini-cli / unknown）
- --skill-root PMO 已 read 的 SKILL.md 所在目录（templates 子目录靠它定位）
- --skill-version PMO 已 read 的 SKILL.md frontmatter version

红线：
1. 创建动作 = bootstrap 例外（与 R8 业务写门禁区隔 · 仅幂等复制空骨架）
2. cite-only output：单次 stdout JSON · 含 advisories[] · PMO 一次引入对话
3. 不写 secret / 不动用户已有内容（已存在文件不覆盖）
4. 项目根 = git root（cwd 在 git repo 内时）· 否则 = cwd
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HOST_ENUM = {"claude-code", "codex-cli", "gemini-cli", "unknown"}

# 空骨架检测稳定标识符（与 templates/* 顶部一致 · 改模板时记得同步）
EMPTY_SKELETON_MARKER = "本文是 teamwork prepare-stage 自动创建的空骨架"

# 项目根创建文件清单：file_name → template_relative_path
BOOTSTRAP_FILES = {
    "TROUBLESHOOTING.md": "templates/troubleshooting.md",
    "GLOSSARY.md": "templates/glossary.md",
}

# 项目根只读检测文件清单
PROBE_FILES = ["teamwork_space.md", ".teamwork_localconfig.md"]

# 全局 schema 文档 find pattern（P0-119）
SCHEMA_DOC_PATTERNS = ["*database*schema*.md", "*schema*registry*.md"]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def die(code: int, payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(code)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def resolve_project_root(cwd: Path) -> tuple[Path, str]:
    """git rev-parse --show-toplevel · 失败回退到 cwd。"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd), capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()), "git"
    except FileNotFoundError:
        pass
    return cwd, "cwd"


def is_empty_skeleton(path: Path) -> bool:
    """读前 30 行查 marker · marker 存在 = 用户没填（fill-in 时通常会删除提示）。"""
    try:
        with path.open("r", encoding="utf-8") as f:
            head = "".join(f.readline() for _ in range(30))
        return EMPTY_SKELETON_MARKER in head
    except OSError:
        return False


def bootstrap_file(name: str, tpl_rel: str, project_root: Path,
                   skill_root: Path, no_create: bool) -> dict[str, Any]:
    target = project_root / name
    if target.exists():
        return {
            "exists": True,
            "path": str(target),
            "is_empty_skeleton": is_empty_skeleton(target),
            "created_now": False,
        }
    if no_create:
        return {"exists": False, "path": None, "is_empty_skeleton": None, "created_now": False}

    src = skill_root / tpl_rel
    if not src.exists():
        return {
            "exists": False, "path": None, "is_empty_skeleton": None, "created_now": False,
            "error": f"template missing: {src}",
        }
    shutil.copy2(src, target)
    return {
        "exists": True, "path": str(target),
        "is_empty_skeleton": True,  # 刚复制的肯定是空骨架
        "created_now": True,
    }


def probe_file(name: str, project_root: Path) -> dict[str, Any]:
    p = project_root / name
    if p.exists():
        return {"exists": True, "path": str(p)}
    # teamwork_space.md 容许 docs/ 子目录
    if name == "teamwork_space.md":
        alt = project_root / "docs" / name
        if alt.exists():
            return {"exists": True, "path": str(alt)}
    return {"exists": False, "path": None}


def find_schema_docs(project_root: Path) -> dict[str, Any]:
    """find {root} -name '*database*schema*.md' -o -name '*schema*registry*.md'"""
    args = ["find", str(project_root)]
    for i, pat in enumerate(SCHEMA_DOC_PATTERNS):
        if i > 0:
            args.append("-o")
        args += ["-name", pat]
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return {"docs": [], "evidence": {"error": "find not in PATH"}}
    docs = sorted(p for p in result.stdout.strip().splitlines() if p)
    return {
        "docs": docs,
        "evidence": {
            "command": " ".join(args),
            "exit_code": result.returncode,
            "stdout_lines": len(docs),
            "scanned_at": now_iso(),
        },
    }


def probe_worktree(project_root: Path) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(project_root), capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return {"available": False, "reason": "git not found"}
    if result.returncode != 0:
        return {"available": False, "reason": result.stderr.strip()}

    # parse porcelain · 找当前 cwd 对应的 worktree
    worktrees: list[dict[str, str]] = []
    cur: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if not line:
            if cur:
                worktrees.append(cur)
                cur = {}
            continue
        if line.startswith("worktree "):
            cur["path"] = line[len("worktree "):]
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch "):].replace("refs/heads/", "")
    if cur:
        worktrees.append(cur)

    # 当前在哪个 worktree
    cwd_str = str(Path.cwd().resolve())
    in_wt = next((w for w in worktrees if cwd_str.startswith(w.get("path", "_no_match_"))), None)
    return {
        "available": True,
        "current_path": in_wt.get("path") if in_wt else cwd_str,
        "current_branch": (in_wt or {}).get("branch"),
        "worktree_count": len(worktrees),
        "feature_id": None,  # PMO 后续按 branch 推断 · 脚本不解析
    }


def build_advisories(state: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []

    if not state["project_files"]["teamwork_space.md"]["exists"]:
        out.append({
            "severity": "INFO", "topic": "first-init",
            "message": "teamwork_space.md 不存在 · 走首次初始化流程（用户首次跑 teamwork）",
        })

    for name in BOOTSTRAP_FILES:
        info = state["project_files"][name]
        if info.get("created_now"):
            out.append({
                "severity": "INFO", "topic": "skeleton-created",
                "message": (f"{name} 不存在 · 已 silent 复制 teamwork 模板 · "
                            f"用户首次相关动作时建议一句话提示补充"),
            })
        elif info.get("is_empty_skeleton"):
            out.append({
                "severity": "INFO", "topic": "empty-skeleton",
                "message": (f"{name} 仍是 teamwork 自动复制的空骨架 · "
                            f"用户首次相关动作时建议一句话提示补充"),
            })

    if not state["version_match"]:
        out.append({
            "severity": "WARN", "topic": "version-mismatch",
            "message": (f"skill_version={state['skill_version']} ≠ "
                        f"local_version={state['local_version']} · "
                        f"PMO 应跑 tools/sync-drift.py 同步 CLAUDE.md/AGENTS.md "
                        f"teamwork 注入段（marker-aware · 用户内容保护 · v7.3.10+P0-134）· "
                        f"完成后回写 .teamwork_localconfig.md"),
        })

    if state["global_schema_docs"]["docs"]:
        out.append({
            "severity": "INFO", "topic": "schema-docs-found",
            "message": (f"全仓库 find 命中 {len(state['global_schema_docs']['docs'])} 个全局 schema 文档 · "
                        f"Blueprint Tech Review / Review CR 启用 schema 专项时强校验同步"),
        })

    if not state["worktree"]["available"]:
        out.append({
            "severity": "WARN", "topic": "worktree-unavailable",
            "message": f"worktree 不可用：{state['worktree'].get('reason', 'unknown')}",
        })

    return out


def main() -> None:
    p = argparse.ArgumentParser(prog="init_triage.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cwd", default=os.getcwd(), help="cwd · 默认当前目录")
    p.add_argument("--host", required=True, choices=sorted(HOST_ENUM),
                   help="PMO 自报宿主 · 脚本不探测")
    p.add_argument("--skill-root", required=True,
                   help="PMO 已 read 的 SKILL.md 所在目录（templates 子目录靠它定位）")
    p.add_argument("--skill-version", required=True,
                   help="PMO 已 read 的 SKILL.md frontmatter version")
    p.add_argument("--local-version", default=None,
                   help="可选 · 缺省脚本自己读 .teamwork_localconfig.md.teamwork_version")
    p.add_argument("--no-create", action="store_true",
                   help="只检测不创建（dry-run 模式）")
    args = p.parse_args()

    cwd = Path(args.cwd).resolve()
    skill_root = Path(args.skill_root).resolve()
    if not skill_root.exists():
        die(2, {"verdict": "FAIL", "error": f"skill-root 不存在: {skill_root}"})

    project_root, root_source = resolve_project_root(cwd)

    # 1. 探测项目级文件
    project_files: dict[str, Any] = {}
    for name in PROBE_FILES:
        project_files[name] = probe_file(name, project_root)
    for name, tpl in BOOTSTRAP_FILES.items():
        project_files[name] = bootstrap_file(name, tpl, project_root, skill_root, args.no_create)

    # 2. 解析 local_version
    local_version = args.local_version
    if local_version is None:
        cfg = project_root / ".teamwork_localconfig.md"
        if cfg.exists():
            try:
                for line in cfg.read_text(encoding="utf-8").splitlines():
                    s = line.strip()
                    if s.startswith("teamwork_version:") or s.startswith("- teamwork_version:"):
                        local_version = s.split(":", 1)[1].strip().strip('"').strip("'") or None
                        break
            except OSError:
                pass

    version_match = (local_version == args.skill_version) if local_version else False

    # 3. global schema docs find
    schema_docs = find_schema_docs(project_root)

    # 4. worktree 探测（read-only）
    worktree = probe_worktree(project_root)

    state: dict[str, Any] = {
        "host": args.host,
        "skill_root": str(skill_root),
        "skill_version": args.skill_version,
        "local_version": local_version,
        "version_match": version_match,
        "project_root": str(project_root),
        "project_root_source": root_source,
        "project_files": project_files,
        "global_schema_docs": schema_docs,
        "worktree": worktree,
        "scanned_at": now_iso(),
    }
    state["advisories"] = build_advisories(state)
    state["audit_line"] = build_audit_line(state)

    emit({"verdict": "OK", **state})


def build_audit_line(state: dict[str, Any]) -> str:
    """单行 audit · PMO 在首条响应可见 cite（治本 P0-133：用户能直接看到 PMO 跑了 init_triage）。"""
    advs = state.get("advisories") or []
    if not advs:
        topics = "无"
    else:
        # 聚合相同 topic 的计数
        from collections import Counter
        counts = Counter(a["topic"] for a in advs)
        topics = ", ".join(f"{t}×{c}" if c > 1 else t for t, c in counts.items())
    pf = state.get("project_files") or {}
    created = [n for n, v in pf.items() if isinstance(v, dict) and v.get("created_now")]
    empty = [n for n, v in pf.items() if isinstance(v, dict) and v.get("is_empty_skeleton") and not v.get("created_now")]
    extras = []
    if created:
        extras.append(f"已创建={','.join(created)}")
    if empty:
        extras.append(f"空骨架={','.join(empty)}")
    if not state.get("version_match"):
        extras.append("version-mismatch")
    extra_str = " · " + " · ".join(extras) if extras else ""
    return (f"📊 init_triage: verdict=OK · host={state['host']} · "
            f"project_root={state['project_root']} · advisories=[{topics}]{extra_str}")


if __name__ == "__main__":
    main()
