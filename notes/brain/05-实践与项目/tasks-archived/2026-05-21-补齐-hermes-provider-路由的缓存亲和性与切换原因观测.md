---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: provider-control-plane
dependency_order: ["1. 盘点 Hermes 当前 provider/model routing 日志字段与 quota 状态记录", "2. 定义不含敏感提示词的 cache_affinity、provider_stickiness、route_reason、switch_reason 最小事件字段", "3. 在非侵入式 dry-run 或日志层验证字段可生成且不改变路由决策", "4. 形成是否进入实现的补丁计划与回滚策略"]
created: 2026-05-21T09:06:31+08:00
updated: 2026-05-21T09:29:36+08:00
expires_at: 2026-06-04T09:06:31+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: 提升 provider quota 主链可诊断性，减少因隐式缓存或 provider 粘滞导致的成本、延迟、质量异常难以复盘的问题。
anti_drift_check: 只记录路由元数据和过期/切换原因，不记录用户敏感内容；不得把第三方 OpenRouter 行为假设硬编码为所有 provider 的事实。
acceptance_evidence: 产出路由观测字段清单与一段本地 dry-run/模拟日志样例，能展示 cache affinity present/absent、route_reason、switch_reason，且确认未改变实际调用路径。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: 
multimodel_reason: 该候选限定为观测与设计，不改变真实路由；策略级变更才需要多模型复核。
expected_participants: ["single-agent", "maintainer-review"]
truth_gate: report-evidence-present
evidence_bundle: AIHOT 2026-05-21 条目：OpenRouter 自动路由缓存机制说明——OpenRouter 会将会话固定在一个模型/提供商上直到缓存过期。
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "not_required: 当前仅要求观测字段与设计盘点，不改变 provider 选择；涉及实际路由策略变更时再触发多模型。"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-21T09:15:48+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260521-010638-140059-p76667-11434305-af490293/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-21-补齐-hermes-provider-路由的缓存亲和性与切换原因观测-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 可与 local-codegraph 评测并行；不得与 provider 默认模型切换、quota 强制策略或外部 API 调用重试策略改动并行合入。
evidence:
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-010638-140059-p76667-11434305-af490293/discussion_result.json"
  - proof:sha256:0528678104a3717ceddf99f5b615d255bdf76dd738bb85ab77b03e40f6e16487
concepts: ["provider-quota", "routing", "cache-affinity", "observability", "control-plane"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#169"
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["accuracy_keyword", "architecture_target", "closeout_ratification", "evidence_bundle_contract", "evolution_lane", "expected_participants_contract", "explicit_multimodel_reason", "truth_gate_contract"]
multimodel_certification_reasons: []
---

# Task - 补齐 Hermes provider 路由的缓存亲和性与切换原因观测

## Objective

让 Hermes 在 provider quota 与自动路由场景下能解释一次会话为什么固定在某 provider、缓存亲和性何时存在、何时因 quota/错误/缓存过期而切换。

## Acceptance Criteria

- [ ] Observable result is recorded in Proof Log.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-21T09:06:31+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-21T09:06:37+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-21T09:06:37+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-21T09:15:48+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260521-010638-140059-p76667-11434305-af490293/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-21T09:15:48+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-010638-140059-p76667-11434305-af490293/discussion_result.json

- 2026-05-21T09:29:36+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:0528678104a3717ceddf99f5b615d255bdf76dd738bb85ab77b03e40f6e16487, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-010638-140059-p76667-11434305-af490293/discussion_result.json
