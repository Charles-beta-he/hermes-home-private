---
type: playbook
layer: L4
status: active-stable
created: 2026-06-30T15:40:00+08:00
finalized: 2026-06-30T15:40:00+08:00
stability_class: long_term_canonical_plan
concepts: [multimodel-smart-routing, route-review-gate, surface-routing, evidence-gate, degraded-not-certified, fail-closed]
source_evidence:
  - 07-关键点多模型介入路由矩阵
  - 12-本地大脑全量自动约束层最终长期稳定方案
  - consult_models_status_ACTUAL_T0_T1_T2_T3_20260630
  - consult_models_tick_20260630_073340_degraded_not_certified_truth_grounded
related:
  - 07-关键点多模型介入路由矩阵
  - 12-本地大脑全量自动约束层长期方案
---

# 13 - 多模型智能路由 Review 最终长期稳定方案

## 0. 最终稳定结论

多模型智能路由 Review 的最终形态不是“四模型永远全量投票”，而是一个可审计、可回放、可降级、fail-closed 的 RouteReviewGate。

稳定定义：任何需要模型评审的关键改动，必须先经过 RouteReviewGate：

Change / Claim / Evidence → Surface Classification → Risk Tier → Capability Match → Side-effect Boundary → Evidence-State Check → Model Route Plan → Fanout / Specialist Review → Truth Gate → Ratification / Degraded Verdict → Action Boundary。

核心口径：

1. 按 surface / risk / capability / side-effect / evidence-state 路由，不按模型名崇拜，也不按简单多数投票。
2. 模型意见默认是 advisory；只有绑定非模型证据、命中 required_evidence、并通过角色分离与 quorum/ratification 的意见，才能参与完成认证。
3. 实现者/生产者不能认证自己的 completion-critical claim。
4. T2/T3 或外部副作用类任务在 quorum 退化、证据缺失、模型健康不明时必须 fail-closed 或降级为 not_certified，不允许“多模型想过了”代替证据。
5. RouteReviewGate 是 BrainConstraintRecord 的 review/routing 子门禁，也是 taskpool closeout、completion-claim gate、skill/SSOT 写回的统一评审入口。

## 1. 当前证据与边界

已验证：

- `07-关键点多模型介入路由矩阵.md` 已定义 T0/T1/T2/T3 的基本分层：T0 机械低风险、T1 单领域 sanity、T2 跨目录/跨系统 fanout、T3 P10/Hermes 自进化/canonical 规则/安全不可逆 full discussion 或 not_certified + local gates。
- `12-本地大脑全量自动约束层最终长期稳定方案.md` 已把 Multi-model Smart Routing 放入 Brain Constraint Gate 流程。
- `consult_models.py status` 显示当前系统支持 ACTUAL real model calls，并有 T0/T1/T2/T3 quorum/min/planners 配置。
- 2026-06-30 T1 评审尝试得到 truth grounded，但 fanout below min_quorum，因此本轮只能作为 degraded_not_certified / single-substantive-model advisory，不可声称多模型完整认证。

未实现/不可声称：

- RouteReviewGate 还不是 runtime hard gate。
- live model readiness 不稳定时，不能声称 T2/T3 quorum 当前总能满足。
- 当前方案是最终长期稳定架构与入口契约，不是自动执行完成态。

## 2. Core object: RouteReviewRecord

```yaml
RouteReviewRecord:
  schema: route_review_record_v1
  review_id: string
  created_at: iso8601
  subject:
    kind: change|claim|completion_claim|brain_constraint|taskpool_closeout|skill_update|ssot_update|external_action
    summary: string
    target_files: []
    target_systems: []
    claim_ids: []
  classification:
    surfaces: []          # architecture, code, ui_visual, retrieval, safety, mlops, taskpool, docs, domain
    risk_tier: T0|T1|T2|T3
    side_effect_class: read_only|local_write|lifecycle_write|external_dispatch|publish_deploy_push|destructive|credential_payment
    reversibility: reversible|rollback_available|irreversible|unknown
    blast_radius: local|project|workflow|runtime|external|global
  evidence_state:
    required_evidence: []
    provided_evidence: []
    missing_evidence: []
    evidence_coverage: 0.0
    truth_status: unsupported|needs_link_review|grounded|contradicted
    non_model_evidence_present: bool
  routing:
    primary_specialist: string
    adversarial_reviewers: []
    optional_reviewers: []
    excluded_reviewers: []
    exclusion_reasons: []
    quorum_required: int
    min_quorum: int
    role_separation_required: bool
    producer_models: []
  execution:
    mode: no_model|single_specialist|fanout|discussion|ratification|human_gate
    timeout_seconds: int
    cost_budget: optional
    health_snapshot_ref: string
  votes:
    - model: string
      role: specialist|adversary|arbiter|producer|observer
      verdict: approve|amend|reject|abstain|timeout|unhealthy
      evidence_refs: []
      confidence: 0.0
      advisory_only: bool
  verdict:
    status: pass|warn|amend|block|not_certified|degraded_not_certified|human_authority_required
    certified: bool
    multi_model_certified: bool
    reasons: []
    allowed_actions: []
    forbidden_actions: []
    next_required_gates: []
  readback:
    artifacts: []
    commands: []
    receipts: []
```

## 3. Routing dimensions

### 3.1 Surface first, not model first

| Surface | Primary reviewer | Secondary / adversarial | Required non-model evidence |
|---|---|---|---|
| Architecture / control-plane | Claude/architecture arbiter | GPT or DeepSeek risk review | design doc, code path, route table, readback |
| Code implementation | GPT/Codex or Claude Code | DeepSeek adversarial/code-risk | diff, unit tests, py_compile/build, regression output |
| UI / visual | Gemini visual if available | Claude/GPT UX reasoning | screenshot, browser interaction, console/network evidence |
| Retrieval / local brain | Claude architecture | GPT implementation + deterministic fixture | search output, accepted/filtered hits, reindex/readback |
| Safety / permissions | Claude governance | DeepSeek adversarial | exact target, authority, rollback, post-action readback |
| MLOps / model health | mlops route / GPT | Claude architecture | provider status, smoke probe, quota/health snapshot |
| Taskpool / lifecycle | Claude governance | DeepSeek/GPT state-machine review | task record, lifecycle command, proof log, transition readback |
| Domain facts / research | research/source tools first | model synthesis only after source packet | source URLs/files, quotes, timestamps, extraction logs |

### 3.2 Risk tier then quorum

| Tier | Trigger | Review shape | Quorum / certification | Degraded policy |
|---|---|---|---|---|
| T0 | Mechanical/read-only/low-risk, tool-verifiable | no model or one specialist sanity | tool evidence enough; single model not multi-certified | proceed if deterministic evidence passes |
| T1 | Single-surface design/docs/local low blast radius | one specialist + optional second reviewer | min 1 for advisory; min 2 for multi-model wording | advisory allowed; do not claim multi-certified |
| T2 | Cross-file/cross-workflow/code gate/local automation | specialist + adversarial reviewer + deterministic gate | min 2, prefer 3; producer excluded | block or degraded_not_certified until evidence/quorum fixed |
| T3 | Runtime/control-plane/lifecycle/external/destructive/canonical rule | full discussion/ratification + objective evidence + authority gate | min 3 and role-separated; human authority if side effect | fail-closed; not_certified cannot become done |

### 3.3 Evidence-state gate

Before model routing, RouteReviewGate must classify evidence:

- `unsupported`: route may ask for evidence, but cannot certify.
- `needs_link_review`: repair evidence links before voting.
- `grounded`: model review may evaluate sufficiency and risk.
- `contradicted`: block until contradiction resolved.
- `advisory_only`: model opinions exist but required non-model evidence is missing.

## 4. State machine

| State | Meaning | Exit gate |
|---|---|---|
| REVIEW_REQUESTED | 需要 review 的改动/声明出现 | subject + claim/evidence packet |
| SURFACE_CLASSIFIED | surface/risk/side-effect/blast radius 完成 | route dimensions complete |
| EVIDENCE_CHECKED | required_evidence 与 provided_evidence 对齐 | no unsupported high-severity claims |
| ROUTE_PLANNED | primary/adversarial/arbiter/quorum 确定 | role separation checked |
| HEALTH_PROBED | 模型健康、quota、timeout、skip 状态读取 | enough reachable reviewers or degraded policy selected |
| FANOUT_RUNNING | 调用模型或 no-model deterministic gate | artifacts written |
| VOTES_NORMALIZED | votes 归一化为 approve/amend/reject/timeout/unhealthy | evidence_refs checked |
| TRUTH_GATED | 非模型证据与模型判断分离 | unsupported/contradicted cannot certify |
| RATIFIED_OR_DEGRADED | 输出 certified / not_certified / degraded_not_certified | action boundary explicit |
| WRITEBACK | 写回 BrainConstraintRecord/taskpool/SSOT/skill refs | readback proves artifact exists |

## 5. Fail-closed 条件

任一满足即 block / not_certified / degraded_not_certified：

1. T2/T3 quorum 未达。
2. required_evidence 缺失，尤其是工具/测试/readback/截图/proof。
3. producer model 的 self-report 被用于完成认证。
4. 模型 vote 没有 evidence_refs，却被当作认证证据。
5. truth_status 为 unsupported、needs_link_review 或 contradicted。
6. 只有多数赞成，但少数意见指出未解决的安全/权限/数据/不可逆风险。
7. 模型健康/配额不明，却声称 full discussion 或 certified。
8. external/publish/destructive/credential/payment/broad fanout 没有 exact target + authority + rollback + readback。
9. 旧项目经验或过期 brain note 被当作 current SSOT。
10. 内部 JSON/auto-relay/projection 中的“完成”文字被误当用户-facing completion claim。

## 6. Degraded 策略

### 6.1 Degraded classes

| Class | Meaning | Allowed output | Forbidden output |
|---|---|---|---|
| single_model_quorum_met | 单模型完成 T0/T1 advisory | advisory / draft / evidence request | multi-model certified |
| below_min_quorum | 未达 min quorum | degraded_not_certified | done / certified / force-close |
| provider_unhealthy | timeout/quota/exhausted/skipped | health boundary + retry plan | 永久删除模型或降低全局 quorum |
| truth_not_grounded | 证据不足或链接失败 | evidence repair request | claim accepted |
| not_certified | 讨论未认证 | implementation proof only; lifecycle not done | done transition |
| advisory_only | 模型有意见但缺非模型证据 | risk notes / next evidence | completion claim |

### 6.2 Degraded still useful

降级不等于无效。它可以用于：

- 生成方案草案。
- 提出 evidence_requests。
- 标记 live readiness gap。
- 创建 taskpool follow-up。
- 辅助人类决策。

但不能用于：

- T2/T3 closeout。
- 完成声明认证。
- lifecycle done。
- runtime hard gate 放行。
- 外部副作用执行授权。

## 7. Integration with BrainConstraintRecord

RouteReviewRecord 是 BrainConstraintRecord 的 `routing` 与 `verdict` 子对象扩展。

推荐绑定方式：

```yaml
BrainConstraintRecord.routing.route_review_ref: path/to/route_review_record.json
BrainConstraintRecord.routing.model_route: RouteReviewRecord.routing
BrainConstraintRecord.verdict.status: derived from RouteReviewRecord.verdict.status
BrainConstraintRecord.evidence.receipts: include route review artifacts
```

BrainConstraintGate 负责“哪些知识/规则相关”；RouteReviewGate 负责“哪些模型/证据/角色应该评审”。两者不能合并成一个黑箱：

- BrainConstraintGate 选择约束。
- RouteReviewGate 评审约束和改动是否满足。
- EvidenceGate 决定事实是否成立。
- AuthorityGate 决定副作用是否允许。

## 8. Integration with taskpool / completion claims / skills

### 8.1 Taskpool closeout

T2/T3 taskpool closeout 需要：

- deterministic proof。
- route_review_record。
- truth_status grounded。
- required participant quorum 或明确 not_certified。
- not_certified 时不得自动 done；进入 intervention packet。

### 8.2 Completion-claim gate

用户-facing “完成/已验证/production-ready” 前：

- 抽取 completion claim。
- 绑定 route_required_evidence。
- 若 claim 涉及 UI，必须有截图/browser/console；若涉及代码，必须有 test/build；若涉及外部，必须有 receipt/readback。
- 模型只评估证据充分性，不替代证据。

### 8.3 Skill / SSOT 写回

多模型 review 结果可沉淀到 skill/SSOT 的条件：

- 不是单次项目状态。
- 有至少一个非模型证据。
- 有反例/适用边界。
- 有 fail-closed 或 rollback 条件。
- T2/T3 经验需要 degraded 状态标注，不能包装成 fully certified。

## 9. Implementation phases

### P0 - 最终稳定文档与 schema（当前阶段）

产物：

- 本文档。
- RouteReviewRecord schema。
- routing table、state machine、fail-closed、degraded 策略。

当前验收：

- 现有路由矩阵与全量自动约束层文档已 readback。
- consult_models 当前状态已 readback。
- 本次评审 truth grounded，但 degraded_not_certified；不得声称多模型完整认证。

### P1 - Local dry-run RouteReviewGate

新增：

- `route_review_gate.py --subject ... --claims ... --evidence ... --json`
- fixture-only / no side effect。

能力：

- classify surface/risk/side-effect。
- 生成 RouteReviewRecord。
- 读取 consult_models status/health snapshot。
- 输出 no_model/single_specialist/fanout/discussion/human_gate route plan。
- 不真正调用外部副作用。

### P2 - Evidence-linked fanout

能力：

- 对 T1/T2 调 consult_models。
- 自动修复/报告 claim-id evidence link mismatch。
- 将 votes 归一化为 advisory/certifying。
- 生成 degraded_not_certified 时的 evidence_requests。

### P3 - Taskpool / BrainConstraintGate 集成

能力：

- taskpool closeout 前自动附 RouteReviewRecord。
- BrainConstraintRecord 引用 route_review_ref。
- completion-claim gate 可读取 route_required_evidence。
- not_certified 阻止 T2/T3 done。

### P4 - Runtime-aware hard gate

前提：P1-P3 误拦截率、latency、model health、成本可控。

能力：

- 对 Hermes runtime/control-plane/lifecycle/external/high-risk 改动硬阻断。
- 支持 kill switch。
- 支持 provider health breaker，但不永久降低 quorum。
- 支持 human authority packet。

## 10. Metrics

- route_precision：路由到的模型是否匹配 surface。
- required_evidence_coverage：route_required_evidence 覆盖率。
- quorum_satisfied_rate：各 tier quorum 满足率。
- degraded_not_certified_rate：退化率。
- false_block_rate：误阻断率。
- missed_risk_rate：漏路由高风险 surface。
- producer_self_cert_block_count：阻断自证次数。
- model_cost_per_review：单 review 模型成本。
- review_latency_p95：评审延迟。
- completion_claim_reversal_count：完成声明被证据门撤回次数。

## 11. Human authority boundary

RouteReviewGate 永远不授权以下动作，只能请求授权：

- 外部发送 / broad fanout。
- push / deploy / publish。
- destructive cleanup / delete / migration。
- payment / credential / secret entry。
- runtime scheduler/worker/lifecycle 真写入，如果未在 exact target 授权内。
- 将 advisory route 直接升级为 hard gate。

## 12. Final operating rule

最终稳定规则一句话：

先判 surface，再判 risk，再判证据，再判模型角色；模型只评审证据充分性与风险，不替代证据；T2/T3 没有 quorum、证据或授权就 fail-closed；降级结果可指导下一步，但不能伪装成认证完成。

## 13. 中文检索别名

多模型智能路由 Review RouteReviewGate RouteReviewRecord surface risk capability side-effect evidence-state T0 T1 T2 T3 degraded_not_certified not_certified advisory_only producer self certification required evidence completion claim gate taskpool closeout BrainConstraintRecord fail-closed quorum model health route_required_evidence
