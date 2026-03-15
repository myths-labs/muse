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

🚨 **防遗漏铁律 — 读三遍**:
> Agent 上下文退化时（长对话/多轮交互后），只能记住**最近 20% 的内容**。
> `/bye` 写的 memory 如果只覆盖最后几项工作 = **等于丢失了 80% 的工作记录**。
> 这是 MUSE SOP 最严重的 Bug：下次 `/resume` 读到残缺 memory → 以为工作没做过 → 重复劳动或错误决策。

**必须执行（不可省略）**:
1. **列出本轮所有 tool calls 类型和数量**（不需要逐条，概括即可）:
   - 代码编辑: N 次
   - 命令执行: N 次（部署/构建/etc）
   - 文件读取: N 次
   - 用户交互轮次: N 轮
2. **如果对话轮次 ≥ 10 或 tool calls ≥ 20**:
   - 🚨 **高遗漏风险** — 必须从对话**开头**逐段回顾，不能只看最近的部分
   - 用 `grep_search` 搜索本次 `.muse/` 文件的 `git diff` 或直接回顾对话开头的 tool calls
   - 确保每一段用户需求和完成的工作都被记录
3. **用户明确说过的事实 > Agent 推断**:
   - 如果用户说"我删了 xxx" → memory 记 "用户手动删除"，**不能**记 "auto-fix 会处理"
   - 如果用户说"这个不要了" → memory 记 "用户决定跳过"，**不能**记 "待完成"
4. 生成工作摘要（完成了什么 / 关键决策 / 变更的文件）
   - **短对话（≤5 轮）**: 3-5 行摘要即可
   - **长对话（≥10 轮）**: 按时间段或功能模块分组，确保每段工作都覆盖
- **不需要用户输入任何描述**

#### 🆕 语义压缩规则 (v2.14.0 — mem0-inspired)

> 问题: 传统摘要是逐条平铺罗列（10 项工作 = 10 行），长对话写出的 memory 又长又缺结构。
> 解法: **层次化语义压缩** — 先归类再压缩，而不是平铺。

**压缩方法**（Step 4 写 memory 时使用）：

1. **归类**: 将所有工作按「主线」分组（通常 1-3 条主线）
   ```
   ❌ 平铺: "修了A, 改了B, 加了C, 删了D, 测了E, 发了F..."
   ✅ 归类: "主线1: X功能 (A→B→C) | 主线2: Y发布 (D→E→F)"
   ```

2. **压缩比例**:
   | 对话长度 | 压缩目标 | 方法 |
   |---------|---------|------|
   | ≤5 轮 | 1:1 (不压缩) | 逐条列举 |
   | 6-15 轮 | 3:1 | 合并同类项，每条主线 1-2 行 |
   | ≥16 轮 | 5:1 | 只保留主线+关键决策+结果 |

3. **必保留项**（无论多压缩都不能丢）:
   - 版本号变更 (v2.12.0→v2.13.0)
   - 用户明确做的决策
   - 文件创建/删除
   - 外部操作 (commit/push/deploy/release)

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

### 3.5 🚨 角色文件待办更新（防止待办 stale）

> **根因**: sync 只写工作摘要/回传，但不更新角色文件的 `[ ]` 待办项 → 下次 `/resume` 看到的待办仍是旧状态。

**必须执行（所有角色都适用）**：
1. 回顾本轮完成的工作，与目标角色文件的「待办」/「下一步」section 对照
2. 将本轮**确认完成**的待办项从 `[ ]` 或 `[/]` 改为 `[x]`
3. 将本轮**开始但未完成**的待办项从 `[ ]` 改为 `[/]`
4. 如果本轮产生了**新的待办**，追加到角色文件的待办 section
5. **不要删除待办项**，只改状态标记（保留历史）

**示例**：
```diff
- - [ ] 修复登录 Bug
+ - [x] 修复登录 Bug ✅ (3/14)
- - [ ] 加速器申请准备
+ - [/] 加速器申请准备（已评估适配度）
```

**⚠️ 常见错误**（以下 = /bye 执行不完整）：
- ❌ 只写了工作摘要但没更新角色文件的 checkbox
- ❌ 本轮完成了 3 项工作但角色文件的 `[ ]` 全没变
- ✅ **正确做法**: 每项完成的工作都在角色文件中找到对应 `[ ]` 并翻转为 `[x]`

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

### 4.7 🆕 自动记忆捕获 (Auto Capture)

> Inspired by Supermemory Auto Capture + claude-mem automatic compression.
> 本轮新增 (v2.12.0 Batch 2) — 在 session 结束时自动提取可复用知识，无需手动 `/distill`。

**每次 /bye 都执行**（紧接 Step 4 memory 写入后）：

#### Why
`/distill` 是批量蒸馏（每周跑一次），但高价值知识在产生时就应捕获。
Auto Capture = **实时提取** — 每次 `/bye` 都把本轮产生的关键知识写入 `MEMORIES.md`，不等积累。

#### How

1. **从 Step 1 的工作摘要中提取**（不重新扫描对话）：
   - 🔍 筛选出属于以下 3 类的条目：
     | Type | Tag | Capture 条件 | Example |
     |------|-----|-------------|---------|
     | `[LESSON]` | 错误/教训/发现 | 犯了错并修复 / 发现了反直觉的规律 | "小红书对自推广型限流" |
     | `[DECISION]` | 重要决策 | 有明确的选择+理由+替代方案被否决 | "Show HN 暂缓 — T3 先进化" |
     | `[FACT]` | 关键数据 | 数值/基准线/benchmarks 首次获得 | "mem0 比 OpenAI Memory 省 90% token" |

   - ❌ **不要捕获**: 常规工作完成记录（这些已在 Step 4 memory 中）、临时性待办（这些在角色文件中）

2. **Dedup Check**（防重复）：
   - `grep` 检查 `MEMORIES.md` 是否已有相同/相似条目
   - 已有 → **NOOP**（跳过）或 **UPDATE**（合并新数据）
   - 没有 → **ADD**（追加到对应 section）

3. **写入 MEMORIES.md**：
   - 追加到对应主题 section（找最匹配的已有 section，或新建）
   - 格式：
     ```markdown
     - **[TAG] Description** (source: memory/YYYY-MM-DD.md, auto-captured) 
     ```
   - ⚠️ **Token 预算检查**：写入后 `wc -w MEMORIES.md`，超过 2250 words 则跳过本次 capture，在 Step 6 提醒用户先 `/distill` 压缩

4. **静默 vs 提醒**：
   - 捕获了 ≥1 条 → Step 6 输出中加 `📸 Auto-captured N entries to MEMORIES.md`
   - 捕获了 0 条（本轮无高价值知识）→ 静默跳过
   - Token 超预算 → Step 6 输出 `⚠️ MEMORIES.md 已满 (N/2250 words)，请先 /distill`

#### Guardrails
- **每次 /bye 最多捕获 5 条**（防止膨胀）
- **只捕获 LESSON/DECISION/FACT**（TODO 不捕获 — 已在角色文件中追踪）
- **捕获 ≠ 替代 /distill** — Auto Capture 是实时增量，`/distill` 是定期全量压缩+衰减检测
- **不修改 memory/ 文件** — Auto Capture 只读 Step 1 摘要 + 写 MEMORIES.md

### 4.8 🆕 Auto Profile (自动用户画像)

> Inspired by Supermemory Auto Profile — 自动从对话中提取用户偏好并丰富 `USER.md`。
> 本轮新增 (v2.14.0) — 零输入，纯观察。

**每次 /bye 都执行**（紧接 Auto Capture 后）：

#### Why
`USER.md` 通常只在 `/start` 或 `/settings` 时由用户手动填写。但用户的真实偏好藏在日常对话中（"我喜欢中文回复"、"别用 tailwind"、"commit message 用英文"）。Auto Profile 把这些隐性偏好显性化。

#### How

1. **从本轮对话中检测** 以下信号：

   | 信号类型 | 检测方法 | USER.md 字段 |
   |---------|---------|-------------|
   | **语言偏好** | 用户持续用中文/英文/混合交流 | `language` |
   | **代码风格** | 用户纠正过命名/格式/注释风格 | `code_style` |
   | **工作节奏** | 对话时间段、频率 | `work_hours` (新) |
   | **技术偏好** | 反复选择/拒绝某种技术方案 | `tech_preferences` (新) |
   | **沟通偏好** | "别太啰嗦"/"给我详细解释" | `verbosity` (新) |

2. **Dedup + 冲突检查**：
   - `grep` 检查 `USER.md` 是否已有该偏好
   - 已有且一致 → **跳过**
   - 已有但冲突 → **不修改，在 Step 6 提醒用户确认**
   - 没有 → **追加**

3. **写入 USER.md**：
   - 追加到合适的 section（找 `## Preferences` 或文件末尾）
   - 格式：
     ```markdown
     - **[field]**: value (auto-detected from conversation on YYYY-MM-DD)
     ```

4. **静默 vs 提醒**：
   - 检测到 ≥1 个新偏好 → Step 6 输出 `👤 Auto-profile: detected N new preferences → USER.md`
   - 检测到冲突 → Step 6 输出 `⚠️ Profile conflict: [field] current=X detected=Y — 请用 /settings 确认`
   - 无新发现 → 静默跳过

#### Guardrails
- **每次 /bye 最多写入 3 个偏好**（防止过拟合单次对话）
- **永不覆盖用户手动设置的值**（手动 > 自动检测）
- **只追加，不删除**（用户可通过 `/settings` 手动清理）
- **不读取对话内容**（只从 Step 1 摘要 + 观察到的交互模式推断）

### 5. 对话存档引导

> [!CAUTION]
> **此步骤不可省略。** 每次 `/bye` 必须输出建议 convo 文件名。跳过此步 = /bye 执行失败。
> 
> 🚨 **NEVER GUESS THE SEQUENCE NUMBER.** 你必须实际运行 `ls` 命令查看已有文件后才能生成文件名。
> 猜测 NN = /bye 执行失败。默认 -01- = /bye 执行失败（除非文件夹确实为空）。

提醒用户手动导出对话（Agent 无法自动完成导出）。

**⚠️ 严格规则 — 三步法（每步都不可跳过）**：

**Step 5a. 确定日期 YYMMDD**
- YYMMDD = **当前日期**（对话结束时的日期，不是对话开始时的日期）
- 使用系统提供的当前时间。例：当前是 2026-03-14 → `260314`

**Step 5b. 🚨 运行 ls 命令获取序号（必须执行，不可跳过）**
- **必须运行**以下命令（不可跳过、不可假设、不可猜测）：
  ```bash
  mkdir -p convo/YYMMDD && ls convo/YYMMDD/ 2>/dev/null || echo "FOLDER_NOT_EXIST"
  ```
- 从 `ls` 输出中找到最大的 NN 值：
  - 如有 `260314-04-xxx.md` → 最大 NN=04 → **新文件 NN=05**
  - 如有 `260314-01-xxx.md` 和 `260314-03-xxx.md` → 最大 NN=03 → **新文件 NN=04**
  - 如输出 `FOLDER_NOT_EXIST` 或文件夹为空 → **新文件 NN=01**
- ⚠️ **NN 必须用两位数补零**：01, 02, ..., 09, 10, 11...

**Step 5c. 组装文件名并输出**
- **描述**用英文下划线，简洁，不超过 5 个词
- 如果本轮是上下文快爆掉的紧急结束，加 `_CRASH` 后缀

**输出格式**：
```
📂 建议导出本次对话到:
   convo/YYMMDD/YYMMDD-NN-简短描述.md
```

**🔴 常见错误（以下任何一种 = /bye 执行失败）**：
- ❌ 没有运行 `ls` 就直接写 `-01-`（文件夹里已有 4 个文件）
- ❌ 日期用了昨天或对话开始时的日期
- ❌ 序号没有 +1（如文件夹里最大是 -04-，却写了 -04-）
- ✅ **正确做法**: 运行 `ls` → 发现最大 NN=04 → 新文件 NN=05

### 6. 告知用户
输出简洁的收尾确认：
```
✅ /bye 完成
- 同步: [列出同步了哪些 .muse/ 文件]
- 记忆: memory/YYYY-MM-DD.md 已更新
- 📸 Auto-capture: [N entries → MEMORIES.md / 无新知识 / ⚠️ 已满]
- 👤 Auto-profile: [N new preferences → USER.md / 无新发现 / ⚠️ 冲突]
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
