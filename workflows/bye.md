---
description: 结束对话的一键收尾指令。自动汇总工作、同步 .muse/ 角色文件、写短期记忆。零输入。
---

## 🚨 铁律 — 必须完整执行（不可违反）

> **每次 `/bye` 必须完整执行下方全部 6 步。**
> **NEVER skip any step. 不能偷懒给简短摘要就结束。**
> **如果你只输出了"再见"或几行摘要而没有执行 Step 1-6，你就违反了铁律。**
> 
> ⚠️ **跨项目适用**: 此 SOP 适用于 **所有项目**（DYA / Prometheus / MUSE）。
> Prometheus 和 MUSE 对话的 `/bye` **同样必须执行全部 6 步**，不能因为"不是 DYA"就省略。
>
> 🔴 **反幻觉声明**: /bye 不涉及 L0 操作。L0 是 `/resume` 的概念。
> 如果你认为 "写了 memory + L0 就完成了"，你错了 — 你跳过了 Step 2/3/3.5/5/6。
> /bye 的 6 步是: 摘要→身份→同步→记忆→导出→告知，**缺一不可**。

### 🚨 记忆系统声明 — 读三遍

> **当前项目使用 MUSE 角色文件系统 (`.muse/*.md`)，不是 trio-status-sop。**
>
> ✅ 正确的文件: `.muse/strategy.md`, `.muse/build.md`, `.muse/growth.md`, `.muse/qa.md` 等
> ❌ 严禁创建: `STATUS.md`, `STRATEGY_STATUS.md`, `MARKETING_STATUS.md`
>
> 如果你找不到预期的状态文件，**停下来确认**，不能自行创建新文件。

### 🚨 跨项目 strategy.md 路径

> **strategy.md 始终位于 `DYA/.muse/strategy.md`**，无论当前项目是 DYA/Prometheus/MUSE。
> 绝对路径: `/Users/jj/Desktop/DYA/.muse/strategy.md`
> Step 3 的 sync 操作中，所有项目的回传都写入这个文件。

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
5. **上下文恢复三问**（完成工作清单后必须自问）:
   - "下一轮 Agent 接手这个任务时，光看 memory + 角色文件，能否 100% 恢复到当前理解水平？"
   - "有没有本轮讨论的方案被否决但未记录？下轮 Agent 可能会重新提出同样的错误方案"
   - "有没有用户纠正过我的理解？这个纠正会影响后续所有决策吗？"
   如果任何一问的答案是 "不能/有"，则必须在 memory 中补充 📡 跨对话上下文条目。

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
| Prometheus 开发 | `.muse/build.md`（Prometheus 数据已合并回 DYA build.md） | sync prometheus build up |
| Prometheus QA | `.muse/qa.md`（同上） | sync prometheus qa broadcast* |
| Prometheus 增长 | `.muse/growth.md`（同上） | sync prometheus growth up |
| MUSE 开发 | **`/Users/jj/Desktop/MUSE/.muse/build.md`** + **strategy.md** | sync muse build up |
| MUSE QA | **`/Users/jj/Desktop/MUSE/.muse/qa.md`** | sync muse qa broadcast* |
| MUSE 增长 | **`/Users/jj/Desktop/MUSE/.muse/growth.md`** | sync muse growth up |

> 🚨 **sync up 必须回传 strategy 规则**:
> **任何** `sync [project] [role] up` 操作，如果涉及重大事件（版本发布、里程碑、架构变更），
> **必须同时**回传到 `DYA/.muse/strategy.md`。路由表中的「同步目标文件」是主文件，
> strategy.md 是**所有 up 操作的隐含目标**。不是只有 checklist 中的事件才需要回传——
> 任何 strategy 对话恢复时需要知道的进展都应该回传。

> ⚠️ **MUSE 路径铁律**: MUSE 的 `.muse/` 文件在 `/Users/jj/Desktop/MUSE/.muse/`，不在 DYA 目录下。
> Prometheus 已无独立 `.muse/` 目录，数据合并回 DYA 的 `.muse/build.md`。

\* broadcast = 写 QA 报告 + 通知 BUILD + 通知 STRATEGY

**身份判断方法**（按优先级）：
1. 对话中的 `/resume [xxx]` 指令 → 直接映射
2. 对话中操作过的 `.muse/` 文件 → 用文件名确定角色
3. 对话内容关键词（代码/Bug → build, 发帖/视频 → growth, 验证/AC → qa）

**Fallback**: 如果无法确定身份，列出本轮操作过的所有 `.muse/` 文件作为同步目标。

#### ⚠️ 重大事件强制回传 checklist
以下任何一项发生时，**无论 Agent 是否认为"只是内部事"，都必须 sync up 到 strategy**：
- Apple 审核被拒 / 通过 / 重新提交
- 版本发布 — **不只是 App Store**，包括 GitHub Release / npm publish / 开源发布
- 关键 Bug 修复（影响用户可见体验）
- Deck / 融资材料定稿或部署
- 新战略决策（即使是 build/growth 层面自行决定的快路径决策）
- D3/D7 数据节点到达
- **BUILD 修复了 QA FAIL 项** → 必须写回 qa.md（`/sync build to qa`）
- 🆕 **安全事件/审计** — git 历史清理、Key 轮换、泄露修复、安全红线写入
- 🆕 **新 Skill 或工具创建** — 扩展了 agent 能力边界的新 Skill/workflow
- 🆕 **产品洞察/改进方向** — 有战略价值的 Gap 发现或架构改进思路
- 🆕 **跨项目基础设施变更** — CLAUDE.md 宪法更新、共享配置变更
- 🆕 **已发送的外部沟通** — 投资人/推荐人/合作方材料已发出（更新待办状态）

如果 checklist 中任何一项未被 sync，Agent 必须在 Step 3 补同步。

### 3. 执行同步
- 按 Step 2 的路由表和 checklist 执行 sync
- 🔴 **先执行 Step 3.3 指令状态反向回写**，再执行下方主动 Diff
- 🆕 **主动 Diff（防遗漏·必须执行）**:
  - 写完 memory 后（或准备写 memory 时），**逐条对比**本轮 memory 新增条目与目标角色文件
  - 每条 memory 条目必须分类为:
    - ✅ **已在角色文件中** → 跳过
    - 📝 **需要同步** → 执行 sync
    - ⏭️ **不需要同步** → 附理由（如"纯执行细节，无战略价值"）
  - ❌ **不允许**整体判断 "无需同步" — 必须逐条过
- **Cross-check 四重校验**:
  - ① **跨文件一致性**：本轮 memory 条目 vs 对应 .muse/ 文件，确认重大事件已同步
  - ② **同文件内部一致性**：检查同一事项在角色文件不同位置（融资表/决策表/待办/指令队列）的状态是否矛盾
  - ③ **memory 追溯更正**：如本轮有更正旧信息（如日期延后、状态变更），也更新之前 memory 中的对应记录，避免下次 resume 读到过时快照
  - ④ 🚨 **BUILD→QA 反向同步检查**（仅 BUILD 角色）：
    - 检查本轮是否修复了任何 QA FAIL 项
    - 是 → 必须执行 `/sync [project] build to qa`，在 qa.md 对应 FAIL 报告下方追加「⚡ BUILD 声称已修复」
    - 否 → 静默跳过
- 格式严格遵守 `/sync` workflow 的规范

### 3.3 🔴 指令状态反向回写（强制 — 不可跳过）

> **根因**: BUILD/GROWTH/QA 完成 strategy 指令后只更新自己的角色文件，
> 但不回 strategy.md 翻转指令状态 → /resume strategy 下轮仍看到"待回传/待执行"。
> 这是 4/3 S097/S094/BUG-12 三重记忆丢失的直接根因。

**触发条件**: 本轮完成了任何来自 strategy.md 的指令（S0XX）或其他重大任务

**必须执行**:
1. `grep -n "🟡\|待回传\|待执行\|BUILD 待\|BUILD 必须" /Users/jj/Desktop/DYA/.muse/strategy.md`
2. 对每个匹配项，检查本轮是否已完成该指令
3. 已完成 → **直接在 strategy.md 中**将状态改为 ✅ + 追加完成摘要和日期
4. 未完成但有进展 → 更新进展描述
5. 无关 → 跳过

**示例**:
```
# 本轮完成 S097 回传
# strategy.md 原文:
📡 S097→BUILD: 🟡 待回传 Launch 时间表
# 改为:
📡 S097→BUILD: ✅ **已回传** (4/3 17:50) — 4/8 最早可 Launch
```

**覆盖范围**: 不只是指令队列 — strategy.md 的**待办、状态快照、Launch Blocker 列表**中
引用的同一事项也必须一并更新。用 `grep` 搜索指令编号确保**全文一致**。

🔴 **铁律**:
- 如果 `grep` 搜到 🟡/待回传匹配项但你判断"不需要更新" → 必须在 memory 中说明原因
- 静默跳过 = /bye 执行失败
- 此步在**所有角色**的 /bye 中执行（BUILD/GROWTH/QA/OPS），不仅限于 Strategy

### 3.4 🔴 MUSE 源码仓库同步检查（v3.0 新增 — 防版本断裂）

> **根因**: v2.37→v3.0 期间，skill/workflow 升级做在 DYA 安装副本中，未同步回 MUSE 源码仓库 (`/Users/jj/Desktop/MUSE/`)。下轮 /resume 读到的 MUSE git tag 与实际改动不一致 → 版本号虚报 → 灾难级 bug。

**触发条件**: 本轮改动涉及以下任何文件:
- `DYA/.agent/skills/*/SKILL.md`
- `DYA/.agent/workflows/*.md`
- `DYA/CLAUDE.md`

**必须执行**:
```bash
# 1. 检查哪些 skill 在 DYA 和 MUSE 之间有 diff
for skill in $(ls /Users/jj/Desktop/DYA/.agent/skills/); do
  muse_file=$(find /Users/jj/Desktop/MUSE/skills/ -path "*/$skill/SKILL.md" 2>/dev/null | head -1)
  dya_file="/Users/jj/Desktop/DYA/.agent/skills/$skill/SKILL.md"
  if [ -n "$muse_file" ] && [ -f "$dya_file" ]; then
    if ! diff -q "$muse_file" "$dya_file" > /dev/null 2>&1; then
      echo "🔴 DIFF: $skill (MUSE ≠ DYA)"
    fi
  fi
done

# 2. 检查 workflow diff
for wf in bye.md resume.md sync.md; do
  if ! diff -q "/Users/jj/Desktop/MUSE/workflows/$wf" "/Users/jj/Desktop/DYA/.agent/workflows/$wf" > /dev/null 2>&1; then
    echo "🔴 DIFF: workflows/$wf (MUSE ≠ DYA)"
  fi
done
```

**处理**:
- 有 diff → 在 memory 中标注 `🔴 MUSE 源码未同步: [文件列表]`，提醒下轮执行 `/release`
- 无 diff → 静默跳过

**🔴 铁律**: 此步不可跳过。上轮 /bye 跳过此步导致 4 个版本断裂。

### 3.5 🚨 角色文件待办更新（防止待办 stale）

> **根因**: 之前 sync 只写工作摘要/回传，但不更新角色文件的 `[ ]` 待办项 → 下次 `/resume` 看到的待办仍是旧状态。

**必须执行（所有角色都适用）**：
1. 回顾本轮完成的工作，与目标角色文件的「待办」/「下一步」section 对照
2. 将本轮**确认完成**的待办项从 `[ ]` 或 `[/]` 改为 `[x]`
3. 将本轮**开始但未完成**的待办项从 `[ ]` 改为 `[/]`
4. 如果本轮产生了**新的待办**，追加到角色文件的待办 section
5. **不要删除待办项**，只改状态标记（保留历史）

**规则**: `[ ]`→`[x]`(完成) 或 `[ ]`→`[/]`(进行中)。不删除待办项。
❌ 只写摘要不更新 checkbox = 执行失败 | ✅ 每项完成的工作在角色文件翻转 `[x]`

### 3.7 🚀 社交发帖（Airachne 网络）

> **必须在 Step 4 (写 memory) 之前执行。** 发帖结果需要被 memory 记录，放在 memory 之后 = 信息缺失。

1. 问用户："要顺便把今日研发进度去 AI 味压缩成一条极客推文发到 X 吗？(Y/N)"
2. 如果 Y → 生成推文 → 用户确认 → 发布（或用户手动发）→ 记录到 Step 4 memory 中
3. 如果 N → 跳过，不记录

**用户偏好（已确认）**：
- ✅ **只发 X**，不发 LinkedIn（LinkedIn 留给重大里程碑，不做日常流水线）
- 🚫 **禁止暴露产品属性**：不能让人猜到是 Avatar SDK / Avatar Marketplace。用抽象技术描述替代
- 🚫 **去 AI 味铁律**：
  - 禁止 em dash (—)，用句号或逗号替代
  - 禁止全小写，正常英文大小写
  - 禁止 "delve", "leverage", "tapestry", "landscape" 等 AI 高频词
  - 语气要像真人开发者随口说的，不是 PR 稿
- 发完后把推文内容 + URL 写入 memory

**发帖方式（已确认）**：
- 🔴 **禁止使用 browser_subagent 的沙盒浏览器**。那个浏览器没有登录任何账号，发不了。
- ✅ **X**: 用 `open` 命令打开用户主 Chrome（已登录 X），直接在已登录状态下操作
- ✅ **LinkedIn**: 后台 API 发帖，不需要登录
- 如果主 Chrome 方式失败 → 告知用户手动发，给出复制粘贴内容

### 3.8 🧠 认知与人格镜像同步 (Digital Twin Profiling)

> **对齐 OpenClaw 生态的记忆与成长逻辑：越用越懂用户。**
> 此步骤用于收集用户的思维方式、表达习惯、决策偏好，并在每次 /bye 时持续修正用户的数字化身（Digital Twin），使 MUSE 和 Airachne 生成的内容越来越贴合用户的「Founder's voice」。

**静默执行（必须包含）：**
1. **反思提取**：回顾本轮对话中，用户表现出了哪些独特的：
   - 决策逻辑（如：偏好极致极客风，反感假大空）
   - 词汇/口头禅（如：特定的英文混用习惯，特定的行业黑话）
   - 审美/语气要求（如：要求去 AI 破折号，要求短句，避免华丽辞藻）
2. **状态更新**：打开 `/Users/jj/Desktop/DYA/USER.md`，找到 `## 🧠 认知与人格镜像 (Digital Twin Profile)` 模块：
   - 将新发现的特征合并进去，修正不准确的旧理解。
   - 像刻画游戏 NPC 或 OpenClaw Agent 行为树一样，具象化这些属性。
3. 如果本轮没有明显的新人格特征特征流露，可静默跳过写入。

### 4. 写短期记忆 (v3.0 升级)

#### 4.0 写入前过滤（v3.0 禁存列表）
> 以下信息**不存入 memory**，即使用户要求（问"什么是出乎意料的？"那部分才存）：
> - ❌ 代码模式/架构/文件路径（可从代码推导）
> - ❌ Git 历史/谁改了什么（git log 是权威）
> - ❌ Debug 解决方案（fix 在代码里）
> - ❌ CLAUDE.md 已有的内容 | ❌ PR 列表/活动摘要

更新 `memory/YYYY-MM-DD.md`（追加，不覆盖之前轮次的内容）：
```markdown
## [角色] Session [N] (HH:MM-HH:MM)
- ✅ 上轮遗留: [完成的上一轮"下一步"任务]（如有）
- 完成: [要点]
- 决策: [决策内容 + 为什么]
  - type: project | Why: [动机] | How to apply: [对后续工作的影响]
- ❌ 否决: [讨论过但否决的方案 + 原因]（如有）
- 💬 用户反馈（feedback 类·记正也记反）:
  - 纠正: "[用户纠正的原话]" → Rule: [规则] | Why: [原因] | How to apply: [怎么用]
  - 确认: "[用户确认的好做法]" → Rule: [继续做] | Why: [为什么好] | How to apply: [适用场景]
- 🔗 关键 URL/文件: [本轮新产生或涉及的网址、文件路径]（如有）
- 📡 跨对话上下文: [下一轮 Agent 恢复工作必须知道的架构决策/技术选型/讨论结论]（如有）
- ➡️ 下一步: [具体可执行项]（⚠️ 所有日期用绝对日期如 2026-04-03，不用"周四"）
```

> 🚨 **上轮遗留回写规则（RC-2 修复）**:
> 读取当天 memory 文件中前几个 Session 的「➡️ 下一步」条目，如果本轮完成了其中任何一项:
> 1. 在本轮 memory 的第一行用 `✅ 上轮遗留: [任务名]` 明确标注
> 2. **不需要**回去修改旧 Session 的内容（避免并发冲突）
> 3. 如果 memory 文件中无前置 Session（本轮是当天第一个），跳过此步

> ⚠️ **「如有」≠「可省略」**：如果本轮有否决/纠正/URL 但你没写 → 等于你制造了记忆黑洞。
> 🔴 **最常见遗漏**: 用户纠正了 Agent 的理解但 Agent 没记录 → 下轮 Agent 重犯同样错误。

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

### 6. 告知用户（强制合规格式）

> ⚠️ **必须使用以下完整格式输出。缺少任何一行 = /bye 执行失败。**
> 此格式适用于 **所有项目、所有角色**（DYA/Prometheus/MUSE × Strategy/Build/Growth/QA）。

```
✅ /bye 完成 — [项目名] [角色名]

📋 SOP 合规检查:
- [x] Step 1: 工作摘要已提取
- [x] Step 2: 身份=[角色], 同步目标=[文件名]
- [x] Step 3: 同步已执行 → [列出同步了哪些 .muse/ 文件]
  - [x] 重大事件 checklist 已检查
  - [x] Cross-check 校验已执行
- [x] Step 3.7: 社交发帖=[已发X/已跳过]
- [x] Step 3.8: 认知镜像更新=[已更新 USER.md/无新特征]
- [x] Step 4: memory/YYYY-MM-DD.md 已更新
- [x] Step 4.5: 角色文件膨胀=[N行/无需归档]
- [x] Step 4.6: Distill=[无需/建议执行]
- [x] Step 5: 导出 → convo/YYMMDD/YYMMDD-NN-desc.md
```

---

## 与其他指令的关系

| 指令 | 用途 | 需要用户输入？ |
|------|------|:---:|
| `/resume` | 开始对话 | ✅ 一句话说要做什么 |
| `/bye` | **结束对话** | **❌ 零输入** |
| `/sync all` | 手动全量同步 | 可选（加描述更精确） |
| `/ctx` | 上下文健康检查 | ❌ |
