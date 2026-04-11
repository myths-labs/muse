#!/usr/bin/env bash
# export_cc_session.sh — Export Claude Code session to convo/YYMMDD/ (L1 format)
#
# Usage:
#   bash scripts/adapters/export_cc_session.sh "session-title"
#   bash scripts/adapters/export_cc_session.sh "session-title" --project-root /path/to/project
#
# Reads the latest JSONL transcript from ~/.claude/projects/<encoded-cwd>/
# and converts it to L1-compliant markdown at <project-root>/convo/YYMMDD/YYMMDD-NN-title.md
#
# --project-root PATH  Override the output root (used by bye.md Step 5 to route
#                      exports to the active role's project).
#                      Default: git main repo root → $(pwd) fallback.
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

# CC resolves project dir from the git repo root, not pwd.
# In worktrees, pwd differs from repo root — use git-common-dir to find the real root.
GIT_COMMON_FOR_CC="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
if [ -n "$GIT_COMMON_FOR_CC" ]; then
  CWD="$(dirname "$GIT_COMMON_FOR_CC")"
else
  CWD="$(pwd)"
fi
# CC encodes cwd by replacing / with - only (dots are preserved)
ENCODED="$(echo "$CWD" | sed -e 's|/|-|g')"
PROJECT_DIR="$HOME/.claude/projects/$ENCODED"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ No Claude Code project dir found: $PROJECT_DIR" >&2
  echo "   (Are you running this from a directory you've used CC in?)" >&2
  exit 1
fi

# Latest jsonl by mtime
JSONL=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1 || true)
if [ -z "$JSONL" ]; then
  echo "❌ No JSONL session found in $PROJECT_DIR" >&2
  exit 1
fi

# Resolve project root — where the convo/ folder lives.
# Priority:
#   1. --project-root PATH (from bye.md Step 5 role routing)
#   2. git main repo root (worktree-safe — uses --git-common-dir)
#   3. $(pwd) fallback
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
OUT_DIR="$REPO_ROOT/convo/$DATE"
mkdir -p "$OUT_DIR"

# Find next sequence number (NN)
EXISTING=$(find "$OUT_DIR" -maxdepth 1 -name "${DATE}-*.md" 2>/dev/null | wc -l | tr -d ' ')
NN=$(printf "%02d" $((EXISTING + 1)))
OUT="$OUT_DIR/${DATE}-${NN}-${TITLE_SAFE}.md"

python3 - "$JSONL" "$OUT" "$CWD" "$TITLE" <<'PY'
import json, sys, os
from datetime import datetime

src, dst, cwd, title = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

entries = []
with open(src, encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass

def extract(content):
    """Extract text from a message content field (str or list of blocks)."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)

    parts = []
    for item in content:
        if not isinstance(item, dict):
            continue
        t = item.get('type')

        if t == 'text':
            parts.append(item.get('text', ''))

        elif t == 'thinking':
            think = item.get('thinking', '').strip()
            if think:
                parts.append(f"\n<details><summary>Thinking</summary>\n\n{think}\n\n</details>\n")

        elif t == 'tool_use':
            name = item.get('name', '?')
            inp = item.get('input', {})
            inp_str = json.dumps(inp, indent=2, ensure_ascii=False)
            if len(inp_str) > 2000:
                inp_str = inp_str[:2000] + '\n... [truncated]'
            parts.append(f"\n```json\n// Tool: {name}\n{inp_str}\n```\n")

        elif t == 'tool_result':
            val = item.get('content', '')
            if isinstance(val, list):
                val = ''.join(
                    c.get('text', '') if isinstance(c, dict) else str(c)
                    for c in val
                )
            val = str(val)
            if len(val) > 1500:
                val = val[:1500] + '\n... [truncated]'
            parts.append(f"\n```\n// Result\n{val}\n```\n")

    return '\n'.join(p for p in parts if p)

# Count messages for header
msg_count = sum(1 for e in entries if e.get('type') in ('user', 'assistant'))

out = []
out.append(f"# Session — {title}")
out.append("")
out.append(f"- **Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
out.append(f"- **Tool:** claude-code")
out.append(f"- **Project:** `{cwd}`")
out.append(f"- **Messages:** {msg_count}")
out.append("")
out.append("---")
out.append("")

for entry in entries:
    etype = entry.get('type')

    if etype == 'summary':
        out.append("## 📝 Prior Summary")
        out.append("")
        out.append(entry.get('summary', ''))
        out.append("")

    elif etype == 'user':
        msg = entry.get('message', {})
        text = extract(msg.get('content', '')).strip()
        if text:
            out.append("## 👤 User")
            out.append("")
            out.append(text)
            out.append("")

    elif etype == 'assistant':
        msg = entry.get('message', {})
        text = extract(msg.get('content', '')).strip()
        if text:
            out.append("## 🤖 Assistant")
            out.append("")
            out.append(text)
            out.append("")

with open(dst, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print(f"✅ Exported {msg_count} messages ({len(entries)} entries) → {dst}")
PY
