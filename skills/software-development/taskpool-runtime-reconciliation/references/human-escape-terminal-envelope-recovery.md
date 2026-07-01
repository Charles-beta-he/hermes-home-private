# Human-escape terminal-envelope recovery

Use this when a taskpool drain/assist run is interrupted by post-ack terminal envelopes, worker timeouts, or claimed rows with no visible worker.

## Goal

Resume bounded assist/drain without weakening proof, lifecycle, or multimodel gates.

## Review sequence

1. Read guard state:
   - `python3 ~/.hermes/scripts/taskpool_escape_guard.py --json`
   - Capture `human_escape_triggered`, `post_ack_terminal_count`, `worker_timeout_count`, `since_ack`, and `post_ack_terminal_rows`.
2. Read live owners:
   - `agent_team_controller.py worker-jobs --json`
   - `brain_task_orchestrator.py multimodel-intervention-jobs --json`
   - process text for `agent_team_controller`, `team-worker`, `hermes -p`, `consult_models`, `consume-claimed`, and the exact task id / run id.
3. Read canonical task rows:
   - `brain_task_orchestrator.py list --json`
   - Check that each terminal envelope’s task is now `retry`, `blocked`, or otherwise safely non-active.
4. Inspect latest worker logs under `~/.hermes/logs/taskpool-workers/` for the batch/job id. Confirm the controller recorded a lifecycle transition such as `running -> retry` or `running -> blocked`.

## When to ack

Ack only if all are true:

- `human_escape_triggered=true` or the guard is explicitly blocking dispatch.
- The terminal rows were reviewed.
- No live worker/multimodel/process owner remains.
- The mapped brain tasks are not being marked done; they are in retry/blocked/pending or have a normal lifecycle record explaining their state.

Command shape:

```bash
python3 ~/.hermes/scripts/taskpool_escape_guard.py \
  --ack-reviewed \
  --reason '<review receipt: terminal rows mapped to retry/blocked, no live owner, preserve gates>' \
  --json
```

Then immediately read back `human_escape_triggered=false` before dispatching.

## If post_ack_terminal_count remains but human_escape is false

Treat it as a warning, not a hard stop. Some rows can be historical or classified as suspicious timeout/timestamp issues while the breaker remains open. Continue only bounded safe steps (`blocked-resolve-step`, readbacks, no completion) and report the residual row.

## Handoff-only claimed rows

A task can be `claimed` with a `parallel_handoffs/*.md` file but no live owner. Before releasing:

- Check `worker-jobs alive_count=0` or no job for that task/batch.
- Check no taskpool-worker log exists for the batch, or the log ended without ownership.
- Check process text for the exact `run_id` and task id.
- Check multimodel jobs are not alive for the task.

If the normal release is rejected due to actor mismatch (`claimed by hermes-parallel`), use `--force` only with an evidence-rich reason and release to `retry`, never to `done`:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py release '<task_id>' \
  --to-status retry \
  --actor hermes-assist-continue \
  --force \
  --reason 'force_release_orphaned_parallel_handoff_no_live_owner: worker-jobs alive=0, no matching process owner, no worker log; release to retry only, no completion' \
  --json
```

## Race caution

Dynamic runners can claim new work while you are reconciling. If a new `agent_team_controller.py cycle` or `consume-claimed` process appears, wait for it to exit and re-read before force-releasing anything.

## Anti-conditions

Do not ack or force-release when:

- A live worker/job/process owns the task.
- The task id appears in a live multimodel async job.
- The terminal envelope is the only evidence and canonical task state has not been read back.
- The intended action would mark done/review without normal proof/certification.
