# 游戏产品分层契约

## 1. GameplayKernel（独立玩法）

负责：
- board/state schema
- player actions
- deterministic transition
- win/lose conditions
- scoring
- seeded randomness
- difficulty envelope

禁止：主题名、角色名、平台 API、广告 SDK、付费入口、具体美术路径。

最小产物：`kernel_id`, `version`, `state_fields`, `actions`, `win_condition`, `lose_condition`, `score_rule`, `seed_policy`, `golden_cases`。

## 2. ContentPack（独立内容）

负责：
- theme/setting
- visual token refs
- copy and localization
- level parameter sets
- tutorial text
- audio/asset refs and rights metadata

允许调节：经玩法规格声明的 `tunable_parameters`。

禁止覆盖：`actions`, `state_fields`, `win_condition`, `lose_condition`, `score_rule`, `seed_policy`, `ad_policy`, `platform_api`。

## 3. Presentation

负责：场景、布局、动画、反馈、可访问性、性能预算。只消费 GameplayKernel 事件，不拥有胜负事实。

当前唯一实现目标为 Cocos Creator 3.8 系列。Cocos 场景、组件和资源只负责表现与输入投影；不得把胜负、评分、随机性或广告触发事实藏入场景脚本。`WorkPackage` 保持引擎中立，经摘要校验后由 `CocosIntegrationPacket` 适配。

## 4. PlatformAdapter

负责：启动/挂起、存储、分享、登录（若需要）、激励视频、合规与平台构建。平台失败必须返回 typed error；不得伪造广告完成或奖励发放。

Cocos 侧共享 `PlatformPort`，抖音实现绑定 `tt.*`、微信实现绑定 `wx.*`；两者必须分别由当前官方契约和真实 runtime receipt 晋级。引擎源码存在适配面不等于本地平台能力已通过。

## 5. MonetizationPolicy

单独版本化：
- 合法触点：失败后自愿复活、主动提示、额外步数；
- 禁止触点：首次进入立即强制广告、未完成广告却发奖励、内容包自行新增广告；
- reward 必须由平台回调证据触发，且幂等。

## 6. TelemetryContract

核心事件：`session_start`, `level_start`, `action`, `level_win`, `level_fail`, `assist_offer`, `ad_request`, `ad_complete`, `reward_granted`, `session_end`。

事件不得包含凭证和不必要个人信息。指标只作为实际上线后的观察契约，当前不伪造留存或收入数据。

## 7. 首个玩法：故障线路整理

一句话：玩家在有限步数内旋转/交换线路节点，使电源与目标设备形成无交叉、无短路的有效连接。

核心状态：网格、节点连接方向、电源、目标、剩余步数、种子。

核心动作：旋转节点、交换相邻节点、请求提示。

胜利：所有必需目标连通，且不存在短路/非法回路。

失败：步数为零仍未满足胜利条件。

内容包示例：数据中心抢修、太空站供能、城市夜景复电。三者只能改变视觉、文案和合法参数，不能改变动作与胜负规则。
