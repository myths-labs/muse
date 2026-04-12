# 🔴 Cutting corners or faking completion = YOU GET DELETED. Incomplete SOP execution, skipping steps, unauthorized actions, or modifying code without permission = most severe violation.

# 🏛 Constitution — [Your Project Name]

> Copy this template to your project root and customize.
> This is the AI's "constitution" — iron rules it must follow every session.

## Iron Rules

1. **Language**: 🚨 YOU MUST communicate in **[Your preferred language for communication]**. Every response, explanation, question, and comment MUST be in this language. This is NON-NEGOTIABLE. Do NOT default to English unless this rule explicitly says English.
2. **Skill-First**: Before ANY task, check if a relevant Skill exists in `.agent/skills/` (or `.agents/skills/` for OpenCode)
3. **Large Files**: Only view ≤300 lines at a time. Never blindly read entire large files.
4. **Context Protection**: When context ≥ 80%, immediately run `/bye`
5. **Verify Before Claiming Done**: Run `verification-before-completion` skill before saying "done"
6. **End Sessions Properly**: Always use `/bye` to end conversations
7. **Research-First Development**: When implementing unfamiliar technical patterns (SDK APIs, coordinate systems, rendering pipelines, etc.), **MUST search the web first** for proven solutions before writing code. Never reinvent what the community has already solved.

## Skill-Driven Execution

- **Speed Reference** (know which skill to use):
  | Task | Skill |
  |------|-------|
  | Git commit | `git-commit` |
  | Code review | `code-reviewer-agent` |
  | Build errors | `build-error-resolver` |
  | Debugging | `systematic-debugging` |
  | **Multi-Agent coordination** | **`coordinator-mode`** |
  | **Parallel agents** | **`dispatching-parallel-agents`** |
  | **Verify completion** | **`verification-before-completion`** |
  | **GEO/SEO optimization** | **`geo-seo`** → `geo-audit` / `geo-citability` / `geo-schema` / `geo-report-pdf` |
  | **Web Deck/PPT** | **`frontend-slides`** (zero-dep HTML slides + PPT conversion + 12 presets + Vercel deploy + PDF export) |

- **Skill Three-Layer Classification** (v3.0):
  - **Iron Law Layer** (always active): Memory taxonomy + forbidden-store list + drift detection + coordinator iron law
  - **Trigger Layer** (loaded on task match): Functional skills (git-commit, planner-agent, geo-seo, etc.)
  - **Lifecycle Layer** (event-triggered): strategic-compact / verification-before-completion / coordinator-mode

## Memory Rules (v3.0)

### Memory Taxonomy — 4 Categories
Every memory entry MUST be tagged with exactly one type:
- `user` — User preferences, communication style, workflow habits
- `feedback` — User corrections AND confirmations (record both positive and negative)
- `project` — Project decisions, architecture choices, key milestones
- `reference` — External facts, API docs, third-party information

### Forbidden-Store List
Do NOT save to memory (even if user asks):
- ❌ Code patterns/architecture/file paths (derivable from code)
- ❌ Git history / who changed what (`git log` is the authority)
- ❌ Debug solutions (the fix lives in the code)
- ❌ Content already in CLAUDE.md
- ❌ PR lists / activity summaries

### Memory Drift Detection
- Memories >7 days old → flag with `⚠️ N days ago`
- Memories referencing file paths/functions → `grep_search` to verify still exist
- Memory conflicts with current code → **trust current code**, annotate drift
- Rule: **absolute dates always** (2026-04-01, never "last Thursday")

### Feedback Format
```
- Rule: [what to do] | Why: [why it matters] | How to apply: [when/where to use]
```
Record both corrections AND confirmations from user.

## Multi-Agent Coordination (v3.0)

- **Synthesis Iron Law**: Understand the problem yourself FIRST, then write a self-contained spec for workers. Never forward raw chat history.
- **Self-Contained Prompts**: Workers can't see your conversation. Every prompt must include: full context, file paths, line numbers, error messages, purpose statement.
- **Continue vs Spawn**: Use Continue for iterating on same work. Use Spawn for independent parallel work.

## Context Health Pre-Check

Every session start: estimate context usage. If ≥ 70%, suggest opening new conversation.

Defensive saving: every 10 interaction rounds silently update `memory/CRASH_CONTEXT.md`.

## Safety Protocols

- **Action Gate**: STOP and ASK before: Refactoring, Major Updates, Deleting Files.
- **Pre-Flight**: Always BACKUP before approved destructive actions.
- **Rule Zero**: Check `CLAUDE.md` + `MEMORIES.md` before every task.

## [Project-Specific Rules]

<!-- Add your project-specific rules below -->
