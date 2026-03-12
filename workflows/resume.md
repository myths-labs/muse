---
description: Restore project context at the start of every new conversation. Boot sequence assembles constitution, memory, preferences, and role state.
---

## 🚨 Rule Zero

**The role you load is the only topic you discuss.** Never talk about marketing in a build session, or code in a growth session.

## Pre-Flight Check

Before running the boot sequence, verify essential files exist:

```
✅ Required:  CLAUDE.md
✅ Required:  USER.md
✅ Required:  memory/ directory
✅ Required:  .muse/ directory (with at least one role file)
```

**If ANY required file is missing** → STOP and tell the user:

```
⚠️ MUSE is not configured yet. Missing: [list missing files]

Run /start to set up MUSE for this project first.
```

Do NOT proceed with the boot sequence. Do NOT create files silently. Let `/start` handle initial setup.

---

## Boot Sequence (run in order, every new conversation)

```
① CLAUDE.md + MEMORIES.md  → Constitution + long-term lessons (auto-injected)
② memory/today.md + yesterday.md → Short-term memory (what happened recently)
②.5 Scan memory `➡️ Next` sections for 🔲 / - [ ] items → remind if unfinished
③ Cross-day task? grep_search memory/ for task keywords → locate older context
④ USER.md                  → User preferences (language, model, style)
⑤ Target .muse/ role file  → Full progress (based on /resume scope)
⑥ 🚨 Strategy directive pull → Non-strategy roles auto-grep active directives
```

> ③ Only when task spans > 2 days

---

## Usage

```
/resume [role]               — Resume work on a specific role
/resume [project] [role]     — Multi-project: resume a specific project's role
/resume crash                — Recover from context blowout
```

### Standard Roles

| Scope | Command | Role File |
|-------|---------|-----------|
| Dev execution | `/resume build` | `.muse/build.md` |
| Quality verification | `/resume qa` | `.muse/qa.md` |
| Marketing & growth | `/resume growth` | `.muse/growth.md` |
| Strategic decisions | `/resume strategy` | `.muse/strategy.md` |
| DevOps & releases | `/resume ops` | `.muse/ops.md` |
| Research | `/resume research` | `.muse/research.md` |
| Fundraising | `/resume fundraise` | `.muse/fundraise.md` |
| Project GM | `/resume gm` | `.muse/gm.md` |

### Multi-Project

For workspaces with multiple projects, prefix with project name:

```
/resume [project] build      → [Project]/.muse/build.md
/resume [project] qa         → [Project]/.muse/qa.md
/resume [project] growth     → [Project]/.muse/growth.md
```

### Backward Compatibility

- `/resume status` → `/resume build`
- `/resume marketing` → `/resume growth`

---

## What the Agent Does

1. Read `memory/YYYY-MM-DD.md` (today + yesterday) for quick context
2. Read the target `.muse/[role].md` file for full progress and state
3. **Scan memory for unfinished items** — search recent 2 days for:
   - `🔲` items
   - `- [ ]` items
   - `➡️ Next` sections with incomplete items
   → Report any found (regardless of current role scope)
4. **Role file size check**: `wc -l` target file. **>800 lines → archive first** (move completed items to `.muse/archive/`, target ≤500 lines)
5. **🚨 Auto-pull strategy directives** (all non-strategy roles):
   - `grep_search` scan `.muse/strategy.md` for active directives tagged with current role
   - Found → highlight in resume report as "📡 New Strategy Directive", write to role file
   - Not found → skip silently
6. **If `/resume build`**: auto-check `.muse/qa.md` for unresolved ❌ FAIL → fix those first
7. **If `/resume qa`**: auto-detect what needs verification:
   - Check qa.md "Pending Re-Verify" section for ❌ FAIL items → **automatically re-verify them** (user doesn't need to specify anything)
   - If user mentions a strategy directive (e.g., "S028") → read AC from strategy.md
   - If nothing in qa.md and user gives no instruction → ask what to verify
8. **If `/resume strategy`**: grep `memory/` for major events not yet synced (keywords: rejected/approved/deployed/launched/funded/resubmit/merged/released)
9. **Conflict resolution**: Role file > memory snapshot (role files are continuously updated, memory is point-in-time)
10. **Internal consistency check**: cross-verify same facts across sections before outputting report
11. Only recommend next steps within the role's scope
12. Read relevant code/docs as needed to begin work

---

## Context Blowout Recovery

```
/resume crash
```

1. Check `memory/CRASH_CONTEXT.md` — if exists, read it (auto-saved snapshot) → delete after recovery
2. If not found, scan `convo/` for latest `_CRASH` file → read last 30%
3. If nothing found → ask user for file path
4. Run standard boot sequence
5. Output recovery report: what was being worked on, what's unfinished, suggested next steps

---

## Ending Conversations

```
/bye
```

Zero input. Auto-summarizes → syncs .muse/ role files → writes `memory/YYYY-MM-DD.md`. See `bye.md`.

## Mid-Conversation Sync

When another role finishes work in a separate conversation (e.g., QA completes while build is still active), the active conversation can pull in new results:

```
/sync receive          — Pull updates from other role files into current session
```

**Common scenarios:**

| You're in... | What happened elsewhere | What to do |
|-------------|------------------------|------------|
| `/resume build` | QA finished, wrote results to `qa.md` | `/sync receive` → reads qa.md FAILs → fix them |
| `/resume build` | Strategy issued new directive | `/sync receive` → reads strategy.md directives |
| `/resume growth` | Build shipped new feature | `/sync receive` → reads build.md for launch content |

**How it works:**
1. User says `/sync receive` (or mentions "QA results are in" / "check qa.md")
2. Agent reads the relevant role file(s) for new information
3. Integrates new tasks/directives into current session
4. Continues working with updated context

> This avoids the need to end a conversation and start a new one just to pick up cross-role updates.

---

## When to Start a New Conversation

- ✅ Completed a full feature/task
- ✅ **Switching work topics** (most important signal)
- ✅ Responses feel slow or quality drops
- ✅ ~15-20 interaction rounds
- ✅ `/ctx` shows ≥ 80%

## Core Principles

1. **Role isolation** — build/qa/growth/strategy are independent
2. **Load one, discuss one** — never cross-contaminate roles
3. **Short and dense** — each conversation focuses on one topic
4. **Save on exit** — always update .muse/ + write memory/
