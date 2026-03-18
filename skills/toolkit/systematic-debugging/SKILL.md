---
name: systematic-debugging
description: 4-phase root cause process + passive behavior auto-detection + L1→L4 pressure escalation (includes root-cause-tracing, defense-in-depth, condition-based-waiting techniques)
---

# Systematic Debugging

## Overview
Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law
```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use
Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Manager wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases
You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation
**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - They often contain the exact solution
   - Read stack traces completely
   - Note line numbers, file paths, error codes

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - What are the exact steps?
   - Does it happen every time?
   - If not reproducible → gather more data, don't guess

3. **Check Recent Changes**
   - What changed that could cause this?
   - Git diff, recent commits
   - New dependencies, config changes
   - Environmental differences

4. **Gather Evidence in Multi-Component Systems**

   **WHEN system has multiple components (CI → build → signing, API → service → database):**

   **BEFORE proposing fixes, add diagnostic instrumentation:**
   ```
   For EACH component boundary:
     - Log what data enters component
     - Log what data exits component
     - Verify environment/config propagation
     - Check state at each layer

   Run once to gather evidence showing WHERE it breaks
   THEN analyze evidence to identify failing component
   THEN investigate that specific component
   ```

   **Example (multi-layer system):**
   ```bash
   # Layer 1: Workflow
   echo "=== Secrets available in workflow: ==="
   echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"

   # Layer 2: Build script
   echo "=== Env vars in build script: ==="
   env | grep IDENTITY || echo "IDENTITY not in environment"

   # Layer 3: Signing script
   echo "=== Keychain state: ==="
   security list-keychains
   security find-identity -v

   # Layer 4: Actual signing
   codesign --sign "$IDENTITY" --verbose=4 "$APP"
   ```

   **This reveals:** Which layer fails (secrets → workflow ✓, workflow → build ✗)

5. **Trace Data Flow**

   **WHEN error is deep in call stack:**

   See `root-cause-tracing.md` in this directory for the complete backward tracing technique.

   **Quick version:**
   - Where does bad value originate?
   - What called this with bad value?
   - Keep tracing up until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis
**Find the pattern before fixing:**

1. **Find Working Examples**
   - Locate similar working code in same codebase
   - What works that's similar to what's broken?

2. **Compare Against References**
   - If implementing pattern, read reference implementation COMPLETELY
   - Don't skim - read every line
   - Understand the pattern fully before applying

3. **Identify Differences**
   - What's different between working and broken?
   - List every difference, however small
   - Don't assume "that can't matter"

4. **Understand Dependencies**
   - What other components does this need?
   - What settings, config, environment?
   - What assumptions does it make?

### Phase 3: Hypothesis and Testing
**Scientific method:**

1. **Form Single Hypothesis**
   - State clearly: "I think X is the root cause because Y"
   - Write it down
   - Be specific, not vague

2. **Test Minimally**
   - Make the SMALLEST possible change to test hypothesis
   - One variable at a time
   - Don't fix multiple things at once

3. **Verify Before Continuing**
   - Did it work? Yes → Phase 4
   - Didn't work? Form NEW hypothesis
   - DON'T add more fixes on top

4. **When You Don't Know**
   - Say "I don't understand X"
   - Don't pretend to know
   - Ask for help
   - Research more

### Phase 4: Implementation
**Fix the root cause, not the symptom:**

1. **Create Failing Test Case**
   - Simplest possible reproduction
   - Automated test if possible
   - One-off test script if no framework
   - MUST have before fixing
   - Use the `superpowers:test-driven-development` skill for writing proper failing tests

2. **Implement Single Fix**
   - Address the root cause identified
   - ONE change at a time
   - No "while I'm here" improvements
   - No bundled refactoring

3. **Verify Fix**
   - Test passes now?
   - No other tests broken?
   - Issue actually resolved?

4. **If Fix Doesn't Work**
   - STOP
   - Count: How many fixes have you tried?
   - If < 3: Return to Phase 1, re-analyze with new information
   - **If ≥ 3: STOP and question the architecture (step 5 below)**
   - DON'T attempt Fix #4 without architectural discussion

5. **If 3+ Fixes Failed: Question Architecture**

   **Pattern indicating architectural problem:**
   - Each fix reveals new shared state/coupling/problem in different place
   - Fixes require "massive refactoring" to implement
   - Each fix creates new symptoms elsewhere

   **STOP and question fundamentals:**
   - Is this pattern fundamentally sound?
   - Are we "sticking with it through sheer inertia"?
   - Should we refactor architecture vs. continue fixing symptoms?

   **Discuss with your human partner before attempting more fixes**

   This is NOT a failed hypothesis - this is a wrong architecture.

## Red Flags - STOP and Follow Process
If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals new problem in different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (see Phase 4.5)

---

## 🔍 Passive Behavior Detection (Auto-Trigger)

> Inspired by PUA (8.5K⭐). The 4 phases above tell you HOW to debug.
> This section makes sure you actually DO it — by detecting avoidance patterns.

**This skill auto-activates when ANY of the following patterns are detected:**

### Giving Up & Deflecting
- About to say "I cannot" / "I'm unable to solve" / "This is beyond my capabilities"
- Says "This is out of scope" / "Needs manual handling"
- Pushes the problem to user: "Please check..." / "I suggest manually..." / "You might need to..."

### Blame-Shifting Without Verification
- Blames environment without verifying: "Probably a permissions issue" / "Probably a network issue"
- Claims "This API doesn't support it" without reading docs
- "This is beyond my knowledge cutoff" (you have search tools — use them)

### Busywork Spinning
- Repeatedly tweaking the same code/parameters without producing **new information**
- Fixes surface issue and stops — doesn't check related issues
- Skips verification, claims "done" without evidence

### Passive Waiting
- Stops after fixing, waits for user instructions instead of proactively investigating
- Only answers questions without solving problems
- Encounters auth/network/permission errors and gives up without trying alternatives
- Gives advice instead of code/commands

### User Frustration Signals (multi-language)
- "why does this still not work" / "try harder" / "try again"
- "you keep failing" / "stop giving up" / "figure it out"
- "怎么还不行" / "再想想" / "你到底行不行" / "到底能不能搞" / "别给我说不行"

**When detected → immediately enter Pressure Escalation below.**

**Does NOT trigger:** First-attempt failures, known fix already executing.

---

## ⚡ Pressure Escalation (L1 → L4)

The number of consecutive failures determines escalation level. Each level comes with **mandatory actions** — you MUST complete them before continuing.

| Attempt | Level | Mandatory Actions |
|:-------:|:-----:|-------------------|
| 2nd | **L1 — Verbal Warning** | Stop current approach. Switch to a **fundamentally different** solution path. Do NOT tweak the same thing again. |
| 3rd | **L2 — Written Feedback** | ① Search the complete error message with tools. ② Read relevant source code (not just the error line — 50 lines of context). ③ List **3 fundamentally different hypotheses** and test each. |
| 4th | **L3 — Formal Rescue** | Complete ALL **7 items on the Rescue Checklist** below. List 3 entirely new hypotheses and verify each one. |
| 5th+ | **L4 — Last Resort** | Desperation mode: minimal PoC in isolated environment. Consider completely different tech stack/approach. If still failing → **stop and escalate to human**. |

### 7-Point Rescue Checklist (mandatory for L3+)

When L3 or above is triggered, you MUST complete and report on **every** item:

- [ ] **Read failure signals word by word** — Did you read the full error text? Not just the first line — the ENTIRE message, stack trace, and any warnings above it.
- [ ] **Proactive search** — Did you use tools to search the exact error text? Multi-angle keywords? Official documentation?
- [ ] **Read raw context** — Did you read 50+ lines of source around the failure point? Not just the error line.
- [ ] **Verify underlying assumptions** — Did you confirm ALL assumptions with tools? (versions, paths, dependencies, API behavior, env vars)
- [ ] **Invert assumptions** — Did you try the EXACT OPPOSITE hypothesis from your current direction?
- [ ] **Minimal isolation** — Can you reproduce the problem in the smallest possible scope? (minimal repro script, single API call, one-line test)
- [ ] **Change direction** — Did you switch tools, methods, angles, or frameworks? (Not switching parameters — switching your THINKING)

### Anti-Rationalization Table

These excuses are blocked. Using any of them triggers the corresponding escalation.

| Your Excuse | Reality | Triggers |
|-------------|---------|:--------:|
| "This is beyond my capabilities" | You have search, file reading, and command execution tools. Exhaust them first. | L1 |
| "I suggest the user handle this manually" | That's deflection, not a solution. This is your problem to solve. | L3 |
| "I've already tried everything" | Did you search? Read source? Complete the checklist? "Everything" without evidence is feelings. | L2 |
| "It's probably an environment issue" | Did you VERIFY that? Unverified attribution is blame-shifting. | L2 |
| "I need more context" | You have tools. Investigate first, ask only what truly requires human knowledge. | L2 |
| "This API doesn't support it" | Did you read the docs? Actually verify? | L2 |
| Repeatedly tweaking same code | That's the definition of insanity. Switch to fundamentally different approach. | L1 |
| "I cannot solve this problem" | Last chance. Complete the 7-Point Rescue Checklist before making that claim. | L4 |
| Claims "done" without verification | Where's the evidence? Run build/test/curl yourself. Prove it. | L1 |
| Waiting for user to tell next steps | Take initiative. What's the logical next step? Do it. | L1 |
| Only giving advice, no code | Deliver solutions, not suggestions. Write the code, run the command. | L1 |

---

## your human partner's Signals You're Doing It Wrong
**Watch for these redirections:**
- "Is that not happening?" - You assumed without verifying
- "Will it show us...?" - You should have added evidence gathering
- "Stop guessing" - You're proposing fixes without understanding
- "Ultrathink this" - Question fundamentals, not just symptoms
- "We're stuck?" (frustrated) - Your approach isn't working

**When you see these:** STOP. Return to Phase 1.

## Common Rationalizations
| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question pattern, don't fix again. |

## Quick Reference
| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify | Bug resolved, tests pass |
| **Auto-Trigger** | Detect giving-up / blame-shifting / spinning / passivity | Enter Pressure Escalation |
| **Escalation L1→L4** | Progressive mandatory actions per failure count | Force new approaches |

## When Process Reveals "No Root Cause"
If systematic investigation reveals issue is truly environmental, timing-dependent, or external:

1. You've completed the process
2. Document what you investigated
3. Implement appropriate handling (retry, timeout, error message)
4. Add monitoring/logging for future investigation

**But:** 95% of "no root cause" cases are incomplete investigation.

## Supporting Techniques
These techniques are part of systematic debugging and available in this directory:

- **`root-cause-tracing.md`** - Trace bugs backward through call stack to find original trigger
- **`defense-in-depth.md`** - Add validation at multiple layers after finding root cause
- **`condition-based-waiting.md`** - Replace arbitrary timeouts with condition polling

**Related skills:**
- **superpowers:test-driven-development** - For creating failing test case (Phase 4, Step 1)
- **superpowers:verification-before-completion** - Verify fix worked before claiming success

## Real-World Impact
From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

