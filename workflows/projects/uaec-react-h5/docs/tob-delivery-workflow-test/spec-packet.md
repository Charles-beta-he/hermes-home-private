# Spec Packet — ToB AI 辅助软件交付工作流 v1

## 目标

使用 UAEC React H5 的真实项目进度作为内部测试样本，形成可复用、可审计、可交接、可验收的 ToB 交付工作流；工作流必须能识别项目状态声明与证据口径冲突，而不是把文档存在误判为交付完成。

## 非目标

- 不修改 UAEC 业务代码、项目状态或远程仓库。
- 不把 UAEC 客户名、域名、接口、认证字段、仓库路径等内部事实写入公共案例模板。
- 不把本地构建、截图或 reviewer vote 提升为生产、真机、资金链路或全项目验收。
- 不要求交付物绑定 Pi；允许 Hermes、其他 Agent 或混合实现。

## 已证据化事实

1. 项目已建立 Profile、SSOT、Capability Backlog、状态、事件、lease、receipt 和 evidence 结构。
2. `progress-ledger.md` 的 2026-07-14 条目声明“100% Android functional parity”。
3. 更新日期为 2026-07-16 的全模块计划仍给出多个模块 1%–57% 的对齐度。
4. 当前交付状态快照记录仓库干净、ahead/behind 为 0，但明确不证明业务范围全部完成。
5. push、deploy、外发、凭证、支付和破坏性动作没有授权。

## 不变量

- 每个完成声明必须包含明确 scope、时间点、证据引用、适用阶段 `stage_refs`、最高可支撑阶段 `max_stage` 和非空 limitations；每个 accepted stage 必须由未超过 `max_stage` 的 verified claim 覆盖。
- 新证据与旧结论冲突时，交付状态必须降级为 `blocked` 或 `ready_for_review`，不能继续标记 `accepted`。
- 所有外部副作用必须由 Authority Matrix 明确授权。
- 客户验收与内部技术验证分离。
- 负向要求必须有负向证据或明确未验证状态。
- 可公开案例必须通过匿名化检查。

## 路径选择

候选路径：

- A：只写一份 ToB SOP。成本低，但无法证明工作流能识别真实项目冲突。
- B：在项目 SSOT 中硬编码 UAEC 专用流程。能运行，但无法复用，也容易泄漏客户事实。
- C：建立通用交付协议、机器可读 Manifest、校验器和 UAEC 内部测试夹具。兼顾复用、证据和隐私。

选择 C。通用规则进入 `ai-agent-b2b-service` skill；项目事实和测试结果留在 UAEC SSOT。

## 交付级验收标准

1. 存在覆盖售前、诊断、合同/规格、方案、试点、生产交付、验收交接、运维复盘的完整生命周期。
2. 每阶段定义输入、必需产物、入口门、退出门、责任人和允许状态。
3. 存在机器可读的 engagement manifest 模板。
4. 校验器能对以下问题 fail closed：
   - 未解决的证据冲突；
   - verified claim 缺少 scope/evidence，或引用未知证据 ID；
   - accepted 或 ready_for_review stage 缺少 artifact/evidence、artifact 不存在、引用未知 ID，或缺少该阶段要求的语义类型；
   - 阶段越序、超出 completion boundary 仍处于活动状态，或 closure_state 与 completion boundary 不一致；
   - 本地绝对证据路径缺失、SHA-256 不匹配、日期损坏或位于未来；
   - 未知外部动作、外部动作授权缺少目标、scope、与 action/target/scope 精确绑定的 typed authority grant、回滚或 readback，或 credential/payment 被错误启用；
   - accepted closure 没有任何 verified outcome、仍含 unverified/disputed claim，或 accepted_risk 缺少批准人、日期、补偿控制和证据；
   - public case 含敏感标记、未引用 typed 发布权/匿名化证据，或 confidentiality 不是 public；
   - client_acceptance=accepted 时 S6 未 accepted，或 S6/S7 在没有非 placeholder 身份/scope、有效日期和 typed acceptance 证据的明确客户验收时越级通过；
   - superseded closure 缺少边界阶段 superseded 状态，或 `superseded_by` 未解析到带证据且状态有效的 registered successor engagement；
   - production/acceptance/operations 阶段只依赖 `max_stage` 较低的 pilot claim；
   - 错误嵌套类型导致校验器崩溃。
5. 未完成的 in_progress Manifest 不得被 completion_boundary 强制伪装为 accepted；模板中的 placeholder 必须保持 RED，直到被真实值替换。
6. UAEC 冲突夹具必须失败（RED）。
7. 将“全项目 100%”降级为有限范围结论并保留冲突后，内部交付实例必须通过结构校验（GREEN），但公开案例状态保持 `not_ready`。
8. 更新 `ai-agent-b2b-service` 入口，指向新协议、模板和校验器。
9. 对已接受阶段使用的本地 source/artifact 固定文件哈希，源文件改变后 GREEN 必须失效并要求刷新证据；用于认证候选的项目事实应复制为 commit 内 evidence snapshot，避免依赖 dirty/untracked 外部字节。

## 风险等级与权限

风险等级：local_reversible。

允许：读取现有证据、创建项目 SSOT 测试文件、更新本地 skill、运行本地校验。

禁止：业务代码修改、push、deploy、外发、凭证输入、生产写入、支付和删除历史证据。

## 所需证据

- 文件回读；
- RED 命令非零退出和具体错误；
- GREEN 命令零退出；
- 校验器单元测试；
- 更新后 skill 回读；
- Converge Matrix。
