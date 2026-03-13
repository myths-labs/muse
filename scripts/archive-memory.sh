#!/bin/bash
# MUSE — Memory Archive Script
# Archives old memory/ daily logs to memory/archive/
# Preserves lessons by running /distill first (manual step)
#
# Usage:
#   ./scripts/archive-memory.sh [project-dir] [--days 30] [--dry-run]
#
# Options:
#   --days N     Archive files older than N days (default: 30)
#   --dry-run    Show what would be archived without moving files

set -e

# ─── Colors ───
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
DIM='\033[2m'
RESET='\033[0m'

info()  { echo -e "  ${GREEN}✓${RESET} $1"; }
warn()  { echo -e "  ${YELLOW}⚠${RESET} $1"; }

# ─── Args ───
DAYS=30
DRY_RUN=false
TARGET_DIR="."

while [[ $# -gt 0 ]]; do
  case $1 in
    --days)   DAYS="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    *)        TARGET_DIR="$1"; shift ;;
  esac
done

TARGET_DIR=$(cd "$TARGET_DIR" 2>/dev/null && pwd || echo "$TARGET_DIR")
MEMORY_DIR="$TARGET_DIR/memory"
ARCHIVE_DIR="$MEMORY_DIR/archive"

echo ""
echo "🎭 MUSE — Memory Archive"
echo "═════════════════════════"
echo ""

# ─── Check memory/ exists ───
if [ ! -d "$MEMORY_DIR" ]; then
  warn "No memory/ directory found in $TARGET_DIR"
  exit 1
fi

# ─── Find old files ───
CUTOFF_DATE=$(date -v-${DAYS}d +%Y-%m-%d 2>/dev/null || date -d "-${DAYS} days" +%Y-%m-%d 2>/dev/null)

if [ -z "$CUTOFF_DATE" ]; then
  warn "Could not calculate cutoff date. Falling back to file modification time."
  # Fallback: use find with -mtime
  OLD_FILES=$(find "$MEMORY_DIR" -maxdepth 1 -name "*.md" -mtime +${DAYS} -not -name "CRASH_CONTEXT.md" | sort)
else
  # Parse YYYY-MM-DD from filenames and compare
  OLD_FILES=""
  for f in "$MEMORY_DIR"/????-??-??.md; do
    [ ! -f "$f" ] && continue
    filename=$(basename "$f" .md)
    # Compare date strings (lexicographic works for YYYY-MM-DD)
    if [[ "$filename" < "$CUTOFF_DATE" ]]; then
      OLD_FILES="$OLD_FILES $f"
    fi
  done
fi

# ─── Count files ───
FILE_COUNT=0
for f in $OLD_FILES; do
  [ -f "$f" ] && ((FILE_COUNT++))
done

if [ "$FILE_COUNT" -eq 0 ]; then
  info "No memory files older than $DAYS days. Nothing to archive."
  echo ""
  exit 0
fi

echo "  Found $FILE_COUNT file(s) older than $DAYS days (before $CUTOFF_DATE):"
echo ""
for f in $OLD_FILES; do
  [ ! -f "$f" ] && continue
  echo "    ${DIM}$(basename "$f")${RESET}"
done
echo ""

# ─── Dry run? ───
if [ "$DRY_RUN" = true ]; then
  warn "Dry run — no files moved."
  echo ""
  echo "  ${DIM}Run without --dry-run to archive these files.${RESET}"
  echo "  ${DIM}💡 Tip: Run /distill first to extract lessons before archiving.${RESET}"
  echo ""
  exit 0
fi

# ─── Confirm ───
echo "  💡 Have you run /distill to extract lessons? (recommended before archiving)"
read -p "  Archive these $FILE_COUNT files? (y/n) " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "  Cancelled."
  exit 0
fi

# ─── Archive ───
mkdir -p "$ARCHIVE_DIR"

MOVED=0
for f in $OLD_FILES; do
  [ ! -f "$f" ] && continue
  mv "$f" "$ARCHIVE_DIR/"
  ((MOVED++))
done

info "Archived $MOVED file(s) → memory/archive/"
echo ""
echo "  ${DIM}Files moved to: $ARCHIVE_DIR${RESET}"
echo "  ${DIM}To restore: mv memory/archive/YYYY-MM-DD.md memory/${RESET}"
echo ""
