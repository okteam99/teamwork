#!/usr/bin/env python3
"""
verify-ac.py — AC↔test 覆盖校验脚本（标准实现）

用法（二选一）：
    python3 {SKILL_ROOT}/templates/verify-ac.py <Feature 目录>
    python3 {SKILL_ROOT}/templates/verify-ac.py --prd <PRD.md 路径> --tc <TC.md 路径>

（--prd/--tc 是 _v8_stage_specs._evidence_ac_test_binding 门禁的调用形态 ·
  位置参数保留兼容旧用法。）

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
    """提取机读 YAML 文本段。

    优先 `<!-- TEAMWORK-MACHINE ... -->` 注释块(MD 预览隐藏 · 所有渲染器都不显机读契约)·
    兜底文件开头的 `--- ... ---` frontmatter(旧 PRD 兼容)。
    """
    if not md_path.exists():
        return ""
    text = md_path.read_text(encoding="utf-8")
    # 机读契约注释块(预览隐藏)优先
    m = re.search(r"(?:\A|\n)<!--[ \t]*TEAMWORK-MACHINE[^\n]*\n(.*?)\n-->", text, re.DOTALL)
    if m:
        return m.group(1)
    # 兜底:文件开头的 --- ... --- frontmatter
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


def verify_test_refs(prd: Path, repo_root: Path) -> int:
    """lite 档校验:AC 直接绑真实测试(PRD.acceptance_criteria[].test_refs)· 无 TC.md。

    格式:`<相对测试文件路径>` 或 `<相对测试文件路径>::<用例名>`。
    两道判据(缺一不可):
      ① 每条 AC 的 test_refs 非空          —— 拦「写了 AC 没写测试」
      ② 每个 ref 指向的文件真实存在;带 `::用例名` 的,用例名要在文件里出现
                                           —— 拦「点名一个不存在的测试」
    ② 是本模式存在的理由:TC 模式只核对 covers_ac 的 id 对得上,
    TC 里点名的测试函数全仓不存在也能 21/21 全绿(实证)。用例名匹配跨语言故意做宽松
    (纯子串):python `def test_x` / js `it('test_x')` / go `func TestX` 都能命中,
    不为了严格把多数语言挡在门外。
    """
    prd_fm = parse_frontmatter(extract_frontmatter(prd))
    ac_list = prd_fm.get("acceptance_criteria", []) or []
    if not ac_list:
        print(f"❌ {prd} frontmatter 无 acceptance_criteria 或解析失败", file=sys.stderr)
        return 2

    print(f"📋 AC↔测试引用校验(lite 档 · 无 TC)：{prd.parent}")
    print(f"├── PRD AC 数：{len(ac_list)}")
    print(f"├── 代码根：{repo_root}")
    print(f"└── 逐条：")

    empty, broken = [], []
    for ac in ac_list:
        ac_id = ac.get("id") or "<no-id>"
        refs = ac.get("test_refs") or []
        if isinstance(refs, str):
            refs = [refs] if refs.strip() else []
        refs = [r for r in refs if str(r).strip()]

        if not refs:
            empty.append(ac_id)
            print(f"    ❌ {ac_id}: test_refs 为空")
            continue

        bad = []
        for ref in refs:
            rel, _, case = str(ref).partition("::")
            target = repo_root / rel.strip()
            if not target.is_file():
                bad.append(f"{ref}(文件不存在)")
                continue
            if case.strip():
                body = target.read_text(encoding="utf-8", errors="replace")
                if case.strip() not in body:
                    bad.append(f"{ref}(文件在 · 用例名未出现)")
        if bad:
            broken.append((ac_id, bad))
            print(f"    ❌ {ac_id}: {len(bad)}/{len(refs)} 个引用不成立 —— {'; '.join(bad)}")
        else:
            print(f"    ✅ {ac_id}: {len(refs)} 个测试引用均存在 ({', '.join(refs)})")

    if empty or broken:
        print()
        if empty:
            print(f"❌ {len(empty)} 条 AC 的 test_refs 为空：{', '.join(empty)}")
            print("   修复方法：在 PRD 机读块对应 AC 填 test_refs "
                  "（如 tests/test_login.py::test_reject_expired_token）· dev 写完测试即回填")
        if broken:
            print(f"❌ {len(broken)} 条 AC 的 test_refs 指向不存在的测试："
                  f"{', '.join(a for a, _ in broken)}")
            print("   修复方法：核对路径相对代码根、用例名与实际测试一致"
                  "（点名一个不存在的测试 = 这条 AC 实际没被验证）")
        return 3

    print()
    print(f"✅ AC↔测试引用校验通过（{len(ac_list)} 条 AC 均绑定到真实存在的测试）")
    return 0


def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="AC↔test 覆盖校验(PRD.acceptance_criteria ↔ TC.tests[].covers_ac · "
                    "lite 档改核 PRD.acceptance_criteria[].test_refs)")
    ap.add_argument("feature_dir", nargs="?", default=None,
                    help="Feature 目录(含 PRD.md + TC.md)· 与 --prd/--tc 二选一")
    ap.add_argument("--prd", default=None, help="PRD.md 路径(与 --tc 成对传)")
    ap.add_argument("--tc", default=None, help="TC.md 路径(与 --prd 成对传)")
    ap.add_argument("--mode", choices=["tc", "test-refs"], default="tc",
                    help="tc(默认)= AC↔TC.covers_ac 覆盖校验 · "
                         "test-refs = lite 档 AC↔真实测试引用校验(不需要 TC.md)")
    ap.add_argument("--repo-root", default=None,
                    help="test-refs 模式下解析测试路径的根(缺省 = PRD 所在目录上溯的 git 根)")
    ns = ap.parse_args()

    # v8.342:lite 档分支 —— 只需要 PRD(TC 是 blueprint 产物 · lite 跳过 blueprint)
    if ns.mode == "test-refs":
        if not ns.prd and not ns.feature_dir:
            print("usage: --mode test-refs 需要 --prd <PRD.md> 或 <Feature 目录>", file=sys.stderr)
            return 1
        prd = Path(ns.prd) if ns.prd else Path(ns.feature_dir) / "PRD.md"
        if not prd.exists():
            print(f"❌ PRD.md 不存在：{prd}", file=sys.stderr)
            return 1
        if ns.repo_root:
            repo_root = Path(ns.repo_root)
        else:
            repo_root = next((p for p in [prd.parent, *prd.parent.parents]
                              if (p / ".git").exists()), prd.parent)
        return verify_test_refs(prd, repo_root)

    if ns.prd or ns.tc:
        if not (ns.prd and ns.tc):
            print("usage: --prd <PRD.md> 与 --tc <TC.md> 必须成对传", file=sys.stderr)
            return 1
        prd = Path(ns.prd)
        tc = Path(ns.tc)
        feature_dir = prd.parent
    elif ns.feature_dir:
        feature_dir = Path(ns.feature_dir)
        prd = feature_dir / "PRD.md"
        tc = feature_dir / "TC.md"
    else:
        print(f"usage: {sys.argv[0]} <Feature 目录> | --prd <PRD.md> --tc <TC.md>",
              file=sys.stderr)
        print(
            "  example: python3 verify-ac.py docs/features/AUTH-F042-email-login/",
            file=sys.stderr,
        )
        return 1

    # 0. 文件存在校验
    if not prd.exists():
        print(f"❌ PRD.md 不存在：{prd}", file=sys.stderr)
        return 1
    if not tc.exists():
        # v8.301:TC.md 是 blueprint 阶段产物 —— 在 goal 阶段跑本脚本必然到这里。
        # 保持 exit=1(blueprint-complete / test-complete 的门依赖它),但把裸失败
        # 换成**路由信息**:告诉调用方「你不该在这个时点调我」以及「你想验的东西谁在管」。
        # why:注定失败的调用会逼调用方自我解释成「预期的 FAIL」——
        # 而「预期的 FAIL」一旦被正常化,真 FAIL 就会被同样对待。
        print(f"❌ TC.md 不存在：{tc}", file=sys.stderr)
        print("   ℹ️ TC.md 是 blueprint 阶段产物。若当前在 goal 阶段,本校验尚不适用:",
              file=sys.stderr)
        print("      · AC 机读块本身 → goal-complete 的 prd_template_conformance 已校验(无需手跑本脚本)",
              file=sys.stderr)
        print("      · AC↔TC 覆盖    → blueprint-complete / test-complete 自动跑本脚本",
              file=sys.stderr)
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
        # 兼容 scalar 字符串(covers_ac: AC-1)· 防字符串被逐字符迭代(实证 PTR-F042)
        if isinstance(covers, str):
            covers = [covers]
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
