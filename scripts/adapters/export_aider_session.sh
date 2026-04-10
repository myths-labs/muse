#!/usr/bin/env bash
# export_aider_session.sh — Export Aider chat history to convo/YYMMDD/ (L1 format)
#
# Usage:
#   bash scripts/adapters/export_aider_session.sh "session-title"
#   bash scripts/adapters/export_aider_session.sh "session-title" --project-root /path/to/project
#
# Reads .aider.chat.history.md from the project root and converts it to
# L1-compliant markdown at <project-root>/convo/YYMMDD/YYMMDD-NN-title.md
#
# Aider's history format uses #### headers for roles:
#   #### user\n<message>
#   #### assistant\n<message>
#
# Zero external dependencies — uses python3 stdlib only.
# See docs/CONVO_SPEC.md for the L1 format specification.

set -euo pipefail

TITLE="${1:-session}"
shift || true

PROJECT_ROOT_OVERRIDE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --project-root)
      PROJECT_ROOT_OVERRIDE="${2:-}"
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

HISTORY_FILE="$REPO_ROOT/.aider.chat.history.md"
if [ ! -f "$HISTORY_FILE" ]; then
  echo "❌ No Aider chat history found: $HISTORY_FILE" >&2
  exit 1
fi

DATE=$(date +%y%m%d)
OUT_DIR="$REPO_ROOT/convo/$DATE"
mkdir -p "$OUT_DIR"

# Find next sequence number (NN)
EXISTING=$(find "$OUT_DIR" -maxdepth 1 -name "${DATE}-*.md" 2>/dev/null | wc -l | tr -d ' ')
NN=$(printf "%02d" $((EXISTING + 1)))
OUT="$OUT_DIR/${DATE}-${NN}-${TITLE_SAFE}.md"

python3 - "$HISTORY_FILE" "$OUT" "$REPO_ROOT" "$TITLE" <<'PY'
import sys, re
from datetime import datetime

src, dst, project, title = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

with open(src, encoding='utf-8') as f:
    content = f.read()

# Parse #### user / #### assistant blocks
# Aider format: "#### <role>\n<content until next #### or EOF>"
blocks = re.split(r'^####\s+', content, flags=re.MULTILINE)

messages = []
for block in blocks:
    block = block.strip()
    if not block:
        continue
    # First line is the role, rest is content
    lines = block.split('\n', 1)
    role = lines[0].strip().lower()
    text = lines[1].strip() if len(lines) > 1 else ''
    if role in ('user', 'human') and text:
        messages.append(('user', text))
    elif role in ('assistant', 'ai', 'aider') and text:
        messages.append(('assistant', text))

# Build L1-compliant output
out = []
out.append(f"# Session — {title}")
out.append("")
out.append(f"- **Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
out.append(f"- **Tool:** aider")
out.append(f"- **Project:** `{project}`")
out.append(f"- **Messages:** {len(messages)}")
out.append("")
out.append("---")
out.append("")

for role, text in messages:
    if role == 'user':
        out.append("## 👤 User")
    else:
        out.append("## 🤖 Assistant")
    out.append("")
    out.append(text)
    out.append("")

with open(dst, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print(f"✅ Exported {len(messages)} messages → {dst}")
PY
