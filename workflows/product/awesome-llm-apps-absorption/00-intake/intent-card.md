# Intent Card

## Objective

将 `Shubhamsaboo/awesome-llm-apps` 固定版本中的应用样例转化为可检索的功能目录、候选模块池、Loop 推荐结果和一个本地临时工作流；不批量安装或执行上游应用。

## User / Segment

Hermes 使用者，希望将高价值开源功能逐步转化为 Hermes 可组合能力。

## Scenario

从大型 AI 应用示例库中去重底层能力，先建立模块池，再按用户意图临时组合工作流，后续按证据逐项复刻。

## Evidence So Far

- Source: https://github.com/Shubhamsaboo/awesome-llm-apps
- Pinned commit: `426cfa66b5fd832090038c36e50a6aa1dab3119c`
- License: Apache-2.0（仓库根 LICENSE）
- README claim boundary: 100+ templates、provider-agnostic、tested end-to-end 均为上游声明；本轮不视为本地运行证明。

## Non-goals

- 不批量安装依赖或导入外部 prompts/skills/hooks。
- 不填写 API key，不调用收费服务。
- 不声称任何上游应用已在本机运行。
- 不直接修改 Hermes 核心、全局路由、cron、taskpool 或 AgentOS。
- 不将候选模块直接提升为 canonical。

## Success Criteria

- 生成带源码路径证据的功能目录。
- 生成符合 Hermes capability module schema 的候选模块注册表。
- Loop 能从功能吸收意图推荐并匹配模块，而不是全部报缺失。
- 创建一个 local-only 临时工作流，明确节点、门禁、输入输出和未证明边界。
- 验证 JSON、模块 schema、Loop receipt 及 side-effect flags。

## Authority Boundary

- Local artifact writes allowed: yes
- Taskpool enqueue allowed: no
- Hermes core code changes allowed: no
- External publishing/sending allowed: no
- Private access material needed: no
