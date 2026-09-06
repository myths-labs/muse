---
name: layered-context
description: L0/L1/L2 three-layer context loading protocol — reduces token consumption during /resume boot
---

# Layered Context Loading Protocol

> Inspired by OpenViking (ByteDance) L0/L1/L2 architecture.
> Adapted for MUSE's on-demand Markdown context loading.

## Why

Full-loading all `.muse/*.md` files during `/resume` wastes tokens when the Agent only needs one role's context. The layered approach loads minimum context first, then deepens on demand.

## Three Layers

| Layer | Token Budget | Content | When to Load |
|:-----:|:-----------:|---------|-------------|
| **L0** | ~100 tokens | One-line HTML comment at top of each `.muse/*.md` | **Always** — scan ALL role files |
| **L1** | ~2K tokens | Full role file content | **On demand** — only the CURRENT role's file |
| **L2** | Unbounded | `memory/*.md` + code files + docs | **On demand** — grep search when needed |

## L0 Format

Every `.muse/*.md` file MUST have an L0 comment as the **first line**:

```html
<!-- L0: v2.10.1 | P0=竞品技术吸收, P1/P2全清, QA PASS, S036已接收 -->
```

### L0 Content Rules

1. **Max 120 characters** (excluding `<!-- L0: ` and ` -->`)
2. **Must include**: current version + top priority + blocking issues
3. **Pipe-separated** sections: `version | priorities | status`
4. **Updated every /bye** — when the role file is synced

### L0 Examples

```html
<!-- L0: v2.10.1 | P0=竞品技术吸收(mem0/OpenViking), P1全清, QA 10/10 PASS -->
<!-- L0: 9/9渠道已发, Show HN暂缓, S040梗图排期中, Stars=2 -->
<!-- L0: 最近QA全PASS(10/10 v2.3), 无待修FAIL, QA清洁状态 -->
```

## Boot Sequence with Layered Loading

```
/resume [role]
  │
  ├─① Read CLAUDE.md + MEMORIES.md (constitutional layer, always)
  │
  ├─② Scan ALL .muse/*.md L0 lines (grep "<!-- L0:" .muse/*.md)
  │   → Get one-liner status of every role in ~400 tokens total
  │
  ├─③ Deep-read CURRENT role's .muse/*.md (L1, full file)
  │   → Only the file matching /resume [role]
  │
  ├─④ Scan memory/ for unfinished items (L2, on demand)
  │   → grep 🔲 and [ ] in recent memory files
  │
  └─⑤ grep strategy.md for 🟡 directives (L2, on demand)
      → Only if non-strategy role
```

## Decision Tree: When to Upgrade

```
Agent receives a question/task
  │
  ├─ Can answer from L0? → Answer immediately
  │   (e.g., "What version is MUSE?" → L0 has it)
  │
  ├─ Need role details? → Load L1 (full role file)
  │   (e.g., "What's the P0 task?" → need build.md details)
  │
  └─ Need historical context? → Load L2 (memory/grep)
      (e.g., "What did we decide about X last week?" → grep memory/)
```

## Maintaining L0

### Who Updates L0

The **`/bye` workflow** updates L0 as part of Step 3.5 (role file sync):
1. After syncing the role file content
2. Rewrite the L0 comment to reflect current state
3. Keep within 120 char limit

### L0 Staleness Detection

If the L0 comment's version doesn't match the latest tag, the `/resume` boot should flag it:
```
⚠️ L0 stale: build.md says v2.10.1 but latest tag is v2.11.0
```
