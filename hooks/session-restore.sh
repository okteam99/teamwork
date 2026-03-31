#!/bin/bash
# Teamwork SessionStart hook
# Scans STATUS.md files to detect in-progress Features and injects context
# for automatic session recovery via additionalContext.

set -euo pipefail

# --- Find teamwork project root (look for teamwork_space.md) ---
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

# Scan all STATUS.md files for in-progress Features
features=""
feature_count=0

# Search for STATUS.md in all sub-project docs/features directories
while IFS= read -r status_file; do
  [ -f "$status_file" ] || continue

  # Read current phase
  phase=$(grep -m1 '当前阶段' "$status_file" 2>/dev/null | sed 's/.*|[[:space:]]*//' | sed 's/[[:space:]]*|.*//' || true)

  # Skip completed features
  if [[ "$phase" == *"已完成"* ]] || [[ "$phase" == *"Bugfix 已完成"* ]]; then
    continue
  fi

  # Skip empty phase (malformed STATUS.md)
  [ -z "$phase" ] && continue

  # Extract feature name from directory path
  feature_dir=$(dirname "$status_file")
  feature_name=$(basename "$feature_dir")

  # Extract current role
  role=$(grep -m1 '当前角色' "$status_file" 2>/dev/null | sed 's/.*|[[:space:]]*//' | sed 's/[[:space:]]*|.*//' || true)

  # Extract last update
  last_update=$(grep -m1 '最后更新' "$status_file" 2>/dev/null | sed 's/.*|[[:space:]]*//' | sed 's/[[:space:]]*|.*//' || true)

  # Extract sub-project from path (e.g., auth-service from auth-service/docs/features/AUTH-F001/STATUS.md)
  rel_path="${status_file#$ROOT/}"
  sub_project=$(echo "$rel_path" | cut -d'/' -f1)

  features+="- ${feature_name} [${sub_project}]: 阶段=${phase}, 角色=${role}, 更新=${last_update}\n"
  feature_count=$((feature_count + 1))

done < <(find "$ROOT" -path "*/docs/features/*/STATUS.md" -type f 2>/dev/null)

# If no in-progress features, still inject teamwork mode reminder
if [ "$feature_count" -eq 0 ]; then
  context="[Teamwork 会话恢复] 检测到 teamwork 项目（teamwork_space.md 存在），但无进行中的 Feature。等待用户输入新需求或执行 /teamwork 启动。"
else
  context="[Teamwork 会话恢复] 检测到 ${feature_count} 个进行中的 Feature：\n\n${features}\n请以 PMO 角色承接。读取 CONTEXT-RECOVERY.md 执行完整恢复流程，输出 Feature 状态看板后询问用户从哪里继续。\n\n🔴 恢复时基于 STATUS.md 判断阶段，禁止自行猜测。"
fi

escaped=$(escape_for_json "$context")
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$escaped"

exit 0
