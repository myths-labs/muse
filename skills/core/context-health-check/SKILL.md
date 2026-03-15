---
name: context-health-check
description: Context window health check. Trigger with /ctx or phrases like "context check", "do I need a new conversation", "how much context left". Evaluates current context consumption and recommends whether to start a new conversation.
---

# Context Health Check

When this skill is triggered, perform the following assessment and output a report.

## Token Estimation Method

LLMs cannot directly read consumed token counts. Use these proxy formulas:

### Estimation Formula

```
Consumed ≈ System Overhead + Σ(Per-turn Consumption)

System Overhead ≈ 15K-25K tokens (system prompt + skills metadata + workspace info)

Per-turn Consumption ≈ User message (~200-500) 
           + Tool call results (each ~500-5000, large file reads ~3000-8000)
           + Assistant response (~500-2000)
```

### High-Consumption Operation Reference

| Operation | Estimated Tokens |
|-----------|:---------------:|
| Read <100 line file | ~500-1500 |
| Read 200-500 line file | ~3000-5000 |
| Read 500+ line file (e.g. STATUS.md) | ~5000-10000 |
| grep search results (50 matches) | ~3000-5000 |
| Long command output | ~2000-8000 |
| Generate/edit a file | ~1000-3000 |
| Browser operations (with DOM) | ~5000-15000 |

### Model Context Windows

| Model | Total Window | Available (minus overhead) | Safety Threshold (80%) |
|-------|:-----------:|:-------------------------:|:---------------------:|
| Claude Opus/Sonnet (Anthropic) | 200K | ~175K | **140K** |
| GPT-4o (OpenAI) | 128K | ~105K | **84K** |
| Gemini Pro (Google) | 1M+ | ~950K+ | **Unlikely to overflow** |

⚠️ **MUST read `USER.md` `model preference` field first.** If found, use that model's window size. If not found, default to Claude 200K. **Do NOT default to Gemini 1M or other models.**

## Assessment Process

1. **Identify current model** (read `USER.md` → `model preference` field. If not found, default to Claude 200K. **Do not guess, do not use Gemini 1M**)
2. **Count conversation turns** (user↔assistant interaction count)
3. **Estimate tool call token consumption** (accumulate per the table above)
4. **Calculate total estimated consumption**
5. **Calculate remaining percentage** = (available window - consumed) / available window
6. **Assign health level**

## Health Levels

| Level | Remaining % | Recommendation |
|:----:|:----------:|----------------|
| 🟢 **Healthy** | >50% remaining | Continue working, no concerns |
| 🟡 **Caution** | 20-50% remaining | Finish current task then start a new conversation. Avoid loading more large files. Avoid long output commands |
| 🔴 **Danger** | <20% remaining | ⚠️ Immediately update status files and start a new conversation. Continuing will likely cause forgetting/repetition/quality degradation |

### Quick Judgment Rules of Thumb (when you don't want to calculate)

For Claude 200K window:
- **≤5 turns + 1 large file** → 🟢 
- **10-15 turns + 2-3 large files + multiple code edits** → 🟡
- **>18 turns** or **>5 large file reads** or **starting to forget early content** → 🔴

## Output Format

```
## 🧠 Context Health Check

**Model**: [Claude/GPT-4o/Gemini/...] (context window XK)

| Metric | Current Value | Estimated Tokens |
|--------|:------------:|:----------------:|
| System overhead | — | ~20K |
| Conversation turns | X turns | ~YK |
| Large file reads | [list files + line counts] | ~ZK |
| Tool calls | ~N calls | ~WK |
| **Total estimated** | — | **~TK** |
| **Remaining estimated** | — | **~RK (P%)** |

**Health Level**: 🟢/🟡/🔴

**Recommendation**: [specific advice]
**Estimated remaining capacity**: ~M normal turns / ~L large file reads
```

## Defensive Auto-Save

> **Core problem**: 🔴 detection depends on the Agent having an opportunity to execute — when context suddenly overflows, the Agent has no chance to save anything.
> **Solution**: Don't wait for 🔴 — proactively save every 10 turns.

### Rules

1. **Every 10 interaction turns** (one user↔assistant round = 1 turn), Agent **MUST** silently update `memory/CRASH_CONTEXT.md`
2. **Silent = don't interrupt the user**. No announcement needed, no confirmation needed. Complete during response or between tool calls
3. **Incremental update**: Only update changed fields, don't full-rewrite
4. **Format** matches what's written during 🔴 detection (see Additional Rule #1 below)
5. **Delete after recovery**: After `/resume crash` successfully recovers, delete `CRASH_CONTEXT.md` (avoid stale data)
6. **Trigger timing checklist**:
   - Turn 10 → First write ✅
   - Turn 20 → Update ✅
   - Turn 30 → Update ✅ (usually approaching 🟡/🔴 by now)
   - 🔴 detection triggered → Final update (including "suggested next steps") ✅

### Defense Layers

| Layer | Trigger Condition | Reliability |
|:-----:|-------------------|:----------:|
| **L0 Defense** | Silent save every 10 turns | ⭐⭐⭐ Most reliable |
| **L1 Warning** | Auto-save when `/ctx` detects 🔴 | ⭐⭐ Needs detection opportunity |
| **L2 Fallback** | `/resume crash` scans `convo/` for _CRASH files | ⭐ Safety net |

## Additional Rules

1. When 🔴 danger is detected, **automatically** execute memory snapshot + crash recovery file (MUSE compact:before protocol):
   - Write current progress to `memory/YYYY-MM-DD.md` (don't wait for user /bye)
   - Update `task.md` progress markers
   - **Write `memory/CRASH_CONTEXT.md`** (structured recovery file, auto-read by next `/resume crash`):
     ```markdown
     # Crash Context — YYYY-MM-DD HH:MM
     ## Current Role: [strategy/build/growth/qa]
     ## Current Task: [what was being done]
     ## Unfinished: [list]
     ## Key Decisions: [decisions made this session]
     ## User's Last Question: [if any]
     ## Suggested Next Steps: [what to do after recovery]
     ```
   - Then notify the user:
     ```
     ⚠️ Context is about to overflow! Auto-saved:
     - memory/YYYY-MM-DD.md ✅
     - memory/CRASH_CONTEXT.md ✅
     Please end this conversation. Use `/resume crash` in a new conversation to auto-recover.
     To export this conversation, save to: convo/YYMMDD/YYMMDD-NN-desc_CRASH.md
     ```
2. If current conversation has not loaded any status files and is ≤3 turns, report 🟢 directly without detailed calculation
3. Natural language triggers also apply ("how much context left?", "context enough?", etc.)
4. If you detect yourself forgetting early conversation content or repeating yourself, even if the formula says there's room left, report 🔴 directly

## 🆕 Session Checkpoint (v2.14.0 — OpenViking-inspired)

> Inspired by OpenViking's session compression — auto-checkpoint mid-conversation to prevent context loss.
> Complements Defensive Auto-Save (CRASH_CONTEXT.md): Auto-Save = crash recovery safety net, Session Checkpoint = quality preservation.

### Why

Long conversations degrade quality because the Agent loses track of early context. By the time `/bye` runs, the Agent may have already forgotten 50-80% of early work. Session Checkpoint writes compressed mid-session snapshots to preserve context fidelity.

### When to Checkpoint

| Trigger | Action |
|---------|--------|
| **Every 15 turns** | Silent checkpoint (no user notification) |
| **After a major milestone** (commit, deploy, release, version bump) | Silent checkpoint |
| **When /ctx detects 🟡** | Checkpoint + notify user |
| **When switching topics** (user asks about something unrelated to current work) | Silent checkpoint |

### What to Write

**File**: `memory/YYYY-MM-DD.md` (append, not overwrite)

**Format** (compressed — use Semantic Compression rules from `/bye`):
```markdown
## 📍 Checkpoint (HH:MM, ~turn N)
- 主线: [1-2 sentence summary of work so far]
- 决策: [key decisions if any]
- 状态: [current task status]
```

### Rules

1. **Silent**: Do NOT announce checkpoints to the user. Do NOT ask for confirmation. Write silently between tool calls
2. **Append-only**: Never overwrite existing memory content. Always append
3. **Compressed**: Use the 5:1 compression ratio — max 3-4 lines per checkpoint
4. **Idempotent**: If the same milestone was already checkpointed, skip (check last checkpoint's content)
5. **No performance impact**: Checkpoint during response generation or between tool calls, never adding a delay
6. **Checkpoint counter**: Track `_checkpoint_count` mentally. First checkpoint = turn ~15, then every ~15 turns after

### Interaction with Other Systems

| System | Relationship |
|--------|-------------|
| **Defensive Auto-Save** (CRASH_CONTEXT.md) | Auto-Save = full structured snapshot for crash recovery. Checkpoint = lightweight append for quality preservation. Both can coexist |
| **`/bye` Step 1** | `/bye` should READ checkpoints to reconstruct full session history (prevents the 80% forgetting problem) |
| **`/bye` Step 4** | Final memory write should reference checkpoints: "See checkpoints at HH:MM, HH:MM" |
| **`/resume`** | Checkpoints appear as part of daily memory — no special handling needed |

