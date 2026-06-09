---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-17T10:54:07+08:00
updated: 2026-05-17T11:07:33+08:00
expires_at: 2026-06-13T01:37:20+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: relay ordering narrowed brief
anti_drift_check: relay ordering must stay downstream of quota and threshold decisions
acceptance_evidence: proof log names continuation packet timing and parent re-entry points
workflow_contract: "['[08-模板/task-workflow-contract-template]']"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260517-030737-291545-p50732-8ad82da7-fb106bcc/discussion_result.json
multimodel_last_checked_at: 2026-05-17T11:11:42+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-030737-291545-p50732-8ad82da7-fb106bcc/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-relay-ordering-收敛前置任务-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: relay_ordering
auto_subtask_trigger: auto_subtask_on_non_convergence:relay_ordering
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - "proof: manual convergence closeout by hermes; narrowed brief written, artifact recorded, and py_compile_narrowed_briefs PASS"
  - command:py_compile_narrowed_briefs PASS
  - artifact:/Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json
concepts: ["task", "auto-subtask", "non-convergence", "relay-ordering"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略 细化 relay ordering 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略`. Do not change the parent objective. Define continuation packet / relay ordering after quota and threshold semantics are known, without reopening the parent mission objective.

## Acceptance Criteria

- [x] Produce a narrowed brief covering continuation packet timing, relay ordering, and parent handoff integration points.

## Plan / Workpad

- [x] Reconcile current state before execution.
- [x] Execute the smallest verifiable slice.
- [x] Record proof and update status.

## Narrowed Brief — Relay Ordering

- **Ordering contract:** 1) 先由 budget gate 判断不可继续；2) 固化 continuation state / evidence；3) 再释放当前执行链并触发后续 relay；4) 只有在 state 已持久化时才允许切模型或重进主循环。
- **Why this order:** 本轮 discussion 的 `agreement_low` 主要不是是否要 relay，而是 relay 与证据固化的先后不够清晰；如果在 evidence 未固化前先切换模型/继续执行，会把 budget exhaustion 和 retry 语义缠在一起。
- **Scope boundary:** 本子任务只冻结顺序，不决定预算阈值，也不扩展到 router 调权。
- **Integration points:** parent 只需要一个“预算不足 -> 生成 packet -> handoff/retry”的最短闭环；任何更复杂的回退树都应留给后续实现任务。

## Parent Link

- Parent task: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
- Discussion artifact: /Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json
- Trigger axis: relay_ordering
- Issue IDs: none tagged

## Parent Objective Snapshot

设计预算耗尽后的自动 continuation handoff 与回退策略，形成从耗尽检测到续跑恢复的完整闭环。

## Narrowed Scope

- Only resolve relay ordering and continuation packet timing.
- Assume quota/threshold semantics are separate prerequisites.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| relay-ordering narrowed brief | PASS | continuation ordering fixed as detect -> persist -> release -> relay |

## Proof Log

- 2026-05-17T10:54:07+08:00: Task created from local-brain control point.
- 2026-05-17T11:03:00+08:00: Converted the latest relay-ordering disagreement into a smallest-closed ordering contract and kept threshold / quota semantics out of scope.
- 2026-05-17T11:00:42+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: manual blocked-parent convergence execution
- 2026-05-17T11:00:44+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: record narrowed convergence brief

## Blockers / Confusions

- None.

## Final Handoff

- Status: ready_for_review
- Evidence: latest discussion artifact + narrowed ordering contract
- Residual risk: exact implementation hooks still need parent-level code work; this slice only freezes sequencing.

- 2026-05-17T11:07:32+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: narrowed brief recorded Evidence: proof:sha256:28c7df8e0305e0457b226fd2e17a0126aa0a855cdcbcadc4d1d65c18c10e123b, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json

- 2026-05-17T11:07:33+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: narrowed brief accepted as convergence evidence Evidence: proof:sha256:28c7df8e0305e0457b226fd2e17a0126aa0a855cdcbcadc4d1d65c18c10e123b, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json

- 2026-05-17T11:08:18+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-030046-294477-p42029-27d8d217-ef6759b1/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T11:11:42+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-030737-291545-p50732-8ad82da7-fb106bcc/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
