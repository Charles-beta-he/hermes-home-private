# UAEC React H5 工作流落地与 ToB 产品化审计

## 1. 目标与边界

目标：把当前真实工作项目中已经运行的 Agent 辅助研发流程整理为可复用、可演示、可交付的 ToB 工作流能力。

边界：
- 本文只整理流程和证据结构，不修改业务代码。
- UAEC、仓库路径、域名、业务字段和认证信息均属于内部事实；对外案例必须匿名化。
- 本地验证不等于远程 CI、部署、真机、生产或资金链路验收。

## 2. 当前已有的工作流闭环

```text
项目接入
  → 项目 Profile / SSOT 建立
  → 参考端(Android)与目标端(H5)建模
  → Capability Backlog 分域、分优先级
  → 选择最小安全 Slice
  → Spec / 风险 / 权限边界
  → 开发与局部提交
  → 类型、Lint、Build、交互、截图验证
  → 独立 Review / 证据包 / 认证等级
  → 状态、事件、Receipt、Continuation 回写
  → 下一 Slice 或停在权限门
```

### 已落地能力

| 层 | 当前载体 | 可产品化价值 |
|---|---|---|
| 项目建模 | `project-profiles/uaec-react-h5.json` | 快速建立项目上下文、技术栈、红线、导航和权限边界 |
| 真相源治理 | Android 参考仓 + React H5 目标仓 + SSOT | 防止仅按 PRD、口述或单一仓库误判 |
| 能力拆解 | `workflow/parity-backlog.json` | 按业务域、优先级、风险、参考文件和目标文件拆解工作 |
| 风险路由 | profile 中的 capability tags / hazard inventory | 根据键盘、滚动、鉴权、Token、PWA 等风险自动选择验证路径 |
| 最小切片执行 | slice → scoped diff → local commit | 控制变更范围，避免大范围重写和回归 |
| 正向门禁 | lint / typecheck / build / smoke / screenshot | 用真实运行证据替代“代码看起来完成” |
| 负向门禁 | 不删路由、不改认证字段、不泄露 Token、不越级声明 | 保护既有业务约束和安全边界 |
| 权限治理 | local-safe 与 push/deploy/device/payment 分离 | Agent 可自治推进安全工作，外部副作用保持人工授权 |
| 可追踪执行 | state / event / lease / receipt | 支持续跑、失败预算、执行归属和审计 |
| 交付认证 | evidence / reviewer vote / certification level | 把完成声明绑定到测试、截图、代码和独立审查证据 |

## 3. 当前证据锚点

- 项目入口：`/Users/charles/.hermes/project-profiles/uaec-react-h5.json`
- 项目 SSOT：`/Users/charles/.hermes/workflows/projects/uaec-react-h5/`
- 能力 Backlog：`workflow/parity-backlog.json`
- 当前交付状态：`workflow/project-delivery-state.json`
- 进度账本：`progress-ledger.md`
- 模块对齐计划：`evidence/2026-07-16-full-alignment-plan.md`
- 运行证据：`evidence/**`
- 执行回执：`receipts/project-delivery-runs/**`

当前交付状态文件记录：仓库位于 `dev`，工作树干净，`origin/dev` ahead/behind 均为 0；本地权限开放，但 push、deploy、外发、凭证、支付和破坏性操作均关闭。该状态是运行快照，不证明所有业务功能已完成。

## 4. 必须先解决的真实性问题

### P0：完成度投影存在冲突

`progress-ledger.md` 在 2026-07-14 声明“100% Android functional parity”；但更新日期为 2026-07-16 的 `evidence/2026-07-16-full-alignment-plan.md` 仍给出：

- contract 16%
- legalTender 6%
- mine 5%
- property 1%
- home 30%
- market 35%
- bbtrade 33%
- login 14%
- assets 57%

因此，现有“100%”最多只能解释为某个有限模块集、某一认证口径或某一时点的局部结论，不能直接作为整个产品的对外案例主张。产品化前必须统一：范围、分母、认证等级、时间点和剩余门禁。

### P1：Profile 过度承载会话级认证细节

项目 Profile 已包含大量 slice 级证据和 reviewer 信息，降低了入口可读性，也容易产生陈旧投影。建议拆为：

1. 稳定项目事实与红线；
2. 当前状态投影；
3. 能力 Backlog；
4. 证据索引；
5. 历史 receipts/events。

### P1：调度仍是轮询传输

`project-delivery-state.json` 明确标注：`polling_transport_with_state_driven_eligibility_not_true_event_dispatch`。对外不能描述成真正事件驱动；可描述为“状态驱动资格判断 + 轮询调度”，后续再升级事件触发。

### P1：证据等级需要面向客户翻译

内部的 L3、reviewer vote、receipt、lease 对研发治理有价值，但客户更容易理解：

- 改了什么；
- 为什么安全；
- 测了什么；
- 哪些没有测；
- 谁批准了外部动作；
- 出问题如何回滚和追责。

## 5. 可形成的首个 ToB 产品

建议不是泛化为“帮企业部署 Agent”，而是先定义为：

> AI 辅助软件交付工作流治理：把需求、参考实现、开发切片、质量验证、权限审批、证据归档和持续交付串成可审计闭环。

### 客户画像

- 有多个前端、App、H5 或管理后台实现；
- 存在跨端功能对齐、旧系统重写、需求遗漏和回归风险；
- 已使用 AI 编码，但缺少边界、审查和验收机制；
- 项目状态主要靠群聊、口头汇报或零散文档；
- 不敢让 Agent 自治执行 push、部署或生产操作。

### 首单范围

1. 选择一个真实项目；
2. 建立项目 Profile 与真相源地图；
3. 生成按业务域拆解的 Capability Backlog；
4. 配置正向/负向质量门禁；
5. 跑通一个最小功能 Slice；
6. 输出证据包、状态看板和权限边界；
7. 培训项目负责人如何继续运行。

### 可量化指标

- 需求到可执行 Slice 的转换时间；
- 每个 Slice 的验证覆盖率；
- 未经授权的外部动作次数（目标为 0）；
- 回归问题发现阶段；
- 状态声明与证据的一致率；
- 交接后恢复上下文所需时间；
- 重复流程中可复用模板/规则比例。

## 6. 对外案例的匿名化叙事

可表述为：

> 某金融交易团队需要将原生移动端能力迁移到 React H5/PWA。项目存在多业务模块、鉴权边界、实时行情、资金精度、移动键盘和跨端交互差异。通过项目真相源建模、Capability Backlog、最小切片交付、正负门禁、截图/交互验证和权限分层，建立了可续跑、可审计的 Agent 辅助交付闭环。

不得对外暴露：客户名称、真实域名、仓库地址、认证字段、接口地址、Token 规则细节、未公开业务功能和内部 commit/receipt。

## 7. 产品化落地顺序

1. 先修正“100% 对齐”口径冲突，建立唯一当前状态投影。
2. 将现有工作流压缩为一张生命周期图和一份 SOP。
3. 从当前项目抽取通用模板：Profile、Backlog、Slice Spec、验证清单、Evidence Packet、Authority Matrix、Continuation Packet。
4. 用一个已完成的有限 Slice 制作匿名案例，禁止使用全项目完成声明。
5. 在第二个工作项目复用，验证哪些是通用能力、哪些只是 UAEC 特例。
6. 两个项目复用通过后，再包装成诊断服务和首单交付套餐。

## 8. 当前结论

现有项目不是“从零构思 ToB Agent”的素材，而是已经运行过的 AI 辅助软件交付控制面原型。最有商业价值的不是单个 Skill 数量，而是：

- 多真相源对齐；
- 风险感知的任务拆解；
- Agent 自治与人工权限边界；
- 正向和负向验收证据；
- 可恢复、可审计、可持续运行。

当前可进入内部整理与匿名案例制作，但在状态口径冲突收敛前，不应对外宣称整个项目实现了 100% 跨端对齐。
