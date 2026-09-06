---
description: 已登记Lane的按需恢复和显式会话接手；保留必要检查与未知范围
---

# daily-v1 恢复

由 `muse-doctor.sh resume-workflow` 按共享默认策略为所有角色/Lane选择；显式legacy退出才使用原 `resume.md`。协议未知/损坏时停止该状态写入，不能静默退回旧模式覆盖。

## 首次接续与新Lane

先读 `muse-commands/references/ONBOARDING_V1.md`。prepare-resume 返回 MIGRATION_REVIEW_REQUIRED 时，按用户本次继续该Lane的要求审阅并 adopt-lane；NEW_LANE_REVIEW_REQUIRED 时，由Strategy依据当前请求或既有已授权目标拟定八区段并 initialize-lane，不要求用户另填目标表。RECORDED_WORKSPACE_REQUIRED 时核对记录的worktree，在该workspace重新prepare；路径消失/冲突不猜。已有活动会话尚未移交则不抢写。用户已经授权全局使用/继续本Lane，不另问是否升级。只读查看仍不授权接手。

## 读取与核对

沿用项目自己的角色与执行政策。若项目规定 Strategy 直接开发、修复、测试和验收，恢复时保持此模式；其他项目按其已授权的分工执行。先核对共享决策、验收基线及跨Lane依赖，再按需恢复当前Lane；不能因技术工作或读取项目build.md而切换角色或引入派单链。检查点若明确Lane CLOSED，先保留关闭状态并说明重开条件，不能因换客户端自动开工。

用户只需恢复指令或在当前会话说继续。目标、验收、限制、工作区、下一步以及本文件要求的review/JSON均由Strategy从已有授权和记录恢复或拟定，不要求用户填表。是否需要新Lane按_CONVENTIONS的自动划分规则判断；可自行处理的步骤直接执行，仅对记录无法解决的实质歧义提问。

1. 用原始 `/resume` 指令解析并锁定 role_home、role、Lane；subject project不改变身份。运行 `prepare-resume --command '<原始resume指令>' --workspace '<实际工作区>'`，将结果写入本任务资料文件并分区读取。只读准备不取得写权限。
2. 从packet恢复全部八个区段，尤其决定/否决、未闭失败、证据和Next Action。helper只读取一次当前检查点，不自动读取历史。比对实际repo/worktree、branch、HEAD及未提交状态；Git差异或packet过期需要解释，不用旧结论覆盖当前事实。
   若Git采用explicit_files范围，必须读取其scope_sha256和excluded_work；COMPLETE仅表示该明确范围可核对，不代表整个产品。范围外的源码、配置或其他Lane仍未核实，不能扩大执行范围。源文件过大/不可读造成PARTIAL时，接手写入会被拒绝；不要扩大读取上限或临时删减范围来绕过。工作范围确需变化时，由当前写入者按用户已授权的任务重新审阅并登记范围。
3. 核对当前适用宪法、角色指令、用户偏好和该Lane的显式指令。已在当前上下文中加载且版本不变的不重读；新会话按相关节读取。按checkpoint的Required Reads定位本轮必需证据；只有缺项、争议、引用失效或版本变化时扩展读取范围。
4. 按精确session与已有来源水位核对新增真实用户消息；不按“最新同cwd文件”猜，不将固定尾行或摘要视为全覆盖。超过大小限制的源不直接读；用可用原生接口/分段归档补证。仍缺失则将source_tail记为UNKNOWN，保留缺口，只推进明确不依赖缺口的工作。所有新增授权/否决须保留原话位置及supersedes，助手建议不自动变为授权。
5. 检查相关的全部未闭Pending Propagation及共享配置风险，不以文件年龄排除；只读非秘密状态。实际涉及生产、部署、launch、E2E或alias时，执行适用的生产env/alias核验；缺证据、空结果、目标歧义为未验证，preview-target承载生产域名为阻塞。恢复本身不授权轮换、部署或回滚。
6. 恢复上一产品修复的回归义务、未闭失败、回滚和BUILD/QA通知；按问题/证据去重。保留未撤销工作基线、认可原话及反转依据；received、executed、verified分开。纯记录保存不能消除FAIL。只执行与当前任务相关且已获授权的检查，其余明确保留。

这些步骤压缩重复读写，不删除实质义务。不得用一个布尔勾选或程序的RECOVERY_REVIEW_REQUIRED替代语义审阅。若关键身份、授权或状态冲突未解决，不继续依赖该状态的动作。

## 显式接手

- 通过 `runtime-identity` 取得当前会话身份：Codex使用原生CODEX_THREAD_ID；Claude使用本项目SessionStart捕获的环境。缺失时不填旧ID或猜ID；读取仍可进行，写入保持拒绝。安装Hook前已存在的Claude会话需从原生事件补获身份或在下一次原生启动/恢复时捕获，不能手工冒充。
- 若当前身份与checkpoint保存者相同，无需claim，继续已授权工作。
- 若不同，先完成以上核对，并确认用户明确请求在本会话继续/接手这个Lane；只读查看不构成接手。用户已明确让当前会话继续该Lane时，记录该指令来源并直接处理，无需再次确认。若发现另一会话仍在主动执行同一工作项或接手意图不清，保持只读并先澄清冲突。
- 准备 `claim-lane` 输入，固定旧checkpoint SHA/身份、当前Git证据SHA、小型partial source note及用户接手要求来源。review保留source_tail是否未知、允许推进的具体范围；它是执行者已审阅内容的记录，不是helper的语义证明。格式见 `muse-commands/references/DAILY_V1.md`。
- 执行 `muse-doctor.sh claim-lane --input '<绝对JSON路径>'`，读回并核对旧ID、新运行时ID、原八区段及handoff不变。claim只改变写入者元数据并追加可追溯接手记录。旧会话此后写同Lane会被拒绝；若冲突，读取实际版本后解决，不反复抢占。

恢复报告只需：角色/Lane、当前写入者、确认的来源范围、阻塞/未知、工作基线和准确下一步。不要为报告重抄历史。按核对后允许的范围继续任务，并通过 `/save` 保存本轮变化。

正式 `/bye` 由 bye-workflow 选择 daily-bye.md，保留十面、两轮、来源和适用产品回归义务，并允许有效收据复核。prepare-resume 的 source_ledger 返回来源水位、缺口及最多20条待审消息；按 SOURCES_V1.md 刷新增量，审完本批再读下一批。当前来源不等于完整历史；任意旁路直接改文件也不在helper保护边界内。内部阶段保存后继续完整目标，不等待用户反复说下一步。
