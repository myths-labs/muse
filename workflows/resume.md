---
description: 新对话开始时恢复项目上下文的标准流程
---

## 🚨 第零铁律

**读哪个文件就只聊哪个文件的内容。** 绝不在开发对话里谈营销，也不在营销对话里谈代码。

## Boot 序列（MUSE 上下文组装 — 每次新对话按顺序执行）

```
① CLAUDE.md + MEMORIES.md  → 宪法 + 长期教训（自动注入）
② memory/今天.md + 昨天.md → 短期记忆（最近发生了什么）
②.3 🆕 Conversation Summaries 交叉验证 → 防 /bye 未执行导致的记忆黑洞
②.5 扫描 memory `➡️ 下一步` 中的 🟨 项 → 有未完成项则主动提醒（标注可信度）
③ 跨天任务? grep_search memory/ 搜索任务关键词 → 定位更早的相关记忆
④ USER.md                  → 用户偏好
⑤ 对应 .muse/ 角色文件     → 完整进度（按指令决定读哪个）
⑥ 🚨 strategy.md 指令拉取  → 非 strategy 角色自动 grep 活跃指令（→BUILD / →GROWTH 等）
   ⚠️ **跨项目铁律**: strategy.md **始终位于 `DYA/.muse/strategy.md`**，无论当前项目是 DYA/Prometheus/MUSE
   → 路径由 CLAUDE.md 中的跨项目配置指定
⑦ 项目部署事实表        → strategy.md 的 🌐 项目部署事实表（快查网址/域名/版本）
   ⚠️ 所有角色（含 Strategy 本身）恢复报告必须列出当前项目的活跃网址
```

> ③ 只在任务跨度 > 2 天时执行（≈ LCM lcm_grep 深度检索）

### DYA 项目

| 场景 | 指令 |
|------|------|
| 继续开发 | `/resume build` |
| 继续增长/营销 | `/resume growth` |
| 继续战略 | `/resume strategy` |
| **继续 QA 验证** | **`/resume qa`** |
| 继续运维/发布 | `/resume ops` |
| 继续研究 | `/resume research` |
| 继续融资执行 | `/resume fundraise` |
| 跨层参考 | `/resume strategy + build` |
| **上下文爆掉恢复** | **`/resume crash`** |

### Prometheus 项目

| 场景 | 指令 |
|------|------|
| 继续开发 | `/resume prometheus` |
| 继续增长/营销 | `/resume prometheus growth` |
| **继续 QA 验证** | **`/resume prometheus qa`** |

### MUSE 项目

| 场景 | 指令 |
|------|------|
| 继续开发 | `/resume muse` 或 `/resume muse build` |
| 继续增长/推广 | `/resume muse growth` |
| **继续 QA 验证** | **`/resume muse qa`** |

我会：
1. 读 `memory/YYYY-MM-DD.md`（今天+昨天）快速恢复上下文
2. 再读指定的 .muse/ 角色文件确认待办和完整进度
2.3 🆕 **Conversation Summaries 交叉验证**（防 /bye 未执行导致的记忆黑洞）：
   - 读取系统提供的 conversation summaries（最近 10 条）
   - 与 memory/ 文件交叉对比：每个 conversation summary 是否有对应的 memory session 记录？
   - **没有 memory 记录的对话** = 可能 /bye 未执行 = 潜在记忆黑洞
   - 如发现未记录的对话：
     - 从 conversation summary 的 title + objective 提取关键事实
     - 在恢复报告中标注「⚠️ 以下对话无 memory 记录（/bye 可能未执行）」
     - 列出对话标题和推断的关键完成事项
   - ⚠️ conversation summary 是**推断性信息**，精度低于 memory，仅用于填补空白
   - 如果某个 summary 提示「下一步」中的某项已完成 → 标注为 🟡 可能已完成
2.5 **扫描 memory 未完成项** → 搜索 memory 最近 2 天文件中的 **所有** 未完成项格式：
   - `🔲` 项
   - `- [ ]` 项
   - `➡️ 下一步` section 下的所有非 `[x]`/非 `✅` 项
   
   🚨 **可信度标注（RC-2 修复·防止已完成项被误报为待做）**：
   对每个「下一步」未完成项，标注来源可信度：
   - 🟢 **角色文件确认未完成** → high confidence，直接列入未完成项
   - 🟡 **仅 memory 记录为下一步，角色文件无对应项** → medium，可能已在后续对话完成
   - 🔴 **memory 记录为下一步 + conversation summary 显示有后续对话处理该主题** → 很可能已完成，需向用户确认
   恢复报告中 🟡/🔴 项用括号标注 `(⚠️ 可能已完成·需确认)` 而非直接列为待办

   🚨 **角色过滤（防混入）**：
   - **Step A**: 根据当前 `/resume [xxx]` 指令确定当前角色（如 build/growth/strategy/qa）和当前项目（DYA/Prometheus/MUSE）
   - **Step B**: 将未完成项按角色/项目分类：
     - ✅ **当前角色的项目内待办** → 放在恢复报告「📋 未完成项」中，直接融入建议
     - ⚠️ **其他角色/项目的待办** → 放在恢复报告单独的「⚠️ 其他角色/项目待提醒」区块，仅做提醒，**不混入当前角色的建议列表**
   - **分类方法**:
     - memory 条目有「角色:」或「> 角色:」标注 → 直接用
     - memory 的 section header 含项目名（如 "Prometheus QA"、"MUSE BUILD"）→ 用 header 判断
     - 关键词推断: 代码/Bug/commit → build | 发帖/视频/小红书 → growth | PMF/融资/加速器 → strategy | AC/PASS/FAIL → qa
   - **输出格式示例**:
     ```
     📋 未完成项（Strategy 范围）:
     - 🔲 Alliance DAO 申请 (3/25 截止)
     
     ⚠️ 其他角色/项目待提醒（非本轮范围，仅供知悉）:
     - 🔲 [BUILD] resume.md 角色过滤修复
     - 🔲 [MUSE/GROWTH] S033 执行
     ```
2.7 **角色文件膨胀检查**：`wc -l` 目标 .muse/ 文件，**>800 行 → 先执行归档再开始工作**（移动已完成工作记录/已传递指令到 `.muse/archive/`，目标 ≤500 行）
3. **🚨 自动拉取战略指令（所有非 strategy 角色必须执行）**：
   - `grep_search` 扫描 strategy.md（路径从 CLAUDE.md 跨项目配置获取） 中的「📡 战略指令队列 → 活跃指令」
   - **⚠️ 精确匹配规则**（防止跨项目误拉取）：
     - `/resume build` → 搜 `→DYA/BUILD` 或 `→BUILD`（不带任何项目前缀的）
     - `/resume growth` → 搜 `→DYA/GROWTH` 或 `→GROWTH`（不带任何项目前缀的）
     - **必须排除**: `→MUSE/GROWTH`、`→PROMETHEUS/GROWTH` 等其他项目前缀的指令
     - 判断方法: 如果 `→` 前面有 `/`（如 `→MUSE/GROWTH`），检查项目名是否匹配当前对话的项目
   - ⚠️ **跨项目搜索路径铁律**:
     - **所有项目**（DYA/Prometheus/MUSE）的指令拉取都搜索 **同一个文件**: `DYA/.muse/strategy.md`
     - 路径由 CLAUDE.md 跨项目配置指定
     - ❌ **禁止**搜索项目本地的 strategy.md（如 `MUSE/.muse/strategy.md` 或 `Prometheus/.muse/strategy.md`）
     - 原因: DYA strategy.md 是全局战略中枢，所有项目的指令都从这里发出
   - 🚨 **✅/🟡 过滤规则（必读·防止漏拉取）**:
     - **🟡 = 待传递**（还没被目标角色的 /resume 拉取过）→ **必须拉取**
     - **✅ = 已确认接收**（目标角色的 /resume 已拉取并写入角色文件）→ **跳过**
     - ⚠️ **只有执行 `/resume` 的目标角色才能标记 ✅** — Strategy 对话创建指令时**必须用 🟡**
     - ❌ **常见错误**: Strategy 对话创建指令时就标了 ✅ → 目标角色永远拉取不到
   - **拉取后操作**:
     - 找到 🟡 指令 → **在恢复报告中高亮显示「📡 新战略指令」**，并写入对应角色文件的「📡 已接收战略指令」区块
     - 回到 strategy.md 将该指令的 🟡 标记改为「✅ 已传递」
     - 没找到 🟡 指令 → 跳过（静默）
   - ⚡ **Prometheus 角色同理**：`/resume prometheus` → 只搜 `→PROMETHEUS/BUILD`（不搜裸 `→BUILD`）
   - ⚡ **MUSE 角色同理**：`/resume muse growth` → 只搜 `→MUSE/GROWTH`
4. **如果是 `/resume build`：双重检查 QA 通知**
   - ① 检查 `.muse/qa.md` 有没有未处理的 ❌ FAIL → 有则先修复
   - ② 🚨 **检查 build.md 自身** 中的 QA→BUILD 通知（`grep_search build.md "待 BUILD 处理"`）
     - 找到 → 恢复报告中高亮 `🚨 QA 有新通知待处理`，列出通知摘要
     - 未找到 → 静默跳过
   - 两个检查**都做**，不能只查一个
4.5 **如果是 `/resume [project] qa`：自动读取 QA 指令来源**
   - 用户会在指令中说明 AC 来源（如 "执行 S028 QA"）
   - 如没说明 → 检查 qa.md「最近 QA 结果」是否有待复验的 FAIL 项
   - 输出恢复报告时包含：上次 QA 状态 + 有无待执行的 QA 指令
4.6 🚨 **如果是 `/resume [project] qa`：检查 BUILD 修复通知**
   - `grep_search qa.md "BUILD 声称已修复"` → 有未复验的修复通知 → 恢复报告高亮 `⚡ BUILD 有 N 项修复待复验`
   - `grep_search build.md "BUILD→QA 指派"` → 有新的 QA 指派 → 恢复报告高亮 `📡 BUILD 新增 QA 指派 S0XX`
   - 两个都查，确保不遗漏
4.7 🚨 **防 Phantom Features 检查**（QA 验证前必做）
   - QA 验证任何 BUILD 声称 `[x]` 完成的功能前 → 先 `grep_search` 代码库确认关键代码文件/函数存在
   - 如果 grep = 0 results → **直接 FAIL**，不需要进浏览器/curl 验证
   - 在 QA Report 中标注「🔴 P0: 代码不存在（grep 验证失败）」
5. **如果是 `/resume strategy`：检查 memory/ 中是否有未同步到 strategy.md 的重大事件**（grep 关键词：被拒/通过/审核/定稿/部署/融资/resubmit/rejected/approved/MUSE/开源/repo/安全/security/泄露/轮换/filter-branch/Skill/instinct/预装/发布/release/宪法/CLAUDE\.md/推荐人/已发送）→ 有则提醒用户需要 sync
   🆕 **同时检查 conversation summaries**：memory 之外，也用 ②.3 中识别出的"无 memory 对话"交叉验证——这些对话的 summary 中是否含有 strategy 相关的重大事件（融资/提交/部署/决策等）？如有 → 也提醒用户需要 sync
5.1 **冲突解决**：memory 和角色文件数据冲突时，**以角色文件为准**（memory 是写入时的快照，角色文件持续更新）。恢复报告只引用角色文件中的数据，memory 仅用于发现遗漏
5.2 **内部一致性校验**：输出恢复报告前，交叉检查角色文件内的同一事实是否在多处一致（如融资表/决策表/待办/指令队列中同一事项的状态是否矛盾）
5.3 **项目部署事实表校验**（全角色必做）：扫描 `🌐 项目部署事实表`，交叉验证：
   - 有无新上线/新部署未更新到事实表（检查 memory 中的 "部署/上线/deploy/发布" 关键词）
   - 事实表中的版本号是否与角色文件一致
   - **恢复报告必须包含** `🌐 项目活跃部署` section，列出当前项目的 URL + 状态
6. 只推荐该文件职责范围内的下一步行动
7. 按需读取相关代码/文档开始工作

**文件路径约定**：
- `/resume gm` → `DYA/.muse/gm.md`（项目 GM · v2.0）
- `/resume build` → `DYA/.muse/build.md`（+ 检查 `qa.md` FAIL）
- `/resume qa` → `DYA/.muse/qa.md`（QA 验证 · 独立于 build）
- `/resume growth` → `DYA/.muse/growth.md`
- `/resume strategy` → `DYA/.muse/strategy.md`
- `/resume ops` → `DYA/.muse/ops.md`
- `/resume research` → `DYA/.muse/research.md`
- `/resume fundraise` → `DYA/.muse/fundraise.md`
- `/resume prometheus gm` → `Prometheus/.muse/gm.md`（Prometheus GM · v2.0）
- `/resume prometheus` → `Prometheus/.muse/build.md` + `Prometheus/PRD.md`
- `/resume prometheus qa` → `Prometheus/.muse/qa.md`（QA 验证）
- `/resume prometheus growth` → `Prometheus/.muse/growth.md`
- `/resume muse` → `MUSE/.muse/build.md`（MUSE 开发）
- `/resume muse build` → `MUSE/.muse/build.md`
- `/resume muse growth` → `MUSE/.muse/growth.md`（MUSE 推广）
- `/resume muse qa` → `MUSE/.muse/qa.md`（MUSE QA）

**向后兼容**（旧指令自动映射）：
- `/resume status` → `/resume build`
- `/resume marketing` → `/resume growth`

### 上下文爆掉恢复

| 场景 | 指令 |
|------|------|
| 上下文爆掉或紧急中断需恢复 | `/resume crash` |

**`/resume crash` 流程：**
1. 检查 `memory/CRASH_CONTEXT.md` 是否存在
   - **存在** → 读取（这是 🔴 时自动预存的快照）→ 恢复后删除该文件
2. 如不存在，扫描 `convo/` 下最新的 `_CRASH` 文件（按修改时间排序）
   - **找到** → 读取最后 30% 内容（通常包含最近的讨论和决策）
   - 提取：当前任务、未完成事项、关键决策、用户最后的问题
3. 如都没找到 → 用户手动指定文件路径
4. 执行标准 Boot 序列（memory/ + USER.md + .muse/ 角色文件）
5. 输出恢复报告：上轮做了什么、未完成什么、建议下一步

---

## 结束对话时

```
/bye
```

零输入。自动汇总本轮工作 → 同步 .muse/ 角色文件 → 写 `memory/YYYY-MM-DD.md` → 建议导出到 `convo/`。详见 `bye.md`。

## 跨项目同步

| 方向 | 指令 | 说明 |
|------|------|------|
| Prometheus → DYA 战略 | `同步 Prometheus 进度` | 读 Prometheus/.muse/build.md 回传到 STRATEGY |
| DYA 战略 → Prometheus | `下发 Prometheus 指令` | 写 S021 指令，Prometheus 对话自动拉取 |
| DYA 角色文件互同步 | `/sync all` | 见 sync.md workflow |

## 角色文件分工

| 文件 | 内容 | 更新时机 |
|------|------|---------| 
| `.muse/strategy.md` | 商业战略、PMF、融资、增长、**Prometheus 战略 (S021)** | 战略讨论后 |
| `.muse/build.md` | DYA 代码开发、Bug修复 | 代码/Bug后 |
| `.muse/growth.md` | 广告创意、品牌文案、社交媒体、视频 | 营销讨论后 |
| `.muse/qa.md` | QA 验证规范、AC 流程、反弄虚作假 | QA 验证后 |
| `.muse/ops.md` | App Store 提审、CI/CD、版本号、发布 | 提审/发布后 |
| `.muse/research.md` | 竞品分析、用户调研、市场数据、OXYZ | 研究讨论后 |
| `.muse/fundraise.md` | Deck内容、申请文案、Pitch脚本、材料自检 | 融资执行后 |
| `Prometheus/.muse/build.md` | Prometheus SDK/Marketplace/Plugin | Prometheus 开发后 |
| `MUSE/.muse/build.md` | MUSE 开源项目开发 | MUSE 开发后 |
| `MUSE/.muse/growth.md` | MUSE 开源推广、社区、竞品 | MUSE 增长讨论后 |
| `memory/YYYY-MM-DD.md` | 每日快照（轻量，跨所有项目） | **每轮对话结束时** |

## 什么时候该开新对话？

- ✅ 完成了一个完整功能/任务
- ✅ **切换了工作主题**（最重要的信号）
- ✅ 感觉回复变慢或质量下降
- ✅ 大约 15-20 轮交互后
- ✅ `/ctx` 检查显示 ≥ 80%

## 关键原则

1. **MUSE 四角色制** — strategy/build/growth/qa 各自独立，互不干扰
2. **读哪个聊哪个** — 绝不跨文件混聊
3. **短对话、高密度** — 每次对话聚焦一个主题
4. **结束即存档** — 更新 .muse/ 角色文件 + 写入 memory/
5. **跨项目路径明确** — DYA / Prometheus / MUSE 各有独立的 .muse/ 目录，不能混读
