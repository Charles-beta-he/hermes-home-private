# Long taskpool drain loop: safe pending-child + targeted repair

Use this reference when the user asks to keep draining the Hermes taskpool until no executable work remains.

## Loop shape

Run bounded cycles instead of one-off snapshots:

1. `auto-close-review --max-tasks 1000 --authority autonomous-execution --json`
2. `reconcile --write --promote-due-retry --actor safe-pending-child-targeted-repair --json`
3. `auto-subtask-sync --write --actor safe-pending-child-targeted-repair --json`
4. `blocked-resolve-step --max-tasks 1000 --authority autonomous-execution --actor safe-pending-child-targeted-repair --force --retry-delay-minutes 10 --json`
5. `review-gap-scan --max-tasks 300 --write --actor targeted-evidence-repair --json`
6. `parallel-dispatch-dry-run --max-agents 8 --lane all --json`
7. If selected tasks exist: `parallel-claim-and-handoff --max-agents 8 --lane all --write --actor hermes-parallel --json`, then `agent_team_controller.py consume-claimed ... --background`
8. Read back `list --json`, `agent_team_controller.py worker-jobs --json`, multimodel jobs if relevant, and `selfcheck --json`.

A reusable background harness can repeat the same loop with bounded `MAX_CYCLES`; `MAX_CYCLES_REACHED` is a tick boundary, not a completion signal.

## Safety strategy

Default safe strategy: automatically execute pending child tasks plus targeted evidence repair child tasks. This means:

- Release flow-normalized/temporary blocked items to retry, pending, or review via `blocked-resolve-step`.
- Preserve real verification gates: browser proof, UI proof, API readback, proof hashes, and lifecycle review gates.
- Do not mark orphaned claimed/running work as done. If no live worker exists, canonical `reconcile --write --promote-due-retry` may requeue/retry orphaned active claims.
- Do not fabricate proof. If evidence is unavailable, keep the task in retry/blocked/review with an explicit evidence gap.

## Readback interpretation

Always re-read live state after a loop output because worker registry and task status may diverge between the loop's final line and current truth.

Progress report fields:

- `active_total`
- counts by status
- `blocked` list and whether `kept_blocked_count` is nonzero
- `running`/`claimed` lists
- `worker_alive_count` and live batch/task ids
- `review` count/list
- `retry` count and nearest `next_attempt_at`
- `selfcheck` status/failures/warnings
- background loop session id/log when one is running

Interpretation rules:

- `blocked=0` with `running/claimed` or live workers: normal flow, not complete.
- `blocked=0`, no live workers, no selected tasks, and only future retry timestamps: retry backoff, not complete.
- `MAX_CYCLES_REACHED`: continue by taking a fresh snapshot, running one manual repair/dispatch pass, then starting the next bounded loop if the user asked for continuous draining.
- `claimed/running` with `worker_alive_count=0`: likely orphaned active claim; run reconcile and retry/requeue, never force done.
- `blocked` but `kept_blocked_count=0`: run blocked-resolve-step; these are usually transient flow-normalized waits.
- `blocked` with proof/browser/UI/API gates: treat as real hard boundary unless exact evidence/readback is produced.

## Human escape guard recovery

If consume/dispatch is skipped due to human escape guard:

1. Run `taskpool_escape_guard.py --json`.
2. Inspect post-ack terminal rows, worker timeouts, and `since_ack` counts.
3. If rows are stale/failed envelopes and the user has authorized continued safe drain, run `taskpool_escape_guard.py --ack-reviewed --reason '<receipt>' --json`.
4. Immediately re-read guard state and require `human_escape_triggered=false` before dispatch.

Do not encode the specific stale row ids as durable rules; the reusable lesson is the review-and-ack recovery procedure.
