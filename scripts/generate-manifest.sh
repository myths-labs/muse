#!/bin/bash
# MUSE Skill Manifest Generator
# Generates skills/manifest.json — a machine-readable index of all installed skills.
#
# Inspired by garrytan/gbrain's manifest.json pattern for dynamic skill discovery.
# Usage:
#   ./scripts/generate-manifest.sh                # Generate skills/manifest.json
#   ./scripts/generate-manifest.sh --pretty       # Pretty-print with indentation
#   ./scripts/generate-manifest.sh --check        # Verify existing manifest is up-to-date

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MUSE_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_DIR="$MUSE_ROOT/skills"
MANIFEST="$SKILLS_DIR/manifest.json"
TODAY=$(date +%Y-%m-%d)

# ─── Helpers ─────────────────────────────────────────────────

extract_field() {
  local file="$1" field="$2"
  sed -n '/^---$/,/^---$/p' "$file" \
    | grep "^${field}:" \
    | sed "s/^${field}: *//" \
    | sed 's/^"//' | sed 's/"$//' \
    | head -1
}

escape_json() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

detect_category() {
  local path="$1"
  case "$path" in
    skills/core/*)                 echo "core" ;;
    skills/toolkit/*)              echo "toolkit" ;;
    skills/ecosystem/*)            echo "ecosystem" ;;
    skills/growth-distribution/*)  echo "growth" ;;
    *)                             echo "other" ;;
  esac
}

has_dir_contents() {
  local skill_dir="$1" subdir="$2"
  [[ -d "$skill_dir/$subdir" ]] && [[ -n "$(ls -A "$skill_dir/$subdir" 2>/dev/null)" ]]
}

# ─── Main ────────────────────────────────────────────────────

MODE="generate"
PRETTY=false

for arg in "$@"; do
  case "$arg" in
    --pretty) PRETTY=true ;;
    --check)  MODE="check" ;;
    --help|-h)
      echo "Usage: generate-manifest.sh [--pretty] [--check]"
      echo "  --pretty   Pretty-print JSON output"
      echo "  --check    Verify existing manifest matches current skills (exit 1 if stale)"
      exit 0
      ;;
  esac
done

# Collect all skills
SKILL_FILES=$(find "$SKILLS_DIR" -name "SKILL.md" | sort)
TOTAL=$(echo "$SKILL_FILES" | wc -l | tr -d ' ')

# Build JSON
{
  echo "{"
  echo "  \"version\": \"1.0.0\","
  echo "  \"generated\": \"$TODAY\","
  echo "  \"generator\": \"scripts/generate-manifest.sh\","
  echo "  \"total\": $TOTAL,"
  echo "  \"categories\": {"

  # Count per category
  CORE=0; TOOLKIT=0; ECOSYSTEM=0; GROWTH=0
  while IFS= read -r f; do
    rel="${f#$MUSE_ROOT/}"
    cat=$(detect_category "$rel")
    case "$cat" in
      core)      CORE=$((CORE+1)) ;;
      toolkit)   TOOLKIT=$((TOOLKIT+1)) ;;
      ecosystem) ECOSYSTEM=$((ECOSYSTEM+1)) ;;
      growth)    GROWTH=$((GROWTH+1)) ;;
    esac
  done <<< "$SKILL_FILES"

  echo "    \"core\": $CORE,"
  echo "    \"toolkit\": $TOOLKIT,"
  echo "    \"ecosystem\": $ECOSYSTEM,"
  echo "    \"growth\": $GROWTH"
  echo "  },"
  echo "  \"skills\": ["

  FIRST=true
  while IFS= read -r f; do
    skill_dir="$(dirname "$f")"
    rel="${f#$MUSE_ROOT/}"
    rel_dir="${skill_dir#$MUSE_ROOT/}"

    name=$(extract_field "$f" "name")
    desc=$(extract_field "$f" "description")
    category=$(detect_category "$rel")
    size=$(wc -c < "$f" | tr -d ' ')

    # Truncate description to 200 chars
    if [[ ${#desc} -gt 200 ]]; then
      desc="${desc:0:197}..."
    fi

    name_escaped=$(escape_json "$name")
    desc_escaped=$(escape_json "$desc")

    # Detect extra assets
    has_data=false
    has_scripts=false
    has_dir_contents "$skill_dir" "data" && has_data=true
    has_dir_contents "$skill_dir" "scripts" && has_scripts=true
    # Also check for any non-SKILL.md files
    extra_files=$(find "$skill_dir" -maxdepth 1 -type f ! -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$FIRST" == "true" ]]; then
      FIRST=false
    else
      echo ","
    fi

    printf '    {'
    printf '"name": "%s"' "$name_escaped"
    printf ', "description": "%s"' "$desc_escaped"
    printf ', "category": "%s"' "$category"
    printf ', "path": "%s"' "$rel_dir"
    printf ', "sizeBytes": %d' "$size"
    [[ "$has_data" == "true" ]] && printf ', "hasData": true'
    [[ "$has_scripts" == "true" ]] && printf ', "hasScripts": true'
    [[ "$extra_files" -gt 0 ]] && printf ', "extraFiles": %d' "$extra_files"
    printf '}'
  done <<< "$SKILL_FILES"

  echo ""
  echo "  ]"
  echo "}"
} > "$MANIFEST.tmp"

if [[ "$MODE" == "check" ]]; then
  if [[ ! -f "$MANIFEST" ]]; then
    echo "❌ No manifest.json found. Run without --check to generate."
    exit 1
  fi
  if diff -q "$MANIFEST.tmp" "$MANIFEST" > /dev/null 2>&1; then
    echo "✅ manifest.json is up-to-date ($TOTAL skills)"
    rm -f "$MANIFEST.tmp"
    exit 0
  else
    echo "❌ manifest.json is stale. Regenerate with: ./scripts/generate-manifest.sh"
    rm -f "$MANIFEST.tmp"
    exit 1
  fi
fi

mv "$MANIFEST.tmp" "$MANIFEST"

if [[ "$PRETTY" == "true" ]] && command -v python3 &>/dev/null; then
  python3 -c "
import json, sys
with open(sys.argv[1], 'rb') as f:
    data = f.read().decode('utf-8', errors='replace')
parsed = json.loads(data)
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    json.dump(parsed, f, indent=2, ensure_ascii=False)
" "$MANIFEST" 2>/dev/null || true
fi

echo "✅ Generated $MANIFEST ($TOTAL skills)"
echo "   Categories: core=$CORE toolkit=$TOOLKIT ecosystem=$ECOSYSTEM growth=$GROWTH"
