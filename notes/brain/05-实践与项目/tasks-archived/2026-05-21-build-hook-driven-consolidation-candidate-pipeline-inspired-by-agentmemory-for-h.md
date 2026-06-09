---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["depends on AgentMemory policy wrapper -> 1 map existing Hermes hooks/bg-review -> 2 define candidate schema -> 3 produce suggest-only prototype/report -> 4 gate enqueue/write paths"]
created: 2026-05-21T20:36:50+08:00
updated: 2026-05-21T21:46:29+08:00
expires_at: 2026-06-20T20:36:50+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 借鉴 AgentMemory prefetch/sync_turn/session_end/pre_compress/on_memory_write 生命周期，为 Hermes 设计会话结束后的 memory/skill candidate 提议流水线，先 suggest 后 enqueue，避免自动写入假记忆。
anti_drift_check: 不得自动把候选写入 durable memory/skills；候选必须带 evidence、source session、ghost-prevention 检查与人工/确定性 gate；与现有 bg-review/taskpool suggest mode 对齐。
acceptance_evidence: 生命周期映射、candidate schema、suggest/enqueue 边界、至少 3 个样例候选及拒绝理由、bg-review/taskpool 集成点验证。
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
multimodel_last_checked_at: 2026-05-21T20:39:32+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260521-123659-175708-p23962-0bffa79c-29b0eb73/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-21-build-hook-driven-consolidation-candidate-pipeline-inspired-by-agentmemory-for-h-state.json
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
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123659-175708-p23962-0bffa79c-29b0eb73/discussion_result.json"
  - proof:sha256:7ccf1918b159a888ae06086d8d4169411a08ec7f4fb65449e72f60bb9ce2bec2
  - "command: brain_task_orchestrator transition --to pending after add-time advisory auto-close"
  - proof:sha256:076f111ad17760afdf67e204ec8a485cbb5f7fc736d86f0dd359805d5a0ee5a7
  - command:py_compile_taskpool PASS
  - proof:sha256:4c8e556308a366761ee2baad25d683483606df709e0d38b4837724e53a524b1d
concepts: ["agentmemory", "hook-capture", "consolidation", "memory-candidates", "skill-candidates", "bg-review"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#261"
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evolution_lane"]
multimodel_certification_reasons: []
---

# Task - Build hook-driven consolidation candidate pipeline inspired by AgentMemory for Hermes sessions

## Objective

把 AgentMemory 源码分析中的 hook-driven consolidation 能力转成 Hermes 可执行进化任务，保持默认关闭、安全优先、证据驱动。

## Acceptance Criteria

- [ ] 生命周期映射、candidate schema、suggest/enqueue 边界、至少 3 个样例候选及拒绝理由、bg-review/taskpool 集成点验证。

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-21T20:36:50+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-21T20:36:58+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-21T20:36:58+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-21T20:39:32+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260521-123659-175708-p23962-0bffa79c-29b0eb73/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-21T20:39:32+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123659-175708-p23962-0bffa79c-29b0eb73/discussion_result.json

- 2026-05-21T20:42:08+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:7ccf1918b159a888ae06086d8d4169411a08ec7f4fb65449e72f60bb9ce2bec2, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123659-175708-p23962-0bffa79c-29b0eb73/discussion_result.json

- 2026-05-21T20:44:08+08:00: Lifecycle transition `done` -> `pending` by `hermes-agent`. Force: true. Reason: User asked to add AgentMemory evolution improvements to taskpool; queued work items are not completed implementation. Evidence: command: brain_task_orchestrator transition --to pending after add-time advisory auto-close

- 2026-05-21T21:46:29+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-21T21:46:29+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-21T21:46:29+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:076f111ad17760afdf67e204ec8a485cbb5f7fc736d86f0dd359805d5a0ee5a7, command:py_compile_taskpool PASS

- 2026-05-21T21:46:29+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:4c8e556308a366761ee2baad25d683483606df709e0d38b4837724e53a524b1d, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123659-175708-p23962-0bffa79c-29b0eb73/discussion_result.json, proof:sha256:7ccf1918b159a888ae06086d8d4169411a08ec7f4fb65449e72f60bb9ce2bec2, command: brain_task_orchestrator transition --to pending after add-time advisory auto-close, proof:sha256:076f111ad17760afdf67e204ec8a485cbb5f7fc736d86f0dd359805d5a0ee5a7, command:py_compile_taskpool PASS
