# Taskpool bounded drain continuation patterns

Use this reference when a taskpool drain loop completes with `MAX_CYCLES_REACHED` while the user still wants safe progression toward normal flow or full completion.

## MAX_CYCLES is a handoff, not completion

A bounded loop ending with `MAX_CYCLES_REACHED` means the watch window expired. Do not report the loop's final JSON as the only truth. Immediately re-read live state:

- `python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json`
- `python3 ~/.hermes/scripts/agent_team_controller.py worker-jobs --json`
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-jobs --json` when multimodel may be involved
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`

The live task statuses may differ from the loop's last line because workers can finish, claims can expire, and retry gates can mature after the loop wrote its final JSON.

## Safe continuation sequence

Run one bounded foreground recovery pass before starting the next background loop:

1. `auto-close-review --max-tasks 1000 --authority autonomous-execution --json`
2. `reconcile --write --promote-due-retry --actor safe-pending-child-targeted-repair --json`
3. `auto-subtask-sync --write --actor safe-pending-child-targeted-repair --json`
4. `blocked-resolve-step --max-tasks 1000 --authority autonomous-execution --actor safe-pending-child-targeted-repair --force --retry-delay-minutes 10 --json`
5. `review-gap-scan --max-tasks 300 --write --actor targeted-evidence-repair --json`
6. `parallel-dispatch-dry-run --max-agents 8 --lane all --json`
7. If tasks are selected, `parallel-claim-and-handoff --write ...` then `agent_team_controller.py consume-claimed --background`.

## Human escape guard recovery

If `consume-claimed --background` returns `status=SKIP` with a Human escape reason and releases claims:

1. Run `taskpool_escape_guard.py --json`.
2. Inspect `classification.post_ack_terminal_count`, `classification.worker_timeout_count`, `escape_info.since_ack`, and the terminal rows.
3. If the rows are stale terminal/failed worker envelopes and no live worker jobs exist, ack explicitly:
   `taskpool_escape_guard.py --ack-reviewed --reason '<operator reviewed stale terminal rows; preserve proof/lifecycle gates and resume autorun>' --json`
4. Read back `taskpool_escape_guard.py --json` and require `human_escape_triggered=false` before reclaiming.
5. Re-run claim/consume; do not use `--force` on claims unless a separate live-worker review proves the owner is stale.

## Orphaned active and blocked health

- If a task is `running` or `claimed` and appears in a live worker job, do not release it or mark it done.
- If a task is active but worker registry/process liveness is empty, let canonical `reconcile --write` requeue/retry it; do not manually set done.
- `blocked=0` is a flow-health target, not a permission to bypass evidence gates. Use `blocked-resolve-step` to release transient blocked items to retry/targeted repair or resolve ready evidence to review.
- A parent waiting on child evidence should be flow-normalized away from `blocked`, but still protected from dispatch until the child evidence is ready.

## Starting the next bounded loop

After a recovery pass, start the next loop with completion notification:

```bash
TASKPOOL_DRAIN_MAX_CYCLES=12 \
TASKPOOL_DRAIN_SLEEP_SECONDS=300 \
TASKPOOL_DRAIN_MAX_AGENTS=8 \
TASKPOOL_DRAIN_ACTOR=safe-pending-child-targeted-repair \
python3 /tmp/taskpool_full_drain_loop.py | tee /tmp/taskpool_full_drain_loop_safe<N>.log
```

Use the terminal tool with `background=true` and `notify_on_complete=true`. Report the new session id and log path.
