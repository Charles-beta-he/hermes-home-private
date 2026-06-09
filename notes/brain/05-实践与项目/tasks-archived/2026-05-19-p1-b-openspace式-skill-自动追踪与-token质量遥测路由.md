---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["1 append-only ledger schema; 2 report command; 3 runtime skill hook; 4 routing policy hints"]
created: 2026-05-19T13:34:19+08:00
updated: 2026-05-19T13:12:36Z
expires_at: 2026-06-18T13:34:19+08:00
project: local-brain
architecture_target: skill-graph
capability_delta: Hermes gains skill usage telemetry tied to task outcomes so cost and quality regressions are visible.
anti_drift_check: Do not silently remove required skills to save tokens; telemetry is local append-only and cannot auto-patch skills without review.
acceptance_evidence: empty-ledger and sample-ledger report PASS; later runtime hook records skill_view events with task/outcome linkage.
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
multimodel_triage_result: "P1/evolution: reduces prompt/token drift and makes skill selection auditable; depends on P1-A proof artifact shape."
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: /Users/charles/.hermes
parallel_boundary: Can run after P1-A schema; should not modify skill content automatically.
evidence: []
concepts: ["task", "hermes", "autonomous-workflow-execution"]
---

# Task - P1-B OpenSpace式 skill 自动追踪与 token质量遥测路由

## Objective

Implement OpenSpace-style skill telemetry and routing observability.

## Acceptance Criteria

- [ ] Observable result is recorded in Proof Log.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| `python3 /Users/charles/.hermes/scripts/skill_telemetry_report.py --ledger /Users/charles/.hermes/kanban/workspaces/t_9e71c54b/empty-skill-telemetry.jsonl --json` | PASS | `ledger_state=empty`, `event_count=0`, `task_count=0` |
| `python3 /Users/charles/.hermes/scripts/skill_telemetry_report.py --ledger /Users/charles/.hermes/kanban/workspaces/t_9e71c54b/sample-skill-telemetry.jsonl --json` | PASS | `event_count=4`, `correlated_task_count=2`, per-skill pass/fail split emitted |
| `python3 /Users/charles/.hermes/scripts/test_skill_telemetry_report.py` | PASS | Regression tests cover empty ledger, correlated sample ledger, and CLI JSON output |

## Proof Log

- 2026-05-19T13:34:19+08:00: Task created from local-brain control point.
- 2026-05-19T13:12:36Z: Implemented `/Users/charles/.hermes/scripts/skill_telemetry_report.py` as the bounded P1-B slice. The script reads append-only JSONL telemetry, tolerates empty/missing ledgers, correlates `skill_load` and `task_outcome` events by task/session/run key, and reports token proxy plus quality/pass associations.
- 2026-05-19T13:12:36Z: Added `/Users/charles/.hermes/scripts/test_skill_telemetry_report.py` to lock the empty-ledger PASS contract, sample-ledger correlation summary, and CLI `--json` output.

## Blockers / Confusions

- Future runtime hook remains intentionally deferred: current slice establishes the append-only ledger report surface only, per dependency order.

## Final Handoff

- Status: done
- Evidence: `skill_telemetry_report.py` + `test_skill_telemetry_report.py` landed; empty-ledger and sample-ledger report commands both PASS; sample output shows per-skill load counts, token proxy averages, routing reasons, and PASS/FAIL task linkage.
- Residual risk: runtime `skill_view` / prompt-assembly hook is not wired yet, so production telemetry still depends on a later event emitter landing on the same schema.

- 2026-05-19T13:34:24+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-19T13:34:24+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-19T13:56:36+08:00: Lifecycle transition `running` -> `pending` by `hermes`. Force: true. Reason: orphaned_multimodel_running_cleanup:no_live_process_no_discussion_artifact
