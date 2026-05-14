#!/usr/bin/env python3
"""
bootstrap.py — Teamwork v8.0+P0-13 session 启动系统维护(独立脚本)。

每个 session 启动时 PMO 首条响应前必跑(silent · 不打扰用户)。
**独立可执行 · 不归 state.py 状态机域**(职责分离)。

用法:
    python3 tools/bootstrap.py \\
      --host claude-code \\
      --skill-root /Users/X/.claude/skills/teamwork \\
      --skill-version v8.0.0

职责(纯系统维护 · 不做业务分诊):
- SKILL_VERSION 一致性校验
- 项目级骨架检查/创建(KNOWLEDGE/TROUBLESHOOTING/GLOSSARY)
- CLAUDE.md / AGENTS.md / GEMINI.md 注入段检查(对接 sync-drift.py)
- state.json v7 → v8 迁移扫描

设计原则:
- 全 silent · 不 emit 用户可见报告
- 失败不阻塞(WARN/INFO 内部记录)
- 幂等(重复跑无副作用)
- AI 跑后不必 cite(audit JSON 写日志即可)
- 独立脚本 · 不混入 state.py(状态机)域
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─── 项目根推断 ──────────────────────────────────────────────


def find_project_root(start: Path) -> Path:
    """从 start 向上找 git common dir 的 parent(主 tree)。

    使用 git rev-parse --git-common-dir 确保:
    - worktree 内跑时返回主 tree(共享骨架文档)
    - 主 tree 内跑时返回主 tree
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(start.resolve()),
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            git_common = result.stdout.strip()
            git_common_path = Path(git_common)
            if not git_common_path.is_absolute():
                git_common_path = (start.resolve() / git_common).resolve()
            return git_common_path.parent
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # fallback:向上找 .git 文件/目录
    p = start.resolve()
    for _ in range(10):
        if (p / ".git").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return start.resolve()


# ─── SKILL_VERSION 校验 ───────────────────────────────────


def check_skill_version(skill_root: Path, claimed_version: str) -> dict:
    """读 SKILL.md frontmatter version · 对比 claimed_version。"""
    skill_md = skill_root / "SKILL.md"
    if not skill_md.exists():
        return {"status": "skill_md_not_found", "skill_md_path": str(skill_md)}

    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as e:
        return {"status": "read_error", "error": str(e)}

    # 解析 frontmatter version
    if not text.startswith("---\n"):
        return {"status": "no_frontmatter"}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {"status": "frontmatter_unclosed"}

    fm_text = text[4:end]
    actual_version = None
    for line in fm_text.splitlines():
        if line.startswith("version:"):
            actual_version = line.split(":", 1)[1].strip()
            break

    if not actual_version:
        return {"status": "version_field_missing"}

    if actual_version == claimed_version:
        return {"status": "ok", "actual": actual_version, "claimed": claimed_version}
    return {
        "status": "mismatch",
        "actual": actual_version,
        "claimed": claimed_version,
    }


# ─── 项目级骨架维护 ──────────────────────────────────


def maintain_project_skeletons(skill_root: Path, project_root: Path) -> dict:
    """silent 复制 templates/ 骨架到项目根(若不存在)。"""
    skeletons = [
        ("KNOWLEDGE.md", "knowledge.md"),
        ("TROUBLESHOOTING.md", "troubleshooting.md"),
        ("GLOSSARY.md", "glossary.md"),
    ]

    created, existed, failed = [], [], []
    for project_doc, template_doc in skeletons:
        target = project_root / project_doc
        if target.exists():
            existed.append(project_doc)
            continue
        template = skill_root / "templates" / template_doc
        if not template.exists():
            failed.append({"doc": project_doc, "reason": f"template not found: {template}"})
            continue
        try:
            shutil.copy(template, target)
            created.append(project_doc)
        except OSError as e:
            failed.append({"doc": project_doc, "reason": str(e)})

    return {"created": created, "existed": existed, "failed": failed}


# ─── 宿主注入段检查 ────────────────────────────────────


HOST_INJECTION_FILES = {
    "claude-code": "CLAUDE.md",
    "codex-cli": "AGENTS.md",
    "gemini-cli": "GEMINI.md",
}


def check_host_injection(project_root: Path, host: str) -> dict:
    """检查宿主指令文件是否含 teamwork 注入段标记。

    标记格式(sync-drift.py 维护):
    <!-- TEAMWORK_SKILL_BEGIN -->
    ...
    <!-- TEAMWORK_SKILL_END -->
    """
    fname = HOST_INJECTION_FILES.get(host)
    if not fname:
        return {"status": "host_unknown", "host": host}

    target = project_root / fname
    if not target.exists():
        return {"status": "host_file_missing", "file": fname}

    try:
        text = target.read_text(encoding="utf-8")
    except OSError as e:
        return {"status": "read_error", "error": str(e)}

    has_begin = "TEAMWORK_SKILL_BEGIN" in text
    has_end = "TEAMWORK_SKILL_END" in text
    if has_begin and has_end:
        return {"status": "ok", "file": fname}
    return {
        "status": "injection_missing",
        "file": fname,
        "has_begin": has_begin,
        "has_end": has_end,
    }


# ─── v7 state.json 扫描(迁移检测) ──────────────────────


def scan_v7_state_json(project_root: Path) -> list[str]:
    """扫 docs/features/*/state.json · 找需要 migrate-v7-to-v8 的。

    v8 state.json 含 schema_version=v8.0 · v7 没此字段。
    """
    pending = []
    features_dir = project_root / "docs" / "features"
    if not features_dir.exists():
        return pending

    for state_json in features_dir.glob("*/state.json"):
        try:
            data = json.loads(state_json.read_text(encoding="utf-8"))
            if data.get("schema_version") != "v8.0":
                pending.append(str(state_json))
        except (OSError, json.JSONDecodeError):
            continue
    return pending


# ─── 主入口 ─────────────────────────────────────────


def cmd_session_bootstrap(args: argparse.Namespace) -> None:
    """v8.0+P0-13:session 启动 silent 系统维护。

    设计:
    - 全 silent · 不打扰用户
    - 失败不阻塞 · 内部记录
    - emit JSON(audit · AI 不必 cite)
    """
    skill_root = Path(args.skill_root).resolve()
    cwd = Path.cwd()
    project_root = find_project_root(cwd)

    # 1. SKILL_VERSION 校验
    version_check = check_skill_version(skill_root, args.skill_version)

    # 2. 项目级骨架维护
    skeletons = maintain_project_skeletons(skill_root, project_root)

    # 3. 宿主注入段检查
    injection = check_host_injection(project_root, args.host)

    # 4. v7 state.json 扫描
    pending_v7 = scan_v7_state_json(project_root)

    result = {
        "verdict": "PASS",  # silent · 总是 PASS · 不阻塞
        "command": "session-bootstrap",
        "timestamp": now_iso(),
        "host": args.host,
        "skill_root": str(skill_root),
        "skill_version": args.skill_version,
        "project_root": str(project_root),
        "checks": {
            "skill_version": version_check,
            "skeletons": skeletons,
            "host_injection": injection,
            "v7_features_pending_migrate": pending_v7,
        },
    }

    # silent emit JSON · AI 跑后不必 cite · 用户不可见报告
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)


def build_parser() -> argparse.ArgumentParser:
    """独立脚本 argparse(不归 state.py)。"""
    p = argparse.ArgumentParser(
        prog="bootstrap.py",
        description="Teamwork v8.0+P0-13 session 启动系统维护(silent)",
    )
    p.add_argument(
        "--host",
        required=True,
        choices=["claude-code", "codex-cli", "gemini-cli", "unknown"],
        help="宿主环境",
    )
    p.add_argument(
        "--skill-root",
        required=True,
        help="SKILL_ROOT 绝对路径(如 /Users/X/.claude/skills/teamwork)",
    )
    p.add_argument(
        "--skill-version",
        required=True,
        help="AI 声称的 skill version(用于一致性校验)",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()
    cmd_session_bootstrap(args)


if __name__ == "__main__":
    main()
