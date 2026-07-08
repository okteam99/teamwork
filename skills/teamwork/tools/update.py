#!/usr/bin/env python3
"""
tools/update.py — Teamwork skill 自更新独立脚本(v8.42 抽离 · v8.44.3 重设计)。

设计哲学:
- **职责分离**:更新代码(元工具)与运行时代码(state.py · stage 状态机)解耦
- **与 bootstrap.py pattern 对齐**:bootstrap 是 setup 元工具 · update 是 upgrade 元工具 · 同级独立
- **chicken-and-egg 隔离**:若 state.py 自身坏掉 · update.py 仍能跑救命
- **架构去 git 化**(v8.41 用户拍板):tarball download + 解压覆盖 · 不依赖 git
- **默认 backup + overwrite**(v8.44.3 用户拍板):删 BLOCK · 改默认安全 · 不再二次问用户

行为要点:
- **受管目录 manifest 对账**:MANAGED_DIRS 内 target 有而 tarball 无的文件 = 幽灵 · 更新时删除
  (docs/audit/ 与 docs/retro/ 是安装侧运行时数据 · 豁免;根目录散文件只覆盖不删)
- **降级防护**:目标版本低于本地 → FAIL · 需 `--allow-downgrade` 显式放行
- **backup 保留策略**:成功更新后只保留最近 BACKUP_KEEP_COUNT 份

用法:
    python3 SKILL_ROOT/tools/update.py [--channel <branch>] [--no-backup] [--allow-downgrade]

默认 channel:从 cwd 找 project_root · 读 .teamwork_localconfig.json.update_channel · fallback main
默认 backup 路径:~/.teamwork/backups/<ts>/(用户拍板 B3 · 不污染 skill_root)
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
from pathlib import Path
from typing import Optional


# ─── 常量 ─────────────────────────────────────────────────────────────────

SKILL_TARBALL_URL_TEMPLATE = (
    "https://github.com/okteam99/teamwork/archive/refs/heads/{channel}.tar.gz"
)
SKILL_UPDATE_DOWNLOAD_TIMEOUT_SEC = 60
SKILL_UPDATE_URL_ENV_TARBALL = "TEAMWORK_SKILL_TARBALL_URL"  # 测试覆盖用

# v8.44.3:backup 路径(用户拍板 B3 · ~/.teamwork/backups/<ts>/ · 不污染 skill_root)
SKILL_BACKUP_ROOT_ENV = "TEAMWORK_BACKUP_ROOT"  # 测试覆盖用 · 默认 ~/.teamwork/backups

# backup 保留策略:成功更新后只留最近 N 份(防 ~/.teamwork/backups 无限膨胀)
BACKUP_KEEP_COUNT = 10

# 受管目录(相对 skill_root):更新时做 manifest 对账 · target 有而 tarball 无的文件视为幽灵删除。
# tools/tests/ 在 tools/ 之下一并覆盖;根目录散文件与未列目录(用户自定义)不在对账范围。
MANAGED_DIRS = (
    "tools", "stages", "standards", "roles", "templates",
    "docs", "agents", "claude-agents", "codex-agents", "hooks",
)
# 对账豁免前缀:安装侧运行时数据(_v8_ship.py 往 docs/audit/ 写审计)· tarball 不含 · 不得当幽灵删
RECONCILE_EXEMPT_PREFIXES = ("docs/audit/", "docs/retro/")
# 受管目录内顺带清理的缓存/系统垃圾(不计入幽灵清单)
JUNK_DIR_NAMES = frozenset({"__pycache__", ".pytest_cache"})
JUNK_FILE_NAMES = frozenset({".DS_Store"})


# ─── helpers ─────────────────────────────────────────────────────────────


def _now_iso() -> str:
    """ISO 时间戳(UTC · for emit timestamp)。"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now_ts_compact() -> str:
    """紧凑时间戳(20260528T143022Z · 用作 backup 目录名)。"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _emit(payload: dict) -> None:
    """统一 stdout JSON emit · 风格与 state.py / bootstrap.py 对齐。"""
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _backup_root() -> Path:
    """v8.44.3:backup 根目录 · 默认 ~/.teamwork/backups/ · env 可 override。"""
    override = os.environ.get(SKILL_BACKUP_ROOT_ENV)
    if override:
        return Path(override)
    return Path.home() / ".teamwork" / "backups"


def _backup_skill_root(skill_root: Path) -> tuple[Path, int]:
    """v8.44.3:backup skill_root 整个目录到 ~/.teamwork/backups/<ts>/ · 返 (backup_path, file_count)。

    用 shutil.copytree 完整复制 · 含全部文件 + 子目录 + mode + mtime。
    """
    ts = _now_ts_compact()
    backup_root = _backup_root()
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_dir = backup_root / ts
    # 若同 ts 已存在(罕见)· 追加 PID 防冲突
    if backup_dir.exists():
        backup_dir = backup_root / f"{ts}-{os.getpid()}"
    shutil.copytree(skill_root, backup_dir, symlinks=False)
    # 统计文件数
    file_count = sum(1 for _ in backup_dir.rglob("*") if _.is_file())
    return backup_dir, file_count


def _download_skill_tarball(channel: str, work_dir: Path
                             ) -> tuple[bool, str, Optional[Path]]:
    """v8.41 / v8.42:下载 GitHub tarball(指定 channel)+ 解压 · 返 (ok, error, source_skill_dir)。

    解压后 GitHub tarball 顶层目录是 teamwork-<channel>/ · skill 在 skills/teamwork/。
    """
    url = (os.environ.get(SKILL_UPDATE_URL_ENV_TARBALL)
           or SKILL_TARBALL_URL_TEMPLATE.format(channel=channel))
    tarball = work_dir / "tarball.tar.gz"
    extract_dir = work_dir / "extract"
    extract_dir.mkdir(parents=True, exist_ok=True)

    # curl 下载
    r = subprocess.run(
        ["curl", "-sL", "--fail", "--max-time",
         str(SKILL_UPDATE_DOWNLOAD_TIMEOUT_SEC), "-o", str(tarball), url],
        capture_output=True, text=True, timeout=SKILL_UPDATE_DOWNLOAD_TIMEOUT_SEC + 5,
    )
    if r.returncode != 0 or not tarball.exists() or tarball.stat().st_size == 0:
        return (False,
                f"curl 下载 {url} 失败(exit={r.returncode} · "
                f"size={tarball.stat().st_size if tarball.exists() else 0})· "
                f"stderr={r.stderr.strip()[:200]}",
                None)

    # tar 解压
    t = subprocess.run(
        ["tar", "-xzf", str(tarball), "-C", str(extract_dir)],
        capture_output=True, text=True, timeout=60,
    )
    if t.returncode != 0:
        return (False, f"tar 解压失败:{t.stderr.strip()[:200]}", None)

    # 找解压后的 skill 目录(teamwork-<channel>/skills/teamwork/)
    candidates = list(extract_dir.glob("*/skills/teamwork"))
    if not candidates:
        return (False,
                f"解压后未找到 skills/teamwork/ 目录(检查 channel={channel} "
                f"是否含 skills/teamwork/)· extract_dir={extract_dir}",
                None)
    if not (candidates[0] / "SKILL.md").exists():
        return (False, f"解压后 skill 目录缺 SKILL.md:{candidates[0]}", None)
    return (True, "", candidates[0])


def _parse_skill_md_version(skill_md: Path) -> Optional[str]:
    """读 SKILL.md frontmatter version · 不存在/无字段 → None。"""
    if not skill_md.exists():
        return None
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"^version:\s*(\S+)\s*$", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def _detect_local_modifications(target_dir: Path, source_dir: Path) -> dict:
    """v8.41:对比 target_dir(本地 skill_root)与 source_dir(下载解压)文件内容。

    遍历 source_dir 所有 file · 若 target 对应文件存在但 hash 不同 → modified。
    target 有 source 没 → 不视作 modification(本地新增 · 可能是用户自定义)。

    返 {modified: [rel_path], new_files: [rel_path]}
    """
    modified: list[str] = []
    new_files: list[str] = []

    for src_file in source_dir.rglob("*"):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(source_dir)
        tgt_file = target_dir / rel
        if not tgt_file.exists():
            new_files.append(str(rel))
            continue
        try:
            if src_file.read_bytes() != tgt_file.read_bytes():
                modified.append(str(rel))
        except OSError:
            modified.append(str(rel))
    return {"modified": modified, "new_files": new_files}


def _overwrite_skill_files(target_dir: Path, source_dir: Path) -> int:
    """把 source_dir 所有文件复制到 target_dir · 覆盖同名 · 返复制文件数。

    本函数只覆盖不删;target 多余文件由 _reconcile_managed_dirs 对账处理
    (受管目录内删幽灵 · 根目录散文件/用户自定义目录不动)。
    """
    copied = 0
    for src_file in source_dir.rglob("*"):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(source_dir)
        tgt_file = target_dir / rel
        tgt_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, tgt_file)  # copy2 保留 mode + mtime
        copied += 1
    return copied


def _reconcile_managed_dirs(target_dir: Path, source_dir: Path) -> tuple[list[str], int]:
    """受管目录 manifest 对账:删除 target 有而 source(tarball)无的文件(幽灵文件)。

    - 只处理 MANAGED_DIRS 下的文件 · 根目录散文件 / 未受管目录(用户自定义)不动
    - RECONCILE_EXEMPT_PREFIXES 豁免(安装侧运行时审计数据)
    - __pycache__ / .pytest_cache / .DS_Store 一律清掉 · 计入 junk 不计入幽灵清单
    - 对账后 bottom-up 清掉受管目录内的空子目录(豁免前缀内的目录不动)

    返 (stale_removed 相对路径清单, junk_removed 数量)。
    """
    source_files = {
        str(p.relative_to(source_dir))
        for p in source_dir.rglob("*") if p.is_file()
    }
    stale_removed: list[str] = []
    junk_removed = 0
    for dirname in MANAGED_DIRS:
        base = target_dir / dirname
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*")):
            if not f.is_file():
                continue
            rel_path = f.relative_to(target_dir)
            rel = str(rel_path)
            if any(rel.startswith(pfx) for pfx in RECONCILE_EXEMPT_PREFIXES):
                continue
            # 缓存/系统垃圾:直接清 · 不算幽灵
            if f.name in JUNK_FILE_NAMES or JUNK_DIR_NAMES.intersection(rel_path.parts[:-1]):
                f.unlink(missing_ok=True)
                junk_removed += 1
                continue
            if rel not in source_files:
                f.unlink(missing_ok=True)
                stale_removed.append(rel)
        # 空目录 bottom-up 清理 · 含受管目录本身(rmdir 只删空目录 · 非空抛错跳过)
        subdirs = sorted((p for p in base.rglob("*") if p.is_dir()),
                         key=lambda p: len(p.parts), reverse=True)
        for d in subdirs:
            rel_d = str(d.relative_to(target_dir)) + "/"
            if any(rel_d.startswith(pfx) for pfx in RECONCILE_EXEMPT_PREFIXES):
                continue
            try:
                d.rmdir()
            except OSError:
                pass
        try:
            base.rmdir()
        except OSError:
            pass
    return stale_removed, junk_removed


def _version_tuple(version: Optional[str]) -> Optional[tuple[int, int, int]]:
    """把 'v8.44.3' / '8.44' 解析成可比较三元组(缺 patch 段视为 0)· 解析不了 → None。"""
    if not version:
        return None
    m = re.match(r"^v?(\d+)\.(\d+)(?:\.(\d+))?", version.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)


def _prune_old_backups(keep: int = BACKUP_KEEP_COUNT) -> int:
    """backup 保留策略:按目录名(紧凑时间戳 · 字典序=时间序)排序 · 只留最近 keep 份。

    返清理数量 · 只在成功更新后调用 · 失败不影响更新结果(调用方兜 try)。
    """
    root = _backup_root()
    if not root.is_dir():
        return 0
    dirs = sorted((d for d in root.iterdir() if d.is_dir()), key=lambda p: p.name)
    excess = dirs[:-keep] if len(dirs) > keep else []
    pruned = 0
    for d in excess:
        shutil.rmtree(d, ignore_errors=True)
        pruned += 1
    return pruned


def _resolve_channel(args) -> tuple[str, str]:
    """v8.39:resolve channel 优先级 args > localconfig > main。

    返 (channel, channel_source)。
    """
    channel = getattr(args, "channel", None)
    if channel:
        return channel, "args"
    # 从 cwd 找 project_root · 读 .teamwork_localconfig.json
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from bootstrap import (
            find_project_root,
            _read_update_channel,
            SKILL_UPDATE_DEFAULT_CHANNEL,
        )
        project_root = find_project_root(Path.cwd())
        ch = _read_update_channel(project_root)
        return ch, ("localconfig" if ch != SKILL_UPDATE_DEFAULT_CHANNEL else "default")
    except Exception:
        return "main", "default_fallback"


# ─── 主流程 ───────────────────────────────────────────────────────────────


def cmd_update(args) -> int:
    """v8.42:update.py 主流程(从 v8.41 state.py:cmd_update_skill 抽离)。
    v8.44.3 重设计:默认 backup + overwrite · 不再 BLOCK 二次问用户(用户拍板)。

    流程:
      1. resolve channel(args > localconfig > main)
      2. 读 old version
      3. download tarball + 解压 to /tmp(失败 → FAIL with hint)
      4. 读 new version + 校验完整性 + 降级防护(new < old → FAIL · 需 --allow-downgrade)
      5. 检测本地修改(audit 用 · 不再 BLOCK)
      6. backup skill_root → ~/.teamwork/backups/<ts>/(默认 · --no-backup 跳过)
      7. 覆盖 skill_root + 受管目录对账删幽灵 · prune 旧 backup · cleanup tmp · emit OK
    """
    # skill_root:从本文件位置反推(同 bootstrap / state.py pattern)
    skill_root = Path(__file__).resolve().parent.parent

    # Step 1: channel
    channel, channel_source = _resolve_channel(args)

    # Step 2: 读 old version
    old_version = _parse_skill_md_version(skill_root / "SKILL.md")

    # Step 3: 下载 tarball + 解压
    work_dir = Path(tempfile.mkdtemp(prefix=f"teamwork-update-{channel}-"))
    try:
        ok, err, source_skill_dir = _download_skill_tarball(channel, work_dir)
        if not ok:
            _emit({
                "verdict": "FAIL",
                "command": "update",
                "error": f"下载/解压失败:{err}",
                "channel": channel,
                "channel_source": channel_source,
                "hint": (
                    f"检查网络 / 分支 {channel} 是否存在 / GitHub repo 路径 · 修复后重跑。"
                    f"\n  若想换 channel · 加 --channel main(或编辑 "
                    f".teamwork_localconfig.json.update_channel)"
                ),
            })
            return 1

        # Step 4: 读 new version + 校验
        assert source_skill_dir is not None  # type narrow
        new_version = _parse_skill_md_version(source_skill_dir / "SKILL.md")
        if not new_version:
            _emit({
                "verdict": "FAIL",
                "command": "update",
                "error": (
                    f"下载的 SKILL.md frontmatter 抽不出 version 字段 · "
                    f"channel={channel} · 不覆盖防写坏本地"
                ),
                "channel": channel,
                "channel_source": channel_source,
            })
            return 1

        # Step 4.5: 降级防护 · 目标版本低于本地 → FAIL(需 --allow-downgrade 显式放行)
        old_t = _version_tuple(old_version)
        new_t = _version_tuple(new_version)
        if (old_t is not None and new_t is not None and new_t < old_t
                and not getattr(args, "allow_downgrade", False)):
            _emit({
                "verdict": "FAIL",
                "command": "update",
                "error": (f"目标版本 {new_version} 低于本地 {old_version} · "
                          f"拒绝降级(防误覆盖新版)"),
                "channel": channel,
                "channel_source": channel_source,
                "old_version": old_version,
                "new_version": new_version,
                "hint": (
                    "确要降级(如回滚坏版本)加 --allow-downgrade 重跑 · "
                    "否则检查 channel 是否指错分支(--channel main / "
                    ".teamwork_localconfig.json.update_channel)"
                ),
            })
            return 1

        # Step 5: 检测本地修改(audit 用 · 不再 BLOCK · v8.44.3 治本)
        mods = _detect_local_modifications(skill_root, source_skill_dir)
        modified = mods["modified"]
        new_files = mods["new_files"]

        # Step 6: backup(默认 · --no-backup 跳过)
        no_backup = getattr(args, "no_backup", False)
        backup_path: Optional[Path] = None
        backup_file_count = 0
        backup_skip_reason = None
        if no_backup:
            backup_skip_reason = "--no-backup flag passed · skip backup"
        else:
            try:
                backup_path, backup_file_count = _backup_skill_root(skill_root)
            except OSError as e:
                _emit({
                    "verdict": "FAIL",
                    "command": "update",
                    "error": f"backup 失败:{e}",
                    "channel": channel,
                    "channel_source": channel_source,
                    "hint": (
                        "backup 路径:~/.teamwork/backups/<ts>/ · 检查 disk 空间 / 权限"
                        " · 或加 --no-backup 跳过(慎用 · 不可恢复)"
                    ),
                })
                return 1

        # Step 7: 覆盖 + 受管目录对账(中途失败 → emit backup 恢复指引)
        try:
            copied = _overwrite_skill_files(skill_root, source_skill_dir)
            stale_removed, junk_removed = _reconcile_managed_dirs(
                skill_root, source_skill_dir)
        except OSError as e:
            restore_hint = (
                (f"skill_root 可能处于半覆盖状态 · 恢复命令:\n"
                 f"  cp -R '{backup_path}/.' '{skill_root}/'\n"
                 f"(把 backup 整树覆盖回 skill_root · 恢复后重跑 update.py)")
                if backup_path else
                ("无 backup(--no-backup)· skill_root 可能处于半覆盖状态 · "
                 "修复磁盘/权限问题后重跑 update.py 完成覆盖")
            )
            _emit({
                "verdict": "FAIL",
                "command": "update",
                "error": f"覆盖/对账中途失败:{e}",
                "channel": channel,
                "channel_source": channel_source,
                "skill_root": str(skill_root),
                "backup_path": str(backup_path) if backup_path else None,
                "hint": restore_hint,
            })
            return 1

        # 成功更新且本次有新建 backup → prune 旧 backup(只留最近 BACKUP_KEEP_COUNT 份)
        # --no-backup 的运行不动 backup 存量 · prune 失败不影响更新结果
        backups_pruned = 0
        if backup_path is not None:
            try:
                backups_pruned = _prune_old_backups()
            except OSError:
                pass

        same_version = old_version == new_version
        channel_hint = (f"(channel={channel})" if channel != "main" else "")
        _emit({
            "verdict": "OK",
            "command": "update",
            "old_version": old_version,
            "new_version": new_version,
            "version_changed": not same_version,
            "channel": channel,
            "channel_source": channel_source,
            "skill_root": str(skill_root),
            "files_copied": copied,
            "modified_overwritten": modified[:10] if modified else [],
            "modified_overwritten_total": len(modified),
            "new_files_added": new_files[:10] if new_files else [],
            "new_files_added_total": len(new_files),
            "stale_files_removed": stale_removed[:20] if stale_removed else [],
            "stale_files_removed_total": len(stale_removed),
            "junk_removed_total": junk_removed,
            "backups_pruned": backups_pruned,
            "backup_path": str(backup_path) if backup_path else None,
            "backup_file_count": backup_file_count,
            "backup_skip_reason": backup_skip_reason,
            "timestamp": _now_ts_compact(),
            "next_hint": (
                (f"✅ 升级 {old_version} → {new_version}{channel_hint} · "
                 f"复制 {copied} 文件(覆盖 {len(modified)} 个本地改动 · "
                 f"新增 {len(new_files)} 个文件 · 清理 {len(stale_removed)} 个幽灵文件)· "
                 + (f"backup 在 {backup_path}(可对比 diff 决定是否合回本地改动)· "
                    if backup_path else "(无 backup · --no-backup)· ")
                 + f"查 {skill_root}/docs/CHANGELOG.md 顶部新版本段了解变更。")
                if not same_version else
                ((f"已在最新版本 {new_version}{channel_hint} · "
                  f"{len(modified)} 个本地改动已覆盖 · {copied} 文件复制 · "
                  + (f"backup 在 {backup_path}" if backup_path else "无 backup"))
                 if modified else
                 f"已在最新版本 {new_version}{channel_hint} · 无变化 · "
                 + (f"backup 在 {backup_path}" if backup_path else "无 backup"))
            ),
        })
        return 0
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass


def build_parser() -> argparse.ArgumentParser:
    """v8.42:独立 argparse(不归 state.py)· v8.44.3 重设计 flag。"""
    p = argparse.ArgumentParser(
        prog="update.py",
        description=(
            "Teamwork skill 自更新(v8.42 独立脚本 · v8.44.3 默认 backup+overwrite)。\n"
            "下载 GitHub tarball 覆盖 skill_root · 不依赖 git · "
            "默认 backup 到 ~/.teamwork/backups/<ts>/(用户拍板 · 治本 2 次暂停点过度)"
        ),
    )
    p.add_argument("--channel",
                   help=("skill 升级分支 · 默认从 .teamwork_localconfig.json.update_channel 读 · "
                         "fallback main。推荐:稳定环境用 main · 尝鲜用 dev"))
    p.add_argument("--no-backup", action="store_true",
                   help=("[v8.44.3] 跳过 backup(默认 backup 到 ~/.teamwork/backups/<ts>/) · "
                         "慎用 · 本地改动覆盖不可恢复。仅极端用户(不想累积 backup)用"))
    p.add_argument("--allow-downgrade", action="store_true",
                   help=("显式允许降级(目标版本低于本地时默认 FAIL)· "
                         "仅回滚坏版本等场景用"))
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return cmd_update(args)


if __name__ == "__main__":
    sys.exit(main())
