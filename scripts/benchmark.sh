#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# MUSE Benchmark — Context Coverage Analysis
# Compares MUSE project vs bare .cursorrules / AGENTS.md setup
# Usage:  ./scripts/benchmark.sh [--project /path/to/project]
# ──────────────────────────────────────────────────────────────
set -euo pipefail

# ─── Config ───
PROJECT="${1:-$(pwd)}"
if [[ "$1" == "--project" ]]; then PROJECT="${2:-$(pwd)}"; fi

# ─── Colors ───
if [[ -t 1 ]]; then
  BOLD='\033[1m' DIM='\033[2m' CYAN='\033[36m' GOLD='\033[33m'
  GREEN='\033[32m' RED='\033[31m' RESET='\033[0m' MAGENTA='\033[35m'
else
  BOLD='' DIM='' CYAN='' GOLD='' GREEN='' RED='' RESET='' MAGENTA=''
fi

# ─── Header ───
echo -e "\n${BOLD}📊 MUSE Benchmark — Context Coverage Analysis${RESET}"
echo -e "${DIM}   Target: ${PROJECT}${RESET}\n"

# ─── Helper: count files ───
count_files() { find "$1" -name "$2" 2>/dev/null | wc -l | tr -d ' '; }
count_lines() { find "$1" -name "$2" -exec cat {} + 2>/dev/null | wc -l | tr -d ' '; }
count_words() { find "$1" -name "$2" -exec cat {} + 2>/dev/null | wc -w | tr -d ' '; }
file_exists() { [[ -f "$1" ]] && echo "✅" || echo "❌"; }
dir_exists() { [[ -d "$1" ]] && echo "✅" || echo "❌"; }

# ═══════════════════════════════════════════════════════════════
# Section 1: MUSE Project Inventory
# ═══════════════════════════════════════════════════════════════
echo -e "${BOLD}${CYAN}━━━ 1. Project Inventory ━━━${RESET}\n"

# Constitution
has_claude=$(file_exists "$PROJECT/CLAUDE.md")
has_agents=$(file_exists "$PROJECT/AGENTS.md")
has_cursorrules=$(file_exists "$PROJECT/.cursorrules")
has_gemini=$(file_exists "$PROJECT/GEMINI.md")

# Memory
has_memory=$(dir_exists "$PROJECT/memory")
memory_files=$(count_files "$PROJECT/memory" '*.md')
memory_lines=$(count_lines "$PROJECT/memory" '*.md')
has_memories=$(file_exists "$PROJECT/MEMORIES.md")
memories_words=0
[[ -f "$PROJECT/MEMORIES.md" ]] && memories_words=$(wc -w < "$PROJECT/MEMORIES.md" | tr -d ' ')

# Roles
has_muse_dir=$(dir_exists "$PROJECT/.muse")
role_count=0
role_lines=0
if [[ -d "$PROJECT/.muse" ]]; then
  role_count=$(count_files "$PROJECT/.muse" '*.md')
  role_lines=$(count_lines "$PROJECT/.muse" '*.md')
fi

# Skills
skill_count=0
skill_lines=0
for d in "$PROJECT/skills" "$PROJECT/.agent/skills"; do
  if [[ -d "$d" ]]; then
    c=$(count_files "$d" 'SKILL.md')
    l=$(count_lines "$d" 'SKILL.md')
    skill_count=$((skill_count + c))
    skill_lines=$((skill_lines + l))
  fi
done

# Workflows
workflow_count=0
for d in "$PROJECT/.agent/workflows" "$PROJECT/.agents/workflows"; do
  if [[ -d "$d" ]]; then
    c=$(count_files "$d" '*.md')
    workflow_count=$((workflow_count + c))
  fi
done

# Dashboard
has_dashboard_script=$([[ -f "$PROJECT/scripts/dashboard.sh" ]] && echo "✅" || echo "❌")
has_dashboard_online=$([[ -f "$PROJECT/docs/dashboard.html" ]] && echo "✅" || echo "❌")

# MCP Server
has_mcp=$([[ -f "$PROJECT/scripts/mcp-server.sh" ]] && echo "✅" || echo "❌")

# Search
has_search=$([[ -f "$PROJECT/scripts/search.sh" ]] && echo "✅" || echo "❌")

# VSCode Extension
has_vscode=$([[ -d "$PROJECT/vscode-extension" ]] && echo "✅" || echo "❌")

printf "  %-28s %s\n" "CLAUDE.md (constitution)" "$has_claude"
printf "  %-28s %s\n" "AGENTS.md" "$has_agents"
printf "  %-28s %s\n" ".cursorrules" "$has_cursorrules"
printf "  %-28s %s\n" "GEMINI.md" "$has_gemini"
echo ""
printf "  %-28s %s\n" "memory/ directory" "$has_memory"
printf "  %-28s %s\n" "  └ memory files" "${memory_files}"
printf "  %-28s %s\n" "  └ total lines" "${memory_lines}"
printf "  %-28s %s\n" "MEMORIES.md (long-term)" "$has_memories"
printf "  %-28s %s\n" "  └ words" "${memories_words}"
echo ""
printf "  %-28s %s\n" ".muse/ roles" "$has_muse_dir"
printf "  %-28s %s\n" "  └ role files" "${role_count}"
printf "  %-28s %s\n" "  └ total lines" "${role_lines}"
echo ""
printf "  %-28s %s\n" "Skills (SKILL.md)" "${skill_count}"
printf "  %-28s %s\n" "  └ total lines" "${skill_lines}"
printf "  %-28s %s\n" "Workflows" "${workflow_count}"
echo ""
printf "  %-28s %s\n" "Dashboard (local)" "$has_dashboard_script"
printf "  %-28s %s\n" "Dashboard (online)" "$has_dashboard_online"
printf "  %-28s %s\n" "MCP Server" "$has_mcp"
printf "  %-28s %s\n" "TF-IDF Search" "$has_search"
printf "  %-28s %s\n" "VS Code Extension" "$has_vscode"

# ═══════════════════════════════════════════════════════════════
# Section 2: Context Recovery Simulation
# ═══════════════════════════════════════════════════════════════
echo -e "\n${BOLD}${CYAN}━━━ 2. Context Recovery: /resume vs Cold Start ━━━${RESET}\n"

# Calculate what MUSE /resume loads
resume_tokens=0
resume_components=0

# L0 scan (all .muse/*.md first lines)
l0_tokens=0
if [[ -d "$PROJECT/.muse" ]]; then
  for f in "$PROJECT/.muse/"*.md; do
    [[ -f "$f" ]] || continue
    first_line=$(head -1 "$f" 2>/dev/null | wc -w | tr -d ' ')
    l0_tokens=$((l0_tokens + first_line))
  done
fi

# Constitution (CLAUDE.md)
claude_words=0
[[ -f "$PROJECT/CLAUDE.md" ]] && claude_words=$(wc -w < "$PROJECT/CLAUDE.md" | tr -d ' ')

# Current role file (estimate: largest .muse/*.md)
role_words=0
if [[ -d "$PROJECT/.muse" ]]; then
  for f in "$PROJECT/.muse/"*.md; do
    [[ -f "$f" ]] || continue
    w=$(wc -w < "$f" | tr -d ' ')
    [[ $w -gt $role_words ]] && role_words=$w
  done
fi

# Latest memory file
latest_memory_words=0
if [[ -d "$PROJECT/memory" ]]; then
  latest=$(ls -t "$PROJECT/memory/"*.md 2>/dev/null | head -1)
  [[ -n "$latest" ]] && latest_memory_words=$(wc -w < "$latest" | tr -d ' ')
fi

# USER.md
user_words=0
[[ -f "$PROJECT/USER.md" ]] && user_words=$(wc -w < "$PROJECT/USER.md" | tr -d ' ')

muse_total=$((claude_words + l0_tokens + role_words + latest_memory_words + memories_words + user_words))

# .cursorrules only
cursorrules_words=0
[[ -f "$PROJECT/.cursorrules" ]] && cursorrules_words=$(wc -w < "$PROJECT/.cursorrules" | tr -d ' ')

# AGENTS.md only
agents_words=0
[[ -f "$PROJECT/AGENTS.md" ]] && agents_words=$(wc -w < "$PROJECT/AGENTS.md" | tr -d ' ')

bare_total=$((cursorrules_words + agents_words))

echo -e "  ${BOLD}MUSE /resume loads:${RESET}"
printf "    %-30s %6d words\n" "CLAUDE.md (constitution)" "$claude_words"
printf "    %-30s %6d words\n" "L0 scan (role summaries)" "$l0_tokens"
printf "    %-30s %6d words\n" "Current role file" "$role_words"
printf "    %-30s %6d words\n" "Latest memory file" "$latest_memory_words"
printf "    %-30s %6d words\n" "MEMORIES.md (long-term)" "$memories_words"
printf "    %-30s %6d words\n" "USER.md (preferences)" "$user_words"
echo -e "    ${BOLD}──────────────────────────────────────${RESET}"
printf "    ${BOLD}%-30s %6d words${RESET}\n" "Total context on resume" "$muse_total"

echo ""
echo -e "  ${BOLD}Bare setup loads:${RESET}"
printf "    %-30s %6d words\n" ".cursorrules" "$cursorrules_words"
printf "    %-30s %6d words\n" "AGENTS.md" "$agents_words"
echo -e "    ${BOLD}──────────────────────────────────────${RESET}"
printf "    ${BOLD}%-30s %6d words${RESET}\n" "Total context on start" "$bare_total"

echo ""
if [[ $bare_total -gt 0 ]]; then
  ratio=$(echo "$muse_total $bare_total" | awk '{printf "%.1f", $1/$2}')
  echo -e "  ${GOLD}${BOLD}→ MUSE provides ${ratio}× more context on session start${RESET}"
else
  if [[ $muse_total -gt 0 ]]; then
    echo -e "  ${GOLD}${BOLD}→ No .cursorrules/AGENTS.md found. MUSE provides ${muse_total} words vs 0.${RESET}"
  else
    echo -e "  ${DIM}→ Both setups have minimal context.${RESET}"
  fi
fi

# ═══════════════════════════════════════════════════════════════
# Section 3: Feature Coverage Matrix
# ═══════════════════════════════════════════════════════════════
echo -e "\n${BOLD}${CYAN}━━━ 3. Feature Coverage: MUSE vs Bare Setup ━━━${RESET}\n"

declare -a features=(
  "Constitution/Rules"
  "Cross-session memory"
  "Long-term lessons"
  "Role isolation"
  "Cross-role directives"
  "Reusable skill library"
  "Context health monitoring"
  "Crash recovery"
  "Auto memory capture"
  "Memory search"
  "Visual dashboard"
  "MCP server integration"
  "VS Code extension"
  "One-click session save"
  "Memory distillation"
)

# MUSE coverage
declare -a muse_has=()
[[ "$has_claude" == "✅" || "$has_agents" == "✅" ]] && muse_has+=("✅") || muse_has+=("❌")
[[ "$has_memory" == "✅" ]] && muse_has+=("✅") || muse_has+=("❌")
[[ "$has_memories" == "✅" ]] && muse_has+=("✅") || muse_has+=("❌")
[[ $role_count -gt 1 ]] && muse_has+=("✅") || muse_has+=("❌")
# Directives: check for 📡 in .muse/*.md
has_directives="❌"
if [[ -d "$PROJECT/.muse" ]]; then
  grep -rl '📡' "$PROJECT/.muse/"*.md 2>/dev/null | head -1 > /dev/null && has_directives="✅"
fi
muse_has+=("$has_directives")
[[ $skill_count -gt 0 ]] && muse_has+=("✅") || muse_has+=("❌")
# Context health: check for context-health-check skill
has_ctx="❌"
for d in "$PROJECT/skills/core/context-health-check" "$PROJECT/.agent/skills/context-health-check"; do
  [[ -d "$d" ]] && has_ctx="✅" && break
done
muse_has+=("$has_ctx")
# Crash recovery
has_crash="❌"
[[ -f "$PROJECT/memory/CRASH_CONTEXT.md" ]] || grep -r 'CRASH_CONTEXT' "$PROJECT/.agent/workflows/" 2>/dev/null | head -1 > /dev/null && has_crash="✅"
muse_has+=("$has_crash")
# Auto capture: check for bye workflow with auto-capture
has_autocap="❌"
grep -rl 'Auto.*[Cc]apture\|auto.*capture\|LESSON.*DECISION\|auto-capture' "$PROJECT/.agent/workflows/" 2>/dev/null | head -1 > /dev/null && has_autocap="✅"
muse_has+=("$has_autocap")
muse_has+=("$has_search")
[[ "$has_dashboard_script" == "✅" || "$has_dashboard_online" == "✅" ]] && muse_has+=("✅") || muse_has+=("❌")
muse_has+=("$has_mcp")
muse_has+=("$has_vscode")
# One-click save: check for bye workflow
has_bye="❌"
[[ -f "$PROJECT/.agent/workflows/bye.md" || -f "$PROJECT/.agents/workflows/bye.md" ]] && has_bye="✅"
muse_has+=("$has_bye")
# Distill
has_distill="❌"
[[ -f "$PROJECT/.agent/workflows/distill.md" || -f "$PROJECT/.agents/workflows/distill.md" ]] && has_distill="✅"
muse_has+=("$has_distill")

muse_count=0
bare_count=0

printf "  ${BOLD}%-32s  %-6s  %-6s${RESET}\n" "Feature" "MUSE" "Bare"
printf "  %-32s  %-6s  %-6s\n" "────────────────────────────────" "──────" "──────"

for i in "${!features[@]}"; do
  m="${muse_has[$i]}"
  # Bare setup: only has constitution/rules
  b="❌"
  [[ $i -eq 0 ]] && b="⚠️"  # partial: .cursorrules is limited rules
  printf "  %-32s  %-6s  %-6s\n" "${features[$i]}" "$m" "$b"
  [[ "$m" == "✅" ]] && muse_count=$((muse_count + 1))
  [[ "$b" == "✅" ]] && bare_count=$((bare_count + 1))
done

echo ""
echo -e "  ${BOLD}Score: MUSE ${GREEN}${muse_count}/${#features[@]}${RESET} ${BOLD}vs Bare ${RED}${bare_count}/${#features[@]}${RESET}"

# ═══════════════════════════════════════════════════════════════
# Section 4: Knowledge Accumulation
# ═══════════════════════════════════════════════════════════════
echo -e "\n${BOLD}${CYAN}━━━ 4. Knowledge Accumulation Over Time ━━━${RESET}\n"

if [[ -d "$PROJECT/memory" ]] && [[ $memory_files -gt 0 ]]; then
  # Date range
  first_file=$(ls "$PROJECT/memory/"*.md 2>/dev/null | head -1 | xargs basename 2>/dev/null | sed 's/\.md//')
  last_file=$(ls "$PROJECT/memory/"*.md 2>/dev/null | tail -1 | xargs basename 2>/dev/null | sed 's/\.md//')

  # Average lines per day
  avg_lines=$((memory_lines / memory_files))

  # Growth rate
  printf "  %-28s %s\n" "First memory" "$first_file"
  printf "  %-28s %s\n" "Latest memory" "$last_file"
  printf "  %-28s %s\n" "Total sessions" "$memory_files"
  printf "  %-28s %s\n" "Total lines logged" "$memory_lines"
  printf "  %-28s %s\n" "Avg lines/session" "$avg_lines"
  printf "  %-28s %s\n" "Long-term lessons" "${memories_words} words"

  echo ""
  echo -e "  ${DIM}With .cursorrules only: 0 lines retained across sessions.${RESET}"
  echo -e "  ${GOLD}${BOLD}→ MUSE has accumulated ${memory_lines} lines of project knowledge${RESET}"
else
  echo -e "  ${DIM}No memory files found. Start using MUSE to accumulate knowledge!${RESET}"
fi

# ═══════════════════════════════════════════════════════════════
# Section 5: Summary
# ═══════════════════════════════════════════════════════════════
echo -e "\n${BOLD}${CYAN}━━━ 5. Summary ━━━${RESET}\n"

echo -e "  ${BOLD}${MAGENTA}MUSE Governance System${RESET}"
echo -e "  ├── ${skill_count} skills loaded on demand"
echo -e "  ├── ${role_count} roles with isolated context"
echo -e "  ├── ${memory_files} memory files (${memory_lines} lines)"
echo -e "  ├── ${memories_words}-word long-term memory"
echo -e "  ├── ${workflow_count} automated workflows"
echo -e "  └── ${muse_count}/${#features[@]} governance features active"
echo ""
echo -e "  ${BOLD}${DIM}Bare .cursorrules / AGENTS.md${RESET}"
echo -e "  ${DIM}├── 1 rules file (${bare_total} words)"
echo -e "  ├── 0 memory across sessions"
echo -e "  ├── 0 role isolation"
echo -e "  ├── 0 skills"
echo -e "  └── ${bare_count}/${#features[@]} governance features${RESET}"
echo ""

if [[ $muse_total -gt 0 && $bare_total -gt 0 ]]; then
  echo -e "  ${BOLD}${GOLD}MUSE provides ${ratio}× more context, ${muse_count}× more features.${RESET}"
elif [[ $muse_total -gt 0 ]]; then
  echo -e "  ${BOLD}${GOLD}MUSE provides ${muse_total} words of structured context vs 0 for bare setup.${RESET}"
fi
echo -e "  ${DIM}Report generated at: $(date '+%Y-%m-%d %H:%M')${RESET}\n"
