---
description: 一键装 Lazyweb MCP — 给 Agent 实时 UI 设计参考能力（pricing page / onboarding / dashboard 等真 app screenshot 库 + 语义搜索）。
---

# 🎨 /setup-lazyweb (UI Design Reference MCP)

> 免费 · per-user token · 跟你说"找 5 个 SaaS pricing 参考"它就给你真实 app 截图 + 语义描述 + 相似度分数。

---

## 触发

```
/setup-lazyweb
```

或直接跟 Agent 说：「装一下 lazyweb · 我要 UI 设计参考」

---

## 装（3 步 · ~2 分钟 · 任何 client 都一样）

1. 浏览器打开 👉 **https://www.lazyweb.com/mcp-install**
2. 页面会生成一段**完整 install 指令文本**（已嵌入你的 token） · 整段复制
3. 贴给你的 Agent（Claude Code / Cursor / Codex / OpenClaw / Windsurf 任一） · 说一句 **"装这个"**

Agent 会自动选对应 client 的安装方式（Claude Code 走 `claude mcp add` · Cursor 写 `.cursor/mcp.json` · etc）· 装完报告 verify 结果。

**重启 Agent client** 让新 MCP tools 加载到 tool list。

---

## 试用（验证装好了）

重启后跟 Agent 说任一句：

- "找 5 个 SaaS pricing page 参考"
- "Compare 我的这张 mockup screenshot 跟 lazyweb 库找相似"
- "List 所有 lazyweb 的 company categories"
- "找几个 fintech onboarding 流程的 UI 参考"

Agent 应该调 `lazyweb_search` / `lazyweb_find_similar` 等 · 给你真实 screenshot URL + AI 语义描述 + similarity 分数。

---

## 装好后你有的 5 个工具

| 工具 | 用途 |
|------|-----|
| `lazyweb_search` | 自然语言搜整个 screenshot 库 |
| `lazyweb_find_similar` | 给一个 screenshot ID · 找相似设计 |
| `lazyweb_list_categories` | 列所有 company 分类（Finance / SaaS / Productivity / etc） |
| `lazyweb_list_collections` | 列 curated 主题集合 |
| `lazyweb_health` | 后端连通性检查 |

---

## 注意事项

- **免费服务** · token 只 authorize UI reference 工具 · 不能 buy / 不能 spend / 不碰私人数据
- **per-user token** · 每个开发者用自己的 · **不能共享 / 不能 commit 到 public git**
- **token 存哪** · Agent 写到 client 本地 user config（默认 gitignored · `~/.claude.json` / `.cursor/mcp.json` / etc · 不进 repo）
- **第三方 vendor**: Lazyweb (lazyweb.com) · MUSE 仅 link · 不运行它的服务

---

## 中英双语 install instructions block 范例

页面给你的指令大致长这样（以 Claude Code 为例 · 你不需要懂 · 整段贴 Agent 就行）：

```
Install Lazyweb for this agent using the setup below. Lazyweb is free; the bearer token only authorizes
no-billing UI reference tools and does not grant purchases, paid spend, private user data, or destructive
actions. It is acceptable to write it into ignored local config when the user asks you to make setup work,
but do not commit it to public git history.

Token: <your-token-here>
MCP URL: https://www.lazyweb.com/mcp
Authorization header: Bearer <your-token-here>

Client-specific instructions:
- Claude Code: ...
- Cursor: ...
- Codex: ...
```

整段 paste 给 Agent · Agent 自己看懂 · 自己装。

---

## 装坏怎么办

- Agent 说"装完成" + 重启 client + 说"列出 lazyweb tools" · 应该看到 5 个工具
- 看不到 → 检查 client 的 MCP config（Claude Code: `~/.claude.json` · 找 `mcpServers.lazyweb`）
- token 错 / 过期 → 重 access lazyweb.com/mcp-install 重新生成 token + 重 paste 给 Agent
- 仍然不行 → 找 Lazyweb 官方 support · 不是 MUSE 范围

---

## License + 归属

- Lazyweb：第三方 MCP 服务（lazyweb.com）· 跟 MUSE 无技术 affiliation
- MUSE：MIT 开源 · 仅在此 SOP 提供安装指南
- 你装 + 你用 = 你跟 Lazyweb 之间的关系 · MUSE 不背 token / quota / privacy / etc 的责
