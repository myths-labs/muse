---
description: Weekly development retrospective — generates statistics from memory/ logs and git history. Use when reviewing progress, generating weekly summaries, or evaluating shipping velocity.
---

# /retro — Development Retrospective

*Inspired by gstack's /retro, adapted for MUSE's memory system.*

## What This Does

Generates a development retrospective by combining:
1. `memory/` daily logs
2. Git commit history
3. `.muse/` role file changes

Outputs a structured weekly/monthly summary with statistics, trends, and actionable insights.

## When to Use

- End of week → weekly retro
- End of month → monthly retro  
- Before investor meetings → progress summary
- Before `/distill` → understand what to keep

## Steps

### 1. Determine Time Range
// turbo
Ask the user or default to last 7 days.

```bash
# Get the date range
date -v-7d "+%Y-%m-%d"
```

### 2. Gather Data

**Git statistics:**
// turbo
```bash
# Commits in range
git log --since="7 days ago" --oneline --all | head -50

# Lines changed
git diff --stat $(git log --since="7 days ago" --format="%H" --all | tail -1) HEAD 2>/dev/null || echo "No commits in range"

# Files changed
git log --since="7 days ago" --name-only --all --format="" | sort -u | head -30
```

**Memory logs:**
Read all files in `memory/` that fall within the time range.
Extract:
- Tasks completed
- Decisions made
- Blockers encountered
- Lessons learned

**Role file diff:**
// turbo
```bash
git log --since="7 days ago" -p -- "**/.muse/*.md" | head -100
```

### 3. Generate Report

Create a retro report in the following format:

```markdown
# Retro: [date range]

## 📊 Stats
- **Commits**: X
- **Lines added/removed**: +X / -X  
- **Files touched**: X
- **Products worked on**: [list]
- **Skills used most**: [from memory logs]
- **Sessions**: X conversations

## 🚀 Shipped
- [Feature/fix 1]
- [Feature/fix 2]
- ...

## 🎯 Decisions Made
- [Decision 1] — [rationale]
- [Decision 2] — [rationale]

## 🧱 Blockers Hit
- [Blocker 1] — [resolution/status]

## 💡 Lessons Learned
- [Lesson 1]
- [Lesson 2]

## 📈 Trends
- Shipping velocity: [increasing/stable/decreasing] 
- Test coverage: [improving/stable/declining]
- Focus: [concentrated on X / spread across Y]

## 🎯 Next Week
- [Priority 1]
- [Priority 2]
- [Priority 3]
```

### 4. Save and Offer Actions

Save the retro to `memory/retro-[date].md`.

Offer:
- Update `.muse/` role files with retrospective insights
- Run `/distill` to extract permanent lessons to MEMORIES.md
- Share with team (if applicable)

## Pro Tips

- Run `/retro` before starting a new sprint to ground yourself
- Compare retros month-over-month to spot drift
- Use retro data in investor updates (e.g., "428 commits across 3 products")
- Pair with `/ctx` to check if context is getting too big before starting a new sprint
