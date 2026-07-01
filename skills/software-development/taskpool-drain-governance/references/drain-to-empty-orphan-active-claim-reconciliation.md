# Orphan active claim reconciliation during drain

This reference captures the reusable recovery pattern for a taskpool drain where `claimed`/`running` tasks remain after their workers have exited and keep the active ceiling blocked.

## Trigger

Use when all are true:

1. The drain loop is otherwise safe and local.
2. `list --json` shows `claimed` or `running` rows.
3. `worker-jobs --json` shows no live worker for the relevant batch/task, or `alive_count: 0` overall.
4. `multimodel-intervention-jobs --json` shows no live multimodel job for the task when relevant.
5. `ps` has no matching process for the task/run/batch.

Suggested `ps` pattern:

```bash
ps -axo pid,etime,stat,command | egrep 'agent_team_controller.py|team-worker|hermes -p|multimodel_intervention|brain_task_orchestrator.py multimodel|brain_task_orchestrator.py transition|parallel-claim-and-handoff' | grep -v egrep || true
```

## Action

Release only to `retry` or `pending`.

Task frontmatter should record:

- cleared `claimed_by`, `claim_expires_at`, `run_id`;
- incremented `retry_count` if using `retry`;
- a short `next_attempt_at` backoff;
- `orphaned_active_reconciled_at`;
- `orphaned_active_reconcile_reason`;
- evidence such as `command:orphaned_active_claim_reconcile_worker_jobs_0_mm_jobs_0_ps_empty`.

## Anti-conditions

Do not reconcile if any worker/multimodel/transition/proof-check/parallel-claim process is still alive.

Do not mark the task `done` from this path. Orphan reconciliation only frees the scheduler to retry or re-dispatch; it is not acceptance evidence.

## Post-reconcile loop

Run:

1. `auto-close-review`
2. `auto-subtask-sync --write`
3. `blocked-resolve-step`
4. `list --json`
5. `selfcheck --json`

If the same rows repeatedly orphan, the durable fix belongs in canonical reconcile/dispatch code, not manual one-off mutation.
