---
description: 结束对话的一键收尾指令。自动汇总工作、同步 .muse/ 角色文件、写短期记忆。零输入。
---

## 铁律

> **每次 /bye 必须完整执行全部 6 步。跨项目适用。**
> 路径配置: 读取 `.muse/paths.md` 中的路径定义（如 `STRATEGY_PATH`、`OBSIDIAN_VAULT`）。
> 未配置的路径默认为当前项目根目录。
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
1. 扫描对话中操作过的**所有项目路径**（检测 `.muse/` 文件操作）
2. 扫描关键词: 战略决策/架构变更/技术选型 → 自动追加 STRATEGY
3. 输出: `本轮涉及角色: [列表]`，每个角色独立 sync

角色路由表（默认，可通过 `.muse/paths.md` 覆盖）:
- Strategy → `.muse/strategy.md`（如有 `STRATEGY_PATH` 配置则用外部路径）
- Build → `.muse/build.md`（如有跨项目 strategy 则回传）
- Growth → `.muse/growth.md`
- QA → `.muse/qa.md`

### Step 3: 同步角色文件

对 Step 2 检测到的**每个角色**执行:

**3.1 L0 + 状态行更新** — 更新文件首行 L0 注释和 header 时间戳

**3.2 指令状态回写** — 如有外部 strategy.md（`.muse/paths.md` 中 `STRATEGY_PATH`），`grep -n "🟡\|待回传\|待执行" strategy.md`，本轮完成的翻 ✅
- 🔴 **BUG-MUSE-08 修复 — 全文件一致性验证**: 翻转后，对每个被翻转的指令编号执行 `grep "<编号>" strategy.md`，确认该编号在**所有出现位置**（进度表 / 活跃指令队列 / Checklist / Countdown / 待办）状态一致。不一致 → 立即修正。
  - ⚠️ 常见遗漏: 进度表标了 ✅ 但活跃指令队列仍是 🟡（两处数据结构独立，Agent 容易只改一处）

**3.3 新决策正向写入** — 扫描 Step 1 的「决策」列表:
- 每条决策记录到对应角色文件
- 如有跨项目 strategy.md 也要同步

**3.4 Checklist 刷新** — 如果 strategy.md 有 Launch Readiness Checklist:
- 本轮完成的项 → 翻 `[x]`
- 新发现的缺口 → 加 `[ ]`
- **不写硬编码百分比**，完成度由 checklist 自动体现
- 🔴 **BUG-MUSE-08 修复 — 已关闭项清理**: 本轮确认「非 bug / 设计如此 / 不再需要」的项 → 从 Checklist **删除或标注关闭原因**，不能留空 `[ ]` 永久占位
- 🔴 **BUG-MUSE-08 修复 — 多表同步**: Checklist 中的同一项如果也出现在 Countdown 表 / Go/No-Go 标准中 → 同步翻转/删除，不能只改一处

**3.5 Strategy 直接执行下游推送** — 如果 Strategy 角色直接执行了 BUILD 工作:
- 必须推送到对应项目的 build.md（状态/Blocker/技术栈）
- 双向检查: strategy.md 已完成但 build.md 未更新的指令 → 补推
- 🔴 **BUG-MUSE-08 修复 — git state section 同步**: 如果 Strategy 直接做了 commit，必须更新 build.md 的「📋 Git 状态」section（最新 commit hash + log 摘要 + Production deploy 版本）。Header 更新 ≠ 全文件更新

**3.6 源码同步检查** — 如果当前项目有上游 OSS 仓库，`diff` 本地 workflows vs 上游，有 diff 记入 memory

**3.7 🧠 Digital Twin 自动更新** — 每次 /bye 持续迭代 `USER.md` 的 `## 🧠 Digital Twin Profile`

> **v3.2.0 恢复 + 升级**: 原 v2.36.0 Step 3.8 因 SOP 膨胀在 v3.1.2 被删。
> 本次恢复为精简版 + 扩展到全角色全产品线。
> **Scope**: 不只是文风/口吻 — 覆盖 Strategy 决策模式、BUILD 质量标准、QA 验证偏好、Growth 品牌声音。
> 越用越准，像用户的行为模型一样进化。
> **跨产品共用**: 同一个 USER.md Twin 喂给 DYA/Prometheus/MUSE/Airachne 全部产品的 Growth。

**执行**:
1. **信号提取**: 回顾本轮对话，用户是否表现出新的（或修正已有的）:
   - 语言/文风偏好（词汇选择、格式习惯、禁用词）
   - 决策/思维模式（风险偏好、角色边界、反模式）
   - 沟通习惯（简洁度、核实要求、跨平台节奏）
   - 质量/工艺标准（"完成"的定义、全流程思维、竞品对标）
   - 品牌/产品直觉（命名、保密、Bundle 思维、美学）
2. **有新信号 → 更新**: 打开 `USER.md`，在对应 section（1-5）合并新特征 / 修正旧理解
3. **无新信号 → 静默跳过**（不写空更新）
4. **铁律**: 只追加用户**亲口表达或行为表现出**的特征，禁止 Agent 推测/编造

### Step 4: 写 memory

> 🚨 **路径规则**: 必须写入**项目根目录**的 `memory/YYYY-MM-DD.md`。
> 在 worktree 中使用绝对路径（通过 `git rev-parse --path-format=absolute --git-common-dir` 获取主仓库根）。
> **验证**: 写入后 `ls -la <project-root>/memory/YYYY-MM-DD.md` 确认文件在正确位置。

写入 `<project-root>/memory/YYYY-MM-DD.md`（追加模式）:

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

### Step 4.5: 同步 Obsidian Vault（可选增强层）

**检测**: 读取 `.muse/paths.md` 中 `OBSIDIAN_VAULT` 路径 → 不存在则静默跳过

**存在 → 执行**:

**4.5.1 写入/追加 `<vault>/daily/YYYY-MM-DD.md`**

从 Step 1 工作摘要提取，每个 Session 一个 section。如文件已存在则追加:
```markdown
# YYYY-MM-DD

## Session N (HH:MM-HH:MM) — [角色] [标题]
- **完成**: [完成项摘要，每项一行]
- **决策**: [[decisions/YYYY-MM-DD-描述]] — [简短理由]
- **下一步**: [关键下一步]
```

**4.5.2 写入 `<vault>/decisions/` 条目**（如本轮有新的重大决策）

扫描 Step 1「决策」列表。每条重大决策写一个文件:
- 文件名: `YYYY-MM-DD-简短描述.md`（kebab-case）
- 格式: Background / Options / Decision / Rationale / Risks / Execution Status

**4.5.3 写入 `<vault>/bugs/` 条目**（如本轮有新 Bug 根因分析）

仅当 Step 1 中有明确的 Bug 诊断+修复时才写:
- 文件名: `YYYY-MM-DD-BUG-ID.md`
- 格式: Symptoms / Root Cause / Fix / Impact / Lessons Learned

**4.5.4 更新 `<vault>/_index.md` 最近活动**

在「最近活动」section 的列表**顶部**追加一行（保持倒序）:
```markdown
- YYYY-MM-DD: [角色] — [一句话摘要] → [[daily/YYYY-MM-DD]]
```

**4.5.5 限制**: 最近活动列表保留最近 10 条，超出的移除末尾行。

### Step 5: 导出对话

**对话归档写入主角色对应产品的 `convo/`**。路由规则见 `.muse/paths.md` 或默认为项目根。

**5.1 解析主角色 → `$CONVO_ROOT`**

> 🚨 **BUG-MUSE-09 修复 (4/11)**: 多角色对话中 Agent 按"代码改动量"选主角色 → 导出到错误产品目录。
> **铁律: 主角色 = `/resume` 启动时指定的角色，不是"做了最多工作的角色"。**
> - Step 2 检测的"涉及角色"用于 Step 3 同步，但 Step 5 导出**只看启动角色**

默认: `$CONVO_ROOT` = 当前项目根目录。
如有 `.muse/paths.md` 中定义跨项目路由表，则按配置覆盖。

**5.2 检测工具 + 分流导出（N-way dispatch）**

```bash
# 检测当前 AI 工具
TOOL=$(bash scripts/adapters/detect_tool.sh)

case "$TOOL" in
  claude-code|openclaw)
    # JSONL → L1 markdown
    bash scripts/adapters/export_cc_session.sh "[标题]" --project-root "$CONVO_ROOT"
    ;;
  aider)
    # .aider.chat.history.md → L1 markdown
    bash scripts/adapters/export_aider_session.sh "[标题]" --project-root "$CONVO_ROOT"
    ;;
  cursor|windsurf|copilot|codex|gemini|antigravity|opencode|unknown)
    # 生成 L1 模板，用户手动粘贴
    bash scripts/adapters/export_manual.sh "[标题]" --project-root "$CONVO_ROOT" --tool "$TOOL"
    ;;
esac
```

> 适配器规范见 `docs/CONVO_SPEC.md`。所有输出统一到 `convo/YYMMDD/YYMMDD-NN-title.md` L1 格式。

**5.3 验证落地路径（强制，证据 > 断言）**

脚本返回成功后**必须** `ls -la "$CONVO_ROOT/convo/YYMMDD/"` 验证文件真的在预期位置，再告知用户。踩过的坑：worktree 相对路径 bug + NN 撞号 — 只信 stdout 会报假路径。

**5.4 标题生成**：从 Step 1 工作摘要提取 2-5 词短标题（kebab-case），例如 `cc-bridge-setup`、`s114-volcengine-migration`。

### Step 6: 告知用户

输出:
1. 一行摘要（角色 + 主要完成项）
2. SOP 合规 checklist（Step 1-5 每步 ✅/❌）
3. 导出建议路径
4. 如有源码 diff → 提醒下轮同步

---

## 教训索引

> 详细教训存储在 `MEMORIES.md` 和 Obsidian Vault `bugs/`。
> 以下仅列索引，供 Agent 遇到相关场景时查阅。

| ID | 教训 | 参考 |
|:--:|------|------|
| BUG-MEM-01 | /bye 不回写指令状态 → Step 3.2 grep 翻转 | MEMORIES.md |
| BUG-MUSE-02 | 混合角色对话只 sync 一个 → Step 2 多角色检测 | MEMORIES.md |
| BUG-MUSE-03 | Strategy 做 BUILD 工作 build.md 不知道 → Step 3.5 | MEMORIES.md |
| BUG-MUSE-04 | 硬编码% 写后僵死 → Step 3.4 Checklist 刷新 | MEMORIES.md |
| BUG-MUSE-05 | /resume 盲信数字 → resume.md Checklist 核查 | MEMORIES.md |
| BUG-MUSE-06 | /bye memory 写到 auto-memory 路径 → Step 4 强制绝对路径 + 验证 | MEMORIES.md |
| BUG-MUSE-07 | v3.1.2 SOP 精简误删 Digital Twin 自动更新 → Step 3.7 恢复 | MEMORIES.md |
| BUG-MUSE-08 | /bye sync 粒度不足：同一事实在 strategy.md 5 处冗余，Agent 只改 1-2 处 → Step 3.2 全文件一致性 grep + Step 3.4 已关闭项清理+多表同步 + Step 3.5 git state section 同步 | bye.md |
