#!/bin/bash
# MUSE First-Time Setup
# Configures language, AI model, and basic preferences

set -e

echo ""
echo "🎭 MUSE — First-Time Setup"
echo "════════════════════════════"
echo ""

# ─── Language Preference ───
echo "1. What language should the AI communicate in?"
echo "   [1] English (default)"
echo "   [2] 简体中文 (Chinese)"
echo "   [3] Other"
echo ""
read -p "   Choice [1]: " lang_choice
lang_choice=${lang_choice:-1}

case $lang_choice in
  1) LANG_PREF="English" ;;
  2) LANG_PREF="简体中文" ;;
  3) read -p "   Enter language: " LANG_PREF ;;
  *) LANG_PREF="English" ;;
esac

# ─── AI Model ───
echo ""
echo "2. Which AI model are you using?"
echo "   [1] Claude Sonnet 4 (200K context)"
echo "   [2] Claude Opus 4 (200K context)"
echo "   [3] Gemini 2.5 Pro (1M context)"
echo "   [4] GPT-4o (128K context)"
echo "   [5] Other"
echo ""
read -p "   Choice [1]: " model_choice
model_choice=${model_choice:-1}

case $model_choice in
  1) MODEL="Claude Sonnet 4"; CTX="200K" ;;
  2) MODEL="Claude Opus 4"; CTX="200K" ;;
  3) MODEL="Gemini 2.5 Pro"; CTX="1M" ;;
  4) MODEL="GPT-4o"; CTX="128K" ;;
  5) 
    read -p "   Model name: " MODEL
    read -p "   Context window (e.g. 200K): " CTX
    ;;
  *) MODEL="Claude Sonnet 4"; CTX="200K" ;;
esac

# ─── Docs Language ───
echo ""
echo "3. Documentation language preference?"
echo "   [1] English for everything (default)"
echo "   [2] English for code, ${LANG_PREF} for discussions"
echo "   [3] ${LANG_PREF} for everything"
echo ""
read -p "   Choice [1]: " docs_choice
docs_choice=${docs_choice:-1}

case $docs_choice in
  1) DOCS_LANG="English" ;;
  2) DOCS_LANG="English for code/README, ${LANG_PREF} for discussions" ;;
  3) DOCS_LANG="${LANG_PREF}" ;;
  *) DOCS_LANG="English" ;;
esac

# ─── Target Directory ───
echo ""
read -p "4. Project directory to configure [./]: " TARGET_DIR
TARGET_DIR=${TARGET_DIR:-./}

# Resolve path
TARGET_DIR=$(cd "$TARGET_DIR" 2>/dev/null && pwd || echo "$TARGET_DIR")

# ─── Check if templates exist ───
if [ ! -f "$TARGET_DIR/USER.md" ] && [ ! -f "$TARGET_DIR/CLAUDE.md" ]; then
  echo ""
  echo "   ⚠️  No USER.md or CLAUDE.md found in $TARGET_DIR"
  echo "   Copy templates first? (y/n)"
  read -p "   " copy_templates
  if [ "$copy_templates" = "y" ] || [ "$copy_templates" = "Y" ]; then
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    TEMPLATE_DIR="$SCRIPT_DIR/templates"
    if [ -d "$TEMPLATE_DIR" ]; then
      cp "$TEMPLATE_DIR/CLAUDE.md" "$TARGET_DIR/CLAUDE.md"
      cp "$TEMPLATE_DIR/USER.md" "$TARGET_DIR/USER.md"
      cp "$TEMPLATE_DIR/MEMORIES.md" "$TARGET_DIR/MEMORIES.md"
      mkdir -p "$TARGET_DIR/memory" "$TARGET_DIR/.muse" "$TARGET_DIR/convo"
      echo "   ✅ Templates copied"
    else
      echo "   ❌ Template directory not found at $TEMPLATE_DIR"
      exit 1
    fi
  fi
fi

# ─── Skills & Workflows ───
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "5. Install MUSE skills & workflows?"
echo "   [1] All (Core + Toolkit + Workflows) — recommended"
echo "   [2] Core only (minimum for MUSE to work)"
echo "   [3] Skip"
echo ""
read -p "   Choice [1]: " skills_choice
skills_choice=${skills_choice:-1}

if [ "$skills_choice" != "3" ]; then
  mkdir -p "$TARGET_DIR/.agent/skills" "$TARGET_DIR/.agent/workflows"

  # Core skills (always)
  if [ -d "$SCRIPT_DIR/skills/core" ]; then
    cp -r "$SCRIPT_DIR/skills/core" "$TARGET_DIR/.agent/skills/core"
    echo "   ✅ Core skills installed (4)"
  fi

  # Toolkit skills (if chosen)
  if [ "$skills_choice" = "1" ] && [ -d "$SCRIPT_DIR/skills/toolkit" ]; then
    cp -r "$SCRIPT_DIR/skills/toolkit" "$TARGET_DIR/.agent/skills/toolkit"
    echo "   ✅ Toolkit skills installed (37)"
  fi

  # Workflows (always)
  if [ -d "$SCRIPT_DIR/workflows" ]; then
    cp "$SCRIPT_DIR/workflows/"*.md "$TARGET_DIR/.agent/workflows/" 2>/dev/null
    echo "   ✅ Workflows installed"
  fi
fi

# ─── Apply Preferences ───
echo ""
echo "Applying preferences..."

# Update USER.md
if [ -f "$TARGET_DIR/USER.md" ]; then
  sed -i '' "s|\[e\.g\., English, 简体中文, etc\.\]|${LANG_PREF}|g" "$TARGET_DIR/USER.md" 2>/dev/null || \
  sed -i "s|\[e\.g\., English, 简体中文, etc\.\]|${LANG_PREF}|g" "$TARGET_DIR/USER.md"
  
  sed -i '' "s|\[e\.g\., Claude Opus 4\.6, GPT-4, etc\.\]|${MODEL}|g" "$TARGET_DIR/USER.md" 2>/dev/null || \
  sed -i "s|\[e\.g\., Claude Opus 4\.6, GPT-4, etc\.\]|${MODEL}|g" "$TARGET_DIR/USER.md"
  
  sed -i '' "s|\[e\.g\., 200K tokens\]|${CTX} tokens|g" "$TARGET_DIR/USER.md" 2>/dev/null || \
  sed -i "s|\[e\.g\., 200K tokens\]|${CTX} tokens|g" "$TARGET_DIR/USER.md"
  
  sed -i '' "s|\[e\.g\., English for code/README, Chinese for discussions\]|${DOCS_LANG}|g" "$TARGET_DIR/USER.md" 2>/dev/null || \
  sed -i "s|\[e\.g\., English for code/README, Chinese for discussions\]|${DOCS_LANG}|g" "$TARGET_DIR/USER.md"
  
  echo "   ✅ USER.md configured"
fi

# Update CLAUDE.md
if [ -f "$TARGET_DIR/CLAUDE.md" ]; then
  sed -i '' "s|\[Your preferred language for communication\]|All communication in ${LANG_PREF}|g" "$TARGET_DIR/CLAUDE.md" 2>/dev/null || \
  sed -i "s|\[Your preferred language for communication\]|All communication in ${LANG_PREF}|g" "$TARGET_DIR/CLAUDE.md"
  
  sed -i '' "s|\[Your Project Name\]|$(basename "$TARGET_DIR")|g" "$TARGET_DIR/CLAUDE.md" 2>/dev/null || \
  sed -i "s|\[Your Project Name\]|$(basename "$TARGET_DIR")|g" "$TARGET_DIR/CLAUDE.md"
  
  echo "   ✅ CLAUDE.md configured"
fi

# ─── Summary ───
echo ""
echo "════════════════════════════"
echo "🎭 MUSE Setup Complete!"
echo "════════════════════════════"
echo ""
echo "   Language:  ${LANG_PREF}"
echo "   Model:     ${MODEL} (${CTX})"
echo "   Docs:      ${DOCS_LANG}"
echo "   Directory: ${TARGET_DIR}"
echo ""
echo "Next steps:"
echo "  1. Review ${TARGET_DIR}/CLAUDE.md — add project-specific rules"
echo "  2. Start your first conversation with: /start (or /resume)"
echo "  3. Change preferences anytime with: /settings"
echo "  4. End conversations with: /bye"
echo ""
echo "📖 Full docs: https://github.com/myths-labs/muse"
echo ""
