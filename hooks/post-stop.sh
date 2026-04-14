#!/bin/bash
# Teamwork Stop hook
# 1. Reads 流转约束 section from active STATUS.md and injects as context
# 2. Checks if STATUS.md is stale (not updated today)
# Both reminders are injected so PMO sees constraints before every turn.

set -euo pipefail

# --- Logging helper ---
log_warn() {
  echo "[teamwork-hook][warn] $1" >&2
}

# --- Find teamwork project root ---
find_teamwork_root() {
  local dir="${PWD}"
  while [ "$dir" != "/" ]; do
    if [ -f "$dir/teamwork_space.md" ]; then
      echo "$dir"
      return 0
    fi
    # Fallback: single-project mode may not have teamwork_space.md
    if [ -d "$dir/docs/features" ]; then
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

# --- Extract 流转约束 section from STATUS.md ---
extract_flow_constraints() {
  local status_file="$1"
  local in_section=0
  local constraints=""

  while IFS= read -r line; do
    # Start of section
    if [[ "$line" == *"流转约束"* ]] && [[ "$line" == "##"* ]]; then
      in_section=1
      continue
    fi
    # End of section (next ## heading)
    if [ "$in_section" -eq 1 ] && [[ "$line" == "##"* ]]; then
      break
    fi
    # Capture content
    if [ "$in_section" -eq 1 ] && [ -n "$line" ]; then
      constraints+="${line}"$'\n'
    fi
  done < "$status_file"

  printf '%s' "$constraints"
}

# --- Main ---
ROOT=$(find_teamwork_root 2>/dev/null) || exit 0

today=$(date +%Y-%m-%d)
stale_features=""
stale_count=0
active_constraints=""
active_feature=""

while IFS= read -r status_file; do
  [ -f "$status_file" ] || continue

  # Read current phase - skip completed
  phase_raw=$(grep -m1 '当前阶段' "$status_file" 2>/dev/null || true)
  if [[ "$phase_raw" == *"|"* ]]; then
    phase=$(echo "$phase_raw" | sed 's/.*|[[:space:]]*//' | sed 's/[[:space:]]*|.*//')
  else
    phase=""
  fi
  if [[ "$phase" == *"已完成"* ]] || [[ "$phase" == *"Bugfix 已完成"* ]] || [ -z "$phase" ]; then
    continue
  fi

  # Extract feature name
  feature_dir=$(dirname "$status_file")
  feature_name=$(basename "$feature_dir")

  # Extract 流转约束 for active features
  constraints=$(extract_flow_constraints "$status_file")
  if [ -n "$constraints" ]; then
    active_constraints+="【${feature_name}】\n${constraints}\n"
    active_feature="$feature_name"
  fi

  # Check last update date
  last_update=$(grep -m1 '最后更新' "$status_file" 2>/dev/null | sed 's/.*|[[:space:]]*//' | sed 's/[[:space:]]*|.*//' || true)
  update_date=$(echo "$last_update" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1 || true)

  if [ -n "$update_date" ] && [ "$update_date" != "$today" ]; then
    stale_features+="- ${feature_name}: 最后更新=${last_update:-未知}\n"
    stale_count=$((stale_count + 1))
  fi

done < <(find "$ROOT" -path "*/docs/features/*/STATUS.md" -type f 2>/dev/null)

# Build output
context=""

# Part 1: Flow constraints reminder (high priority)
if [ -n "$active_constraints" ]; then
  context+="[Teamwork 流转约束提醒] 当前进行中 Feature 的流转约束（🔴 每次阶段变更前必须对照检查）：\n\n${active_constraints}🔴 目标阶段出现在「禁止跳转到」列表中 → 阻塞，禁止执行。\n🔴 如需跳过阶段 → 必须用户明确说「跳过流程」。\n"
fi

# Part 2: Stale STATUS.md reminder
if [ "$stale_count" -gt 0 ]; then
  if [ -n "$context" ]; then
    context+="\n"
  fi
  context+="[Teamwork 状态同步提醒] ${stale_count} 个进行中的 Feature 的 STATUS.md 今日未更新：\n\n${stale_features}\n如果本轮对话涉及了这些 Feature，PMO 应同步更新 STATUS.md（当前阶段 + 流转约束 + 最后更新时间）。"
fi

# Output if there's anything to say
if [ -n "$context" ]; then
  escaped=$(escape_for_json "$context")
  printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"%s"}}\n' "$escaped"
fi

exit 0
