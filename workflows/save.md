---
description: 保存当前角色和Lane的本轮变化，继续当前任务，不执行正式Bye
---

# 日常保存

用于已登记 daily-v1 的当前 Lane。角色未确定时先解析用户的角色/Lane要求；不从cwd、最近文件或工作量猜。共享策略为daily-v1的未登记Lane，先按daily-resume和ONBOARDING_V1完成已有用户授权下的首次接续；显式legacy退出保留原流程。

1. 复用已锁定的 `/resume <role> Lane <lane>` 身份。用 `muse-doctor.sh prepare-resume --command '<完整resume指令>' --workspace '<checkpoint workspace>'` 获取当前SHA和保存者；将JSON写入本任务的资料文件，按区段读取，不整包灌进上下文。用 `runtime-identity` 核对当前真实会话。
2. 当前会话不是保存者时，先按 `daily-resume.md` 的“显式接手”完成核对和claim。缺运行时身份、版本过期或状态冲突时，保留原文件，处理具体原因；不要只换成最新SHA重试。
3. 从本轮实际发生的内容生成小型 source note，保留用户决定/否决/限制、失败和未查事项、实际证据及下一步。区分原话、助手选择和观察结果，使用精确session来源。当前source仅能声明partial；未保存尾部不能宣称已覆盖。不得写入秘密。
4. 准备schema1增量JSON。格式见共享 `muse-commands/references/DAILY_V1.md`。使用刚核对的checkpoint SHA、已有handoff ID、当前platform/session；source包含绝对路径和SHA256。历史决定、限制和失败只追加或显式标记supersedes；仅Next Action、Required Reads可替换，旧版本由helper保留。
5. 执行 `muse-doctor.sh save-daily --input '<绝对JSON路径>'`。`SAVED`后使用返回SHA进行读回并逐项比对预期变化；`UNCHANGED`不重写、不补造归档；失败或写后不确定时核对实际canonical和PREPARED archive，不把残留目录当成功。
6. 在角色home和必要subject项目的当天memory追加简短结果/决定/问题/下一步与同一handoff ID；共享索引有变化时只更新相关条目。它们引用本次事实，不复制整套历史或冒充完整Bye的覆盖凭据。

阶段结果、关键决定和上下文保存提醒均可使用本流程，无需用户每次手打 `/save`。没有实质变化时不为了确认反复保存。保存只证明声明版本的记录可读，不替代本轮真实测试、语义核对、正式Bye或产品QA。保存后继续当前任务。

来源账本已安装时，步骤3之前按 SOURCES_V1.md 获取精确原生会话的新增用户消息，source-update 导入并完整审阅；随后重新取得保存SHA。Codex用原生read_thread投影用户消息，Claude用已落盘的UserPromptSubmit记录。原始记录与source note分开，note不冒充原话。缺接口/缺历史标UNKNOWN，只继续不依赖缺口的工作。不要每次重放全部历史。保存完成后继续执行用户的完整目标，只有真实缺授权/登录/信息才请求用户介入。
