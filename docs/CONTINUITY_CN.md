# MUSE 3.6 连续开发使用说明

MUSE 将角色、Lane 和必要证据保存在项目中。你可以只用 Codex、只用 Claude
Code，或者在两者之间接续同一份工作；换客户端不会改变角色。
本版在原有 Markdown 技能之外新增 Python 运行器，支持有 Git、Python 3.7+
的本地 macOS/Linux。原生 Windows 和网络文件系统的持久性尚未认证。

## 安装或升级

在 MUSE 仓库中执行：

```bash
bash scripts/install.sh --tool codex --target /你的项目路径
bash scripts/install.sh --tool claude --target /你的项目路径
```

只装你使用的一端，也可以两端指向同一项目。默认安装 core 和 toolkit 技能；
加 `--core-only` 可只装 core。原有 AGENTS.md/CLAUDE.md 保留，只追加一小段
MUSE 入口；技能按需加载，不再把所有角色与技能正文塞进入口文件。
Claude 的设置和已有 hooks 合并保留。客户端未发现新增技能目录时重启即可。
需要指定 Python 时使用 `MUSE_PYTHON=/你的/python3路径`。

安装结果中的 `receipt_path` 是回退记录。原版 3.5 工作流会先备份再升级；
遇到运行器或工作流中的未知修改，安装会先停止，保留现场，由代理核对后处理。
安装本身不会创建、接管或重写任何 Lane 检查点。

## 日常只需要这些指令

| 情况 | 你说什么 |
|---|---|
| 当前对话继续开发 | `继续` |
| 恢复某条已有线 | `/resume strategy Lane A` |
| 保存进度并继续 | `/save` |
| 正式收尾 | `/bye` |

Codex 可以把这些作为普通消息识别，不要求原生斜杠菜单出现对应命令。
必要时 Codex 用 `$muse-commands`、Claude 用 `/muse-commands` 明确调用技能，
再说明动作。目标、验收、限制、工作区和恢复所需 JSON 都由代理依据你的要求
及已有记录整理，你不用填写模板。

沿用项目自己的分工。如果项目由 Strategy 直接开发，就继续用 Strategy；
技术工作不会自动转交 Build。默认同一 Lane，只在工作确实需要独立接续时
划分新线，不为每个步骤、换模型或上下文压缩开新 Lane。

## 切换客户端与故障恢复

能操作原会话时，先 Save 并停止它继续写入；在另一端恢复相同角色和 Lane。
接收代理核对检查点、真实工作区、来源缺口和未完成义务后接手。旧写入者再
通过 MUSE 保存时会被拒绝，不能覆盖新写入者。

切换不要求完整 Bye。原会话崩溃或没有 Bye 时，代理核对已保存状态与未提交
工作后恢复；旧记录缺失时不能直接创建空白状态覆盖。若 Lane 本身已经 CLOSED，
可以恢复查看，但只有满足记录中的重开条件才执行新工作。

实际观察到上下文达到80%时，先保存，客户端支持时压缩，核对当前状态后继续。
没有可靠指标就写 UNKNOWN；不根据模型名、用户偏好、累计 token 或旧百分比猜测。
自动压缩不保证记忆无损，缺失证据按需补读，不默认重放所有历史对话。

## 配置与记忆位置

- `.muse/config.json`：项目名称、路径和角色归属。
- `memory/lanes/`：权威检查点与受写入者保护的增量历史。
- `.agent/skills/muse-commands/`：两端共用的运行器。
- `.agents/skills/`、`.claude/skills/`：指向本项目技能的相对发现链接。
- `memory/.muse-source-inbox/`：可取得的 Claude 原生提示来源，经脱敏保存。
- `.muse/installations/`：私人安装与回退记录，包含本地配置备份，不要公开。

默认配置是 `{ "schema_version": 1, "role_home": "home",
"projects": { "home": "." } }`。相对路径以该配置所在项目为基准。
需要跨项目时由代理配置共享角色中心，并确保中心也安装了对应工作流。
在配置树以外执行可设置 `MUSE_CONFIG`。优先级是显式 MUSE_CONFIG、显式旧版
root 环境变量、自动发现。已有身份迁移要保留旧 role_home 标识，不能随意改
检查点头部把历史重新命名。

## 验证与回退

Save 证明声明版本的检查点已写入并读回，不代表产品已经完成。原生来源能力
随客户端而异；Claude 使用 SessionStart/UserPromptSubmit，Codex 使用真实
会话身份与可用的原生消息。来源不完整时保留 partial 和缺口，不声称完美记忆。
不会假定每个用户都有某个项目专属的对话导出脚本。

正式 Bye 验证声明范围并产生可复用记录。范围和证据未变化时核对已有收据；
有新要求、代码、配置、验证器或证据变化时处理受影响项。已有产品失败不会
因为保存或 Bye 消失，必须通过它自己的真实验收。

撤回一次安装时，先停止正在使用这些文件的客户端，再执行：

```bash
python3 scripts/install-continuity.py --rollback /安装返回的/receipt.json
```

回退先核对全部受影响文件，再恢复原字节/链接。安装后有人修改过的文件不会
被强行覆盖；多次安装按逆序回退。记录之外的用户文件不删除。整机断电、恶意
同用户文件系统修改、绕过助手的任意外部写入，不在协作式保护的保证范围内。

协议细节见安装技能的 references；英文版见 [CONTINUITY.md](CONTINUITY.md)。
