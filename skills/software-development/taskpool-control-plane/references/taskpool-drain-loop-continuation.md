# Taskpool drain loop continuation pattern

Use when a governed taskpool drain loop exits with `MAX_CYCLES_REACHED`, or when the pool oscillates between retry/pending/claimed/running while the user wants safe continued progress.

## Landing zone

This is a reusable taskpool-control-plane procedure, not a record of one session. It applies to governed taskpool drain/dispatch loops with proof/lifecycle gates.

## Continuation checklist after `MAX_CYCLES_REACHED`

Do not treat `MAX_CYCLES_REACHED` as completion. Read back live state before reporting progress:

1. `python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json`
2. `python3 ~/.hermes/scripts/agent_team_controller.py worker-jobs --json`
3. `python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-jobs --json` when multimodel jobs may be active.
4. `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`; continue only if `status=PASS` unless the task is explicitly to repair selfcheck.

Then run the safe cycle:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-close-review --max-tasks 1000 --authority autonomous-execution --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py reconcile --write --promote-due-retry --actor safe-pending-child-targeted-repair --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-subtask-sync --write --actor safe-pending-child-targeted-repair --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --max-tasks 1000 --authority autonomous-execution --actor safe-pending-child-targeted-repair --force --retry-delay-minutes 10 --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py review-gap-scan --max-tasks 300 --write --actor targeted-evidence-repair --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 8 --lane all --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-claim-and-handoff --max-agents 8 --lane all --write --actor hermes-parallel --json
python3 ~/.hermes/scripts/agent_team_controller.py consume-claimed --claimed-json '<claimed_tasks_json>' --max-agents 8 --batch-id '<batch_id>' --background
```

## Human escape / stale terminal rows

If `consume-claimed` returns `SKIP` with a human escape reason and releases claims:

1. Run `python3 ~/.hermes/scripts/taskpool_escape_guard.py --json`.
2. Verify there are no live worker jobs for the affected task ids.
3. If the rows are stale terminal/failed envelopes already reviewed by the operator, run:

```bash
python3 ~/.hermes/scripts/taskpool_escape_guard.py --ack-reviewed --reason '<operator-reviewed stale terminal rows; preserve proof/lifecycle gates and resume autorun>' --json
```

4. Read back `taskpool_escape_guard.py --json` and require `human_escape_triggered=false`, `since_ack.failures=0`, and `since_ack.blocks=0` before re-running claim/consume.

Do not force `done` to bypass the escape guard.

## Live-worker/status skew

If a task is `blocked` or `claimed` in task files but appears in `worker-jobs --json` under an alive job's `task_ids`, treat it as transient registry/status skew. Do not release or mark it done while the worker is alive.

If no live worker owns the task, use `blocked-resolve-step --force` or `reconcile --write --promote-due-retry` to move flow-normalizable blocks/orphans back to retry/pending for targeted repair.

## Reporting rule

Only claim taskpool normal-flow if the latest same-slice readback supports it, e.g. `blocked=0` plus live `worker_alive_count>0` or no due eligible work. Mention retry backoff separately; retry items with future `next_attempt_at` are not proof of completion.
