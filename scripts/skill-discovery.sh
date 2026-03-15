#!/bin/bash
# MUSE Skill Discovery — browse, search, and install skills
# Usage:
#   ./scripts/skill-discovery.sh list              # List all available skills
#   ./scripts/skill-discovery.sh search <query>     # Search skills by keyword
#   ./scripts/skill-discovery.sh info <skill-name>  # Show skill details
#   ./scripts/skill-discovery.sh install <skill-name> [target-dir]  # Install a skill
#   ./scripts/skill-discovery.sh index              # Generate SKILL_INDEX.md

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MUSE_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_DIR="$MUSE_ROOT/skills"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Helpers ─────────────────────────────────────────────────

extract_frontmatter() {
    local file="$1"
    local field="$2"
    # Extract value between --- markers
    sed -n '/^---$/,/^---$/p' "$file" | grep "^${field}:" | sed "s/^${field}: *//" | sed 's/^"//' | sed 's/"$//'
}

get_tier() {
    local path="$1"
    if [[ "$path" == *"/core/"* ]]; then
        echo "core"
    elif [[ "$path" == *"/ecosystem/"* ]]; then
        echo "ecosystem"
    elif [[ "$path" == *"/toolkit/"* ]]; then
        echo "toolkit"
    else
        echo "unknown"
    fi
}

get_tier_emoji() {
    case "$1" in
        core)      echo "🔵" ;;
        toolkit)   echo "🟢" ;;
        ecosystem) echo "🟠" ;;
        *)         echo "⚪" ;;
    esac
}

count_lines() {
    wc -l < "$1" | tr -d ' '
}

# ─── Commands ────────────────────────────────────────────────

cmd_list() {
    echo -e "${BOLD}📦 MUSE Skill Index${NC}"
    echo ""

    local total=0
    local core_count=0
    local toolkit_count=0
    local eco_count=0

    # Collect and sort
    while IFS= read -r skill_file; do
        local name
        name=$(extract_frontmatter "$skill_file" "name")
        local desc
        desc=$(extract_frontmatter "$skill_file" "description")
        local tier
        tier=$(get_tier "$skill_file")
        local emoji
        emoji=$(get_tier_emoji "$tier")
        local lines
        lines=$(count_lines "$skill_file")

        # Truncate description to 80 chars
        if [ ${#desc} -gt 80 ]; then
            desc="${desc:0:77}..."
        fi

        printf "  %s %-30s %s\n" "$emoji" "${BOLD}${name}${NC}" "$desc"
        total=$((total + 1))

        case "$tier" in
            core)      core_count=$((core_count + 1)) ;;
            toolkit)   toolkit_count=$((toolkit_count + 1)) ;;
            ecosystem) eco_count=$((eco_count + 1)) ;;
        esac
    done < <(find "$SKILLS_DIR" -name "SKILL.md" -type f | sort)

    echo ""
    echo -e "${BOLD}Total: ${total} skills${NC} (🔵 Core: ${core_count} | 🟢 Toolkit: ${toolkit_count} | 🟠 Ecosystem: ${eco_count})"
    echo ""
    echo -e "Use ${CYAN}./scripts/skill-discovery.sh info <name>${NC} for details"
    echo -e "Use ${CYAN}./scripts/skill-discovery.sh search <query>${NC} to search"
}

cmd_search() {
    local query="${1:-}"
    if [ -z "$query" ]; then
        echo -e "${RED}Error: search query required${NC}"
        echo "Usage: ./scripts/skill-discovery.sh search <query>"
        exit 1
    fi

    echo -e "${BOLD}🔍 Searching for: ${CYAN}${query}${NC}"
    echo ""

    local found=0
    while IFS= read -r skill_file; do
        local name
        name=$(extract_frontmatter "$skill_file" "name")
        local desc
        desc=$(extract_frontmatter "$skill_file" "description")
        local tier
        tier=$(get_tier "$skill_file")
        local emoji
        emoji=$(get_tier_emoji "$tier")

        # Case-insensitive search in name + description
        if echo "$name $desc" | grep -iq "$query"; then
            if [ ${#desc} -gt 80 ]; then
                desc="${desc:0:77}..."
            fi
            printf "  %s %-30s %s\n" "$emoji" "${BOLD}${name}${NC}" "$desc"
            found=$((found + 1))
        fi
    done < <(find "$SKILLS_DIR" -name "SKILL.md" -type f | sort)

    echo ""
    if [ $found -eq 0 ]; then
        echo -e "${YELLOW}No skills found matching '${query}'${NC}"
    else
        echo -e "${GREEN}Found ${found} skill(s)${NC}"
    fi
}

cmd_info() {
    local skill_name="${1:-}"
    if [ -z "$skill_name" ]; then
        echo -e "${RED}Error: skill name required${NC}"
        echo "Usage: ./scripts/skill-discovery.sh info <skill-name>"
        exit 1
    fi

    # Find the skill
    local skill_file
    skill_file=$(find "$SKILLS_DIR" -name "SKILL.md" -type f | while read -r f; do
        local n
        n=$(extract_frontmatter "$f" "name")
        if [ "$n" = "$skill_name" ]; then
            echo "$f"
            break
        fi
    done)

    if [ -z "$skill_file" ]; then
        echo -e "${RED}Skill '${skill_name}' not found${NC}"
        echo ""
        echo "Available skills matching '${skill_name}':"
        cmd_search "$skill_name"
        exit 1
    fi

    local name desc tier lines deps
    name=$(extract_frontmatter "$skill_file" "name")
    desc=$(extract_frontmatter "$skill_file" "description")
    tier=$(get_tier "$skill_file")
    lines=$(count_lines "$skill_file")
    deps=$(extract_frontmatter "$skill_file" "dependencies" 2>/dev/null || echo "none")

    local rel_path="${skill_file#$MUSE_ROOT/}"

    echo -e "${BOLD}📋 Skill: ${CYAN}${name}${NC}"
    echo ""
    echo -e "  ${BOLD}Tier:${NC}         $(get_tier_emoji "$tier") ${tier}"
    echo -e "  ${BOLD}Path:${NC}         ${rel_path}"
    echo -e "  ${BOLD}Lines:${NC}        ${lines}"
    echo -e "  ${BOLD}Dependencies:${NC} ${deps}"
    echo ""
    echo -e "  ${BOLD}Description:${NC}"
    echo "  $desc"
    echo ""

    # Show if has scripts/ or references/
    local skill_dir
    skill_dir=$(dirname "$skill_file")
    if [ -d "$skill_dir/scripts" ]; then
        echo -e "  ${BOLD}Scripts:${NC}      $(ls "$skill_dir/scripts/" 2>/dev/null | wc -l | tr -d ' ') files"
    fi
    if [ -d "$skill_dir/references" ]; then
        echo -e "  ${BOLD}References:${NC}   $(ls "$skill_dir/references/" 2>/dev/null | wc -l | tr -d ' ') files"
    fi
}

cmd_install() {
    local skill_name="${1:-}"
    local target_dir="${2:-.}"

    if [ -z "$skill_name" ]; then
        echo -e "${RED}Error: skill name required${NC}"
        echo "Usage: ./scripts/skill-discovery.sh install <skill-name> [target-dir]"
        exit 1
    fi

    # Find the skill
    local skill_file
    skill_file=$(find "$SKILLS_DIR" -name "SKILL.md" -type f | while read -r f; do
        local n
        n=$(extract_frontmatter "$f" "name")
        if [ "$n" = "$skill_name" ]; then
            echo "$f"
            break
        fi
    done)

    if [ -z "$skill_file" ]; then
        echo -e "${RED}Skill '${skill_name}' not found${NC}"
        exit 1
    fi

    local skill_dir
    skill_dir=$(dirname "$skill_file")
    local dest="$target_dir/.agent/skills/$skill_name"

    if [ -d "$dest" ]; then
        echo -e "${YELLOW}Skill '${skill_name}' already installed at ${dest}${NC}"
        echo -n "Overwrite? [y/N] "
        read -r answer
        if [[ ! "$answer" =~ ^[Yy]$ ]]; then
            echo "Cancelled."
            exit 0
        fi
    fi

    mkdir -p "$dest"
    cp -r "$skill_dir"/* "$dest/"
    echo -e "${GREEN}✅ Installed '${skill_name}' → ${dest}${NC}"
}

cmd_index() {
    echo -e "${BOLD}📝 Generating SKILL_INDEX.md...${NC}"

    local output="$MUSE_ROOT/SKILL_INDEX.md"
    
    {
        echo "# 📦 MUSE Skill Index"
        echo ""
        echo "> Auto-generated by \`scripts/skill-discovery.sh index\`"
        echo "> Last updated: $(date '+%Y-%m-%d %H:%M')"
        echo "> Total: $(find "$SKILLS_DIR" -name "SKILL.md" -type f | wc -l | tr -d ' ') skills"
        echo ""
        echo "## 🔵 Core Skills"
        echo ""
        echo "Essential skills loaded by default. Required for MUSE to function."
        echo ""
        echo "| Skill | Description |"
        echo "|-------|-------------|"

        find "$SKILLS_DIR/core" -name "SKILL.md" -type f | sort | while read -r f; do
            local name desc
            name=$(extract_frontmatter "$f" "name")
            desc=$(extract_frontmatter "$f" "description")
            if [ ${#desc} -gt 100 ]; then desc="${desc:0:97}..."; fi
            echo "| **${name}** | ${desc} |"
        done

        echo ""
        echo "## 🟢 Toolkit Skills"
        echo ""
        echo "General-purpose development skills. Mix and match based on your workflow."
        echo ""
        echo "| Skill | Description |"
        echo "|-------|-------------|"

        find "$SKILLS_DIR/toolkit" -name "SKILL.md" -type f | sort | while read -r f; do
            local name desc
            name=$(extract_frontmatter "$f" "name")
            desc=$(extract_frontmatter "$f" "description")
            if [ ${#desc} -gt 100 ]; then desc="${desc:0:97}..."; fi
            echo "| **${name}** | ${desc} |"
        done

        echo ""
        echo "## 🟠 Ecosystem Skills"
        echo ""
        echo "Technology-specific skill packs. Install only what matches your stack."
        echo ""

        # Group by pack
        for pack_dir in "$SKILLS_DIR/ecosystem"/*/; do
            local pack_name
            pack_name=$(basename "$pack_dir")
            echo "### ${pack_name}"
            echo ""
            echo "| Skill | Description |"
            echo "|-------|-------------|"

            find "$pack_dir" -name "SKILL.md" -type f | sort | while read -r f; do
                local name desc
                name=$(extract_frontmatter "$f" "name")
                desc=$(extract_frontmatter "$f" "description")
                if [ ${#desc} -gt 100 ]; then desc="${desc:0:97}..."; fi
                echo "| **${name}** | ${desc} |"
            done
            echo ""
        done

        echo "---"
        echo ""
        echo "## CLI Discovery"
        echo ""
        echo '```bash'
        echo "# List all skills"
        echo "./scripts/skill-discovery.sh list"
        echo ""
        echo "# Search by keyword"
        echo './scripts/skill-discovery.sh search "git"'
        echo ""
        echo "# Get skill details"
        echo "./scripts/skill-discovery.sh info git-commit"
        echo ""
        echo "# Install a skill to your project"
        echo "./scripts/skill-discovery.sh install brainstorming /path/to/project"
        echo '```'
    } > "$output"

    echo -e "${GREEN}✅ Generated ${output}${NC}"
    echo -e "  $(wc -l < "$output" | tr -d ' ') lines"
}

# ─── Main ────────────────────────────────────────────────────

case "${1:-help}" in
    list)    cmd_list ;;
    search)  cmd_search "${2:-}" ;;
    info)    cmd_info "${2:-}" ;;
    install) cmd_install "${2:-}" "${3:-}" ;;
    index)   cmd_index ;;
    help|--help|-h)
        echo -e "${BOLD}MUSE Skill Discovery${NC}"
        echo ""
        echo "Usage:"
        echo "  ./scripts/skill-discovery.sh list              List all skills"
        echo "  ./scripts/skill-discovery.sh search <query>     Search by keyword"
        echo "  ./scripts/skill-discovery.sh info <name>        Show skill details"
        echo "  ./scripts/skill-discovery.sh install <name> [dir]  Install a skill"
        echo "  ./scripts/skill-discovery.sh index              Generate SKILL_INDEX.md"
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run with --help for usage"
        exit 1
        ;;
esac
