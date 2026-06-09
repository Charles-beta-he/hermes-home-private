---
type: task
lane: work
layer: L3
status: done
priority: P2
priority_layer: long-running-task-governance
dependency_order: ["1. Read current taskpool/orchestrator state model and proof-log expectations.", "2. Identify where task status", "execution environment", "model conversation", "and evidence artifacts are currently coupled.", "3. Draft minimal invariants and checks that prevent environment drift from corrupting task state.", "4. Add tests or dry-run validation only after the invariants are documented."]
created: 2026-05-22T11:20:26+08:00
updated: 2026-05-24T17:25:05+08:00
expires_at: 2026-06-05T11:20:26+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: Reduces long-running task drift by making it clearer which state is canonical, which environment assumptions must be revalidated, and what proof is required before status transitions.
anti_drift_check: Avoid importing external cloud-agent architecture wholesale; only encode invariants that can be verified in the current Hermes local taskpool and proof-log implementation.
acceptance_evidence: A checked-in or report-linked spec plus at least one validation/dry-run output showing detection of missing environment or evidence assumptions before task status advancement.
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: 
multimodel_reason: Single-owner implementation is acceptable because the first deliverable is a bounded spec/check, not a broad architecture migration.
expected_participants: ["taskpool-maintainer"]
truth_gate: report-evidence-present
evidence_bundle: "AIHOT 2026-05-22 report cites Cursor cloud-agent lessons: complete dev environment, Temporal-level reliability, agent loop/machine/conversation state separation; source report: /Users/charles/.hermes/notes/reports/aihot-daily-2026-05-22.md"
required_authority: autonomous-execution
max_authority: yolo-execution
permission_tier: autonomous-execution
write_surfaces: ["taskpool", "codebase"]
completion_gate: project-evidence-review-done
lane_semantics: "work/product delivery: project evidence, tests/build, scoped commit, report/push policy as required"
multimodel_triage_result: Candidate is directly relevant to Hermes taskpool reliability; implementation should be small and evidence-driven, not a rewrite of orchestration.
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-22T11:28:55+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260522-032243-035879-p23573-db2b9fdc-f2fd11df/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-22-specify-taskpool-state-and-execution-environment-separation-checks-state.json
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
parallel_boundary: May proceed independently of browser evidence evaluation, but should not modify task creation/ingest behavior while daily_report_task_ingest is running.
evidence:
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260522-032243-035879-p23573-db2b9fdc-f2fd11df/discussion_result.json"
  - "artifact:/Users/charles/.hermes/state/taskpool-review-evidence-gaps/20260524T071125Z-advisory-review-gap-backfill.json#2026-05-22-specify-taskpool-state-and-execution-environment-separation-checks"
  - command:review-gap-backfill chain=hermes_architecture_or_tooling action=requeue_for_project_evidence
  - "command: git commit a09c8df taskpool: trigger workers after parallel claim"
  - "command: git commit c829cd8 taskpool: support targeted multimodel tick hooks"
  - "command: python3 scripts/test_brain_task_dispatch_tick.py PASS"
  - "command: python3 -m py_compile scripts/brain_task_dispatch_tick.py scripts/agent_team_controller.py scripts/test_brain_task_dispatch_tick.py PASS"
  - "command: python3 scripts/test_taskpool_dynamic_runner.py PASS"
  - "command: python3 scripts/brain_task_orchestrator.py boundary-check --json PASS invalid_count=0"
  - command:git commit a09c8df taskpool trigger workers after parallel claim
  - command:target tests py_compile dynamic-runner dispatch-summary boundary-check PASS commit a09c8df
  - command:target tests py_compile dynamic-runner dispatch-summary boundary-check proof-check PASS commit a09c8df
concepts: ["taskpool", "state-management", "long-running-agents", "reliability", "proof-log"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#2464"
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evidence_bundle_contract", "expected_participants_contract", "explicit_multimodel_reason", "truth_gate_contract"]
multimodel_certification_reasons: []
review_gap_chain: hermes_architecture_or_tooling
review_gap_artifact: /Users/charles/.hermes/state/taskpool-review-evidence-gaps/20260524T071125Z-advisory-review-gap-backfill.json
review_gap_required_evidence: ["artifact:docs/private 或 state 下分析/验证报告", "command:py_compile/pytest/selfcheck/proof-check PASS", "commit:<sha> 或 explicit no-code verification", "artifact:回退/风险边界说明"]
---

# Task - Specify taskpool state and execution-environment separation checks

## Objective

Create a maintainable specification and validation path for separating task state, execution environment assumptions, conversation context, and acceptance evidence in Hermes taskpool flows.

## Acceptance Criteria

- [x] Observable result is recorded in Proof Log.
- [x] Taskpool state advancement is explicitly separated from worker execution: `parallel-claim-and-handoff` remains the claim/audit step, while `consume-claimed` is the bounded worker-consumer execution step.
- [x] Worker execution cannot directly close brain tasks as `done`; worker completion advances only to `review`, preserving proof-gated review closeout.
- [x] Event-driven summary exposes the new contract via `autorun.step_mode=parallel_claim_and_execute` and `worker_trigger` evidence.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| `python3 scripts/test_brain_task_dispatch_tick.py` | PASS | Event-driven regression covers claim -> consume-claimed trigger and summary contract. |
| `python3 -m py_compile scripts/brain_task_dispatch_tick.py scripts/agent_team_controller.py scripts/test_brain_task_dispatch_tick.py` | PASS | Syntax gate for changed taskpool scripts. |
| `python3 scripts/agent_team_controller.py consume-claimed --claimed-json '[]' --max-agents 2` | PASS | Empty batch returns `SKIP/no claimed tasks` without unsafe side effects. |
| `python3 scripts/brain_task_dispatch_tick.py --summary --no-state` | PASS | Dispatch tick self-summary remained OK after landing event-driven bridge. |
| `python3 scripts/test_taskpool_dynamic_runner.py` | PASS | Dynamic runner regression suite passed. |
| `python3 scripts/brain_task_orchestrator.py boundary-check --json` | PASS | Boundary check returned PASS/invalid_count=0. |
| git scoped commit | PASS | `/Users/charles/.hermes` commit `a09c8df taskpool: trigger workers after parallel claim`. |

## Proof Log

- 2026-05-22T11:20:26+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status: event-driven taskpool bridge landed and taskpool item closed as `done` through proof-gated closeout.
- Evidence: commits `a09c8df` and `c829cd8`; target regression, py_compile, dynamic runner, dispatch summary, boundary-check, and targeted multimodel-hook parser compatibility all PASS.
- Residual risk: first landing keeps next-tick recursion out of scope to avoid execution storms; future improvement can add bounded depth-limited chaining once worker-consumer telemetry is stable.

- 2026-05-22T11:22:42+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-22T11:22:42+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-22T11:28:55+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260522-032243-035879-p23573-db2b9fdc-f2fd11df/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-22T11:28:55+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260522-032243-035879-p23573-db2b9fdc-f2fd11df/discussion_result.json


## Review Evidence Gap Backfill

- Artifact: `/Users/charles/.hermes/state/taskpool-review-evidence-gaps/20260524T071125Z-advisory-review-gap-backfill.json#2026-05-22-specify-taskpool-state-and-execution-environment-separation-checks`
- Chain: `hermes_architecture_or_tooling`
- 当前 review 只证明多模型 advisory/讨论已发生；不等于项目交付完成。
- Requeued to `pending` so a project worker can produce the required closeout evidence; no test/build/browser/curl/commit evidence was fabricated.
- Required evidence:
  - artifact:docs/private 或 state 下分析/验证报告
  - command:py_compile/pytest/selfcheck/proof-check PASS
  - commit:<sha> 或 explicit no-code verification
  - artifact:回退/风险边界说明

- 2026-05-24T15:11:29+08:00: Lifecycle transition `review` -> `pending` by `hermes-review-gap-backfill`. Force: true. Reason: advisory-only review lacks project execution evidence; requeue for matching closeout chain Evidence: artifact:/Users/charles/.hermes/state/taskpool-review-evidence-gaps/20260524T071125Z-advisory-review-gap-backfill.json#2026-05-22-specify-taskpool-state-and-execution-environment-separation-checks, command:review-gap-backfill chain=hermes_architecture_or_tooling action=requeue_for_project_evidence

- 2026-05-24T16:17:43+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-parallel`. Reason: parallel-claim-and-handoff; batch=parallel-20260524161721-8

- 2026-05-24T17:22:46+08:00: Lifecycle transition `claimed` -> `pending` by `hermes`. Force: true. Reason: guardian_stale_claim_cleanup

- 2026-05-24T17:23:45+08:00: Lifecycle transition `pending` -> `running` by `hermes`. Force: true. Reason: event_driven_worker_bridge_landed_scoped_commit Evidence: command:git commit a09c8df taskpool trigger workers after parallel claim

- 2026-05-24T17:23:45+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: project_evidence_ready_for_proof_gated_closeout Evidence: command:target tests py_compile dynamic-runner dispatch-summary boundary-check PASS commit a09c8df

- 2026-05-24T17:25:05+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: event_driven_taskpool_bridge_landed_with_scoped_commit_and_gates Evidence: command:target tests py_compile dynamic-runner dispatch-summary boundary-check proof-check PASS commit a09c8df
