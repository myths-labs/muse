---
description: 结束对话的一键收尾指令。自动汇总工作、同步 .muse/ 角色文件、写短期记忆。零输入。
---

## 🚨 铁律 — 必须完整执行（不可违反）

> **每次 `/bye` 必须完整执行下方全部 6 步。**
> **NEVER skip any step. 不能偷懒给简短摘要就结束。**
> **如果你只输出了"再见"或几行摘要而没有执行 Step 1-6，你就违反了铁律。**

### 🚨 记忆系统声明 — 读三遍

> **当前项目使用 MUSE 角色文件系统 (`.muse/*.md`)，不是 trio-status-sop。**
>
> ✅ 正确的文件: `.muse/strategy.md`, `.muse/build.md`, `.muse/growth.md`, `.muse/qa.md` 等
> ❌ 严禁创建: `STATUS.md`, `STRATEGY_STATUS.md`, `MARKETING_STATUS.md`
>
> 如果你找不到预期的状态文件，**停下来确认**，不能自行创建新文件。

## 用法

```
/bye
```

**不需要任何参数。** Agent 自动从对话上下文提取本轮工作摘要。

---

## 执行步骤

// turbo-all

### 1. 自动提取本轮工作摘要
- 回顾本次对话所有 tool calls 和文件变更
- 生成 3-5 行工作摘要（完成了什么 / 关键决策 / 变更的文件）
- **不需要用户输入任何描述**

### 2. 判断身份和同步方向

⚠️ **必须使用下面的路由表确定同步目标文件，不能猜测。**

#### 项目-角色路由表

| 对话类型 | 同步目标文件 | sync 方向 |
|---------|-----------|-----------|
| DYA Strategy | `.muse/strategy.md` | sync strategy down（有新决策时） |
| DYA 开发/Build | `.muse/build.md` | sync build up |
| DYA 增长/Growth | `.muse/growth.md` | sync growth up |
| DYA QA | `.muse/qa.md` | sync qa broadcast* |
| DYA Ops | `.muse/ops.md` | sync ops up |
| DYA Fundraise | `.muse/fundraise.md` | sync fundraise up |
| DYA Research | `.muse/research.md` | 无需 sync |
| Prometheus 开发 | `Prometheus/.muse/build.md` | sync prometheus build up |
| Prometheus QA | `Prometheus/.muse/qa.md` | sync prometheus qa broadcast* |
| Prometheus 增长 | `Prometheus/.muse/growth.md` | sync prometheus growth up |
| MUSE 开发 | `MUSE/.muse/build.md` | sync muse build up |
| MUSE QA | `MUSE/.muse/qa.md` | sync muse qa broadcast* |
| MUSE 增长 | `MUSE/.muse/growth.md` | sync muse growth up |

\* broadcast = 写 QA 报告 + 通知 BUILD + 通知 STRATEGY

**身份判断方法**（按优先级）：
1. 对话中的 `/resume [xxx]` 指令 → 直接映射
2. 对话中操作过的 `.muse/` 文件 → 用文件名确定角色
3. 对话内容关键词（代码/Bug → build, 发帖/视频 → growth, 验证/AC → qa）

**Fallback**: 如果无法确定身份，列出本轮操作过的所有 `.muse/` 文件作为同步目标。

#### ⚠️ 重大事件强制回传 checklist
以下任何一项发生时，**无论 Agent 是否认为"只是内部事"，都必须 sync up 到 strategy**：
- Apple 审核被拒 / 通过 / 重新提交
- 版本发布（App Store 分发）
- 关键 Bug 修复（影响用户可见体验）
- Deck / 融资材料定稿或部署
- 新战略决策（即使是 build/growth 层面自行决定的快路径决策）
- D3/D7 数据节点到达

如果 checklist 中任何一项未被 sync，Agent 必须在 Step 3 补同步。

### 3. 执行同步
- 按 Step 2 的路由表和 checklist 执行 sync
- **Cross-check 三重校验**:
  - ① **跨文件一致性**：本轮 memory 条目 vs 对应 .muse/ 文件，确认重大事件已同步
  - ② **同文件内部一致性**：检查同一事项在角色文件不同位置（融资表/决策表/待办/指令队列）的状态是否矛盾
  - ③ **memory 追溯更正**：如本轮有更正旧信息（如日期延后、状态变更），也更新之前 memory 中的对应记录，避免下次 resume 读到过时快照
- 格式严格遵守 `/sync` workflow 的规范

### 4. 写短期记忆
更新 `memory/YYYY-MM-DD.md`（追加，不覆盖之前轮次的内容）：
```markdown
## [角色] (HH:MM)
- 完成: [要点]
- 决策: [如有]
- 下一步: [如有]
```

### 4.5 角色文件膨胀检查（静默）
**每次 /bye 都检查**，不需要用户触发：
1. 运行 `wc -l .muse/*.md`
2. **触发条件**：任何角色文件 > 800 行
3. **触发时**：在 Step 6 收尾确认中加入：
   ```
   ⚠️ .muse/[文件名] 已达 N 行（目标 ≤500），建议归档历史内容到 .muse/archive/
   ```
4. **不触发时**：静默跳过

### 4.6 Distill 自动检测（静默）
**每次 /bye 都检查**，不需要用户触发：

1. 扫描 `memory/` 下所有 `.md` 文件（排除 `TEMPLATE.md`、`CRASH_CONTEXT.md`、`archive/`）
2. 检查 `MEMORIES.md` 的最后更新时间：
   - 方法 A: `stat -f %Sm MEMORIES.md`（文件修改时间）
   - 方法 B: `grep -n "蒸馏\|distill\|Distill" MEMORIES.md | tail -1`（文件内日期标记）
3. **触发条件**（满足任一）：
   - memory/ 有 **≥ 7 天**的未蒸馏日志
   - 距上次 distill 已 **≥ 5 个日志文件**
   - memory/ 总文件数 **≥ 15** 且从未 distill 过
4. **触发时**：在 Step 6 的收尾确认中加入提醒：
   ```
   ⚠️ memory/ 积累了 N 天日志，建议下轮对话开始时执行 /distill
   ```
5. **不触发时**：静默跳过，不打扰用户

### 5. 对话存档引导

> [!CAUTION]
> **此步骤不可省略。** 每次 `/bye` 必须输出建议 convo 文件名。跳过此步 = /bye 执行失败。

提醒用户手动导出对话（Agent 无法自动完成导出）。

**⚠️ 严格规则（不可违反）**：

1. **YYMMDD = 当前日期**（对话结束时的日期，不是对话开始时的日期，不是示例日期）
   - 使用系统提供的当前时间。例：当前是 2026-03-13 → `260313`
2. **NN = 当天文件夹中最大序号 + 1**：
   - **先执行** `ls convo/YYMMDD/` 查看已有文件
   - 找到最大的 NN 值（如 `260313-02-xxx.md` 则最大 NN=02）→ 新文件 NN=03
   - 如果文件夹不存在或为空 → NN=01
   - ⚠️ **不能假设 NN**，必须实际检查
3. **描述**用英文下划线，简洁，不超过 5 个词
4. 如果本轮是上下文快爆掉的紧急结束，加 `_CRASH` 后缀

**输出格式**：
```
📂 建议导出本次对话到:
   convo/YYMMDD/YYMMDD-NN-简短描述.md
```

❌ **错误示例**: 3/13 的对话命名为 `260312-02-xxx.md`（日期错误用了昨天）
✅ **正确示例**: 3/13 的对话命名为 `260313-02-xxx.md`（使用当天日期）

### 6. 告知用户
输出简洁的收尾确认：
```
✅ /bye 完成
- 同步: [列出同步了哪些 .muse/ 文件]
- 记忆: memory/YYYY-MM-DD.md 已更新
- 导出: convo/YYMMDD/YYMMDD-NN-desc.md（请手动导出）
```

---

## 与其他指令的关系

| 指令 | 用途 | 需要用户输入？ |
|------|------|:---:|
| `/resume` | 开始对话 | ✅ 一句话说要做什么 |
| `/bye` | **结束对话** | **❌ 零输入** |
| `/sync all` | 手动全量同步 | 可选（加描述更精确） |
| `/ctx` | 上下文健康检查 | ❌ |
