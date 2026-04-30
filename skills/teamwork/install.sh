#!/usr/bin/env bash
# Teamwork Skill Installer
# Detects host AI tool (Claude Code / Codex CLI) and deploys accordingly.
# Usage: bash install.sh [--host claude|codex|auto]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${1:---host}"
HOST_VALUE="${2:-auto}"

# Parse arguments
if [[ "$HOST" == "--host" ]]; then
    HOST_VALUE="${HOST_VALUE}"
else
    HOST_VALUE="auto"
fi

# Auto-detect host
detect_host() {
    if [[ -d ".claude" ]] || command -v claude &>/dev/null; then
        echo "claude"
    elif [[ -d ".codex" ]] || command -v codex &>/dev/null; then
        echo "codex"
    else
        echo "unknown"
    fi
}

if [[ "$HOST_VALUE" == "auto" ]]; then
    HOST_VALUE=$(detect_host)
    echo "🔧 Auto-detected host: $HOST_VALUE"
fi

case "$HOST_VALUE" in
    claude)
        SKILL_DIR=".claude/skills/teamwork"
        HOOKS_DIR=".claude/hooks"
        echo "📦 Installing Teamwork for Claude Code..."

        # Create skill directory
        mkdir -p "$SKILL_DIR"

        # Copy all skill files (preserve structure)
        cp -r "$SCRIPT_DIR"/*.md "$SKILL_DIR/" 2>/dev/null || true
        for dir in agents roles rules stages standards templates docs; do
            if [[ -d "$SCRIPT_DIR/$dir" ]]; then
                cp -r "$SCRIPT_DIR/$dir" "$SKILL_DIR/"
            fi
        done

        # Deploy hooks
        mkdir -p "$HOOKS_DIR"
        if [[ -d "$SCRIPT_DIR/../hooks" ]]; then
            cp "$SCRIPT_DIR/../hooks/"*.sh "$SKILL_DIR/hooks/" 2>/dev/null || true
            # Use Claude-specific hooks.json (with PreCompact/PostCompact)
            cp "$SCRIPT_DIR/../hooks/hooks.json" "$HOOKS_DIR/hooks.json" 2>/dev/null || true
        fi

        echo "✅ Installed to $SKILL_DIR"
        echo "   Hooks deployed to $HOOKS_DIR"
        ;;

    codex)
        SKILL_DIR=".agents/skills/teamwork"
        HOOKS_DIR=".codex"
        AGENTS_DIR=".codex/agents"
        echo "📦 Installing Teamwork for Codex CLI..."

        # Create skill directory
        mkdir -p "$SKILL_DIR"

        # Copy all skill files (preserve structure)
        cp -r "$SCRIPT_DIR"/*.md "$SKILL_DIR/" 2>/dev/null || true
        for dir in agents roles rules stages standards templates docs; do
            if [[ -d "$SCRIPT_DIR/$dir" ]]; then
                cp -r "$SCRIPT_DIR/$dir" "$SKILL_DIR/"
            fi
        done

        # Copy hooks scripts into skill directory (Codex references them from there)
        mkdir -p "$SKILL_DIR/hooks"
        if [[ -d "$SCRIPT_DIR/../hooks" ]]; then
            cp "$SCRIPT_DIR/../hooks/"*.sh "$SKILL_DIR/hooks/" 2>/dev/null || true
        fi

        # Deploy Codex-specific hooks.json (no PreCompact/PostCompact)
        mkdir -p "$HOOKS_DIR"
        if [[ -f "$SCRIPT_DIR/codex-agents/hooks.json" ]]; then
            cp "$SCRIPT_DIR/codex-agents/hooks.json" "$HOOKS_DIR/hooks.json"
        fi

        # Deploy Codex agent definitions
        mkdir -p "$AGENTS_DIR"
        if [[ -d "$SCRIPT_DIR/codex-agents" ]]; then
            cp "$SCRIPT_DIR/codex-agents/"*.toml "$AGENTS_DIR/" 2>/dev/null || true
        fi

        # Enable hooks feature flag if not already set
        CONFIG_FILE="$HOME/.codex/config.toml"
        if [[ -f "$CONFIG_FILE" ]]; then
            if ! grep -q "codex_hooks" "$CONFIG_FILE" 2>/dev/null; then
                echo "" >> "$CONFIG_FILE"
                echo "[features]" >> "$CONFIG_FILE"
                echo "codex_hooks = true" >> "$CONFIG_FILE"
                echo "   ⚙️ Enabled codex_hooks in $CONFIG_FILE"
            fi
        fi

        echo "✅ Installed to $SKILL_DIR"
        echo "   Agents deployed to $AGENTS_DIR"
        echo "   Hooks deployed to $HOOKS_DIR/hooks.json"
        echo ""
        echo "💡 Tip: Start with 'codex' then type '/teamwork [your requirement]'"
        ;;

    *)
        echo "⚠️ Could not detect host AI tool."
        echo ""
        echo "Usage: bash install.sh --host [claude|codex|auto]"
        echo ""
        echo "  claude  → Install for Claude Code (.claude/skills/teamwork/)"
        echo "  codex   → Install for Codex CLI (.agents/skills/teamwork/)"
        echo "  auto    → Auto-detect (default)"
        exit 1
        ;;
esac

# v7.3.10+P0-39: 注入 .worktree/ 到项目根 .gitignore（避免主仓库 git 嵌套混乱）
# 默认 worktree_root_path = .worktree，install 时确保 gitignore 已含此条目
GITIGNORE_FILE=".gitignore"
WORKTREE_PATTERN=".worktree/"
if [[ -d ".git" ]] || git rev-parse --git-dir &>/dev/null; then
    if [[ -f "$GITIGNORE_FILE" ]]; then
        if ! grep -qxF "$WORKTREE_PATTERN" "$GITIGNORE_FILE" 2>/dev/null && ! grep -qxF ".worktree" "$GITIGNORE_FILE" 2>/dev/null; then
            echo "" >> "$GITIGNORE_FILE"
            echo "# Teamwork worktree root (v7.3.10+P0-39 default)" >> "$GITIGNORE_FILE"
            echo "$WORKTREE_PATTERN" >> "$GITIGNORE_FILE"
            echo "   📝 Appended .worktree/ to $GITIGNORE_FILE"
        fi
    else
        echo "# Teamwork worktree root (v7.3.10+P0-39 default)" > "$GITIGNORE_FILE"
        echo "$WORKTREE_PATTERN" >> "$GITIGNORE_FILE"
        echo "   📝 Created $GITIGNORE_FILE with .worktree/"
    fi
fi

echo ""
echo "📋 Installed files:"
find "$SKILL_DIR" -type f | head -20
TOTAL=$(find "$SKILL_DIR" -type f | wc -l)
if [[ "$TOTAL" -gt 20 ]]; then
    echo "   ... and $((TOTAL - 20)) more files"
fi
echo "   Total: $TOTAL files"
