#!/usr/bin/env python3
"""
tools/bump_patch_version.py — 把 SKILL.md frontmatter version 的 patch 段 +1。

用户拍板 2026-05-28:
- dev push 自动 bump patch · 不让小 description/fix 改动漏 release
- 规则:patch 段(.x)递增 · minor 段保留为 merge dev→main 时人工 bump

行为:
- v8.44     → v8.44.1   (无 patch 段 → 加 .1)
- v8.44.1   → v8.44.2   (patch 段 +1)
- v8.44.99  → v8.44.100 (无上限)
- vX.Y      → vX.Y.1
- 不合法 frontmatter → exit 2

用法:
    python3 tools/bump_patch_version.py [path/to/SKILL.md]
    (路径缺省 = 当前文件所在 dir 的 parent / SKILL.md = SKILL_ROOT/SKILL.md)

退出码:
    0 = OK · stdout 打印 "v8.X.Y → v8.X.Y+1"
    1 = OK 但已 bump(idempotent · 同一 SKILL.md 多次跑保持安全 · 仅打印当前 version)
        (注:本工具默认每次都 bump · idempotent 由调用方[hook]控制 · 见 hook 内 [auto-bump] guard)
    2 = 错误(文件不存在 / 无 frontmatter / 无 version 字段 / version 不合法)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


VERSION_RE = re.compile(r"^version:\s*v?(\d+)\.(\d+)(?:\.(\d+))?\s*$", re.MULTILINE)


def _default_skill_md_path() -> Path:
    """SKILL_ROOT/SKILL.md(bump_patch_version.py 在 SKILL_ROOT/tools/ 下)。"""
    return Path(__file__).resolve().parent.parent / "SKILL.md"


def bump_patch(text: str) -> tuple[str, str, str]:
    """对 frontmatter version 做 patch +1 · 返 (new_text, old_version_str, new_version_str)。

    raise ValueError 若 frontmatter 不含 version 字段。
    """
    m = VERSION_RE.search(text)
    if not m:
        raise ValueError("SKILL.md frontmatter 不含合法 version: vX.Y(.Z) 字段")

    major = int(m.group(1))
    minor = int(m.group(2))
    patch_str = m.group(3)
    patch = int(patch_str) + 1 if patch_str else 1

    old_version = f"v{major}.{minor}" + (f".{patch_str}" if patch_str else "")
    new_version = f"v{major}.{minor}.{patch}"

    new_text = VERSION_RE.sub(f"version: {new_version}", text, count=1)
    return new_text, old_version, new_version


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    path = Path(args[0]).expanduser().resolve() if args else _default_skill_md_path()

    if not path.exists():
        print(f"FAIL: SKILL.md 不存在: {path}", file=sys.stderr)
        return 2

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"FAIL: 读 {path} 失败: {e}", file=sys.stderr)
        return 2

    # 必须含 frontmatter(--- ... ---)
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        print(f"FAIL: {path} 顶部无 YAML frontmatter(--- ... ---)", file=sys.stderr)
        return 2

    try:
        new_text, old_v, new_v = bump_patch(text)
    except ValueError as e:
        print(f"FAIL: {e} · path={path}", file=sys.stderr)
        return 2

    path.write_text(new_text, encoding="utf-8")
    print(f"{old_v} → {new_v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
