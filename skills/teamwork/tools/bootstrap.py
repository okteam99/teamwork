#!/usr/bin/env python3
"""
bootstrap.py — Teamwork session 启动系统维护(独立脚本 · 替代 install.sh)。

每个 session 启动时 PMO 首条响应前必跑(silent · 不打扰用户)。
**独立可执行 · 不归 state.py 状态机域**(职责分离)。

用法:
    python3 tools/bootstrap.py --host claude-code

    仅 --host 必传(宿主是 AI 关于自身的事实 · 不在文件里 · 须显式)。
    --skill-root 自推(bootstrap.py 在 {skill_root}/tools/ 下)·
    --skill-version 已废弃(版本号自读 SKILL.md frontmatter · 单源 · 不由 AI 传)。

职责(纯系统维护 · 不做业务分诊):
- 版本号自读 SKILL.md frontmatter(单源 · 治本 AI 传错版本号写坏注入标记)
- 项目级骨架检查/创建(project-specs/ 下 KNOWLEDGE/TROUBLESHOOTING/GLOSSARY · 旧散放自动迁移)
- chmod +x tools/*.py + templates/*.py(自愈 · 防丢失可执行位)
- 宿主 hooks 部署(.claude/hooks/ 或 .codex/hooks.json)
- CLAUDE.md / AGENTS.md / GEMINI.md 注入段同步(跑 sync-drift.py)
- .worktree/ → .gitignore(默认 worktree_root_path · 详 docs/conventions.md § 10)
- state.json v7 → v8 迁移扫描

版本门禁:
- `.teamwork_localconfig.json` 单文件含两段:
  - 用户 config(worktree / scope / merge_target 等)
  - `_bootstrap` 工具维护(skill_version / last_maintain_at / last_maintain_results)
- bootstrap.py 跑 maintain 前对比 _bootstrap.skill_version + host 与当前 args
  · 相同 → skip maintain 4 项(chmod/hooks/sync-drift/gitignore)
  · 不同 / 缺失 → 跑 maintain 后 update _bootstrap

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


# ─── SKILL 版本号自读(单源 = SKILL.md frontmatter) ──────────


def read_skill_version(skill_root: Path) -> dict:
    """读 SKILL.md frontmatter `version:` → {status, version}。

    v8.x:版本号单源 = SKILL.md frontmatter · bootstrap **自读** · 不再由 AI 传。
    治本:让 AI 转述文件里已有的事实必错 —— case 实证 AI 从 SKILL.md 标题行
    猜成 `8.0`(实际 frontmatter `v8.0.0`)· bootstrap 拿错值喂 sync-drift →
    CLAUDE.md / AGENTS.md 指针标记被写坏。
    """
    skill_md = skill_root / "SKILL.md"
    if not skill_md.exists():
        return {"status": "skill_md_not_found", "version": None,
                "skill_md_path": str(skill_md)}
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as e:
        return {"status": "read_error", "version": None, "error": str(e)}
    if not text.startswith("---\n"):
        return {"status": "no_frontmatter", "version": None}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {"status": "frontmatter_unclosed", "version": None}
    for line in text[4:end].splitlines():
        if line.startswith("version:"):
            v = line.split(":", 1)[1].strip()
            if v:
                return {"status": "ok", "version": v}
            break
    return {"status": "version_field_missing", "version": None}


# ─── 项目级骨架维护 ──────────────────────────────────


PROJECT_SPECS_DIR = "project-specs"


def maintain_project_skeletons(skill_root: Path, project_root: Path) -> dict:
    """silent 维护 project-specs/ 下的项目级骨架文档。

    v8.3:KNOWLEDGE / GLOSSARY / TROUBLESHOOTING 从散在仓库根 → 收敛进
    `project-specs/`(与 `product-overview/` 同级 · 详 docs/conventions.md §13)。
    - project-specs/ 下已存在 → skip
    - 仓库根遗留同名旧文件 → 自动迁移进 project-specs/
    - 都没有 → 复制 templates/ 空骨架
    """
    skeletons = [
        ("KNOWLEDGE.md", "knowledge.md"),
        ("TROUBLESHOOTING.md", "troubleshooting.md"),
        ("GLOSSARY.md", "glossary.md"),
    ]
    specs_dir = project_root / PROJECT_SPECS_DIR

    created, existed, migrated, failed = [], [], [], []
    for project_doc, template_doc in skeletons:
        target = specs_dir / project_doc
        legacy = project_root / project_doc  # 旧:散在仓库根
        if target.exists():
            existed.append(project_doc)
            if legacy.exists():
                failed.append({
                    "doc": project_doc,
                    "reason": f"project-specs/ 已有此文件 · 仓库根遗留同名 {legacy} 需人工删除",
                })
            continue
        # 迁移:仓库根旧散放文件 → project-specs/
        if legacy.exists() and legacy.is_file():
            try:
                specs_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(legacy), str(target))
                migrated.append(project_doc)
            except OSError as e:
                failed.append({"doc": project_doc, "reason": f"migrate failed: {e}"})
            continue
        # 新建空骨架
        template = skill_root / "templates" / template_doc
        if not template.exists():
            failed.append({"doc": project_doc, "reason": f"template not found: {template}"})
            continue
        try:
            specs_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(template, target)
            created.append(project_doc)
        except OSError as e:
            failed.append({"doc": project_doc, "reason": str(e)})

    return {
        "created": created,
        "existed": existed,
        "migrated": migrated,
        "failed": failed,
        "dir": PROJECT_SPECS_DIR,
    }


# ─── workspace 文件名迁移(v7 下划线 → v8 连字符) ──────────


def maintain_workspace_filename(project_root: Path) -> dict:
    """legacy `teamwork_space.md`(下划线)→ `teamwork-space.md`(连字符)。

    v7 用下划线 teamwork_space.md · v8 规范连字符 teamwork-space.md。v7 期建的
    项目 workspace 文件还是下划线名 → v8 spec 让 PMO 读连字符名 → 找不到 →
    子项目 registry 静默不加载 → 路由失效(治本 F049 目录错位 case)。
    bootstrap 在 PMO 读 workspace 之前跑 · 迁移后当次 session 即对上。
    """
    canonical = project_root / "teamwork-space.md"
    legacy = project_root / "teamwork_space.md"
    if canonical.exists():
        if legacy.exists():
            return {"status": "conflict",
                    "detail": f"teamwork-space.md 与 legacy teamwork_space.md 并存 · 人工合并后删 {legacy}"}
        return {"status": "ok"}
    if legacy.exists() and legacy.is_file():
        try:
            shutil.move(str(legacy), str(canonical))
            return {"status": "migrated", "from": "teamwork_space.md", "to": "teamwork-space.md"}
        except OSError as e:
            return {"status": "migrate_failed", "error": str(e)}
    return {"status": "n_a"}  # 单项目仓库 · 无 workspace 文件


# ─── 宿主注入段检查 ────────────────────────────────────


HOST_INJECTION_FILES = {
    "claude-code": "CLAUDE.md",
    "codex-cli": "AGENTS.md",
    "gemini-cli": "GEMINI.md",
}


def maintain_host_injection(skill_root: Path, project_root: Path, host: str,
                             skill_version: str) -> dict:
    """同步**所有已存在**的宿主指令文件 teamwork 注入段(v8.14)。

    策略:
    - 当前 host 对应文件:不存在则创建(--init)· 存在则同步
    - 其他指令文件(CLAUDE.md / AGENTS.md / GEMINI.md):**已存在才同步**(不主动建)
    - 多工具项目下 · 用户单次 bootstrap 让所有指令文件保持最新

    标记格式由 sync-drift.py 维护:`<!-- TEAMWORK_BEGIN:teamwork-pointer vX.Y -->`
    """
    if host not in HOST_INJECTION_FILES:
        return {"status": "host_unknown", "host": host}
    if not skill_version:
        return {"status": "skipped",
                "reason": "SKILL.md frontmatter version 读取失败 · 跳过注入(不写坏标记)"}

    sync_drift = skill_root / "tools" / "sync-drift.py"
    source = skill_root / "templates" / "host-instruction-injection.md"

    if not sync_drift.exists() or not source.exists():
        return {
            "status": "skipped",
            "reason": "sync-drift.py or source template missing",
        }

    primary_fname = HOST_INJECTION_FILES[host]
    results = {}

    for host_name, fname in HOST_INJECTION_FILES.items():
        target = project_root / fname
        is_primary = (host_name == host)
        # 非当前 host 文件 · 已存在才同步 · 不主动创建
        if not is_primary and not target.exists():
            results[fname] = {"status": "skipped_not_present"}
            continue

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
            results[fname] = {"status": "subprocess_error", "error": str(e)}
            continue

        if result.returncode == 0:
            results[fname] = {
                "status": "synced",
                "primary": is_primary,
            }
        else:
            results[fname] = {
                "status": "sync_failed",
                "exit_code": result.returncode,
                "stderr": result.stderr.strip()[:200],
            }

    return {
        "status": "ok",
        "primary_file": primary_fname,
        "results": results,
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
    """确保 .gitignore 含 `.worktree/` + `.teamwork_localconfig.json`(默认 worktree_root_path · 详 docs/conventions.md § 10)。"""
    gitignore = project_root / ".gitignore"
    entries = [
        (".worktree/", ".worktree", "# Teamwork worktree root (default)"),
        (LOCALCONFIG_FILE, LOCALCONFIG_FILE, "# Teamwork local config + bootstrap state"),
    ]

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

    try:
        text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    except OSError as e:
        return {"status": "read_error", "error": str(e)}

    lines = text.split("\n")
    appended = []
    for pattern, pattern_alt, header in entries:
        if pattern in text or pattern_alt in lines:
            continue
        text += (("\n" if text and not text.endswith("\n") else "")
                 + f"{header}\n{pattern}\n")
        appended.append(pattern)

    if not appended:
        return {"status": "already_present"}

    try:
        gitignore.write_text(text, encoding="utf-8")
        return {"status": "appended", "patterns": appended}
    except OSError as e:
        return {"status": "write_failed", "error": str(e)}


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


# ─── localconfig(单源 · config + _bootstrap state) ─────────


LOCALCONFIG_FILE = ".teamwork_localconfig.json"


def read_localconfig(project_root: Path) -> dict:
    """读 .teamwork_localconfig.json · 不存在/损坏返回 {}。

    结构:
    {
      "worktree": "auto",            # config 段(用户编辑)
      "worktree_root_path": ".worktree",
      "scope": "all",
      "merge_target": "staging",
      "_bootstrap": {                # state 段(工具维护 · 用户不编)
        "skill_version": "v8.x",
        "host": "claude-code",
        "last_maintain_at": "...",
        "last_maintain_results": {...}
      }
    }
    """
    cfg = project_root / LOCALCONFIG_FILE
    if not cfg.exists():
        return {}
    try:
        return json.loads(cfg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def read_bootstrap_marker(project_root: Path) -> dict:
    """读 localconfig 的 _bootstrap 子段(版本门禁用)。"""
    return read_localconfig(project_root).get("_bootstrap", {})


def write_bootstrap_marker(project_root: Path, skill_version: str,
                            host: str, maintain_results: dict) -> bool:
    """写 marker 到 localconfig._bootstrap · 保留用户 config 段不动。"""
    cfg = project_root / LOCALCONFIG_FILE
    data = read_localconfig(project_root)  # 保留现有 config 段
    data["_bootstrap"] = {
        "skill_version": skill_version,
        "host": host,
        "last_maintain_at": now_iso(),
        "last_maintain_results": maintain_results,
    }
    try:
        cfg.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


# ─── 主入口 ─────────────────────────────────────────


def cmd_session_bootstrap(args: argparse.Namespace) -> None:
    """session 启动 silent 系统维护(替代 install.sh)。

    设计:
    - 全 silent · 不打扰用户
    - 失败不阻塞 · 内部记录
    - 幂等(已部署/已配置则跳过)
    - **版本门禁**:marker 中 skill_version 与自读的 skill_version 相同 → 跳过 maintain 4 项(chmod/hooks/sync-drift/gitignore)
    - emit JSON(audit · AI 不必 cite)
    """
    # skill_root:--skill-root 显式传则用 · 否则自推(bootstrap.py 在 {skill_root}/tools/ 下)
    skill_root = (Path(args.skill_root).resolve() if args.skill_root
                  else Path(__file__).resolve().parent.parent)
    cwd = Path.cwd()
    project_root = find_project_root(cwd)

    # 每次必跑(轻量 · 幂等)· 版本号自读 SKILL.md frontmatter(单源 · 不由 AI 传)
    version_check = read_skill_version(skill_root)
    skill_version = version_check.get("version")
    skeletons = maintain_project_skeletons(skill_root, project_root)
    workspace_file = maintain_workspace_filename(project_root)
    pending_v7 = scan_v7_state_json(project_root)

    # 版本门禁:marker 记录的版本 == 当前版本 → 跳过 maintain 4 项
    marker = read_bootstrap_marker(project_root)
    marker_version = marker.get("skill_version")
    marker_host = marker.get("host")

    skip_maintain = (
        not args.force
        and marker_version == skill_version
        and marker_host == args.host
    )

    if skip_maintain:
        maintain_status = "skipped_version_unchanged"
        chmod_result = {"status": "skipped"}
        hooks_result = {"status": "skipped"}
        injection = {"status": "skipped"}
        gitignore = {"status": "skipped"}
    else:
        maintain_status = "ran" if not args.force else "ran_forced"
        chmod_result = maintain_chmod_tools(skill_root)
        hooks_result = maintain_host_hooks(skill_root, project_root, args.host)
        injection = maintain_host_injection(
            skill_root, project_root, args.host, skill_version
        )
        gitignore = maintain_gitignore_worktree(project_root)
        # 跑完 maintain 写 marker 锁版本(下次同版本会 skip)
        marker_results = {
            "chmod": chmod_result.get("status", "unknown"),
            "hooks": hooks_result.get("status", "unknown"),
            "host_injection": injection.get("status", "unknown"),
            "gitignore_worktree": gitignore.get("status", "unknown"),
        }
        write_bootstrap_marker(project_root, skill_version,
                                args.host, marker_results)

    result = {
        "verdict": "PASS",  # silent · 总是 PASS · 不阻塞
        "command": "session-bootstrap",
        "timestamp": now_iso(),
        "host": args.host,
        "skill_root": str(skill_root),
        "skill_version": skill_version,
        "project_root": str(project_root),
        "maintain_status": maintain_status,
        "marker_skill_version_before": marker_version,
        "checks": {
            "skill_version": version_check,
            "skeletons": skeletons,
            "workspace_filename": workspace_file,
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
        default=None,
        help="[可选] SKILL_ROOT 绝对路径 · 缺省自推(bootstrap.py 在 {skill_root}/tools/ 下)",
    )
    p.add_argument(
        "--skill-version",
        default=None,
        help="[已废弃] 版本号由 bootstrap 自读 SKILL.md frontmatter · 传了忽略(保留仅防老命令报错)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="强制跑 maintain 4 项(chmod/hooks/sync-drift/gitignore)· 忽略 marker 版本门禁",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()
    cmd_session_bootstrap(args)


if __name__ == "__main__":
    main()
