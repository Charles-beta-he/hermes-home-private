# 批量研发流程

## 主链

来源注册
→ 带时间戳的市场快照
→ 热门候选去重与证据分级
→ 玩法机制卡
→ 跨来源/跨周期趋势聚类
→ 玩法假设卡
→ 玩法内核规格
→ 纸面/离线规则模拟
→ 内核冻结
→ 内容包并行生成
→ 内容静态门禁
→ 工作包编译
→ 实现切片
→ 单元/模拟/性能/平台契约门禁
→ 人工试玩
→ 小流量实验（未来，需发布授权）
→ 指标回读
→ 保留/迭代/停止

## 市场观测前置回路（M0）

1. 每周保存抖音/微信客户端榜单截图或录屏；网页榜单、行业报告和社交帖子只作补充。
2. 对同一游戏的多条视频、转载和榜单记录去重，转载不增加独立来源数。
3. 用 `hot_game_observatory.py` 按 `as_of` 计算证据新鲜度；超过窗口自动降级。
4. 只有 7 天内直接榜单读回、两个独立来源、摘要绑定人工内容分类和使用不同媒体摘要的直接试玩同时成立，才标记 `verified_current_hot`。
5. 市场观测输出 `MechanicObservation`，只描述动作、状态、闭环、压力和传播钩子，不向玩法线复制名称、美术、关卡或数值。
6. 单次上榜只产生 `kernel_hypothesis`；仍需差异化、规则模拟和人工试玩，不能直接冻结内核。
7. 用 `market_loop_gate.py` 将市场 receipt 与抽象玩法候选串联：只有 `verified_current_hot` 观察且候选显式声明非空 `proposed_changes`，并且 `proposed_changes`、`abstract_mechanics`、`differentiation` 均不触及保护面时，才可进入 `kernel_hypothesis`；无论是否进入，`may_freeze_kernel`、`may_compile_work_package` 和发布权限均保持 false。
8. 当前市场候选的确定性读回保存到 `evidence/market-loop-receipt-2026-07-26.json`；`accepted=0` 是缺少直接证据时的预期 fail-closed 结果。

当前输入规范、状态机和人工采集方法见 `01-discovery/hot-game-observatory.md`。

## 两条独立生产线

### 玩法线（低吞吐、高精度）

1. 提出核心动作与目标。
2. 明确状态机、随机性、胜负和评分。
3. 设计 5 个 golden cases 和 5 个反例。
4. 离线模拟可解性、确定性和难度边界。
5. 高质量模型或人工审查玩法规格。
6. 冻结 kernel 版本。

玩法线禁止批量低成本模型直接改写 protected surfaces。

### 内容线（高吞吐、低成本）

1. 读取冻结 kernel 与 tunable parameter allowlist。
2. 批量生成主题、文案、关卡参数和资产 brief。
3. 执行 schema、禁词、重复度、版权来源、参数边界检查。
4. 编译成候选工作包。
5. 失败项隔离；通过项进入实现/预览队列。

## 研发切片

M0：热门玩法观测台、快照、机制卡和趋势聚类；无实时直接证据则保持候选态。
R0：规则模拟器，不依赖引擎。
R1：单关卡可玩闭环。
R2：内容包加载与三主题一致性测试。
R3：存档、恢复、错误态。
R4：平台适配 stub 契约；不伪造真实平台能力。
R5：真实平台 SDK 与广告回调（需官方文档、账号和人工授权）。
R6：送审/发布/指标观察（外部写，需精确授权）。

### Cocos 制作与平台证据链

C1：固定 Cocos Creator 3.8 integration profile，只记录已读回的引擎源码身份和默认关闭权限。
C2：校验 `WorkPackage.compile_digest`，生成确定性 `CocosIntegrationPacket`。
C3：物料化本地 candidate bundle，记录每个输入/生成文件 SHA-256；不修改真实 Cocos 工程。
C4：读回 exact Creator 安装、版本、CLI 与模板摘要，冻结 Cocos 项目模板。
C5：实现单关卡可玩闭环；GameplayKernel 不依赖 Cocos 场景状态，内容包可替换。
C6：基于当前官方契约分别实现抖音 `tt.*` 与微信 `wx.*` PlatformAdapter。
C7：使用 exact build target 构建，保存命令、exit code、产物目录和摘要。
C8：开发者工具导入、模拟器编译、真机预览分别生成 receipt。
C9：上传与审核只在精确人工授权后执行，并回读平台状态。
C10：发布与回滚分别授权，回读线上版本和回滚结果。

当前只完成 C1–C3；C4–C10 blocked。

## 质量门禁

G0 Market：热度、机制和时间分别绑定原始来源；实时热度必须满足新鲜度、独立来源和直接试玩门禁。
G1 Spec：玩法字段完整、无内容/平台污染。
G2 Determinism：同输入同结果。
G3 Golden：正反例全通过。
G4 Content Isolation：内容不能覆盖 protected surfaces。
G5 Rights：资产来源与许可字段齐全。
G6 Platform Contract：SDK 字段来自当前官方契约；未知即阻塞。
G7 Human Playtest：乐趣、可理解性、公平性由人工试玩确认。
G8 Release：构建、性能、隐私、审核材料与回滚齐全。

## 批量执行策略

- 并行单位：不同 ContentPack、文案、本地化、资产 brief、测试数据。
- 串行单位：同一 kernel 的规则修改、经济/广告策略、平台 SDK、共享模板。
- 批次上限由验证成本决定，不由模型吞吐决定。
- 任一共享内核修订使其后的旧门禁证据失效，必须重新编译和验证。

## 终止条件

- 玩法在小样试玩中无法形成清晰反馈循环；
- 内容只能靠侵权或诱导广告成立；
- 平台政策不允许目标商业化；
- 获客/留存实验在预设阈值下持续失败；
- 每新增内容包的验证成本高于复用收益。
