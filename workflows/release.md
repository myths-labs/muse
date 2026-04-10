---
description: MUSE 开源仓库版本发布 SOP — 更新 README/CHANGELOG/version + git commit + GitHub Release
---

## 触发

```
/release
```

**零输入。** 版本号和标题全部自动生成，用户只需要说 `/release`。

## 自动检测逻辑

### 版本号：自动递增
```bash
# 读取当前版本
grep -o 'version-[0-9.]*' /Users/jj/Desktop/MUSE/README.md | head -1
# 例: version-2.6 → 新版本 = 2.7.0
```
规则：当前版本 minor +1（如 2.6→2.7）。如果是纯 bugfix 无新功能 → patch +1（如 2.6.0→2.6.1）。

### 标题：从 git log 自动生成
```bash
# 从 MUSE 仓库最后一次 release tag 到现在的 commit 信息中提取
cd /Users/jj/Desktop/MUSE && git log $(git describe --tags --abbrev=0)..HEAD --oneline
```
- 提取 commit message 中的关键词，组合成 3-5 个词的标题
- 格式：`[核心功能] + [次要功能]`（如 `QA System v2.0 + SOP Deep Fix`）
- 如果只有一个功能 → 直接用（如 `Ecosystem Packs v2`）

## 前置条件

- MUSE 仓库路径: `/Users/jj/Desktop/MUSE`
- 已有 GitHub CLI (`gh`) 并已登录
- 所有代码改动已完成（本 SOP 只管发布，不管改代码）

---

## Step-by-Step

### 1. 自动检测版本号和变更内容

```bash
# 0. 同步远程 tags（防止版本号不同步 — 2026-03-21 bug fix）
cd /Users/jj/Desktop/MUSE && git fetch --tags origin

# 1a. 读取当前版本
grep -o 'version-[0-9.]*' /Users/jj/Desktop/MUSE/README.md | head -1

# 1b. 读取上次 release 后的 commit
cd /Users/jj/Desktop/MUSE && git log $(git describe --tags --abbrev=0)..HEAD --oneline

# 1c. 读取 DYA 本轮 MUSE 相关 commit（如有从 DYA 同步过来的改动）
cd /Users/jj/Desktop/DYA && git log --oneline -10 --grep="muse" --grep="MUSE" --all-match
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

在 `/Users/jj/Desktop/MUSE/CHANGELOG.md` 顶部插入新版本条目：

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
  [ -f "/Users/jj/Desktop/DYA/.agent/workflows/$f" ] && \
  cp "/Users/jj/Desktop/DYA/.agent/workflows/$f" "/Users/jj/Desktop/MUSE/workflows/$f"
done

# resume.md 和 sync.md — 用 diff 检查，手动合并
diff /Users/jj/Desktop/DYA/.agent/workflows/resume.md /Users/jj/Desktop/MUSE/workflows/resume.md
diff /Users/jj/Desktop/DYA/.agent/workflows/sync.md /Users/jj/Desktop/MUSE/workflows/sync.md
# ⚠️ 只合并通用改动（如新 Step、格式修复），不合并 DYA 绝对路径
```

### 4b. 更新 package.json 版本号（如有）

```bash
# 检查 package.json 是否存在
if [ -f "/Users/jj/Desktop/MUSE/package.json" ]; then
  # 更新 version 字段
  sed -i '' 's/"version": "[^"]*"/"version": "X.Y.0"/' /Users/jj/Desktop/MUSE/package.json
fi
```

### 5. 🔴 Pre-flight Gate（不通过 = 禁止发版）

```bash
cd /Users/jj/Desktop/MUSE

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

### 6. Git Commit + Push

```bash
cd /Users/jj/Desktop/MUSE

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
cd /Users/jj/Desktop/MUSE

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
cd /Users/jj/Desktop/MUSE
./release.sh 3.1.0 "Release Title" "### Added\n- Feature description"
```
脚本自动执行: 版本检测 → 旧版本号替换 → skill 数量验证 → pre-flight gate → commit+tag+push → GitHub Release

---

## 注意事项

- **本文件是 DYA 专属**，不同步到 MUSE 开源仓库（因为包含本地路径等私密信息）
- 未来可以泛化为 MUSE Ecosystem 的可选 GitHub 发布 skill（去掉硬编码路径，改为配置项）
- 版本号遵循 semver：X.Y.0（major 功能用 Y 递增，patch 修复用 Z 递增）
