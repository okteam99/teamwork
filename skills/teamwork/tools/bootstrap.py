#!/usr/bin/env python3
"""
bootstrap.py — Teamwork session 启动系统维护(独立脚本 · 替代 install.sh)。

每个 session 启动时 PMO 首条响应前必跑(silent · 不打扰用户)。
**独立可执行 · 不归 state.py 状态机域**(职责分离)。

用法:
    python3 tools/bootstrap.py \\
      --host claude-code \\
      --skill-root /Users/X/.claude/skills/teamwork \\
      --skill-version v8.x

职责(纯系统维护 · 不做业务分诊):
- SKILL_VERSION 一致性校验
- 项目级骨架检查/创建(KNOWLEDGE/TROUBLESHOOTING/GLOSSARY)
- chmod +x tools/*.py + templates/*.py(自愈 · 防丢失可执行位)
- 宿主 hooks 部署(.claude/hooks/ 或 .codex/hooks.json)
- CLAUDE.md / AGENTS.md / GEMINI.md 注入段同步(跑 sync-drift.py)
- .worktree/ → .gitignore(默认 worktree_root_path · 详 docs/conventions.md § 10)
- state.json v7 → v8 迁移扫描

设计原则:
- 全 silent · 不 emit 用户可见报告
- 失败不阻塞(WARN/INFO 内部记录)
- 幂等(重复跑无副作用 · 已部署/已配置则跳过)
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


def maintain_host_injection(skill_root: Path, project_root: Path, host: str,
                             skill_version: str) -> dict:
    """同步宿主指令文件 teamwork 注入段(缺则跑 sync-drift.py 注入 / 旧则升级)。

    标记格式由 sync-drift.py 维护:`<!-- TEAMWORK_BEGIN:teamwork-pointer vX.Y -->`
    """
    fname = HOST_INJECTION_FILES.get(host)
    if not fname:
        return {"status": "host_unknown", "host": host}

    target = project_root / fname
    sync_drift = skill_root / "tools" / "sync-drift.py"
    source = skill_root / "templates" / "host-instruction-injection.md"

    if not sync_drift.exists() or not source.exists():
        return {
            "status": "skipped",
            "reason": "sync-drift.py or source template missing",
            "file": fname,
        }

    try:
        result = subprocess.run(
            [
                "python3", str(sync_drift),
                "--target", str(target),
                "--source", str(source),
                "--skill-version", skill_version,
                "--init",
            ],
            capture_output=True, text=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"status": "subprocess_error", "error": str(e), "file": fname}

    if result.returncode == 0:
        return {"status": "synced", "file": fname}
    return {
        "status": "sync_failed",
        "file": fname,
        "exit_code": result.returncode,
        "stderr": result.stderr.strip()[:200],
    }


# ─── chmod 工具脚本 ─────────────────────────────────────


def maintain_chmod_tools(skill_root: Path) -> dict:
    """给 tools/*.py + templates/*.py 加可执行位(idempotent)。"""
    import stat

    counts = {"tools_py": 0, "templates_py": 0, "failed": []}
    for sub in ("tools", "templates"):
        d = skill_root / sub
        if not d.is_dir():
            continue
        for p in d.glob("*.py"):
            try:
                st = p.stat()
                p.chmod(st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                if sub == "tools":
                    counts["tools_py"] += 1
                else:
                    counts["templates_py"] += 1
            except OSError as e:
                counts["failed"].append({"path": str(p), "reason": str(e)})
    return counts


# ─── hooks 部署 ──────────────────────────────────────


def _find_hooks_src(skill_root: Path) -> Optional[Path]:
    """找 hooks/ 源目录(*.sh 在这里):优先 skill_root/hooks · fallback repo 根。"""
    candidates = [
        skill_root / "hooks",                      # skill 内嵌
        skill_root.parent.parent / "hooks",        # symlink 模式 repo 根 hooks/
    ]
    for c in candidates:
        if c.is_dir() and any(c.glob("*.sh")):
            return c
    return None


def maintain_host_hooks(skill_root: Path, project_root: Path, host: str) -> dict:
    """部署 hooks 到宿主目录(claude-code → .claude/hooks/ · codex-cli → .codex/)。"""
    hooks_src = _find_hooks_src(skill_root)
    if hooks_src is None:
        return {"status": "skipped", "reason": "no hooks/ source dir found"}

    deployed_sh, deployed_json = [], None
    failed = []

    if host == "claude-code":
        target_dir = project_root / ".claude" / "hooks"
        target_dir.mkdir(parents=True, exist_ok=True)
        for sh in hooks_src.glob("*.sh"):
            try:
                shutil.copy(sh, target_dir / sh.name)
                deployed_sh.append(sh.name)
            except OSError as e:
                failed.append({"file": sh.name, "reason": str(e)})
        # hooks.json:claude 用 hooks/ 下的(含 PreCompact/PostCompact)
        src_json = hooks_src / "hooks.json"
        if src_json.exists():
            try:
                shutil.copy(src_json, target_dir / "hooks.json")
                deployed_json = "hooks.json (claude-code)"
            except OSError as e:
                failed.append({"file": "hooks.json", "reason": str(e)})
    elif host == "codex-cli":
        target_hooks_dir = project_root / ".codex"
        target_hooks_dir.mkdir(parents=True, exist_ok=True)
        # codex hooks.json 在 codex-agents/(独立 · 无 PreCompact)
        codex_hooks_json = skill_root / "codex-agents" / "hooks.json"
        if codex_hooks_json.exists():
            try:
                shutil.copy(codex_hooks_json, target_hooks_dir / "hooks.json")
                deployed_json = "hooks.json (codex-cli)"
            except OSError as e:
                failed.append({"file": "hooks.json", "reason": str(e)})
        # codex agent toml
        agents_target = target_hooks_dir / "agents"
        agents_target.mkdir(parents=True, exist_ok=True)
        codex_agents_dir = skill_root / "codex-agents"
        if codex_agents_dir.is_dir():
            for toml in codex_agents_dir.glob("*.toml"):
                try:
                    shutil.copy(toml, agents_target / toml.name)
                    deployed_sh.append(toml.name)
                except OSError as e:
                    failed.append({"file": toml.name, "reason": str(e)})
    else:
        return {"status": "host_no_hooks", "host": host}

    return {
        "status": "deployed",
        "host": host,
        "sh_count": len(deployed_sh),
        "hooks_json": deployed_json,
        "failed": failed,
    }


# ─── .worktree/ → .gitignore ─────────────────────────


def maintain_gitignore_worktree(project_root: Path) -> dict:
    """确保 .gitignore 含 .worktree/(默认 worktree_root_path · 详 docs/conventions.md § 10)。"""
    gitignore = project_root / ".gitignore"
    pattern = ".worktree/"
    pattern_alt = ".worktree"
    header = "# Teamwork worktree root (default)"

    # 仅在 git repo 内执行
    if not (project_root / ".git").exists():
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=str(project_root), capture_output=True, text=True, timeout=3,
            )
            if result.returncode != 0:
                return {"status": "not_git_repo"}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"status": "git_not_available"}

    if gitignore.exists():
        try:
            text = gitignore.read_text(encoding="utf-8")
        except OSError as e:
            return {"status": "read_error", "error": str(e)}
        if pattern in text or pattern_alt in text.split("\n"):
            return {"status": "already_present"}
        try:
            with gitignore.open("a", encoding="utf-8") as fh:
                fh.write(f"\n{header}\n{pattern}\n")
            return {"status": "appended"}
        except OSError as e:
            return {"status": "append_failed", "error": str(e)}
    else:
        try:
            gitignore.write_text(f"{header}\n{pattern}\n", encoding="utf-8")
            return {"status": "created"}
        except OSError as e:
            return {"status": "create_failed", "error": str(e)}


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
    """session 启动 silent 系统维护(替代 install.sh)。

    设计:
    - 全 silent · 不打扰用户
    - 失败不阻塞 · 内部记录
    - 幂等(已部署/已配置则跳过)
    - emit JSON(audit · AI 不必 cite)
    """
    skill_root = Path(args.skill_root).resolve()
    cwd = Path.cwd()
    project_root = find_project_root(cwd)

    # 1. SKILL_VERSION 校验
    version_check = check_skill_version(skill_root, args.skill_version)

    # 2. 项目级骨架维护
    skeletons = maintain_project_skeletons(skill_root, project_root)

    # 3. chmod +x tools/*.py + templates/*.py(防丢失可执行位)
    chmod_result = maintain_chmod_tools(skill_root)

    # 4. 宿主 hooks 部署(.claude/hooks/ 或 .codex/)
    hooks_result = maintain_host_hooks(skill_root, project_root, args.host)

    # 5. 宿主注入段同步(跑 sync-drift.py)
    injection = maintain_host_injection(
        skill_root, project_root, args.host, args.skill_version
    )

    # 6. .worktree/ → .gitignore
    gitignore = maintain_gitignore_worktree(project_root)

    # 7. v7 state.json 扫描
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
            "chmod": chmod_result,
            "hooks": hooks_result,
            "host_injection": injection,
            "gitignore_worktree": gitignore,
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
