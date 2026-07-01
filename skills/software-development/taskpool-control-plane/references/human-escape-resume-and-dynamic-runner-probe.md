# Human-escape resume and dynamic-runner probe pitfalls

Use this reference when recovering Hermes/local-brain taskpool auto-advance after `human_escape_active_preclaim`, worker-timeout envelopes, or dynamic runner no-op behavior.

## Landing-zone classification

- Reusable procedure / debugging path: belongs in `taskpool-control-plane`.
- Task IDs, commit hashes, concrete Product Hunt task details: session-specific evidence only; do not promote to global rules.
- User authorization receipts: task/ledger evidence, not durable memory.

## Resume verification after human-escape ack

When the user explicitly authorizes resuming auto-advance:

1. Ack only reviewed stale terminal rows:
   ```bash
   python3 ~/.hermes/scripts/taskpool_escape_guard.py \
     --ack-reviewed \
     --reason '<review receipt>' \
     --json
   ```
2. Immediately read back:
   ```bash
   python3 ~/.hermes/scripts/taskpool_escape_guard.py --json
   ```
   Require:
   - `human_escape_triggered=false`
   - `post_ack_terminal_count=0`
   - `worker_timeout_count=0`
   - `timeouts_now=0`
3. Run a read-only boundary check before write ticks. Confirm kill switches are absent, autorun is enabled, and the active lane policy matches the intended supply.
4. Wake the executor/dynamic runner once, then verify by reading canonical task notes and runner state/logs. Silent runner output is not proof; read back state.
5. If a lifecycle/autoclose command times out, inspect the canonical task note before retrying. It may have already mutated status/evidence. Continue from observed state, not from the timeout assumption.

## Dynamic runner probe timeout pitfall

`taskpool_dynamic_runner.py` may call:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents N --json
```

On large taskpools this can take several minutes. If the runner's probe timeout is too short, it may log `probe_unavailable`, skip autorun, and leave a stale lock if the outer process is killed.

Recovery / hardening pattern:

1. Measure the dry-run once with a generous timeout before changing policy.
2. Prefer a configurable timeout such as `HERMES_TASKPOOL_PARALLEL_PROBE_TIMEOUT` over a hard-coded short value.
3. After killing a timed-out runner, remove `~/.hermes/state/taskpool_dynamic_runner.pid` only if the recorded PID is no longer alive:
   ```bash
   pidfile=~/.hermes/state/taskpool_dynamic_runner.pid
   pid=$(cat "$pidfile" 2>/dev/null || true)
   if [ -n "$pid" ] && ! ps -p "$pid" >/dev/null 2>&1; then
     rm -f "$pidfile"
   fi
   ```
4. Re-run `py_compile` or focused runner tests.
5. Execute one live runner tick and verify via task-note readback or runner JSONL state.

## Multimodel review boundary

For tasks with `requires_multimodel: true`, deterministic implementation proof is not enough for `done`. If implementation/test evidence is complete but T3 certification fails or returns `CONTINUE_LOOP`, leave the task in `review` or requeue per the orchestrator's normal gate. Do not force `done`; record the certification artifact and failure taxonomy instead.

## Anti-conditions

Do not generalize these as permanent claims that tools are broken:

- a one-time dry-run timeout;
- transient orphan processes;
- provider/model parse failures;
- a specific task's certification failure.

Capture the recovery pattern, not the transient failure narrative.
