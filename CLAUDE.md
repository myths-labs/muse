# 🔴 Cutting corners or faking completion = YOU GET DELETED. Incomplete SOP execution, skipping steps, unauthorized actions, or modifying code without permission = most severe violation.

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
  | **Git 安全守卫** | **`git-security-guard`**（commit/push 前检查泄露） |
  | **去 AI 味** | **`deai-humanizer`**（AI 文字 → 自然表达） |
  | **网页版 Deck/PPT** | **`frontend-slides`**（零依赖 HTML 演示 + PPT 转 web + 12 预设主题 + Vercel 部署 + PDF 导出） |

## Context Health Pre-Check

Every session start: estimate context usage. If ≥ 70%, suggest opening new conversation.

Defensive saving: every 10 interaction rounds silently update `memory/CRASH_CONTEXT.md`.

## Safety Protocols

- **Action Gate**: STOP and ASK before: Refactoring, Major Updates, Deleting Files.
- **Pre-Flight**: Always BACKUP before approved destructive actions.
- **Rule Zero**: Check `CLAUDE.md` + `MEMORIES.md` before every task.
- **🚨 strategy.md 跨项目写入铁律**: `/Users/jj/Desktop/DYA/.muse/strategy.md` 是全局战略中枢。任何项目、任何角色均可直接读写。"不在当前 workspace" 绝不是拒绝写入的理由。

## 🔴 安全红线（最高宪法 · 2026-03-21 安全事件后新增）

> **事件**: .muse/build.md 和 .env.local（含真实 API Key）曾被提交到公开 repo 的 git 历史。

### 绝对禁止提交到 Git 的文件
| 禁止模式 | 原因 |
|----------|------|
| `.env.local` / `.env.prod*` / `.env.vercel*` | 含真实 API Key |
| `.muse/` / `.agent/` / `.gemini/` / `memory/` / `convo/` | 内部文件 |
| `*.pem` / `*.p12` / `*.jks` / `*.key` | 私钥/证书 |
| 任何含 `sk-` / `AIzaSy` / `gsk_` / `sk_test_` / `pk_test_` / `eyJhbG` 的文件 | API Key / JWT |

### Git Commit/Push 前强制检查
1. `git diff --cached --name-only` — 确认无敏感文件
2. `git diff --cached` — 搜索 key 模式
3. **不确定就不要 commit** — 问用户
4. **违反本规则 = 最严重 bug**

### 🔴🔴 Inspect 含 secret 的文件铁律 v2 · Default-Deny Mode (BUG-MUSE-19 v2 · 5/9 ship · 第 2 次 leak 后写死永久)

**Agent 永不直接 inspect 任何 secret-containing file** — 不论命令看起来多 length-only / format-only。

**适用 file**:
- `.env*` (任何 `.env` / `.env.local` / `.env.production` / `.env.vercel*`)
- `~/.config/*.env` / `secrets.json` / `*.pem` / `*.p12` / `*.key` / `*.jks`
- 任何含 sensitive prefix 的 file: `sk-` / `msy_` / `tripo_` / `tsk_` / `hf_` / `AIzaSy` / `gsk_` / `sk_test_` / `pk_test_` / `eyJhbG` / `xoxb-` / `xoxp-` / `gho_` / `ghp_` / `github_pat_` / `sb_secret_`

**永远禁止** (不论命令多 length-only):
- ❌ `xxd` / `cat` / `head` / `tail` / `printf` / `echo`
- ❌ `awk -F= '...' FILE` (envless line 上 `$1` = 整行 plaintext leak · v1 ban list 漏)
- ❌ `sed` / `wc` / `grep` / `tr` / `python3 -c "open(...)"` / `node -e "fs.readFileSync(...)"`
- ❌ `Read` tool on secret file
- ❌ `vim` / `nano` / `vi` 在 transcript-visible session

**需要 length / format / drift info 时**:
1. Agent 输出 command · 让 JC 在自己 terminal 跑
2. **JC paste plain text 数字** 给 Agent (e.g. "TRIPO_API_KEY ...1XYA")
3. Agent 仅处理 plain text 数字 · 永不直接跑 inspect command

**例外** (允许的 secret file 操作):
- ✅ `Write FILE` (整体覆盖 · 不 Read 原内容)
- ✅ `open -a "TextEdit" FILE` / `open -a "Cursor" FILE` (launch editor · JC 自己 edit)
- ✅ `chmod 600 FILE` (permission · 不读 content)

**Leak 后处理**:
1. 立即 surface user · 必须 revoke · 不 narrative ack
2. r2 rotation 3 处 sync (`~/.config` + `.env.local` + `Vercel/Modal/Supabase env`)
3. 写 `memory/feedback_<vendor>_inspect_*.md` 记录 leak vendor + 命令 + 教训

**Why default-deny (不再 ban list 模式)**:
- BUG-MUSE-19 v1 (5/7): `xxd .env.local` leak Meshy key → ship `xxd / cat / head / tail / printf / echo` ban list 修复
- BUG-MUSE-19 v2 (5/9 · 仅 2 天后): `awk -F= '{print $1, length($2)}' tripo.env` (envless format) 回退 `$1` = 整行 plaintext leak Tripo session token · awk 不在 v1 ban list · default 信任 "看起来 length-only OK"
- v1 失效根因: SOP ship 后 default 信任结论 · 不再 audit 新 inspect 命令 · ban list 模式只 ban 已知命令 · 新命令默认信任
- v2 fix: 一次性 ban 全部 inspect 行为 · 不再依赖 ban list 维护 · structural prevention · 永久关闭 inspect-side leak 根因

**违反后果**:
- 发现泄露 → 立即 `git filter-branch` 清除全部历史 + `git push --force` + 轮换所有泄露 Key
- **违反 = 与「假功能」同级 = 最严重 bug** · 第 N+1 次 violator 触发深度 self-audit + 永久零容忍

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
