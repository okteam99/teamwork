#!/usr/bin/env python3
"""
verify-ac.py — AC↔test 覆盖校验脚本（标准实现，v7.3.1）

用法：
    python3 {SKILL_ROOT}/templates/verify-ac.py <Feature 目录>

功能：
    1. 从 PRD.md 的 YAML frontmatter 提取所有 acceptance_criteria[].id
    2. 从 TC.md 的 YAML frontmatter 提取所有 tests[] 及其 covers_ac
    3. 校验每条 AC 至少被 1 个 test 覆盖
    4. 输出人可读报告 + 返回非 0 exit code 表示失败

依赖：只依赖 Python 3.6+（标准库），无 yq / 其他外部工具。
     YAML frontmatter 解析采用简化的纯文本扫描，不依赖 PyYAML。
     如果项目已装 PyYAML 会优先使用（更健壮）。

退出码：
    0 - 校验通过
    1 - 使用错误 / 文件缺失
    2 - frontmatter 解析失败
    3 - 覆盖不完整

🔴 本脚本是 Teamwork v7.3 Stage Output Contract 的机器校验入口。
   各 Stage 的 Dev / Blueprint 完成前必须通过此校验才能进入下一 Stage。

跨项目使用方式：
    - 不需要复制到项目目录，直接从 {SKILL_ROOT}/templates/verify-ac.py 调用
    - 或在 package.json / Makefile 里加 alias：
      "scripts": {
        "verify-ac": "python3 .claude/skills/teamwork/templates/verify-ac.py"
      }
"""

import os
import re
import sys
from pathlib import Path

# 尝试用 PyYAML（更健壮），失败则用简化解析（纯标准库）
try:
    import yaml
    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False


def extract_frontmatter(md_path: Path) -> str:
    """从 markdown 文件提取 YAML frontmatter 文本段（--- 之间的内容）。"""
    if not md_path.exists():
        return ""
    text = md_path.read_text(encoding="utf-8")
    # 匹配文件开头的 --- ... --- 块
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    return m.group(1) if m else ""


def parse_frontmatter(fm_text: str) -> dict:
    """解析 frontmatter YAML 文本为 dict。

    优先用 PyYAML（完整支持）；否则用简化解析只提取本脚本需要的字段。
    """
    if not fm_text.strip():
        return {}

    if HAS_PYYAML:
        try:
            return yaml.safe_load(fm_text) or {}
        except yaml.YAMLError:
            return {}

    # 简化解析：只支持 acceptance_criteria[].id / tests[].covers_ac[]
    result = {}
    current_list_key = None  # 'acceptance_criteria' | 'tests' | None
    items = []
    current_item = {}
    current_list_field = None  # 'covers_ac' | None
    current_list_values = []

    lines = fm_text.split("\n")
    for line in lines:
        # 顶层列表开始
        m = re.match(r"^(acceptance_criteria|tests):\s*$", line)
        if m:
            if current_list_key:
                if current_item:
                    if current_list_field and current_list_values:
                        current_item[current_list_field] = current_list_values
                    items.append(current_item)
                result[current_list_key] = items
            current_list_key = m.group(1)
            items = []
            current_item = {}
            current_list_field = None
            current_list_values = []
            continue

        if current_list_key is None:
            continue

        # 新的列表项（- id: xxx / - file: xxx）
        m = re.match(r"^\s*-\s+(\w+):\s*(.*)$", line)
        if m:
            # 保存上一项
            if current_item:
                if current_list_field and current_list_values:
                    current_item[current_list_field] = current_list_values
                items.append(current_item)
            # 开新项
            current_item = {}
            current_list_field = None
            current_list_values = []
            key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
            current_item[key] = val
            continue

        # 列表项内的字段（    key: value 或     key:）
        m = re.match(r"^\s{4,}(\w+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            # 保存上一个内嵌列表
            if current_list_field and current_list_values:
                current_item[current_list_field] = current_list_values
                current_list_field = None
                current_list_values = []

            if val == "":
                # 可能是内嵌列表开始（如 covers_ac:）
                current_list_field = key
                current_list_values = []
            elif val.startswith("["):
                # 内联列表 covers_ac: ["AC-1", "AC-2"]
                inner = val.strip("[]")
                current_item[key] = [
                    v.strip().strip('"').strip("'")
                    for v in inner.split(",")
                    if v.strip()
                ]
            else:
                current_item[key] = val.strip('"').strip("'")
            continue

        # 内嵌列表项（      - AC-1）
        m = re.match(r"^\s{6,}-\s+(.+)$", line)
        if m and current_list_field:
            current_list_values.append(m.group(1).strip().strip('"').strip("'"))
            continue

    # 收尾
    if current_list_key:
        if current_item:
            if current_list_field and current_list_values:
                current_item[current_list_field] = current_list_values
            items.append(current_item)
        result[current_list_key] = items

    return result


def main():
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <Feature 目录>", file=sys.stderr)
        print(
            "  example: python3 verify-ac.py docs/features/AUTH-F042-email-login/",
            file=sys.stderr,
        )
        return 1

    feature_dir = Path(sys.argv[1])
    prd = feature_dir / "PRD.md"
    tc = feature_dir / "TC.md"

    # 0. 文件存在校验
    if not prd.exists():
        print(f"❌ PRD.md 不存在：{prd}", file=sys.stderr)
        return 1
    if not tc.exists():
        print(f"❌ TC.md 不存在：{tc}", file=sys.stderr)
        return 1

    # 1. 解析 PRD frontmatter
    prd_fm = parse_frontmatter(extract_frontmatter(prd))
    ac_list = prd_fm.get("acceptance_criteria", []) or []
    prd_ac_ids = [ac.get("id") for ac in ac_list if ac.get("id")]

    if not prd_ac_ids:
        print(f"❌ {prd} frontmatter 无 acceptance_criteria 或解析失败", file=sys.stderr)
        print("    提示：检查 PRD.md 头部是否有 --- ... --- 包裹的 YAML", file=sys.stderr)
        if not HAS_PYYAML:
            print("    提示：安装 PyYAML 可获得更健壮的解析（pip install pyyaml）", file=sys.stderr)
        return 2

    # 2. 解析 TC frontmatter，收集每个 AC 被哪些 test 覆盖
    tc_fm = parse_frontmatter(extract_frontmatter(tc))
    tests = tc_fm.get("tests", []) or []

    if not tests:
        print(f"❌ {tc} frontmatter 无 tests 或解析失败", file=sys.stderr)
        return 2

    ac_covers = {ac_id: [] for ac_id in prd_ac_ids}
    for t in tests:
        tid = t.get("id", "<no-id>")
        covers = t.get("covers_ac", []) or []
        for ac in covers:
            if ac in ac_covers:
                ac_covers[ac].append(tid)

    # 3. 校验覆盖完整性
    missing = [ac for ac, tids in ac_covers.items() if not tids]
    covered = [ac for ac, tids in ac_covers.items() if tids]

    print(f"📋 AC↔test 覆盖校验：{feature_dir}")
    print(f"├── PRD AC 数：{len(prd_ac_ids)}")
    print(f"├── TC test 数：{len(tests)}")
    print(f"└── 覆盖情况：")
    for ac_id in prd_ac_ids:
        tids = ac_covers[ac_id]
        if tids:
            print(f"    ✅ {ac_id}: 被 {len(tids)} 个 test 覆盖 ({', '.join(tids)})")
        else:
            print(f"    ❌ {ac_id}: 无测试覆盖")

    if missing:
        print()
        print(f"❌ 校验未通过：{len(missing)} 条 AC 缺测试覆盖")
        print(f"   缺失：{', '.join(missing)}")
        print(f"   修复方法：在 TC.md 的 tests[] 中添加对应 covers_ac 引用")
        return 3

    print()
    print(f"✅ AC 覆盖校验通过（{len(prd_ac_ids)} 条 AC 均有测试覆盖）")

    # 4. （可选）提示后续运行测试的命令
    print()
    print("📝 下一步：运行上述 test 确保全部通过（由 Dev/Test Stage 自行调用 test runner）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
