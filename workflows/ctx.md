---
description: Check current conversation's context window health and assess if a new conversation is needed
---

## Trigger

- User runs `/ctx`
- Or asks "is context enough?", "do I need a new conversation?", "context check"

## Execution

### 0. 读取 LLM 上下文窗口（必须执行，不可跳过）

> [!CAUTION]
> **必须先读 `USER.md`** 获取用户配置的模型和上下文窗口，以此为计算基准。
> **禁止 fallback、禁止猜测、禁止硬编码。** 用户指定什么模型就用什么模型的窗口大小。

1. 读取项目根目录的 `USER.md` → `AI Model` section
2. 提取 **Preferred Model** 和 **Context Window** 值
3. 如 `USER.md` 不存在或 `AI Model` section 未设值 → **停止执行**，输出：
   ```
   ❌ USER.md 中未配置 AI Model / Context Window，无法计算。
   请先运行 /settings 设置你的模型。
   ```

### 1. 估算当前上下文用量

基于对话长度、已读文件数、tool call 次数估算 token 占用，**除以 Step 0 得到的窗口大小**。

### 2. 交通灯评估

| Status | Usage | Action |
|:------:|:-----:|--------|
| 🟢 Green | < 50% | Safe to continue |
| 🟡 Yellow | 50-80% | Wrap up current task, avoid starting new large tasks |
| 🔴 Red | > 80% | **Stop immediately**, run `/bye`, start new conversation |

### 3. 输出健康报告

```
🟢/🟡/🔴 Context: ~XX% of [MODEL_NAME] [WINDOW_SIZE]
Estimated remaining: ~N rounds
Recommendation: [continue / wrap up soon / stop now]
```

## Defensive Auto-Save (L0 Defense)

Every **10 interaction rounds**, silently update `memory/CRASH_CONTEXT.md` — no user interruption needed.

| Layer | Trigger | Reliability |
|:-----:|---------|:-----------:|
| L0 | Every 10 rounds (silent) | ⭐⭐⭐ |
| L1 | 🔴 context detection | ⭐⭐ |
| L2 | `/resume crash` scans convo/ | ⭐ |

If a sudden blowout occurs, at most 10 rounds of progress are lost.
