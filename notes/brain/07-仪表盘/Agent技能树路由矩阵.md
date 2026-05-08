---
title: Agent技能树路由矩阵
created: 2026-05-08
type: control-plane-overlay
concepts: [skill tree, route matrix, project memory, systems engineering, agent control plane]
---

# Agent技能树路由矩阵

> 目的：补上“有很多 skills，但没有显式项目路线图”的缺口。它不替代 skill graph；它把任务类型映射到可执行能力链。

## 四层技能树

| 层 | 作用 | 存放内容 | 不应存放 |
|---|---|---|---|
| L0 理论/治理 | 决定为什么这样做 | 系统工程、控制论、P10、风险路由 | 具体项目进度 |
| L1 通用领域 | 决定做哪类事 | 前端、后端、文档、MCP、研究、桌面整理 | 项目专属业务状态 |
| L2 项目工作流 | 决定这个项目如何做 | workpad、anchors、red lines、验收矩阵 | 全局用户画像 |
| L3 会话执行 | 决定现在做哪一步 | todo、临时假设、当前验证命令 | 跨会话稳定事实 |

## 前端项目默认路线

| 阶段 | 技能/能力链 | 输出 |
|---|---|---|
| Intake | requirement-clarification + source-driven-development + read-repo | 目标、非目标、锚点、风险 |
| Architecture | p10 + p9 + architecture-optimization-loop | P10/P9 任务树 |
| Implementation | test-driven-development + incremental-implementation + project modify-code | 小切片修改与回归测试 |
| UI Closure | browser-harness-integration + visual-regression + uimax-audit + fixing-accessibility/motion/metadata | 交互闭环证据 |
| Verification | requesting-code-review + post-deploy-verification + multi-model-thinking(按风险) | build/test/UI/多模型验证 |
| Deposition | obsidian + project workpad + ADR/UI_TEST_CASES | 项目记忆沉淀 |

## 路由规则

- 低风险单文件：L1 + L3 即可，不跑四模型。
- 跨模块业务流：L1 + L2 + browser/Playwright 验证。
- 架构/原型漂移/删除功能：必须 P10 + workpad anchors + 多模型 T2/T3。
- 项目状态、业务流程、验收矩阵进入 Project Workpad，不进 persistent memory。
- 用户稳定偏好、职业目标、长期红线进入 memory；但必须压缩成不会过期的事实。

## 与 Skill Graph 2.0 的区别

- Skill Graph：skill 之间有没有循环、深度、依赖，属于拓扑健康。
- Skill Route Matrix：某类任务应该加载/执行哪些技能，属于语义控制面。

两者互补：前者防混乱，后者防“会很多但不会调度”。
