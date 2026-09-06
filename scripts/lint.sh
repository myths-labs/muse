#!/bin/bash

# muse-lint: Protocol Conformance Test (v1.0)
# Verifies a project against the MUSE Protocol Specification v1.0

if [[ "${1:-}" == "--release" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  exec "${MUSE_PYTHON:-python3}" "$SCRIPT_DIR/check-release.py"
fi

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎭 MUSE Protocol Conformance Test (v1.0)${NC}"
echo "Running checks..."
echo

ERRORS=0
WARNINGS=0

# Helper functions
fail() {
  echo -e "  ${RED}✗ FAIL:${NC} $1"
  ((ERRORS++))
}

warn() {
  echo -e "  ${YELLOW}⚠ WARN:${NC} $1"
  ((WARNINGS++))
}

pass() {
  echo -e "  ${GREEN}✓ PASS:${NC} $1"
}

# 1. Directory Structure
echo "1. Directory Structure"
if [ ! -d ".muse" ]; then
  fail "Missing .muse/ directory"
else
  pass "Found .muse/ directory"
fi

if [ ! -d "memory" ]; then
  fail "Missing memory/ directory"
else
  pass "Found memory/ directory"
fi

if [ ! -f "CLAUDE.md" ] && [ ! -f "GEMINI.md" ]; then
  warn "Missing project constitution (CLAUDE.md or GEMINI.md)"
else
  pass "Found project constitution"
fi

echo

# 2. Role Files & L0 Headers
echo "2. Role Files & L0 Headers"
if [ ! -d ".muse" ]; then
  fail "Cannot check role files (missing .muse/)"
else
  ROLE_COUNT=0
  for file in .muse/*.md; do
    [ -e "$file" ] || continue
    ROLE_COUNT=$((ROLE_COUNT + 1))
    
    filename=$(basename "$file")
    
    # Check L0 Header
    l0_line=$(head -n 1 "$file")
    if [[ "$l0_line" != "<!-- L0:"* ]]; then
      fail "$filename: Missing L0 Header on line 1"
    else
      # Check L0 format: <!-- L0: [Any content here] -->
      # The protocol specifies version | priority, but for tools, any non-empty string is a valid L0 summary
      if [[ ! "$l0_line" =~ \<\!--\ L0:\ .+\ --\> ]]; then
        warn "$filename: L0 Header format should be '<!-- L0: [summary] -->'"
      else
        pass "$filename: Valid L0 Header"
      fi
    fi
    
    # Check for bloat (>800 lines)
    lines=$(wc -l < "$file")
    if [ "$lines" -gt 800 ]; then
      warn "$filename: File is too large ($lines lines). Consider archiving historical content."
    fi
  done
  
  if [ "$ROLE_COUNT" -eq 0 ]; then
    fail "No role files found in .muse/"
  else
    pass "Found $ROLE_COUNT role files"
  fi
fi

echo

# 3. Memory Structure
echo "3. Memory Structure"
if [ -f "MEMORIES.md" ]; then
  pass "Found MEMORIES.md (Long-term memory)"
else
  warn "Missing MEMORIES.md (No long-term distilled memory yet)"
fi

if [ -d "memory" ]; then
  MEM_COUNT=$(find memory -maxdepth 1 -name "*.md" | wc -l)
  if [ "$MEM_COUNT" -eq 0 ]; then
    warn "No short-term session logs found in memory/"
  else
    pass "Found $MEM_COUNT session logs in memory/"
  fi
fi

echo

# Summary
echo "----------------------------------------"
if [ $ERRORS -gt 0 ]; then
  echo -e "${RED}❌ FAILED${NC}: Project does not comply with MUSE Protocol v1.0"
  echo "Errors: $ERRORS | Warnings: $WARNINGS"
  exit 1
elif [ $WARNINGS -gt 0 ]; then
  echo -e "${YELLOW}⚠️ PASSED WITH WARNINGS${NC}: Project is missing some recommended components"
  echo "Errors: 0 | Warnings: $WARNINGS"
  exit 0
else
  echo -e "${GREEN}✅ PASSED${NC}: Project fully complies with MUSE Protocol v1.0!"
  exit 0
fi
