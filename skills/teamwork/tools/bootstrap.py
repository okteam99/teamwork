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
import os
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


def maintain_gitignore_worktree(project_root: Path,
                                 skill_root: Optional[Path] = None) -> dict:
    """确保 .gitignore 含 teamwork 推荐 ignore 模式。

    v8.31 治本 INFRA-F025 case G2:`.claude/scheduled_tasks.lock` 等 harness 锁
    文件每 session 写自己 pid · 跟踪意义为 0 · 必须 ignore(否则拖累 ship-finalize
    step 7 ff-pull · 形成"主工作区永远 dirty")。

    v8.35 治本 2 个 case:
    - Bug B(用户问"自动升级是否符合预期" 2026-05-27):project_root == skill_root 时 skip
      · 防 bootstrap 修改 skill 仓自己 .gitignore · 导致 state.py update-skill 立即 BLOCK
      · 跨仓污染(只在开发 teamwork 自己时撞 · 用户项目场景不撞)
    - Bug C(同 case):连续同 header 的 entries 共用一个 header 注释 · 不重复打印
      · 实际看 .gitignore 时美观

    entries:(pattern, alt_pattern, header) · 连续相同 header 自动 dedup。
    """
    # v8.35 Bug B:skill_root 与 project_root 同一个 git 仓 → skip(防跨仓污染)
    # 2 种命中场景:
    #   a) project_root == skill_root(skill 仓就是 repo 根)
    #   b) skill_root 是 project_root 子目录 + 同一个 git 仓(skill 嵌在子目录 · 开发场景)
    # 判定:用 `git -C skill_root rev-parse --show-toplevel` 看是否等于 project_root
    if skill_root:
        try:
            pr_resolved = project_root.resolve()
            sr_resolved = skill_root.resolve()
            if pr_resolved == sr_resolved:
                return {"status": "skipped_skill_root_self",
                        "reason": ("project_root == skill_root · skill 仓自己 .gitignore "
                                   "由 skill 仓维护者管(v8.35 治本跨仓污染)")}
            # 检查二者是不是同一个 git 仓(skill 嵌子目录场景)
            r = subprocess.run(
                ["git", "-C", str(sr_resolved), "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0:
                sr_git_root = Path(r.stdout.strip()).resolve()
                if sr_git_root == pr_resolved:
                    return {"status": "skipped_skill_root_self",
                            "reason": (f"skill_root({sr_resolved}) 与 project_root({pr_resolved}) "
                                       "同一个 git 仓(skill 嵌子目录开发场景)· "
                                       "skip 防修改 skill 仓自己 .gitignore(v8.35 治本跨仓污染)")}
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass  # git 不可用 · 走原路径

    gitignore = project_root / ".gitignore"
    entries = [
        (".worktree/", ".worktree", "# Teamwork worktree root (default)"),
        (LOCALCONFIG_FILE, LOCALCONFIG_FILE, "# Teamwork local config + bootstrap state"),
        # v8.31:harness 锁文件(session pid · 历史 commit 误入)· 治本 INFRA-F025 G2
        (".claude/scheduled_tasks.lock", ".claude/scheduled_tasks.lock",
         "# Teamwork harness locks (session pid · 不该 commit · v8.31)"),
        (".claude/agents.lock", ".claude/agents.lock",
         "# Teamwork harness locks (session pid · 不该 commit · v8.31)"),
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
    last_header_written = None  # v8.35 Bug C:连续同 header dedup 状态机
    for pattern, pattern_alt, header in entries:
        if pattern in text or pattern_alt in lines:
            # 已存在 → 下一个新 entry 若与该 entry 同 header 仍需写 header
            # (因为前一行没写 header · 不重复)· 重置 last_header_written
            last_header_written = None
            continue
        prefix_nl = "\n" if text and not text.endswith("\n") else ""
        if header == last_header_written:
            # 与上一已写 entry 共用 header · 只写 pattern
            text += f"{prefix_nl}{pattern}\n"
        else:
            text += f"{prefix_nl}{header}\n{pattern}\n"
            last_header_written = header
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


# v8.24:skill 自更新检测(GitHub raw · 5s timeout silent · 落后 emit R5 1/2 选项)
# 治本 PMO 不知道何时升级 · 跨 session 长时间不更新错过治本
# v8.39(用户拍板 2026-05-27):支持 update_channel · 默认 main · dev 用于尝鲜
SKILL_UPDATE_RAW_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/okteam99/teamwork/{channel}/skills/teamwork/SKILL.md"
)
SKILL_UPDATE_DEFAULT_CHANNEL = "main"
SKILL_UPDATE_TIMEOUT_SEC = 5
SKILL_UPDATE_URL_ENV = "TEAMWORK_SKILL_UPDATE_URL"  # 测试覆盖用


def _read_update_channel(project_root: Optional[Path]) -> str:
    """v8.39:读 .teamwork_localconfig.json.update_channel · 默认 main。

    优先级:config update_channel(if str) > 默认 main
    损坏 config / 缺字段 / 非 string 类型 → 默认 main(silent · 不阻塞)
    """
    if not project_root:
        return SKILL_UPDATE_DEFAULT_CHANNEL
    try:
        cfg = read_localconfig(project_root)
        ch = cfg.get("update_channel")
        if isinstance(ch, str) and ch.strip():
            return ch.strip()
    except Exception:
        pass
    return SKILL_UPDATE_DEFAULT_CHANNEL


def _parse_skill_version(text: str) -> Optional[str]:
    """从 SKILL.md frontmatter 抽 version 字段值(`version: vX.Y`)· 失败返 None。"""
    import re
    # frontmatter 在文件顶部 · `---\n...version: vX.Y\n...---\n`
    m = re.search(r"^version:\s*(\S+)\s*$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return None


def _version_tuple(v: str) -> tuple:
    """v8.23 / v8.10 → (8, 23) / (8, 10) · 字符串 vs 字符串 ascii 比较错(10<9)"""
    import re
    m = re.match(r"^v?(\d+)\.(\d+)(?:\.(\d+))?$", v.strip())
    if not m:
        return (0, 0, 0)  # 无法 parse · 视作最低 · 不阻塞
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def check_skill_update(local_version: str,
                       channel: str = SKILL_UPDATE_DEFAULT_CHANNEL) -> dict:
    """v8.24:检测 GitHub 上 skill 最新 version · 与本地比较。
    v8.39:加 channel 参数(默认 main) · 支持 dev 等其他分支(用户 opt-in 尝鲜)。

    返回 dict:
      - status: up_to_date / outdated / network_failed / parse_failed
      - local_version / latest_version / channel
      - upgrade_prompt(若 outdated · R5 1/2 选项 markdown)
    """
    # URL:env override > template + channel
    url = os.environ.get(SKILL_UPDATE_URL_ENV) or SKILL_UPDATE_RAW_URL_TEMPLATE.format(
        channel=channel
    )

    # 用 curl(跨平台 + 无 python http 依赖)· 5s timeout · silent
    try:
        r = subprocess.run(
            ["curl", "-s", "-L", "--max-time", str(SKILL_UPDATE_TIMEOUT_SEC), url],
            capture_output=True, text=True, timeout=SKILL_UPDATE_TIMEOUT_SEC + 2,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return {
                "status": "network_failed",
                "local_version": local_version,
                "latest_version": None,
                "channel": channel,
                "url": url,
                "reason": f"curl exit={r.returncode} · {r.stderr.strip()[:80]}",
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return {
            "status": "network_failed",
            "local_version": local_version,
            "latest_version": None,
            "channel": channel,
            "url": url,
            "reason": f"curl 不可用 / 超时:{e}",
        }

    latest = _parse_skill_version(r.stdout)
    if not latest:
        return {
            "status": "parse_failed",
            "local_version": local_version,
            "latest_version": None,
            "channel": channel,
            "url": url,
            "reason": (
                f"线上 SKILL.md frontmatter 抽不出 version 字段(channel={channel} · "
                f"检查分支是否存在 / SKILL.md 路径是否正确)"
            ),
        }

    if _version_tuple(latest) <= _version_tuple(local_version):
        return {
            "status": "up_to_date",
            "local_version": local_version,
            "latest_version": latest,
            "channel": channel,
        }

    # outdated → emit R5 1/2 选项
    # v8.39:channel != main 时 prompt 标注尝鲜 channel(避免用户混淆)
    # v8.42:update 命令改 `python3 SKILL_ROOT/tools/update.py`(独立脚本 · 不再 state.py update-skill)
    channel_note = (
        f"(channel: **{channel}** · 默认 main · 配置在 "
        f"`.teamwork_localconfig.json.update_channel`)"
    )
    update_cmd = (
        "`python3 $SKILL_ROOT/tools/update.py`"
        if channel == SKILL_UPDATE_DEFAULT_CHANNEL
        else f"`python3 $SKILL_ROOT/tools/update.py --channel {channel}`"
    )
    prompt = (
        f"⏸️ teamwork skill 检测到新版本(本地 **{local_version}** · 线上 **{latest}**)"
        f"{channel_note}\n\n"
        "请选择:\n\n"
        "1. ✅ **升级** 💡 推荐\n"
        "   理由:获取治本 / 新功能 / bug fix\n"
        f"   动作:回 `1` → PMO 跑 {update_cmd}"
        "(git pull · 自动检测脏树 · 失败 BLOCK with hint)\n"
        "2. ⏭️ **本 session 跳过**\n"
        "   理由:正在赶进度 / 评估 changelog 后再决定\n"
        "   动作:回 `2` → 本 session 不再提示(下个 session bootstrap 仍会检测)\n\n"
        f"📚 决策参考:看 GitHub `docs/CHANGELOG.md` 顶部新增段了解变更"
        + (f"\n⚠️ channel=`{channel}` 是尝鲜分支 · 可能不稳定 · 评估后再升"
           if channel != SKILL_UPDATE_DEFAULT_CHANNEL else "")
    )
    return {
        "status": "outdated",
        "local_version": local_version,
        "latest_version": latest,
        "channel": channel,
        "upgrade_prompt": prompt,
    }


# v8.21:host audit · 跨 session 全局 host 记忆(治本 PMO 还要传 --host 心智)
# 落 ~/.teamwork/host_audit.json · state.py 跨命令自动读取 · PMO 心智 -1 参数
HOST_AUDIT_PATH_ENV = "TEAMWORK_HOST_AUDIT_PATH"


def _host_audit_path() -> Path:
    """host audit 落位 · 用户级跨项目(与 prepare_check_audit 同目录)。

    覆盖路径:TEAMWORK_HOST_AUDIT_PATH=<path>(测试用)。
    """
    override = os.environ.get(HOST_AUDIT_PATH_ENV)
    if override:
        return Path(override)
    return Path.home() / ".teamwork" / "host_audit.json"


def write_host_audit(host: str) -> bool:
    """v8.21:bootstrap 跑成功后写 host audit · external-review 等下游命令自动读取。

    单条记录(覆盖写 · 不 append)· 保留最新一次 bootstrap 的 host:
        {"host": "claude-code", "timestamp": "2026-05-25T..."}

    v8.36 DEPRECATED:全局 audit 跨 session 残留 · 治本 SVC-PLATFORM-F054 case
    (PMO 切到 Codex CLI 但 audit 残留 claude-code · 推出 model=codex 同源 · 异质失效)
    主路径已改 per-feature state.json.host(init-feature / stage-start 传 --host 写入)
    audit 仅作为 fallback 兼容路径 · v8.37 计划删除。
    """
    try:
        p = _host_audit_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps({
                "host": host,
                "timestamp": now_iso(),
                # v8.36:audit 标 deprecated · 下游 _detect_host 读到 emit deprecation_warning
                "_deprecated": (
                    "v8.36 → ~/.teamwork/host_audit.json 是 fallback 兼容路径 · "
                    "主路径请 init-feature/stage-start 传 --host 写 state.json.host · "
                    "v8.37 将删此全局文件"
                ),
            }, ensure_ascii=False, indent=2),
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
        gitignore = maintain_gitignore_worktree(project_root, skill_root)  # v8.35:传 skill_root · skip 跨仓污染
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
        # v8.14:forewarn AI 下游硬墙 · 治本 PTR-F054 prepare 跳过 case
        # 因果机制描述(非宣誓):AI 知道 init-feature 会 BLOCK · 主动先 prepare-check
        # 避免「直跑 init-feature → BLOCKED → 回头 prepare → 重跑」round-trip
        "flow_gates": [
            {
                "gate": "prepare_check_required_before_init_feature",
                "trigger": "state.py init-feature",
                "checks": (
                    "扫 ~/.teamwork/prepare_check_audit.jsonl · 找近 60min 匹配 "
                    "--feature-id 前缀的 record · 无 → BLOCKED"
                ),
                "action": (
                    "规划 Feature/Bug/Micro 时 · 先跑 `state.py prepare-check "
                    "--feature-id-prefix <PREFIX> --features-root <abs> --flow-type <type>` · "
                    "再 init-feature(prepare-check 输出含 next_available_id_stem · "
                    "暂停点表格直接填)"
                ),
                "skip_consequence": (
                    "init-feature 物化 FAIL · hint 指回 prepare-check · "
                    "跳过这一步等于浪费一轮 round-trip"
                ),
                "bypass_env": "TEAMWORK_BYPASS_PREPARE_CHECK=1(仅 debug / migration)",
                "spec": "docs/prepare.md § 0",
            }
        ],
    }

    # v8.47 + v8.48:冷启动检测 — teamwork-space.md 缺失 → forewarn 引导「产品规划优先」冷启动
    # v8.48 治本(用户 case 2026-05-29 · gcpdev):v8.47 gate 路由指错 —— 写「进 Feature Planning
    #   生成 teamwork-space.md」· 但 teamwork-space.md 不是 Feature Planning 产出的:权威流是
    #   product-overview(PL 引导模式)→ ✅确认派生 teamwork-space.md → 再 Feature Planning 拆 ROADMAP
    #   (PRODUCT-OVERVIEW-INTEGRATION.md:67)。gcpdev 已做 Feature Planning(PROJECT/ROADMAP)却跳过上游产品规划。
    # 用户决策:产品规划优先(权威流)· 一律引导 product-overview(用户可拒)· spec/wording 修正
    _AUTH_ORDER = ("product-overview(产品规划 · PL 引导模式)→ ✅确认 → teamwork-space.md(工作区全景)"
                   "→ Feature Planning(拆 ROADMAP)→ Feature 状态机")
    _po_exists = (project_root / "product-overview").is_dir()
    if not (project_root / "teamwork-space.md").exists():
        if _po_exists:
            # 已有 product-overview · 仅缺 teamwork-space → 从「✅ 已确认」内容派生(跳过 ① 初创)
            _cold_action = (
                "🔴 PMO 本 session 首次响应前 · emit R5 暂停点:本项目有 product-overview/ 但无 teamwork-space.md · "
                "从 product-overview「✅ 已确认」内容派生 teamwork-space.md(工作区全景索引)→ 再 Feature Planning 拆 ROADMAP。"
                "选项:1 派生 teamwork-space.md 💡 / 2 跳过直接做任务 / 3 其他"
            )
            _po_status = ("已存在 · 从其「✅ 已确认」内容派生 teamwork-space.md"
                          "(PRODUCT-OVERVIEW-INTEGRATION.md § 与 teamwork-space 关系)")
        else:
            # 全冷启动 · 无 product-overview 无 teamwork-space → 产品规划优先(权威流)
            _cold_action = (
                "🔴 PMO 本 session 首次响应前 · emit R5 暂停点引导用户:本项目未初始化 teamwork 工作区(无 teamwork-space.md)· "
                "权威冷启动顺序 = 产品规划优先:① 先建 product-overview/(PL 引导模式 · 产品定位/业务架构/执行手册 · "
                "见 PRODUCT-OVERVIEW-INTEGRATION.md 建议章节 + 裁剪规则)→ ② ✅确认后派生 teamwork-space.md → "
                "③ 再 Feature Planning 拆 ROADMAP。选项:1 进产品规划冷启动(建 product-overview)💡 / "
                "2 跳过直接做任务(单 Feature 快速场景 · 后续可补)/ 3 其他。"
                "🔴 即使项目已有 PROJECT/ROADMAP(说明跳过了上游产品规划)· 仍 surface 此引导(让用户决定是否补上游)"
            )
            _po_status = "也缺失 · 冷启动第一步就是建它(产品规划上游 · teamwork-space.md 由其「✅ 已确认」内容派生)"
        result["flow_gates"].append({
            "gate": "cold_start_workspace_uninitialized",
            "trigger": "session 启动 · 本项目无 teamwork-space.md(工作区未初始化 · 新项目冷启动)",
            "checks": "project_root 无 teamwork-space.md · teamwork 项目应有(由 product-overview ✅确认内容派生 · 含子项目清单 + 待规划需求池)",
            "action": _cold_action,
            "skip_consequence": (
                "跳过可直接做任务(用户拍板)· 但缺产品规划上游 + 工作区清单 → 多子项目管理 / 待规划需求池 / "
                "跨项目变更追踪 / 执行线对齐 缺失 · 后续可随时补"
            ),
            "product_overview_status": _po_status,
            "authoritative_order": _AUTH_ORDER,
            "spec": ("PRODUCT-OVERVIEW-INTEGRATION.md(产品规划权威 · 引导模式建 product-overview)"
                     "+ docs/feature-planning.md + templates/teamwork-space.md"),
        })

    # v8.46 A:检测 product-overview/ → flow_gates 加规划规范 gate(治本 Feature Planning 未物化漏洞)
    # 根因:Feature Planning 不进状态机 · 无 state.py 兜底 · PRODUCT-OVERVIEW-INTEGRATION.md 纯靠 AI 自觉读
    # session 启动时若项目有 product-overview/ · forewarn AI 规划类任务必读规范 + 跑 planning-check
    if _po_exists:
        result["flow_gates"].append({
            "gate": "product_overview_planning_spec_required",
            "trigger": "Feature Planning / 规划类任务(拆 ROADMAP · 更新 product-overview · 商业模式调整)",
            "checks": (
                "本项目存在 product-overview/ · 规划有独立状态机"
                "(📝草稿 / 🔄讨论中 / ⏸️待确认 / ✅已确认)· 不进 teamwork stage 状态机"
            ),
            "action": (
                "规划类任务**先跑** `state.py planning-check --project-root <abs>`(emit 规划状态 "
                "checklist + 必读规范)· 必读 PRODUCT-OVERVIEW-INTEGRATION.md(加载规则 + 状态管理 + "
                "议题追踪)· 维护规划状态表 · 仅「✅ 已确认」内容才影响 teamwork-space.md / 下游执行"
            ),
            "skip_consequence": (
                "AI 没读规范 → 不维护规划状态表 / 草稿态内容误影响下游 / 议题追踪缺失。"
                "Feature Planning 不进状态机 · 无 stage 物化兜底 · 这是 v8 物化盲区(v8.46 用 gate 提示补)"
            ),
            "spec": "PRODUCT-OVERVIEW-INTEGRATION.md + docs/feature-planning.md",
        })

    # v8.21:写 host audit(跨 session 全局 host 记忆 · 治本 PMO 还要传 --host 心智)
    # 下游命令(state.py external-review 等)自动读 · PMO 不需要再传 --host
    host_audit_ok = write_host_audit(args.host)
    result["checks"]["host_audit"] = {
        "status": "written" if host_audit_ok else "write_failed",
        "path": str(_host_audit_path()),
    }

    # v8.24:检测 GitHub 上 skill 最新版本 · 落后 emit R5 1/2 选项暂停点
    # 网络失败 silent skip 不阻塞 bootstrap · 治本 PMO 不知何时升级
    # v8.39:加 channel 支持(默认 main · 用户可配 .teamwork_localconfig.json.update_channel)
    if skill_version:
        channel = _read_update_channel(project_root)
        result["checks"]["skill_update_check"] = check_skill_update(skill_version, channel)
    else:
        result["checks"]["skill_update_check"] = {
            "status": "skipped",
            "reason": "本地 skill_version 探测失败 · 无法比较",
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
