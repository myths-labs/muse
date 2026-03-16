#!/bin/bash
# MUSE — Skill Format Converter
# Convert MUSE skills to/from other AI coding tool formats.
#
# Supports:
#   Export: cursor, windsurf, copilot, openclaw, aider, antigravity
#   Import: agency-agents repo → MUSE skill format
#
# Usage:
#   ./scripts/convert-skills.sh --tool cursor [--target ./output]
#   ./scripts/convert-skills.sh --tool windsurf [--target ./output]
#   ./scripts/convert-skills.sh --tool copilot [--target ./output]
#   ./scripts/convert-skills.sh --tool openclaw [--target ./output]
#   ./scripts/convert-skills.sh --tool aider [--target ./output]
#   ./scripts/convert-skills.sh --tool antigravity [--target ./output]
#   ./scripts/convert-skills.sh --tool all [--target ./output]
#   ./scripts/convert-skills.sh --import agency-agents /path/to/agency-agents
#   ./scripts/convert-skills.sh --help
#
# Inspired by agency-agents/scripts/convert.sh (35K+ ⭐)

set -euo pipefail

# ─── Colors ───
if [[ -t 1 && -z "${NO_COLOR:-}" && "${TERM:-}" != "dumb" ]]; then
  GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; RED=$'\033[0;31m'
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RESET=$'\033[0m'
else
  GREEN=''; YELLOW=''; RED=''; BOLD=''; DIM=''; RESET=''
fi

info()   { printf "  ${GREEN}✓${RESET} %s\n" "$*"; }
warn()   { printf "  ${YELLOW}⚠${RESET} %s\n" "$*"; }
error()  { printf "  ${RED}✗${RESET} %s\n" "$*" >&2; }
header() { echo -e "\n${BOLD}$*${RESET}"; }

# ─── Paths ───
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
TODAY="$(date +%Y-%m-%d)"

# ─── Helpers ───

# Extract YAML frontmatter field value
get_field() {
  local field="$1" file="$2"
  awk -v f="$field" '
    /^---$/ { fm++; next }
    fm == 1 && $0 ~ "^" f ": " { sub("^" f ": ", ""); print; exit }
  ' "$file"
}

# Extract markdown body (everything after frontmatter)
get_body() {
  awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$1"
}

# Slugify a name: "Frontend Developer" → "frontend-developer"
slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//'
}

# Count skills
count_skills() {
  find "$SKILLS_DIR" -name "SKILL.md" -type f 2>/dev/null | wc -l | tr -d ' '
}

# ─── Per-Tool Converters ───

convert_cursor() {
  local file="$1" target_dir="$2"
  local name description slug outfile body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  [[ -z "$name" ]] && return
  slug="muse-$(slugify "$name")"
  body="$(get_body "$file")"

  outfile="$target_dir/.cursor/rules/${slug}.mdc"
  mkdir -p "$(dirname "$outfile")"

  cat > "$outfile" <<HEREDOC
---
description: ${description}
globs:
alwaysApply: false
---
# ${name} (MUSE Skill)

${body}
HEREDOC
}

convert_windsurf() {
  local file="$1" target_dir="$2"
  # Windsurf uses a single .windsurfrules file — accumulate
  WINDSURF_CONTENT+="
---

## $(get_field "name" "$file")

$(get_body "$file")
"
}

convert_copilot() {
  local file="$1" target_dir="$2"
  # Copilot uses a single copilot-instructions.md — accumulate
  COPILOT_CONTENT+="
---

## $(get_field "name" "$file")

$(get_body "$file")
"
}

convert_openclaw() {
  local file="$1" target_dir="$2"
  local name description slug outdir body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  [[ -z "$name" ]] && return
  slug="muse-$(slugify "$name")"
  body="$(get_body "$file")"

  outdir="$target_dir/.openclaw/agents/$slug"
  mkdir -p "$outdir"

  # SOUL.md — identity
  cat > "$outdir/SOUL.md" <<HEREDOC
# ${name}

${description}
HEREDOC

  # AGENTS.md — behavior
  cat > "$outdir/AGENTS.md" <<HEREDOC
# ${name} — Agent Behavior

${body}
HEREDOC
}

convert_aider() {
  local file="$1" target_dir="$2"
  # Aider uses a single CONVENTIONS.md — accumulate
  AIDER_CONTENT+="
---

## $(get_field "name" "$file")

$(get_body "$file")
"
}

convert_antigravity() {
  local file="$1" target_dir="$2"
  local name description slug outdir outfile body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  [[ -z "$name" ]] && return
  slug="muse-$(slugify "$name")"
  body="$(get_body "$file")"

  outdir="$target_dir/.gemini/antigravity/skills/$slug"
  outfile="$outdir/SKILL.md"
  mkdir -p "$outdir"

  cat > "$outfile" <<HEREDOC
---
name: ${slug}
description: ${description}
risk: low
source: community
date_added: '${TODAY}'
---
${body}
HEREDOC
}

# ─── Import: agency-agents → MUSE ───

import_agency_agents() {
  local source_dir="$1"
  local output_dir="$REPO_ROOT/skills/imported/agency-agents"
  local count=0

  if [ ! -d "$source_dir" ]; then
    error "agency-agents repo not found at: $source_dir"
    exit 1
  fi

  header "📥 Importing agency-agents → MUSE format"
  echo "  Source: $source_dir"
  echo "  Target: $output_dir"
  echo ""

  # agency-agents directories
  local agent_dirs=(
    academic design engineering game-development marketing paid-media
    sales product project-management testing support spatial-computing specialized
  )

  for dir in "${agent_dirs[@]}"; do
    local dirpath="$source_dir/$dir"
    [[ -d "$dirpath" ]] || continue

    while IFS= read -r -d '' file; do
      # Skip files without frontmatter
      local first_line
      first_line="$(head -1 "$file")"
      [[ "$first_line" == "---" ]] || continue

      local name description body slug skill_dir skill_file
      name="$(get_field "name" "$file")"
      [[ -z "$name" ]] && continue

      description="$(get_field "description" "$file")"
      body="$(get_body "$file")"
      slug="agency-$(slugify "$name")"
      skill_dir="$output_dir/$slug"
      skill_file="$skill_dir/SKILL.md"

      mkdir -p "$skill_dir"

      cat > "$skill_file" <<HEREDOC
---
name: ${slug}
description: ${description}. Imported from agency-agents (${dir} division). Use when ${name,,} expertise is needed.
source: agency-agents
date_imported: '${TODAY}'
---

${body}
HEREDOC

      info "Imported: $slug (from $dir/)"
      (( count++ )) || true
    done < <(find "$dirpath" -name "*.md" -type f -print0 | sort -z)
  done

  echo ""
  info "Imported $count agents → $output_dir"
  echo ""
  echo "  ${DIM}To use imported skills, copy desired ones to:${RESET}"
  echo "  ${DIM}  ~/.claude/skills/ or your project's skills/ directory${RESET}"
  echo ""
}

# ─── Main Export Loop ───

run_export() {
  local tool="$1" target_dir="$2"
  local count=0

  # Initialize accumulators for single-file formats
  WINDSURF_CONTENT="# MUSE Skills
# Auto-generated by MUSE convert-skills.sh on ${TODAY}
# Source: ${REPO_ROOT}/skills/
# Regenerate with: ./scripts/convert-skills.sh --tool windsurf"

  COPILOT_CONTENT="# MUSE Skills
# Auto-generated by MUSE convert-skills.sh on ${TODAY}
# Source: ${REPO_ROOT}/skills/
# Regenerate with: ./scripts/convert-skills.sh --tool copilot"

  AIDER_CONTENT="# MUSE Skills
# Auto-generated by MUSE convert-skills.sh on ${TODAY}
# Source: ${REPO_ROOT}/skills/
# Regenerate with: ./scripts/convert-skills.sh --tool aider"

  while IFS= read -r -d '' skill_file; do
    local name
    name="$(get_field "name" "$skill_file")"
    [[ -z "$name" ]] && continue

    case "$tool" in
      cursor)       convert_cursor       "$skill_file" "$target_dir" ;;
      windsurf)     convert_windsurf     "$skill_file" "$target_dir" ;;
      copilot)      convert_copilot      "$skill_file" "$target_dir" ;;
      openclaw)     convert_openclaw     "$skill_file" "$target_dir" ;;
      aider)        convert_aider        "$skill_file" "$target_dir" ;;
      antigravity)  convert_antigravity  "$skill_file" "$target_dir" ;;
    esac

    (( count++ )) || true
  done < <(find "$SKILLS_DIR" -name "SKILL.md" -type f -print0 | sort -z)

  # Write accumulated single-file formats
  case "$tool" in
    windsurf)
      local outfile="$target_dir/.windsurfrules"
      echo "$WINDSURF_CONTENT" > "$outfile"
      info "Generated: $outfile"
      ;;
    copilot)
      local outdir="$target_dir/.github"
      mkdir -p "$outdir"
      local outfile="$outdir/copilot-instructions.md"
      echo "$COPILOT_CONTENT" > "$outfile"
      info "Generated: $outfile"
      ;;
    aider)
      local outfile="$target_dir/CONVENTIONS.md"
      echo "$AIDER_CONTENT" > "$outfile"
      info "Generated: $outfile"
      ;;
  esac

  echo ""
  info "Converted $count skills → $tool format"
}

# ─── Usage ───

usage() {
  echo ""
  echo "🎭 MUSE — Skill Format Converter"
  echo "═══════════════════════════════════"
  echo ""
  echo "Export MUSE skills to other AI coding tools:"
  echo ""
  echo "  ${BOLD}./scripts/convert-skills.sh --tool <tool> [--target <dir>]${RESET}"
  echo ""
  echo "Supported tools:"
  echo "  cursor       → .cursor/rules/*.mdc (per-skill rule files)"
  echo "  windsurf     → .windsurfrules (single combined file)"
  echo "  copilot      → .github/copilot-instructions.md (single file)"
  echo "  openclaw     → .openclaw/agents/*/SOUL.md + AGENTS.md"
  echo "  aider        → CONVENTIONS.md (single combined file)"
  echo "  antigravity  → .gemini/antigravity/skills/*/SKILL.md"
  echo "  all          → all formats at once"
  echo ""
  echo "Import from agency-agents (35K+ ⭐):"
  echo ""
  echo "  ${BOLD}./scripts/convert-skills.sh --import agency-agents /path/to/repo${RESET}"
  echo ""
  echo "Options:"
  echo "  --tool <name>   Target tool format (required for export)"
  echo "  --target <dir>  Output directory (default: current directory)"
  echo "  --import <fmt>  Import format (currently: agency-agents)"
  echo "  --list          List available MUSE skills"
  echo "  --help          Show this help"
  echo ""
  echo "Examples:"
  echo "  ./scripts/convert-skills.sh --tool cursor --target ~/myproject"
  echo "  ./scripts/convert-skills.sh --tool all --target ./output"
  echo "  ./scripts/convert-skills.sh --import agency-agents ~/code/agency-agents"
  echo "  ./scripts/convert-skills.sh --list"
  echo ""
  exit 0
}

list_skills() {
  echo ""
  echo "🎭 MUSE Skills ($(count_skills) total)"
  echo "═══════════════════════════════════"
  echo ""

  for tier_dir in core toolkit ecosystem; do
    local tier_path="$SKILLS_DIR/$tier_dir"
    [[ -d "$tier_path" ]] || continue

    local tier_icon=""
    case "$tier_dir" in
      core)      tier_icon="🔵" ;;
      toolkit)   tier_icon="🟢" ;;
      ecosystem) tier_icon="🟠" ;;
    esac

    echo "  ${BOLD}${tier_icon} ${tier_dir}${RESET}"

    while IFS= read -r -d '' skill_file; do
      local name description
      name="$(get_field "name" "$skill_file")"
      [[ -z "$name" ]] && continue
      description="$(get_field "description" "$skill_file")"
      # Truncate description to 60 chars
      if [ ${#description} -gt 60 ]; then
        description="${description:0:57}..."
      fi
      echo "    ${name}  ${DIM}${description}${RESET}"
    done < <(find "$tier_path" -name "SKILL.md" -type f -print0 | sort -z)
    echo ""
  done

  exit 0
}

# ─── Parse Args ───

TOOL=""
TARGET_DIR="."
IMPORT_FMT=""
IMPORT_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tool)
      TOOL="$2"
      shift 2
      ;;
    --target)
      TARGET_DIR="$2"
      shift 2
      ;;
    --import)
      IMPORT_FMT="$2"
      IMPORT_PATH="${3:-}"
      shift 2
      [[ -n "$IMPORT_PATH" ]] && shift
      ;;
    --list)
      list_skills
      ;;
    --help|-h)
      usage
      ;;
    *)
      error "Unknown option: $1"
      usage
      ;;
  esac
done

# ─── Execute ───

echo ""
echo "🎭 MUSE — Skill Format Converter"
echo "═══════════════════════════════════"

# Import mode
if [[ -n "$IMPORT_FMT" ]]; then
  case "$IMPORT_FMT" in
    agency-agents)
      if [[ -z "$IMPORT_PATH" ]]; then
        error "Usage: --import agency-agents /path/to/agency-agents"
        exit 1
      fi
      import_agency_agents "$IMPORT_PATH"
      ;;
    *)
      error "Unknown import format: $IMPORT_FMT"
      echo "  Supported: agency-agents"
      exit 1
      ;;
  esac
  exit 0
fi

# Export mode
if [[ -z "$TOOL" ]]; then
  error "No tool specified. Use --tool <name> or --help"
  exit 1
fi

TARGET_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd || echo "$TARGET_DIR")"
mkdir -p "$TARGET_DIR"

SKILL_COUNT="$(count_skills)"
echo ""
echo "  Skills: $SKILL_COUNT"
echo "  Target: $TARGET_DIR"

if [[ "$TOOL" == "all" ]]; then
  for t in cursor windsurf copilot openclaw aider antigravity; do
    header "📤 Exporting → $t"
    run_export "$t" "$TARGET_DIR"
  done
else
  header "📤 Exporting → $TOOL"
  run_export "$TOOL" "$TARGET_DIR"
fi

echo ""
echo "  ${DIM}Skills source: ${REPO_ROOT}/skills/${RESET}"
echo ""
