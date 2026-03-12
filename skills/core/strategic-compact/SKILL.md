---
name: strategic-compact
description: Suggests manual context compaction at logical intervals to preserve context through task phases rather than arbitrary auto-compaction. Supports focus-aware compaction for targeted context preservation.
---

# Strategic Compact Skill

Suggests manual `/compact` at strategic points rather than relying on arbitrary auto-compaction.

## Why Strategic Compaction?

Auto-compaction triggers at arbitrary points:
- Often mid-task, losing important context
- No awareness of logical task boundaries
- Can interrupt complex multi-step operations

Strategic compaction at logical boundaries:
- **After exploration, before execution** — Compact research, keep plan
- **After completing a milestone** — Fresh start for next phase
- **Before major context shifts** — Clear old context before different task

## Focus-Aware Compaction (inspired by OpenClaw)

普通压缩 = 盲目丢弃。指定重点的压缩 = 保留关键信息。

**用法**：在手动压缩时指定需要保留的重点领域。

```
场景：已完成 3 小时的调试，现在要开始新功能
✅ /compact 保留 bug 根因分析和修复方案，丢弃调试过程中的试错
❌ /compact（盲目压缩，可能丢掉根因分析）
```

**常用 focus 模板**：

| 场景 | Focus 指令 |
|------|------------|
| 调试后 | `保留根因和修复方案，丢弃试错过程` |
| 规划后 | `保留最终方案和关键决策，丢弃备选方案讨论` |
| 代码审查后 | `保留需要改的点，丢弃已确认无问题的部分` |
| 战略讨论后 | `保留战略决策和数据指标，丢弃头脑风暴过程` |
| 多文件编辑后 | `保留改了哪些文件和为什么，丢弃文件内容细节` |

## 何时触发压缩

| 信号 | 动作 |
|------|------|
| 完成了一个完整 milestone | ✅ 适合压缩 |
| 要从探索切到执行 | ✅ 适合压缩 |
| 调试完成，要开始新功能 | ✅ 适合压缩 |
| 正在多步实现中途 | ❌ 不要压缩 |
| 还在分析问题 | ❌ 不要压缩 |
| `/ctx` 显示 60-70% | 🟡 考虑压缩 |
| `/ctx` 显示 ≥ 80% | 🔴 必须退出（宪法规定） |

## Hook Setup

Add to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "tool == \"Edit\" || tool == \"Write\"",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/skills/strategic-compact/suggest-compact.sh"
      }]
    }]
  }
}
```

## Configuration

Environment variables:
- `COMPACT_THRESHOLD` - Tool calls before first suggestion (default: 50)

## Best Practices

1. **带 focus 压缩** — 永远指定保留什么，不要盲目压缩
2. **压缩后写 memory** — 压缩前先把关键信息写入 `memory/YYYY-MM-DD.md`
3. **不要中途压缩** — 多步实现时保持上下文完整
4. **配合 /ctx** — 60-70% 考虑压缩，≥ 80% 必须退出

## Pre-Compaction Protocol（MUSE — 吸收自 LCM compact:before）

压缩前**必须**按顺序执行：
1. **持久化**: 将当前任务进度写入 `memory/YYYY-MM-DD.md`
2. **保护区标记**: 最近 5 轮对话标记为"不可压缩"（≈ LCM freshTailCount=32）
3. **关键决策提取**: 扫描即将被压缩的内容，提取关键决策/数据写入 memory
4. **通知用户**: 告知即将压缩，列出将被保留的重点

> **原则: 先持久化，再压缩。永远不在没有备份的情况下丢弃信息。**

## Post-Compaction Injection（MUSE — 吸收自 OpenClaw postCompactionSections）

压缩后**必须**重新内化以下内容：
1. `CLAUDE.md` 前 4 行（7 条铁律 + 优先级链）
2. 当前 `task.md` 中 `[/]` 标记的进行中任务
3. `memory/` 今天的快照（刚写入的）
4. 任何 focus-aware 指定的保留项

> **原则: 压缩 ≠ 遗忘。核心身份和当前上下文必须在压缩后立即恢复。**
