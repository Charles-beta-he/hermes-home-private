---
type: task
lane: evolution
layer: L3
status: review
priority: P1
priority_layer: P1-3
dependency_order: ["3/4 depends_on:P1-2"]
created: 2026-05-23T18:04:15+08:00
updated: 2026-05-27T18:11:27+08:00
expires_at: 2026-06-22T18:04:15+08:00
project: hermes-agent
architecture_target: skill-graph
capability_delta: Hermes verifies the new coding guardrails improve surgical edits without over-triggering on trivial/non-coding tasks.
anti_drift_check: Include cases where simple typo fixes stay lightweight, broad migrations are not blocked, and low-ambiguity tasks do not trigger unnecessary questions.
acceptance_evidence: "command: pytest/eval command output plus fixtures showing positive and negative routing cases."
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: 
multimodel_reason: 
expected_participants: []
truth_gate: evals cover both trigger and non-trigger behavior
evidence_bundle: /tmp/andrej-karpathy-skills-hermes-adoption-state.json
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: Pre-ingest analysis requires evals before calling the guardrail successful; T1 consult_models attempted and all_failed due adapter timeouts.
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-23T18:11:47+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260523-100423-712887-p7255-7f074426-e8b49868/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-23-add-negative-space-evals-for-karpathy-style-hermes-coding-guardrails-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 1
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260523-100423-712887-p7255-7f074426-e8b49868/discussion_result.json"
  - proof:sha256:4069e720e342f037b97fb3ba61cd50c58619fa2059faca4c70776c47e8bb0b11
  - file:/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md
  - proof:sha256:9937b5559e22901fd5a4c1ec6585f11b3598881f9c856ae654d7b9ff785c43b1
  - command:py_compile_taskpool PASS
  - proof:sha256:70b47286a31d34bc9bdbb18af274ff0bbc9a7c363bb0582f2f66e9c80652835e
  - command:agent_team_controller consume-claimed human_escape_release
  - proof:sha256:9cef986c4a46515f6d4a4e05fb60f35269b29db7618d072e272edc71ea409ad9
concepts: ["karpathy-guidelines", "evals", "negative-space", "skill-routing"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#4698"
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evidence_bundle_contract", "evolution_lane", "truth_gate_contract"]
multimodel_certification_reasons: []
manual_review_decided_at: 2026-05-27T16:20:00+08:00
manual_review_decided_by: user-approved-multimodel-review
manual_review_classification: REOPEN_FOR_TASKPOOL
manual_review_approval_action: approve_reopen
manual_review_final_landed: false
manual_review_result_ref: /Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md
manual_review_reason: P1；缺真实 eval fixtures + pytest/read-back，重开 guardrail eval 落地。
---

# Task - Add negative-space evals for Karpathy-style Hermes coding guardrails

## Objective

Create or extend tests/evals proving adapted coding guardrails trigger for coding/refactor/debug/review tasks and do not degrade trivial fixes, non-coding tasks, or explicitly requested broad architecture changes.

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

- 2026-05-27T16:20:00+08:00: User approved multimodel manual-review classification REOPEN_FOR_TASKPOOL; action=approve_reopen; final_landed=false; ref=/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md; reason=P1；缺真实 eval fixtures + pytest/read-back，重开 guardrail eval 落地。

- 2026-05-23T18:04:15+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-23T18:04:23+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-23T18:04:23+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-23T18:11:47+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260523-100423-712887-p7255-7f074426-e8b49868/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-23T18:11:47+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260523-100423-712887-p7255-7f074426-e8b49868/discussion_result.json

- 2026-05-23T18:18:11+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:4069e720e342f037b97fb3ba61cd50c58619fa2059faca4c70776c47e8bb0b11, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260523-100423-712887-p7255-7f074426-e8b49868/discussion_result.json

- 2026-05-27T16:20:49+08:00: Lifecycle transition `done` -> `pending` by `hermes-manual-review`. Force: true. Reason: user approved multimodel manual review: reopen non-final done task for prototype/benchmark/adopt-update Evidence: file:/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md

- 2026-05-27T16:23:24+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-27T16:23:27+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-27T16:23:27+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:9937b5559e22901fd5a4c1ec6585f11b3598881f9c856ae654d7b9ff785c43b1, command:py_compile_taskpool PASS

- 2026-05-27T16:23:27+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:70b47286a31d34bc9bdbb18af274ff0bbc9a7c363bb0582f2f66e9c80652835e, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260523-100423-712887-p7255-7f074426-e8b49868/discussion_result.json, proof:sha256:4069e720e342f037b97fb3ba61cd50c58619fa2059faca4c70776c47e8bb0b11, file:/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md, proof:sha256:9937b5559e22901fd5a4c1ec6585f11b3598881f9c856ae654d7b9ff785c43b1, command:py_compile_taskpool PASS

- 2026-05-27T16:23:57+08:00: Lifecycle transition `done` -> `pending` by `hermes-manual-review`. Force: true. Reason: manual-review approval/status correction: queued for real implementation/evidence work; event-hook bounded static proof is not final completion Evidence: file:/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md

- 2026-05-27T16:51:40+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-parallel`. Reason: parallel-claim-and-handoff; batch=parallel-20260527165128-3

- 2026-05-27T16:52:12+08:00: Lifecycle transition `claimed` -> `retry` by `hermes-parallel`. Reason: event-driven worker blocked by human escape; claim released for retry: {'blocks': 0, 'failures': 3, 'since_ack': {'blocks': 0, 'failures': 3, 'invalid_timestamps': 0}, 'historical': {'blocks': 4, 'failures': 87, 'invalid_timestamps': 0}, 'ack': {'status': 'ok', 'acked_at': '2026-05-26T07:20:51Z', 'acked_by': 'human', 'reason': 'authorized by user full-pool advance; pos Evidence: command:agent_team_controller consume-claimed human_escape_release

- 2026-05-27T17:55:46+08:00: Reconcile action `retry_due_promoted` by `hermes-reconcile`. Previous status `retry`.

- 2026-05-27T18:11:24+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-27T18:11:27+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-27T18:11:27+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:9cef986c4a46515f6d4a4e05fb60f35269b29db7618d072e272edc71ea409ad9, command:py_compile_taskpool PASS
