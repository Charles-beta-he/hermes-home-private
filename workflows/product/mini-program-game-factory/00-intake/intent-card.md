# Intent Card

## Objective

建立可复用的小程序游戏研发工厂：玩法内核与内容包独立，低成本模型可批量生成候选并编译成确定性工作包，所有模型共享同一质量门禁。

## User / Segment

- 研发者：熟悉 TypeScript/前端，希望低成本验证小游戏方向的个人或小团队。
- 玩家假设：偏好短局、低学习成本、即时反馈的抖音/微信小游戏用户。

## Scenario

需要连续验证多个题材与关卡内容，但不能让低成本批量生成污染玩法规则、商业化策略、平台契约或发布决策。

## Evidence So Far

- Source：用户明确认可“故障线路整理”方向，并要求抽象批量研发工作流。
- Source：千问录音《AI开发与求职策略深度分享会》，2026-07-26，114:13；约 44:00–1:10:00 涉及小游戏引擎、微信/抖音小游戏和激励视频。
- Boundary：录音属于讲师陈述，不证明平台政策、审核资格、留存或收益。

## Non-goals

- 本轮不接平台 SDK、不注册账号、不申请广告、不送审、不发布。
- 不承诺商业结果或“模型永不出错”。
- 不复制受保护玩法表达、品牌、美术、文案或关卡。

## Success Criteria

- Observable result：存在机器可读能力图、模型路由、分层契约和可执行批量工作包编译器。
- Acceptance evidence：单元测试、CLI 编译回执、恶意越权负例、确定性摘要。
- Stop condition：安全本地流程闭环到 `local_contract_verified`；平台/发布边界保持关闭。

## Authority Boundary

- Local artifact writes allowed: yes
- Taskpool enqueue allowed: no
- Code changes allowed: yes，仅此工作区本地工具
- External publishing/sending allowed: no
- Private access material needed: no
