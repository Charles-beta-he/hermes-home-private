---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["1 self-proving executor schema; 2 command proof artifact; 3 git safety gates; 4 taskpool lifecycle integration"]
created: 2026-05-19T13:24:34+08:00
updated: 2026-05-19T13:34:18+08:00
expires_at: 2026-06-18T13:24:34+08:00
project: local-brain
architecture_target: taskpool
capability_delta: Hermes gains a self-proving executor that can run verification bundles, emit machine-readable proof, and prevent failed runs from looking complete.
anti_drift_check: Do not auto-push; do not mark done on py_compile-only proof; protected branches and dirty-state resets must be explicit and audited.
acceptance_evidence: artifact:/Users/charles/.hermes/hermes-agent/docs/private/autonomous-workflow-execution-plan.md plus PASS/FAIL smoke proof artifacts from self_proving_executor.
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
multimodel_triage_result: "P1/evolution: directly blocks false completion; deterministic local proof first, no expensive multimodel required for skeleton."
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-19T13:34:17+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260519-052439-142983-p71898-a51728f0-a5f799d7/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-19-p1-a-autoresearch式自证执行闭环测试达标才-checkpoint失败自动证据化回退-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: /Users/charles/.hermes
parallel_boundary: Serial P1-A before telemetry consumers; code writes isolated to ~/.hermes/scripts and private plan.
evidence:
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-052439-142983-p71898-a51728f0-a5f799d7/discussion_result.json"
  - proof:sha256:437af1c29ea2894c53b2e5d5e02100c06bde54b9f0c30993afcdadc275a200cb
  - artifact:/Users/charles/.hermes/scripts/self_proving_executor.py
  - artifact:/Users/charles/.hermes/hermes-agent/docs/private/autonomous-workflow-execution-plan.md
  - proof:self_proving_executor PASS smoke emitted pass.proof.json with safe_next_action=advance_to_review_with_artifact
  - proof:self_proving_executor FAIL smoke exited 1 and emitted fail.proof.json with safe_next_action=retry_or_reset_with_failure_artifact
concepts: ["task", "hermes", "autonomous-workflow-execution"]
multimodel_advisory_only: True
multimodel_certification_authority: True
multimodel_advisory_reasons: ["architecture_target", "evolution_lane"]
multimodel_certification_reasons: ["closeout_ratification"]
---

# Task - P1-A AutoResearch式自证执行闭环：测试达标才 checkpoint失败自动证据化回退

## Objective

Implement the AutoResearch-style self-test/checkpoint/reset loop as Hermes self-proving execution substrate.

## Acceptance Criteria

- [x] Observable result is recorded in Proof Log.
- [x] Self-proving executor emits structured PASS proof and safe advancement action.
- [x] Self-proving executor emits structured FAIL proof, exits nonzero, and never reports advancement.
- [x] No commit/push/reset is performed by default.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| `python3 -m py_compile ~/.hermes/scripts/self_proving_executor.py ~/.hermes/scripts/test_self_proving_executor.py` | PASS | syntax verified |
| `/Users/charles/.hermes/hermes-agent/.venv/bin/python -m pytest ~/.hermes/scripts/test_self_proving_executor.py -q` | PASS | 2 passed |
| PASS smoke via `self_proving_executor.py --config pass.json` | PASS | artifact status=PASS, safe_next_action=advance_to_review_with_artifact |
| FAIL smoke via `self_proving_executor.py --config fail.json` | PASS | process exit=1, artifact status=FAIL, safe_next_action=retry_or_reset_with_failure_artifact |
| `brain_task_orchestrator.py selfcheck --json` | PASS | `/tmp/autonomous-workflow-selfcheck.json` |
| `brain_task_orchestrator.py proof-check --json` | PASS | `/tmp/autonomous-workflow-proof-check.json` |
| `brain_task_dispatch_tick.py --summary --print-always --no-state` | PASS | schema=brain_task_dispatch_tick_summary_v1, status=OK, error_count=0 |

## Proof Log

- 2026-05-19T13:24:34+08:00: Task created from local-brain control point.
- 2026-05-19T13:45:00+08:00: Created `/Users/charles/.hermes/scripts/self_proving_executor.py` and regression test `/Users/charles/.hermes/scripts/test_self_proving_executor.py`.
- 2026-05-19T13:45:00+08:00: PASS smoke emitted structured proof with `safe_next_action=advance_to_review_with_artifact`; FAIL smoke exited nonzero and emitted `safe_next_action=retry_or_reset_with_failure_artifact`.
- 2026-05-19T13:45:00+08:00: Verified taskpool control plane: selfcheck PASS, proof-check PASS, dispatch tick status OK/error_count=0.

## Blockers / Confusions

- None for the P1-A skeleton. Next dependency is P1-B skill telemetry; full lifecycle integration can build on the proof schema.

## Final Handoff

- Status: P1-A skeleton implemented and verified.
- Evidence: `/Users/charles/.hermes/scripts/self_proving_executor.py`, `/Users/charles/.hermes/scripts/test_self_proving_executor.py`, `/tmp/autonomous-workflow-selfcheck.json`, `/tmp/autonomous-workflow-proof-check.json`, `/tmp/autonomous-workflow-dispatch-tick.json`.
- Residual risk: checkpoint commit/reset behavior is intentionally not implemented yet; current safe default is verify-only proof emission.

- 2026-05-19T13:24:38+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-19T13:24:38+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-19T13:34:17+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-052439-142983-p71898-a51728f0-a5f799d7/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T13:34:17+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-052439-142983-p71898-a51728f0-a5f799d7/discussion_result.json

- 2026-05-19T13:34:18+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:437af1c29ea2894c53b2e5d5e02100c06bde54b9f0c30993afcdadc275a200cb, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-052439-142983-p71898-a51728f0-a5f799d7/discussion_result.json
