# Parallel worker nested event-hook repair

## Applicability

Use this when Hermes taskpool appears healthy enough to dispatch, but parallel flow does not truly advance: examples include `parallel-claim-and-handoff` claiming work, `consume-claimed` starting, only one task reaching `running`, another task staying `claimed`/false-running, stale runner `ERROR` summaries, or dispatch ticks returning non-zero while no stale claim is reported.

This is for local taskpool/agent-team control-plane debugging. It is not a reason to bypass proof gates, force-close blocked parent tasks, or raise global concurrency beyond the scheduler's resource ceiling.

## Symptom pattern

- `selfcheck` can still be `PASS`.
- `brain_task_dispatch_tick.py --summary --print-always --no-state` may show no stale claims, but scheduler waits because active/running accounting is saturated.
- `taskpool_dynamic_runner.json` may contain a stale `last_summary.status: ERROR` until a later OK tick refreshes it.
- `ps` may reveal a worker-owned `agent_team_controller.py consume-claimed` process with child `brain_task_dispatch_tick.py --autorun-step` or nested transition processes.
- The bug is often not the task itself; it is a control-plane recursion/ownership issue.

## Diagnosis checklist

1. Read taskpool list JSON and count `pending`, `retry`, `claimed`, `running`, `blocked`, `review`.
2. Verify stale-claim state with dispatch dry-run / tick summary; do not assume every `running` row is live.
3. Cross-check active rows against process ownership: a real running task should have a matching live worker/conductor process or a clear external worker such as `consult_models.py run`.
4. Inspect recent taskpool-worker logs for a batch that started but did not emit a final JSON summary.
5. If a worker-owned lifecycle transition recursively starts taskpool event hooks, treat it as nested hook recursion, not as a business-task block.

## Durable fix pattern

Inside agent-team worker-owned lifecycle transitions, disable nested taskpool event hooks by passing an environment override only to the transition subprocess:

```python
transition_env = os.environ.copy()
transition_env.setdefault('HERMES_TASKPOOL_EVENT_HOOK_DISABLED', '1')
r = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=transition_env)
```

Keep this scoped to worker-owned transitions. Do not disable top-level cron/operator hooks globally; cron and manual operator transitions should keep normal hook behavior.

## Recovery sequence

1. Patch the worker transition path and add a regression test asserting `HERMES_TASKPOOL_EVENT_HOOK_DISABLED=1` is passed to the subprocess.
2. Run focused tests, e.g. `python3 ~/.hermes/scripts/test_agent_team_controller_safety.py`, and `py_compile` relevant scripts.
3. Kill only old pre-patch worker processes that no longer have valid ownership. Do not kill unrelated model/conductor processes.
4. Release false-running tasks back to `retry` using the claim owner/actor, with evidence that the old worker was pre-patch and dead/stuck.
5. Let the patched event-driven controller re-claim/consume work.
6. Verify:
   - `selfcheck: PASS`
   - dry tick `status: OK`, `error_count: 0`
   - stale claim candidate/reclaimed count is 0
   - runner state `last_summary.status: OK`
   - cron job `last_status: ok`
   - at least two active tasks are genuinely backed by live processes, or the scheduler explicitly reports `resource_ceiling_reached` at the configured ceiling.

## Anti-conditions

- Do not classify legitimate `blocked` parent tasks as system blockage when resolver says they are waiting for child tasks, missing taxonomy artifacts, or multi-model certification.
- Do not force `blocked -> retry` for proof-gated parents unless the resolver says the block is transient and authority permits it.
- Do not claim “no block exists” without distinguishing system-level block from task-level blocked status.
