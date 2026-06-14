# Taskpool → Mission flow bridge pattern

Scope: Hermes/local control-plane systems that have both a taskpool ledger and a separate long-running objective/Mission ledger.

Applicability: use when taskpool mutations should wake the long-running objective controller without giving the taskpool direct authority to execute, close, send, deploy, or mutate external adapters.

Anti-condition: do not use for ordinary project task queues, user-product workflows, external platform sends, arbitrary shell execution, production deploys, or broad taskpool-to-agent auto-execution. This pattern is a local-ledger wakeup bridge only.

## Pattern

1. Keep the objective/Mission layer as the durable objective ledger.
   - Add a local objective event type such as `taskpool_status_changed`.
   - Include it in the actionable flow-event set so it enqueues durable flow signals.
   - Let the objective store dispatch the already-installed scheduled runner by moving `next_run_at` to now.

2. Bridge from the taskpool event hook, not from arbitrary Markdown edits.
   - Hook candidates: `task_added`, `task_transitioned`, `task_dispatch_authorized`.
   - Return bridge status inside the existing event-hook payload, e.g. `event_hook.mission_bridge`.
   - Keep the bridge fail-soft: taskpool mutations must not fail merely because objective-ledger observability failed.

3. Scope aggressively.
   - Only bridge control-plane/self-architecture work.
   - Good filters: project/lane/architecture-target/brain metadata that marks local control-plane evolution rather than ordinary product delivery.
   - Provide an explicit target override env var for the objective id.
   - Provide a kill switch env var for the bridge.

4. Preserve event-governed boundaries.
   - The bridge appends a local objective event and schedules an existing runner only.
   - It must not execute the agent inline.
   - It must not mark tasks done/review by itself.
   - It must not send external messages, push/merge, deploy, delete, or write secrets.

## Verification checklist

- Unit: appending the taskpool-status objective event creates a pending flow-signal row bound to the source event id.
- Script compile: compile both objective-ledger code and the taskpool orchestrator script.
- Focused tests: objective/Mission tests and CLI tests pass.
- Temp HOME smoke: create an isolated objective DB and brain vault, run the taskpool add command for a scoped local-control-plane/evolution task with heavy dispatch disabled, then assert:
  - `event_hook.<bridge>.status == OK`
  - pending objective signals include the taskpool status event type
  - payload includes the task id.
- Live readback: after stage-report or bridge event, doctor/status shows pending/stale signals accurately; after the scheduled runner consumes them, pending/stale return to zero.

## Pitfalls

- Do not make the bridge broad enough to wake the long-running controller for every ordinary product task.
- Do not create a new daemon/worker pool for the bridge; scheduling the existing runner is the safe executor boundary.
- If a smoke test appears to read the wrong objective ledger, check the profile/home env var; generated scripts and CLI calls must agree on the same home.
- If stale signals remain after dispatching, remember dispatch only schedules the runner; the runner must execute to consume the signal.
