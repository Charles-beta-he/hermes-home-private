# 热门玩法观测台（Spec Brief）

## 目标

让研发流程持续获得“现在什么玩法正在抖音/微信小游戏中变热”的外部证据，并把具体产品拆成可比较的玩法机制，而不是依赖模型记忆、单次录音或搜索摘要。

## 非目标

- 不声称覆盖平台完整榜单；
- 不绕过登录、风控、付费数据或平台权限；
- 不把第三方文章中的历史排名标成当前实时排名；
- 不复制游戏名称、美术、关卡、文案或其他受保护表达；
- 不因某款产品短期上榜就直接冻结 GameplayKernel。

## 输入通道

按证据强度从高到低：

1. `direct_app_rank_capture`：用户在抖音/微信客户端打开小游戏榜单，提供带榜单名、排名、时间的截图或录屏；这是实时榜单的首选证据。
2. `direct_gameplay_capture`：用户提供游戏分享卡、入口链接、截图或 1–3 分钟实际试玩录屏；用于确认核心动作和状态转移。
3. `official_platform_case`：平台公开课、生态大会、官方案例和开发者后台可导出的只读数据。
4. `first_party_creator_report`：开发者演讲或访谈中的 DAU、玩法和增长陈述；保留“开发者自报”边界。
5. `third_party_rank_report`：DataEye、热力引擎、行业媒体等带日期的榜单/投放观察；只能作为候选或交叉信号。
6. `search_or_social_lead`：搜索结果、话题、评论、短视频帖子；只用于发现，不证明热度。

用户最低成本输入：每周一次抖音小游戏热门榜/畅销榜录屏，缓慢滚动 Top 30；对其中 5–10 款打开详情或试玩 30–60 秒。助手负责 OCR、去重、机制卡和跨周变化。

## 最小证据单元

每条观测必须保存：

- `observed_at`、`platform`、`source_type`，以及可回读 HTTPS URL 或绝对本地证据路径；
- 游戏名称或稳定标识；
- 榜单名、排名/播放/投放等原始信号；
- 信号实际发生时间，而不是只保存文章发布时间；
- 核心动作、闭环、胜负/退出条件和局长；
- `direct_readback` / `direct_playback` 标志；
- 来源身份、证据等级、访问时间和摘要；直接来源的 `source_type` 与 `evidence_level=direct` 必须一致；
- `subject_bindings` 将来源显式绑定到平台、游戏，排名证据还必须绑定榜单；
- `independence_key`（同一原始报告/视频的转载共用一个 lineage；任何来源如声明相同 `evidence_digest` 也会跨 direct/indirect 归并，不能靠改 source type 或 key 重复计数）；
- 可回读 URL 或本地证据路径；直接截图/录屏必须保存 SHA-256 摘要。只有本地媒体可重新读取且摘要一致时，直接证据才能参与 `verified_current_hot` 晋级；仅声明远端 URL 与摘要仍保持线索状态。

## 热度状态机

`search_lead → recent_market_lead → verified_current_hot → mechanic_observed → kernel_hypothesis`

- `verified_current_hot`：至少一条 7 天内、可本地摘要回读的客户端榜单直接证据；至少两个 7 天内、主体绑定正确且证据类型合格的独立 lineage；以及 7 天内可本地摘要回读的直接试玩证据。搜索/社交发现信号不参与该 quorum。
- `recent_market_lead`：60 天内存在主体绑定正确的排名/数值热度信号，但未满足实时榜单或独立来源门禁。来源的发布时间和访问时间也必须在 60 天内。
- `stale_lead`：只有超过 60 天的信号。
- `unranked_lead`：只有讨论或玩法描述，没有可核对热度信号。

同一文章被多个站点转载仍算一个来源；模型总结不算独立来源。状态会随 `as_of` 推进自动失效。

## 玩法机制卡

市场研究只向研发线输出抽象字段：

- `core_action`
- `state_transition`
- `session_loop`
- `goal_or_exit`
- `failure_pressure`
- `session_length_seconds`
- `randomness`
- `spectator_hook`
- `social_hook`
- `monetization_observation`
- `content_burden`
- `reusable_mechanics`
- `non_copyable_expression`

低成本模型可做 OCR 后的字段提取、标签、去重和聚类候选，但不得补造缺失证据，也不得把候选升级为 `verified_current_hot`。

## 当前证据边界（2026-07-26）

已获得两类可回读行业证据：

- 2026-06-22，36氪转载 DataEye 对抖音“开玉石”类产品的榜单与玩法观察；排名实际发生于 2026-05-30 至 2026-06-15 左右，属于近期市场线索，不是 7 天内实时榜单。
- 2025-12-25，GameLook/腾讯新闻记录《狙击外星人》开发者在抖音小游戏生态大会的分享；可支持历史爆款机制研究，不支持 2026-07 当前热度。
- 2026-05-11，网易号转述《2026 年小游戏获客增长趋势报告》；可支持“榜单之外还需投放、内容传播和增长信号”的方法判断，不提供单款实时榜单读回。

因此当前最高市场状态是 `recent_market_lead`，尚无任何游戏达到 `verified_current_hot`。实时门禁需要新的客户端榜单截图/录屏或等价官方直接证据。
