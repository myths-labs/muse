#!/bin/bash
# MUSE Release Script — Pre-flight checks + version bump + commit + tag + push + GitHub Release
# Usage: ./release.sh <new_version> "<release_title>" "<release_notes>"
# Example: ./release.sh 3.1.0 "Memory Compression" "### Added\n- Semantic compression engine"

set -euo pipefail

# ─── Args ───
NEW_VERSION="${1:?Usage: ./release.sh <version> <title> <notes>}"
RELEASE_TITLE="${2:?Missing release title}"
RELEASE_NOTES="${3:?Missing release notes}"

# Strip leading 'v' if user passes v3.1.0
NEW_VERSION="${NEW_VERSION#v}"

cd "$(dirname "$0")" || exit 1

# ─── Step 0: Detect old version ───
OLD_VERSION=$(git tag --sort=-creatordate | head -1 | sed 's/^v//')
if [ -z "$OLD_VERSION" ]; then
  echo "❌ No existing tags found"
  exit 1
fi
echo "📦 Upgrading: v${OLD_VERSION} → v${NEW_VERSION}"

# ─── Step 1: Physical skill count ───
SKILL_COUNT=$(find skills/ -name "SKILL.md" | wc -l | tr -d ' ')
echo "🔢 Physical skill count: ${SKILL_COUNT}"

# ─── Step 2: Pre-flight — scan for OLD version remnants ───
echo ""
echo "🔍 Pre-flight: scanning for old version remnants..."
REMNANTS=$(grep -rn "v${OLD_VERSION}\|version-${OLD_VERSION}" \
  README.md README_CN.md SKILL_INDEX.md docs/llms.txt docs/index.html 2>/dev/null || true)

if [ -n "$REMNANTS" ]; then
  echo "⚠️  Found old version references (will be auto-fixed):"
  echo "$REMNANTS"
  echo ""
fi

# ─── Step 3: Auto-fix version references ───
echo "🔧 Fixing version references..."

# Badges
sed -i '' "s/version-[0-9]*\.[0-9]*\.[0-9]*-blue/version-${NEW_VERSION}-blue/g" README.md README_CN.md

# Footer / inline version strings
sed -i '' "s/MUSE v[0-9]*\.[0-9]*\.[0-9]*/MUSE v${NEW_VERSION}/g" README.md README_CN.md docs/index.html 2>/dev/null || true

# Skill count in prose (e.g. "62 skills" → "65 skills")
OLD_SKILL_REFS=$(grep -rn "[0-9]* skills" README.md docs/llms.txt docs/index.html 2>/dev/null | grep -oP '\d+ skills' | sort -u || true)
for old_ref in $OLD_SKILL_REFS; do
  old_num=$(echo "$old_ref" | grep -oP '\d+')
  if [ "$old_num" != "$SKILL_COUNT" ]; then
    echo "  Fixing: ${old_num} skills → ${SKILL_COUNT} skills"
    sed -i '' "s/${old_num} skills/${SKILL_COUNT} skills/g" README.md README_CN.md docs/llms.txt docs/index.html 2>/dev/null || true
  fi
done

# ─── Step 4: Post-fix verification ───
echo ""
echo "🔍 Post-fix verification..."
STILL_OLD=$(grep -rn "v${OLD_VERSION}\|version-${OLD_VERSION}\|${OLD_VERSION}-blue" \
  README.md README_CN.md SKILL_INDEX.md docs/llms.txt docs/index.html 2>/dev/null || true)

if [ -n "$STILL_OLD" ]; then
  echo "❌ ABORT: Old version still found after fix:"
  echo "$STILL_OLD"
  echo ""
  echo "Fix manually, then re-run."
  exit 1
fi
echo "✅ No old version remnants found"

# ─── Step 5: Summary before commit ───
echo ""
echo "┌─────────────────────────────────────┐"
echo "│ Release Summary                     │"
echo "├─────────────────────────────────────┤"
echo "│ Version:  v${NEW_VERSION}"
echo "│ Skills:   ${SKILL_COUNT}"
echo "│ Title:    ${RELEASE_TITLE}"
echo "│ Old ver:  v${OLD_VERSION}"
echo "└─────────────────────────────────────┘"
echo ""
read -p "Proceed? (y/N) " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "Aborted."
  exit 0
fi

# ─── Step 6: Commit + Tag + Push ───
git add .
git commit -m "feat(v${NEW_VERSION}): ${RELEASE_TITLE}

Skills: ${SKILL_COUNT} (Core $(find skills/core -name 'SKILL.md' | wc -l | tr -d ' ') + Toolkit $(find skills/toolkit -name 'SKILL.md' | wc -l | tr -d ' ') + Ecosystem $(find skills/ecosystem -name 'SKILL.md' | wc -l | tr -d ' '))"

git tag "v${NEW_VERSION}"
git push origin main --tags

# ─── Step 7: GitHub Release ───
gh release create "v${NEW_VERSION}" \
  --title "v${NEW_VERSION} — ${RELEASE_TITLE}" \
  --notes "${RELEASE_NOTES}" \
  --latest

echo ""
echo "✅ v${NEW_VERSION} released successfully!"
echo "🔗 https://github.com/myths-labs/muse/releases/tag/v${NEW_VERSION}"
