---
description: 已登记 Lane 的有界收尾与收据复核
---

# 收尾与复核

由 `bye-workflow --command '<锁定的resume指令>' --workspace '<workspace>'` 选择本文件才适用。共享默认启用的未登记Lane先按daily-resume完成首次接续；显式退出的Lane使用原bye.md。普通阶段完成使用 save.md 并继续；用户明确结束/交接才执行正式收尾。

1. 复用角色/Lane，prepare-resume 核对版本、原生写入者、未闭问题和范围。读 SOURCES_V1.md、CLOSEOUT_V1.md。刷新精确会话的新增原生用户消息，完整审阅每条；“完整了吗＋新要求”必须保留新要求。来源不可得保留 UNKNOWN，不能用旧收据证明本次完整。
2. 有该范围收据时先 check-closeout。VALID 报告核查时间、来源水位、收据及范围，不重写工作区/生成handoff/重复两轮。STALE 按 affected_ids 和依赖闭包处理变化；BLOCKED 明确缺证据。不得删事件、缩范围或改时间制造 VALID。
3. 没有有效收据且确需结束时，列明本次范围、未撤销要求/否决、真实完成/失败及跨Lane待同步项。产品/merge/launch未就绪可以保留为未闭事项，不能写成产品完成。执行授权内必要修复、记录及适用QA。
4. 生成一次handoff_id，用带当前SHA的 write-checkpoint 更新八区段并保留来源指针；角色记录、必要subject memory、来源/工作证据索引用同一ID。verify-handoff 验证关联，独立审阅验证语义。来源包标明精确会话/消息区间、未覆盖类型及缺口。完整导出可用时按CODEX_ADAPTER执行；不可得时只声明已取得的范围，不伪称完整transcript。
5. 固定范围和版本，实际审查十面：product_code、verification、operator_contract、migration、delivery_docs、role_consistency、carrier_manifest、secrets_default_deny、cross_lane、numeric_sampling。每面给出检查/依赖/证据；不适用也说明范围依据。两轮必须是真实不同执行，修复后回归；各轮有独立执行者的回归证据，最终有独立来源/语义审阅。不能复制日志换run_id冒充第二轮，HTTP200/编译通过不等于业务QA。
6. 保存实际命令、时间、返回值和日志，声明文件/清单/时效观察依赖，刷新来源后 verify-closeout。只有 DECLARED_SCOPE_CLOSEOUT_VERIFIED 才能说“声明范围的收尾核查通过”。收据单独保存，不写回自身依赖造成循环失效。新增实质改动使旧收据失效；纯说明/确认无需制造新轮次。

一次报告全部已发现问题，修复后只重跑必要检查及相关回归；持续失败保留具体原因，不要求用户反复问完整吗。收据不授权merge、部署或产品launch。80%是保存/压缩后的恢复检查点，不自动退出；当前上下文数值不可得标UNKNOWN。

同一Lane之前未撤销的产品失败、认可基线及既定回归义务必须继续保留；纯文档/收尾轮不能使其消失或免除。属于本次声明完成范围的回归需真实执行，缺失则不能封存该完成范围；范围外义务明确记为未闭并指定接续位置，不能因此宣称产品就绪。其他Lane的失败保留引用及归属，不擅自接手或扩大授权。
