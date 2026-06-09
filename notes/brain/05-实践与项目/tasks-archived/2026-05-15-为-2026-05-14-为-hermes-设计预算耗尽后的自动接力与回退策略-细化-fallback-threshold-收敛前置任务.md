---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-15T10:30:14+08:00
updated: 2026-05-19T19:05:27+08:00
expires_at: 2026-06-13T01:37:20+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: fallback threshold narrowed brief
anti_drift_check: separate threshold policy from relay implementation so the parent scope does not drift
acceptance_evidence: proof log states threshold semantics and the evidence gate for noop-vs-change
workflow_contract: "['[08-模板/task-workflow-contract-template]']"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260516-125102-192257-p6455-ddc50336-e9e70865/discussion_result.json
multimodel_last_checked_at: 2026-05-16T20:54:40+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260516-125102-192257-p6455-ddc50336-e9e70865/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-15-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-fallback-threshold-收敛前置任务-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: fallback_threshold
auto_subtask_trigger: auto_subtask_on_non_convergence:fallback_threshold
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260513-213742-502936-p80883-2e691a87-ed06220b/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - proof:sha256:a6cacd622ae51d87b99a0a74dcc067e5044477ec81c37fe0a4f4b10f1f9fa5db
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:965a9d7281e1f457bfc7979005adf655b60b0374f96fb9d511004a254eb54ba3
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:c48076c42ece6a9151b74bc10fdb263a42b86055f5036de50c52650329f24327
  - proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json
  - proof:sha256:8324b7a030fe832fde531a74c6cc4e7155d709d788664ca7a3e8f039f91ee51d
  - proof:sha256:79e3a293fb39b629ee69df9839663679f999356a922e3efc894d966569690feb
concepts: ["task", "auto-subtask", "non-convergence", "fallback-thresholds"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略 细化 fallback threshold 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略`. Do not change the parent objective. Define fallback thresholds, downgrade policy, and the minimum evidence required to justify noop vs change on budget exhaustion behavior.

## Acceptance Criteria

- [ ] Produce a narrowed brief covering trigger thresholds, allowed fallback actions, and explicit noop-vs-change decision criteria.

## Plan / Workpad

- [ ] Reconcile current state before execution.
- [ ] Execute the smallest verifiable slice.
- [ ] Record proof and update status.

## Parent Link

- Parent task: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
- Discussion artifact: /Users/charles/.hermes/tick-20260513-213742-502936-p80883-2e691a87-ed06220b/discussion_result.json
- Trigger axis: fallback_threshold
- Issue IDs: none tagged

## Parent Objective Snapshot

设计预算耗尽后的自动 continuation handoff 与回退策略，形成从耗尽检测到续跑恢复的完整闭环。

## Narrowed Scope

- Only resolve threshold semantics and noop-vs-change decision criteria.
- Do not redesign the full handoff workflow here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-15T10:30:14+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-15T10:32:13+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: auto-claim-and-handoff

- 2026-05-15T10:41:42+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260515-023213-946515-p52842-e7ac96da-5833340f/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-16T20:50:40+08:00: Reconcile action `stale_claim_released` by `hermes-reconcile`. Previous status `claimed`.

- 2026-05-16T20:51:01+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-16T20:51:01+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-16T20:51:01+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:965a9d7281e1f457bfc7979005adf655b60b0374f96fb9d511004a254eb54ba3, command:py_compile_taskpool PASS

- 2026-05-16T20:51:01+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:c48076c42ece6a9151b74bc10fdb263a42b86055f5036de50c52650329f24327, proof:sha256:965a9d7281e1f457bfc7979005adf655b60b0374f96fb9d511004a254eb54ba3, command:py_compile_taskpool PASS

- 2026-05-16T20:54:23+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260516-125102-192067-p6449-41e5dd11-a74fc929/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-16T20:54:40+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260516-125102-192257-p6455-ddc50336-e9e70865/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T11:11:13+08:00: Lifecycle transition `done` -> `pending` by `hermes-closeout-audit`. Force: true. Reason: new closeout rule audit: done evidence is py_compile/hash/multimodel-only or lacks task-type-specific real-chain acceptance; reopening for honest completion Evidence: proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json

- 2026-05-19T19:05:27+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-19T19:05:27+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-19T19:05:27+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:8324b7a030fe832fde531a74c6cc4e7155d709d788664ca7a3e8f039f91ee51d, command:py_compile_taskpool PASS

- 2026-05-19T19:05:27+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:79e3a293fb39b629ee69df9839663679f999356a922e3efc894d966569690feb, proof:sha256:a6cacd622ae51d87b99a0a74dcc067e5044477ec81c37fe0a4f4b10f1f9fa5db, classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task, classification:legacy_autorun_proof_hash=sha256:965a9d7281e1f457bfc7979005adf655b60b0374f96fb9d511004a254eb54ba3, command:py_compile_taskpool PASS, classification:legacy_autorun_proof_hash=sha256:c48076c42ece6a9151b74bc10fdb263a42b86055f5036de50c52650329f24327, proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json, proof:sha256:8324b7a030fe832fde531a74c6cc4e7155d709d788664ca7a3e8f039f91ee51d
