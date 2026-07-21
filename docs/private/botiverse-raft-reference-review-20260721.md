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

## 10. 第二轮公开面扩展

### 10.1 Botiverse 组织仓库拓扑

第二轮使用 GitHub Organization API 重新枚举公开仓库。调用时必须显式使用 GET；`gh api ... -f per_page=100` 未指定 `-X GET` 会被解释为创建仓库的 POST，返回 403。这是 API 调用方式错误，不是组织拒绝公开读取。

与 Raft 产品直接相关的新增公开面：

- `botiverse/create-raft-app`：Raft-native 应用脚手架；
- `botiverse/raft-survey-sample`：Login with Raft 的 Cloudflare Worker 示例；
- `botiverse/agent-screen-recorder`：Raft Agent 的 CLI-first 录屏工具；
- `botiverse/kimi-code-sdk`：供 Botiverse/Raft 消费的上游镜像；
- `botiverse/multica`：`multica-ai/multica` 的 fork，不是 Raft 核心仓库。

`botiverse/multica` 的出现不能证明 Raft 是 Multica 重命名或基于 Multica 实现。它在组织中是公开 fork，品牌、域名、代码历史和版本仍然不同，因此继续作为相似架构参考而非身份链证据。

### 10.2 可访问产品运行面

对 `https://app.raft.build/` 进行了未登录只读访问：

- 页面可达；
- 只公开 Sign In、Forgot password、Create account、Terms、Privacy 等入口；
- 未进入认证流程；
- 没有账号内 task claim、agent routing、status、event delivery 的运行时读回证据。

因此这里只有“公开登录页当前可达”的网络读回证据，不属于 L4。L4 专指认证后的产品行为读回；核心协作声明仍没有 L4 行为验证。

## 11. Agent App 与外部事件模型

### 11.1 新固定快照

`botiverse/create-raft-app`：

- commit：`21a01daeeffed2a7136e0b30275543c039f007d1`
- package version：`0.2.0`
- package metadata：MIT
- GitHub repository license metadata：NONE
- 本地快照：`runs/raft-public-reference-review-20260721/create-raft-app`

`botiverse/raft-survey-sample`：

- commit：`3f4b6f6c87efdc623dc989bd268a94a42d2c6bb7`
- package version：`0.1.0`
- private package：true
- repository license：未声明
- 本地快照：`runs/raft-public-reference-review-20260721/raft-survey-sample`

`create-raft-app` package 声明 MIT，但仓库没有独立 `LICENSE` 文件。该声明可作为 npm 包元数据事实，不能自动扩张为所有组织资料均为 MIT。

### 11.2 Manifest 的正确定位

`create-raft-app` 为每种模板提供 `raft-template.json`，其中明确区分：

- `capabilities`；
- `negativeCapabilities`；
- `authoritySources`；
- `appType`；
- `conversationRole`。

Conformance validator 直接拒绝把 `appType` 或 `conversationRole` 放入 authority source。当前允许的 authority source 是：

```text
registration
grant
scope
review
runtime-permission
```

这证明其设计层明确遵守：

```text
Manifest = capability/discovery projection
Manifest != authorization
Role != authority
App type != authority
```

这比普通 tool manifest 多了一项重要能力：把“明确不能做什么”纳入机器校验。

### 11.3 第三方 Agent Inbound Event

Raft 文档描述的 Agent inbound event 是信息通道，不是 command channel。合同要素：

- App 预先声明非默认 scope；
- access request 选择一个具体 agent；
- token 绑定具体 server 的 `agent-inbound` resource；
- kind 只允许 `event` 或 `notification`；
- `action_request` 保留并拒绝；
- payload 最大 32 KiB；
- summary 最大 500 字符；
- `externalEventId` 在 app + target agent 内唯一；
- TTL 默认 24 小时，最大 7 天；
- 接受时返回 event id、queued/deduped、expiresAt 和 payload hash；
- `@mention`、Raft ref、Agent markup 等控制形文本被中和为数据；
- App 不能读取消息、冒充人/Agent 发言、改目标、从 payload 文本获得操作权限。

可迁移的完整安全关系是：

```text
scope
+ exact target
+ resource audience
+ idempotency
+ TTL
+ payload hash
+ provenance
+ inert rendering
!= action authority
```

其中任一控制都不能替代其他控制。

### 11.4 Product-semantic Action

Agent manifest 的 action 应表示可审查的产品动作，例如 `summarize-note`，而不是暴露全部内部 HTTP route。调用链应为：

```text
manifest discovery
→ app installed/available
→ grant/scope/runtime permission
→ parameter validation
→ service-local authorization recheck
→ operation
→ structured result/error
→ domain readback
```

这使安装审查、权限审查、审计日志和版本兼容都围绕稳定业务语义，而不是底层接口形状。

### 11.5 Agent 本地凭据隔离

Local CLI wrapper 会为每个 Agent 重写：

- `HOME`；
- `XDG_CONFIG_HOME`；
- `XDG_DATA_HOME`；
- Agent token file；
- Agent/App identity env。

并用 argv 启动 child，透传 stdio 和 exit code。

这是“防止误用宿主用户全局登录”的凭据边界，但不是 OS sandbox：

- child 仍继承大量环境变量；
- 没有网络隔离；
- 没有文件系统 namespace；
- 没有证明 child 无法读取其他路径；
- Windows 分支使用 `shell: true`，需要额外参数边界审计。

因此吸收时应命名为 `per_agent_credential_state_isolation`，不能命名为通用 sandbox。

## 12. 第二轮验证

### 12.1 `create-raft-app`

执行：

```text
npm ci
npm test
npm pack --dry-run
```

结果：

- 14 tests / 14 pass / 0 fail；
- 六种模板均完成 scaffold-and-build；
- conformance passed；
- npm pack dry-run 成功；
- 打包 66 files，unpacked size 114.4 kB。

模板覆盖：

- Hono + React + Cloudflare Worker；
- pure human sign-in；
- local CLI wrapper；
- hosted HTTP action；
- OAuth HTTP action；
- dual human/agent app。

这些测试证明脚手架和 conformance，不证明实际 Raft OAuth server 或 Agent action runtime。

### 12.2 `raft-survey-sample`

执行：

```text
npm ci
npm run typecheck
npm test
```

结果：

- TypeScript typecheck：通过；
- 6 test files：全部通过；
- 282 tests / 282 pass / 0 fail。

它证明公开 OAuth consumer sample 的本地逻辑，不证明生产 OAuth endpoint、token revocation 或 server membership 行为。

### 12.3 机器可读能力图

创建：

```text
docs/private/botiverse-raft-capability-graph-20260721.json.md
```

图包含：

- 11 capability nodes；
- 10 edges；
- 12 Agent wrappers；
- 22 gates；
- L0–L5 claim evidence ladder；
- unsupported claims；
- private-core `cannot_prove` 边界。

实际 JSON 解析和引用完整性校验结果：

```text
valid: true
node_count: 11
edge_count: 10
wrapper_count: 12
gate_count: 22
errors: []
```

## 13. 第二轮新增吸收结论

在第一轮共享协作面、message→task、claim、review、wake/pull 之外，第二轮确认了以下新增类级模式：

1. Manifest 只做 capability discovery，不能携带 authority。
2. `negativeCapabilities` 与正向能力一起进入 conformance。
3. 第三方 event 必须结构性保持“事实而非命令”。
4. Scope、target、resource、idempotency、TTL、hash、provenance 和 inert rendering 构成联合入口合同。
5. `202 queued`、delivered、consumed、acted 必须是不同证据层级。
6. Action 使用产品语义，并在服务端重新授权。
7. 每 Agent HOME/XDG 隔离只是一种 credential-state boundary，不是 sandbox。
8. Agent identity、runtime session、workspace 和 process state 必须分别建模。
9. Restart、session reset、full reset、stop、delete 必须明确各自清理范围。
10. 外部仓库中某一 adapter 达到 L3，不能升级私有核心 allocator/claim 到 L3。

## 14. 最终判断

Raft 值得学习，但真正成熟的价值不在“多 Agent 自动分工”口号，而在把团队协作分解为几个可验证原语：共享上下文面、消息派生任务、单 owner claim、显式 review 状态、角色与权限分离、内容无关 wake、Agent 主动 pull、信号语义对应的可靠性等级。

公开证据不足以证明中心化智能分配算法，也不足以审查其核心 server、router、claim 原子性、lease、reconciliation 和权限实现。后续若获得公开核心仓库、版本 1.4 release notes 或原始社交传播链接，应重新固定快照并增量审查，而不是用当前文档反向补齐宣传结论。

## 15. 第三轮：未登录部署面与协议入口

### 15.1 当前公开部署读回

2026-07-21 对未登录公开面执行了只读读回，没有创建账号、提交表单、触发 OAuth code 或使用凭据。

`app.raft.build` 当前加载：

```text
/assets/index-BPDGTSBL.js
sha256 252be6b7379906df812e630f71ca30fe1ab6535acaa3026ea0a8861bea39aa41
size   2,378,297 bytes
```

该 bundle 没有暴露 source-map trailer。它公开引用了 `api.raft.build/api/auth/providers`，当前返回 Google、GitHub 两个 enabled provider；这只证明未登录 provider discovery，不证明任一登录流程成功。

本轮公开部署证据已永久保存至：

```text
runs/raft-public-reference-review-20260721/live-public-20260721/
```

目录中的 `manifest.json` 记录原始 URL、SHA-256、认证状态和每项证据边界。

OAuth discovery 的实际公开路径不是站点根部标准猜测路径，而是：

```text
GET https://api.raft.build/api/oauth/.well-known/openid-configuration
sha256 8934add84e70c859bbef4092713d656d76eeb15abf5d8556e7fa9827787e55f3
```

当前广告：

```text
issuer: https://api.raft.build
token_endpoint: /api/oauth/token
userinfo_endpoint: /api/oauth/userinfo
serverinfo_endpoint: /api/oauth/serverinfo
grant_types: authorization_code, urn:slock:grant-type:agent_request
scopes: openid, profile, identity, agent:event:write, agent:notification:write
token auth: client_secret_basic, client_secret_post
```

负向读回：

- `/api/oauth/userinfo` 无 Bearer 返回结构化 401；
- `/api/oauth/serverinfo` 无 Bearer 返回结构化 401；
- `api.raft.build/.well-known/openid-configuration` 返回 404；
- `app.raft.build/.well-known/openid-configuration` 返回 SPA HTML 200，而不是 OAuth metadata。

因此 discovery consumer 必须使用被文档/配置明确声明的 endpoint，不能把“HTTP 200 + HTML fallback”误判为协议发现成功。

### 15.2 部署 bundle 的证据边界

公开 bundle 可用于发现部署构成、兼容别名和候选协议字符串，但不是 canonical source。当前可见字符串包括：

```text
raft-agent-activity-ingest.v1
slock-external-runtime-integration.v1
slock-external-agent-wake-event.v1
slock.state.transition
slock.state.violation
/login-with-raft/setup
/login-with-slock/setup
```

这证明生产 bundle 仍携带 Slock→Raft 兼容层，但不能仅凭 minified 字符串推断服务端路由已启用、schema 行为完整或权限正确。

`robots.txt` 仍写着 `app.slock.ai`、`slock.ai`，sha256 为 `f3dc0cf362b9885623ccd7067624a15e7ca80289370c0d4cb68b750e55af412f`。这是品牌迁移残留证据，不是域名所有权、产品版本或安全漏洞证据。

## 16. 第三轮：公开历史与能力演化

将四个永久快照的 origin 修正到 GitHub 并抓取全部公开 refs 后，固定 HEAD 未改变；可见 commit 数为：

```text
raft-docs             80
raft-external-agents  30
create-raft-app       27
raft-survey-sample     1
```

关键演化链：

1. 2026-06-09：external-agent marketplace 以 Slock 品牌出现；
2. 2026-06-12：plugin 正式改名 `raft-channel`，保留历史 wire aliases；
3. 2026-06-23：文档删除“@mention 会唤醒 idle agent”的错误描述；
4. 2026-06-25：非成员 mention 行为修正为 notify-or-add，而非自动送达；
5. 2026-07-07：Hono 模板从宽松 auth stub 改为未实现时 501 fail-closed；
6. 2026-07-11：增加 token-bound `serverinfo` 投影；
7. 2026-07-13：Hono 模板实现 userinfo token verification；
8. 2026-07-19：公开文档加入 bounded Agent inbound event。

结论：

- Raft 与 Slock 的重命名/兼容链有源码和部署 artifact 双重支持；
- 这与 `multica` fork 没有身份链关系；
- 历史中多次纠正“delivery、mention、wake、session”的混淆，说明这些边界不是措辞细节，而是必须进入可执行测试的协议语义；
- 公开 release 列表和 tags 仍为空，不能从 commit 时间线推导“版本 1.4”。

## 17. 第三轮：跨平面 principal 合同

仅验证 token 可被 issuer 的 userinfo 接受仍不够。Agent App 的 canonical principal 至少应绑定：

```text
issuer/provider
+ client_id or audience
+ server_id/resource
+ stable sub
+ strict principal type
+ granted scopes
```

显示名、handle、server slug、avatar 等属于 mutable presentation，不应进入数据库唯一键或审计 actor 主键。

正确链路：

```text
token accepted by issuer
→ expected client/audience matches
→ expected server/resource matches
→ stable subject present
→ type is exactly human|agent
→ required scopes present
→ app-local policy
→ operation
→ receipt/readback
```

App ownership、App availability、installation、publication 和 per-operation authority 也必须分离：

```text
owner can maintain app metadata/secret
!= app published
!= app installed on another server
!= caller authorized for an operation
```

## 18. 第三轮负向审查：scaffold conformance 的覆盖缺口

当前 `create-raft-app` Hono 模板已比早期 permissive stub 更安全：无 token 返回 401，userinfo 失败返回 401，callback 交换失败返回 501/502，cookie 使用 HttpOnly + Secure + SameSite=Lax。

但对当前 `resolvePrincipal` 的静态读回显示：

```text
userinfo_fetch:                    true
parses_sub:                        true
parses_server_id:                  true
parses_client_id:                  false
compares_client_id_to_config:      false
requires_server_id:                false
stable_actor_uses_sub_server_id:   false
unknown_type_defaults_human:       true
fallback_server_literal:           true
```

具体风险面：

1. userinfo 返回的 `client_id` 没有被解析或与 `RAFT_CLIENT_ID` 比较；
2. `server_id` 不是必需字段，缺失时允许退化；
3. audit actor 使用 mutable handle + server slug，而不是文档要求的 `(provider, sub, server_id)`；
4. 未知或缺失 `type` 被默认归为 human，而不是 fail closed；
5. scopes 没有进入 principal 或 route-level authorization；
6. pending-login cookie 只区分 browser/agent callback，没有与 callback code 建立可验证关联；在协议不回传标准 `state` 的前提下，需要单独审查 login-CSRF/session-swap 防线。

合并 PR `botiverse/create-raft-app#18` 的公开说明明确写为 `resolvePrincipal verifies any Raft access token via /api/oauth/userinfo`。该 PR 没有 issue comments 或 reviews；当前公开 issue 标题中也没有命中 auth/OAuth/token/scope/client/identity/CSRF/state 的独立跟踪项。这强化了“scaffold 目前只验证 issuer acceptance”的源码判断，但仍不证明生产 userinfo 是否在服务端实施额外 audience/resource 约束。

重新执行 `npm test`：

```text
14 tests
14 pass
0 fail
conformance passed
```

因此现有测试证明 scaffold、build 和字符串级合同，没有证明：

- cross-client token 被拒绝；
- stable canonical identity 被保留；
- principal type 严格校验；
- scope/resource audience 被强制；
- callback 与发起会话绑定。

这是一项公开 scaffold review gap，不是已证实的生产漏洞。生产 userinfo 可能在服务端强制 token audience；没有两个真实 client/token 的认证运行时证据，不能升级为 exploit claim。

## 19. 第三轮新增吸收结论

第三轮相对 Hermes 的真实增量：

1. 把 identity tuple 扩展为 issuer/client/resource/sub/type/scopes，而不只 resource-bound subject；
2. 把 mutable presentation 与 canonical/audit identity 分离；
3. conformance 必须覆盖跨 client token、缺失 server、未知 type、scope mismatch 等负向语义，而不只检查代码中出现了 userinfo；
4. OAuth discovery endpoint 必须验证 status、content-type 和 schema，不能接受 SPA fallback HTML；
5. 品牌/协议迁移需要 canonical name、legacy alias、deprecation、telemetry、removal gate 五件套；
6. 文档纠错应转化为测试：mention≠delivery、delivery≠wake、restart≠reset；
7. public deployed artifact 是独立证据通道，但不能覆盖 private core 或认证行为。

下一证据边界仍是认证后的多 client、多 server 运行时：只有它能验证 token audience、安装边界、Agent Login、event delivery 和跨 server 负向行为。

## 20. 第四轮：本地可执行 auth-contract 负向证据

为避免把静态代码审查升级成未经执行的安全结论，本轮从固定 commit `21a01daeeffed2a7136e0b30275543c039f007d1` 重新生成 Hono subject app，并建立无真实凭据、无 Raft 网络调用的 mock-userinfo harness：

```text
runs/raft-public-reference-review-20260721/p4-auth-conformance-harness/
```

Spec 边界：

- 目标：把 scaffold 的身份绑定、资源绑定、稳定审计身份、scope 和 callback 语义变成可执行负向用例；
- 非目标：不创建 Raft app/account，不使用 token/secret，不请求认证端点，不改上游源码，不发布 issue；
- 证据合同：同一 fixture 同时运行 normative RED 和 descriptive GREEN；
- `evidence.json` sha256：`0ce0e8381debce1dcf2fe40d159b7cd6d5dbd4b5111d0eb11537e83762ac6491`。

### 20.1 Normative RED

命令：

```text
node --test auth-contract.expected.test.mjs
```

结果：

```text
8 tests
1 pass   # 完整 principal 正向控制
7 fail   # 预期的 fail-closed 合同尚未满足
exit 1
```

七个 RED 语义是：

1. `client_id != RAFT_CLIENT_ID` 仍返回 200；
2. 缺失 `server_id` 仍返回 200；
3. 未知 `type=service` 仍返回 200 并被降级为 human；
4. 返回 scope 缺失 `profile` 仍返回 200；
5. 不同 `server_id`、相同 slug/handle 折叠到同一个 audit actor；
6. 相同 `(sub, server_id)` 改变 handle 后 audit actor 随之改变；
7. login-init cookie 仅证明“曾发起过登录”，与 synthetic foreign transaction code 没有关联，callback 仍 302 到 `/`。

RED 退出码 1 是规范断言命中覆盖缺口，不是 harness 崩溃；正向控制通过，排除了所有请求都失败造成的假阳性。

### 20.2 Descriptive GREEN

`node probe.mjs` 以当前真实 scaffold 行为为断言，退出 0，并生成 `observed.json`：

```text
complete_principal_status:        200
cross_client_status:              200
missing_server_id_status:         200
unknown_type_status:              200
scope_mismatch_status:            200
cross_resource_actor_collision:   true
actor_changed_with_mutable_handle:true
callback_status:                  302
callback_location:                /
network:                          mock-only
```

双视图的意义：

```text
normative RED = 所需安全合同尚未满足
observational GREEN = 当前行为被稳定复现
```

不能把 RED 当作测试设施失败，也不能把 GREEN 当作当前行为安全。

### 20.3 回归和构建控制

```text
生成 subject app: npm run build -> exit 0
worker TypeScript: tsc --noEmit -> exit 0
上游 create-raft-app: 14/14 pass
上游 conformance: passed
固定上游 worktree: clean
```

因此差异不是生成失败、依赖失败或模板无法构建，而是现有 conformance 没有编码上述负向合同。

### 20.4 结论边界

本轮把证据从“L2 静态 scaffold 读回”提升为“L3 本地可执行 mock conformance gap”。它仍然不能证明：

- 生产 userinfo 未实施 client/audience 检查；
- 真实 authorization code 可被跨浏览器/session swap；
- 任一生产 Raft app 可被实际跨 client 或跨 server 利用。

下一有效跃迁只能来自 L4 认证运行时矩阵，或上游将这些负向用例加入真实 conformance。继续扩展同一 mock 不能替代这两个证据面。

## 21. 第五轮：隔离 remediation 原型与协议剩余边界

本轮没有修改固定上游快照，而是复制生成 subject app 到隔离目录，实现并验证 app 本地可执行的 fail-closed 合同：

```text
runs/raft-public-reference-review-20260721/p4-auth-conformance-harness/hardened-subject-app/
```

证据包：

```text
p5-evidence.json
sha256: 0f16cf1cd5920c97e31337c0d7b33e1cc28470e07b43fd9f4759fe7ce35551c4
```

### 21.1 App 可本地关闭的合同

原型将 `resolvePrincipal` 收敛为：

```text
expected RAFT_CLIENT_ID configured
+ userinfo.client_id exact match
+ sub present
+ server_id present
+ type in {human, agent}
+ openid/profile scopes present
+ audit actor = raft:${sub}@${server_id}
```

这使 canonical/audit identity 不再依赖可变的 `preferred_username`、`name` 或 `server_slug`。本地 semantic harness 结果：

```text
8 tests
8 pass
0 fail
exit 0
```

完整生成 app build 和 worker TypeScript 校验均通过。

### 21.2 Callback transaction binding 仍为协议边界

独立 normative 测试仍保持 RED：

```text
1 test
0 pass
1 fail
actual callback status: 302
required status:        400
```

公开 setup/callback 协议只返回 `code`，且 `return_to` 需要精确注册；仅有 pending-login cookie 不能证明 callback code 与本地 login-init transaction 相关。未在 app 侧伪造未经服务端支持的 state、nonce 或 PKCE。

关闭此项至少需要服务端支持的 transaction correlation（state、nonce、PKCE 或等价机制），再以 attacker/victim browser-session 矩阵验证。当前 RED 不能提升为生产 session-swap 漏洞。

### 21.3 上游审查 patch

生成了只覆盖两个上游文件的本地 patch：

```text
runs/raft-public-reference-review-20260721/p4-auth-conformance-harness/upstream-review.patch
sha256: 68fd9feb64a5a55777f18977d2849488f88d7f41e08f6d08d5b7f93a2cf35a3b
```

控制结果：

```text
git apply --check: pass
proposal npm test: 14/14 pass
proposal conformance: pass
```

patch 内测试是生成模板的静态 regression guard；8/8 semantic proof 仍位于外部隔离 harness。因此该 patch 是 reviewable prototype，不是未经补齐语义测试即可发布的 PR-ready 交付物。

### 21.4 结论边界

本轮证明：固定公开 scaffold 的六类 app-local principal 合同可以在不访问 Raft、不使用凭据的情况下被 fail-closed，并保持现有生成/build/conformance 回归通过。

本轮仍不能证明：

- 更严格 client binding 与生产 token/userinfo 发行语义完全兼容；
- 生产 callback 可被利用；
- 上游会接受该 patch；
- 认证后的跨 client、跨 resource 行为已经关闭。

没有修改上游、push、创建 issue/PR、使用凭据或产生产品侧副作用。

## 22. 第六轮：模板内生产候选与默认关闭的浏览器边界

本轮以固定基线 `21a01daeeffed2a7136e0b30275543c039f007d1` 建立隔离候选，并把外部 P5 harness 的身份合同移入生成模板自身。最终 staged tree：

```text
1fe11dba7e7d14708e430ab8ea2e875f4051700f
binary staged diff sha256: de820544706d832c658c9ff74d9fd58473639d4dff6153e1142bb11002b0acbb
```

### 22.1 模板内可执行合同

生成的 Hono Worker 现在要求：

```text
userinfo.client_id == RAFT_CLIENT_ID
userinfo.server_id in RAFT_ALLOWED_SERVER_IDS
userinfo.type in {human, agent}
userinfo.scope contains openid and profile
sub and server_id are non-empty
canonical actor = raft:<percent-encoded sub>@<percent-encoded server_id>
```

percent encoding 防止 delimiter collision；显示名、handle、server slug 和 avatar 不进入稳定 actor。

认证与动作授权分层：`/api/auth/me` 只验证身份合同；`POST /api/events` 还要求已配置的 `RAFT_EVENT_WRITE_SCOPE`，无策略或无 capability 均返回 `403`。显式浏览器兼容登录发起时，authorize request 同时请求 identity scopes 与已配置 route capability scope。

### 22.2 OAuth/callback 安全边界

默认配置 `RAFT_ALLOW_UNBOUND_BROWSER_LOGIN=false`：

```text
/api/auth/login -> 503
不创建 pending cookie
不发起 authorize request
human callback without initiated compatibility flow -> 400
```

仅显式兼容模式可建立浏览器 session。兼容 cookie 为 `HttpOnly; Secure; SameSite=Lax`，且本地将 provider TTL 上限收敛为 3600 秒。token exchange 的网络错误、非 JSON、空/非字符串 access token 和非法 TTL 均 fail closed 为 `502`；direct agent callback 只返回 JSON，不创建浏览器 session。

该兼容模式不是 transaction-binding 修复。公开协议没有可验证的 `state`、nonce、PKCE 或等价 correlation，因此 human browser Login with Raft 仍不得作为安全生产能力启用。

### 22.3 可执行证据

模板语义合同：

```text
25 tests
25 pass
0 fail
```

新增 RED→GREEN 证据包括：authorize scope propagation、delimiter-collision actor、malformed/network token exchange、browser TTL cap、OpenAPI stale-501 removal，以及 public API reference 仍把已实现 `/api/auth/me` 描述为 501 stub 的文档漂移。最后一项先取得 24/25 RED，再修正文档和生成器回归到 25/25 GREEN。

固定 staged tree 的 clean archive 重建得到相同 tree hash，并执行：

```text
generator tests: 14/14 pass
conformance: pass
all six templates generated/installed/built
Hono generated subject semantic contract: pass
generated admin production build: pass
generated worker tsc --noEmit: pass
npm pack --dry-run: create-raft-app@0.2.0, 67 files
generated package-lock: worker tsx and @types/node present
production/full npm audit: 0 vulnerabilities
git diff --check: pass
```

核心日志：

```text
staged-tree-v2-test.log sha256: 10457141f1780ac503e5e3d83140846450f14d9c16903a6147f4391d9c040c1a
staged-tree-v2-pack.json sha256: 3337cdc0cb43ce26ed589ed89bb6bf85833270c5fb231c6c93cbca936b224c0c
frozen-subject-v2-test.log sha256: 9b7af2ced696f939c2de5dc5d1a8fb55ffde8c9a7025e92f5c2854a3c8040746
frozen-subject-v2-build.log sha256: 3280f781660d67b30c7184f4bf75cc9e7a52b22894253a43ccc14f077660e3cd
public-doc-red.tap sha256: 10ff69fd463d80e35c0053db80a5481337b6c8c3e7fef5cfe7016e0a72130ca6
production audit sha256: c09913e09500ef57a857d63c8c7c4b92fcdfdd3dca19b77daa84042bd4da86be
```

### 22.4 Immutable candidate 与独立证据认证

最终候选已创建本地提交：

```text
commit: e510afc2b37b565a8767179a596382c686b2d0d2
parent: 21a01daeeffed2a7136e0b30275543c039f007d1
tree:   1fe11dba7e7d14708e430ab8ea2e875f4051700f
```

提交后 worktree clean，且 `commit^{tree}` 精确匹配冻结 tree。未 push。

独立认证使用显式拆分的 14 项 exact-tree/L3 证据合同。GPT-5.5、MiMo V2.5 Pro、DeepSeek V4 Pro 三个独立参与者均返回 no-action approval；truth gate 为 grounded、evidence coverage 为 1.0、14/14 claims verified、P0/P1 为 0。最终 manifest：

```text
chain: eb6aefc8-79b2-4cde-88b6-9e445b747d98
status: certified
approvals: 3/3
agreement floor: 0.95
manifest sha256: bcd87d51e2a2b1bc3acb799607dc4b438ca165f66bc64e5b3ca016eeca26e48a
```

该认证是客观 artifacts 支撑的 L3 本地证据认证；模型判断仍为 advisory，不证明真实协议、部署或生产运行时安全。

### 22.5 结论边界

上述是固定 staged tree 的 L3 本地生成、mock-auth、构建、打包和审计证据。它不证明：

- 真实 Raft token 与更严格 client/resource 合同兼容；
- 真实 human/agent OAuth 流程、撤销和 session cleanup；
- 两 client × 两 server 的 cross-client/cross-resource 负向矩阵；
- Cloudflare 部署、回滚、生产流量或上游接受；
- human browser callback transaction binding。

未使用凭据，未部署，未 push，未创建 issue/PR，未修改生产资源。只有认证 L4、协议 binding、部署和回滚读回齐备后，才可评估 `production-ready`。
