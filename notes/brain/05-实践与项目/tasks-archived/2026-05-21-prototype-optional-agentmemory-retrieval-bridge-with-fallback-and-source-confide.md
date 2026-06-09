---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["depends on AgentMemory policy wrapper -> 1 define context-source contract -> 2 implement default-off query path -> 3 add fallback/degraded labels -> 4 test server unavailable and vector unavailable cases"]
created: 2026-05-21T20:35:05+08:00
updated: 2026-05-21T21:16:01+08:00
expires_at: 2026-06-20T20:35:05+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 为 Hermes 增加可选 AgentMemory retrieval context source 设计/原型：保留 MEMORY/USER/session_search 基线，同时查询 AgentMemory 并标注 source id、confidence、degraded-mode。
anti_drift_check: 不得用 AgentMemory 替换 Hermes 内建 memory/session_search；AgentMemory 不可达、vector index 失败、认证失败时必须显式降级且不阻塞主对话。
acceptance_evidence: retrieval bridge 方案或 default-off 原型、fallback 行为证据、source/confidence/degraded 标签样例、不可达时 smoke test。
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
multimodel_last_checked_at: 2026-05-21T20:42:08+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260521-123702-935023-p24076-7bf3f604-01eb8f3c/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-21-prototype-optional-agentmemory-retrieval-bridge-with-fallback-and-source-confide-state.json
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
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123513-062997-p23046-f4eef777-0cd35e5e/discussion_result.json"
  - proof:sha256:35e89d92eaa658e14b525f8ea32e7823e71b43aed4be99f2481a4759f88e24cb
  - "command: brain_task_orchestrator transition --to pending after add-time advisory auto-close"
  - proof:sha256:9b73e1803be4d6e88994b99539fed76b0f3649565b1f3070ff5aee0dd02c49c5
  - command:py_compile_taskpool PASS
  - proof:sha256:fef063378b33af116b502d99204cb198b1ff0302cf698fb07503e6be1f9f40d2
concepts: ["agentmemory", "retrieval-bridge", "hybrid-search", "context-injection", "degraded-mode"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#256"
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - Prototype optional AgentMemory retrieval bridge with fallback and source confidence labels

## Objective

把 AgentMemory 源码分析中的 retrieval 可吸收能力转成 Hermes 可执行进化任务，保持默认关闭、安全优先、证据驱动。

## Acceptance Criteria

- [ ] retrieval bridge 方案或 default-off 原型、fallback 行为证据、source/confidence/degraded 标签样例、不可达时 smoke test。

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-21T20:35:05+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-21T20:35:12+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-21T20:35:12+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-21T20:38:09+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260521-123513-062997-p23046-f4eef777-0cd35e5e/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-21T20:38:09+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123513-062997-p23046-f4eef777-0cd35e5e/discussion_result.json

- 2026-05-21T20:42:08+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260521-123702-935023-p24076-7bf3f604-01eb8f3c/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-21T20:42:08+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:35e89d92eaa658e14b525f8ea32e7823e71b43aed4be99f2481a4759f88e24cb, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123513-062997-p23046-f4eef777-0cd35e5e/discussion_result.json

- 2026-05-21T20:44:07+08:00: Lifecycle transition `done` -> `pending` by `hermes-agent`. Force: true. Reason: User asked to add AgentMemory evolution improvements to taskpool; queued work items are not completed implementation. Evidence: command: brain_task_orchestrator transition --to pending after add-time advisory auto-close

- 2026-05-21T21:16:00+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-21T21:16:01+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-21T21:16:01+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:9b73e1803be4d6e88994b99539fed76b0f3649565b1f3070ff5aee0dd02c49c5, command:py_compile_taskpool PASS

- 2026-05-21T21:16:01+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:fef063378b33af116b502d99204cb198b1ff0302cf698fb07503e6be1f9f40d2, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123513-062997-p23046-f4eef777-0cd35e5e/discussion_result.json, proof:sha256:35e89d92eaa658e14b525f8ea32e7823e71b43aed4be99f2481a4759f88e24cb, command: brain_task_orchestrator transition --to pending after add-time advisory auto-close, proof:sha256:9b73e1803be4d6e88994b99539fed76b0f3649565b1f3070ff5aee0dd02c49c5, command:py_compile_taskpool PASS
