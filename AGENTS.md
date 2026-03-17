# AGENTS.md
> Auto-generated from MUSE (The AI Coding Governance System)
> This file acts as a compatibility layer for tools expecting a single AGENTS.md file.

## Core Constitution
# 🏛 Constitution — MUSE

> Copy this template to your project root and customize.
> This is the AI's "constitution" — iron rules it must follow every session.

## Iron Rules

1. **Language**: 🚨 YOU MUST communicate in **简体中文**. Every response, explanation, question, and comment MUST be in 简体中文. This is NON-NEGOTIABLE. Do NOT default to English unless this rule explicitly says English.
2. **Skill-First**: Before ANY task, check if a relevant Skill exists in `.agent/skills/`
3. **Large Files**: Only view ≤300 lines at a time. Never blindly read entire large files.
4. **Context Protection**: When context ≥ 80%, immediately run `/bye`
5. **Verify Before Claiming Done**: Run `verification-before-completion` skill before saying "done"
6. **End Sessions Properly**: Always use `/bye` to end conversations

## Skill-Driven Execution

- **Speed Reference** (know which skill to use):
  | Task | Skill |
  |------|-------|
  | Git commit | `git-commit` |
  | Code review | `code-reviewer-agent` |
  | Build errors | `build-error-resolver` |
  | Debugging | `systematic-debugging` |
  | **Verify completion** | **`verification-before-completion`** |
  | **GEO/SEO optimization** | **`geo-seo`** → `geo-audit` / `geo-citability` / `geo-schema` / `geo-report-pdf` |

## Context Health Pre-Check

Every session start: estimate context usage. If ≥ 70%, suggest opening new conversation.

Defensive saving: every 10 interaction rounds silently update `memory/CRASH_CONTEXT.md`.

## Safety Protocols

- **Action Gate**: STOP and ASK before: Refactoring, Major Updates, Deleting Files.
- **Pre-Flight**: Always BACKUP before approved destructive actions.
- **Rule Zero**: Check `CLAUDE.md` + `MEMORIES.md` before every task.

## Project-Specific Rules

### 🚨 跨项目战略指令搜索路径

> **strategy.md 位于 DYA 项目，不在 MUSE 本地。**
> 
> 绝对路径: `/Users/jj/Desktop/DYA/.muse/strategy.md`
> 
> `/resume` 执行 Step 3（拉取战略指令）时，必须搜索上方绝对路径，
> 而不是本地相对路径 `.muse/strategy.md`（MUSE 本地不存在此文件）。


### 跨项目指令匹配规则
- `/resume muse build` → 搜 `→MUSE/BUILD`
- `/resume muse growth` → 搜 `→MUSE/GROWTH`
- `/resume muse qa` → 搜 `→MUSE/QA`
- ❌ 不搜裸 `→BUILD`（那是 DYA 的指令）

---

## Roles
### Role: BUILD
**Current State**: `<!-- L0: v2.22.0 | S043✅, Skill Marketplace✅, Web Dashboard✅, VS Code Extension✅, Online Dashboard✅, TF-IDF Search✅, Benchmark✅, Strategic Repositioning✅, Memory Loss Prevention✅, 57skills -->`

# MUSE 开发状态 (Build)

> 最后更新: 2026-03-17 13:40 (CST) — v2.22.0 Memory Loss Prevention 发布
> 每次 `/resume build` 时读取此文件。
>
> ⚠️ **本文件只管开发。**
> 项目全局 → .muse/gm.md
> 开源推广 → .muse/growth.md

## 📐 职责边界

| 归本文件 (.muse/build.md) | 归 gm.md | 归 growth.md |
|--------------------------|----------|-------------|
| 框架代码开发 | 路线图/版本规划 | README 更新 |
| setup.sh 维护 | 跨角色优先级 | 社媒内容 |
| Skill/Workflow 开发 | 版本发布决策 | 社区互动 |
| Bug 修复 | 战略对齐 | 竞品分析 |
| 技术架构 | 用户反馈分类 | 文档翻译 |

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|------|
| **核心** | 纯 Markdown (零代码依赖) |
| **安装** | Bash (setup.sh) |
| **Skills** | SKILL.md (YAML frontmatter + Markdown) |
| **Workflows** | Markdown (YAML frontmatter + Steps) |
| **Templates** | CLAUDE.md / USER.md / MEMORIES.md (sed 占位替换) |

## 📦 当前版本: **v2.22.0**

### ✅ 已完成

#### v2.3 (03-12)
- [x] `/start` onboarding workflow (8 步交互引导)
- [x] `setup.sh` 交互式安装 (语言/模型/Skills 选择)
- [x] Core Skills 全部英文翻译
- [x] README badges (MIT/v2.3/Stars/Markdown/社交链接)
- [x] CHANGELOG.md (v1.0→v2.3 完整记录)
- [x] Links 修复 (mythslabs.ai → github.com/myths-labs)
- [x] Assets convention (logo/banner/screenshots/diagrams/social)
- [x] Banner + Logo 嵌入 README

#### v2.2 (03-12)
- [x] 目录命名规范
- [x] `/distill` scope 控制
- [x] L0 Defensive Auto-Save
- [x] Cheat Sheet

#### v2.1 (03-12)
- [x] GM 角色
- [x] 多项目架构
- [x] `/sync` workflow
- [x] `/resume crash`
- [x] `/model`, `/role`
- [x] QA 角色

### ⏳ 待办 (按优先级)

#### P0 — 近期
- [x] **OpenClaw / 龙虾 兼容验证** — ✅ install.sh --tool openclaw 完整实现 + 自动检测 (v2.8.0 S031)
- [x] **OpenClaw 适配文档** — ✅ README 工具表 + FAQ + Quick Start 全覆盖 (v2.8.0 S031)
- [x] `/start` workflow 端到端测试 — ✅ 4 core skills + 37 toolkit + 5 templates + 8 workflows 全部验证存在
- [x] setup.sh Linux 兼容性 — ✅ 静态分析通过，sed -i macOS→Linux fallback 正确，无 macOS-only 语法

#### P1 — 下版本
- [x] `.cursorrules` 生成器 — ✅ `scripts/generate-cursorrules.sh` (CLAUDE.md + core skills → 单文件)
- [x] Skill 依赖声明 — ✅ `creating-skills` SKILL.md frontmatter 新增 `dependencies` 字段
- [x] `memory/archive/` 自动归档脚本 — ✅ `scripts/archive-memory.sh` (--days/--dry-run)

#### P0 — 竞品技术吸收进化 (GROWTH→BUILD 3/15)

> 🔴 **最重要任务**: MUSE 当前处于全球第三梯队(详见 `docs/internal/MUSE_COMPETITIVE_DEEP_DIVE.md`)
> 目标: T3→T2→T1 逐步进化。学习+吸收+融合竞品最优实践。

| # | 吸收方向 | 学习对象 | MUSE 现状 | 目标 |
|:-:|---------|---------|----------|------|
| 1 | **记忆自动压缩/蒸馏** | mem0 (压缩引擎, 省90%token) | 手动 `/distill` | 自动化蒸馏 + token 感知 |
| 2 | **语义检索** | memsearch (Milvus向量), mem0 (hybrid DB) | 纯顺序读取 | 可选向量搜索层 (保持零依赖为 fallback) |
| 3 | **上下文分层加载** | OpenViking (L0/L1/L2) | 全量读取 | 按需加载: L0(宪法) → L1(角色) → L2(记忆按需) |
| 4 | **自动记忆捕获** | Supermemory (Auto Capture), claude-mem | 手动 `/bye` 保存 | session 结束自动捕获 + 手动并存 |
| 5 | **多Agent协作准备** | MemOS (isolation+sharing), multi-agent-memory | 手动角色切换 | 角色文件 = agent-readable protocol |
| 6 | **Plugin 生态** | memsearch ccplugin, MemOS OpenClaw Plugin | install.sh 安装 | Claude Plugin 提交 + MCP server |

- [x] 研究 mem0 架构 + 论文 → 提取可融合的设计模式 ✅ (3/15)
- [x] 研究 memsearch plain-text + 向量混合方案 → 评估: 暂不引入向量依赖，保持零依赖 ✅ (3/15)
- [x] 研究 OpenViking L0/L1/L2 → **已实现 L0 分层加载协议** ✅ (3/15)
  - `.muse/*.md` 全部加 `<!-- L0: -->` 一行摘要
  - `skills/core/layered-context/SKILL.md` 新建
  - `resume.md` boot 序列新增 Step ④.5 L0 扫描
- [x] 研究 Supermemory Auto Capture → **已增强 `/distill` 工作流** ✅ (3/15)
  - 结构化提取 (`[FACT]/[DECISION]/[LESSON]/[TODO]`)
  - 重复检测 (ADD/UPDATE/NOOP)
  - 衰减检测 (`[DECAY]` + 30天 TTL)
  - Token 预算 (≤3000 tokens)
- [x] **自动记忆捕获 (Auto Capture)** → `/bye` Step 4.7 ✅ (3/15)
  - session 结束时实时提取 `[LESSON]/[DECISION]/[FACT]` → MEMORIES.md
  - Dedup check (ADD/UPDATE/NOOP) + Token 预算 (≤2250 words)
  - 每次 /bye 最多 5 条, 不捕获 TODO
- [x] **Agent Protocol Specification** → `skills/core/agent-protocol/SKILL.md` ✅ (3/15)
  - 角色文件 = machine-readable protocol (L0/section/directive/memory/isolation)
  - MCP server / CLI / IDE plugin 集成点
  - 多项目跨角色通信规范
- [x] Claude Plugin Official 提交 (Batch 3) ✅ MCP Server `scripts/mcp-server.sh` (v2.15.0)

#### P2 — 下阶段 (按优先级)
- [x] **Skill marketplace 发现机制** ✅ (v2.17.0) — categories/stats/export/recommend/remote-install/registry
- [x] Web dashboard（记忆/任务可视化）✅ (v2.18.0) — scripts/dashboard.sh → .muse/dashboard.html
- [x] VS Code extension ✅ (v2.19.0) — vscode-extension/ (roles/skills/memory tree views + dashboard + search)

---

## 🎯 BUILD→QA: ✅ 已验证 AC (2026-03-15 v2.15.0) — MCP Server 10/10 PASS

> ✅ **QA 已验证 (2026-03-15 23:46)**: 10/10 AC PASS + 3/3 Error Paths PASS + 0 Issues
> Build Source: v2.15.0 / main / commit `f631dfe`

### AC 列表

| # | AC 描述 | 验证方式 |
|:-:|---------|----------|
| AC1 | **mcp-server.sh 可执行** — `scripts/mcp-server.sh --help` 输出包含 "MUSE MCP Server" 和 `--project-root` 选项说明 | 终端执行，验证输出 |
| AC2 | **JSON-RPC initialize** — 发送 `initialize` 请求返回 JSON-RPC response 含 `serverInfo.name = "muse-memory-os"` + `capabilities.tools` | `echo '{"jsonrpc":"2.0","id":1,"method":"initialize",...}' \| ./scripts/mcp-server.sh` |
| AC3 | **tools/list 返回 6 工具** — 发送 `tools/list` 返回 JSON 含 6 个 tool 定义，每个都含 `name` + `description` + `inputSchema` | 终端执行，验证 6 个工具名 |
| AC4 | **muse_get_status 读 L0** — 调用 `muse_get_status` 返回所有 `.muse/*.md` 文件的 L0 行内容，格式 `[role] L0内容` | 终端执行，对比 `grep '<!-- L0:' .muse/*.md` 输出 |
| AC5 | **muse_list_roles 含行数** — 调用 `muse_list_roles` 返回每个角色的文件名 + 行数 + L0 摘要 | 终端执行，验证输出含 `build`/`growth`/`qa`/`gm` |
| AC6 | **muse_get_role 读完整文件** — 调用 `muse_get_role {"role":"qa"}` 返回 qa.md 完整内容 | 终端执行，验证返回内容与 `cat .muse/qa.md` 一致 |
| AC7 | **muse_search_memory 搜索** — 调用 `muse_search_memory {"query":"v2.15","scope":"all"}` 返回匹配结果含文件名 + 行号 | 终端执行，验证输出 |
| AC8 | **mcp-config.json 存在** — `scripts/mcp-config.json` 是合法 JSON，含 `mcpServers.muse.command` 和 `args` 字段 | `jq . scripts/mcp-config.json` |
| AC9 | **CHANGELOG v2.15.0 完整** — `CHANGELOG.md` 包含 `[2.15.0]` section，列出 MCP Server + 6 工具名 | grep 验证 |
| AC10 | **README MCP section** — `README.md` 和 `README_CN.md` 均包含 "MCP" section + 6 工具表格 + 配置 JSON 示例 + v2.15.0 版本标识 | 读取文件验证 |

### 错误路径测试

| # | 场景 | 预期行为 | 验证方式 |
|:-:|------|---------|----------|
| E1 | **路径遍历攻击** — `muse_get_role {"role":"../../etc/passwd"}` | 返回 `isError: true` + "Invalid role name" 错误信息，**不返回文件内容** | 终端执行，验证拒绝 |
| E2 | **不存在的角色** — `muse_get_role {"role":"nonexistent"}` | 返回 `isError: true` + 列出可用角色 | 终端执行，验证友好错误 |
| E3 | **无效 JSON 输入** — 发送非 JSON 文本给 stdin | 不崩溃，继续运行（跳过无效行） | 终端执行，验证 server 不退出 |

---

## 🎯 BUILD→QA: ✅ 已验证 AC (2026-03-15 v2.13.0+v2.14.0) — 15/15 PASS

> ✅ **QA 已验证 (2026-03-15 20:48)**: 15/15 AC PASS + 3/3 Error Paths PASS + 0 Issues
> Build Source: v2.14.0 / main / commit `6365f13`

### AC 列表

| # | AC 描述 | 验证方式 |
|:-:|---------|----------|
| AC1 | **Semantic Compression 规则存在** — `bye.md` Step 1 包含「语义压缩规则」section，含 3 级压缩比例表 (≤5轮/6-15轮/≥16轮) + 必保留项清单 (4项) | 读取 `bye.md` 搜索 "语义压缩" 验证表格和清单 |
| AC2 | **Semantic Compression 归类示例** — `bye.md` 包含 ❌/✅ 对比示例（平铺 vs 归类） | 读取 `bye.md` 搜索 "❌ 平铺" 和 "✅ 归类" |
| AC3 | **Session Checkpoint 在 context-health-check** — `context-health-check/SKILL.md` 包含 "Session Checkpoint" section，含 When/What/Rules 子节 | 读取文件验证 3 个子节存在 |
| AC4 | **Checkpoint 触发条件表** — SKILL.md 的 Session Checkpoint 包含 4 种触发条件表格 (every 15 turns / milestone / 🟡 / topic switch) | 读取并验证 4 行表格 |
| AC5 | **Checkpoint 格式定义** — SKILL.md 包含 📍 Checkpoint 格式示例（主线/决策/状态 3 项） | grep 搜索 "📍 Checkpoint" 并验证格式 |
| AC6 | **Checkpoint 系统交互表** — SKILL.md 包含与 Defensive Auto-Save / `/bye` Step 1 / Step 4 / `/resume` 的交互关系表格 | 读取验证 4 行交互表 |
| AC7 | **Auto Profile 在 bye.md** — `bye.md` 包含 Step 4.8 Auto Profile section，标题含「自动用户画像」 | grep `bye.md` 搜索 "4.8" 和 "Auto Profile" |
| AC8 | **Auto Profile 信号检测表** — Step 4.8 包含 5 种信号类型表格 (language / code_style / work_hours / tech_preferences / verbosity) | 读取 bye.md 验证 5 行表格 |
| AC9 | **Auto Profile Guardrails** — Step 4.8 包含 4 条 guardrails (max 3/session + 不覆盖手动 + 只追加 + 不读对话) | 读取验证 4 条规则 |
| AC10 | **Step 6 输出含 Auto-profile** — `/bye` Step 6 输出模板包含 `👤 Auto-profile` 行 | grep `bye.md` 搜索 "Auto-profile" 在 Step 6 区域 |
| AC11 | **skill-discovery.sh 可执行** — `scripts/skill-discovery.sh list` 输出包含 skill 列表和 tier 徽章 (🔵/🟢/🟠) | 终端执行 `./scripts/skill-discovery.sh list \| head -10` |
| AC12 | **skill-discovery.sh search 可用** — `./scripts/skill-discovery.sh search "git"` 返回包含 git-commit 的结果 | 终端执行并验证 |
| AC13 | **SKILL_INDEX.md 存在且完整** — 根目录 `SKILL_INDEX.md` 包含 Core / Toolkit / Ecosystem 三个 section | 读取文件验证 3 个 section header |
| AC14 | **CHANGELOG v2.13.0+v2.14.0 完整** — CHANGELOG 包含两个版本 section，各有对应功能名 | grep `CHANGELOG.md` 搜索 "2.13.0" 和 "2.14.0" |
| AC15 | **README/README_CN 版本一致** — 两个文件版本标注均为 `v2.14.0` | grep 两文件搜索 "v2.14.0" |

### 错误路径测试

| # | 场景 | 预期行为 | 验证方式 |
|:-:|------|---------|----------|
| E1 | **Auto Profile 冲突** — USER.md 已有 language=en 但检测到用户用中文 | 不修改，Step 6 提示冲突 | 读取 bye.md 验证冲突处理逻辑 |
| E2 | **压缩比例边界** — 恰好 5 轮对话 | 使用 1:1 不压缩 | 读取 bye.md 验证 "≤5 轮" 规则 |
| E3 | **Checkpoint 幂等** — 同一 milestone 已 checkpoint | 应跳过不重复写 | 读取 SKILL.md 验证 idempotent 规则 |

---

### ✅ 历史 AC (v2.12.0 — 2026-03-15) — 10/10 + 2/2 PASS

<details>
<summary>展开查看</summary>

10/10 AC ✅ + 2/2 Error Paths ✅ + 0 Issues

</details>


---

---

## 📡 GROWTH→BUILD 通知

### 📡 GROWTH→BUILD (2026-03-16 00:14) ✅ 已完成

> **`muse.mythslabs.ai` 落地页 — GitHub Pages (P1)**

**背景**: S042 目录提交攻势中，OpenAlternative (13K 会员) 要求 Custom Domain（不接受 github.com 作为 Website URL）。MUSE 需要一个自定义域名落地页。

**需求**:
1. 用 **GitHub Pages** 在 MUSE repo 上部署一个简单落地页
2. 域名: `muse.mythslabs.ai`（CNAME 指向 `myths-labs.github.io`）
3. 内容: 单页介绍 — hero section + 功能亮点 + 安装命令 + GitHub 链接 + 竞品对比表
4. 素材已有: banner.png, logo.png, demo.webp, before-after.png
5. 零成本（GitHub Pages 免费）

**验收标准**:
- [x] `muse.mythslabs.ai` 可访问
- [x] 页面含 MUSE 核心功能介绍
- [x] 页面含安装命令 (`curl` one-liner)
- [x] 页面含 GitHub repo 链接
- [x] Mobile 响应式

**优先级**: P1（解锁目录提交 + 长期 SEO 价值）

---

## 📡 QA→BUILD 通知

### 📡 QA→BUILD 通知 (2026-03-15 23:46)

> ✅ **BUILD→QA v2.15.0 MCP Server — 10 AC 全部 PASS**
> Verifier: QA identity (独立对话)
> Build Source: v2.15.0 / main / commit `f631dfe`

**结果**: 10/10 AC ✅ + 错误路径 3/3 ✅ + 0 Issues (无 P0/P1/P2)

**验证范围**: mcp-server.sh CLI + JSON-RPC initialize + tools/list (6 tools) + muse_get_status/list_roles/get_role/search_memory 功能验证 + mcp-config.json + CHANGELOG + README MCP section + 安全测试 (路径遍历/不存在角色/无效 JSON)

✅ BUILD 无需操作

---

### 📡 QA→BUILD 通知 (2026-03-15 20:48)

> ✅ **BUILD→QA v2.13.0+v2.14.0 — 15 AC 全部 PASS**
> Verifier: QA identity (独立对话)
> Build Source: v2.14.0 / main / commit `6365f13`

**结果**: 15/15 AC ✅ + 错误路径 3/3 ✅ + 0 Issues (无 P0/P1/P2)

**验证范围**: Semantic Compression (bye.md Step 1) + Session Checkpoint (context-health-check SKILL.md) + Auto Profile (bye.md Step 4.8) + skill-discovery.sh (终端执行) + SKILL_INDEX.md + CHANGELOG + README 版本一致性

✅ BUILD 无需操作

---

### 📡 QA→BUILD 通知 (2026-03-15 16:54)

> ✅ **BUILD→QA v2.12.0 — 10/10 AC + 2/2 错误路径 全部 PASS**
> Verifier: QA identity (独立对话)
> Build Source: v2.12.0 / main / `7515086`

**结果**: 10/10 AC ✅ + 2/2 E ✅ + 0 Issues

✅ BUILD 已处理 — 无需操作

---

### 📡 QA→BUILD 通知 (2026-03-13 12:23)

> ✅ **BUILD→QA 10 AC 全部 PASS**
> Verifier: QA identity (独立对话)
> Build Source: v2.3 / main

**结果**: 10/10 AC ✅ + 错误路径 2/3 ✅

**🟡 P1 已修复 (ec22dad)**:
> `scripts/generate-cursorrules.sh` — 新增目标路径验证，不存在时 exit 1。

✅ BUILD 已处理

---

## 📡 已接收战略指令

### S029→MUSE/BUILD (3/13) — ✅ 已接收 3/14 16:00
> **QA SOP 已修复** — `.muse/qa.md` 已创建（速查+7步SOP+覆盖范围+Report模板）。README/resume.md QA 行已在 S030 v2.7.0 中完成。

### S035→MUSE/BUILD (3/14) — ✅ 已接收 3/14 16:00
> **MUSE SOP 同步 Bug 根因修复 (v2)** — 5个bug已修复。修改文件: `sync.md`(+Section 4b BUILD→QA reverse sync), `bye.md`(+跨项目执行铁律+strategy.md绝对路径+Step6强制合规checklist), `resume.md`(+Step4.6/4.7+跨项目Step⑥ strategy.md绝对路径铁律)。根因: QA↔BUILD反馈闭环断裂 + memory快照过时 + phantom features无检测 + 跨项目指令拉取无绝对路径 + bye无强制合规格式。

### S037→MUSE/BUILD (3/14) — ✅ Strategy 直接执行 (不需拉取)
> **SOP 角色过滤 + 待办同步修复 (v2.10.1)** — Strategy 直接修复并发布。resume.md Step 2.5 角色过滤（跨角色项分区显示）+ bye.md Step 3.5 待办更新（防 checkbox stale）。已 commit `b56460c` + tag v2.10.1 + GitHub Release 创建。CHANGELOG + README badges 已更新。

### S036→MUSE/BUILD (3/14) — ✅ 已接收 3/15 10:01
> **SOP 指令交付修复 + bye 序号 + 跨项目配置 — v2.10.0 已发布**。3 个 SOP bug 已修复: ① bye.md Step 5 convo 序号三步法 ② resume.md 🟡/✅ 过滤规则 + CLAUDE.md 路径查找 ③ CLAUDE.md 跨项目 strategy.md 绝对路径配置。已随 S029+S035 一起 commit + GitHub Release v2.10.0。

### S039→MUSE/BUILD (3/14) — ✅ 已接收 3/15 10:01
> **Skill 数量修正 54→48**。实际清点: 4 (core) + 7 (ecosystem) + 37 (toolkit) = 48 个 skills。README.md / README_CN.md 已在 Growth Session 7 修正。CHANGELOG.md 残留已修正。

### 📡 GROWTH→BUILD (2026-03-16 17:06) — ✅ 已接收 3/16 17:45

> **Online Dashboard v2 增强 + 落地页设计合规 (P1, ~2-3h)**

**背景**: Growth 审查发现 Online Dashboard (`docs/dashboard.html`) 信息密度偏低，仅展示 4 stat + role L0 + memory timeline，用户看完后没有足够的 "aha moment"。落地页也有几个 BUILD 新增内容需要与 Growth 设计规范对齐。

**A. Dashboard v2 增强** (P1):
1. **角色卡展开** — 点击 role card → 展开显示完整 L0 + 关键 sections 预览（职责/待办前 5 行）
2. **Skills 分类视图** — 新 tab，按 Core/Toolkit/Ecosystem 分类展示 + 搜索
3. **Memory 内容预览** — 点击 memory 条目 → 展开显示前 10 行摘要
4. **项目健康度** — 最近活跃时间、memory 增长趋势 (简单 bar chart, CSS-only)
5. **Directive 队列** — 显示待处理 🟡 指令 + 已完成 ✅（从 role files 解析 `📡` sections）

**B. 落地页设计合规** (已由 Growth 部分修复，BUILD 确认):
- ✅ Nav "Dashboard" 改为金色 pill button (`.nav-dashboard-link`)
- ✅ "New in v2.20" section 改为非 dark 背景（与 Demo section 区分）
- ✅ Dashboard `.role-l0` 文字溢出修复 (`line-clamp: 3`)
- ⬜ Dashboard title 去 emoji（`🎭` → 纯文字）— ✅ 已修

**增长价值**: Dashboard 是 MUSE 最直观的 Demo 入口，增强后可直接用于 Product Hunt gallery + Reddit 帖子配图 + 落地页嵌入。

### S043→MUSE/BUILD (3/16) — ✅ 已接收 3/16 15:50
> **agency-agents 吸收 + 兼容层 (P1, ~5h)**。两个任务: A. Prompt 质量吸收 — 从 142 agent 中挑编程相关优质 prompt → 融入 MUSE skills + 角色人格化。B. convert.sh 兼容层 — MUSE skills 一键导出 .cursorrules/Windsurf/Copilot/OpenClaw 格式 + 反向 agency-agents→MUSE 迁移。增长价值: convert.sh 切入 agency-agents 35.2K 用户池。

### S041→MUSE/BUILD (3/15) — ✅ 已接收 3/15 16:08
> **🔴 MUSE 竞品深度调研回传 — T3 定位 + 技术进化路径 (P0)**。MUSE 在全球 Agent Memory 市场为 T3 下游: T1=mem0(49.8K⭐/YC), Supermemory(10K+/SaaS), OpenViking(7.4K/字节); T2=memsearch(Zilliz), MemOS(学术级); T3=MUSE(2⭐)。MUSE 独有: 战略指令队列 + 角色文件隔离。**Batch 1 ✅** (v2.11.0): L0分层加载 + `/distill`增强。**Batch 2 执行中**: 自动记忆捕获(`/bye`增强) + Agent Protocol spec。**Batch 3**: Claude Plugin 提交。完整报告: `docs/internal/MUSE_COMPETITIVE_DEEP_DIVE.md`。

### S047→MUSE/BUILD (3/17) — ✅ 已接收 3/17 17:24
> **🚨 新增 SOP — 开发完成自动发 AC 给 QA**。每完成一个功能开发或更新后，BUILD 角色必须自动将 Acceptance Criteria (AC) 整理并写入 `.muse/qa.md`，不再需要用户手动输入"发ac给xxx qa"。
>
> **流程**:
> 1. 功能开发/更新完成 → 确认所有 commit 已推送
> 2. 整理 AC 清单（功能描述 + 验收标准 + 测试步骤 + 错误路径）
> 3. 自动写入 `.muse/qa.md`「BUILD→QA」区域，标注 🔲 待验收
> 4. 在 `/bye` 或任务结束时的输出中提示用户 "AC 已发给 QA"
>
> **适用范围**: 所有项目（DYA / Prometheus / MUSE / Pantheon）
> **触发条件**: `git tag` / `feat()` commit / 功能模块交付

---

## 📋 CHANGELOG 维护规则

> ⚠️ **每次 feat/fix commit 时，必须同步更新 `CHANGELOG.md`。**

| 场景 | 操作 |
|------|------|
| 新功能 `feat(...)` | 在当前版本下 `### Added` 中加一行 |
| Bug 修复 `fix(...)` | 在当前版本下 `### Fixed` 中加一行 |
| 版本发布 (tag) | 执行下方 Release Checklist ↓ |

### 🚨 Release Checklist（打 tag 前必须全部完成）

> **教训 v2.10.0**: tag 打在 badge 修复前 + 忘记创建 GitHub Release → 修复后写此清单

1. [ ] **版本号全局搜索** — `grep -r "旧版本号" README.md README_CN.md CHANGELOG.md` 确保零残留
2. [ ] **CHANGELOG** 已添加新版本 section
3. [ ] **所有变更已 commit** — `git status` 无未提交文件
4. [ ] **打 tag** — `git tag vX.Y.Z`
5. [ ] **Push tag** — `git push origin main --tags`
6. [ ] **创建 GitHub Release** — `gh release create vX.Y.Z --title "..." --notes "..." --latest`
7. [ ] **验证** — 刷新 GitHub repo 页面，确认 Releases 栏显示新版本为 Latest

---

## Git

- 当前分支: `main`
- **Repo**: `origin` → https://github.com/myths-labs/muse.git
- **Git Config**: email=`jc@mythslabs.ai`, name=`JC-Myths`


### Role: GM
**Current State**: `<!-- L0: v2.14.0 | Stars=2, Core Skills=5, Toolkit=42, Eco=7, Workflows=8, T2巩固✅(Batch1-2+SemanticCompression+SessionCheckpoint+AutoProfile), Batch3=Plugin -->`

# MUSE 项目总管 (GM)

> 最后更新: 2026-03-15 21:40 (CST)
> 每次 `/resume gm` 时读取此文件。
>
> ⚠️ **本文件管 MUSE 项目全局。**
> 开发细节 → .muse/build.md
> 开源推广 → .muse/growth.md
> 战略对齐 → DYA/.muse/strategy.md (S019)

## 📐 职责边界

| 归本文件 (.muse/gm.md) | 归 build.md | 归 growth.md |
|------------------------|-------------|-------------|
| 路线图和版本规划 | 框架开发 | GitHub stars 增长 |
| 跨角色优先级仲裁 | setup.sh/工作流维护 | 社区运营 |
| 版本发布决策 | Skill/Workflow 开发 | 社媒推广 |
| 战略对齐 (DYA S019) | Bug 修复 | README/文档优化 |
| 用户反馈分类 | 技术架构决策 | 竞品分析 |

---

## 📦 当前版本: **v2.14.0**

### 🎯 项目定位

MUSE = 纯 Markdown AI 编程协作 OS
核心价值: 跨对话无损上下文管理
目标用户: Claude Code / Cursor / Windsurf / OpenClaw / Gemini CLI 用户
差异化: 零代码依赖，纯 SOP 驱动
竞品定位: T3→T2 进化中（详见 `docs/internal/MUSE_COMPETITIVE_DEEP_DIVE.md`）

### 📊 项目现状

| 指标 | 当前 | 目标 |
|------|------|------|
| GitHub Stars | 2 | 100 (Show HN 后) |
| 版本 | v2.14.0 | v3.0 |
| Skills (Core) | 5 | 6+ |
| Skills (Toolkit) | 42 | 50+ |
| Skills (Ecosystem) | 7 | 10+ |
| Workflows | 8 | 10+ |
| 文档语言 | EN + CN | + JP (stretch) |
| 支持工具 | Claude/Cursor/Windsurf/OpenClaw/Gemini/Codex | + VS Code ext |

### ✅ 已完成里程碑

- [x] v2.3: `/start` onboarding + `setup.sh` + Core Skills 英文翻译 + README badges
- [x] v2.5: 48 Skills (4 Core + 37 Toolkit + 7 Ecosystem)
- [x] v2.7: `/settings` + Pre-Flight Check + Mid-Conversation Sync
- [x] v2.8: Multi-tool installer (`install.sh` 6 工具) + OpenClaw 兼容
- [x] v2.9-v2.10: SOP 铁律修复 (bye/resume/sync) + 跨项目配置
- [x] v2.11: L0 分层加载 (Batch 1) + `/distill` 增强
- [x] v2.12: Auto Memory Capture (Batch 2) + Agent Protocol Spec
- [x] v2.13: Skill Marketplace CLI (`skill-discovery.sh`) + `SKILL_INDEX.md` (56 skills)
- [x] v2.14: T2 巩固 — Semantic Compression + Session Checkpoint + Auto Profile
- [x] Demo GIF 制作 (85帧, 17秒)
- [x] Social preview + Banner + Logo
- [x] 9/9 渠道首发完成
- [x] Awesome list PR x7 提交
- [x] 竞品深度调研 (10+ 全球竞品)

---

## 📋 路线图

### v2.15 — 近期
- [ ] Claude Plugin Official 适配 (Batch 3)
- [ ] MCP Server 实现 (基于 Agent Protocol spec)

### v3.0 — 中期
- [ ] Show HN 发布 (T2→T1 进化后)
- [ ] `/start` 实际外部用户测试
- [ ] 第三方社区 Skill 贡献流程

### v4.0 — 远期
- [ ] Web UI dashboard (可视化记忆/任务管理)
- [ ] VS Code extension

---

## 📡 跨项目同步指令

| 指令 | 干什么 |
|------|--------|
| `/sync strategy` | 读取 `DYA/.muse/strategy.md` 的 S019 部分 |
| `/sync strategy up` | 将 MUSE 进度回传到 S019 |
| `/sync build` | 查看 build.md 当前开发状态 |
| `/sync growth` | 查看 growth.md 推广进展 |

**路径约定**：
- 战略文件: `/Users/jj/Desktop/DYA/.muse/strategy.md` → S019 MUSE 部分
- MUSE 代码: `/Users/jj/Desktop/MUSE/`


### Role: GROWTH
**Current State**: `<!-- L0: v2.22.0 | Governance System✅, TF-IDF Search✅, Benchmark✅, Memory Loss Prevention✅, Skill Marketplace✅, Web Dashboard✅, VS Code Extension✅, Online Dashboard✅, S043✅, 57skills, 9/9渠道已发, S040黑客松梗图 Batch1+2已就绪, S042目录攻势✅, LLM SEO✅, Show HN暂缓, Reddit仍封, Stars=2, BUILD_IN_PUBLIC_POSTS.md待更新 -->`

# MUSE 开源推广 (Growth)

> 最后更新: 2026-03-17 13:42 (CST) — v2.22.0 Memory Loss Prevention + v2.21.0 Governance Repositioning 同步
> 每次 `/resume growth` 时读取此文件。
>
> ⚠️ **本文件只管推广和社区。**
> 开发细节 → .muse/build.md
> 项目全局 → .muse/gm.md

## 📐 职责边界

| 归本文件 (.muse/growth.md) | 归 build.md | 归 gm.md |
|--------------------------|-------------|----------|
| GitHub stars 增长 | 框架代码开发 | 路线图规划 |
| 社区运营 | Bug 修复 | 版本发布 |
| 社媒内容 (X/Reddit/HN) | Skill 开发 | 跨角色协调 |
| README/文档优化 | setup.sh 维护 | 战略对齐 |
| 竞品分析 | 架构决策 | 用户反馈分类 |
| KOL/社区合作 | 技术文档 | 优先级仲裁 |

---

## 📊 增长目标

| 指标 | 当前 | 30天目标 | 90天目标 |
|------|------|---------|---------| 
| GitHub Stars | 0 | 100 | 500 |
| X Followers (@MythsLabs) | — | 200 | 1K |
| README 访问量 | — | 1K | 5K |
| setup.sh 使用次数 | — | 50 | 200 |

---

## 🎯 增长策略

### 渠道优先级

> ⚠️ **2026-03-15 Growth 决策：Show HN 暂缓 + MUSE 先进化**
> - 🔴 **竞品深度调研结论**: MUSE = 全球第三梯队下游 (详见 `docs/internal/MUSE_COMPETITIVE_DEEP_DIVE.md`)
> - T1: mem0 (49.8K⭐/YC), Supermemory (10K+/SaaS), OpenViking (7.4K/字节)
> - T2: memsearch (Zilliz), MemOS (学术级)
> - **Show HN 暂缓** — 先吸收竞品技术进化 MUSE → 积累外部用户 → 再发
> - Show HN 帖子 v3 已备好: `docs/internal/SHOW_HN_DRAFT.md`
> - Reddit 账号仍 shadowban 中
> - **→BUILD**: 竞品技术吸收 = 下阶段最重要任务 (已写入 build.md P0)

| 渠道 | 优先级 | 策略 | 状态 |
|------|:------:|------|:----:|
| **X (Twitter)** | P0 🥇 | Thread EN | ✅ @MythsLabs 已发 (3/13) |
| **小红书** | P0 🥇 | S040 黑客松巅峰赛 梗图系列 #vibecoding | ✅ v2 已发 + 3帖排期中 |
| **LinkedIn** | P1 | 公司页 + 个人帖 | ✅ 已发 (3/15 00:28) |
| **Threads** | P1 | 繁体中文版 | ✅ 已发 (3/14) |
| **Facebook** | P1 | 分享帖 | ✅ 已发 (3/14) |
| **Reddit** | P1 🚫 | r/ClaudeAI — **等 shadowban 解除** | ⏳ 被封中 |
| **Hacker News** | P2 ⏸️ | Show HN — **暂缓, 等 MUSE 进化后再发** | ⏸️ 帖子v3已备 |
| **Product Hunt** | P2 | Launch with demo GIF | 🔲 文案就绪 (`PRODUCT_HUNT_LAUNCH.md`) |
| **Dev.to / Hashnode** | P2 | 技术文章 | ✅ 草稿更新至 v2.15.0 |
| **LLM SEO / AEO** | P0 🆕 | llms.txt + JSON-LD + structured data | ✅ 已上线 |
| **8 新 Launch 平台** | P1 🆕 | Betalist/Fazier/Uneed/SaaSHub/TAAFT/Microlaunch/Peerlist/Toolfolio | 🔲 文案就绪 (`PLATFORM_SUBMISSION_GUIDE.md`) |

### 内容素材

| 素材 | 状态 | 说明 |
|------|:----:|------|
| Banner image | ✅ | 缪斯女神 + 金色迷宫 logo |
| Logo | ✅ | 金色迷宫 logo.png |
| Demo Animation (WebP) | ✅ | `assets/demo.webp` — `/resume` → work → `/bye` full flow recording |
| Demo Preview (PNG) | ✅ | `assets/demo-preview.png` — static final state screenshot |
| Before/After 对比图 | ✅ | `assets/before-after.png` — dark devtool aesthetic, EN |
| 1-min 介绍视频 | 🔲 | 即梦/CapCut 制作 |
| llms.txt | ✅ | `docs/llms.txt` — LLM SEO 结构化描述 |
| JSON-LD | ✅ | `docs/index.html` — Schema.org SoftwareApplication |
| Platform 提交指南 | ✅ | `docs/internal/PLATFORM_SUBMISSION_GUIDE.md` — 8 平台 |
| Reddit 帖子草稿 | ✅ | `docs/internal/REDDIT_POST_DRAFTS.md` — 10 subreddits |
| PH Launch 文案 | ✅ | `docs/internal/PRODUCT_HUNT_LAUNCH.md` |
| Build in Public 系列 | ✅ | `docs/internal/BUILD_IN_PUBLIC_POSTS.md` — 3 X Threads + 2 LinkedIn |

### 竞品定位（2026-03-15 深度调研更新）

> 完整报告: `docs/internal/MUSE_COMPETITIVE_DEEP_DIVE.md`

| 梯队 | 竞品 | Stars | 方案 | MUSE 差距 |
|:----:|------|:-----:|------|----------|
| 🏆T1 | **mem0** | 49.8K | vector+graph 混合DB, 压缩引擎, YC, 论文 | 技术代差 |
| 🏆T1 | **Supermemory** | 10K+ | 语义图谱, Auto Capture, SaaS API | 商业完整度 |
| 🏆T1 | **OpenViking** (字节) | 7.4K | L0/L1/L2分层加载, ArkClaw云端版 | 企业级 infra |
| 🥈T2 | **memsearch** (Zilliz) | 新发布 | 纯文本+Milvus向量搜索, Claude Code plugin | 直接优于MUSE |
| 🥈T2 | **MemOS** | — | 统一API, 多模态, MemCubes, 异步预加载 | 学术深度 |
| 🥉**T3→T2** | **MUSE** | **2** | 纯Markdown, 角色隔离, 指令队列, MCP Server | ← Batch1-3✅ |

**MUSE 真正独有**:
- ✅ 战略指令队列 (📡 跨角色异步消息 🟡/✅ 协议)
- ⚠️ 角色文件隔离 (build.md/qa.md/growth.md 各读各的)

**→BUILD 进化路径**: 吸收 mem0 压缩 + memsearch 向量 + OpenViking 分层 → T3→T2→T1

**v2.22.0 卖点**: **"The AI Coding Governance System"**——唯一 L2 治理层玩家 | MCP Server(6工具Bash零依赖) | Memory Loss Prevention(5层SOP修复防止上下文丢失) | TF-IDF Search(search.sh零依赖语义搜索) | Benchmark(16.9×上下文 vs bare) | Dashboard(在线+本地+VS Code) | Skill Marketplace(57 skills/6格式导出) | L0分层加载 | 自动记忆捕获 | QA 35/35 PASS

> 🚨 **重大更新**: BUILD_IN_PUBLIC_POSTS.md 内容已严重过时（还写 v2.15.0/56 skills/旧 tagline），待 GROWTH 下次对话重写。

### 🦞 OpenClaw / 龙虾 热潮 (3/13 发现)

**背景**: 中国大陆全网在聊 OpenClaw (龙虾)，国内大厂也在做 fork。MUSE 天然兼容。

**Growth 机会**:
- MUSE 支持所有支持 system prompt 的 AI 工具，包括 OpenClaw 及 fork
- 中文推广（小红书/微信群）应明确提到兼容龙虾
- 龙虾社区 = MUSE 中国市场最大流量入口

**→BUILD**: ✅ 已完成 OpenClaw 兼容安装 (v2.8.0 install.sh --tool openclaw)

---

## 📋 内容日历

### Week 1: 冷启动
- [ ] Reddit r/ClaudeAI 首帖 — ✗ shadowban 中
- [x] X Thread (EN) — ✅ @MythsLabs 已发 (3/13)
- [x] ~~小红书 v1~~ — ❌ 被限流(0浏览) → 已删帖 (3/14 02:31)
- [x] 小红书 v2 — ✅ 砸电脑续集·边界→系统叙事 (3/14 13:15)
- [x] Demo 动画制作 — ✅ `assets/demo.webp` + `.gif` + `.mp4`
- [x] Before/After 对比图 — ✅ EN + CN 两版
- [x] 微信发布 — ✅ 朋友圈 + 微信群分发完成 (3/13)
- [x] LinkedIn x2 — ✅ 公司页 + 个人帖 已发 (3/15 00:28)，含竞品差异化定位
- [x] Threads (繁中版) — ✅ 已发 (3/14 13:41)
- [x] Facebook — ✅ 已发 (3/14 13:29)
- [x] X Quote RT (@SunshiningDay) — ✅ 已发 (3/14 01:50)
- [x] Show HN 帖子 v3 已备 — ⏸️ **暂缓, 等 MUSE 进化后再发** (`docs/internal/SHOW_HN_DRAFT.md`)
- [x] Awesome list PR x7 — **1/7 merged** (awesome-vibe-coding-resources #6 ✅), 6 open (`docs/internal/AWESOME_LIST_TRACKER.md`)

### Week 2: S040 黑客松 + 进化
- [x] 小红书黑客松巅峰赛 梨图 Batch 1 x3 (3/16-3/20 排期) ← `assets/social/`
- [x] 🔴 **S040v3 升级: 每帖补至 3 图** ✅ (3/15)
- [x] 🚨 **S040v4 铁律: 评论区禁止自推广** — 6帖全部改为故事型追评 (3/15 20:55)
- [/] 继续小红书黑客松产出 (每划3-4帖至4/30)

### Week 3: Batch 2 梨图 (3/23-3/29) ← 基于全网热门趋势
- [ ] 帖4: Vibe Coder的五个阶段 (3/23 周日 20:00, 3图) ← `2026-03-22-xhs-hackathon/`
- [ ] 帖5: git blame 不会说谎 (3/26 周三 12:30, 3图) ← `2026-03-25-xhs-hackathon/`
- [ ] 帖6: 面试翻车·传统程序员vs Vibe Coder (3/29 周六 20:00, 3图) ← `2026-03-28-xhs-hackathon/`

### Week 4-8: 排期框架 (3/29-4/30)
- [ ] W4 (3/29-4/3): 展示作品 — 终端录屏 /resume 恢复 + 角色隔离效果
- [ ] W5 (4/4-4/10): 梗图 Batch 3 x2 + 教程 x1 (5步安装教程)
- [ ] W6 (4/11-4/17): 展示作品 + 独立开发者效率故事
- [ ] W7 (4/18-4/24): 梗图 Batch 4 x2 + 进阶教程 x1
- [ ] W8 (4/25-4/30): 收官冲刺 — 高表现类型复制 + 投票帖
- [ ] Product Hunt launch (待 Stars ≥50)
- [/] Dev.to 技术文章 — 草稿已更新至 v2.15.0 (`docs/internal/DEVTO_ARTICLE_DRAFT.md`)  — **待 T2+ 再发**
- [ ] 邀请 3-5 个 Claude Code 重度用户试用
- [ ] 收集首批用户反馈

### Week 3-4: 社区
- [ ] 创建 Discussions 板块
- [ ] 第一个外部 PR 引导
- [ ] 用户 Skill 展示 (Community Skills Showcase)

### 🚨 小红书限流教训 (3/14)

| 教训 | 详情 |
|------|------|
| **自推广 vs 利他** | 小红书算法对「我做了个东西来看看」（利己型）严重限流，「帮你发现好东西」（利他型）正常推流 |
| **GitHub 不是禁词** | 几十万帖用 GitHub 正常跑量，关键词本身不是问题 |
| **功能清单 = 产品说明书** | ✅ Checklist 格式 + 多个产品名堆叠 = 广告特征 |
| **v2 策略** | 故事/吐槽壳包装 + 零外链(评论区放) + 延续高表现 IP（砸电脑帖 856 views） |

---

## 📡 已接收战略指令

### S040→MUSE/GROWTH (3/15) ✅ 已拉取

**小红书黑客松巅峰赛 MUSE 内容计划 (主攻 #vibecoding)**

**活动规则**: 必带 #黑客松巅峰赛 + 子话题(#vibecoding 或 #独立开发)，每帖保底3W流量扶持，优质帖追加投放上不封顶，截止4/30。

**竞品分析基础 (S040 v2)**:
- 梗图是绝对互动王者(1421赞/1195赞 vs 教程60评论)
- 投票是互动核武器(412/681人参与)
- "X时间做出Y"是#独立开发通用公式
- 真诚谦虚>炫技
- 视频/实机演示是必须
- 只用 #vibecoding + #独立开发（#黑科技全硬件，砍掉）

**内容方向(按优先级)**:
1. **梗图先行 #vibecoding** (产量最高，涨粉最快): "AI写代码写着写着突然开始讨论营销策略..." / "vibe coding翻车集锦: 上下文爆了篇" / "Claude Code用户的一天 vs 装了MUSE的Claude Code用户"
2. **#vibecoding「展示作品」**: 酷炫终端录屏展示 /resume 恢复 + 角色隔离效果 — Demo GIF/录屏是核心素材
3. **#vibecoding「教程」**: 给你的AI编程助手装一个操作系统，5步搞定(❶curl安装 ❷配置 ❸第一次/resume ❹效果对比 ❺进阶用法)
4. **#独立开发「推荐宝藏产品」**: 推荐一个让vibe coding不翻车的开源工具(第三方推荐口吻)
5. **#独立开发「展示作品」**: 一个人做了3个开源项目管理它们全靠一套markdown文件 — 末尾加投票

**建议频率**: 每周3-4帖(三项目中产量最高)
**社群引流**: 参考麻省理工Rui(vibe coding社区群聊+154人)，可建小红书原生群

---

### S040v3→MUSE/GROWTH (3/15 10:38) ✅ 已完成

**已有梗图升级为 3-4 图帖（立即执行）**

> 来源: S040v3 配图帖深度分析 (4个top案例截图拆解)

**问题**: 当前 3 张梗图每帖1图 → 违反 v3 规律（top 无单图帖）

**7条成功规律**:
1. 经典梗图模板 = 最高赞上限
2. **3-4张图是最佳数量** (无单图进 top)
3. 自嘲>炫技 (痛点共鸣×幽默=最高互动)
4. **文案≤45行** (梗在图里不在文里)
5. 对比表格/假排行榜 = 高收藏原创图式
6. 成就帖用"真诚反差"+第三方截图背书 = 高评论
7. 视频教程 = 收藏核武器但门槛高

**每帖图片组合**: 图1钩子(梗图) → 图2深度(表格/第二梗) → 图3高潮(金句/分享冲动) → 图4彩蛋(可选)

**图片制作优先级**: 🥇经典梗图模板(5min) → 🥈对比表格/排行榜(15min) → 🥉文字金句图(3min)

**具体操作**: 每帖保留原梗图作为图1，追加:
- 图2: 🥈对比表格/假排行榜 (如"Top 10 Claude Code 翻车语录" / "有MUSE vs 没MUSE的AI编程日常")
- 图3: 🥉文字金句图 (黑底绿字毒鸡汤，如"与其购买AI生产力课程，不如先预约心理疗程")

**避坑**: ❌单图 ❌长文案(>5行) ❌自卖自夸 ❌全文字图 ❌堆功能清单

---

### S041→MUSE/BUILD (3/15 09:50) ✅ 已接收

**MUSE 竞品深度调研 T3 定位 + 技术进化路径 (P0)**

> BUILD 已接收并列为 P0。v2.11.0 已完成 Batch 1 (L0分层+/distill增强)。
> 完整报告: `docs/internal/MUSE_COMPETITIVE_DEEP_DIVE.md`

---

### S042→MUSE/GROWTH (3/15) ✅ 已执行 (3/16 13:31)

**Launch 平台提交 + 开源目录攻势** — 全部完成 ✅

**目录提交（已完成）**:
1. ✅ [OpenAlternative](https://openalternative.co/) — 已提交，24h 内上线 (3/16)
2. ✅ [LibHunt](https://www.libhunt.com/) — 已提交为 Claude Code alternative (3/16)
3. ✅ [AlternativeTo](https://alternativeto.net/) — 已提交 "MUSE - AI Agent Memory System" (3/16)
4. ✅ [SourceForge](https://sourceforge.net/) — 已提交 museai (3/16)

**Social Listening**:
- ✅ [F5Bot](https://f5bot.com) 已注册 — 5 关键词: muse agent / claude code memory / agent memory markdown / myths-labs / vibe coding memory (3/16)

**Reddit 解封后**: r/SideProject / r/indiehackers / r/ClaudeAI（技术价值帖不推产品）

**中期**: Indie Hackers builder story → Product Hunt（Show HN 先行·PH 后发）→ [Peerlist](https://peerlist.io/)

---

### S033→MUSE/GROWTH (3/14) 🟡 待执行

**MUSE 增长包装优化 — 竞品定位 + 差异化包装**

**竞品分析结论**: MUSE 有 3 个独有差异化，但 Star 数致命落后。

| 差异化 | 说明 | 竞品情况 |
|--------|------|----------|
| **角色权限隔离** | strategy/build/growth/qa 独立角色，互不干扰 | 竞品无 |
| **战略指令队列** | 📡 跨角色指令传递 + 🟡/✅ 状态追踪 | 竞品无 |
| **双层记忆系统** | memory/ 短期快照 + .muse/ 长期进度 | 竞品多为单层 |

**Star 差距**: MUSE 2 ⭐ vs everything-claude-code 50K+ / claude-mem 34.7K / agency-agents 35.2K

**行动指令**:
1. ✅ README 英文优先重写 + "Why MUSE" section + 竞品对比表 — 已在 v2.10.0 更新
2. ✅ Demo GIF/30秒视频展示跨对话记忆 — `assets/demo.webp` 85帧17秒已重做
3. ✅ 提交 PR 到 awesome 列表 (5/7 成功):
   - ✅ [awesome-claude-skills #276](https://github.com/travisvn/awesome-claude-skills/pull/276)
   - ✅ [awesome-claude-code #25](https://github.com/jmanhype/awesome-claude-code/pull/25)
   - ✅ [awesome-vibe-coding #90](https://github.com/filipecalegario/awesome-vibe-coding/pull/90)
   - ✅ [awesome-claude-code-toolkit #42](https://github.com/rohitg00/awesome-claude-code-toolkit/pull/42)
   - ✅ [awesome-claude-code (jqueryscript) #88](https://github.com/jqueryscript/awesome-claude-code/pull/88)
   - ❌ sourcegraph/awesome-code-ai — repo 已 archived (只读)
   - ❌ hesreallyhim/awesome-claude-code — 仅限 collaborators 提 PR
4. 🔲 Show HN（HN 已解封，养号 1-2 周 + 20 karma 后发）
5. ✅ 清除 DYA/Prometheus 自用痕迹 — 已完成内部文件泄漏修复 v2.10.0

**定位口号**: 「AI 编程 Agent 的操作系统 — 跨对话记忆 + 角色治理 + 多项目管理」

**竞品分析完整报告**: `brain/e80ad0ee.../muse_competitive_analysis.md`

---

### S027→MUSE/GROWTH (3/13) 🟡 待执行

**MUSE Launch 战略定位 + 发帖指令**

**核心定位**: MUSE = Myths Labs 口碑项目，不盈利。开源建信任 → 为 Prometheus 预热。

| 维度 | 指令 |
|------|------|
| **目标受众** | AI 编程用户（Claude Code / Cursor / Windsurf），独立开发者，solopreneur |
| **核心叙事** | Solo Founder 用 MUSE 管理 3 个产品的真实故事 |
| **发布渠道** | ① X launch thread → ② 小红书/即刻开发者帖 → ③ LinkedIn → ④ Reddit（等解封）→ ⑤ Show HN（等养号） |
| **可以提** | "Myths Labs 的下一个产品 Prometheus Avatar SDK 即将上线"（自然引流） |
| **绝对不提** | 定价、商业模式、融资（这是 Prometheus 的事） |
| **语气** | 真诚分享，独立开发者视角，不做营销腔 |
| **关键数据** | 56 skills / 零依赖 / 纯 Markdown / MIT 开源 / 同时管理 3 个产品 / **6 AI 工具一键安装** / **自动记忆捕获** / **L0 分层加载** |

### S031→MUSE/GROWTH (3/13) ✅ 已完成

**中文渠道推广加龙虾/OpenClaw 兼容角度**
- 小红书/微信群/即刻内容明确提到: “兼容龙虾/OpenClaw 及国内 fork”
- 卖点: v2.8.0 `install.sh --tool openclaw` 一键安装
- BUILD 已完成技术实现 ✅，待 GROWTH 在推广内容中落地

### S025→MUSE/GROWTH (3/12) ✅ 已完成

**社交 Profile 更新 + Launch Campaign**
- 推广优先级: MUSE › Prometheus › DYA › Airachne
- Bio 文案见 `docs/social-media/MUSE_BIO_UPDATE.md`
- 社交平台 Profile 手动更新中（X/LinkedIn/小红书/B站等）

---

## 📡 跨角色同步日志

### 2026-03-17 13:42 — BUILD→GROWTH 同步 (v2.21.0+v2.22.0 两版发布)

**来源**: BUILD v2.21.0 (3/16 23:19) + v2.22.0 (3/17 13:31)

**同步内容**:
1. ✅ **v2.21.0**: **战略重定位** — "Memory-Unified Skills & Execution" → **"The AI Coding Governance System"**
   - AGENTS.md(19K⭐) = L1 Workflow 层王者，MUSE 重定位为 L2 Governance System 层唯一玩家
   - TF-IDF Search (`scripts/search.sh`) — 零依赖语义搜索
   - Benchmark: 16.9× vs bare .cursorrules
   - README/Landing page 全量重写
2. ✅ **v2.22.0**: **Memory Loss Prevention** — 5层 SOP 修复防止跨对话上下文丢失
   - `/bye` 上下文恢复三问 + 7字段记忆模板
   - `/resume` Boot Step ⑦ 项目部署事实表 + Step 5.3 校验
   - GitHub Release: https://github.com/myths-labs/muse/releases/tag/v2.22.0
   - Skills: 56→57

**🚨 →GROWTH 行动项**:
- [ ] 🔴 **重写 `BUILD_IN_PUBLIC_POSTS.md`** — 当前内容严重过时（还写 v2.15.0/56 skills/旧 tagline "Memory-Unified Skills & Execution"），必须更新为 v2.22.0 + "The AI Coding Governance System" + L2层叙事 + Benchmark数据 + Dashboard/VS Code/TF-IDF 等新功能
- [ ] Show HN 帖子内容更新 (v2.22.0 + Governance System 定位)
- [ ] Product Hunt 文案更新 (Dashboard + Benchmark 作为 demo 点)
- [ ] Dev.to 文稿更新 (v2.22.0 + Memory Loss Prevention 放进技术叙事)
- [ ] 8新Launch平台描述更新为 v2.22.0
- [ ] X Thread: "MUSE is now The AI Coding Governance System" (新素材)

### 2026-03-16 16:40 — BUILD→GROWTH 同步 (v2.16.0→v2.20.0 五版发布)

**来源**: BUILD v2.16.0-v2.20.0 连续五版发布 (3/16)

**同步内容**:
1. ✅ **v2.16.0**: Skill Format Converter (`convert-skills.sh`) — 导出 56 skills 到 6 种 AI 工具格式 (Cursor/Windsurf/Copilot/OpenClaw/Aider/Antigravity) + agency-agents prompt 质量吸收
2. ✅ **v2.17.0**: Skill Marketplace Discovery — 6 个新命令 (categories/stats/export/recommend/remote-install/registry)
3. ✅ **v2.18.0**: Web Dashboard (`scripts/dashboard.sh`) — 零依赖 HTML 项目可视化面板
4. ✅ **v2.19.0**: VS Code Extension (`vscode-extension/`) — Activity bar + 8 命令 + Roles/Skills/Memory 树视图
5. ✅ **v2.20.0**: Online Dashboard (`docs/dashboard.html`) — [muse.mythslabs.ai/dashboard](https://muse.mythslabs.ai/dashboard) 100% 客户端专属面板
6. ✅ **官网同步**: index.html 版本 v2.15.0→v2.20.0，新增 "New in v2.20" section (3 张 feature cards)
7. ✅ **README/README_CN**: 新增 3 条 FAQ (Dashboard/Marketplace/VS Code Extension)
8. ✅ **P2 路线图全部完成** (Skill Marketplace + Web Dashboard + VS Code Extension)

**→GROWTH 行动项**:
- [ ] Show HN 帖子内容更新 (v2.20.0 功能增量: Marketplace + Dashboard + VS Code)
- [ ] Dev.to 文稿更新技术细节 (v2.20.0 + Online Dashboard)
- [ ] Product Hunt 文案更新 (Online Dashboard 是强博的 demo 点)
- [ ] 社媒推广新功能: "MUSE has a dashboard now" 类型帖子
- [ ] 小红书/X 发布 Dashboard 截图 + 使用教程
- [ ] 8 新 Launch 平台描述更新为 v2.20.0

### 2026-03-15 21:49 — BUILD→GROWTH 同步 (已更新 3/16 13:51)

**来源**: BUILD v2.12.0-v2.15.0 四版发布 (3/15)

**同步内容**:
1. ✅ **v2.12.0**: Auto Memory Capture (`/bye` 自动提取 LESSON/DECISION/FACT) + Agent Protocol spec (core skill #5)
2. ✅ **v2.13.0**: Skill Marketplace CLI (`skill-discovery.sh`) + `SKILL_INDEX.md` (56 skills 全量索引)
3. ✅ **v2.14.0**: T2 巩固三件套 — Semantic Compression + Session Checkpoint + Auto Profile
4. ✅ **v2.15.0**: MCP Server (`scripts/mcp-server.sh`) — 6 tools, JSON-RPC, QA 10/10 PASS
5. ✅ **QA 35/35 全 PASS** (v2.12.0→v2.15.0)
6. ✅ **muse.mythslabs.ai 落地页已上线** (GitHub Pages, 3/16)
7. ℹ️ **竞品定位**: MUSE 从 T3→T2 下游（保持纯 Markdown 零依赖）
8. ℹ️ **Skill 数量**: 48→56 (skill-discovery.sh 全量索引)

**→GROWTH 行动项**:
- [x] S042 目录提交用 v2.14.0+ 描述 ✅ (3/16 完成)
- [x] muse.mythslabs.ai 落地页上线 ✅ (3/16 BUILD 已部署)
- [x] Dev.to 文稿更新技术细节 (v2.15.0 + MCP Server + 56 skills) ✅ (3/16)
- [ ] Show HN 帖子内容更新 (v2.15.0 功能增量)

### 2026-03-14 16:11 — BUILD→GROWTH 同步

**来源**: BUILD v2.10.0 release (`445a87a`)

**同步内容**:
1. ✅ **v2.10.0 发布** — S035 SOP 同步 Bug 根因修复 + Demo 重制 + 🟡/✅ 指令过滤协议
2. ✅ **Demo 动画已重制** — 85帧/17秒，完整展示 `/resume` → boot → work → `/ctx` → `/bye`。文件: `assets/demo.{webp,gif,mp4}`
3. ✅ **S029/S035 战略指令已拉取** — QA SOP 修复 + SOP 同步 Bug 根因修复（跨项目绝对路径 + bye 强制 ls + 🟡/✅ 标记规则）
4. ℹ️ **当前版本 v2.10.0** — P0/P1 全清，QA 10/10 PASS，所有新功能已推送 origin/main

### 2026-03-13 10:47 — BUILD→GROWTH 同步

**来源**: BUILD 角色竞品分析 + v2.8.0 发布

**同步内容**:
1. 竞品分析完成: agency-agents (35.2K⭐) + paperclip (20.9K⭐) vs MUSE
2. v2.8.0 发布: `scripts/install.sh` 支持 6 工具一键安装
3. Growth 建议"暂缓 HN、先验 Reddit/X"已同步到渠道优先级
4. S027 发布渠道顺序已调整为: Reddit → X → HN（验证后）

**→GROWTH 行动项**:
- [x] 帖子内容加入 v2.8.0 多工具卖点
- [x] 竞品对比要点纳入叙事
- [ ] 优先准备 Reddit r/ClaudeAI 帖子（等解封）

</details>

---

## 📡 跨项目同步

| 指令 | 干什么 |
|------|--------|
| `/sync gm` | 读取 gm.md 获取项目优先级 |
| `/sync strategy` | 读取 `DYA/.muse/strategy.md` S019 战略指令 |

**路径约定**：
- MUSE 代码: `/Users/jj/Desktop/MUSE/`
- 战略: `/Users/jj/Desktop/DYA/.muse/strategy.md` → S019
### 📡 BUILD→GROWTH (2026-03-16 16:44) — v2.16→v2.20 同步

> **5 个新版本已发布，Growth 需更新营销素材**

| 版本 | 功能 | Growth 影响 |
|------|------|:-----------:|
| **v2.16.0** | `convert-skills.sh` — 56 skills 一键导出 6 格式 (Cursor/Windsurf/Copilot/OpenClaw/Aider/Antigravity) + agency-agents 35K 用户 prompt 吸收 | 🔴 切入 agency-agents 35K 用户池 |
| **v2.17.0** | Skill Marketplace — 6 发现命令 (categories/stats/export/recommend/remote-install/registry) | 🟡 新卖点 |
| **v2.18.0** | Web Dashboard — `scripts/dashboard.sh` → `.muse/dashboard.html` 本地可视化 | 🟡 Demo 素材 |
| **v2.19.0** | VS Code Extension — Activity bar + Roles/Skills/Memory tree views + 8 commands | 🔴 降低入门门槛 |
| **v2.20.0** | Online Dashboard — `muse.mythslabs.ai/dashboard` 在线版，客户端运行 | 🔴 展示 + 转化 |

**Growth 要做的**:
- [ ] 落地页新增 "New in v2.20" section ✅ (已由 BUILD 直接添加)
- [ ] llms.txt 更新 v2.20 features ✅ (JSON-LD 已更新)
- [ ] Reddit/PH/BiP 文案更新加入新功能
- [ ] Dev.to 文章更新加入 Dashboard + VS Code + Marketplace
- [ ] X Thread: "MUSE now has a VS Code extension" (新素材)


### Role: QA
**Current State**: `<!-- L0: 最近QA全PASS(10/10 v2.15.0 MCP Server), 无待修FAIL, 无待验AC, QA清洁状态 -->`

# 🔍 QA — Quality Assurance

> **Core Principle: The builder and the verifier must be different identities. Self-verification = no verification.**

## 🚀 How to Start QA (Quick Reference)

```
New conversation → /resume [project] qa → tell the Agent what to verify
```

**Three ways to start**:

| Scenario | What you say | Agent does |
|----------|-------------|------------|
| Strategy assigns QA | `/resume muse qa` → "Execute S0XX QA, AC in strategy.md S0XX details" | Read AC from strategy.md → verify → output Report |
| Build claims done | `/resume muse qa` → "Verify the features build completed" | Read build.md completed items → independently verify each → output Report |
| Pre-release regression | `/resume muse qa` → "Full regression for vX.Y" | Verify by coverage table → output Report |

**After QA**:
- ✅ PASS → Write to qa.md "Recent QA Results" + `/sync qa broadcast` (notify build + strategy)
- ❌ FAIL → Same + build must fix first, then re-verify

---

## 📋 QA SOP (Step-by-Step)

> Follow these 7 steps every QA. No skipping.

### Step 1: Confirm AC Source

| AC from | How to find |
|---------|-------------|
| Strategy assigns | User says "S0XX". `grep_search` strategy.md for `S0XX details`, read AC list |
| Build claims done | Read build.md completed items, each `[x]` item is verification scope |
| No explicit AC | **Ask the user**: "Please confirm acceptance criteria (AC), QA doesn't set AC, only verifies" |

### Step 2: Confirm Verification Environment

Before starting, list verification tools:
- 💻 **Terminal**: `setup.sh` / `install.sh` execution, file existence checks
- 📄 **File system**: Verify markdown content, YAML frontmatter, directory structure
- 🌐 **Browser**: README rendering on GitHub (if applicable)
- 🔧 **Git**: Verify commits, tags, changelog entries

> ⚠️ If verification environment is unavailable, **tell the user**, don't pretend you verified it.

### Step 3: Verify Each AC

**Every AC must**:
1. Actually execute the operation (not infer from reading code)
2. Attach evidence (terminal output / file content / screenshots)
3. Record ✅ or ❌ + reason

### Step 4: Test Error Paths

After all AC pass, **test at least 2 error scenarios**:
- Missing files / invalid input / wrong OS / missing dependencies
- Choose the most likely failure scenarios

### Step 5: Output QA Report

Use the QA Report template below. **Must list each AC's verification result and evidence**.

### Step 6: Verdict

- **PASS**: All AC ✅ + no P0 + error paths covered
- **FAIL**: Any AC ❌ or has P0 issue

### Step 7: Result Flow

| Result | Write where | Notify whom |
|:------:|-------------|-------------|
| ✅ PASS | qa.md "Recent QA Results" | build (task done) + strategy (progress) |
| ❌ FAIL | qa.md "Recent QA Results" + detailed FAIL reason | build (must fix first) + strategy |

**Flow method**: Use `/sync qa broadcast` or auto-sync during `/bye`.

---

## AC (Acceptance Criteria) Flow

> Strategy sets the exam, Build adds technical questions, QA grades. QA **never sets AC** — it only verifies.

| Phase | Who | Does what |
|:-----:|:---:|-----------|
| 1. Define task | **strategy** | Set business AC |
| 2. Add technical AC | **build** | Add technical acceptance criteria |
| 3. Implement | **build** | Write code, claim done |
| 4. Verify | **qa** | Verify each AC, output QA Report |
| 5. Fix | **build** | Fix based on QA Report |
| 6. Re-verify | **qa** | Re-verify failed items |

---

## Iron Rules (Non-negotiable)

1. **No self-verification** — build claiming done ≠ done, qa verification passing = done
2. **Evidence > Assertion** — each verification item must have verifiable evidence
3. **No surface verification** — "file exists" / "looks right" **is not QA**
4. **No selective verification** — can't only test happy path, must cover error paths
5. **Done = zero outstanding** — any known unfixed P0 = cannot claim "done"
6. **No fraud** — claiming verified when not = most serious violation
7. **QA is READ-ONLY** — QA only reports, never fixes. Found a bug → write QA Report + `/sync qa broadcast`, **never directly modify code**

---

## Coverage Scope (MUSE-specific)

| Category | ✅ Must verify (counts as QA) | ❌ Not QA (don't use to claim pass) |
|----------|-------------------------------|-------------------------------------|
| **setup.sh** | Actually run on clean directory → verify output | ~~"Script looks correct"~~ |
| **install.sh** | Run with each `--tool` flag → verify generated files | ~~"Code handles all cases"~~ |
| **Workflows** | Actually execute `/resume`, `/bye`, etc. → verify behavior | ~~"Markdown looks right"~~ |
| **Skills** | Verify YAML frontmatter + content complete | ~~"File exists"~~ |
| **Templates** | Verify placeholders get replaced correctly | ~~"sed command looks right"~~ |
| **README** | Verify links work, badges render, examples accurate | ~~"Checked the markdown"~~ |
| **Git** | Verify commit message, tag, changelog entry | ~~"Should be committed"~~ |

---

## QA Report Template

```markdown
## QA Report — [Task Name]
**Date**: YYYY-MM-DD
**Verifier**: qa identity (independent from build)
**Build Source**: [which commit / which version]
**AC Source**: [strategy.md S0XX / build.md completed items]

### AC Verification

| # | AC Description | Pass? | Evidence |
|---|---------------|:-----:|----------|
| 1 | setup.sh runs without error | ✅ | [terminal output] |
| 2 | /resume detects missing files | ❌ | [actual vs expected] |

### Error Paths

| Scenario | Expected | Actual | Pass? |
|----------|----------|--------|:-----:|
| Missing CLAUDE.md | Prompt to run /start | Crashes | ❌ |

### Issues Found

- 🔴 P0: [description] — must fix before done
- 🟡 P1: [description] — can log as TODO, doesn't block
- 🟢 P2: [description] — optimization suggestion

### Verdict

- [ ] ✅ **PASS** — All AC pass + no P0 + error paths covered
- [ ] ❌ **FAIL** — Route back to build → reason: [list failed ACs]
```

---

## Recent QA Results

> QA writes latest Report summary here. Expired results archived to `.muse/archive/qa_reports.md`.

### QA Report — BUILD→QA v2.15.0 MCP Server (10 ACs)
**Date**: 2026-03-15
**Verifier**: QA identity (independent conversation from build)
**Build Source**: v2.15.0 / main / commit `f631dfe`
**AC Source**: build.md §BUILD→QA (2026-03-15 v2.15.0)

#### AC Verification

| # | AC Description | Pass? | Evidence |
|---|---------------|:-----:|----------|
| AC1 | mcp-server.sh --help 输出 | ✅ | 终端执行: 输出含 "MUSE MCP Server" + `--project-root PATH` 选项说明 |
| AC2 | JSON-RPC initialize | ✅ | 终端执行: 返回 `serverInfo.name = "muse-memory-os"` + `capabilities.tools` |
| AC3 | tools/list 返回 6 工具 | ✅ | 终端执行: 6 tools (get_status/list_roles/get_role/send_directive/write_memory/search_memory), 每个含 name+description+inputSchema |
| AC4 | muse_get_status 读 L0 | ✅ | 终端执行: 返回 4 角色 L0 (`[build]`/`[gm]`/`[growth]`/`[qa]`), 与 `grep '<!-- L0:' .muse/*.md` 一致 |
| AC5 | muse_list_roles 含行数 | ✅ | 终端执行: `build (287 lines)`, `gm (94 lines)`, `growth (367 lines)`, `qa (223 lines)` + L0 摘要 |
| AC6 | muse_get_role 读完整文件 | ✅ | 终端执行: role=qa 返回 9316 chars, 首尾与 `cat .muse/qa.md` 一致 |
| AC7 | muse_search_memory 搜索 | ✅ | 终端执行: query="v2.14" → 12行结果 (MEMORIES.md+2026-03-15.md 含文件名+行号); query="v2.15" → 正确返回空 (memory 中确无此字符串) |
| AC8 | mcp-config.json 合法 JSON | ✅ | `python3 -m json.tool` 通过, 含 `mcpServers.muse.command` + `args` |
| AC9 | CHANGELOG v2.15.0 完整 | ✅ | `[2.15.0]` section 列出 MCP Server + 6 工具名 + 安全特性 |
| AC10 | README/README_CN MCP section | ✅ | README.md L351 MCP section + 6 工具 (6 matches) + config JSON + L435 v2.15.0; README_CN.md L281 + 6 工具 (6 matches) + L360 v2.15.0 |

#### Error Paths

| # | Scenario | Expected | Actual | Pass? |
|---|----------|----------|--------|:-----:|
| E1 | 路径遍历 `../../etc/passwd` | isError + 拒绝 | `isError:true` + "Invalid role name" + 建议合法名, 无文件内容泄露 | ✅ |
| E2 | 不存在的角色 `nonexistent` | isError + 列出可用角色 | `isError:true` + "Role file not found" + 列出 build/gm/growth/qa | ✅ |
| E3 | 无效 JSON 输入 | 不崩溃继续运行 | 无效行被静默跳过, 后续 id:3 请求正常返回 get_status 结果 | ✅ |

#### Issues Found

- 无 P0/P1/P2 issue。

#### Verdict

- [x] ✅ **PASS** — All 10 ACs pass + no P0 + error paths 3/3 covered

---

<details>
<summary>📦 历史 QA: v2.14.0 — 2026-03-15 — 15/15 PASS</summary>

15/15 AC ✅ + 3/3 Error Paths ✅ + 0 Issues
- Semantic Compression + Session Checkpoint + Auto Profile + skill-discovery.sh + SKILL_INDEX.md + CHANGELOG + README

</details>

<details>
<summary>📦 历史 QA: v2.12.0 — 2026-03-15 — 10/10 PASS</summary>

10/10 AC ✅ + 2/2 Error Paths ✅ + 0 Issues
- Auto Memory Capture (bye.md Step 4.7) + Agent Protocol (SKILL.md) + distill.md + CHANGELOG + README

</details>

<details>
<summary>📦 历史 QA: v2.3 — 2026-03-13 — 10/10 PASS</summary>

10/10 AC ✅ (cursorrules / archive-memory / install.sh / setup.sh / README×2 / resume.md / qa.md)

</details>

---

*MUSE QA v1.0 — Evidence > Assertion, always.*


---

## Core Skills
### Skill: agent-protocol

# Agent Protocol Specification

> Inspired by MemOS (multi-agent isolation + sharing) and multi-agent-memory (cross-agent persistence).
> Adapted for MUSE's pure Markdown zero-dependency architecture.
> Added in v2.12.0 (Batch 2 — competitive tech absorption).

## Why

MUSE role files (`.muse/*.md`) currently work because AI Agents read Markdown and follow instructions. But as the ecosystem evolves toward multi-agent workflows (MCP servers, Claude Projects, multi-tool chains), role files need a **machine-readable protocol** — not just human-readable documents.

**Problems this solves**:
1. **Agent handoff**: When switching between Agents (e.g., Claude → Gemini), context should be portable
2. **Multi-agent coordination**: Multiple Agents working on the same project should respect role boundaries
3. **Tool interoperability**: MCP servers, IDE plugins, and CLI tools should be able to read/write role files

## Protocol: MUSE Role File Spec v1.0

### File Discovery

```
.muse/
├── strategy.md    # Strategy role
├── build.md       # Build/Dev role
├── growth.md      # Growth/Marketing role
├── qa.md          # QA/Verification role
├── gm.md          # General Manager role
├── ops.md         # Operations role
├── research.md    # Research role
├── fundraise.md   # Fundraise role
└── archive/       # Archived content (not loaded)
```

**Discovery rule**: Any `.md` file in `.muse/` (excluding `archive/`) = a role file.

### L0 Header (Machine-Readable Status Line)

Every role file MUST have an L0 comment as its **first line**:

```
<!-- L0: {version} | {top_priority} | {status_flags} -->
```

**Parsed fields**:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `version` | semver | Current project version | `v2.11.0` |
| `top_priority` | string | Most important current task | `P0=竞品技术吸收Batch2` |
| `status_flags` | csv | Comma-separated status indicators | `QA PASS, 3 pending directives` |

**L0 is the Agent's "at a glance" API** — any tool can grep all L0 lines to get project status in ~400 tokens.

### Section Protocol

Role files use Markdown headers as **semantic sections**. Tools should parse these:

| Section Header Pattern | Semantic Meaning | Agent Action |
|----------------------|-----------------|--------------|
| `## 📐 职责边界` | Role boundaries table | Respect: only act within listed responsibilities |
| `## ⏳ 待办` / `## 🎯 TODO` | Pending tasks | Read for context; update checkboxes when completing |
| `## 📡 已接收战略指令` | Received directives | Check for pending work from other roles |
| `## 📡 QA→BUILD 通知` | Cross-role notifications | Process before starting new work |
| `## 🛠️ 技术栈` | Technology constraints | Respect in all code generation |
| `## 📋 CHANGELOG 维护规则` | Process rules | Follow during releases |

### Directive Protocol (📡)

Directives are the **message-passing API** between roles:

```
📡 **S{NNN}→{TARGET}**: {STATUS} **{TITLE}**
> {BODY}
```

| Field | Format | Example |
|-------|--------|---------|
| `S{NNN}` | Sequential ID | `S041` |
| `{TARGET}` | `ROLE` or `PROJECT/ROLE` | `MUSE/BUILD`, `GROWTH` |
| `{STATUS}` | 🟡 (pending) / ✅ (received) | `🟡` = needs pickup |
| `{TITLE}` | One-line summary | `竞品深度调研回传` |
| `{BODY}` | Blockquote detail | Full directive content |

**Pickup protocol**:
1. Target role's `/resume` scans for 🟡 directives
2. On pickup: write to role file's `📡 已接收战略指令` section
3. Change source 🟡 → ✅ with timestamp

### Memory Protocol

```
memory/
├── YYYY-MM-DD.md   # Daily log (short-term, raw)
├── archive/        # Old logs
MEMORIES.md          # Long-term knowledge (distilled + auto-captured)
```

| Memory Type | File | Write Method | Read Method |
|------------|------|-------------|------------|
| **Short-term** | `memory/YYYY-MM-DD.md` | `/bye` Step 4 | `/resume` Step ② |
| **Long-term** | `MEMORIES.md` | `/distill` (batch) + `/bye` Step 4.7 (auto-capture) | `/resume` Step ① |
| **Constitutional** | `CLAUDE.md` | Manual | Always loaded |
| **User prefs** | `USER.md` | `/settings` | `/resume` Step ④ |

### Isolation Rules

```
┌─────────────────────────────────────────────┐
│ Agent Session (e.g., /resume build)         │
│                                             │
│  ✅ CAN READ:                               │
│  - Own role file (.muse/build.md)           │
│  - L0 lines of ALL role files               │
│  - memory/*.md                              │
│  - MEMORIES.md, CLAUDE.md, USER.md          │
│  - Source code & docs (on demand)           │
│                                             │
│  ✅ CAN WRITE:                               │
│  - Own role file                            │
│  - memory/YYYY-MM-DD.md                     │
│  - MEMORIES.md (auto-capture only)          │
│  - Source code (if build/dev role)           │
│                                             │
│  ❌ MUST NOT:                                │
│  - Write to other role files directly       │
│  - Create files outside .muse/ convention   │
│  - Discuss other roles' topics in depth     │
│                                             │
│  📡 CROSS-ROLE COMMS:                        │
│  - Only via directive protocol (📡 S{NNN})  │
│  - Sender writes directive to OWN file      │
│  - Receiver picks up during /resume         │
└─────────────────────────────────────────────┘
```

### Multi-Project Protocol

For users managing multiple projects:

```
~/ProjectA/.muse/build.md     ← ProjectA's build role
~/ProjectB/.muse/build.md     ← ProjectB's build role
~/ProjectA/.muse/strategy.md  ← May hold cross-project directives
```

**Cross-project directives** use `PROJECT/ROLE` targeting:
```
📡 S041→MUSE/BUILD: 🟡 ...    ← Targets MUSE project's BUILD role
📡 S040→DYA/GROWTH: ✅ ...     ← Targets DYA project's GROWTH role
```

**Path resolution**: `CLAUDE.md` MAY specify absolute paths for cross-project strategy files:
```markdown
> strategy.md 绝对路径: `/Users/jj/Desktop/DYA/.muse/strategy.md`
```

## Integration Points

### For MCP Servers

An MCP server implementing MUSE protocol is **included** — see `scripts/mcp-server.sh` (added in v2.15.0).

| Tool | Description | Status |
|------|-------------|:------:|
| `muse_get_status` | Read all L0 lines → return project status | ✅ |
| `muse_list_roles` | List role files with summaries | ✅ |
| `muse_get_role` | Read a specific role file (L1) | ✅ |
| `muse_send_directive` | Create a 📡 directive in a role file | ✅ |
| `muse_write_memory` | Append to today's memory file | ✅ |
| `muse_search_memory` | Search across memory files + MEMORIES.md | ✅ |

**Configuration**: Add to your MCP client config:
```json
{
  "mcpServers": {
    "muse": {
      "command": "/path/to/muse/scripts/mcp-server.sh",
      "args": ["--project-root", "/path/to/project"]
    }
  }
}
```

### For CLI Tools

```bash
# Get project status (all L0 lines)
grep "<!-- L0:" .muse/*.md

# Check for pending directives
grep "🟡" /path/to/strategy.md

# Count role file lines (bloat check)
wc -l .muse/*.md
```

### For IDE Plugins

- **Status bar**: Show L0 summary of current role
- **Sidebar**: List pending directives (🟡)
- **On save**: Auto-update L0 line if role file changed

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.1 | 2026-03-15 | MCP server implemented (`scripts/mcp-server.sh`) |
| v1.0 | 2026-03-15 | Initial spec (Batch 2) |



### Skill: context-health-check

# Context Health Check

When this skill is triggered, perform the following assessment and output a report.

## Token Estimation Method

LLMs cannot directly read consumed token counts. Use these proxy formulas:

### Estimation Formula

```
Consumed ≈ System Overhead + Σ(Per-turn Consumption)

System Overhead ≈ 15K-25K tokens (system prompt + skills metadata + workspace info)

Per-turn Consumption ≈ User message (~200-500) 
           + Tool call results (each ~500-5000, large file reads ~3000-8000)
           + Assistant response (~500-2000)
```

### High-Consumption Operation Reference

| Operation | Estimated Tokens |
|-----------|:---------------:|
| Read <100 line file | ~500-1500 |
| Read 200-500 line file | ~3000-5000 |
| Read 500+ line file (e.g. STATUS.md) | ~5000-10000 |
| grep search results (50 matches) | ~3000-5000 |
| Long command output | ~2000-8000 |
| Generate/edit a file | ~1000-3000 |
| Browser operations (with DOM) | ~5000-15000 |

### Model Context Windows

| Model | Total Window | Available (minus overhead) | Safety Threshold (80%) |
|-------|:-----------:|:-------------------------:|:---------------------:|
| Claude Opus/Sonnet (Anthropic) | 200K | ~175K | **140K** |
| GPT-4o (OpenAI) | 128K | ~105K | **84K** |
| Gemini Pro (Google) | 1M+ | ~950K+ | **Unlikely to overflow** |

⚠️ **MUST read `USER.md` `model preference` field first.** If found, use that model's window size. If not found, default to Claude 200K. **Do NOT default to Gemini 1M or other models.**

## Assessment Process

1. **Identify current model** (read `USER.md` → `model preference` field. If not found, default to Claude 200K. **Do not guess, do not use Gemini 1M**)
2. **Count conversation turns** (user↔assistant interaction count)
3. **Estimate tool call token consumption** (accumulate per the table above)
4. **Calculate total estimated consumption**
5. **Calculate remaining percentage** = (available window - consumed) / available window
6. **Assign health level**

## Health Levels

| Level | Remaining % | Recommendation |
|:----:|:----------:|----------------|
| 🟢 **Healthy** | >50% remaining | Continue working, no concerns |
| 🟡 **Caution** | 20-50% remaining | Finish current task then start a new conversation. Avoid loading more large files. Avoid long output commands |
| 🔴 **Danger** | <20% remaining | ⚠️ Immediately update status files and start a new conversation. Continuing will likely cause forgetting/repetition/quality degradation |

### Quick Judgment Rules of Thumb (when you don't want to calculate)

For Claude 200K window:
- **≤5 turns + 1 large file** → 🟢 
- **10-15 turns + 2-3 large files + multiple code edits** → 🟡
- **>18 turns** or **>5 large file reads** or **starting to forget early content** → 🔴

## Output Format

```
## 🧠 Context Health Check

**Model**: [Claude/GPT-4o/Gemini/...] (context window XK)

| Metric | Current Value | Estimated Tokens |
|--------|:------------:|:----------------:|
| System overhead | — | ~20K |
| Conversation turns | X turns | ~YK |
| Large file reads | [list files + line counts] | ~ZK |
| Tool calls | ~N calls | ~WK |
| **Total estimated** | — | **~TK** |
| **Remaining estimated** | — | **~RK (P%)** |

**Health Level**: 🟢/🟡/🔴

**Recommendation**: [specific advice]
**Estimated remaining capacity**: ~M normal turns / ~L large file reads
```

## Defensive Auto-Save

> **Core problem**: 🔴 detection depends on the Agent having an opportunity to execute — when context suddenly overflows, the Agent has no chance to save anything.
> **Solution**: Don't wait for 🔴 — proactively save every 10 turns.

### Rules

1. **Every 10 interaction turns** (one user↔assistant round = 1 turn), Agent **MUST** silently update `memory/CRASH_CONTEXT.md`
2. **Silent = don't interrupt the user**. No announcement needed, no confirmation needed. Complete during response or between tool calls
3. **Incremental update**: Only update changed fields, don't full-rewrite
4. **Format** matches what's written during 🔴 detection (see Additional Rule #1 below)
5. **Delete after recovery**: After `/resume crash` successfully recovers, delete `CRASH_CONTEXT.md` (avoid stale data)
6. **Trigger timing checklist**:
   - Turn 10 → First write ✅
   - Turn 20 → Update ✅
   - Turn 30 → Update ✅ (usually approaching 🟡/🔴 by now)
   - 🔴 detection triggered → Final update (including "suggested next steps") ✅

### Defense Layers

| Layer | Trigger Condition | Reliability |
|:-----:|-------------------|:----------:|
| **L0 Defense** | Silent save every 10 turns | ⭐⭐⭐ Most reliable |
| **L1 Warning** | Auto-save when `/ctx` detects 🔴 | ⭐⭐ Needs detection opportunity |
| **L2 Fallback** | `/resume crash` scans `convo/` for _CRASH files | ⭐ Safety net |

## Additional Rules

1. When 🔴 danger is detected, **automatically** execute memory snapshot + crash recovery file (MUSE compact:before protocol):
   - Write current progress to `memory/YYYY-MM-DD.md` (don't wait for user /bye)
   - Update `task.md` progress markers
   - **Write `memory/CRASH_CONTEXT.md`** (structured recovery file, auto-read by next `/resume crash`):
     ```markdown
     # Crash Context — YYYY-MM-DD HH:MM
     ## Current Role: [strategy/build/growth/qa]
     ## Current Task: [what was being done]
     ## Unfinished: [list]
     ## Key Decisions: [decisions made this session]
     ## User's Last Question: [if any]
     ## Suggested Next Steps: [what to do after recovery]
     ```
   - Then notify the user:
     ```
     ⚠️ Context is about to overflow! Auto-saved:
     - memory/YYYY-MM-DD.md ✅
     - memory/CRASH_CONTEXT.md ✅
     Please end this conversation. Use `/resume crash` in a new conversation to auto-recover.
     To export this conversation, save to: convo/YYMMDD/YYMMDD-NN-desc_CRASH.md
     ```
2. If current conversation has not loaded any status files and is ≤3 turns, report 🟢 directly without detailed calculation
3. Natural language triggers also apply ("how much context left?", "context enough?", etc.)
4. If you detect yourself forgetting early conversation content or repeating yourself, even if the formula says there's room left, report 🔴 directly

## 🆕 Session Checkpoint (v2.14.0 — OpenViking-inspired)

> Inspired by OpenViking's session compression — auto-checkpoint mid-conversation to prevent context loss.
> Complements Defensive Auto-Save (CRASH_CONTEXT.md): Auto-Save = crash recovery safety net, Session Checkpoint = quality preservation.

### Why

Long conversations degrade quality because the Agent loses track of early context. By the time `/bye` runs, the Agent may have already forgotten 50-80% of early work. Session Checkpoint writes compressed mid-session snapshots to preserve context fidelity.

### When to Checkpoint

| Trigger | Action |
|---------|--------|
| **Every 15 turns** | Silent checkpoint (no user notification) |
| **After a major milestone** (commit, deploy, release, version bump) | Silent checkpoint |
| **When /ctx detects 🟡** | Checkpoint + notify user |
| **When switching topics** (user asks about something unrelated to current work) | Silent checkpoint |

### What to Write

**File**: `memory/YYYY-MM-DD.md` (append, not overwrite)

**Format** (compressed — use Semantic Compression rules from `/bye`):
```markdown
## 📍 Checkpoint (HH:MM, ~turn N)
- 主线: [1-2 sentence summary of work so far]
- 决策: [key decisions if any]
- 状态: [current task status]
```

### Rules

1. **Silent**: Do NOT announce checkpoints to the user. Do NOT ask for confirmation. Write silently between tool calls
2. **Append-only**: Never overwrite existing memory content. Always append
3. **Compressed**: Use the 5:1 compression ratio — max 3-4 lines per checkpoint
4. **Idempotent**: If the same milestone was already checkpointed, skip (check last checkpoint's content)
5. **No performance impact**: Checkpoint during response generation or between tool calls, never adding a delay
6. **Checkpoint counter**: Track `_checkpoint_count` mentally. First checkpoint = turn ~15, then every ~15 turns after

### Interaction with Other Systems

| System | Relationship |
|--------|-------------|
| **Defensive Auto-Save** (CRASH_CONTEXT.md) | Auto-Save = full structured snapshot for crash recovery. Checkpoint = lightweight append for quality preservation. Both can coexist |
| **`/bye` Step 1** | `/bye` should READ checkpoints to reconstruct full session history (prevents the 80% forgetting problem) |
| **`/bye` Step 4** | Final memory write should reference checkpoints: "See checkpoints at HH:MM, HH:MM" |
| **`/resume`** | Checkpoints appear as part of daily memory — no special handling needed |



### Skill: layered-context

# Layered Context Loading Protocol

> Inspired by OpenViking (ByteDance) L0/L1/L2 architecture.
> Adapted for MUSE's pure Markdown zero-dependency design.

## Why

Full-loading all `.muse/*.md` files during `/resume` wastes tokens when the Agent only needs one role's context. The layered approach loads minimum context first, then deepens on demand.

## Three Layers

| Layer | Token Budget | Content | When to Load |
|:-----:|:-----------:|---------|-------------|
| **L0** | ~100 tokens | One-line HTML comment at top of each `.muse/*.md` | **Always** — scan ALL role files |
| **L1** | ~2K tokens | Full role file content | **On demand** — only the CURRENT role's file |
| **L2** | Unbounded | `memory/*.md` + code files + docs | **On demand** — grep search when needed |

## L0 Format

Every `.muse/*.md` file MUST have an L0 comment as the **first line**:

```html
<!-- L0: v2.10.1 | P0=竞品技术吸收, P1/P2全清, QA PASS, S036已接收 -->
```

### L0 Content Rules

1. **Max 120 characters** (excluding `<!-- L0: ` and ` -->`)
2. **Must include**: current version + top priority + blocking issues
3. **Pipe-separated** sections: `version | priorities | status`
4. **Updated every /bye** — when the role file is synced

### L0 Examples

```html
<!-- L0: v2.10.1 | P0=竞品技术吸收(mem0/OpenViking), P1全清, QA 10/10 PASS -->
<!-- L0: 9/9渠道已发, Show HN暂缓, S040梗图排期中, Stars=2 -->
<!-- L0: 最近QA全PASS(10/10 v2.3), 无待修FAIL, QA清洁状态 -->
```

## Boot Sequence with Layered Loading

```
/resume [role]
  │
  ├─① Read CLAUDE.md + MEMORIES.md (constitutional layer, always)
  │
  ├─② Scan ALL .muse/*.md L0 lines (grep "<!-- L0:" .muse/*.md)
  │   → Get one-liner status of every role in ~400 tokens total
  │
  ├─③ Deep-read CURRENT role's .muse/*.md (L1, full file)
  │   → Only the file matching /resume [role]
  │
  ├─④ Scan memory/ for unfinished items (L2, on demand)
  │   → grep 🔲 and [ ] in recent memory files
  │
  └─⑤ grep strategy.md for 🟡 directives (L2, on demand)
      → Only if non-strategy role
```

## Decision Tree: When to Upgrade

```
Agent receives a question/task
  │
  ├─ Can answer from L0? → Answer immediately
  │   (e.g., "What version is MUSE?" → L0 has it)
  │
  ├─ Need role details? → Load L1 (full role file)
  │   (e.g., "What's the P0 task?" → need build.md details)
  │
  └─ Need historical context? → Load L2 (memory/grep)
      (e.g., "What did we decide about X last week?" → grep memory/)
```

## Maintaining L0

### Who Updates L0

The **`/bye` workflow** updates L0 as part of Step 3.5 (role file sync):
1. After syncing the role file content
2. Rewrite the L0 comment to reflect current state
3. Keep within 120 char limit

### L0 Staleness Detection

If the L0 comment's version doesn't match the latest tag, the `/resume` boot should flag it:
```
⚠️ L0 stale: build.md says v2.10.1 but latest tag is v2.11.0
```


### Skill: semantic-search

# Semantic Search

Search across your entire MUSE project context using TF-IDF ranking.

## When to Use

- User asks "where did we discuss X?"
- User wants to find a past decision or lesson
- User needs to locate a specific skill
- Context recovery when resuming work

## Usage

```bash
# Search everything
./scripts/search.sh "auth jwt oauth"

# Search only memory files
./scripts/search.sh "database migration" --scope memory

# Search only role files
./scripts/search.sh "dashboard" --scope roles --top 3

# Search only skills
./scripts/search.sh "testing" --scope skills --top 10
```

## How It Works

1. **Tokenization**: Query is split into lowercase terms
2. **TF (Term Frequency)**: For each file, count occurrences of each query term, normalized by file length
3. **IDF (Inverse Document Frequency)**: Terms that appear in fewer files get higher weight
4. **Score**: TF × IDF summed across all query terms
5. **Ranking**: Files sorted by score, top N shown with best-matching line as context snippet

## Scopes

| Scope | Files Indexed |
|-------|--------------|
| `all` (default) | memory/ + .muse/ + MEMORIES.md + skills/ |
| `memory` | memory/*.md + MEMORIES.md |
| `roles` | .muse/*.md |
| `skills` | skills/**/SKILL.md + .agent/skills/**/SKILL.md |

## Integration

When resuming a conversation, you can use search to quickly find relevant context:

```bash
# Before /resume — find what was done last week
./scripts/search.sh "migration deploy" --scope memory --top 3
```

## Limitations

- Pure TF-IDF, no semantic understanding (no embeddings/vectors)
- Exact term matching only (no synonyms)
- Best for keyword-based queries with specific terms
- For semantic search, consider integrating with mem0 or memsearch


### Skill: strategic-compact

# Strategic Compact Skill

Suggests manual `/compact` at strategic points rather than relying on arbitrary auto-compaction.

## Why Strategic Compaction?

Auto-compaction triggers at arbitrary points:
- Often mid-task, losing important context
- No awareness of logical task boundaries
- Can interrupt complex multi-step operations

Strategic compaction at logical boundaries:
- **After exploration, before execution** — Compact research, keep plan
- **After completing a milestone** — Fresh start for next phase
- **Before major context shifts** — Clear old context before different task

## Focus-Aware Compaction (inspired by OpenClaw)

Blind compaction = blind discards. Focus-directed compaction = preserving key information.

**Usage**: Specify what to preserve when manually compacting.

```
Scenario: Completed 3 hours of debugging, now starting a new feature
✅ /compact preserve root cause analysis and fix approach, discard trial-and-error debugging
❌ /compact (blind compaction may discard root cause analysis)
```

**Common focus templates**:

| Scenario | Focus Directive |
|----------|----------------|
| After debugging | `Preserve root cause and fix approach, discard trial-and-error` |
| After planning | `Preserve final plan and key decisions, discard alternative discussions` |
| After code review | `Preserve items to change, discard confirmed-OK sections` |
| After strategy discussion | `Preserve strategic decisions and metrics, discard brainstorming process` |
| After multi-file edits | `Preserve which files changed and why, discard file content details` |

## When to Trigger Compaction

| Signal | Action |
|--------|--------|
| Completed a full milestone | ✅ Good time to compact |
| Switching from exploration to execution | ✅ Good time to compact |
| Debugging complete, starting new feature | ✅ Good time to compact |
| In the middle of multi-step implementation | ❌ Do NOT compact |
| Still analyzing a problem | ❌ Do NOT compact |
| `/ctx` shows 60-70% consumed | 🟡 Consider compacting |
| `/ctx` shows ≥ 80% consumed | 🔴 Must exit (constitution rule) |

## Hook Setup

Add to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "tool == \"Edit\" || tool == \"Write\"",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/skills/strategic-compact/suggest-compact.sh"
      }]
    }]
  }
}
```

## Configuration

Environment variables:
- `COMPACT_THRESHOLD` - Tool calls before first suggestion (default: 50)

## Best Practices

1. **Compact with focus** — Always specify what to preserve, never compact blindly
2. **Write memory before compacting** — Save key information to `memory/YYYY-MM-DD.md` first
3. **Never compact mid-task** — Maintain complete context during multi-step implementations
4. **Pair with /ctx** — 60-70% consider compacting, ≥ 80% must exit

## Pre-Compaction Protocol (MUSE — derived from LCM compact:before)

**MUST** execute in order before compaction:
1. **Persist**: Write current task progress to `memory/YYYY-MM-DD.md`
2. **Mark protected zone**: Mark last 5 conversation turns as "non-compactable" (≈ LCM freshTailCount=32)
3. **Extract key decisions**: Scan content about to be compacted, extract key decisions/data to memory
4. **Notify user**: Inform about upcoming compaction, list what will be preserved

> **Principle: Persist first, then compact. Never discard information without a backup.**

## Post-Compaction Injection (MUSE — derived from OpenClaw postCompactionSections)

**MUST** re-internalize the following after compaction:
1. First 4 lines of `CLAUDE.md` (7 iron laws + priority chain)
2. Currently `[/]` in-progress tasks from `task.md`
3. Today's `memory/` snapshot (just written)
4. Any focus-aware specified preservation items

> **Principle: Compaction ≠ forgetting. Core identity and current context must be restored immediately after compaction.**


### Skill: using-superpowers

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## How to Access Skills

**In Claude Code:** Use the `Skill` tool. When you invoke a skill, its content is loaded and presented to you—follow it directly. Never use the Read tool on skill files.

**In other environments:** Check your platform's documentation for how skills are loaded.

# Using Skills

## The Rule

**Invoke relevant or requested skills BEFORE any response or action.** Even a 1% chance a skill might apply means that you should invoke the skill to check. If an invoked skill turns out to be wrong for the situation, you don't need to use it.

```dot
digraph skill_flow {
    "User message received" [shape=doublecircle];
    "Might any skill apply?" [shape=diamond];
    "Invoke Skill tool" [shape=box];
    "Announce: 'Using [skill] to [purpose]'" [shape=box];
    "Has checklist?" [shape=diamond];
    "Create TodoWrite todo per item" [shape=box];
    "Follow skill exactly" [shape=box];
    "Respond (including clarifications)" [shape=doublecircle];

    "User message received" -> "Might any skill apply?";
    "Might any skill apply?" -> "Invoke Skill tool" [label="yes, even 1%"];
    "Might any skill apply?" -> "Respond (including clarifications)" [label="definitely not"];
    "Invoke Skill tool" -> "Announce: 'Using [skill] to [purpose]'";
    "Announce: 'Using [skill] to [purpose]'" -> "Has checklist?";
    "Has checklist?" -> "Create TodoWrite todo per item" [label="yes"];
    "Has checklist?" -> "Follow skill exactly" [label="no"];
    "Create TodoWrite todo per item" -> "Follow skill exactly";
}
```

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Skill Priority

When multiple skills could apply, use this order:

1. **Process skills first** (brainstorming, debugging) - these determine HOW to approach the task
2. **Implementation skills second** (frontend-design, mcp-builder) - these guide execution

"Let's build X" → brainstorming first, then implementation skills.
"Fix this bug" → debugging first, then domain-specific skills.

## Skill Types

**Rigid** (TDD, debugging): Follow exactly. Don't adapt away discipline.

**Flexible** (patterns): Adapt principles to context.

The skill itself tells you which.

## User Instructions

Instructions say WHAT, not HOW. "Add X" or "Fix Y" doesn't mean skip workflows.


### Skill: verification-before-completion

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.


## Phase 0: AC-First Workflow (Before Writing Code)

> 💡 Inspired by opslane/verify: "You can't trust what an agent produces unless you told it what 'done' looks like before it started."

**Before writing any code, define Acceptance Criteria:**

```markdown
## Acceptance Criteria

### AC-1: [Feature/behavior name]
- [Observable outcome 1]
- [Observable outcome 2]

### AC-2: [Edge case / error handling]
- [What user sees]
- [What system does]

### AC-3: [Integration / compatibility]
- [Works with X]
- [Doesn't break Y]
```

**AC Writing Rules:**
- Each AC must be **independently verifiable** (pass or fail, no "partially")
- Use **observable behavior** not implementation details ("User sees X" not "Code calls Y")
- Include **negative cases** (what happens when things go wrong)
- For frontend: specify exact text, navigation, visual state
- For backend: specify status codes, response shape, error messages
- For mobile: specify platform behavior, i18n, haptics

**When to write ACs:**
- ✅ Before ANY new feature (even "simple" ones)
- ✅ Before bug fixes (AC = "original symptom no longer occurs" + "no regression")
- ✅ Before refactors (AC = "all existing behavior preserved")
- ❌ NOT needed for: config changes, docs-only, status file updates


## Phase 1: Pre-Flight Check (Zero-Cost Fast Fail)

> 💡 Pure checks, no LLM tokens. Fail fast before spending effort.

**Before starting work, verify preconditions:**

```
PRE-FLIGHT CHECKLIST (30 seconds, zero tokens):
□ Dev server running? (or can it start?)
□ Target files exist and are accessible?
□ Dependencies installed? (node_modules, Pods, etc.)
□ Auth/session valid? (Supabase, App Store Connect, etc.)
□ Branch correct? (not accidentally on main when should be feature)
□ Previous build clean? (no leftover errors)
```

**If any pre-flight fails → FIX IT FIRST, don't start the feature.**

This prevents the classic failure: spending 30 minutes coding, then discovering the dev server was down the whole time.


## Phase 2: The Gate Function (After Execution)

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```


## Phase 2.5: Deep QA Loop (Anti-Fraud · Infinite Loop)

> ⚠️ **Lesson learned**: Agent claimed "QA 100% passed" multiple times, but actually only checked whether pages loaded (HTTP 200) and API status codes.
> Frontend worked but core functionality (TTS/payments/WebSocket) was never truly verified. This is not QA — this is **fraud**.

### What Does NOT Count as QA (NEVER claim QA passed using these)

| Shallow Check | Why It Doesn't Count |
|--------------|---------------------|
| Page returns HTTP 200 | Only proves page loads, not that features work |
| API returns correct status code | Only proves route exists, not that business logic is correct |
| `next build` / `expo prebuild` exit 0 | Only proves compilation passes, not runtime behavior |
| Dev server console has no errors | Not triggered ≠ no bugs |
| "Looks like no errors" | Not looking ≠ no errors |
| "Visual check passed" | Didn't look at screenshots, only read code ≠ visual pass |

### What Counts as Deep QA (ALL must be done)

- ✅ **Every user interaction flow** actually walked through (click buttons, submit forms, trigger animations, complete chat round-trips)
- ✅ **Every API call** verified for request body + response content (not just status code — check if returned data is correct)
- ✅ **Every state change** verified for correct UI updates (loading→success→idle, error messages appearing/disappearing)
- ✅ **Every integration point** verified end-to-end (frontend→API→database→response→UI update, full chain)
- ✅ **Error paths** must be tested (no network, no permissions, empty data, invalid input, timeouts)
- ✅ **Auth-required features** tested with real authentication state (cannot skip saying "needs manual testing")
- ✅ **Media features** (TTS/voice/video) must be actually triggered and output confirmed (cannot just check if API responds)

### QA Loop Rules

```
Deep QA → find issues → fix → Deep QA → find issues → fix → Deep QA → ...
→ ALL 100% zero issues → only then can you say "done"
```

- ❌ 1 FAIL → not allowed to say "done"
- ❌ "Needs manual testing" → if automatable then automate, if not then use browser tools/curl to actually test
- ❌ "Not a blocker" → any user-perceivable issue IS a blocker
- **Violating this rule = same severity as "fake functionality" = most critical bug**


## Phase 3: Judge Verdict (Structured Judgment)

> 💡 Inspired by opslane/verify's Judge pattern: separate execution from judgment.

**After verification, produce a structured verdict for each AC:**

```markdown
## Verification Report

| AC | Verdict | Evidence |
|----|---------|----------|
| AC-1: Login redirect | ✅ PASS | `curl -s -o /dev/null -w "%{http_code}" → 302` |
| AC-2: Error message | ✅ PASS | Screenshot shows "Invalid email or password" |
| AC-3: Rate limiting | ❌ FAIL | 6th attempt still allowed (expected: blocked) |
| AC-4: i18n | 🟡 NEEDS-REVIEW | Translation exists but quality unverified |

**Overall: 2/4 PASS, 1 FAIL, 1 NEEDS-REVIEW**
**Verdict: NOT READY — AC-3 must be fixed before completion**
```

**Three verdict types:**
- **✅ PASS** — Evidence confirms AC is met
- **❌ FAIL** — Evidence shows AC is NOT met (must fix)
- **🟡 NEEDS-REVIEW** — Cannot be automatically verified (needs human check)

**Rules:**
- NEVER mark PASS without evidence
- FAIL requires specific description of what went wrong
- NEEDS-REVIEW is for visual/UX/copy that can't be command-verified
- **Overall verdict = FAIL if ANY AC is FAIL**


## Common Verification Methods

| What to verify | Method | Not sufficient |
|---------------|--------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line AC checklist | Tests passing |
| API endpoint | `curl` with expected status/body | "Code looks right" |
| UI behavior | Browser screenshot/recording | "Component renders" |
| i18n complete | Grep all locale files for key | "Added to en.json" |
| Mobile build | `npx expo prebuild` exit 0 | "No errors in editor" |

## Red Flags — STOP Immediately

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!")
- About to commit/push/PR without verdict report
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- **ANY wording implying success without having run verification**
- **Skipping AC writing because task "seems simple"**
- **Mentally marking AC as PASS without running the check**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "Too simple for ACs" | Simple tasks have simple ACs — write them anyway |
| "ACs slow me down" | Rework from false completion is slower |
| "Partial check is enough" | Partial proves nothing |

## Quick Reference: Full Workflow

```
┌─────────────────────────────────────────┐
│ 1. DEFINE ACs (before coding)           │
│    What does "done" look like?          │
├─────────────────────────────────────────┤
│ 2. PRE-FLIGHT (before coding)           │
│    Dev server? Files? Deps? Branch?     │
├─────────────────────────────────────────┤
│ 3. EXECUTE (write code)                 │
│    Build the feature / fix the bug      │
├─────────────────────────────────────────┤
│ 4. GATE (after coding)                  │
│    Run verification commands            │
├─────────────────────────────────────────┤
│ 5. JUDGE (before claiming done)         │
│    Produce verdict per AC               │
│    ALL PASS → claim completion          │
│    ANY FAIL → fix and re-verify         │
│    ANY NEEDS-REVIEW → flag for human    │
└─────────────────────────────────────────┘
```

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**The Bottom Line:**

No shortcuts for verification. Define ACs. Run pre-flight. Execute. Verify. Judge. THEN claim the result.

This is non-negotiable.


