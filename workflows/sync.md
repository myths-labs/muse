---
description: MUSE 角色文件之间的指令传递和数据回传
---

## 统一语法

```
/sync [项目] [角色] [方向]
```

**方向**：`up`（回传给 strategy）/ `down`（从 strategy 下发）/ `to [目标]`（横向）

### 速查表

| 指令 | 含义 |
|------|------|
| `/sync dya gm up` | DYA GM 汇总回传 → strategy |
| `/sync dya gm down` | strategy 指令 → DYA GM |
| `/sync prometheus gm up` | Prometheus GM 汇总回传 → strategy |
| `/sync prometheus gm down` | strategy 指令 → Prometheus GM |
| `/sync dya build up` | DYA build 进度 → GM (或 strategy) |
| `/sync dya growth up` | DYA growth 数据 → GM (或 strategy) |
| `/sync dya build down` | GM/strategy 指令 → DYA build |
| `/sync dya growth down` | GM/strategy 指令 → DYA growth |
| `/sync prometheus build up` | Prometheus build 进度 → GM (或 strategy) |
| `/sync prometheus build down` | GM/strategy 指令 → Prometheus build |
| `/sync dya build to growth` | DYA build → DYA growth（横向） |
| `/sync dya qa broadcast` | DYA QA → DYA build + GM（广播） |

### 批量同步

| 指令 | 含义 |
|------|------|
| `/sync dya down` | GM/strategy 指令 → DYA **所有角色** |
| `/sync prometheus down` | GM/strategy 指令 → Prometheus **所有角色** |
| `/sync all down` | strategy 指令 → **所有 GM → 所有角色** |
| `/sync all up` | **所有 GM** 汇总回传 → strategy |
| `/sync all` | 全量双向同步 |

### 省略规则

当前如果在 DYA workspace 下，`dya` 可以省略：
- `/sync build up` = `/sync dya build up`
- `/sync growth down` = `/sync dya growth down`

`strategy` 永远是全局的，不需要项目前缀。

---

## 执行细节

### 1. Strategy → GM（down）— v2.0 首选路径

```
/sync dya gm down
```

我会：
1. 读取 `.muse/strategy.md` 的「📡 战略指令队列」
2. 找出所有标有 `→DYA/GM` 的未传递指令
3. 写入 `DYA/.muse/gm.md` 的「📡 指令接收队列」
4. GM 接收后自行拆解分发到项目内角色
5. 回到 strategy.md 标记「✅ 已传递」

ℹ️ **v2.0 变化**: Strategy 不再直接写入 build/growth。指令发到 GM，GM 内部拆解。

### 1b. Strategy → 角色（down）— 向后兼容

```
/sync dya build down
```

当 GM 角色未启用时，或紧急情况下，仍可直接同步到角色：
1. 读取 `.muse/strategy.md` 的「📡 战略指令队列」
2. 找出所有标有 `→DYA/BUILD` 的未传递指令
3. 写入 `DYA/.muse/build.md` 的「📡 接收战略指令」
4. 回到 strategy.md 标记「✅ 已传递」

### 2. GM → Strategy（up）— v2.0 首选路径

```
/sync dya gm up
```

我会：
1. 读取 `DYA/.muse/gm.md` 的 GM 视角项目状态汇总
2. 用「📡 数据回传 @STRATEGY (DYA/GM)」格式写入 `.muse/strategy.md`
3. 在 gm.md 标记已回传

### 2b. 角色 → Strategy（up）— 向后兼容

```
/sync prometheus build up
```

当 GM 角色未启用时，角色可直接回传 strategy：
1. 读取 `Prometheus/.muse/build.md` 中需要回传的进度/数据/请求
2. 用「📡 数据回传 @STRATEGY (PROMETHEUS/BUILD)」格式写入 `.muse/strategy.md`
3. 在 build.md 标记已回传

### 3. 横向同步（to）

```
/sync dya build to growth
```

当 BUILD 和 GROWTH 之间需要互相同步信息时：
1. 读取源文件中需要传递给对方的信息
2. 用「📡 BUILD→GROWTH 通知」格式写入目标 growth.md
3. 同时将关键信息同步到 strategy.md（保持全局视角）

### 4. QA 广播（broadcast）

```
/sync dya qa broadcast
```

QA 验证完成后，将 QA Report 同时写入多个角色文件：
1. 读取 `.muse/qa.md` 最新的 QA Report
2. 写入 build.md — **必须遵守以下格式**：
   - 使用固定 section header: `## 📡 QA→BUILD 通知`（已有则追加到该 section 下）
   - 每条通知以 `📡 QA→BUILD 通知 (YYYY-MM-DD HH:MM)` 开头
   - 通知末尾加 `🟡 待 BUILD 处理` 标记
   - BUILD 对话处理后改为 `✅ BUILD 已处理 (日期)`
   - ❌ FAIL 时 build 必须先修复
3. 用「📡 QA→STRATEGY」格式写入 strategy.md
4. 如果影响 growth → 也写入 growth.md

⚠️ **QA 铁律**: QA 只报不修。发现 bug 只写 QA Report，**不直接改代码**。需要代码修复 → 写入 build.md 由 BUILD 处理。

### 5. 接收（receive）

```
/sync receive
```

根据当前对话类型自动判断：
- **在 STRATEGY 对话中**：检查所有项目回传的数据
- **在 BUILD 对话中**：
  1. 检查 `strategy.md` 下发的新指令（搜 `→BUILD` 或 `→[PROJECT]/BUILD`）
  2. 检查 `qa.md`「最近 QA 结果」有没有未处理的 ❌ FAIL
  3. 🚨 **检查 build.md 自身** 中的 QA→BUILD 通知（`grep_search build.md "待 BUILD 处理"`）
  - 找到 → 在输出中高亮显示 `🚨 QA 有新通知待处理`，列出通知内容
  - 未找到 → 静默跳过
- **在 GROWTH 对话中**：检查 strategy 下发的新指令 + build 的横向通知
- **在 QA 对话中**：检查 strategy 指派的新 QA 任务 + build.md 中声称完成的功能

---

### 5. 指令格式

Strategy 指令中标注目标项目和 GM：
```
📡 S025→DYA/GM: V1.2.0 加入健康证明功能
📡 S025→PROMETHEUS/GM: SDK v0.3.0 加入语音合成
📡 S025→ALL: 所有项目暂停新功能，集中修 Bug
```

向后兼容（无 GM 时仍可直接指定角色）：
```
📡 S025→DYA/BUILD: V1.2.0 加入健康证明功能
📡 S025→DYA/GROWTH: 等 V1.2.0 上线后开始新一轮推广
```

GM 回传格式：
```
📡 数据回传 @STRATEGY (DYA/GM 3/12 13:07):
> V1.1.1 Build 30 重新提审中。D7 窗口明天截止。
> EP.03 分镜 16/20 完成。
> Deck 已定稿，陆续发投资人。
```

角色回传格式（向后兼容）：
```
📡 数据回传 @STRATEGY (DYA/BUILD 3/12 11:44):
  ✅ V1.1.1 Build 31 已提交审核
```

---

## 多项目场景完整用例

假设你有 3 个项目（DYA、Prometheus、ProjectC）：

**Strategy 做了跨项目决策**：
```
你: /resume strategy
（做出决策 S030→DYA/BUILD + S030→PROMETHEUS/GROWTH + S030→PROJECTC/BUILD）
你: /sync all down
→ Agent 自动分发到 3 个项目的对应角色文件
```

**DYA build 完成开发，要通知 strategy + growth**：
```
你: /resume dya build
（完成开发）
你: /sync dya build up          ← 进度回传 strategy
你: /sync dya build to growth   ← 通知 growth 可以开始推广
```

**Prometheus QA 发现 bug**：
```
你: /resume prometheus qa
（验证发现 bug）
你: /sync prometheus qa broadcast  ← 广播到 prometheus build + strategy
```

**新对话想看全局状态**：
```
你: /resume strategy
你: /sync all up    ← 拉取所有项目最新进度
```

---

## 注意事项

- **第零铁律仍然有效**：sync 是跨文件操作的唯一合法例外，但只做指令传递/数据回传，不做内容讨论
- 传递完成后，当前对话继续聚焦原文件的内容
- 如果没有新指令/回传，会告知「无新内容需要同步」
- 横向同步必须同时通知 STRATEGY（或 GM），保持全局视角
- **所有跨项目同步都在 strategy 对话中执行**（strategy 是全局中枢）
- **向后兼容**：`/sync strategy down` = `/sync dya down`（当前 workspace 默认 DYA）
- **GM 优先**: v2.0 有 GM 时，优先通过 GM 中转；无 GM 时回退到 v1 直接同步

---

## 标准搜索关键词

> Agent 在执行 `/sync receive` 或 `/resume` 时使用这些关键词 grep 搜索。

| 通知类型 | 写入位置 | 搜索关键词 | 搜索命令 |
|---------|---------|-----------|----------|
| Strategy→角色 指令 | strategy.md → 角色文件 | `→BUILD` / `→GROWTH` | `grep_search strategy.md "→BUILD"` |
| QA→BUILD 通知 | build.md 内 | `待 BUILD 处理` | `grep_search build.md "待 BUILD 处理"` |
| QA FAIL 报告 | qa.md 内 | `❌ FAIL` | `grep_search qa.md "FAIL"` |
| 角色→Strategy 回传 | strategy.md 内 | `数据回传 @STRATEGY` | `grep_search strategy.md "数据回传"` |

### QA→BUILD 通知标准格式

```markdown
## 📡 QA→BUILD 通知

### 📡 QA→BUILD 通知 (2026-03-13 04:25)

> ⚠️ [Bug 描述]

**复现**: [步骤]
**根因**: [分析]
**建议修复**: [方案]

🟡 待 BUILD 处理
```

BUILD 处理后：
```markdown
✅ BUILD 已处理 (2026-03-13 15:00) — [采纳/重写/回退]
```
