#!/usr/bin/env bash
# export_manual.sh — Generate a blank L1 convo file for manual paste
#
# Usage:
#   bash scripts/adapters/export_manual.sh "session-title"
#   bash scripts/adapters/export_manual.sh "session-title" --project-root /path --tool cursor
#
# Creates a template file at <project-root>/convo/YYMMDD/YYMMDD-NN-title.md
# with L1 headers and instructions for the user to paste their conversation.
#
# Used as fallback for tools without programmatic session access:
# Cursor, Windsurf, Copilot, Codex, Gemini, Antigravity, OpenCode, unknown.
#
# Zero external dependencies.
# See docs/CONVO_SPEC.md for the L1 format specification.

set -euo pipefail

TITLE="${1:-session}"
shift || true

PROJECT_ROOT_OVERRIDE=""
TOOL_ID="manual"
while [ $# -gt 0 ]; do
  case "$1" in
    --project-root)
      PROJECT_ROOT_OVERRIDE="${2:-}"
      shift 2
      ;;
    --tool)
      TOOL_ID="${2:-manual}"
      shift 2
      ;;
    *)
      echo "❌ Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

# Sanitize title for filename
TITLE_SAFE=$(echo "$TITLE" | tr ' /' '--' | tr -cd '[:alnum:]-_')

# Resolve project root
if [ -n "$PROJECT_ROOT_OVERRIDE" ]; then
  REPO_ROOT="$PROJECT_ROOT_OVERRIDE"
  if [ ! -d "$REPO_ROOT" ]; then
    echo "❌ --project-root does not exist: $REPO_ROOT" >&2
    exit 1
  fi
else
  GIT_COMMON="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  if [ -n "$GIT_COMMON" ]; then
    REPO_ROOT="$(dirname "$GIT_COMMON")"
  else
    REPO_ROOT="$(pwd)"
  fi
fi

DATE=$(date +%y%m%d)
FULL_DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
OUT_DIR="$REPO_ROOT/convo/$DATE"
mkdir -p "$OUT_DIR"

# Find next sequence number (NN)
EXISTING=$(find "$OUT_DIR" -maxdepth 1 -name "${DATE}-*.md" 2>/dev/null | wc -l | tr -d ' ')
NN=$(printf "%02d" $((EXISTING + 1)))
OUT="$OUT_DIR/${DATE}-${NN}-${TITLE_SAFE}.md"

cat > "$OUT" <<EOF
# Session — ${TITLE}

- **Exported:** ${FULL_DATE} ${TIME}
- **Tool:** ${TOOL_ID}
- **Project:** \`${REPO_ROOT}\`
- **Messages:** 0

---

> **Manual export**: Paste your conversation below.
> Use \`## 👤 User\` and \`## 🤖 Assistant\` headers to separate messages.
> Delete this instruction block after pasting.

## 👤 User



## 🤖 Assistant



EOF

echo "✅ Template created → $OUT"
echo "   Paste your conversation into the file above."
