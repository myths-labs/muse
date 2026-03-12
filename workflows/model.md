---
description: 切换 AI 模型配置。更新 USER.md 中的模型偏好，影响 /ctx 上下文窗口计算。
---

## 用法

```
/model [模型名]
```

例：
- `/model claude opus 4.6` — 切换到 Claude Opus 4.6 (thinking)
- `/model gpt-4o` — 切换到 GPT-4o
- `/model gemini` — 切换到 Gemini 2.5 Pro
- `/model` — 不带参数，显示当前模型和可选列表

## 执行步骤

// turbo-all

### 1. 识别目标模型

从用户输入匹配到 `USER.md` 支持的模型表。模糊匹配即可（如 `opus` → `Claude Opus 4.6 (thinking)`）。

### 2. 更新 USER.md

修改 `USER.md` 中 `**当前模型**:` 这一行为新模型名。

### 3. 确认

```
✅ 模型已切换: [旧模型] → [新模型]
   上下文窗口: [总窗口] / 安全阈值: [80%值]
```

## 支持的模型

| 模型名 | 总窗口 | 安全阈值(80%) |
|--------|:-----:|:------------:|
| Claude Opus 4.6 (thinking) | 200K | 140K |
| Claude Sonnet 4.5 | 200K | 140K |
| Claude Sonnet 3.5 | 200K | 140K |
| GPT-4o | 128K | 84K |
| GPT-o1 | 200K | 140K |
| Gemini 2.5 Pro | 1M+ | 不太会爆 |
| DeepSeek V3 | 128K | 84K |

> 如需添加新模型，编辑 `USER.md` 的模型表即可。
