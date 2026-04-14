#!/bin/bash
# post-subagent.sh — Subagent 完成后自动检查产出完整性
# 由 PMO 在 Subagent 返回后调用（非 hooks.json 自动触发，因为 Claude Code 没有 Subagent 完成事件）
# 用法: bash post-subagent.sh <feature_dir> <subagent_type>

FEATURE_DIR="$1"
SUBAGENT_TYPE="$2"

if [ -z "$FEATURE_DIR" ] || [ -z "$SUBAGENT_TYPE" ]; then
    echo "用法: post-subagent.sh <feature_dir> <subagent_type>"
    exit 1
fi

echo "📋 Subagent 产出完整性检查 ($SUBAGENT_TYPE)"
echo "=========================================="

case "$SUBAGENT_TYPE" in
    "rd-develop")
        # 检查是否有技术文档产出
        if [ -f "$FEATURE_DIR/TECH.md" ]; then
            echo "✅ TECH.md 存在"
        else
            echo "⚠️ TECH.md 缺失"
        fi
        # 检查是否有代码变更
        CHANGED=$(git diff --name-only HEAD 2>/dev/null | wc -l)
        echo "📝 本次代码变更文件数: $CHANGED"
        # 检查测试是否通过
        if command -v npm &>/dev/null && [ -f "package.json" ]; then
            echo "🧪 运行测试..."
            npm test 2>&1 | tail -5
        fi
        ;;
    "prd-review"|"tc-review")
        REVIEW_FILE="$FEATURE_DIR/PRD-REVIEW.md"
        [ "$SUBAGENT_TYPE" = "tc-review" ] && REVIEW_FILE="$FEATURE_DIR/TC-REVIEW.md"
        if [ -f "$REVIEW_FILE" ]; then
            echo "✅ 评审记录已生成: $(basename $REVIEW_FILE)"
            ISSUES=$(grep -c "🔴\|❌\|严重" "$REVIEW_FILE" 2>/dev/null || echo "0")
            echo "📊 严重问题数: $ISSUES"
        else
            echo "⚠️ 评审记录缺失: $(basename $REVIEW_FILE)"
        fi
        ;;
    "arch-code-review")
        if [ -f "$FEATURE_DIR/CODE-REVIEW.md" ]; then
            echo "✅ Code Review 报告已生成"
        else
            echo "⚠️ Code Review 报告缺失"
        fi
        ;;
    *)
        echo "ℹ️ 通用检查: $SUBAGENT_TYPE"
        ;;
esac

echo "=========================================="
echo "✅ Subagent 产出检查完成"
