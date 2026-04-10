---
description: 核心项目的 "Launch Day" 核打击发布流。结合 MCP (Airachne) 实现产品预热与行业分析的全网广播。
---

# 🚀 /launch (Airachne Launch Day Protocol)

## 触发

```
/launch [项目名]
```

## 简介
这是我们在部署并验证了重大里程碑（比如 MUSE 开源版、Prometheus SDK）后的终极扩张指令。
它会调用常驻在本机的 `airachne` MCP 服务器，同时打穿 X 和 LinkedIn 两个舆论场，完成**多线程立体化发帖**。

## 前置条件
- 您已启动本地的 Airachne MCP Server (默认跑在 `:9848`)。
- 当您发出指令时，Agent 将确认本次要发布的产品/版本详情。

---

## 执行步骤流

### 1. **提取核心战斗力**
Agent 读取对应的 `.muse/strategy.md` 或本轮最新的更新日志。然后分别生成两条语气截然不同，但相互呼应的宣传弹药：

- **X (推特) 内容 (Geek Style)**：
  - 简短、直奔主题的破局发言。
  - 包含能引起共鸣的技术痛点（如 "No one wants to fight with DOM elements anymore"）。
  - 没有 AI 味（不要用 "Today I'm thrilled to announce" 或过度使用感叹号），句首大写，冷酷极客风。

- **LinkedIn 内容 (Thought Leadership)**：
  - 稍微长篇一点的行业洞察（分析目前的行业痛点，结合我们的破局解法）。
  - 带出产品的愿景与个人反思。
  - 强调效率与宏大叙事。

### 2. **人工核弹确认 (Nuclear Consent)**
Agent 会在同一个回复框里将生成好的两条帖子呈现给您，格式如下：

```
[Airachne 弹药库准备完毕]

🎯 Target: 𝕏 (X.com)
"..."

🎯 Target: LinkedIn
"..."

如果您确认无误，请回复 "发射"，我将同时调用 post_to_x 和 post_to_linkedin 瞬间广播全网。
```

### 3. **引爆轰炸 (MCP Execution)**
等待用户输入确认。一旦收到确认：

- Agent 执行 `call:post_to_linkedin{text: "...", auto_approve: true}`
- Agent 执行 `call:post_to_x{text: "...", auto_approve: true}`

后台服务接到指令，将在 0.1 秒内利用浏览器的 CSRF/CT0 Token 将帖子打入硅谷机房，并自动弹出本地通知。

### 4. **雷达预警启动 (Bidirectional Radar)**
告诉用户：
`“✅ 核打击已完成！我已准备好监测全网对此次发布的探讨。如有大V提及您，我会在后续回合立刻抓取并拟定回复。”`
