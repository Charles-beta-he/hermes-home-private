---
type: task
lane: work
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["3"]
created: 2026-05-21T01:32:21+08:00
updated: 2026-05-21T02:17:52+08:00
expires_at: 2026-06-04T01:32:21+08:00
project: external-control
architecture_target: 
capability_delta: 
anti_drift_check: 
acceptance_evidence: action_request fixture 测试 + stale telemetry refusal + duplicate idempotency no-op + dry-run audit + 无持久化 access code
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: physical-world actuation gate for printer upload/start requires safety review
expected_participants: []
truth_gate: 
evidence_bundle: 
required_authority: autonomous-execution
max_authority: yolo-execution
permission_tier: autonomous-execution
write_surfaces: ["taskpool", "codebase"]
completion_gate: project-evidence-review-done
lane_semantics: "work/product delivery: project evidence, tests/build, scoped commit, report/push policy as required"
multimodel_triage_result: P2
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: external-control-bambu-x2d-actuation
evidence:
  - file:/Users/charles/.hermes/scripts/external_control_gate.py
  - file:/Users/charles/.hermes/scripts/test_external_control_gate.py
  - command:python3 /Users/charles/.hermes/scripts/test_external_control_gate.py => OK 4 tests
  - command:HOME=/Users/charles python3 /Users/charles/.hermes/scripts/brainctl.py --json brains validate => passed true
concepts: ["external-control", "bambu", "x2d", "confirmation", "idempotency", "audit"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#122"
---

# Task - 外控脑 Photo-to-Print S3: X2D start_print 确认门与审计执行器

## Objective

实现 external_control_action 审核/确认/幂等/审计执行骨架；默认 dry-run，真实 start_print 需显式确认 token 和新鲜遥测。

## Acceptance Criteria

- [x] Observable result is recorded in Proof Log.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | not-run | Task note is canonical; no orchestrator mutation was required for this bounded verification pass. |
| `python3 /Users/charles/.hermes/scripts/test_external_control_gate.py` | passed | OK 4 tests after making the harness resolve `external_control_gate.py` relative to `__file__` instead of `Path.home()`. |
| `HOME=/Users/charles python3 /Users/charles/.hermes/scripts/brainctl.py --json brains validate` | passed | `passed: true`; external-control brain registry and runtime repo checks all green. |

## Proof Log

- 2026-05-21T01:32:21+08:00: Task created from local-brain control point.
- 2026-05-21T02:17:52+08:00: Re-verified the external-control gate and closed the reproducibility gap in the test harness by resolving `external_control_gate.py` relative to the test file instead of `Path.home()`, which was profile-sandbox dependent in kanban worker runs.
- 2026-05-21T02:17:52+08:00: `python3 /Users/charles/.hermes/scripts/test_external_control_gate.py` passed all four acceptance checks: confirmation-token gate, stale-telemetry refusal, duplicate-idempotency noop, and dry-run audit without persisting access-code material.
- 2026-05-21T02:17:52+08:00: `HOME=/Users/charles python3 /Users/charles/.hermes/scripts/brainctl.py --json brains validate` returned `passed: true`, confirming the external-control brain registry/runtime wiring remains valid after the S3 gate landing.

## Blockers / Confusions

- None.

## Final Handoff

- Status: done. The X2D `start_print` confirmation/idempotency/audit gate is verified and its test harness is now reproducible inside kanban-worker profile sandboxes.
- Evidence: `/Users/charles/.hermes/scripts/external_control_gate.py`, `/Users/charles/.hermes/scripts/test_external_control_gate.py`, `python3 /Users/charles/.hermes/scripts/test_external_control_gate.py` => `OK 4 tests`, `HOME=/Users/charles python3 /Users/charles/.hermes/scripts/brainctl.py --json brains validate` => `passed: true`.
- Residual risk: `brainctl.py` still derives its default root from `HOME`, so worker/profile sandboxes must continue to set `HOME=/Users/charles` (or equivalent explicit rooting) until the CLI itself is made profile-agnostic.

- 2026-05-21T01:44:12+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`.

- 2026-05-21T01:44:12+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Evidence: file:/Users/charles/.hermes/scripts/external_control_gate.py

- 2026-05-21T01:44:12+08:00: Lifecycle transition `running` -> `review` by `hermes`. Evidence: file:/Users/charles/.hermes/scripts/external_control_gate.py, file:/Users/charles/.hermes/scripts/test_external_control_gate.py, command:python3 ~/.hermes/scripts/test_external_control_gate.py => OK 4 tests, command:python3 ~/.hermes/scripts/brainctl.py --json brains validate => passed true
