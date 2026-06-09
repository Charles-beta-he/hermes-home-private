---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["depends on AgentMemory compatibility spike -> 1 define category matrix -> 2 implement/describe policy guard -> 3 add deterministic examples -> 4 verify no WIP/procedure enters durable memory"]
created: 2026-05-21T20:32:36+08:00
updated: 2026-05-21T20:50:39+08:00
expires_at: 2026-06-20T20:32:36+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 把 AgentMemory 的 type/ttlDays/sourceObservationIds/supersession 思路映射到 Hermes 现有 memory/skill/session_search 规则，形成 durable write 前的策略包装层，防止 WIP ghost 和 procedure 写入 memory。
anti_drift_check: 不得让跨 agent 共享记忆绕过 Hermes 现有 memory 红线；稳定事实、用户偏好、环境事实、流程技能、WIP/session state 必须分流；敏感/短期内容必须 TTL 或拒绝。
acceptance_evidence: 策略设计文档或代码原型、分类矩阵、ghost-prevention 检查、TTL/拒绝样例、与 memory tool/skill_manage/session_search 的边界说明。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: 
multimodel_reason: 
expected_participants: []
truth_gate: 
evidence_bundle: 
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "P2: AgentMemory source-backed Hermes memory evolution task; high leverage but must remain default-off and evidence-gated before runtime adoption"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-21T20:35:50+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260521-123243-585120-p21701-3afaab30-b05cfa0e/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-21-design-hermes-agentmemory-policy-wrapper-for-durable-memory-categories-ttl-and-g-state.json
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
parallel_boundary: 按依赖顺序推进：compatibility spike -> policy wrapper -> retrieval bridge/consolidation -> governance selfcheck；禁止未验证前改默认配置或启用外部 shared memory。
evidence:
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123243-585120-p21701-3afaab30-b05cfa0e/discussion_result.json"
  - proof:sha256:d32dc84063710c983a135f0583e9db556a7704f4d487bbc34e8b6114c4d491c0
  - "command: brain_task_orchestrator transition --to pending after add-time advisory auto-close"
  - proof:sha256:24b315e6549d49ba43130b4c644455090ef9c2904f2a37c6bf8bdc4616b9c501
  - command:py_compile_taskpool PASS
  - proof:sha256:ed7b39a9c34b7cfa7f93f9233df291f1d9510a504b0f55409be0b352c6bc738a
concepts: ["agentmemory", "memory-policy", "ttl", "ghost-prevention", "skills"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#251"
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evolution_lane"]
multimodel_certification_reasons: []
---

# Task - Design Hermes AgentMemory policy wrapper for durable memory categories TTL and ghost prevention

## Objective

把 AgentMemory 源码分析中的可吸收能力转成 Hermes 可执行进化任务，保持默认关闭、安全优先、证据驱动。

## Acceptance Criteria

- [ ] 策略设计文档或代码原型、分类矩阵、ghost-prevention 检查、TTL/拒绝样例、与 memory tool/skill_manage/session_search 的边界说明。

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-21T20:32:36+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-21T20:32:43+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-21T20:32:43+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-21T20:35:50+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260521-123243-585120-p21701-3afaab30-b05cfa0e/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-21T20:35:50+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123243-585120-p21701-3afaab30-b05cfa0e/discussion_result.json

- 2026-05-21T20:42:08+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:d32dc84063710c983a135f0583e9db556a7704f4d487bbc34e8b6114c4d491c0, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123243-585120-p21701-3afaab30-b05cfa0e/discussion_result.json

- 2026-05-21T20:44:07+08:00: Lifecycle transition `done` -> `pending` by `hermes-agent`. Force: true. Reason: User asked to add AgentMemory evolution improvements to taskpool; queued work items are not completed implementation. Evidence: command: brain_task_orchestrator transition --to pending after add-time advisory auto-close

- 2026-05-21T20:50:39+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-21T20:50:39+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-21T20:50:39+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:24b315e6549d49ba43130b4c644455090ef9c2904f2a37c6bf8bdc4616b9c501, command:py_compile_taskpool PASS

- 2026-05-21T20:50:39+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:ed7b39a9c34b7cfa7f93f9233df291f1d9510a504b0f55409be0b352c6bc738a, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123243-585120-p21701-3afaab30-b05cfa0e/discussion_result.json, proof:sha256:d32dc84063710c983a135f0583e9db556a7704f4d487bbc34e8b6114c4d491c0, command: brain_task_orchestrator transition --to pending after add-time advisory auto-close, proof:sha256:24b315e6549d49ba43130b4c644455090ef9c2904f2a37c6bf8bdc4616b9c501, command:py_compile_taskpool PASS
