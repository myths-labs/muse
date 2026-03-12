---
description: 新对话开始时恢复项目上下文的标准流程
---

## 🚨 第零铁律

**读哪个文件就只聊哪个文件的内容。** 绝不在开发对话里谈营销，也不在营销对话里谈代码。

## Boot 序列（MUSE 上下文组装 — 每次新对话按顺序执行）

```
① CLAUDE.md + MEMORIES.md  → 宪法 + 长期教训（自动注入）
② memory/今天.md + 昨天.md → 短期记忆（最近发生了什么）
②.5 扫描 memory `➡️ 下一步` 中的 🔲 项 → 有未完成项则主动提醒
③ 跨天任务? grep_search memory/ 搜索任务关键词 → 定位更早的相关记忆
④ USER.md                  → 用户偏好
⑤ 对应 .muse/ 角色文件     → 完整进度（按指令决定读哪个）
⑥ 🚨 strategy.md 指令拉取  → 非 strategy 角色自动 grep 活跃指令（→BUILD / →GROWTH 等）
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

我会：
1. 读 `memory/YYYY-MM-DD.md`（今天+昨天）快速恢复上下文
2. 再读指定的 .muse/ 角色文件确认待办和完整进度
2.5 **扫描 memory 未完成项** → 搜索 memory 最近 2 天文件中的 **所有** 未完成项格式：
   - `🔲` 项
   - `- [ ]` 项
   - `➡️ 下一步` section 下的所有非 `[x]`/非 `✅` 项
   → 有则在恢复报告中**主动提醒**（不管是否属于当前角色范围）
2.7 **角色文件膨胀检查**：`wc -l` 目标 .muse/ 文件，**>800 行 → 先执行归档再开始工作**（移动已完成工作记录/已传递指令到 `.muse/archive/`，目标 ≤500 行）
3. **🚨 自动拉取战略指令（所有非 strategy 角色必须执行）**：
   - `grep_search` 扫描 `.muse/strategy.md` 中的「📡 战略指令队列 → 活跃指令」
   - 查找所有标有当前角色的未传递指令（如 `/resume build` → 搜 `→BUILD` 或 `→DYA/BUILD`；`/resume growth` → 搜 `→GROWTH`）
   - 找到 → **在恢复报告中高亮显示「📡 新战略指令」**，并写入对应角色文件的「📡 已接收战略指令」区块
   - 回到 strategy.md 标记「✅ 已传递」
   - 没找到 → 跳过（静默）
   - ⚡ **Prometheus 角色同理**：`/resume prometheus` → 搜 `→PROMETHEUS/BUILD`，`/resume prometheus growth` → 搜 `→PROMETHEUS/GROWTH`
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
5. **如果是 `/resume strategy`：检查 memory/ 中是否有未同步到 strategy.md 的重大事件**（grep 关键词：被拒/通过/审核/定稿/部署/融资/resubmit/rejected/approved/MUSE/开源/repo）→ 有则提醒用户需要 sync
5.1 **冲突解决**：memory 和角色文件数据冲突时，**以角色文件为准**（memory 是写入时的快照，角色文件持续更新）。恢复报告只引用角色文件中的数据，memory 仅用于发现遗漏
5.2 **内部一致性校验**：输出恢复报告前，交叉检查角色文件内的同一事实是否在多处一致（如融资表/决策表/待办/指令队列中同一事项的状态是否矛盾）
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
