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

# v8.89:本地敏感配置统一目录(kubeconfig / DB 密码 / 个人 API key)· 双重 gitignore · 不进仓库
LOCAL_ENV_DIR = ".teamwork-local-env"
LOCAL_ENV_CONFIG = "config.properties"
LOCAL_ENV_DIR_GITIGNORE = (
    "# teamwork: 本目录全部内容禁提交(双重保险 · 即便项目根 .gitignore 漏掉本目录)\n"
    "*\n"
)


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
        # v8.96:人维护的项目开发规范(分层/命名/错误处理/测试/风格)· blueprint+dev 必读 ·
        # 与 KNOWLEDGE(AI 沉淀)分家。absent→从模板建;present→不动(人维护)。
        ("DEV-RULES.md", "dev-rules.md"),
        # v8.117:workspace 级系统架构(子项目拓扑+依赖+目录布局)· 从 teamwork-space.md 外迁 ·
        # 区别于 per-subproject {子项目}/docs/architecture/(单子项目内部技术架构)。
        ("ARCHITECTURE.md", "architecture-workspace.md"),
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


# ─── v8.116:teamwork-space.md(知识地图根)自动建骨架 ──────────
#
# N≥1 统一模型:任何 teamwork 项目都有 teamwork-space.md(单项目=1 子项目 · 不再"单项目可无")。
# 🔴 骨架 = **地图**(知识入口自动探测 + 子项目清单待规划填充)· 子项目 taxonomy 由
# product-overview「✅ 已确认」+ Feature Planning 回填(派生关系不变)。已存在 → 不动(幂等)。


def _kg_entry_rows(project_root: Path) -> list:
    """知识入口表行 —— **仅为磁盘上存在**的知识节点生成指针(零死角 · 不存在不留空指针)。"""
    rows = []
    nodes = [
        ("product-overview", "产品规划", "[`product-overview/`](product-overview/)",
         "业务架构+执行线 · workstream/ · PENDING.md"),
        ("project-specs", "工程规范(workspace)", "[`project-specs/`](project-specs/)",
         "DEV-RULES · KNOWLEDGE · GLOSSARY · TROUBLESHOOTING · RESOURCES"),
        ("external", "三方 / 外部", "[`external/`](external/)", "SDK · 协议 · 供应商文档"),
    ]
    for d, label, link, contains in nodes:
        if (project_root / d).is_dir():
            rows.append(f"| {label} | {link} | {contains} |")
    if (project_root / "project-specs" / "ARCHITECTURE.md").is_file():
        rows.append("| 系统架构(workspace) | [`project-specs/ARCHITECTURE.md`](project-specs/ARCHITECTURE.md) | "
                    "子项目拓扑 + 依赖 + 目录布局 |")
    has_archive = (project_root / "docs" / "features" / "_archive").is_dir() or \
        any(project_root.glob("*/docs/features/_archive"))
    if has_archive:
        rows.append("| 归档冷库 | `{子项目}/docs/features/_archive/INDEX.md`(每子项目 docs_root) | "
                    "已交付 feature(id+描述+zip)· 先读描述 · 必要才解压 |")
    return rows


def maintain_teamwork_space(skill_root: Path, project_root: Path) -> dict:
    """teamwork-space.md 缺失 → 自动建**精简骨架**(知识入口自动探测 + 子项目清单空表待填)。

    🔴 子项目清单**空表** → state.py 路由校验 SKIP(填入后才生效)· 不误阻断。
    已存在 → 不动(幂等 · 含用户/规划已填充内容)。
    """
    target = project_root / "teamwork-space.md"
    if target.exists():
        return {"status": "existed"}
    entry_rows = _kg_entry_rows(project_root)
    entry_block = "\n".join(entry_rows) if entry_rows else \
        "| (暂无 workspace 知识节点) | — | bootstrap 探测到即补 |"
    content = (
        "# Teamwork Space\n\n"
        "> **本项目知识地图根 · 索引之索引** · 任何 session 先读本文件 → 指向每个知识节点"
        "(子项目 / 规划 / 工程文档 / 三方 / 归档冷库)· **代码是细节唯一真相**。\n"
        "> 🔴 变更需用户确认(R5)· 任一单元格 ≤ 1 行 · 维护规范 → "
        "`docs/teamwork-space-guide.md`(随 skill · 不复制进项目)。\n"
        "> 🔴 本文件 bootstrap **自动建骨架** · 子项目清单 / 规划章节由 product-overview"
        "「✅ 已确认」+ Feature Planning 回填(派生关系不变)。\n\n"
        "## 知识入口（索引之索引 · 零死角）\n\n"
        "<!-- 🔴 每个磁盘上存在的知识节点一行指针 · 漏一个 = 知识泄露死角 · bootstrap 自动探测维护 -->\n\n"
        "| 知识域 | 入口 | 内含 |\n"
        "|--------|------|------|\n"
        f"{entry_block}\n"
        "| 代码（唯一真相） | `grep` + `Read` 源码 | 🔴 细节一律现查代码 · 不信文档转述 |\n\n"
        "## 子项目清单（路由权威 · 待规划填充）\n\n"
        "<!-- 🔴 docs_root 必填(路由权威)· 由 product-overview ✅确认 + Feature Planning 拆分后"
        "填入 · 单项目 = 1 行 · **空表时 state.py 路由校验 SKIP**(填入后才生效) -->\n\n"
        "| 缩写 | 名称 | 类型 | 职责范围 | docs_root | 承接执行线 | 技术栈 | 需要 UI | 消费方 | 完成度 |\n"
        "|------|------|------|----------|-----------|-----------|--------|---------|--------|--------|\n"
        "<!-- 待规划填充:此处尚无子项目行 → 路由校验 SKIP -->\n\n"
        "---\n\n"
        "> 完整结构(规划状态 / 执行线 / 待规划池 / 跨项目变更)见模板 `templates/teamwork-space.md` + guide · "
        "**系统架构**(子项目拓扑/依赖/目录)→ `project-specs/ARCHITECTURE.md`(已外迁)· 规划期按需补。\n"
    )
    try:
        target.write_text(content, encoding="utf-8")
        return {"status": "created", "knowledge_entries": len(entry_rows)}
    except OSError as e:
        return {"status": "failed", "reason": str(e)}


# ─── 本地敏感配置目录 .teamwork-local-env/(v8.89) ──────────


def maintain_local_env(skill_root: Path, project_root: Path) -> dict:
    """v8.89:本地敏感配置统一目录 `.teamwork-local-env/`(kubeconfig / DB 密码 / API key)。

    用户拍板:统一一个 gitignored 目录放本机敏感配置 · 别散落 · session 初始化自动创建。
    - 缺失 → 自动建目录 + `config.properties` 模板(注释示例 · **无真密钥**)+ 目录内
      `.gitignore`(`*` · 防御纵深:即便项目根 .gitignore 漏 / 子 repo 也不泄密)。
    - 已存在 → **skip**(绝不覆盖用户真 secret)· 仅补缺失的目录内 .gitignore(历史目录加固)。
    - skill 仓自身 → skip(同其他 maintain · 不污染 skill repo · v8.35)。
    - localconfig `local_env_auto_create: false` → disabled(opt-out)。
    根 `.gitignore` 加 `.teamwork-local-env/` 由 `maintain_gitignore_worktree` 负责(双重保险其一)。
    """
    try:
        if project_root.resolve() == skill_root.resolve():
            return {"status": "skipped_skill_root", "dir": LOCAL_ENV_DIR}
    except OSError:
        pass
    # opt-out:localconfig local_env_auto_create:false
    try:
        cfg = project_root / LOCALCONFIG_FILE
        if cfg.exists():
            data = json.loads(cfg.read_text(encoding="utf-8"))
            if data.get("local_env_auto_create") is False:
                return {"status": "disabled", "dir": LOCAL_ENV_DIR}
    except (OSError, json.JSONDecodeError):
        pass

    env_dir = project_root / LOCAL_ENV_DIR
    cfg_file = env_dir / LOCAL_ENV_CONFIG
    dir_gitignore = env_dir / ".gitignore"
    created: list = []
    try:
        if env_dir.exists():
            # 已存在 → 不覆盖 secret · 仅补目录内 .gitignore(历史目录可能没有 · 加固)
            if not dir_gitignore.exists():
                dir_gitignore.write_text(LOCAL_ENV_DIR_GITIGNORE, encoding="utf-8")
                created.append(".gitignore")
            return {"status": "existed", "dir": LOCAL_ENV_DIR, "created": created}
        env_dir.mkdir(parents=True, exist_ok=True)
        # 目录内 .gitignore(防御纵深 · 先写 · 确保任何后续写入都已被 ignore)
        dir_gitignore.write_text(LOCAL_ENV_DIR_GITIGNORE, encoding="utf-8")
        created.append(".gitignore")
        # config.properties 模板(无真密钥)
        template = skill_root / "templates" / "local-env-config.properties"
        if template.exists():
            shutil.copy(template, cfg_file)
        else:
            cfg_file.write_text(
                "# teamwork 本地敏感配置 · 绝不提交 git(KEY=value)\n", encoding="utf-8")
        created.append(LOCAL_ENV_CONFIG)
        return {"status": "created", "dir": LOCAL_ENV_DIR, "created": created}
    except OSError as e:
        return {"status": "failed", "dir": LOCAL_ENV_DIR, "error": str(e)}


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
        # v8.85:external review reviewer 写的 liveness 标记(state.py 跑完会清 · 兜底防残留误入)
        ("review_start.log", "review_start.log",
         "# Teamwork external-review liveness marker (transient · v8.85)"),
        # v8.89:本地敏感配置目录(kubeconfig/密码/API key · 双重保险 · 目录内另有 .gitignore)
        (LOCAL_ENV_DIR + "/", LOCAL_ENV_DIR + "/",
         "# Teamwork local sensitive config dir (secrets · 绝不提交 · v8.89)"),
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


# v8.91:localconfig schema 自愈默认值(缺字段补上 · 尤其 _bootstrap 段 + 新增 feature 开关)
# 🔴 与 templates/teamwork_localconfig.json 保持同步(新增字段两处都加)。
LOCALCONFIG_CONFIG_DEFAULTS = {
    "worktree": "auto",
    "worktree_root_path": ".worktree",
    "scope": "all",
    "merge_target": "staging",
    "worktree_cleanup": "ask",
    "mr_url_template": None,
    "id_strategy": "utc-yymmddhhmmss",
    "archive_on_ship": True,
    "local_env_auto_create": True,
    "disable_external_review": False,
}
LOCALCONFIG_BOOTSTRAP_DEFAULTS = {
    "skill_version": None,
    "host": None,
    "last_maintain_at": None,
    "last_maintain_results": {},
}


def ensure_localconfig_complete(project_root: Path, skill_root: Path) -> dict:
    """v8.91:bootstrap 启动自愈 localconfig —— 缺的已知字段补默认值(尤其 `_bootstrap` 段)。

    治本:localconfig 由**老版 bootstrap / 手建 / 部分写入** 时 · `_bootstrap` 子键或新增
    feature 开关(archive_on_ship / disable_external_review 等)缺失 · 且版本命中
    skip_maintain 时这些缺口**永不补** · 用户也看不到新选项。
    - 仅 **additive**:只补缺的键 · **绝不覆盖**用户已有值(含显式 false/null)。
    - 仅当 localconfig **已存在**时跑(不存在 = 冷启动 · 由 maintain / prepare 创建 · 不在此凭空造)。
    - skill 仓自身 skip(同其他 maintain · v8.35)。无变化不写盘(防 churn)。
    返回 {status, added_config:[...], added_bootstrap:[...]}。
    """
    try:
        if project_root.resolve() == skill_root.resolve():
            return {"status": "skipped_skill_root"}
    except OSError:
        pass
    cfg_path = project_root / LOCALCONFIG_FILE
    if not cfg_path.exists():
        return {"status": "skipped_absent"}  # 冷启动 · 不在此创建(prepare/maintain 负责)
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "skipped_unreadable"}  # 损坏 · 不强改(避免覆盖用户内容)
    if not isinstance(data, dict):
        return {"status": "skipped_not_object"}

    added_config = [k for k in LOCALCONFIG_CONFIG_DEFAULTS if k not in data]
    for k in added_config:
        data[k] = LOCALCONFIG_CONFIG_DEFAULTS[k]
    bs = data.get("_bootstrap")
    if not isinstance(bs, dict):
        bs = {}
        data["_bootstrap"] = bs
    added_bootstrap = [k for k in LOCALCONFIG_BOOTSTRAP_DEFAULTS if k not in bs]
    for k in added_bootstrap:
        bs[k] = LOCALCONFIG_BOOTSTRAP_DEFAULTS[k]

    if not added_config and not added_bootstrap:
        return {"status": "complete"}
    try:
        cfg_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as e:
        return {"status": "write_failed", "error": str(e),
                "added_config": added_config, "added_bootstrap": added_bootstrap}
    return {"status": "backfilled", "added_config": added_config,
            "added_bootstrap": added_bootstrap}


# v8.24:skill 自更新检测(GitHub raw · 5s timeout silent · 落后 emit R5 1/2 选项)
# 治本 PMO 不知道何时升级 · 跨 session 长时间不更新错过治本
# v8.39(用户拍板 2026-05-27):支持 update_channel · 默认 main · dev 用于尝鲜
SKILL_UPDATE_RAW_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/okteam99/teamwork/{channel}/skills/teamwork/SKILL.md"
)
SKILL_UPDATE_DEFAULT_CHANNEL = "main"
SKILL_UPDATE_TIMEOUT_SEC = 5
SKILL_UPDATE_URL_ENV = "TEAMWORK_SKILL_UPDATE_URL"  # 测试覆盖用
# v8.142:升级提示带变更描述(拉线上 CHANGELOG 抽标题行)
SKILL_UPDATE_CHANGELOG_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/okteam99/teamwork/{channel}/skills/teamwork/docs/CHANGELOG.md"
)
SKILL_UPDATE_CHANGELOG_URL_ENV = "TEAMWORK_SKILL_CHANGELOG_URL"  # 测试覆盖用
SKILL_UPDATE_CHANGELOG_MAX_TITLES = 8


def _fetch_changelog_titles(channel: str, local_version: str) -> Optional[dict]:
    """v8.142:升级提示带变更描述 —— 拉线上 CHANGELOG.md · 抽「本地版本之后」各版标题行。

    标题行即蒸馏摘要(发版纪律:`## v8.NNN · <一行描述>`)· 不带 body(暂停点须可读 ·
    详情仍指 CHANGELOG)。CHANGELOG 顶部新→旧有序 · 扫到 <= 本地版本即停。
    🔴 best-effort:网络/解析失败返 None · 提示降级回「去看 CHANGELOG」指针 · 绝不阻塞。
    注意 keep-5 轮转:落后 >5 版时线上只剩最近 5 版标题 · 加「更早见 git 历史」注。
    返 {"titles": [...], "note": str|None}。
    """
    import re
    url = os.environ.get(SKILL_UPDATE_CHANGELOG_URL_ENV) or \
        SKILL_UPDATE_CHANGELOG_URL_TEMPLATE.format(channel=channel)
    try:
        r = subprocess.run(
            ["curl", "-s", "-L", "--max-time", str(SKILL_UPDATE_TIMEOUT_SEC), url],
            capture_output=True, text=True, timeout=SKILL_UPDATE_TIMEOUT_SEC + 2,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    local_t = _version_tuple(local_version)
    titles: list = []
    reached_local = False  # 扫到 <= 本地的条目 = 覆盖无断档(keep-5 未轮转掉中间版本)
    for line in r.stdout.splitlines():
        if not line.startswith("## "):
            continue
        m = re.match(r"^##\s+(v[\d.]+)\s*[·:]?\s*(.*)$", line)
        if not m:
            continue
        ver, title = m.group(1), m.group(2).strip()
        if _version_tuple(ver) <= local_t:
            reached_local = True
            break
        titles.append(f"{ver} · {title}" if title else ver)
    if not titles:
        return None
    note = None
    if len(titles) > SKILL_UPDATE_CHANGELOG_MAX_TITLES:
        note = f"…共 {len(titles)} 版新增 · 仅列最近 {SKILL_UPDATE_CHANGELOG_MAX_TITLES} · 全量见 CHANGELOG"
    elif not reached_local:
        note = "(线上 CHANGELOG 仅存最近 5 版 · 你落后更多 · 更早变更见 git 历史)"
    return {"titles": titles[:SKILL_UPDATE_CHANGELOG_MAX_TITLES], "note": note}


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
    # v8.142:带变更描述(线上 CHANGELOG 标题行 · best-effort · 失败降级回指针)
    channel_note = (
        f"(channel: **{channel}** · 默认 main · 配置在 "
        f"`.teamwork_localconfig.json.update_channel`)"
    )
    update_cmd = (
        "`python3 $SKILL_ROOT/tools/update.py`"
        if channel == SKILL_UPDATE_DEFAULT_CHANNEL
        else f"`python3 $SKILL_ROOT/tools/update.py --channel {channel}`"
    )
    changelog = _fetch_changelog_titles(channel, local_version)
    changes_block = ""
    if changelog:
        bullets = "\n".join(f"- {t}" for t in changelog["titles"])
        tail = f"\n{changelog['note']}" if changelog["note"] else ""
        changes_block = f"\n本次升级包含:\n{bullets}{tail}\n"
    prompt = (
        f"⏸️ teamwork skill 检测到新版本(本地 **{local_version}** · 线上 **{latest}**)"
        f"{channel_note}\n"
        f"{changes_block}\n"
        "请选择:\n\n"
        "1. ✅ **升级** 💡 推荐\n"
        "   理由:获取治本 / 新功能 / bug fix\n"
        f"   动作:回 `1` → PMO 跑 {update_cmd}"
        "(git pull · 自动检测脏树 · 失败 BLOCK with hint)\n"
        "2. ⏭️ **本 session 跳过**\n"
        "   理由:正在赶进度 / 评估 changelog 后再决定\n"
        "   动作:回 `2` → 本 session 不再提示(下个 session bootstrap 仍会检测)\n\n"
        + ("📚 决策参考:各版详情见 GitHub `docs/CHANGELOG.md`" if changelog
           else "📚 决策参考:看 GitHub `docs/CHANGELOG.md` 顶部新增段了解变更")
        + (f"\n⚠️ channel=`{channel}` 是尝鲜分支 · 可能不稳定 · 评估后再升"
           if channel != SKILL_UPDATE_DEFAULT_CHANNEL else "")
    )
    return {
        "status": "outdated",
        "local_version": local_version,
        "latest_version": latest,
        "channel": channel,
        "upgrade_prompt": prompt,
        # v8.142:机器可读变更标题(None = changelog 拉取失败 · prompt 已降级)
        "changelog_titles": changelog["titles"] if changelog else None,
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


# ─── v8.115:知识图谱结构可达性校验(零死角物化 · WARN-only · 非 BLOCK)─────
#
# 🔴 只查**结构可达性**(归档对账 + 节点登记)· **不查内容新鲜度**
# (内容 = 代码唯一真相 + 人/AI 维护 · checker 不碰 —— 否则 checker 通过会被误读成
# 「知识完整/最新」· 自己成误导信号 · 违 v8.105「信号≠判决」)。teamwork-space.md
# 缺失 → skip(cold-start gate 另管 · 不重复报)。


def _find_archive_dirs(project_root: Path) -> list:
    """归档目录 `_archive/` · **有界**查找(子项目直接放根下 · 不深递归 node_modules)。"""
    cands = [project_root / "docs" / "features" / "_archive"]
    try:
        cands.extend(project_root.glob("*/docs/features/_archive"))
    except OSError:
        pass
    return [d for d in cands if d.is_dir()]


def _parse_archive_index_ids(index_md: Path) -> list:
    """解析归档 INDEX.md 数据行 → feature_id(col 0)列表。格式 = _v8_ship._build_archive_index。"""
    ids = []
    try:
        for line in index_md.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not cells or cells[0] in ("Feature", "---", ""):
                continue
            ids.append(cells[0])
    except OSError:
        pass
    return ids


def check_knowledge_graph_integrity(project_root: Path) -> dict:
    """teamwork-space.md 知识图谱**结构可达性**校验(WARN-only · 非 BLOCK)。

    查:① 归档 `INDEX.md` ↔ `*.zip` 双向对账(孤儿 zip / 悬空行 = 翻不到的死角)
        ② workspace 知识节点登记(`product-overview`/`project-specs`/`external` 存在
           于磁盘 → 必在 teamwork-space.md 提及 · 缺 = 知识入口死角)。
    🔴 **不查内容新鲜度**(只保证「可达」· 不保证「最新」· 内容 = 代码唯一真相)。
    """
    space = project_root / "teamwork-space.md"
    if not space.exists():
        return {"status": "skipped", "reason": "无 teamwork-space.md(cold-start gate 另管)"}

    leaks = []

    # (1) 归档 INDEX ↔ zip 双向对账
    for adir in _find_archive_dirs(project_root):
        index_md = adir / "INDEX.md"
        indexed = set(_parse_archive_index_ids(index_md)) if index_md.exists() else set()
        try:
            zips = {p.stem for p in adir.glob("*.zip")}
        except OSError:
            zips = set()
        try:
            rel = adir.relative_to(project_root)
        except ValueError:
            rel = adir
        for orphan in sorted(zips - indexed):
            leaks.append(f"归档孤儿:{rel}/{orphan}.zip 无 INDEX.md 登记(已交付但翻不到)")
        for dangling in sorted(indexed - zips):
            leaks.append(f"归档悬空:{rel}/INDEX.md 有 {dangling} 行但 {dangling}.zip 缺失(断指针)")

    # (2) workspace 知识节点登记(磁盘存在 → 必在地图提及)
    try:
        space_text = space.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        space_text = ""
    for node in ("product-overview", "project-specs", "external"):
        if (project_root / node).is_dir() and node not in space_text:
            leaks.append(f"节点未登记:{node}/ 存在但 teamwork-space.md 未提及(知识入口死角)")

    if leaks:
        return {
            "status": "leaks_found",
            "leak_count": len(leaks),
            "leaks": leaks,
            "scope_note": "🔴 仅结构可达性(断指针/归档对账/节点登记)· **不代表内容最新**(内容=代码唯一真相)",
        }
    return {"status": "ok", "note": "结构可达性零死角(不含内容新鲜度)"}


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
    workspace_file = maintain_workspace_filename(project_root)  # legacy 下划线名迁移(先)
    space_skeleton = maintain_teamwork_space(skill_root, project_root)  # v8.116:地图根自动建(后)
    local_env = maintain_local_env(skill_root, project_root)  # v8.89:本地敏感配置目录
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

    # v8.91:localconfig schema 自愈 —— 缺字段(尤其 _bootstrap 段 + 新增 feature 开关)补默认值。
    # 跑在 maintain 之后(无论 skip 与否)· 覆盖「版本命中 skip_maintain 时缺口永不补」的洞 ·
    # additive 不覆盖用户值 · 不存在不创建 · 无变化不写盘。
    localconfig_backfill = ensure_localconfig_complete(project_root, skill_root)

    result = {
        "verdict": "PASS",  # silent · 总是 PASS · 不阻塞
        "command": "session-bootstrap",
        "timestamp": now_iso(),
        "host": args.host,
        "skill_root": str(skill_root),
        "skill_version": skill_version,
        "project_root": str(project_root),
        "maintain_status": maintain_status,
        "localconfig_backfill": localconfig_backfill,
        "marker_skill_version_before": marker_version,
        "checks": {
            "skill_version": version_check,
            "skeletons": skeletons,
            "workspace_filename": workspace_file,
            "teamwork_space": space_skeleton,  # v8.116:知识地图根自动建骨架
            "local_env": local_env,  # v8.89:本地敏感配置目录 .teamwork-local-env/
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

    # v8.116:cold-start 解耦 —— teamwork-space.md(地图)已 bootstrap 自动建(maintain_teamwork_space)·
    #   gate 不再 fire 于「无 teamwork-space.md」(地图自动有)· 改 fire 于「无 product-overview」
    #   (产品规划上游缺失)· 保留 planning nudge(reframe)。地图 ≠ 规划:地图自动建 · 规划要人建。
    #   承 v8.48 决策(产品规划优先)· teamwork-space.md 子项目清单仍由 product-overview ✅确认回填。
    _AUTH_ORDER = ("product-overview(产品规划 · PL 引导模式)→ ✅确认 → 回填 teamwork-space.md 子项目清单"
                   "(地图骨架已自动建)→ Feature Planning(拆 ROADMAP)→ Feature 状态机")
    _po_exists = (project_root / "product-overview").is_dir()
    _space_created = space_skeleton.get("status") == "created"
    if not _po_exists:
        result["flow_gates"].append({
            "gate": "cold_start_product_planning_recommended",
            "trigger": ("session 启动 · 本项目无 product-overview/(产品规划上游缺失)· "
                        "teamwork-space.md 地图骨架已 bootstrap 自动维护"),
            "checks": ("project_root 无 product-overview/ · teamwork 面向复杂业务 · 建议补产品规划上游"
                       "(愿景 / 业务架构 / 执行线列表)· 地图根 teamwork-space.md 已自动建"
                       "(知识入口已探测 · 子项目清单待规划回填 · 空表时路由校验 SKIP)"),
            "action": (
                "🔴 PMO 本 session 首次响应前 emit R5 暂停点:地图根 teamwork-space.md 已自动建"
                + ("(本 session 新建骨架)" if _space_created else "(已存在)")
                + " · 但缺**产品规划上游** product-overview/(愿景/业务架构/执行线)· 选项:"
                "1 进产品规划冷启动(PL 引导建 product-overview → ✅确认 → 回填 teamwork-space.md 子项目清单)💡 / "
                "2 跳过直接做任务(单 Feature 快速 · 后续可补)/ 3 其他。"
                "🔴 即使已有 PROJECT/ROADMAP(说明跳过了上游产品规划)· 仍 surface(让用户决定补否)"
            ),
            "skip_consequence": (
                "跳过可直接做任务(用户拍板)· 但缺产品规划上游 → 多子项目 taxonomy / 待规划需求池 / "
                "执行线对齐 / 跨项目追踪 缺失 · teamwork-space.md 子项目清单留空(路由校验 SKIP)· 后续可随时补"
            ),
            "teamwork_space_status": space_skeleton.get("status"),
            "authoritative_order": _AUTH_ORDER,
            "spec": ("PRODUCT-OVERVIEW-INTEGRATION.md(产品规划权威 · 引导模式建 product-overview)"
                     "+ docs/feature-planning.md"),
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

    # v8.51:session 入口优先级(治本 gcpdev case 2026-05-29 · PMO 把升级/补规划降成脚注 · 优先级倒置)
    # 物化:把"先升级 → 再补规划 → 最后任务"写进 bootstrap 输出 · AI 跑完即见 · 不靠记 SKILL.md
    _su_status = result["checks"].get("skill_update_check", {}).get("status")
    _has_cold_start = any(g.get("gate") == "cold_start_product_planning_recommended"
                          for g in result.get("flow_gates", []))
    if _su_status == "outdated" or _has_cold_start:
        _priority = []
        if _su_status == "outdated":
            _priority.append(
                "① 升级:skill 落后(见 checks.skill_update_check.upgrade_prompt)· 🔴 最先处理 · "
                "旧版 = 跑旧行为(规划/冷启动逻辑本身可能已被新版治掉 · 旧版上补规划会白补)"
            )
        if _has_cold_start:
            _priority.append(
                "② 补规划:缺产品规划上游 product-overview(见 flow_gates.cold_start_product_planning_recommended)· 升级处理完(或用户忽略)再做"
            )
        _priority.append("③ 任务:triage / 启动 Feature / 看板 · 前面处理完或用户明确跳过才轮到")
        result["session_entry_priority"] = {
            "order": _priority,
            "rule": "🔴 PMO 首条响应按此序 · 不可把 ①/② 降成底部「维护提醒」脚注(治本优先级倒置)",
        }

    # v8.90:异质评审被 localconfig 禁用 → 每次启动 WARN(交叉 review 质量下降 · 建议恢复)
    _ext_disabled = (read_localconfig(project_root).get("disable_external_review") is True
                     or read_localconfig(project_root).get("disable_heterogeneous_review") is True)  # 旧名兼容
    result["checks"]["heterogeneous_review"] = {
        "status": "disabled" if _ext_disabled else "enabled",
        **({"warning": (
            "⚠️ 已禁用 external 评审(disable_external_review=true)· external 评审降级为同模型 "
            "exec 自审 · **交叉 review 质量下降**(同盲点 · 漏检风险↑)· 强烈建议改 "
            ".teamwork_localconfig.json 恢复异质(删该项 / 设 false · 装好第二个模型 CLI 后)")}
            if _ext_disabled else {}),
    }

    # v8.115:知识图谱结构可达性(零死角物化 · WARN-only · 不进 flow_gates/priority · 不劫持升级>规划>任务序)
    result["checks"]["knowledge_graph"] = check_knowledge_graph_integrity(project_root)

    # v8.60:截断鲁棒 digest —— 关键 forewarn(升级 / flow_gates / 优先级)在 JSON 后位 ·
    # AI 习惯 `| head` 截断会吞掉(实证 case:`bootstrap.py | head -50` 吞掉 skill_update_check
    # → PMO 漏升级提示)。把 1 行 digest 提到输出**顶部**(survive `head -5`)+ 显式禁截断警告。
    _mr = ["⚠️ 本输出是结构化 JSON · PMO 必**完整读** · 禁 `| head`/`tail`/`sed` 截断"
           "(关键 forewarn 在 JSON 后位 · 截断必吞)"]
    _suc = result.get("checks", {}).get("skill_update_check", {})
    if _suc.get("status") == "outdated":
        _mr.append(
            f"🔴 ① skill OUTDATED {_suc.get('local_version')}→{_suc.get('latest_version')}"
            f" · 跑 update.py --channel {_suc.get('channel', 'main')}(最先处理)")
    elif _suc.get("status") == "up_to_date":
        _mr.append(f"skill ✅ {_suc.get('local_version')}")
    if _ext_disabled:
        _mr.append("🔴 external 评审已禁用(disable_external_review=true)· 交叉 review 降级为"
                   "同模型自审 · PMO 须告知用户(见 checks.heterogeneous_review · 建议恢复异质)")
    _kg = result.get("checks", {}).get("knowledge_graph", {})
    if _kg.get("status") == "leaks_found":
        _mr.append("🔴 知识图谱 %d 个结构死角(见 checks.knowledge_graph.leaks)· "
                   "断指针/归档孤儿/未登记节点 ≠ 内容陈旧 · 修可达性后零死角"
                   % _kg.get("leak_count", 0))
    _gates = result.get("flow_gates", [])
    if _gates:
        _mr.append("🔴 flow_gates(%d): %s → 逐条读 flow_gates[] 响应"
                   % (len(_gates), ", ".join(g.get("gate", "?") for g in _gates)))
    _sep = result.get("session_entry_priority", {})
    if _sep.get("order"):
        _mr.append("session_entry_priority: %s(见 session_entry_priority.order)"
                   % " / ".join(o.split(":")[0].strip() for o in _sep["order"]))
    # 重排:pmo_must_read 紧跟 command(头部 · 即使 AI 截断输出也能见)
    result = {"verdict": result.get("verdict"), "command": result.get("command"),
              "pmo_must_read": " · ".join(_mr), **result}

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
