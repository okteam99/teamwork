#!/bin/bash
# Teamwork PostCompact hook
# After context compaction completes, automatically inject teamwork recovery
# instructions so PMO can resume without user having to manually say "继续".
#
# This is the key piece of "semi-automatic context cleanup":
# 1. User runs /compact after task completion (prompted by PMO)
# 2. This hook fires → injects recovery context
# 3. Claude auto-restores teamwork state from STATUS.md

set -euo pipefail

# --- Find teamwork project root ---
find_teamwork_root() {
  local dir="${PWD}"
  while [ "$dir" != "/" ]; do
    if [ -f "$dir/teamwork_space.md" ]; then
      echo "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

# --- JSON escape helper ---
escape_for_json() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

# --- Main ---
ROOT=$(find_teamwork_root 2>/dev/null) || exit 0

# Count in-progress features
feature_count=0
features=""

while IFS= read -r status_file; do
  [ -f "$status_file" ] || continue

  phase=$(grep -m1 '当前阶段' "$status_file" 2>/dev/null | sed 's/.*|[[:space:]]*//' | sed 's/[[:space:]]*|.*//' || true)

  # Skip completed or empty
  if [[ "$phase" == *"已完成"* ]] || [[ "$phase" == *"Bugfix 已完成"* ]] || [ -z "$phase" ]; then
    continue
  fi

  feature_dir=$(dirname "$status_file")
  feature_name=$(basename "$feature_dir")
  rel_path="${status_file#$ROOT/}"
  sub_project=$(echo "$rel_path" | cut -d'/' -f1)

  role=$(grep -m1 '当前角色' "$status_file" 2>/dev/null | sed 's/.*|[[:space:]]*//' | sed 's/[[:space:]]*|.*//' || true)

  features+="- ${feature_name} [${sub_project}]: 阶段=${phase}, 角色=${role}\n"
  feature_count=$((feature_count + 1))

done < <(find "$ROOT" -path "*/docs/features/*/STATUS.md" -type f 2>/dev/null)

# Build recovery context
if [ "$feature_count" -eq 0 ]; then
  context="[Teamwork PostCompact 恢复] ✅ Context 已压缩。无进行中的 Feature，上下文已清理完毕。等待用户输入新需求。"
else
  context="[Teamwork PostCompact 恢复] ✅ Context 已压缩。检测到 ${feature_count} 个进行中的 Feature：\n\n${features}\n"
  context+="🔴 自动恢复指令（PMO 必须执行）：\n"
  context+="1. 读取当前 Feature 的 STATUS.md「流转约束」段 → 获得当前流程位置\n"
  context+="2. 读取 RULES.md 前 21 行「PMO 热路径索引」→ 获得规则定位能力\n"
  context+="3. 以 PMO 角色输出状态行 + 一句话摘要，告知用户已恢复\n"
  context+="\n🔴 禁止要求用户手动说「继续」——PostCompact 恢复必须自动完成。"
fi

escaped=$(escape_for_json "$context")
printf '{"hookSpecificOutput":{"hookEventName":"PostCompact","additionalContext":"%s"}}\n' "$escaped"

exit 0
