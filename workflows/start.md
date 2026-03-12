---
description: First-time MUSE setup for new users. Interactive onboarding that configures project, roles, language, and teaches core commands. Run once when adopting MUSE in a new project.
---

## Usage

```
/start
```

**First-time only.** After setup is complete, use `/resume` for all future conversations.

---

## Onboarding Flow

// turbo-all

Agent walks the user through each step interactively. Do NOT rush — pause for user input at each decision point.

### Step 1: Welcome & Context Check

Display welcome message:

```
🎭 Welcome to MUSE — Memory-Unified Skills & Execution

I'll help you set up MUSE for your project in about 5 minutes.
We'll configure:
  ① Project identity
  ② Your preferences (language, AI model)
  ③ Role files (what MUSE tracks for you)
  ④ Quick command tutorial

Let's start! 🚀
```

**Check if MUSE is already configured:**
- If `CLAUDE.md` exists AND `USER.md` exists AND `memory/` exists → warn: "Looks like MUSE is already set up here. Do you want to reconfigure? (y/n)"
- If n → suggest `/resume` instead

### Step 2: Project Identity

Ask the user:

```
1️⃣ What's your project called?
   - If you have a name, tell me
   - If not, tell me what you're building and I'll suggest some
```

**Actions:**
- If user gives a name → use it
- If user describes the project → generate 3 name suggestions, let them pick or enter their own
- Fill `[Your Project Name]` in `CLAUDE.md` template

### Step 3: Language & Model Preferences

Ask:

```
2️⃣ Preferences:

   Language — what language should I communicate in?
   [1] English  [2] 简体中文  [3] Other: ___

   AI Model — which model are you using?
   [1] Claude Sonnet 4 (200K)  [2] Claude Opus 4 (200K)
   [3] Gemini 2.5 Pro (1M)    [4] GPT-4o (128K)
   [5] Other: ___
```

**Actions:**
- Fill `USER.md` → Language, Model, Context Window
- Fill `CLAUDE.md` → Iron Rule #1 language setting

### Step 4: Role Selection

Explain the role system briefly, then ask:

```
3️⃣ MUSE uses "role files" to track different aspects of your project.

   Which do you need? (pick all that apply)

   Essential (recommended):
   [a] ⚙️  build.md  — Dev execution, current tasks, tech decisions
   [b] 🔍  qa.md     — Quality verification (prevents "it works" lies)

   Growth (if doing marketing/launch):
   [c] 📢  growth.md — Marketing, content, user acquisition

   Advanced (multi-project / team):
   [d] 🧠  strategy.md — Strategic decisions (if managing multiple projects)
   [e] 🏢  gm.md       — Project GM (if using strategy layer)
   [f] 🔧  ops.md      — DevOps, releases, CI/CD
   [g] 🔬  research.md — Market research, competitive analysis
   [h] 💰  fundraise.md — Investor deck, accelerator applications

   Enter letters, e.g. "ab" or "abcf": ___
```

**Default suggestion:** `ab` for personal projects, `abc` for products with users.

**Actions:**
- Create `.muse/` directory
- Create selected role files with minimal templates:

```markdown
# ⚙️ [Project Name] — Build

## Current Sprint
- [ ] [First task — user can fill in later]

## Tech Stack
- [To be filled]

## Key Decisions
| # | Decision | Date | Rationale |
|---|----------|------|-----------|
```

### Step 5: Skills & Workflows Installation

Ask:

```
3.5️⃣ Skills — MUSE skills extend the AI's capabilities.

   🏛 Core (auto-installed, required for MUSE to work):
      ✅ context-health-check  — /ctx command
      ✅ strategic-compact     — smart context compression
      ✅ verification-before-completion — anti-fraud QA

   🔧 Toolkit (recommended, pick what you need):
      [a] git-commit           — Conventional Commits format
      [b] systematic-debugging — 4-phase root cause process
      [c] build-error-resolver — Fix build/TypeScript errors
      [d] code-reviewer-agent  — Code quality checks
      [e] creating-skills      — Guide for making your own skills

   Install all Toolkit? (y/n, or pick letters like "abd"): ___
```

**Actions:**
- Create `.agent/skills/` directory structure
- Copy Core skills (always)
- Copy selected Toolkit skills
- Copy all workflows to `.agent/workflows/` (resume, bye, sync, distill, ctx, settings, role, start)

### Step 6: File Creation Summary

Create all necessary files:

1. `CLAUDE.md` — filled with project name + language
2. `USER.md` — filled with language + model
3. `MEMORIES.md` — empty template
4. `memory/` directory
5. `.muse/` + selected role files
6. `.agent/skills/` + selected skills
7. `.agent/workflows/` + all workflows
8. `convo/` directory
9. Append MUSE `.gitignore` entries if `.gitignore` exists

Report what was created:

```
✅ Created:
   CLAUDE.md              — your AI constitution
   USER.md                — your preferences
   MEMORIES.md            — long-term lessons (empty for now)
   memory/                — short-term memory directory
   .muse/build.md         — dev execution tracker
   .muse/qa.md            — quality verification
   .agent/skills/core/    — 3 core skills
   .agent/skills/toolkit/ — N toolkit skills
   .agent/workflows/      — 8 workflows (resume/bye/sync/distill/ctx/settings/role/start)
   convo/                 — conversation archive directory
   .gitignore             — MUSE private files added
```

### Step 7: Command Tutorial

Display interactive cheat sheet:

```
4️⃣ Quick Command Reference:

   ┌──────────────────────────────────────────────┐
   │  /resume [role]  Start working               │
   │    e.g. /resume build   — continue coding    │
   │    e.g. /resume growth  — continue marketing │
   │                                              │
   │  /ctx            Check context health        │
   │    → 🟢 keep going  🟡 wrap up  🔴 exit now │
   │                                              │
   │  /bye            End session (auto-saves)    │
   │    → writes memory, syncs roles, suggests    │
   │      conversation export                     │
   │                                              │
   │  /settings       Change language/model/prefs │
   │    → /settings language 简体中文             │
   │    → /settings model claude opus 4           │
   │                                              │
   │  /distill        Extract lessons             │
   │    → memory/ daily logs → MEMORIES.md        │
   │    → run weekly or after milestones          │
   └──────────────────────────────────────────────┘

   💡 Tip: You can always ask "what commands do I have?"
      and I'll show this reference again.
```

Ask: "Want me to explain any command in more detail, or are you ready to start working?"

### Step 8: First Task Kickoff

```
🎭 MUSE is ready!

   Your first conversation starts now.
   What would you like to work on?

   (I'll track everything in .muse/build.md and
    save our progress when you say /bye)
```

After user responds, switch to normal working mode — read the relevant .muse/ file and begin.

---

## Role File Templates

### build.md Template
```markdown
# ⚙️ {PROJECT} — Build

## Current Sprint
- [ ] [First task]

## Tech Stack
- [To be filled]

## Key Decisions
| # | Decision | Date | Rationale |
|---|----------|------|-----------|
```

### qa.md Template
```markdown
# 🔍 {PROJECT} — QA

## Iron Rules
1. **Evidence > Claims** — every verification must have proof
2. **No self-verification** — build cannot verify its own code
3. **Deep QA only** — HTTP 200 is NOT a pass

## Pending Re-Verify
> When QA reports ❌ FAIL, items go here. `/resume qa` auto-detects and re-verifies.
> After re-verify PASS → move to QA Reports. After re-verify FAIL → stays here.

(none)

## QA Reports
(empty — populated after first QA cycle)
```

### growth.md Template
```markdown
# 📢 {PROJECT} — Growth

## Channels
- [ ] [Identify primary channels]

## Content Calendar
| Date | Platform | Content | Status |
|------|----------|---------|--------|

## Metrics
| Metric | Current | Target |
|--------|---------|--------|
```

### strategy.md Template
```markdown
# 🧠 Strategy

## Vision
[What are you building and why?]

## North Star Metric
[Single metric that matters most right now]

## Active Decisions
| # | Decision | Date | Status |
|---|----------|------|--------|
```

### Other roles (ops/research/fundraise/gm)
Use minimal 10-line templates with section headers only.

---

## Post-Setup

After `/start` completes:
- `/start` should NOT be run again (check for existing CLAUDE.md)
- Use `/resume [role]` for all future sessions
- Use `/settings` to change language, model, or preferences anytime
- `/bye` at end of every session
- `/distill` weekly to extract lessons
