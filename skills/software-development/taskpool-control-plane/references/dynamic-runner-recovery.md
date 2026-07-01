# Dynamic runner recovery after human-escape / slow probe

Applicability: Hermes local taskpool dynamic runner, especially `taskpool_dynamic_runner.py` + `brain_task_dispatch_tick.py --parallel-autorun` when the runner reports no claim even though boundary-check says tasks are dispatchable.

Anti-conditions: do not apply this as a generic rule for all cron failures; do not ack human-escape without explicit user/operator authorization and readback evidence; do not bypass proof/lifecycle/multimodel gates.

## Recovery sequence

1. Read the escape breaker first:
   `python3 ~/.hermes/scripts/taskpool_escape_guard.py --json`

2. If `human_escape_triggered=true`, inspect `post_ack_terminal_count`, `worker_timeout_count`, `timeouts_now`, and listed terminal rows.
   - If `timeouts_now>0`, stop and diagnose live workers.
   - If rows are stale terminal envelopes and the user/operator explicitly authorizes recovery, ack them:
     `python3 ~/.hermes/scripts/taskpool_escape_guard.py --ack-reviewed --reason '<review receipt>' --json`
   - Immediately read back and require `human_escape_triggered=false`, `post_ack_terminal_count=0`, `worker_timeout_count=0`.

3. Check dispatch gates:
   `python3 ~/.hermes/scripts/brain_task_orchestrator.py boundary-check --json`
   Require `status=PASS`, kill switches false, and expected lane availability.

4. If dynamic runner still reports no claim, inspect the dynamic runner log/state:
   - `~/.hermes/logs/taskpool_dynamic_runner.jsonl`
   - `~/.hermes/state/taskpool_dynamic_runner.json`
   - `~/.hermes/state/taskpool_dynamic_runner.pid`

5. Slow probe pitfall: `parallel-dispatch-dry-run --max-agents N --json` may take several minutes on large pools. If the dynamic runner log shows `parallel_cap_probe.returncode="timeout"` or `reason="probe_unavailable"`, time the dry-run manually before changing policy. The durable fix is to give the probe enough timeout (default 300s or `HERMES_TASKPOOL_PARALLEL_PROBE_TIMEOUT`), not to bypass boundary classification.

6. After a successful runner attempt, verify real mutation by reading the canonical task note, not just stdout. Look for lifecycle transitions such as pending -> claimed -> running -> review and structured `evidence:` frontmatter / Proof Log entries.

7. Clean up only stale runner locks/processes created by the recovery attempt:
   - remove `taskpool_dynamic_runner.pid` only if the PID is absent;
   - terminate orphan `brain_task_dispatch_tick.py --summary --parallel-autorun` only after verifying it is from the test/recovery slice and not an active worker the user wants to keep.

## Verification checklist

- `taskpool_escape_guard.py --json` shows no active human escape.
- `boundary-check --json` remains PASS.
- Dynamic runner lock is absent or points to a live expected process.
- No recovery-created orphan dynamic/tick process remains.
- At least one canonical task note or runner log confirms actual progress, or the no-op reason is explicit and safe.
