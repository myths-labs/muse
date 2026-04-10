#!/usr/bin/env bash
# detect_tool.sh — Detect the current AI coding tool
#
# Outputs a single canonical tool ID to stdout.
# See docs/CONVO_SPEC.md for the full tool ID table.
#
# Usage:
#   TOOL=$(bash scripts/adapters/detect_tool.sh)
#   echo "$TOOL"  # e.g., "claude-code", "aider", "cursor"
#
# Detection priority:
#   1. Environment variables (set by the tool's runtime)
#   2. Filesystem signals (config directories, history files)
#   3. "unknown" fallback
#
# Zero external dependencies.

set -euo pipefail

# --- Priority 1: Environment variables ---

# Claude Code sets CLAUDECODE=1 or is detectable via CLAUDE_* vars
if [ "${CLAUDECODE:-}" = "1" ] || [ -n "${CLAUDE_CODE:-}" ]; then
  echo "claude-code"
  exit 0
fi

# OpenClaw (fork of Claude Code)
if [ "${OPENCLAW:-}" = "1" ]; then
  echo "openclaw"
  exit 0
fi

# OpenCode
if [ "${OPENCODE:-}" = "1" ]; then
  echo "opencode"
  exit 0
fi

# Gemini CLI
if [ "${GEMINI_CLI:-}" = "1" ] || [ "${GEMINI:-}" = "1" ]; then
  echo "gemini"
  exit 0
fi

# Codex CLI (OpenAI)
if [ "${CODEX_CLI:-}" = "1" ] || [ "${CODEX:-}" = "1" ]; then
  echo "codex"
  exit 0
fi

# Aider
if [ "${AIDER:-}" = "1" ]; then
  echo "aider"
  exit 0
fi

# --- Priority 2: Filesystem signals ---

# Look for tool-specific directories/files in the project root
# Use $PROJECT_ROOT if set, else try git root, else cwd
PROJECT_ROOT="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Cursor — .cursor/ directory
if [ -d "$PROJECT_ROOT/.cursor" ]; then
  echo "cursor"
  exit 0
fi

# Windsurf — .windsurf/ directory or .windsurfrules file
if [ -d "$PROJECT_ROOT/.windsurf" ] || [ -f "$PROJECT_ROOT/.windsurfrules" ]; then
  echo "windsurf"
  exit 0
fi

# Aider — .aider.chat.history.md in project root
if [ -f "$PROJECT_ROOT/.aider.chat.history.md" ]; then
  echo "aider"
  exit 0
fi

# Antigravity — .gemini/antigravity/ directory
if [ -d "$PROJECT_ROOT/.gemini/antigravity" ]; then
  echo "antigravity"
  exit 0
fi

# Copilot — .github/copilot-instructions.md
if [ -f "$PROJECT_ROOT/.github/copilot-instructions.md" ]; then
  echo "copilot"
  exit 0
fi

# OpenCode — .agents/ (plural) directory
if [ -d "$PROJECT_ROOT/.agents" ]; then
  echo "opencode"
  exit 0
fi

# OpenClaw — .openclaw/ directory
if [ -d "$PROJECT_ROOT/.openclaw" ]; then
  echo "openclaw"
  exit 0
fi

# Claude Code / generic — .agent/ (singular) directory
if [ -d "$PROJECT_ROOT/.agent" ]; then
  echo "claude-code"
  exit 0
fi

# Gemini CLI — .gemini/ directory (without antigravity subfolder)
if [ -d "$PROJECT_ROOT/.gemini" ]; then
  echo "gemini"
  exit 0
fi

# Codex CLI — AGENTS.md at root (generic, low priority)
if [ -f "$PROJECT_ROOT/AGENTS.md" ] && ! [ -d "$PROJECT_ROOT/.agent" ]; then
  echo "codex"
  exit 0
fi

# --- Fallback ---
echo "unknown"
exit 0
