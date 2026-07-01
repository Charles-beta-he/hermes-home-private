# Taskpool long-drain recovery and stale-claim loop

Use this reference when a taskpool drain is being continued across repeated background `MAX_CYCLES_REACHED` notifications, especially with the default safe strategy: `safe-pending-child-targeted-repair` / “自动执行 pending child tasks + targeted evidence repair child”.

## Landing-zone classifier

- Reusable procedure: long-running drain loop readback, safe repair, dispatch, and verification sequence.
- Pitfall: `claimed` may exist without a live worker; do not force completion. Reconcile to retry/pending first.
- Pitfall: human escape guard may block consume because of post-ack terminal rows; inspect rows and only ack-reviewed stale terminal envelopes after explicit continuation authority.
- Not captured here: individual task IDs, project URLs, retry timestamps, or session progress.

## Recovery loop after a background drain finishes

When a background loop exits with `MAX_CYCLES_REACHED`, do not infer success from the loop summary alone. Immediately do fresh readback in the current slice:

1. Read live task counts with `brain_task_orchestrator.py list --json`.
2. Read worker registry with `agent_team_controller.py worker-jobs --json`.
3. Read multimodel jobs if relevant: `brain_task_orchestrator.py multimodel-intervention-jobs --json`.
4. Run `brain_task_orchestrator.py selfcheck --json`; require `PASS` before claiming healthy operation.
5. If `blocked > 0` or due retry exists, run the safe repair sequence:
   - `auto-close-review --max-tasks 1000 --authority autonomous-execution --json`
   - `reconcile --write --promote-due-retry --actor safe-pending-child-targeted-repair --json`
   - `auto-subtask-sync --write --actor safe-pending-child-targeted-repair --json`
   - `blocked-resolve-step --max-tasks 1000 --authority autonomous-execution --actor safe-pending-child-targeted-repair --force --retry-delay-minutes 10 --json`
   - `review-gap-scan --max-tasks 300 --write --actor targeted-evidence-repair --json`
   - `parallel-dispatch-dry-run --max-agents 8 --lane all --json`
6. If dry-run selects tasks, run `parallel-claim-and-handoff --max-agents 8 --lane all --write --actor hermes-parallel --json`, then pass `claimed_tasks` to `agent_team_controller.py consume-claimed --background`.
7. Sleep a short interval and re-read worker jobs + list counts. Report only what the fresh readback shows.
8. If work remains and no hard boundary exists, start the next bounded background loop with `notify_on_complete=true` and a new log path.

## Stale claim / no-live-worker pitfall

If `parallel-claim-and-handoff` fails with a message like “task already claimed by agent-team-controller until …” but `worker-jobs --json` shows no live job for that task:

1. Do not use `--force` first.
2. Run `reconcile --write --promote-due-retry --actor safe-pending-child-targeted-repair --json`.
3. Confirm an action such as `orphaned_active_claim_over_retry` appeared.
4. Re-run `blocked-resolve-step` if the released task or parent becomes blocked.
5. Dry-run and claim again only after fresh list readback shows no live claim conflict.

This preserves lifecycle/proof gates while unwedging stale state.

## Human escape guard pitfall

If `consume-claimed` returns `SKIP` with `Human escape`:

1. Run `taskpool_escape_guard.py --json`.
2. Inspect `post_ack_terminal_rows`, `worker_timeout_count`, `since_ack`, and whether the rows are stale terminal/failed envelopes rather than live process risk.
3. Confirm there are no live worker jobs for the affected tasks.
4. Only after explicit continuation authority, run `taskpool_escape_guard.py --ack-reviewed --reason '<review receipt>' --json`.
5. Read back with `taskpool_escape_guard.py --json` and require `human_escape_triggered=false` before retrying dispatch.

Do not globally disable the guard and do not mutate terminal envelopes.

## Verification checklist

- [ ] Fresh same-slice `list --json` counts recorded.
- [ ] Fresh same-slice worker registry recorded.
- [ ] `selfcheck --json` is `PASS`.
- [ ] Any `claimed` without live worker was reconciled, not forced done.
- [ ] Any escape guard ack has a readback showing `human_escape_triggered=false`.
- [ ] Final status distinguishes `blocked=0/running>0` from “all tasks complete”.
