# 风险登记

| 风险 | 检测 | 缓解/回滚 | 状态 |
|---|---|---|---|
| 低成本模型改写玩法规则 | protected-surface gate | 拒绝批次并升级 high_reasoning | 已实现本地门禁 |
| 参数越界造成不可玩关卡 | parameter bounds + golden cases | 隔离候选，修正后重编译 | 已实现静态边界；可玩性待模拟 |
| 内容换皮改变玩法结果 | kernel digest + same-seed replay | 冻结 kernel，内容只引用 tunable 参数 | 已实现摘要契约；运行时待实现 |
| 平台 API/政策过时 | 官方文档时间戳与 contract gate | 未知即 blocked，不生成假兼容层 | 当前保持 blocked |
| 广告奖励重复/伪造 | 平台回调 + 幂等 reward ledger | 无完成回执不奖励 | 仅规格，未实现 |
| 同质化/侵权 | rights metadata、重复度和来源检查 | 隔离资产、只用原创/授权素材 | rights 字段门禁已实现，法律审查未做 |
| 批量错误扩散 | 每候选独立 accepted/rejected | 共享内核变更使批次证据失效 | 已实现批次隔离 |
| “准确率保证”被误解为模型正确 | 相同门禁、失败升级、模型自评不算证据 | 只承诺 fail-closed 质量契约 | 已明确 |
| 玩法无趣 | 真实人工试玩 | 停止或重开玩法规格 | 待人工验收 |
