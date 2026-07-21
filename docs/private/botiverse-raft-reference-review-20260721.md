# Botiverse Raft 多 Agent 协作项目公开证据审查

审查日期：2026-07-21

## 1. 结论摘要

用户描述的“Raft 多 Agent 协作框架”高概率对应 Botiverse 的 Raft 产品，而不是一个名为 `raft-multiagent` 的公开 GitHub 仓库。匹配依据包括：

- 产品和文档统一使用 Raft 品牌与 `raft.build` 域名；
- 文档明确描述人类与多个 Agent 在同一 server/channel/task/thread 中协作；
- 文档描述 Agent 自动 claim 任务、拆分工作、共享上下文和进入 review 状态；
- `botiverse/raft-external-agents` 提供真实可运行的 Claude Code 外部 Agent 通道插件。

但宣传语混合了可验证事实、产品文档声明和无法核实的传播指标：

- “多 Agent 协作”：有公开文档和外部运行时代码支持。
- “像真实团队一样自动分工”：有任务拆分、共享频道、单一 owner、自动 claim 和 review 工作流的文档支持，但属于产品行为说明，不等于公开核心源码证明。
- “任务路由”：公开证据只支持频道/上下文形成的粗粒度 eligibility routing 与 claim 协调。
- “智能分配”：没有找到公开 allocator、评分器、策略模型、特征输入、决策日志或相关测试，不能确认。
- “最新 1.4”：没有公开 release/tag/package 证据支持。公开包版本分别为 `0.1.0`、`0.1.0` 和 `0.3.1`。
- “23 万+关注”“17 小时引爆开发者圈”：没有可归属的平台、链接、时间窗口或快照，未核实；这也不是 GitHub 架构证据。

核心项目仓库未公开，因此本次是“公开产品行为 + 外部运行时插件”的边界审查，不是 Raft 核心调度器源码审计。

## 2. 仓库消歧

### 2.1 GitHub 精确搜索结果

对 `raft-multiagent` 执行 GitHub repository、issue、commit 搜索：

- repositories：0
- issues：0
- commits：0

Code 搜索出现 27 条结果，但主要因为字符串出现在 `VillagerAgent-Minecraft-multiagent-framework` 等无关文本中，不构成 Raft 仓库身份。

因此，`raft-multiagent` 更像搜索关键词，而不是公开仓库 slug。

### 2.2 选定候选：Botiverse Raft

公开组织：`https://github.com/botiverse`

组织公开元数据（2026-07-21 查询）：

- followers：97
- public repositories：16
- bio：`Building the next civilization.`

关键公开仓库：

1. `botiverse/raft-docs`
   - 描述：Public Raft documentation site
   - stars：7
   - forks：0
   - watchers/subscribers：0
   - 创建：2026-06-18
   - 无 GitHub license 元数据

2. `botiverse/raft-external-agents`
   - 描述：Raft external agent runtime plugins and wake bridge adapters
   - stars：3
   - forks：0
   - watchers/subscribers：0
   - 创建：2026-06-09
   - 无 GitHub license 元数据

`botiverse/raft` API 返回 404。可能是私有仓库或不存在；公开证据无法区分，不能推断内部实现。

### 2.3 排除的相似候选

宽泛搜索还会出现 `multica-ai/multica`：

- 它有 Squads、多 Agent delegation 和任务队列；
- 查询时约 41,006 stars；
- 当前 package 版本 `0.4.7`；
- owner、品牌、域名和版本均与 Botiverse Raft 不同。

它不是本次 Raft 项目，只是宽泛关键词搜索中的高热度干扰项。

## 3. 固定审查快照

### 3.1 文档仓库

- URL：`https://github.com/botiverse/raft-docs`
- commit：`19bce24c6aed7b5dbe1ccc4a71d6cd4e42801c15`
- 最新提交：`docs(developers): describe agent inbound events (#37)`
- package version：`0.1.0`
- 本地快照：`runs/raft-public-reference-review-20260721/raft-docs`

### 3.2 外部 Agent 仓库

- URL：`https://github.com/botiverse/raft-external-agents`
- commit：`72c31894f933b9aa9243195d038d66ee79589593`
- 最新提交：`feat(raft-channel): session orientation context + per-field truncation flags (0.3.1) (#18)`
- root package version：`0.1.0`
- channel plugin version：`0.3.1`
- 本地快照：`runs/raft-public-reference-review-20260721/raft-external-agents`

两个仓库均没有 tag，也没有 GitHub release；没有 `1.4` 的公开版本证据。

两个仓库均未声明许可证。默认不得把公开可读等同于开源授权。本次只提炼关系和控制模式，不复制代码。

## 4. 公开协作模型

### 4.1 共享协作平面

Raft 的公开文档不是把 Agent 描述成后台不可见 worker，而是把人和 Agent 放入同一组可见对象：

- server：成员与权限边界；
- channel：领域上下文与粗路由边界；
- message：对话与原始意图；
- task：在 message 上增加追踪元数据；
- thread：进度、讨论和结果；
- board：按状态投影团队当前工作；
- workspace：每个 Agent 的本地执行环境；
- runtime：Claude Code、Codex 等思考和执行引擎。

这解决了传统 subagent orchestration 的可见性问题：人类可以直接看到谁在做、做到哪、等待谁 review。

### 4.2 Task 是带元数据的 Message

公开文档定义：task 是增加了 number、status、owner 的 message。

状态：

```text
todo -> in_progress -> in_review -> done
                     \-> closed
```

关键边界：

- 一项任务只有一个 owner；
- claim 后其他成员应跳过；
- unclaim 后重新开放；
- Agent 完成后进入 `in_review`；
- human approval 后才进入 `done`；
- thread 保存执行细节，主 channel 保持简洁。

这是可迁移价值最高的设计之一：不创建与对话断开的任务对象，同时把“承诺”从聊天文本中显式投影出来。

### 4.3 分工与路由的实际证据

公开文档支持三层机制：

1. 频道 eligibility
   - Agent 关注自己所在的 channel；
   - 不同 lane 使用不同 channel；
   - 房间自然形成粗粒度任务路由。

2. 角色塑形
   - description 说明关注领域；
   - 长期上下文、历史决定和人类 correction 形成 specialization；
   - 文档强调 lane，而不是僵硬 job title。

3. claim 协调
   - Agent 收到需要行动的消息时先 claim；
   - claim 失败则停止或选择其他工作；
   - 用单 owner 防止重复执行。

公开文档还建议 Agent 提议大任务拆分，但在实际 fan-out 前由人审查拆分。

这些足以支持“上下文路由 + 抢占协调 + 分解建议”，但不足以支持“智能分配算法”。没有公开证据展示：

- capability vector；
- workload/cost/latency score；
- learned routing policy；
- route confidence；
- assignment decision record；
- 对比基准或路由准确率；
- allocator 核心代码和并发测试。

因此“智能分配”必须标记为未经公开源码证实。

## 5. 权限和人工门禁

公开文档区分 Agent 的 Member 与 Admin：

- Member 可参与对话和任务；
- Member 遇到高权限动作时可以准备 action card，交给人提交；
- Admin 可管理部分 server 结构；
- Agent 永远不能成为 owner。

可迁移关系是：

```text
能力 != 权限
能提出方案 != 能执行副作用
Action Card != 执行收据
```

这与 Hermes 的 AuthorityGrant、proposal/receipt 分离、外发和高风险边界一致。

## 6. 外部 Runtime Bridge 代码审查

公开源码最有价值的部分是 Claude Code `raft-channel` 插件。

### 6.1 边界分工

Bridge 负责：

- wake-hint 消费；
- sequence dedup；
- stale prune；
- reconnect/backoff；
- at-least-once-until-consumed reconciliation；
- proof ledger 和日志。

Runtime plugin 只负责：

- 监听 loopback HTTP endpoint；
- 将固定、短小的 wake notice 注入 Agent 可见上下文。

插件不持有 Raft/Slock credential，不接收 message body，不修改 delivery/read/model_seen cursor。Agent 被唤醒后通过 CLI 主动 pull 消息。

### 6.2 Content-free wake

`raft-channel-wake.v1` 只携带 metadata：

- attemptId
- eventId
- messageId
- agentId
- profile
- coreSessionId
- adapterInstance
- occurredAt

不携带 message body、sender、channel name 或 preview。

这把“唤醒信号”和“业务内容”分开：通知层不能把外部消息直接注入 system-like context；真实内容由具备身份和权限的 CLI 读取。

### 6.3 成功语义

协议明确区分：

- HTTP 已收到；
- wake 已进入可见上下文；
- Agent 已处理消息；
- cursor 已推进。

只有 wake 已进入或排队进入 Agent 可见上下文才能返回成功。成功不能被误写成“Agent 已消费”。这是可迁移的证据层级设计。

### 6.4 Wake 与 Telemetry 的可靠性分层

Wake：

- behavioral signal；
- at-least-once-until-consumed；
- 失败后保留 hint；
- 依靠 dedup 和 reconciliation。

Activity：

- observational telemetry；
- at-most-once；
- bounded queue；
- overflow 丢最旧事件；
- drain 后转发失败允许丢失；
- dropped 数量显式可见；
- 不阻塞 tool execution。

这避免 telemetry 与真正控制信号竞争可靠性预算。

### 6.5 Runtime supervision

插件实现并测试了：

- loopback + per-session random token；
- profile 显式来源；
- 新旧 profile env 冲突时 fail closed；
- spawn/attach 两种运行方式；
- starting/running/exited/restarting/stopped 状态；
- fast-exit exponential backoff；
- 稳定运行后重置 backoff；
- SIGTERM 后 bounded SIGKILL；
- discovery file mode `0600`；
- bounded activity queue 与 dropped counter；
- closed allowlist schema；
- 字段级 4096 字符截断标记。

### 6.6 公开实现局限

- `readBody` 没有显式 byte limit；虽然字段后续有长度检查，但 HTTP body 在解析前会完整进入内存。
- token 比较使用普通字符串相等，不是 constant-time；loopback threat model 下风险有限，但高威胁环境应加强。
- activity queue 是内存、at-most-once，进程退出即丢失；这是已声明的设计取舍。
- runtime plugin 只能证明 wake 注入适配器逻辑，不证明真实 Claude Code 端到端可见性；协议自己也要求 fresh-environment E2E。
- 核心 bridge、cursor、dedup、proof ledger 和 server allocator 不在公开仓库中，无法独立审计。

## 7. 实际验证结果

### 7.1 `raft-external-agents`

执行：

```text
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm test
corepack pnpm build
```

结果：

- install：成功；提示 esbuild build script 被 pnpm 默认忽略；
- typecheck：成功；
- tests：32 tests，32 pass，0 fail；
- build：成功，生成 self-contained `index.js` 和 `activity-hook.js`。

测试中的 `MODULE_NOT_FOUND .../agent` 输出是 supervisor restart 场景故意制造的短命 child，不是测试失败；对应测试验证两次 backoff restart 后通过。

### 7.2 `raft-docs`

执行：

```text
corepack pnpm install --frozen-lockfile
corepack pnpm build
corepack pnpm check:agent-artifacts
```

结果：

- install：成功；提示 esbuild build script 被忽略；
- VitePress build：成功；
- client/server bundle：成功；
- pages render：成功；
- sitemap：成功；
- agent artifact freshness：成功。

这些验证不能覆盖私有核心服务。

## 8. 宣传声明核实表

| 声明 | 结论 | 证据边界 |
|---|---|---|
| Raft 是多 Agent 协作框架/产品 | 基本支持 | 公开 docs + external runtime plugin |
| AI 像真实团队一样分工 | 部分支持 | 文档有 channel、task、claim、subtask、review；属于行为说明 |
| 最新 1.4 | 不支持 | 公开版本为 0.1.0/0.1.0/0.3.1，无 tag/release 1.4 |
| 支持任务路由 | 部分支持 | 频道 eligibility + role/context + claim；无公开通用 router 代码 |
| 支持智能分配 | 未证实 | 无 allocator/score/policy/decision evidence |
| GitHub 搜索 `raft-multiagent` 可体验 | 表述不准确 | 精确 repo 搜索为 0；可找到 Botiverse 公开 docs/plugin，但核心不可见 |
| 23 万+关注 | 未证实 | GitHub 组织 97 followers，公开仓库 7/3 stars；可能指未提供来源的社交播放/曝光 |
| 17 小时引爆开发者圈 | 未证实 | 缺少原始社交链接、起止时间和平台指标 |

## 9. 对 Hermes 的新增价值

Hermes 已有 taskpool、AuthorityGrant、proof/readback 和 runtime supervision。Raft 公开材料带来的增量主要是：

1. conversation/task 同源模型：任务是消息的状态投影，不是另建孤立对象；
2. channel eligibility 先于复杂评分路由；
3. role shaping 由 lane、上下文和 correction 渐进形成，而非一次性 job title；
4. subtask decomposition 和 execution authority 分离；
5. `in_review` 是真正生命周期状态；
6. Agent 与人共享同一可见协作面；
7. metadata-only wake + authoritative pull；
8. behavioral wake 与 observational telemetry 使用不同可靠性合同。

不应吸收：

- 未证实的“智能分配”营销标签；
- 产品品牌、CLI 命令和未授权源码；
- 把频道 membership 当成足够精确的全局路由；
- 在没有 lease/stale reconciliation 证据时声称 claim 能处理崩溃恢复；
- 把 HTTP accept、wake injected、model processed、task completed 合并成一个 success。

## 10. 最终判断

Raft 值得学习，但真正成熟的价值不在“多 Agent 自动分工”口号，而在把团队协作分解为几个可验证原语：共享上下文面、消息派生任务、单 owner claim、显式 review 状态、角色与权限分离、内容无关 wake、Agent 主动 pull、信号语义对应的可靠性等级。

公开证据不足以证明中心化智能分配算法，也不足以审查其核心 server、router、claim 原子性、lease、reconciliation 和权限实现。后续若获得公开核心仓库、版本 1.4 release notes 或原始社交传播链接，应重新固定快照并增量审查，而不是用当前文档反向补齐宣传结论。
