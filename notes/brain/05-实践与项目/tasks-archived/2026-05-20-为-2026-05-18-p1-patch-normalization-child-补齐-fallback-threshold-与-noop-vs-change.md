---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["2 after quota_observability and patch_normalization"]
created: 2026-05-20T17:06:33+08:00
updated: 2026-05-20T17:12:09+08:00
expires_at: 2026-06-19T17:06:33+08:00
project: hermes-agent-cache-optimization
architecture_target: provider-quota
capability_delta: fallback_threshold and noop_vs_change ledger narrowed brief for parent reratification
anti_drift_check: do not mark parent done; only resolve threshold/noop ledger evidence for next ratification refresh
acceptance_evidence: brief classifies concrete threshold/router/verifier proposals as accept/defer/reject with rollback boundary and proof-check/selfcheck evidence
workflow_contract: "[08-模板/task-workflow-contract-template]"
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
multimodel_triage_result: targeted evidence fix after T3 economy pause
auto_subtask_parent: 2026-05-18-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-patch-n
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: fallback_threshold
auto_subtask_trigger: manual_targeted_evidence_after_economy_pause:fallback_threshold
auto_subtask_issue_ids: ["I-001", "I-002"]
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260520-084941-635917-p32921-83a774a3-651ef47b/merged_plan.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - artifact:/Users/charles/.hermes/state/taskpool-follow-through/2026-05-20-parent-targeted-refresh-human-review.json
  - artifact:/Users/charles/.hermes/tick-20260520-084941-635917-p32921-83a774a3-651ef47b/merged_plan.json
  - classification:axis=fallback_threshold_and_noop_vs_change_pending
  - command:autorun-runner_handoff_created
  - artifact:/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-20-为-2026-05-18-p1-patch-normalization-child-补齐-fallback-threshold-与-noop-vs-change.md
  - command:brain_task_orchestrator.py_proof-check_PASS
  - proof:sha256:2108091890f6dc25a011563fb88eed8c5c60eb5d50a46aa9599ba416d3132101
concepts: ["task", "auto-subtask", "non-convergence", "fallback-threshold", "noop-vs-change"]
---

# Task - 为 2026-05-18 P1 patch-normalization child 补齐 fallback-threshold 与 noop-vs-change ledger 定向收敛证据

## Objective

Create a bounded targeted evidence brief for parent 2026-05-18...patch-n resolving fallback_threshold criteria_missing and noop-vs-change ledger ambiguity without broadening the parent objective.

## Acceptance Criteria

- [x] A file-backed brief exists, acceptance checkboxes are complete, and the task reaches review/done only with deterministic proof evidence; parent remains blocked until ratification refresh.
- [x] The noop-vs-change ledger explicitly classifies P-002/P-003/P-004 and ratify-patch-normalization-slice as accept/defer/reject with rationale.
- [x] The fallback threshold rule states when threshold changes are allowed and when parse-error handling must happen first.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.


## Targeted Evidence Brief — fallback_threshold + noop_vs_change

Source checkpoint: `/Users/charles/.hermes/tick-20260520-084941-635917-p32921-83a774a3-651ef47b/merged_plan.json` plus round-001 discussion responses. The round did not certify; it surfaced the exact evidence needed for the next bounded slice.

Ledger decisions:

| Proposal | Decision | Rationale | Rollback boundary |
|---|---|---|---|
| P-002 `tune_threshold` / lower agreement threshold | Defer, do not accept as first patch | Threshold lowering can hide provider_parse_error and noop-vs-change ambiguity. It is only allowed after parse failures are excluded from the denominator and the concrete/noop ledger is explicit. | Restore threshold to current default if pass rate improves by masking unresolved severity >=3 ledger items. |
| P-003 `add_verifier` | Accept as evidence requirement, not runtime code in this slice | A verifier is needed, but this child should only define the acceptance contract: candidate patch must carry target file, op, rationale, expected metric, and rollback signal. | If verifier blocks valid noop certification, downgrade to WARN-only until ratified. |
| P-004 `modify_router_weight` / down-weight dissenting Claude | Reject | Dissent is evidence, not a reason to reduce router weight. Down-weighting a model because it disagreed corrupts future fanout diversity. | No router weight change is authorized by this child. |
| `ratify-patch-normalization-slice` | Defer to parent ratification refresh | It may become valid only after this ledger plus parse-error handling are included in the parent evidence packet. | Parent remains blocked/pending, not done, until gate=PASS and decision=LOOP_DONE. |

Fallback threshold rule:
1. If provider output is malformed or parse-error-tainted, exclude that response from threshold denominator only with explicit `provider_parse_error` evidence; do not lower truth gate.
2. If noop-vs-change ledger has unresolved severity >=3 items, threshold tuning is prohibited.
3. If concrete patch count is nonzero, the packet must either name a minimal accepted patch set or explicitly downgrade each concrete patch to advisory/noop with evidence.
4. Router weights must not be changed as a consequence of a non-approve vote.

Completion boundary: this child is a targeted evidence task. It may be dispatched and completed with deterministic proof, but parent completion still requires refreshed ratification gate PASS/LOOP_DONE.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | PASS | task claimed/running from autorun handoff |
| targeted evidence brief | PASS | lines 70-89 classify P-002/P-003/P-004/ratify-patch-normalization-slice and fallback threshold rule |
| proof-check | PASS | command:brain_task_orchestrator.py proof-check --json |

## Proof Log

- 2026-05-20T17:06:33+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status: targeted evidence child completed; parent must still run ratification refresh before closeout.
- Evidence: fallback_threshold/noop_vs_change brief in this task note; parent refresh artifact `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-20-parent-targeted-refresh-human-review.json`; model checkpoint `/Users/charles/.hermes/tick-20260520-084941-635917-p32921-83a774a3-651ef47b/merged_plan.json`.
- Residual risk: parent gate remains FAIL/CONTINUE_LOOP until refreshed certification passes; do not mark parent done from this child alone.

- 2026-05-20T17:08:04+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun`. Reason: auto-claim-and-handoff

- 2026-05-20T17:08:19+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun`. Reason: execute_targeted_evidence_child_after_autorun_handoff Evidence: command:autorun-runner_handoff_created

- 2026-05-20T17:12:00+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun`. Reason: targeted_evidence_brief_complete_ready_for_done Evidence: artifact:/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-20-为-2026-05-18-p1-patch-normalization-child-补齐-fallback-threshold-与-noop-vs-change.md, command:brain_task_orchestrator.py_proof-check_PASS

- 2026-05-20T17:12:09+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun`. Reason: targeted_evidence_child_complete_parent_requires_ratification_refresh Evidence: artifact:/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-20-为-2026-05-18-p1-patch-normalization-child-补齐-fallback-threshold-与-noop-vs-change.md, command:brain_task_orchestrator.py_proof-check_PASS, proof:sha256:2108091890f6dc25a011563fb88eed8c5c60eb5d50a46aa9599ba416d3132101
