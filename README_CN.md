# 🎭 MUSE

**Memory-Unified Skills & Execution**（记忆统一技能与执行）

> *希腊神话中九位缪斯女神是记忆女神 **Mnemosyne** 的女儿。她们将母亲的全知记忆化为对艺术与科学的精通。*
>
> *MUSE 继承了这一血脉。它确保 AI 对话中的每一个洞见都不会丢失，将原始会话数据转化为驱动执行的结构化知识。*

MUSE 是一套**纯 Markdown** 的 AI 编程协作操作系统。通过宪法、记忆层、技能库和执行工作流，实现 AI 编程助手的**跨对话无损上下文管理**。

灵感来源：[LCM（Lossless Context Management）](https://papers.voltropy.com/LCM) 论文 + [lossless-claw](https://github.com/Martian-Engineering/lossless-claw) 插件。MUSE 用**纯 Markdown SOP**（而非代码插件）实现了 LCM 的核心设计思想。

[📖 English Docs](./README.md)

---

## ✨ 为什么需要 MUSE？

| 没有 MUSE | 有 MUSE |
|---------|--------|
| 长对话后 AI 忘记早期内容 | Pre/Post Compaction 协议保护关键信息 |
| 新对话要手动交代背景 | `/resume` 5 步自动组装上下文 |
| 结束对话忘记保存进度 | `/bye` 零输入一键收尾 |
| 跨天任务断档 | `grep memory/` 自动搜索历史 |
| 同样的坑踩两遍 | `/distill` 蒸馏教训到长期记忆 |

**适用**: Claude Code、Cursor、Windsurf、任何支持系统提示的 AI 编程助手。

---

## 🚀 快速上手（5 分钟）

```bash
# 克隆 MUSE
git clone https://github.com/myths-labs/muse.git

# 复制模板到你的项目
cp muse/templates/CLAUDE.md 你的项目/CLAUDE.md
cp muse/templates/USER.md 你的项目/USER.md
cp muse/templates/MEMORIES.md 你的项目/MEMORIES.md
mkdir -p 你的项目/memory 你的项目/.muse

# 复制技能和工作流
cp -r muse/skills 你的项目/.agent/skills
cp -r muse/workflows 你的项目/.agent/workflows

# 添加 MUSE 条目到 .gitignore
cat muse/templates/.gitignore-template >> 你的项目/.gitignore
```

### 开始使用

```
你: /resume           ← AI 自动读宪法 → 读 memory → 开始工作
    ... 工作 ...
你: /ctx              ← 查上下文还够不够
    ... 继续工作 ...
你: /bye              ← 一键收尾，自动保存
```

---

## 📖 核心命令

| 命令 | 说明 | 需要输入？ |
|------|------|:---------:|
| `/resume [scope]` | 启动 — 恢复上下文 | ✅ 一句话 |
| `/ctx` | 上下文健康检查（🟢🟡🔴） | ❌ |
| `/bye` | 零输入一键收尾 | ❌ |
| `/distill` | 蒸馏 memory/ → MEMORIES.md | ❌ |
| `/resume crash` | 上下文爆掉后恢复 | ❌ |

## 🧩 技能体系

| 层级 | 说明 | 随 MUSE 发布？ |
|:----:|------|:-------------:|
| **🏛 Core** | MUSE 运转必须的 | ✅ 内置 |
| **🔧 Toolkit** | 通用开发工具 | ✅ 推荐 |
| **🎯 Domain** | 用户自建领域技能 | ❌ 私密 |

## 📁 目录命名规范

| 分类 | 规则 | 示例 |
|------|------|------|
| 记忆日志 | `YYYY-MM-DD.md` | `2026-03-12.md` |
| 对话存档 | `YYMMDD-NN-desc.md` | `260312-02-setup.md` |
| 角色文件 | `[role].md` 小写 | `build.md`, `qa.md` |

---

完整文档请参阅 [English README](./README.md)。

---

## 📜 License

MIT License — Myths Labs

---

*MUSE v2.2 — Built by [Myths Labs](https://mythslabs.ai)*
