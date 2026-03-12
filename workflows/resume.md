---
description: Boot sequence for restoring project context at conversation start
---

## 🚨 Rule Zero

**Read one role file, discuss only that role's scope.** Don't discuss marketing in a dev conversation, or code in a marketing conversation.

## Boot Sequence (MUSE Context Assembly — execute in order each new conversation)

```
① CLAUDE.md + MEMORIES.md  → Constitution + long-term lessons (auto-injected)
② memory/today.md + yesterday.md → Short-term memory (recent events)
③ Cross-day task? grep_search memory/ for keywords → locate earlier memories
④ USER.md                  → User preferences
⑤ Matching .muse/ role file → Full progress (based on command)
```

> ③ only runs when task spans > 2 days (≈ LCM lcm_grep deep retrieval)

### Resume Commands

| Scenario | Command |
|----------|---------|
| Continue dev work | `/resume build` |
| Continue growth/marketing | `/resume growth` |
| Continue strategy | `/resume strategy` |
| Continue ops/release | `/resume ops` |
| Continue research | `/resume research` |
| Continue fundraising | `/resume fundraise` |
| Project GM overview | `/resume gm` |
| **Crash recovery** | **`/resume crash`** |

For multi-project setups, prefix with project name:
```
/resume [project] build      → [project]/.muse/build.md
/resume [project] growth     → [project]/.muse/growth.md
/resume [project] gm         → [project]/.muse/gm.md
```

### File Path Convention

```
/resume gm         → .muse/gm.md
/resume build      → .muse/build.md (+ check qa.md for FAILs)
/resume growth     → .muse/growth.md
/resume strategy   → .muse/strategy.md
/resume ops        → .muse/ops.md
/resume research   → .muse/research.md
/resume fundraise  → .muse/fundraise.md
```

After reading the role file, the agent will:
1. Read `memory/YYYY-MM-DD.md` (today + yesterday) for quick context
2. Read the specified `.muse/` role file for full progress
3. **If `/resume build`**: auto-check `.muse/qa.md` for unresolved ❌ FAILs → fix first
4. **If `/resume strategy`**: check memory/ for un-synced critical events (grep: rejected/approved/deployed/funded)
5. Only suggest next actions within that role's scope
6. Read relevant code/docs as needed

### Crash Recovery

| Scenario | Command |
|----------|---------|
| Context blowout or emergency recovery | `/resume crash` |

**`/resume crash` flow:**
1. Check if `memory/CRASH_CONTEXT.md` exists
   - **Yes** → Read it (this is the L0/L1 auto-saved snapshot) → resume, then delete
2. If not, scan `convo/` for latest `_CRASH` file (sorted by modification time)
   - **Found** → Read last 30% (usually contains recent discussion and decisions)
   - Extract: current task, unfinished items, key decisions, user's last question
3. If neither found → user manually specifies file path
4. Execute standard Boot Sequence (memory/ + USER.md + .muse/ role file)
5. Output recovery report: what was done, what's unfinished, suggested next steps

---

## Ending a Conversation

```
/bye
```

Zero input. Auto-summarizes work → syncs .muse/ role files → writes `memory/YYYY-MM-DD.md` → suggests archiving to `convo/`. See `bye.md`.

## Role File Responsibilities

| File | Content | Update When |
|------|---------|-------------|
| `.muse/strategy.md` | Business strategy, PMF, fundraising, growth | After strategy discussions |
| `.muse/gm.md` | Project GM — cross-role coordination, L1/L2 decisions | After cross-role work |
| `.muse/build.md` | Code development, bug fixes | After coding sessions |
| `.muse/growth.md` | Marketing, brand, social media, content | After marketing work |
| `.muse/qa.md` | QA verification, acceptance criteria | After QA rounds |
| `.muse/ops.md` | Releases, CI/CD, deployment | After releases |
| `.muse/research.md` | Competitive analysis, market research | After research |
| `.muse/fundraise.md` | Deck, applications, pitch scripts | After fundraising work |
| `memory/YYYY-MM-DD.md` | Daily snapshot (lightweight) | **Every conversation end** |

## When to Start a New Conversation

- ✅ Completed a full feature/task
- ✅ **Switching work topic** (most important signal)
- ✅ Responses feel slow or quality degrades
- ✅ After ~15-20 interaction rounds
- ✅ `/ctx` shows ≥ 80% usage

## Key Principles

1. **Role isolation** — Each role is independent, no cross-contamination
2. **Read one, discuss one** — Never mix topics across role files
3. **Short conversations, high density** — Focus each conversation on one topic
4. **Archive on exit** — Update .muse/ role files + write to memory/
