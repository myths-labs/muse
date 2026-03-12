# Creating Domain Skills

Domain skills are your own specialized knowledge that you create for your specific projects and workflows. They live in your project's `.agent/skills/` directory and are NOT part of the MUSE open-source repo.

## When to Create a Domain Skill

- A lesson from `MEMORIES.md` has appeared 3+ times
- A methodology is generic enough to be reusable
- You find yourself repeating the same instructions to your AI

## Structure

```
.agent/skills/your-skill-name/
└── SKILL.md
```

## SKILL.md Format

```yaml
---
name: your-skill-name
description: Brief description of when to use this skill
---
```

Then write your skill content in Markdown below the frontmatter.

## Examples of Domain Skills

- `china-growth-marketing` — Platform-specific growth strategies
- `video-production-workflow` — AI video generation prompts
- `investor-lens` — VC perspective review framework
- `expo-app-design` — Mobile app design patterns

## Skill Lifecycle

```
memory/ lessons repeat → /distill → MEMORIES.md
→ ≥3 occurrences → upgrade to CLAUDE.md rule
→ generic methodology → create Domain Skill
→ useful across projects → contribute to MUSE Toolkit
```
