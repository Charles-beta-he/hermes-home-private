# Agent / Workflow Builder 最终长期稳定方案

## 0. 一句话定位

不要把这套基座定位成“做一个 Agent”。

最终形态应定位为：

> 一个可把业务意图编译成可运行、可审计、可交付、可演进的 Agent / Workflow Pack 的控制面系统。

它生产三类交付物：

1. **Agent 产品**：对外可卖、可交付的 Bot / Dashboard / SaaS / API / CLI / 私有化 Docker。
2. **企业 Workflow / Automation 产品**：不一定叫 Agent，但能稳定推进业务流程。
3. **自身演进 / 控制面系统**：让基座、模块、流程、证据、评测、经验持续变强。

稳定单元不是 prompt，也不是单个 agent，而是：

```text
Intent → WorkflowSpec → ExecutionDAG → RunLockfile → Taskpool → ModuleRuntime → ModelRouter → Evidence → Acceptance → ReleaseArtifact
```

---

## 1. 目标与硬约束

### 成功标准

长期稳定方案必须满足：

- 能从自然语言/业务需求生成可执行工作流，而不是只生成一次性回答。
- 能交付 Agent 产品、企业自动化流程、自演进控制面三类产物。
- 每次运行有事实源、版本、权限、证据、验收、回滚路径。
- 可对企业交付：可部署、可审计、可复现、可回滚、可定价。
- 可对自身演进：不会把局部经验污染全局，不会让 dashboard/cron/worker 各自变成事实源。

### 红线

- Dashboard / UI 只能是投影与命令入口，不能成为事实源。
- Worker / Agent 只能提交结果和证据，不能直接把任务标记为 done。
- Cron 只能做 watchdog / recovery / report fallback，不能成为主调度真相。
- 运行中的 workflow 不能被热更新随意改变验收标准。
- 模型路由不能无痕动态切换；必须有 route trace、fallback、eval score、privacy/cost gate。
- 自演进不能压过 P0/P1 真实项目交付。
- 不能把 mock-only、advisory pass、文档完成当成交付完成。

---

## 2. 核心架构

### 2.1 三层产品结构

```text
L1 Delivery Surface  交付表面
- Agent Pack Studio
- Delivery Cockpit
- Enterprise Admin
- API / CLI / Bot / Dashboard / Docker

L2 Control Plane  控制面
- Workflow Registry
- Module Registry
- Model Router
- Taskpool Runtime
- Evidence Ledger
- Acceptance Compiler
- Policy / Human Gate
- Run Lockfile

L3 Execution Plane  执行面
- LLM workers
- deterministic scripts
- browser/API/test harness
- external coding agents
- tool adapters
- integration executors
```

关键边界：

- **控制面决定顺序、权限、状态、证据要求。**
- **执行面只做动作并回传事件/证据。**
- **交付表面只展示、配置、审批、发起命令。**

---

## 3. Canonical Fact Source

长期必须只有一个规范事实源：**Control Tower Ledger**。

它拥有：

- workflow spec version
- run id / step id
- task lifecycle
- command/event log
- worker lease / heartbeat
- evidence references
- acceptance state
- policy decision
- human approval
- adapter observation
- projection checkpoint

Taskpool、Kanban、Dashboard、CLI、Gateway、Evidence Spine、Cron Watchdog 都是 ledger 的投影或适配器，不是第二事实源。

---

## 4. 三类交付物如何落地

### 4.1 Agent 产品

示例：HR 初筛、投研日报、PM 助手、客服质检、销售线索、法务初审。

交付形态：

- Bot
- Dashboard
- SaaS
- Docker 私有化
- API
- CLI

Agent 产品的 Pack 必须包含：

- manifest
- workflow spec
- module list
- tool permission matrix
- model policy
- tenant/project profile
- acceptance schema
- golden cases / UAT cases
- evidence schema
- deployment/runbook
- rollback path
- pricing/usage boundary

### 4.2 企业 Workflow / Automation 产品

示例：任务池自动推进、项目验收证据补齐、Lark/Jira/GitHub 工单闭环、多模型代码审查、客户成功跟进、数据监控异常归因。

核心不是人格化助理，而是：

```text
Signal → Intake → Classify → Plan → Dispatch → Execute → Prove → Verify → Close/Retry/Block/AskHuman → Ratchet
```

它的价值来自：

- 稳定业务状态机
- 可审计事件链
- 可恢复执行
- 人工审批边界
- 证据闭环
- 与现有系统融合

### 4.3 自身演进 / 控制面系统

自演进不是“让 agent 自己乱改自己”，而是让系统按治理边界吸收经验：

- 失败模式 → skill / eval / policy / test
- 重复流程 → workflow pack
- 项目事实 → project profile / SSOT
- 用户偏好 → memory
- 临时任务状态 → taskpool / ledger，不进 memory
- 高风险改动 → ADR + human gate

---

## 5. 模块系统

每个能力模块必须声明机器可读 contract：

```yaml
module_id: resume_parser
version: 1.3.0
capability: parse_resume
abstraction_layer: implementation
input_schema:
  - resume_file
  - jd_criteria
output_schema:
  - candidate_profile_json
  - evidence_quotes
side_effects: local-read # pure | local-read | local-write | external-read | external-write | destructive
permissions_required:
  - read_file
model_profile:
  preferred:
    - best.resume_parse.structured
  fallback:
    - cheap_extraction_model
    - deterministic_parser
evidence_required:
  - original_resume_ref
  - quote_match
risk_level: medium
human_gate:
  - low_confidence
  - sensitive_inference
compatibility:
  input: backward-compatible
  output: backward-compatible
  state: migratable
```

模块生命周期：

```text
registered → validated → shadow → canary → active → deprecated → retired
```

---

## 6. Workflow Compiler

自然语言不能直接变成生产逻辑，必须编译成版本化 WorkflowSpec。

编译流程：

```text
自然语言需求
→ Intent Card
→ WorkflowSpec draft
→ semantic diff
→ static checks
→ risk classification
→ dry-run DAG
→ human/policy gate if needed
→ WorkflowSpec version
```

WorkflowSpec 至少包含：

- workflow_id
- objective
- triggers/sources
- stages
- module bindings
- dependency graph
- state machine
- evidence required per step
- acceptance policy
- permissions and side-effect class
- human gate triggers
- model routing policy
- rollback/escape path

---

## 7. Run Lockfile

每次运行必须冻结有效执行信封：

```yaml
run_id: wf_run_123
workflow_spec_version: 1.4.0
modules:
  planner: planner@2.1.0
  verifier: verifier@1.8.4
model_routing_policy: routing@5
acceptance_policy: acceptance@9
project_profile: customer_profile@2.0.0
context_digest: sha256:...
started_at: 2026-06-13T00:00:00Z
route_mode: pinned_run
```

作用：

- 可复现
- 可回滚
- 可审计
- 可解释为什么这次用了这个模型/模块/验收标准
- 防止执行后临时改 done 标准

---

## 8. 模型路由

模型不是写死的，也不是无约束动态切换。

路由输入：

- module type
- task type
- abstraction layer
- risk level
- data sensitivity
- context length
- tool need
- structured output need
- latency/cost budget
- tenant policy
- provider health
- eval score

路由模式：

- `pinned_run`：企业生产/UAT/外部副作用默认。
- `module_dynamic`：长时自演进，在模块边界重新解析。
- `turn_dynamic`：低风险只读聊天/研究。
- `shadow_only`：新模型旁路评估，不影响结果。

每次路由必须留下：

- selected model
- fallback chain
- reason codes
- privacy/cost checks
- eval score reference
- provider health
- route mode

---

## 9. 验收系统

验收标准由 Acceptance Compiler 在执行前冻结。

按抽象层级区分：

- Strategy：目标、约束、路径、风险、证据计划。
- Architecture：不变量、事实源、边界、兼容性、失败模式。
- Implementation：测试、typecheck/lint、diff、API/schema contract。
- Runtime：真实执行、日志、readback、恢复、回滚证明。
- Enterprise Delivery：UAT、审计链、权限矩阵、SLO/SLA、安全、成本、发布/回滚包。

闭环规则：

```text
Output is not done until every frozen acceptance criterion has evidence or an explicit human-accepted waiver.
```

---

## 10. 权限与人门

Action risk levels：

- L0：read-only / projection
- L1：local reversible write / draft / doc / dry-run
- L2：local controlled mutation / task state transition / evidence attach
- L3：external write / worker start / customer-visible action
- L4：destructive / payment / secret-entry / legal / production irreversible

默认策略：

- L0/L1 可自动执行并留证据。
- L2 需 policy allowlist + rollback。
- L3 需 project policy 或人工审批。
- L4 必须人工显式确认。

---

## 11. 产品化路线

### Phase 0：Contract-first Kernel

交付：

- module schema
- workflow spec schema
- run lockfile schema
- evidence schema
- acceptance schema
- policy gate schema
- ledger event schema
- read-only validator
- ADR

验收：schema tests + dry-run 示例 + no execution side effect。

### Phase 1：Read-only Control Tower

交付：

- ledger 初始化
- adapters observation
- snapshot API
- dashboard read-only projection
- taskpool health / worker / evidence / blockers view

验收：隔离 profile smoke；dashboard 只读；事实源指向 ledger。

### Phase 2：Command Registry + Human Inbox

交付：

- proposal-only command registry
- approval lifecycle
- human inbox
- policy preview
- rollback preview

验收：命令只能 proposal，不执行真实外部副作用。

### Phase 3：Workflow Compiler MVP

交付：

- NL intent → WorkflowSpec draft
- semantic diff
- static checks
- risk classification
- DAG dry-run
- run lockfile generation

验收：同一输入可重复生成稳定 spec；高风险自动进入 human gate。

### Phase 4：Module Runtime + Model Router

交付：

- module registry
- model routing policy
- route trace
- shadow/canary lifecycle
- fallback chain

验收：低风险模块可自动运行；生产 run 默认 pinned。

### Phase 5：Agent Pack Studio

交付：

- Pack manifest
- workflow/module/model/permission editor
- UAT/golden cases
- deployment/runbook package
- private Docker/API/CLI/Bot packaging

验收：能打包一个可复现 Pack，不依赖临时 prompt。

### Phase 6：Enterprise Delivery Cockpit

交付：

- tenant/project profile
- deployment status
- audit log
- SLA/SLO view
- usage/cost view
- incident / rollback console

验收：企业交付可运维，而不是 demo。

### Phase 7：Self-evolution Loop

交付：

- failure pattern classifier
- skill/eval/policy/test ratchet
- shadow eval replay
- workflow pack improvement proposal
- human approval for kernel-impacting changes

验收：经验沉淀进入正确边界，不污染 memory/global rules。

---

## 12. 最小可卖产品顺序

不要先做通用 Agent Builder 大而全。

建议先做三个垂直 Pack：

1. **投研日报 / 市场情报 Pack**
   - 数据源监控 → 去重 → 证据引用 → 摘要 → 风险标注 → 分发。
   - 低外部写风险，容易展示价值。

2. **项目 PM / 验收证据 Pack**
   - PRD/任务 → 代码/接口/UI 证据 → 缺口 → 人工 gate → 报告。
   - 贴合你现有强项与 Hermes 任务池能力。

3. **多模型代码审查 / 质量门禁 Pack**
   - diff → 静态检查 → 多模型审查 → 证据 → gate → PR comment/报告。
   - 企业可付费点清晰。

这三个 Pack 反向验证 kernel，而不是先闭门造平台。

---

## 13. 决策结论

最终长期稳定方案的主线应该是：

> 以 Control Tower Ledger 为唯一事实源，以 WorkflowSpec + RunLockfile 固化执行，以 Module Registry + Model Router 承载能力，以 Evidence + Acceptance 关闭结果，以 Human Gate 控制风险，最后打包成可销售的 Agent / Workflow Pack。

第一阶段不要先做花哨 UI 或“万能 Agent”。

第一阶段应该先落：

1. schema/contract
2. read-only ledger/snapshot
3. workflow/module/model/acceptance/policy 版本化
4. 一个垂直 Pack 的 dry-run 到 evidence 闭环

这条路径最小化长期重构风险，也最接近可交付、可审计、可卖的产品形态。
