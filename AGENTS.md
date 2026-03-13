# 🏛 Constitution — MUSE

> Copy this template to your project root and customize.
> This is the AI's "constitution" — iron rules it must follow every session.

## Iron Rules

1. **Language**: 🚨 YOU MUST communicate in **简体中文**. Every response, explanation, question, and comment MUST be in 简体中文. This is NON-NEGOTIABLE. Do NOT default to English unless this rule explicitly says English.
2. **Skill-First**: Before ANY task, check if a relevant Skill exists in `.agent/skills/`
3. **Large Files**: Only view ≤300 lines at a time. Never blindly read entire large files.
4. **Context Protection**: When context ≥ 80%, immediately run `/bye`
5. **Verify Before Claiming Done**: Run `verification-before-completion` skill before saying "done"
6. **End Sessions Properly**: Always use `/bye` to end conversations

## Skill-Driven Execution

- **Speed Reference** (know which skill to use):
  | Task | Skill |
  |------|-------|
  | Git commit | `git-commit` |
  | Code review | `code-reviewer-agent` |
  | Build errors | `build-error-resolver` |
  | Debugging | `systematic-debugging` |
  | **Verify completion** | **`verification-before-completion`** |

## Context Health Pre-Check

Every session start: estimate context usage. If ≥ 70%, suggest opening new conversation.

Defensive saving: every 10 interaction rounds silently update `memory/CRASH_CONTEXT.md`.

## Safety Protocols

- **Action Gate**: STOP and ASK before: Refactoring, Major Updates, Deleting Files.
- **Pre-Flight**: Always BACKUP before approved destructive actions.
- **Rule Zero**: Check `AGENTS.md` + `MEMORIES.md` before every task.

## [Project-Specific Rules]

<!-- Add your project-specific rules below -->
