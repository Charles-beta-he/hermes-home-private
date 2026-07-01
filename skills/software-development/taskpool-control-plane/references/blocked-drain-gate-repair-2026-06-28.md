# Blocked-drain gate repair pattern (2026-06-28)

Use this reference when a Hermes brain/taskpool session stalls with long-lived `blocked` and no `done` output after review/auto-close appears healthy.

## Reusable diagnostic ladder

1. Snapshot current state before mutating:
   - `brain_task_orchestrator.py list --json` counts by status.
   - `agent_team_controller.py worker-jobs --json` for alive jobs.
   - `brain_task_orchestrator.py selfcheck --json`.
   - `auto-close-review --json` and `blocked-resolve-step --json` with high `--max-tasks`.
2. Classify blocked by `blocked_resolve_last_action`, not only status count:
   - `await_auto_subtasks`: parent is correctly waiting for child evidence; do not force parent done.
   - `keep_blocked_missing_taxonomy_artifact`: historical discussion artifact is missing; attempt deterministic taxonomy fallback from `multimodel_last_failures` before declaring human gate.
   - `keep_blocked_transient_retry_cap`: retry cap is working; require targeted evidence repair or certification, not blind retry.
   - `keep_blocked`: inspect certification/proof failure directly.
3. Treat review-close failures as a gate taxonomy problem:
   - `execution_flow_closeout_blocked:*` may be a false positive if advisory/evidence tasks mention UI/API/browser/contracts as source material rather than implementation scope.
   - `project-evidence-review-done` failures are usually real for work-lane implementation tasks; do not downgrade without explicit authority.
4. Run the safe reversible loop:
   - `auto-close-review`
   - `auto-subtask-sync --write`
   - `blocked-resolve-step`
   - `taskpool_dynamic_runner.py`
   - wait for workers/multimodel workers, then repeat.

## Pitfalls and fixes discovered

### Advisory/UI/API false positives

English substring regexes can strand advisory tasks:
- `FixtureKit` can match `fix`.
- `capability` can match `API`.
- metadata such as `guidance` / `required_authority` can match `UI`.

Fix class:
- Use word-boundary regexes for English implementation hints.
- Do not let advisory tasks with `completion_gate=advisory-evidence-review-done` require UI/API implementation readback; their gate is deposited advisory evidence/report artifacts.
- Keep project/work implementation closeout strict.

### Advisory multimodel over-gating

If advisory evidence gate already passes, do not re-trigger product-grade certification merely because historical multimodel fields are inconclusive. Advisory-only PASS/ratification can be sufficient for advisory closeout, but must remain target-bound and evidence-backed.

### Historical artifact pruning

Historical `tick-* / discussion_result.json` artifacts may be pruned while task frontmatter still has `multimodel_last_failures`. If failures produce deterministic taxonomy axes, auto-split can proceed from those local failures. Only emit `keep_blocked_missing_taxonomy_artifact` when both artifact and deterministic failure taxonomy are unavailable.

### Parent/child convergence

For `auto_subtask_kind=non_convergence_narrowing`:
- Child closeout is a narrowed brief + structured evidence, not full product implementation proof.
- Parent can reopen for certification refresh only after all child subtasks are done.
- If T3 rounds hit pause (`max=5`), stop at human/targeted evidence gate rather than loop.

## Stop boundary

Do not claim blocked=0 unless fresh counts prove it. If remaining blocked are child-evidence waits, T3 pause, retry cap, or explicit certification FAIL, produce a DecisionPacket/ContinuationPacket instead of bypassing gates.
