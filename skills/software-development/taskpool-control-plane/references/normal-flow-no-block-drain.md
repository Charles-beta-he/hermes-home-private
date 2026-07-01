# Normal-flow no-block taskpool drain

Use this reference when the operator asks to restore taskpool normal flow, remove `blocked`, or reach multi-concurrency `running` without weakening evidence gates.

## Goal shape

Acceptance is not a narrative blocker report. Produce live readback that shows:
- `blocked_count=0`.
- Multiple real `running` tasks.
- Live `worker-jobs` entries with batch ids, pids, and task ids.
- `claimed_count=0` or claimed tasks backed by a just-started live worker.
- `python3 -m py_compile ~/.hermes/scripts/brain_task_orchestrator.py` PASS.
- `brain_task_orchestrator.py selfcheck --json` PASS with empty failures/warnings.

## Objective model

Before mutating lifecycle state, state the compact operational model:
- Success: no blocked records, safe multi-worker flow, proof gates intact.
- Non-goals: no force-done, no fake evidence, no bypass of human/credential/external/destructive gates.
- Evidence: `list --json`, `agent_team_controller.py worker-jobs --json`, `multimodel-intervention-jobs --json`, `selfcheck`.
- Chosen path: normalize controller-state blockers into pending/retry flow, then dispatch boundary-isolated tasks concurrently.

## Safe normalization pattern

1. Parents waiting on auto-subtask evidence may be moved out of `blocked` into `pending`, but only if dispatch eligibility still blocks parent execution until children are ready. In code terms: lifecycle display can flow, but `work_dispatch_blockers()` must keep the proof gate closed for `auto_subtask_open_children` / `auto_subtask_missing_children`.
2. Retry-cap, non-convergence, missing-certification, and stale taxonomy blockers can be released to `retry` flow for targeted repair/certification when the task is not truly waiting for human input. Preserve the blocker reason and evidence summary; do not mark `done`.
3. Use `blocked-resolve-step --authority autonomous-execution --actor flow-normalize --force --retry-delay-minutes <N> --json`, then inspect `resolved`, `kept_blocked`, and `errors`.
4. If a residue remains, run focused `blocked-resolve-step --task '<id>' ...` instead of blind broad loops.
5. After `blocked_count=0`, run `parallel-dispatch-dry-run --max-agents <N> --lane all --json` and inspect selected/skipped reasons. Boundary conflicts and capacity limits are acceptable; permission, proof, human, credential, or destructive gates are not.
6. To start real concurrency when dry-run is safe, run `parallel-claim-and-handoff --max-agents <N> --lane all --write --actor hermes-parallel --json`, then pass `claimed_tasks` to `agent_team_controller.py consume-claimed --claimed-json ... --max-agents <N> --batch-id <batch> --background`.
7. Verify with both task state and process/job state. `running_count` without a live job may be an orphan; `worker_alive_count` without task state readback is insufficient.

## Orphaned active claim reconciliation

If `claimed` or `running` exists but there is no matching `worker-jobs`, no `multimodel-intervention-jobs`, and no live process matching task id/run id, reconcile to retry/over_retry with an explicit receipt. Never silently force `done`.

## Hard anti-conditions

Do not normalize these into flow:
- Human input required.
- Credentials, payment, or secrets.
- External dispatch, broad fanout, publish/deploy/push, or destructive operations without exact authority and rollback/readback.
- Required browser proof, UI proof, FixtureKit proof, or API readback when not actually collected.
- Any state where normalization would allow parent execution before child evidence is ready.

## Final report checklist

Report live evidence, not intent:
- Counts: active, blocked, pending, retry, claimed, running, review.
- Blocked list is empty.
- Running task ids.
- Worker alive jobs with batch ids/pids/task ids.
- Multimodel alive jobs.
- `py_compile` and `selfcheck` output.
- Diff stat.
- Safety note: gates preserved; no force-done; no fake evidence.
