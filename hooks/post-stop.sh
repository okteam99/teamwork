#!/bin/bash
# Teamwork Stop hook
# Checks if STATUS.md is stale (not updated today) for in-progress Features.
# Reminds PMO to sync status if needed.

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

today=$(date +%Y-%m-%d)
stale_features=""
stale_count=0

while IFS= read -r status_file; do
  [ -f "$status_file" ] || continue

  # Read current phase - skip completed
  phase=$(grep -m1 '当前阶段' "$status_file" 2>/dev/null | sed 's/.*|[[:space:]]*//' | sed 's/[[:space:]]*|.*//' || true)
  if [[ "$phase" == *"已完成"* ]] || [[ "$phase" == *"Bugfix 已完成"* ]] || [ -z "$phase" ]; then
    continue
  fi

  # Check last update date
  last_update=$(grep -m1 '最后更新' "$status_file" 2>/dev/null | sed 's/.*|[[:space:]]*//' | sed 's/[[:space:]]*|.*//' || true)

  # Extract just the date part (YYYY-MM-DD) from the last_update field
  update_date=$(echo "$last_update" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1 || true)

  # If no valid date or date is not today, mark as stale
  if [ -z "$update_date" ] || [ "$update_date" != "$today" ]; then
    feature_dir=$(dirname "$status_file")
    feature_name=$(basename "$feature_dir")
    stale_features+="- ${feature_name}: 最后更新=${last_update:-未知}\n"
    stale_count=$((stale_count + 1))
  fi

done < <(find "$ROOT" -path "*/docs/features/*/STATUS.md" -type f 2>/dev/null)

# Only output if there are stale features
if [ "$stale_count" -gt 0 ]; then
  context="[Teamwork 状态同步提醒] ${stale_count} 个进行中的 Feature 的 STATUS.md 今日未更新：\n\n${stale_features}\n如果本轮对话涉及了这些 Feature，PMO 应在下次回复时同步更新 STATUS.md（当前阶段 + 最后更新时间）。"
  escaped=$(escape_for_json "$context")
  printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"%s"}}\n' "$escaped"
fi

exit 0
