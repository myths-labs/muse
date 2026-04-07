---
description: 结束对话的一键收尾指令。自动汇总工作、同步 .muse/ 角色文件、写短期记忆。零输入。
---

## 铁律

> **每次 /bye 必须完整执行全部 6 步。跨项目适用（DYA/Prometheus/MUSE）。**
> strategy.md 始终位于 `/Users/jj/Desktop/DYA/.muse/strategy.md`。
> 当前项目使用 MUSE 角色文件系统 (`.muse/*.md`)，严禁创建 STATUS.md 等文件。

## 用法

```
/bye
```

// turbo-all

---

### Step 1: 工作摘要

回顾**完整对话**，不只是最后 20%。方法：
1. 统计本轮 tool calls（代码编辑/命令/文件读取/搜索次数）
2. 从对话**开头**逐段提取工作项
3. 分类: 完成 / 决策 / 否决 / 用户反馈 / 关键URL / 下一步

### Step 2: 检测所有涉及角色

**多角色检测**（不是单选）：
1. 扫描对话中操作过的**所有项目路径**（DYA/ Prometheus/ MUSE/ Airachne/）
2. 扫描关键词: 战略决策/架构变更/技术选型 → 自动追加 STRATEGY
3. 输出: `本轮涉及角色: [列表]`，每个角色独立 sync

角色路由表:
- DYA Strategy → `.muse/strategy.md`
- Prometheus → `Prometheus/.muse/build.md` + strategy回传
- MUSE Build → `MUSE/.muse/build.md` + strategy回传
- MUSE Growth → `MUSE/.muse/growth.md`

### Step 3: 同步角色文件

对 Step 2 检测到的**每个角色**执行:

**3.1 L0 + 状态行更新** — 更新文件首行 L0 注释和 header 时间戳

**3.2 指令状态回写** — `grep -n "🟡\|待回传\|待执行" strategy.md`，本轮完成的翻 ✅

**3.3 新决策正向写入** — 扫描 Step 1 的「决策」列表:
- 每条决策必须对应 strategy.md 中的 S0XX 编号（没有则创建）
- 涉及项目的 build.md 也要更新

**3.4 Checklist 刷新** — 如果 strategy.md 有 Launch Readiness Checklist:
- 本轮完成的项 → 翻 `[x]`
- 新发现的缺口 → 加 `[ ]`
- **不写硬编码百分比**，完成度由 checklist 自动体现

**3.5 Strategy 直接执行下游推送** — 如果 Strategy 角色直接执行了 BUILD 工作:
- 必须推送到对应项目的 build.md（状态/Blocker/技术栈）
- 双向检查: strategy.md 已完成但 build.md 未更新的指令 → 补推

**3.6 MUSE 源码同步检查** — `diff` DYA workflows vs MUSE workflows，有 diff 记入 memory

### Step 4: 写 memory

写入 `memory/YYYY-MM-DD.md`（追加模式）:

```markdown
## [角色] Session N: [标题] (HH:MM-HH:MM)

### 完成
- 条目列表

### 决策
- **[决策内容]**: [原因]
  - type: project/preference | Why: ... | How to apply: ...

### ❌ 否决
- 条目

### 💬 用户反馈
- 纠正/确认: [内容] → Rule: ... | Why: ... | How to apply: ...

### 🔗 关键 URL/文件
- 列表

### 📡 跨对话上下文
- 下轮 Agent 必须知道的关键状态

### ➡️ 下一步
- 🔲 [角色] 待办项
```

**禁存**: API Key / 密码 / .env 内容 / 临时 debug 日志 / 大段代码

### Step 5: 导出对话

```bash
mkdir -p convo/YYMMDD/
# 引导用户导出到: convo/YYMMDD/YYMMDD-NN-[标题].md
```

### Step 6: 告知用户

输出:
1. 一行摘要（角色 + 主要完成项）
2. SOP 合规 checklist（Step 1-5 每步 ✅/❌）
3. 导出建议路径
4. 如有 MUSE 源码 diff → 提醒下轮同步

---

## 教训索引

> 详细教训存储在 `MEMORIES.md` 和 Obsidian Vault `MythsLabs/bugs/`。
> 以下仅列索引，供 Agent 遇到相关场景时查阅。

| ID | 教训 | 参考 |
|:--:|------|------|
| BUG-MEM-01 | /bye 不回写指令状态 → Step 3.2 grep 翻转 | MEMORIES.md |
| BUG-MUSE-02 | 混合角色对话只 sync 一个 → Step 2 多角色检测 | MEMORIES.md |
| BUG-MUSE-03 | Strategy 做 BUILD 工作 build.md 不知道 → Step 3.5 | MEMORIES.md |
| BUG-MUSE-04 | 硬编码% 写后僵死 → Step 3.4 Checklist 刷新 | MEMORIES.md |
| BUG-MUSE-05 | /resume 盲信数字 → resume.md Checklist 核查 | MEMORIES.md |
