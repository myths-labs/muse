---
description: 结束对话的一键收尾指令。自动汇总工作、同步 .muse/ 角色文件、写短期记忆。零输入。
---

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
从对话内容自动判断本轮身份，**强制执行对应 sync**：
- Strategy 大脑 → sync strategy down（有新决策时）
- 开发对话 → **必须** sync build up
- 增长对话 → **必须** sync growth up
- 子项目开发 → **必须** sync [project] build up
- 子项目增长 → **必须** sync [project] growth up

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
- 按 Step 2 的判断和 checklist 执行 sync
- **Cross-check**: 快速扫描本轮 memory 条目，确认所有重大事件都已写入对应 .muse/ 文件
- 格式严格遵守 `/sync` workflow 的规范

### 4. 写短期记忆
更新 `memory/YYYY-MM-DD.md`（追加，不覆盖之前轮次的内容）：
```markdown
## [角色] (HH:MM)
- 完成: [要点]
- 决策: [如有]
- 下一步: [如有]
```

### 4.5 Distill 自动检测（静默）
**每次 /bye 都检查**，不需要用户触发：

1. 扫描 `memory/` 下所有 `.md` 文件（排除 `TEMPLATE.md`、`CRASH_CONTEXT.md`、`archive/`）
2. 检查 `MEMORIES.md` 的最后更新时间（grep "最后蒸馏" 或文件修改时间）
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
提醒用户手动导出对话（Agent 无法自动完成导出）：
```
📂 建议导出本次对话到:
   convo/YYMMDD/YYMMDD-NN-简短描述.md
   例: convo/260312/260312-02-muse_pain_point_fixes.md
```
- NN = 当天第几轮对话（01/02/03...），检查 `convo/YYMMDD/` 下已有文件数来确定
- 描述用英文下划线，简洁，不超过 5 个词
- 如果本轮是上下文快爆掉的紧急结束，加 `_CRASH` 后缀

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
