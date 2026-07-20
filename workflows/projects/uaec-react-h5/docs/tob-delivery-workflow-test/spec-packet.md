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

- 每个完成声明必须包含明确 scope、时间点、证据引用和未覆盖边界。
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
   - verified claim 缺少 scope/evidence；
   - accepted stage 缺少 artifact/evidence；
   - 外部动作授权缺少目标、回滚或 readback；
   - public case 含敏感标记或未通过匿名化；
   - final acceptance 在前置阶段未 accepted 时越级通过。
5. UAEC 冲突夹具必须失败（RED）。
6. 将“全项目 100%”降级为有限范围结论并保留冲突后，内部交付实例必须通过结构校验（GREEN），但公开案例状态保持 `not_ready`。
7. 更新 `ai-agent-b2b-service` 入口，指向新协议、模板和校验器。

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
