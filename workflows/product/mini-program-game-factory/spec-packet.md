# 小程序游戏批量研发工厂：规格包

## 目标与成本函数

目标：建立“玩法内核与内容皮肤解耦”的小游戏研发工作流，使低成本模型可以批量生成候选内容和标准工作包，同时不绕过同一套确定性质量门禁。

优化顺序：
1. 玩法正确性、平台合规和用户体验不退化；
2. 每个变体可追溯、可复现、可回滚；
3. 降低高成本模型调用占比和人工重复劳动；
4. 提升内容变体吞吐量。

“准确率不受影响”的可执行定义不是模型永不犯错，而是：低成本模型的产物不得凭模型自评进入可构建/可发布状态；它必须通过与高成本模型产物相同的 schema、规则模拟、golden case、内容约束、平台契约和独立验收门禁。不确定、冲突或门禁失败时自动升级，禁止静默降级。

## Spec Brief

### Goal
- 形成独立的玩法内核、内容包、平台适配层和商业化层。
- 将研发流程抽象成稳定输入/输出的 Capability Graph。
- 允许低成本模型承担可验证、低风险、批量任务。
- 由确定性程序与证据门禁控制正确性，而非依赖模型规模。

### Non-goals
- 当前不注册抖音/微信小游戏账号，不申请广告权限，不送审、不发布。
- 当前不承诺收入、留存或平台审核通过率。
- 不用换皮掩盖玩法抄袭，不复制受保护的美术、文案、关卡或品牌。
- 不让低成本模型修改评分、胜负、经济、广告触发或平台 SDK 契约。

### Source facts and boundaries
- 来源：千问录音分享《AI开发与求职策略深度分享会》，2026-07-26，114:13。
- 录音约 44:00–1:10:00 提及 PixiJS、Phaser、Cocos Creator、微信/抖音小游戏、激励视频和休闲玩法。
- 录音是讲师陈述与平台 AI 纪要，不是平台政策或商业效果的权威证据。
- 平台版本、广告资格、送审政策必须在实际接入前重新读取官方文档。

### Business rules
1. GameplayKernel 只定义状态、动作、转移、胜负、评分和随机种子；不得包含题材文案或平台 SDK。
2. ContentPack 只提供主题、美术引用、文案、关卡参数和本地化；不得改写状态转移或商业化规则。
3. PlatformAdapter 负责生命周期、存储、分享、广告和合规 API；不得改变玩法结果。
4. MonetizationPolicy 单独版本化；广告只能位于明确的可选触点，不得由内容包暗中插入。
5. 每个生成产物必须记录 source_spec、model_route、prompt/template 版本、输入摘要和门禁结果。
6. 低成本模型只处理 allowlist 中的任务；任何 protected_surface 变更必须升级。
7. 不通过门禁的批次隔离到 rejected，不得自动修饰为 PASS。

### Invariants
- 相同 kernel 版本、关卡参数与随机种子产生相同结果。
- 更换 ContentPack 不改变胜负、评分、概率和广告频率。
- 更换平台适配器不改变核心玩法结果。
- 所有候选变体都能追溯到冻结的玩法规格。
- 模型输出不是验收证据；测试、模拟、官方契约与人工试玩才是。

### Acceptance criteria
- 玩法、内容、平台、商业化四个边界在机器可读资产中独立存在。
- 路由器对低风险任务选择 low_cost，对 protected_surface、低置信度和门禁失败选择 escalate。
- 工作包编译器拒绝内容包覆盖玩法字段。
- 编译器对相同输入产生确定性输出。
- 测试包含正例、边界、恶意越权、低置信度升级和换皮不改玩法的负例。
- 所有本地验证通过；外部发布状态保持关闭。

### Evidence required
- 文件 readback；
- Python 单元测试；
- 示例工作包编译结果；
- 负例拒绝输出；
- 规格到证据 Converge Matrix。

## 候选路径与选择

A. 每个游戏独立开发：上手快，但重复劳动、漂移和成本最高。

B. 单体模板大量换皮：吞吐高，但玩法/内容耦合，容易产生同质化、侵权和错误扩散。

C. 冻结玩法内核 + 内容包 + 平台适配 + 商业化策略 + 证据门禁：初始抽象成本更高，但最符合低成本批量推进和准确性约束。

选择 C。低成本模型只扩大候选生成能力，不扩大合并、发布或平台写入权限。

## 风险等级与权限边界

- local_reversible：规格、工作包、校验器、测试、离线模拟。
- external_read：平台官方文档核对，后续执行。
- external_write：账号注册、广告申请、送审、发布，当前关闭。
- payment/credential：当前关闭，必须人工处理。

## Cocos Engine 整合决策（2026-07-27）

### Goal
- Cocos Creator 3.8 系列是唯一游戏制作运行时；`WorkPackage` 继续保持引擎中立。
- 增加确定性的 `WorkPackage → CocosIntegrationPacket` 适配层，为后续 Cocos 项目模板、场景、内容和平台适配实现提供稳定输入。
- 将 Cocos 本地候选物料化、Creator 构建、开发者工具导入、真机、上传、审核和发布拆成独立证据阶段。

### Non-goals
- 不因采用 Cocos 而自动冻结玩法、开放工作包晋级或继承旧 verifier 的认证。
- 不把 Cocos Engine 仓库的小游戏适配源码等同于本地 Creator 构建成功。
- 当前不调用 Creator、不登录开发者工具、不写入 AppID/凭据、不上传、不送审、不发布。
- 不把 Godot/Laya/Unity 项目复制进运行时；它们仅作为 exporter、bridge 或 CI 结构参考。

### Source facts and boundaries
- 技术选型由用户明确确认：游戏制作采用 Cocos Engine。
- 只读源码调研确认 `cocos/cocos-engine` 的 3.8 系列包含微信与 ByteDance/TikTok mini-game PAL/平台实现；这只证明引擎源码存在相关适配面。
- 当前机器 fresh readback 未发现可调用的 Cocos Creator。Homebrew Node 25.8.1 因缺失动态库不可运行，但隔离的 NVM Node 24.14.0、npm/npx 11.9.0 已通过显式 PATH 真实执行；项目工具链不得依赖故障的全局 Node。
- Cocos Creator 的精确安装版本、CLI、build target、项目模板和平台开发者工具仍需后续真实安装/官方文档/执行 receipt 绑定。

### Business rules and invariants
1. `CocosIntegrationPacket` 必须校验上游 `compile_digest`，拒绝被篡改的 WorkPackage。
2. 适配输出只允许声明 `candidate_only`，所有构建、凭据、提交、发布和支付 authority 必须为 false。
3. Cocos profile 必须显式绑定 3.8 系列和来源 commit；不得接受未固定版本或其他引擎。
4. 相同 WorkPackage 与 profile 必须产生相同 integration digest。
5. 物料化只写调用者指定的本地 staging 根目录，拒绝符号链接根目录和路径穿越。
6. 平台能力以 `contract_pending`/`build_pending` 表示；未知 target/CLI 不得硬编码为已支持。
7. GameplayKernel、ContentPack、PlatformAdapter、MonetizationPolicy 的所有权边界保持不变。

### Acceptance criteria
- 新增机器可读 Cocos profile、integration schema/packet 和工作流说明。
- 测试先证明缺少适配器、摘要篡改、错误引擎/版本、路径逃逸和 authority 打开均会失败。
- 有效样例可确定性生成本地 Cocos candidate bundle，并从磁盘读回摘要一致。
- 原 68 项本地契约测试保持通过；新增测试通过；JSON 和 Python 静态检查通过。
- CapabilityGraph 和 workflow state 明确区分 `cocos_integration_planned/materialized` 与 `runtime_verified/platform_ready/published`。

## 当前闭环边界

本轮从 `local_contract_verified` 推进到 Cocos 本地整合契约与候选物料化；真实 Creator 构建、可玩运行时、平台 SDK、开发者工具、真机、审核和商业结果仍需各自 receipt，不能由本轮证据继承或推定。

## 全盘推进 Loop Contract（2026-07-27）

```yaml
objective: 除第三方注册、凭据、人工产品验收和平台外部写之外，把 Cocos 游戏制作链细化为本地可执行、可测试、可回放的工程闭环
baseline: bde9d8310be50d5b90d2aeea983505da15c4ce0c + current scoped C1-C3 mutable slice
authority:
  max_side_effect: scoped_local_write_and_local_process
  external_write: false
  credentials: false
  payment: false
budgets:
  max_iterations: 12
  max_repeated_failure: 2
acceptance:
  - 可运行 GameplayKernel 与 ContentPack，确定性重放和负例通过
  - 微信/抖音 PlatformPort 本地 stub 可运行且绝不伪造官方 SDK 成功
  - 可生成摘要冻结的 Cocos Creator 3.8 项目模板
  - 缺少 Creator 时 build preflight 结构化 fail-closed、零伪造产物
  - 本地 runtime smoke、candidate manifest、handoff verifier 可真实执行
  - 全套回归、Python/TS/JSON、fresh readback 与 scoped Git identity 收敛
stop_conditions:
  - success
  - exact human or third-party boundary
  - repeated-failure budget reached
```

非目标：不自动注册/登录 Cocos、抖音或微信；不输入 AppID/密钥；不上传、审核、发布、支付；不把本地 stub 冒充官方 SDK/Creator 运行时。

## Reference-ad 实验通道（2026-07-30）

用户提供的广告片段可以打开一条 candidate-only 的 clean-room 实验通道（`07-build/reference_ad_experiment.py` + `experiments/stack-path-runner/`）：

- 输入必须是 `source_type=user_supplied_reference_ad`，本地媒体为常规文件并通过声明的 SHA-256 摘要读回；符号链接、缺失文件与摘要不匹配一律 fail closed。
- 必须显式声明 `verified_current_hot=false`、`rank_claimed=false`；任何榜单/热度声明被拒绝。该通道的产物永远不能满足 `verified-current-hot` 的 market-to-kernel 门禁。
- 观察必须区分可见事实、模型推断与未知，并给出 clean-room 可复用机制与不可复制表达清单；来源 MP4/帧只作证据，不进入任何交付资产。
- 机制卡必须恰好包含 warm-up + skill-gate 两关，authority 保持 candidate-only：不冻结内核、不编译工作包、不构建 Cocos、不送审、不发布。
- 产出是本地浏览器 vertical slice 与确定性 receipt；`creator_build_verified=false`、`platform_ready=false`、`published=false` 不变。
