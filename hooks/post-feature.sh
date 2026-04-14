#!/bin/bash
# post-feature.sh — Feature 完成后自动知识库归档 + 状态同步
# 由 PMO 在 Feature 完成后调用
# 用法: bash post-feature.sh <project_dir> <feature_dir> <feature_id>

PROJECT_DIR="$1"
FEATURE_DIR="$2"
FEATURE_ID="$3"

if [ -z "$PROJECT_DIR" ] || [ -z "$FEATURE_DIR" ] || [ -z "$FEATURE_ID" ]; then
    echo "用法: post-feature.sh <project_dir> <feature_dir> <feature_id>"
    exit 1
fi

echo "📦 Feature 完成后自动归档 ($FEATURE_ID)"
echo "=========================================="

# 1. 检查 KNOWLEDGE.md 是否需要更新
KNOWLEDGE="$PROJECT_DIR/docs/KNOWLEDGE.md"
if [ -f "$KNOWLEDGE" ]; then
    if grep -q "$FEATURE_ID" "$KNOWLEDGE"; then
        echo "✅ KNOWLEDGE.md 已包含 $FEATURE_ID 的记录"
    else
        echo "⚠️ KNOWLEDGE.md 尚未记录 $FEATURE_ID — PMO 需补充"
    fi
else
    echo "⚠️ KNOWLEDGE.md 不存在 — PMO 需创建并记录本次经验"
fi

# 2. 检查 ROADMAP.md 状态是否已更新
ROADMAP="$PROJECT_DIR/docs/ROADMAP.md"
if [ -f "$ROADMAP" ]; then
    if grep -q "$FEATURE_ID.*✅" "$ROADMAP"; then
        echo "✅ ROADMAP.md 中 $FEATURE_ID 已标记完成"
    else
        echo "⚠️ ROADMAP.md 中 $FEATURE_ID 未标记完成 — PMO 需更新"
    fi
else
    echo "ℹ️ 无 ROADMAP.md（可能非 Planning 产出的 Feature）"
fi

# 3. 检查 STATUS.md 是否标记完成
STATUS="$FEATURE_DIR/STATUS.md"
if [ -f "$STATUS" ]; then
    if grep -q "✅.*已完成\|已完成.*✅" "$STATUS"; then
        echo "✅ STATUS.md 已标记完成"
    else
        echo "⚠️ STATUS.md 未标记完成 — PMO 需更新"
    fi
else
    echo "⚠️ STATUS.md 不存在"
fi

# 4. 检查 PROJECT.md 是否需要更新
PROJECT="$PROJECT_DIR/docs/PROJECT.md"
if [ -f "$PROJECT" ]; then
    echo "ℹ️ PROJECT.md 存在 — PMO 需判断是否需要更新「当前状态」章节"
fi

# 5. 输出归档摘要
echo ""
echo "=========================================="
echo "📋 归档检查摘要"
echo "├── KNOWLEDGE.md: $([ -f "$KNOWLEDGE" ] && grep -q "$FEATURE_ID" "$KNOWLEDGE" && echo '✅' || echo '⚠️ 待更新')"
echo "├── ROADMAP.md:   $([ -f "$ROADMAP" ] && grep -q "$FEATURE_ID.*✅" "$ROADMAP" && echo '✅' || echo '⚠️ 待更新')"
echo "├── STATUS.md:    $([ -f "$STATUS" ] && grep -q "✅" "$STATUS" && echo '✅' || echo '⚠️ 待更新')"
echo "└── PROJECT.md:   $([ -f "$PROJECT" ] && echo 'ℹ️ 需人工判断' || echo 'ℹ️ 不存在')"
