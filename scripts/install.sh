#!/bin/bash
# MUSE Multi-Tool Installer
# Installs MUSE skills, workflows, and constitution to any supported AI coding tool.
#
# Usage:
#   ./scripts/install.sh                      # Interactive — auto-detects tools
#   ./scripts/install.sh --tool cursor        # Install for Cursor only
#   ./scripts/install.sh --tool all           # Install for all detected tools
#   ./scripts/install.sh --list               # Show detected tools
#   ./scripts/install.sh --target /path       # Set target project directory
#   ./scripts/install.sh --help               # Show usage
#
# Supported tools: claude, openclaw, cursor, windsurf, gemini, codex

set -euo pipefail

# ── Colour helpers ──
if [[ -t 1 && -z "${NO_COLOR:-}" && "${TERM:-}" != "dumb" ]]; then
  GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; RED=$'\033[0;31m'
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RESET=$'\033[0m'; CYAN=$'\033[0;36m'
else
  GREEN=''; YELLOW=''; RED=''; BOLD=''; DIM=''; RESET=''; CYAN=''
fi

info()   { printf "${GREEN}[✓]${RESET} %s\n" "$*"; }
warn()   { printf "${YELLOW}[!]${RESET} %s\n" "$*"; }
error()  { printf "${RED}[✗]${RESET} %s\n" "$*" >&2; }
header() { echo -e "\n${BOLD}$*${RESET}"; }

# ── Paths ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MUSE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$MUSE_ROOT/skills"
WORKFLOWS_DIR="$MUSE_ROOT/workflows"
TEMPLATES_DIR="$MUSE_ROOT/templates"
TARGET_DIR="."
SELECTED_TOOL=""
SKILL_TIERS="core toolkit"  # default: install core + toolkit

ALL_TOOLS=(claude openclaw cursor windsurf gemini codex)

# ── Usage ──
usage() {
  cat <<EOF
${BOLD}🎭 MUSE Multi-Tool Installer${RESET}

${BOLD}USAGE${RESET}
  ./scripts/install.sh [OPTIONS]

${BOLD}OPTIONS${RESET}
  --tool TOOL      Install for a specific tool (${ALL_TOOLS[*]}, all)
  --target DIR     Target project directory (default: current directory)
  --list           List detected tools and exit
  --core-only      Install core skills only (skip toolkit)
  --help           Show this help

${BOLD}EXAMPLES${RESET}
  ./scripts/install.sh                        # Interactive
  ./scripts/install.sh --tool cursor          # Cursor only
  ./scripts/install.sh --tool all --target .  # All tools, current dir
  ./scripts/install.sh --list                 # Show detected tools

${BOLD}SUPPORTED TOOLS${RESET}
  claude     Claude Code (.agent/skills/ + CLAUDE.md)
  openclaw   OpenClaw (same as Claude Code)
  cursor     Cursor IDE (.cursor/rules/*.mdc)
  windsurf   Windsurf IDE (.windsurf/rules/*.md)
  gemini     Gemini CLI (.gemini/ + GEMINI.md)
  codex      Codex CLI (AGENTS.md — all skills concatenated)
EOF
  exit 0
}

# ── Parse args ──
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tool)    SELECTED_TOOL="$2"; shift 2 ;;
    --target)  TARGET_DIR="$2"; shift 2 ;;
    --list)    SELECTED_TOOL="__list__"; shift ;;
    --core-only) SKILL_TIERS="core"; shift ;;
    --help|-h) usage ;;
    *) error "Unknown option: $1"; usage ;;
  esac
done

# Resolve target path
TARGET_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd || echo "$TARGET_DIR")"

# ── Tool Detection ──
detect_tools() {
  local detected=()

  # Claude Code: check for claude command or .agent/ dir
  if command -v claude &>/dev/null || [[ -d "$TARGET_DIR/.agent" ]]; then
    detected+=(claude)
  fi

  # OpenClaw: check for openclaw or claw command
  if command -v openclaw &>/dev/null || command -v claw &>/dev/null; then
    detected+=(openclaw)
  fi

  # Cursor: check for cursor command or .cursor/ dir
  if command -v cursor &>/dev/null || [[ -d "$TARGET_DIR/.cursor" ]]; then
    detected+=(cursor)
  fi

  # Windsurf: check for windsurf command or .windsurf/ dir
  if command -v windsurf &>/dev/null || [[ -d "$TARGET_DIR/.windsurf" ]] || [[ -f "$TARGET_DIR/.windsurfrules" ]]; then
    detected+=(windsurf)
  fi

  # Gemini CLI: check for gemini command or .gemini/ dir
  if command -v gemini &>/dev/null || [[ -d "$TARGET_DIR/.gemini" ]]; then
    detected+=(gemini)
  fi

  # Codex CLI: check for codex command
  if command -v codex &>/dev/null; then
    detected+=(codex)
  fi

  echo "${detected[@]}"
}

# ── YAML Frontmatter Helpers ──
get_field() {
  local field="$1" file="$2"
  awk -v f="$field" '
    /^---$/ { fm++; next }
    fm == 1 && $0 ~ "^" f ": " { sub("^" f ": ", ""); print; exit }
  ' "$file"
}

get_body() {
  awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$1"
}

# ── Skill Collection ──
collect_skills() {
  local skills=()
  for tier in $SKILL_TIERS; do
    local tier_dir="$SKILLS_DIR/$tier"
    if [[ -d "$tier_dir" ]]; then
      for skill_dir in "$tier_dir"/*/; do
        local skill_file="$skill_dir/SKILL.md"
        if [[ -f "$skill_file" ]]; then
          skills+=("$skill_file")
        fi
      done
    fi
  done
  # Also check ecosystem if it exists
  if [[ -d "$SKILLS_DIR/ecosystem" ]]; then
    for pack_dir in "$SKILLS_DIR/ecosystem"/*/; do
      for skill_dir in "$pack_dir"/*/; do
        local skill_file="$skill_dir/SKILL.md"
        if [[ -f "$skill_file" ]]; then
          skills+=("$skill_file")
        fi
      done
    done
  fi
  echo "${skills[@]}"
}

count_skills() {
  local count=0
  for tier in $SKILL_TIERS; do
    local tier_dir="$SKILLS_DIR/$tier"
    if [[ -d "$tier_dir" ]]; then
      for skill_dir in "$tier_dir"/*/; do
        [[ -f "$skill_dir/SKILL.md" ]] && ((count++))
      done
    fi
  done
  if [[ -d "$SKILLS_DIR/ecosystem" ]]; then
    for pack_dir in "$SKILLS_DIR/ecosystem"/*/; do
      for skill_dir in "$pack_dir"/*/; do
        [[ -f "$skill_dir/SKILL.md" ]] && ((count++))
      done
    done
  fi
  echo "$count"
}

# ══════════════════════════════════════════════
# Per-Tool Installers
# ══════════════════════════════════════════════

install_claude() {
  header "📦 Installing for Claude Code / OpenClaw..."
  local dest="$TARGET_DIR/.agent"
  mkdir -p "$dest/skills" "$dest/workflows"

  # Copy skills preserving directory structure
  for tier in $SKILL_TIERS; do
    if [[ -d "$SKILLS_DIR/$tier" ]]; then
      cp -r "$SKILLS_DIR/$tier" "$dest/skills/"
    fi
  done
  if [[ -d "$SKILLS_DIR/ecosystem" ]]; then
    cp -r "$SKILLS_DIR/ecosystem" "$dest/skills/"
  fi

  # Copy workflows
  cp "$WORKFLOWS_DIR/"*.md "$dest/workflows/" 2>/dev/null || true

  # Copy constitution if not exists
  if [[ ! -f "$TARGET_DIR/CLAUDE.md" ]]; then
    cp "$TEMPLATES_DIR/CLAUDE.md" "$TARGET_DIR/CLAUDE.md"
    info "CLAUDE.md created"
  else
    info "CLAUDE.md already exists (skipped)"
  fi

  info "Skills + Workflows → .agent/ ✅"
}

install_cursor() {
  header "📦 Installing for Cursor..."
  local dest="$TARGET_DIR/.cursor/rules"
  mkdir -p "$dest"

  # Constitution → .mdc with always-apply frontmatter
  local const_src="$TEMPLATES_DIR/CLAUDE.md"
  [[ -f "$TARGET_DIR/CLAUDE.md" ]] && const_src="$TARGET_DIR/CLAUDE.md"

  cat > "$dest/muse-constitution.mdc" <<HEREDOC
---
description: MUSE Constitution — Core rules for AI assistant behavior
alwaysApply: true
---
$(cat "$const_src")
HEREDOC
  info "Constitution → muse-constitution.mdc"

  # Skills → individual .mdc files
  local skill_count=0
  for tier in $SKILL_TIERS; do
    local tier_dir="$SKILLS_DIR/$tier"
    [[ ! -d "$tier_dir" ]] && continue
    for skill_dir in "$tier_dir"/*/; do
      local skill_file="$skill_dir/SKILL.md"
      [[ ! -f "$skill_file" ]] && continue
      local name
      name=$(get_field "name" "$skill_file")
      local description
      description=$(get_field "description" "$skill_file")
      local body
      body=$(get_body "$skill_file")
      [[ -z "$name" ]] && name=$(basename "$skill_dir")

      cat > "$dest/muse-skill-${name}.mdc" <<HEREDOC
---
description: "${description}"
alwaysApply: false
---
${body}
HEREDOC
      ((skill_count++))
    done
  done

  # Workflows → .mdc files
  local wf_count=0
  for wf_file in "$WORKFLOWS_DIR"/*.md; do
    [[ ! -f "$wf_file" ]] && continue
    local wf_name
    wf_name=$(basename "$wf_file" .md)
    local wf_desc
    wf_desc=$(get_field "description" "$wf_file")
    local wf_body
    wf_body=$(get_body "$wf_file")
    [[ -z "$wf_desc" ]] && wf_desc="MUSE workflow: $wf_name"

    cat > "$dest/muse-wf-${wf_name}.mdc" <<HEREDOC
---
description: "${wf_desc}"
alwaysApply: false
---
${wf_body}
HEREDOC
    ((wf_count++))
  done

  info "${skill_count} skills + ${wf_count} workflows → .cursor/rules/ ✅"
}

install_windsurf() {
  header "📦 Installing for Windsurf..."
  local dest="$TARGET_DIR/.windsurf/rules"
  mkdir -p "$dest"

  # Constitution
  local const_src="$TEMPLATES_DIR/CLAUDE.md"
  [[ -f "$TARGET_DIR/CLAUDE.md" ]] && const_src="$TARGET_DIR/CLAUDE.md"

  cat > "$dest/muse-constitution.md" <<HEREDOC
<!-- activation: always -->
$(cat "$const_src")
HEREDOC
  info "Constitution → muse-constitution.md"

  # Skills
  local skill_count=0
  for tier in $SKILL_TIERS; do
    local tier_dir="$SKILLS_DIR/$tier"
    [[ ! -d "$tier_dir" ]] && continue
    for skill_dir in "$tier_dir"/*/; do
      local skill_file="$skill_dir/SKILL.md"
      [[ ! -f "$skill_file" ]] && continue
      local name
      name=$(get_field "name" "$skill_file")
      local body
      body=$(get_body "$skill_file")
      [[ -z "$name" ]] && name=$(basename "$skill_dir")

      cat > "$dest/muse-skill-${name}.md" <<HEREDOC
<!-- activation: model-decision -->
${body}
HEREDOC
      ((skill_count++))
    done
  done

  # Workflows
  local wf_count=0
  for wf_file in "$WORKFLOWS_DIR"/*.md; do
    [[ ! -f "$wf_file" ]] && continue
    local wf_name
    wf_name=$(basename "$wf_file" .md)
    local wf_body
    wf_body=$(get_body "$wf_file")

    cat > "$dest/muse-wf-${wf_name}.md" <<HEREDOC
<!-- activation: model-decision -->
${wf_body}
HEREDOC
    ((wf_count++))
  done

  info "${skill_count} skills + ${wf_count} workflows → .windsurf/rules/ ✅"
}

install_gemini() {
  header "📦 Installing for Gemini CLI..."
  local dest="$TARGET_DIR/.gemini"
  mkdir -p "$dest"

  # Constitution → GEMINI.md
  local const_src="$TEMPLATES_DIR/CLAUDE.md"
  [[ -f "$TARGET_DIR/CLAUDE.md" ]] && const_src="$TARGET_DIR/CLAUDE.md"

  # Start with constitution, replacing CLAUDE.md/AGENTS.md references
  sed 's/CLAUDE\.md/GEMINI.md/g; s/AGENTS\.md/GEMINI.md/g' "$const_src" > "$dest/GEMINI.md"
  info "Constitution → GEMINI.md"

  # Skills → .gemini/skills/*/SKILL.md (native Gemini CLI skill format)
  local skill_count=0
  mkdir -p "$dest/skills"
  for tier in $SKILL_TIERS; do
    local tier_dir="$SKILLS_DIR/$tier"
    [[ ! -d "$tier_dir" ]] && continue
    for skill_dir in "$tier_dir"/*/; do
      local skill_file="$skill_dir/SKILL.md"
      [[ ! -f "$skill_file" ]] && continue
      local name
      name=$(get_field "name" "$skill_file")
      [[ -z "$name" ]] && name=$(basename "$skill_dir")

      local out_dir="$dest/skills/$name"
      mkdir -p "$out_dir"
      cp "$skill_file" "$out_dir/SKILL.md"
      ((skill_count++))
    done
  done

  # Workflows → append to GEMINI.md as sections
  echo "" >> "$dest/GEMINI.md"
  echo "---" >> "$dest/GEMINI.md"
  echo "" >> "$dest/GEMINI.md"
  echo "## MUSE Workflows" >> "$dest/GEMINI.md"
  echo "" >> "$dest/GEMINI.md"
  for wf_file in "$WORKFLOWS_DIR"/*.md; do
    [[ ! -f "$wf_file" ]] && continue
    local wf_name
    wf_name=$(basename "$wf_file" .md)
    local wf_body
    wf_body=$(get_body "$wf_file")
    echo "### /$wf_name" >> "$dest/GEMINI.md"
    echo "" >> "$dest/GEMINI.md"
    echo "$wf_body" >> "$dest/GEMINI.md"
    echo "" >> "$dest/GEMINI.md"
  done

  info "${skill_count} skills → .gemini/skills/ ✅"
  info "Workflows appended to GEMINI.md ✅"
}

install_codex() {
  header "📦 Installing for Codex CLI..."

  local outfile="$TARGET_DIR/AGENTS.md"

  # Start with constitution
  local const_src="$TEMPLATES_DIR/CLAUDE.md"
  [[ -f "$TARGET_DIR/CLAUDE.md" ]] && const_src="$TARGET_DIR/CLAUDE.md"

  # Header
  cat > "$outfile" <<HEREDOC
$(sed 's/CLAUDE\.md/AGENTS.md/g' "$const_src")

---

## MUSE Skills Reference

> The following skills are available. Reference them by name when relevant.

HEREDOC

  # Append each skill as a section
  local skill_count=0
  for tier in $SKILL_TIERS; do
    local tier_dir="$SKILLS_DIR/$tier"
    [[ ! -d "$tier_dir" ]] && continue
    for skill_dir in "$tier_dir"/*/; do
      local skill_file="$skill_dir/SKILL.md"
      [[ ! -f "$skill_file" ]] && continue
      local name
      name=$(get_field "name" "$skill_file")
      local description
      description=$(get_field "description" "$skill_file")
      [[ -z "$name" ]] && name=$(basename "$skill_dir")

      echo "### Skill: $name" >> "$outfile"
      echo "" >> "$outfile"
      echo "> $description" >> "$outfile"
      echo "" >> "$outfile"
      get_body "$skill_file" >> "$outfile"
      echo "" >> "$outfile"
      echo "---" >> "$outfile"
      echo "" >> "$outfile"
      ((skill_count++))
    done
  done

  # Append workflows
  echo "## MUSE Workflows" >> "$outfile"
  echo "" >> "$outfile"
  for wf_file in "$WORKFLOWS_DIR"/*.md; do
    [[ ! -f "$wf_file" ]] && continue
    local wf_name
    wf_name=$(basename "$wf_file" .md)
    echo "### /$wf_name" >> "$outfile"
    echo "" >> "$outfile"
    get_body "$wf_file" >> "$outfile"
    echo "" >> "$outfile"
    echo "---" >> "$outfile"
    echo "" >> "$outfile"
  done

  info "${skill_count} skills + workflows → AGENTS.md ✅"
}

# ══════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════

main() {
  echo ""
  echo "${BOLD}🎭 MUSE Multi-Tool Installer${RESET}"
  echo "════════════════════════════"
  echo ""
  echo "  MUSE Root:  ${DIM}${MUSE_ROOT}${RESET}"
  echo "  Target:     ${DIM}${TARGET_DIR}${RESET}"
  echo "  Skills:     ${DIM}$(count_skills) available${RESET}"
  echo ""

  # Detect installed tools
  local detected
  detected=$(detect_tools)
  local detected_arr=($detected)

  # Handle --list
  if [[ "$SELECTED_TOOL" == "__list__" ]]; then
    header "Detected AI coding tools:"
    if [[ ${#detected_arr[@]} -eq 0 ]]; then
      echo "  ${DIM}(none detected — you can still install with --tool)${RESET}"
    else
      for tool in "${detected_arr[@]}"; do
        echo "  ${GREEN}●${RESET} $tool"
      done
    fi
    echo ""
    echo "All supported tools: ${ALL_TOOLS[*]}"
    exit 0
  fi

  # Handle --tool <specific>
  if [[ -n "$SELECTED_TOOL" ]]; then
    if [[ "$SELECTED_TOOL" == "all" ]]; then
      if [[ ${#detected_arr[@]} -eq 0 ]]; then
        warn "No tools detected. Installing for all supported tools."
        detected_arr=("${ALL_TOOLS[@]}")
      fi
      for tool in "${detected_arr[@]}"; do
        run_install "$tool"
      done
    else
      run_install "$SELECTED_TOOL"
    fi
    print_summary
    exit 0
  fi

  # Interactive mode
  header "Detected tools:"
  if [[ ${#detected_arr[@]} -eq 0 ]]; then
    echo "  ${DIM}(none auto-detected)${RESET}"
  else
    for tool in "${detected_arr[@]}"; do
      echo "  ${GREEN}●${RESET} $tool"
    done
  fi

  echo ""
  echo "Which tool(s) to install for?"
  echo "  [1] Claude Code / OpenClaw ${DIM}(.agent/skills/)${RESET}"
  echo "  [2] Cursor ${DIM}(.cursor/rules/*.mdc)${RESET}"
  echo "  [3] Windsurf ${DIM}(.windsurf/rules/*.md)${RESET}"
  echo "  [4] Gemini CLI ${DIM}(.gemini/skills/)${RESET}"
  echo "  [5] Codex CLI ${DIM}(AGENTS.md)${RESET}"
  echo "  [a] All detected tools"
  echo "  [q] Quit"
  echo ""
  read -p "  Choice [1]: " choice
  choice=${choice:-1}

  case "$choice" in
    1) run_install "claude" ;;
    2) run_install "cursor" ;;
    3) run_install "windsurf" ;;
    4) run_install "gemini" ;;
    5) run_install "codex" ;;
    a|A)
      local tools_to_install=("${detected_arr[@]}")
      [[ ${#tools_to_install[@]} -eq 0 ]] && tools_to_install=("${ALL_TOOLS[@]}")
      for tool in "${tools_to_install[@]}"; do
        run_install "$tool"
      done
      ;;
    q|Q) echo "Bye!"; exit 0 ;;
    *) error "Invalid choice"; exit 1 ;;
  esac

  print_summary
}

run_install() {
  local tool="$1"
  case "$tool" in
    claude|openclaw) install_claude ;;
    cursor)          install_cursor ;;
    windsurf)        install_windsurf ;;
    gemini)          install_gemini ;;
    codex)           install_codex ;;
    *) error "Unknown tool: $tool"; return 1 ;;
  esac
}

print_summary() {
  echo ""
  echo "════════════════════════════"
  echo "${BOLD}🎭 MUSE Installation Complete!${RESET}"
  echo "════════════════════════════"
  echo ""
  echo "Next steps:"
  echo "  1. Edit the constitution file for your project-specific rules"
  echo "  2. Create ${CYAN}memory/${RESET} and ${CYAN}.muse/${RESET} directories"
  echo "  3. Start working: type ${BOLD}/resume${RESET} in your AI tool"
  echo ""
  echo "${DIM}Tip: Install 'nah' for smart permission management:${RESET}"
  echo "  ${CYAN}pip install nah && nah install${RESET}"
  echo "  ${DIM}→ Auto-allows safe ops, blocks dangerous patterns (e.g. curl|bash)${RESET}"
  echo ""
  echo "📖 Docs: https://github.com/myths-labs/muse"
  echo ""
}

main
