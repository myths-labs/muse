---
description: Feature development sprint — connects existing skills into a pipeline (Think → Plan → Build → Review → Test → Ship)
---

# /sprint — Feature Development Pipeline

*Inspired by gstack's sprint process, adapted for MUSE's multi-project governance.*

## Overview

This workflow connects existing MUSE skills into a complete feature development pipeline. Each step feeds into the next. Run it for any new feature, bug fix, or refactor.

## The Pipeline

```
Think → Plan → Build → Review → Test → Ship → Reflect
```

## Steps

### 1. Think — Reframe the Problem
// turbo
Use the `brainstorming` skill to challenge assumptions before writing code.

Key questions to answer:
- What's the actual pain being solved? (Not the feature request — the pain.)
- Who has this pain right now, and how do they solve it today?
- What's the narrowest wedge that validates the idea?
- What assumptions are most dangerous?

Output: A clear problem statement and scoped approach.

### 2. Plan — Lock the Architecture

Use the `writing-plans` skill to create an implementation plan.

The plan should include:
- Files to modify/create (with specific changes)
- Dependencies and ordering
- Test strategy
- Acceptance criteria

For architecture decisions, invoke `architect-agent`.

Output: `implementation_plan.md` in the brain directory.

### 3. Build — Write the Code

Use `executing-plans` to implement the plan step by step.

Rules during Build:
- Follow the plan. If you discover the plan is wrong, go back to Step 2.
- Apply `ETHOS.md` principle: Boil the Lake — do the complete thing.
- Write tests as you go (not "later").
- Commit frequently with `git-commit` (Conventional Commits format).

### 4. Review — Find Bugs Before Users Do

Run these reviews in sequence:

**4a. Code Review:**
Use `code-reviewer-agent` — checks for bugs, style, maintainability.

**4b. Security Review:**
Use `security-reviewer-agent` — checks for vulnerabilities, if the change touches auth/input/API/payments.

**4c. Architecture Review (if major change):**
Use `architect-agent` — checks for scalability, design pattern issues.

Auto-fix obvious issues. Flag judgment calls for the user.

### 5. Test — Verify It Works

**5a. Run existing tests:**
// turbo
```bash
npm test
```

**5b. Browser QA (if frontend change):**
Use `webapp-testing` to open the app, click through affected flows, and verify behavior.

**5c. E2E (if critical path):**
Use `e2e-runner` for end-to-end testing.

### 6. Ship — PR and Merge

Use `github-pr-creation` to:
- Sync with main
- Run all tests
- Create PR with Conventional Commits title

After approval, use `github-pr-merge` to merge.

For deployment, use `vercel-deploy` if applicable.

### 7. Reflect — Learn from the Sprint

Use `/retro` to generate statistics on what was shipped.
Update memory/ daily log with what was done, decisions made, and lessons learned.
Use `/bye` at end of session to persist everything.

---

## Quick Reference

| Phase | Skill | What it does |
|-------|-------|-------------|
| Think | `brainstorming` | Challenge assumptions, reframe problem |
| Plan | `writing-plans` + `architect-agent` | Lock architecture, write implementation plan |
| Build | `executing-plans` + `git-commit` | Implement plan, commit frequently |
| Review | `code-reviewer-agent` + `security-reviewer-agent` | Find bugs and vulnerabilities |
| Test | `webapp-testing` + `e2e-runner` | Verify in browser, run e2e |
| Ship | `github-pr-creation` + `github-pr-merge` | PR, merge, deploy |
| Reflect | `/retro` + `/bye` | Statistics, memory, session close |

## When NOT to Use This

- Quick one-liner fixes → just `git-commit` directly
- Documentation-only changes → just `doc-updater`
- Emergency hotfixes → fix → test → commit → deploy (skip Plan/Review)

## Parallel Sprints

You can run multiple sprints in parallel across different branches.
Each sprint should be in its own conversation. Use `/resume` to pick up context.
The `trio-status-sop` keeps all sprints aware of each other through `.muse/` role files.
