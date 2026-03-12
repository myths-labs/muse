---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always. Upgraded with AC-first workflow, pre-flight fast-fail, and structured Judge verdicts (inspired by opslane/verify).
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

---

## Phase 0: AC-First Workflow (写代码前)

> 💡 Inspired by opslane/verify: "You can't trust what an agent produces unless you told it what 'done' looks like before it started."

**Before writing any code, define Acceptance Criteria:**

```markdown
## Acceptance Criteria

### AC-1: [Feature/behavior name]
- [Observable outcome 1]
- [Observable outcome 2]

### AC-2: [Edge case / error handling]
- [What user sees]
- [What system does]

### AC-3: [Integration / compatibility]
- [Works with X]
- [Doesn't break Y]
```

**AC Writing Rules:**
- Each AC must be **independently verifiable** (pass or fail, no "partially")
- Use **observable behavior** not implementation details ("User sees X" not "Code calls Y")
- Include **negative cases** (what happens when things go wrong)
- For frontend: specify exact text, navigation, visual state
- For backend: specify status codes, response shape, error messages
- For mobile: specify platform behavior, i18n, haptics

**When to write ACs:**
- ✅ Before ANY new feature (even "simple" ones)
- ✅ Before bug fixes (AC = "original symptom no longer occurs" + "no regression")
- ✅ Before refactors (AC = "all existing behavior preserved")
- ❌ NOT needed for: config changes, docs-only, status file updates

---

## Phase 1: Pre-Flight Check (零成本快速失败)

> 💡 Pure checks, no LLM tokens. Fail fast before spending effort.

**Before starting work, verify preconditions:**

```
PRE-FLIGHT CHECKLIST (30 seconds, zero tokens):
□ Dev server running? (or can it start?)
□ Target files exist and are accessible?
□ Dependencies installed? (node_modules, Pods, etc.)
□ Auth/session valid? (Supabase, App Store Connect, etc.)
□ Branch correct? (not accidentally on main when should be feature)
□ Previous build clean? (no leftover errors)
```

**If any pre-flight fails → FIX IT FIRST, don't start the feature.**

This prevents the classic failure: spending 30 minutes coding, then discovering the dev server was down the whole time.

---

## Phase 2: The Gate Function (执行完成后)

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

---

## Phase 2.5: Deep QA Loop (反弄虚作假·无限循环)

> ⚠️ **教训**: Agent 多次声称 "QA 100% 通过"，实际只检查了页面是否加载（HTTP 200）和 API 状态码。
> 前端通了但核心功能（TTS/支付/WebSocket）没有真正验证。这不是 QA，这是**弄虚作假**。

### 什么不算 QA（严禁用以下方式声称 QA 通过）

| 浅层检查 | 为什么不算 |
|---------|-----------|
| 页面返回 HTTP 200 | 只证明页面加载，不证明功能正常 |
| API 返回正确状态码 | 只证明路由存在，不证明业务逻辑正确 |
| `next build` / `expo prebuild` exit 0 | 只证明编译通过，不证明运行时行为正确 |
| dev server 控制台无报错 | 不触发 ≠ 没有 bug |
| "看起来没有错误" | 不看 ≠ 没有 |
| "视觉检查通过" | 没看截图只看代码 ≠ 视觉通过 |

### 什么才算深度 QA（必须全部做到）

- ✅ **每个用户交互流程**实际走一遍（点击按钮、提交表单、触发动画、完整聊天往返）
- ✅ **每个 API 调用**验证请求体+响应内容（不只是状态码，检查返回的数据是否正确）
- ✅ **每个状态变化**验证 UI 是否正确更新（loading→success→idle、错误提示显示消失）
- ✅ **每个集成点**端到端验证（前端→API→数据库→返回→UI更新 全链路）
- ✅ **错误路径**必须测试（无网络、无权限、空数据、非法输入、超时）
- ✅ **需要登录的功能**用真实认证状态测试（不能跳过说"需要手动测试"）
- ✅ **媒体功能**（TTS/语音/视频）必须实际触发并确认输出（不能只检查 API 是否返回）

### QA 循环规则

```
深度 QA → 发现问题 → 修复 → 深度 QA → 发现问题 → 修复 → 深度 QA → ...
→ 全部 100% 零问题 → 才能说"完成"
```

- ❌ 1 个 FAIL → 不允许说"完成"
- ❌ "需要手动测试" → 能自动化就自动化，不能就用浏览器工具/curl 实际测试
- ❌ "非 blocker" → 用户可感知的问题都是 blocker
- **违反本规则 = 与「假功能」同级 = 最严重 bug**

---

## Phase 3: Judge Verdict (结构化判决)

> 💡 Inspired by opslane/verify's Judge pattern: separate execution from judgment.

**After verification, produce a structured verdict for each AC:**

```markdown
## Verification Report

| AC | Verdict | Evidence |
|----|---------|----------|
| AC-1: Login redirect | ✅ PASS | `curl -s -o /dev/null -w "%{http_code}" → 302` |
| AC-2: Error message | ✅ PASS | Screenshot shows "Invalid email or password" |
| AC-3: Rate limiting | ❌ FAIL | 6th attempt still allowed (expected: blocked) |
| AC-4: i18n | 🟡 NEEDS-REVIEW | Translation exists but quality unverified |

**Overall: 2/4 PASS, 1 FAIL, 1 NEEDS-REVIEW**
**Verdict: NOT READY — AC-3 must be fixed before completion**
```

**Three verdict types:**
- **✅ PASS** — Evidence confirms AC is met
- **❌ FAIL** — Evidence shows AC is NOT met (must fix)
- **🟡 NEEDS-REVIEW** — Cannot be automatically verified (needs human check)

**Rules:**
- NEVER mark PASS without evidence
- FAIL requires specific description of what went wrong
- NEEDS-REVIEW is for visual/UX/copy that can't be command-verified
- **Overall verdict = FAIL if ANY AC is FAIL**

---

## Common Verification Methods

| What to verify | Method | Not sufficient |
|---------------|--------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line AC checklist | Tests passing |
| API endpoint | `curl` with expected status/body | "Code looks right" |
| UI behavior | Browser screenshot/recording | "Component renders" |
| i18n complete | Grep all locale files for key | "Added to en.json" |
| Mobile build | `npx expo prebuild` exit 0 | "No errors in editor" |

## Red Flags — STOP Immediately

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!")
- About to commit/push/PR without verdict report
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- **ANY wording implying success without having run verification**
- **Skipping AC writing because task "seems simple"**
- **Mentally marking AC as PASS without running the check**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "Too simple for ACs" | Simple tasks have simple ACs — write them anyway |
| "ACs slow me down" | Rework from false completion is slower |
| "Partial check is enough" | Partial proves nothing |

## Quick Reference: Full Workflow

```
┌─────────────────────────────────────────┐
│ 1. DEFINE ACs (before coding)           │
│    What does "done" look like?          │
├─────────────────────────────────────────┤
│ 2. PRE-FLIGHT (before coding)           │
│    Dev server? Files? Deps? Branch?     │
├─────────────────────────────────────────┤
│ 3. EXECUTE (write code)                 │
│    Build the feature / fix the bug      │
├─────────────────────────────────────────┤
│ 4. GATE (after coding)                  │
│    Run verification commands            │
├─────────────────────────────────────────┤
│ 5. JUDGE (before claiming done)         │
│    Produce verdict per AC               │
│    ALL PASS → claim completion          │
│    ANY FAIL → fix and re-verify         │
│    ANY NEEDS-REVIEW → flag for human    │
└─────────────────────────────────────────┘
```

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**The Bottom Line:**

No shortcuts for verification. Define ACs. Run pre-flight. Execute. Verify. Judge. THEN claim the result.

This is non-negotiable.
