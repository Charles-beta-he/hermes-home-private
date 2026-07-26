# Decision Log

## 2026-07-26 — 选择内核/内容/平台/商业化四层分离

- Decision：采用冻结 GameplayKernel + ContentPack + PlatformAdapter + MonetizationPolicy，而非每游戏独立开发或单体换皮模板。
- Evidence：用户目标要求批量低成本推进且不影响准确性；分层使 protected surfaces 可被机器门禁保护。
- Rejected：每项目独立开发（重复与漂移高）；单体换皮（耦合、侵权与错误扩散风险高）。
- Next state：local contract implementation。

## 2026-07-26 — 将“准确率保证”编译为 fail-closed 质量契约

- Decision：不承诺模型本身永不犯错；保证低成本产物仅为 candidate、共享同一门禁、未知/失败自动升级。
- Evidence：12 个本地行为测试、单/批次 CLI 回读。
- Rejected：按模型品牌默认信任；让模型自评作为验收证据。
- Next state：R0 规则模拟器。

## 2026-07-26 — 外部副作用保持关闭

- Decision：本轮不注册、不登录、不申请广告、不送审、不发布。
- Evidence：工作包与批次回执中的 authority flags 全为 false。
- Next state：平台官方文档只读核对可在后续独立推进。
