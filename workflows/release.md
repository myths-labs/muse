---
description: MUSE 开源仓库版本发布 SOP — 更新 README/CHANGELOG/version + git commit + GitHub Release
---

## 触发

```
/release
```

**零输入。** 版本号和标题全部自动生成，用户只需要说 `/release`。

仅同步公开文档时，不执行本流程的版本递增、打 tag 或创建 release 步骤。
在用户授权范围内通过普通 PR/CI 合并，同步官网文档入口并验证实际内容；
版本和已发布的 release 保持原值，不把文档说明写成新的运行时能力。

## 路径约定

```bash
MUSE_ROOT="$(git rev-parse --show-toplevel)"   # MUSE 仓库根目录
# DYA_ROOT: 从 .muse/paths.md 读取（跨项目回传用，OSS 用户可忽略）
```

> 本文件中 `<MUSE_ROOT>` = MUSE 仓库根。`<DYA_ROOT>` = 可选的跨项目主仓库。

## 自动检测逻辑

### 版本号：自动递增
```bash
# 读取当前版本
grep -o 'version-[0-9.]*' <MUSE_ROOT>/README.md | head -1
# 例: version-2.6 → 新版本 = 2.7.0
```
规则：当前版本 minor +1（如 2.6→2.7）。如果是纯 bugfix 无新功能 → patch +1（如 2.6.0→2.6.1）。

### 标题：从 git log 自动生成
```bash
# 从 MUSE 仓库最后一次 release tag 到现在的 commit 信息中提取
cd <MUSE_ROOT> && git log $(git describe --tags --abbrev=0)..HEAD --oneline
```
- 提取 commit message 中的关键词，组合成 3-5 个词的标题
- 格式：`[核心功能] + [次要功能]`（如 `QA System v2.0 + SOP Deep Fix`）
- 如果只有一个功能 → 直接用（如 `Ecosystem Packs v2`）

## 前置条件

- MUSE 仓库路径: `<MUSE_ROOT>`
- 已有 GitHub CLI (`gh`) 并已登录
- 所有代码改动已完成（本 SOP 只管发布，不管改代码）

---

### 检查点尺寸与证据保存

- 按 UTF-8 字节核对容量，包含渲染后的 metadata 和分隔符。增量运行器的输入 JSON、选定 source 文件、canonical 及渲染结果各受 262,144 bytes（256 KiB）上限约束；它与默认 16 MiB Git 内容预算及完整范围分批校验是不同限制。
- 完整新验证留在工件与有界 source/证据索引；检查点只追加必要事实和简短证据指针。当前协议只允许替换 `Next Action`、`Required Reads`，保留历史正文、决定、限制、未决项、来源范围、writer 和 handoff。source/索引也必须符合读取上限，较大日志留在被引用工件中。
- 保存前核对计划增量渲染后的总字节数。遇到 `TOO_LARGE`，保留失败 input/stdout/stderr、source 证据与 canonical SHA；核对当前状态和真实写入者后刷新 expected/source SHA，减少增量中的重复正文，再走官方受保护保存，逐项验证 before/after/input/source 归档及 canonical 读回。
- 若受支持的指针替换仍无法容纳，保留未保存证据并进入独立存储/迁移设计审阅；不自动扩大限制、删除历史或改变写入身份，也不宣称已保存。简短指针是有界操作方式，不等于长期容量问题已解决。
- 后续涉及存储策略的发行，实际验证近上限保存、超限拒绝且 canonical 不变、归档读回和历史证据恢复；完整范围 Git 校验不能替代这些检查。操作细节见安装技能的 `muse-commands/references/CHECKPOINT_CAPACITY.md`。

## Step-by-Step

### 1. 自动检测版本号和变更内容

```bash
# 0. 同步远程 tags（防止版本号不同步 — 2026-03-21 bug fix）
cd <MUSE_ROOT> && git fetch --tags origin

# 1a. 读取当前版本
grep -o 'version-[0-9.]*' <MUSE_ROOT>/README.md | head -1

# 1b. 读取上次 release 后的 commit
cd <MUSE_ROOT> && git log $(git describe --tags --abbrev=0)..HEAD --oneline

# 1c. 读取 DYA 本轮 MUSE 相关 commit（如有从 DYA 同步过来的改动）
cd <DYA_ROOT> && git log --oneline -10 --grep="muse" --grep="MUSE" --all-match
```

Agent 自动：
- 版本号 = 当前 +0.1
- 标题 = 从 commit messages 提取关键功能名
- 变更列表 = 从 commit messages 分类为 Added/Fixed/Changed

**输出确认**（仅展示，不需要用户输入）：
```
📦 自动发布: v[X.Y.0] — [自动生成的标题]
   当前版本: v[旧版本]
   变更: [N] added, [N] fixed, [N] changed
```

### 2. 编写 CHANGELOG 条目

在 `<MUSE_ROOT>/CHANGELOG.md` 顶部插入新版本条目：

```markdown
## [X.Y.0] - YYYY-MM-DD

### Added
- **[功能名]** — [一句话描述]

### Fixed
- **[修复名]** — [一句话描述]

### Changed
- **[变更名]** — [一句话描述]
```

**规则**：
- 日期用当天（系统时间）
- 遵循 [Keep a Changelog](https://keepachangelog.com/) 格式
- 只写 Added/Fixed/Changed 中有内容的 section，空 section 删掉
- 每条一行，简洁但明确

### 3. 更新全局版本号（6+ 处）

**⚠️ 必须全部更新，缺一不可：**

| # | 文件 | 位置 | 示例 |
|---|------|------|------|
| 1 | `README.md` | badge 行 | `version-X.Y-blue` |
| 2 | `README.md` | 页脚 `<i>` | `MUSE vX.Y` |
| 3 | `README.md` | 正文 skill 数量 | `65 skills` |
| 4 | `README_CN.md` | badge 行 | `version-X.Y-blue` |
| 5 | `README_CN.md` | 页脚 `<i>` | `MUSE vX.Y` |
| 6 | `docs/index.html` | meta + footer | `65 skills` + `MUSE vX.Y` |
| 7 | `docs/llms.txt` | 正文 skill 数量 | `65 skills` |
| 8 | `SKILL_INDEX.md` | header | `Total: 65 skills` |

**执行方式**：用 `sed` 或编辑工具一次性替换所有处。

```bash
# 验证替换结果 — 🔴 这一步是强制的，不可跳过
grep -rn "旧版本号" README.md README_CN.md SKILL_INDEX.md docs/llms.txt docs/index.html
# 预期：零结果。有残留 = ABORT
```

### 3b. 物理验证 Skill 数量

```bash
# 🔴 强制执行 — 每次发版前必须运行
find skills/ -name "SKILL.md" | wc -l
# 输出数字必须与 README/SKILL_INDEX/docs 中的数字一致
```

### 4. 同步工作流文件（如有改动）

⚠️ **DYA 和 MUSE 的工作流文件并非完全相同。** DYA 的 `resume.md` 包含 DYA 专用的绝对路径和跨项目规则，MUSE 的 `resume.md` 是通用模板（通过 CLAUDE.md 配置跨项目路径）。

**🚨 安全分类（每次 release 前检查）**：

| 分类 | 文件 | 操作 |
|:---:|------|------|
| ✅ 安全同步 | `bye.md`, `ctx.md`, `distill.md`, `role.md`, `start.md`, `settings.md` | 直接 `cp` 覆盖 |
| ⚠️ **禁止覆盖** | `resume.md` | DYA 版有绝对路径，MUSE 版是通用模板。**手动对比 diff，只合并通用改动** |
| ⚠️ **禁止覆盖** | `sync.md` | DYA 版有项目特定路由。**手动对比 diff，只合并通用改动** |
| ❌ 不同步 | `release.md` | DYA 专属（包含本地路径） |

**执行方式**：
```bash
# 安全文件直接复制
for f in bye.md ctx.md distill.md role.md start.md settings.md; do
  [ -f "<DYA_ROOT>/.agent/workflows/$f" ] && \
  cp "<DYA_ROOT>/.agent/workflows/$f" "<MUSE_ROOT>/workflows/$f"
done

# resume.md 和 sync.md — 用 diff 检查，手动合并
diff <DYA_ROOT>/.agent/workflows/resume.md <MUSE_ROOT>/workflows/resume.md
diff <DYA_ROOT>/.agent/workflows/sync.md <MUSE_ROOT>/workflows/sync.md
# ⚠️ 只合并通用改动（如新 Step、格式修复），不合并 DYA 绝对路径
```

### 4b. 更新 package.json 版本号（如有）

```bash
# 检查 package.json 是否存在
if [ -f "<MUSE_ROOT>/package.json" ]; then
  # 更新 version 字段
  sed -i '' 's/"version": "[^"]*"/"version": "X.Y.0"/' <MUSE_ROOT>/package.json
fi
```

### 5. 🔴 Pre-flight Gate（不通过 = 禁止发版）

```bash
cd <MUSE_ROOT>

# Gate 1: 旧版本号零残留
OLD_VER=$(git tag --sort=-creatordate | head -1)
REMNANTS=$(grep -rn "$OLD_VER" README.md README_CN.md SKILL_INDEX.md docs/llms.txt docs/index.html 2>/dev/null || true)
if [ -n "$REMNANTS" ]; then
  echo "❌ ABORT: 旧版本号残留"
  echo "$REMNANTS"
  exit 1
fi

# Gate 2: Skill 数量一致性
PHYSICAL=$(find skills/ -name "SKILL.md" | wc -l | tr -d ' ')
INDEX=$(grep -o "Total: [0-9]*" SKILL_INDEX.md | grep -o "[0-9]*")
if [ "$PHYSICAL" != "$INDEX" ]; then
  echo "❌ ABORT: SKILL_INDEX ($INDEX) ≠ 物理文件 ($PHYSICAL)"
  exit 1
fi

# Gate 3: 无未提交文件
DIRTY=$(git status --porcelain)
if [ -z "$DIRTY" ]; then
  echo "⚠️ 没有任何改动要提交"
fi

echo "✅ Pre-flight PASS"
```

**🔴 铁律: 不运行 Pre-flight = 不允许 git tag。违反 = P0 bug。**

### 5b. 运行环境、升级与官网验证

先固定本次真实工作流使用的 Python 绝对路径；虚拟环境要保留其 launcher，
不能解析成基础解释器。普通 continuity 只需要标准库，Pillow 不是默认安装依赖。

```bash
MUSE_RELEASE_PYTHON="/absolute/path/to/venv/bin/python"
"$MUSE_RELEASE_PYTHON" -I skills/core/muse-commands/scripts/muse-runtime-dependencies.py \
  --python "$MUSE_RELEASE_PYTHON"
```

只有明确依赖图片解码的工作流才追加 `--require-image-decoder`，要求 PNG/JPEG
均通过 verify 和完整 load。保留调用及 JSON 报告；普通终端 import 成功不证明
隔离环境可用。失败时修复或选择合适环境，再以同一解释器和原生身份重跑实际
工作流，不能让预检替代验收。具体诊断见技能的 `references/RUNTIME_DEPENDENCIES.md`。

使用真实上一版安装包验证升级后的安装副本，保存 receipt，再验证逆序回滚
能恢复原文件、链接和权限。安装副本也要执行预检。维护版至少运行公共回归、
发行检查和官网交互测试；依赖、发行记录和网站必须对应同一提交。

版本分支按仓库 PR/CI 规则合并后才创建 tag 和 release。官网同步版本、说明、
双语使用文档、llms.txt 及 release 链接；发布后在真实浏览器检查生产内容和
链接跳转，不能以 HTTP 200 或部署成功代替交互验收。

### 6. Git Commit + Push

```bash
cd <MUSE_ROOT>

# Stage 所有改动
git add -A

# 检查 diff
git diff --cached --stat

# Commit
git commit -m "feat(vX.Y): [标题]

[变更摘要，2-4行]"

# Push
git push origin main
```

### 7. 创建 Git Tag + GitHub Release

```bash
cd <MUSE_ROOT>

# Tag
git tag vX.Y.0

# Push tag
git push origin --tags

# GitHub Release
gh release create vX.Y.0 \
  --title "vX.Y.0 — [标题]" \
  --notes "## What's New

### [emoji] [主要功能]
[2-3行描述]

### ✨ New Features
- [feature 1]
- [feature 2]

### 🐛 Bug Fixes
- [fix 1]
- [fix 2]"
```

**Release Notes 规则**：
- 用英文（开源项目面向全球）
- 开头用 `## What's New`
- 每个大功能单独 `###` 段落，带 emoji
- 小功能/修复用 bullet list
- 不要写内部实现细节，只写用户可感知的变化

### 8. 同步本地 tags + 验证发布

```bash
# 同步远程 tag 到本地（防止下次对话版本不同步 — 2026-03-21 bug fix）
git fetch --tags origin

# 验证 tag 已同步
git describe --tags --abbrev=0  # 应该输出 vX.Y.0

# 验证 release 创建成功
gh release view vX.Y.0

# 验证 badge 更新（GitHub CDN 可能有 ~5 分钟缓存）
echo "✅ Release published: https://github.com/myths-labs/muse/releases/tag/vX.Y.0"
```

### 9. Airachne 自动发布社交动态 (MCP)

在发布成功后，Agent 应主动调用 `airachne` MCP 服务器向 X 和 LinkedIn 广播更新：
1. 提取本次发布的核心功能（如 "MUSE v2.7.0 brings... "），生成一段 **充满极客感、去 AI 味、不带废话的首字母大写纯靠谱推文**。
2. 呈现给用户：
   `"要不要我顺便帮您把今天的发布通过 Airachne 推送到 X 和 LinkedIn 上？（回复 Y 立即执行）"`
3. 用户回复 Y 后，**并行调用** `post_to_x` 和 `post_to_linkedin`，完成 100% 自动发布的闭环。

### 10. 回传 DYA

在 DYA 的 strategy.md 或 memory 中记录发布：
```
✅ MUSE vX.Y.0 已发布 (YYYY-MM-DD HH:MM)
```

---

## Checklist（Pre-flight 脚本自动执行，但 Agent 也要人肉检查）

```
□ CHANGELOG.md 顶部有新版本条目
□ README.md badge + 正文 skill 数 + 页脚（3 处）
□ README_CN.md badge + 页脚（2 处）
□ docs/index.html meta + footer（2 处）
□ docs/llms.txt skill 数量（1 处）
□ SKILL_INDEX.md Total 数量（1 处）
□ find skills/ -name "SKILL.md" | wc -l = 上述所有数量
□ 工作流文件已同步（如有改动）
□ 🔴 Pre-flight Gate 3 项全 PASS
□ 固定真实解释器，安装副本预检与真实工作流通过；图片解码仅在明确需要时验证
□ 上一版升级、逆序回滚及用户文件保留验证通过
□ 检查点与 source 容量按 UTF-8 字节核对，详细证据留在工件中且历史/身份保留
□ 若改动存储策略，近上限保存、超限拒绝、归档读回及历史证据恢复通过
□ PR/CI 通过，tag、release 与官网部署对应同一提交
□ 官网版本、双语说明、llms.txt、release 跳转及桌面/移动交互实际验证
□ git diff --cached --stat 确认无遗漏
□ commit message 遵循 feat(vX.Y) 格式
□ git push 成功
□ git tag + push --tags 成功
□ gh release create 成功
□ Release notes 用英文
□ 回传 DYA 记录
```

---

## 快捷方式

对于简单发布，可以直接使用 MUSE 仓库中的 `release.sh` 脚本：
```bash
cd <MUSE_ROOT>
./release.sh 3.1.0 "Release Title" "### Added\n- Feature description"
```
脚本自动执行: 版本检测 → 旧版本号替换 → skill 数量验证 → pre-flight gate → commit+tag+push → GitHub Release

---

## 注意事项

- 本文件是公开的可移植发布流程。同步本地 SOP 时，只带入通用规则；不提交私人路径、会话记录、凭据或项目证据。可选的 DYA 回传仅适用于实际配置了该角色中心的项目。
- 版本号遵循 semver：X.Y.0（major 功能用 Y 递增，patch 修复用 Z 递增）
