#!/bin/bash
# verify-ac.sh — AC↔test 覆盖校验脚本示例
#
# 用法：bash verify-ac.sh <Feature 目录>
#
# 功能：
# 1. 从 PRD.md 的 YAML frontmatter 提取所有 AC id
# 2. 从 TC.md 的 YAML frontmatter 提取所有 test 及其 covers_ac
# 3. 校验每个 AC 至少被 1 个 test 覆盖
# 4. （可选）运行对应测试，校验全绿
#
# 退出码：
#   0 - 校验通过
#   1 - 缺少覆盖 / frontmatter 解析失败 / 测试失败
#
# 依赖：yq（YAML 解析），测试 runner（项目自行决定）
#
# 🔴 这是示例脚本。每个项目应该按自己的技术栈（Node/Python/Go 等）落地实际版本。
#    建议放在 {子项目}/scripts/verify-ac.sh，在 Dev Stage / Test Stage Output Contract 中调用。

set -e

FEATURE_DIR="${1:?usage: verify-ac.sh <feature-dir>}"
PRD="$FEATURE_DIR/PRD.md"
TC="$FEATURE_DIR/TC.md"

# 0. 文件存在校验
[ -f "$PRD" ] || { echo "❌ $PRD 不存在"; exit 1; }
[ -f "$TC"  ] || { echo "❌ $TC 不存在";  exit 1; }

# 1. 提取 PRD 的 AC id 列表（读取 frontmatter）
# yq 从 markdown 文件读 frontmatter 需要先提取 YAML 部分
extract_frontmatter() {
  awk '
    /^---$/ { count++; next }
    count == 1 { print }
    count == 2 { exit }
  ' "$1"
}

PRD_ACS=$(extract_frontmatter "$PRD" | yq '.acceptance_criteria[].id' 2>/dev/null || echo "")
[ -z "$PRD_ACS" ] && { echo "❌ $PRD frontmatter 解析失败或无 acceptance_criteria"; exit 1; }

# 2. 提取 TC 的所有 covers_ac（展平）
TC_COVERS=$(extract_frontmatter "$TC" | yq '.tests[].covers_ac[]' 2>/dev/null || echo "")
[ -z "$TC_COVERS" ] && { echo "❌ $TC frontmatter 解析失败或无 tests"; exit 1; }

# 3. 校验：每个 AC 至少被 1 个 test 覆盖
MISSING=""
for ac in $PRD_ACS; do
  if ! echo "$TC_COVERS" | grep -qx "\"$ac\""; then
    MISSING="$MISSING $ac"
  fi
done

if [ -n "$MISSING" ]; then
  echo "❌ 以下 AC 无测试覆盖：$MISSING"
  exit 1
fi

echo "✅ AC 覆盖校验通过（${PRD_ACS} 均有对应测试）"

# 4. （可选）运行测试
# 示例：按项目技术栈调整
# if [ -f "$FEATURE_DIR/../../../package.json" ]; then
#   (cd "$FEATURE_DIR/../../.." && npm test -- --findRelatedTests "$FEATURE_DIR/..")
# elif [ -f "$FEATURE_DIR/../../../pyproject.toml" ]; then
#   (cd "$FEATURE_DIR/../../.." && pytest)
# fi
#
# 当前脚本只做覆盖校验，测试执行由 Dev Stage / Test Stage 自身负责。

exit 0
