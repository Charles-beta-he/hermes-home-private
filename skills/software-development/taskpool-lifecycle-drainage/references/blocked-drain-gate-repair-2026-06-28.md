# Blocked-drain gate repair pattern (2026-06-28)

Use this reference when Hermes brain/taskpool stalls with long-lived `blocked` and little/no `done` output after workers and review closeout appear healthy.

## Diagnostic ladder

1. Snapshot current state before mutating:
   - `brain_task_orchestrator.py list --json` counts by status.
   - `agent_team_controller.py worker-jobs --json` for alive jobs.
   - `brain_task_orchestrator.py selfcheck --json`.
   - `auto-close-review --json` and `blocked-resolve-step --json` with high `--max-tasks`.
2. Classify blocked by `blocked_resolve_last_action`:
   - `await_auto_subtasks`: parent correctly waits for child evidence.
   - `keep_blocked_missing_taxonomy_artifact`: use deterministic taxonomy fallback from `multimodel_last_failures` when possible.
   - `keep_blocked_transient_retry_cap`: retry cap is working; require targeted repair/certification.
   - `keep_blocked`: inspect explicit certification/proof failure.
3. Run the safe loop:
   - auto-close-review
   - auto-subtask-sync --write
   - blocked-resolve-step
   - dynamic runner / dispatch tick
   - worker-jobs readback

## Fix classes

### Advisory/UI/API false positives

Avoid substring implementation hints. Known traps:
- `FixtureKit` -> `fix`
- `capability` -> `API`
- `guidance` / metadata -> `UI`

Advisory tasks with `completion_gate=advisory-evidence-review-done` should close on deposited advisory evidence/report artifacts, not live UI/API implementation proof.

### Advisory multimodel over-gating

If advisory completion gate passes with target-bound evidence, do not re-trigger product-grade certification solely because historical multimodel fields are inconclusive. Keep work/product gates strict.

### Historical artifact pruning

If `tick-*/discussion_result.json` is gone but `multimodel_last_failures` still exists, derive taxonomy axes from local failures. Only keep `missing_taxonomy_artifact` when both artifact and local taxonomy are unavailable.

### Parent/child convergence

For `auto_subtask_kind=non_convergence_narrowing`:
- child closeout is narrowed brief + structured evidence;
- parent waits until all children are done;
- parent can reopen for certification refresh only after child aggregation is complete;
- T3 max-failure pause is a real human/targeted-evidence gate.

## Stop boundary

Do not claim blocked=0 without fresh counts. If remaining blocked are child waits, T3 pause, retry cap, explicit certification FAIL, or missing advisory artifacts, stop with DecisionPacket/ContinuationPacket instead of bypassing gates.
