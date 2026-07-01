# Drain-to-empty: orphan active claim reconciliation

Use when draining the local taskpool and `claimed`/`running` rows keep consuming the active ceiling after workers have actually exited.

## Trigger

During a governed drain loop (`auto-close-review -> auto-subtask-sync -> blocked-resolve-step -> dispatch/dynamic-runner -> readback`), stop treating active rows as live if all of these are true:

1. `agent_team_controller.py worker-jobs --json` reports `alive_count: 0` for the relevant worker class.
2. `brain_task_orchestrator.py multimodel-intervention-jobs --json` reports no live job for the task when `claimed_by` is `hermes-multimodel` or the task was spawned through multimodel intervention.
3. `ps` has no matching process for the task/run/batch, including `agent_team_controller.py`, `team-worker`, `hermes -p`, `multimodel_intervention`, `brain_task_orchestrator.py multimodel`, `transition`, or `parallel-claim-and-handoff`.
4. The claim is not merely still within a known live worker batch.

## Safe action

Release only to `retry` or `pending`; never mark `done` from orphan reconciliation.

Record evidence on the task, for example:

- `command:orphaned_active_claim_reconcile_worker_jobs_0_mm_jobs_0_ps_empty`

Recommended state mutation fields:

- `status: retry`
- clear `claimed_by`, `claim_expires_at`, `run_id`
- set `next_attempt_at` with a short backoff
- increment `retry_count`
- add `orphaned_active_reconciled_at`
- add `orphaned_active_reconcile_reason: no live worker job, multimodel job, or process; released to retry, not done`

## Anti-conditions

Do not reconcile if any matching worker, multimodel job, transition, proof-check, or parallel claim process is still alive. Wait and read back again.

Do not force `done` for tasks whose only proof is worker timeout, model agreement, stale claim state, or retry exhaustion.

Do not repeatedly immediate-dispatch the same retry rows if `next_attempt_at` is in the future; wait for retry due or explicitly run a governed retry promotion.

## Verification loop after reconciliation

1. Run `auto-close-review --max-tasks <N> --authority autonomous-execution --json`.
2. Run `auto-subtask-sync --write --actor <actor> --json`.
3. Run `blocked-resolve-step --max-tasks <N> --authority autonomous-execution --actor <actor> --json`.
4. Read `list --json` and confirm `claimed/running` no longer contain the orphaned task.
5. Confirm `selfcheck --json` remains PASS.

## Interpretation

If `blocked` increases after creating targeted evidence/narrowing children, do not assume regression. Classify the new blocks: an increase from `keep_blocked` to `await_auto_subtasks` can be progress because the parent is now waiting on real child evidence instead of being unsplittable.
