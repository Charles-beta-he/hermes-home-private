# Mission/control-plane resume verification

Use this reference when a governed control-plane workflow says it was "continued" or a UI shows an option was recorded, but the work appears stalled.

## Durable lesson

Clearing a human gate is not the same as advancing the system. Treat decision capture, executor wake-up, and read-back as three separate facts.

## Resume checklist

1. Inspect the canonical ledger first.
   - Board/status: current status, tick budget, open decision id, cron installed, next step.
   - Inbox/decision table: whether the human gate is still `open` or actually `answered`.
   - Signals/events: pending/stale signals and recent `tick_prompt_created` / `stage_report` events.
2. If a user-facing UI wrote only a local option record, do not assume it answered the canonical decision.
   - Record the answer through the mission/control-plane decision command/API that mutates the ledger.
   - Read the inbox again; expected result is zero open decisions for that gate.
3. If continuing requires more budget/cadence, ensure the user’s authorization is explicit and narrow.
   - Scope: allowed local actions, forbidden external side effects, and budget amount.
   - Make the change auditable: backup the ledger/state first if using a low-level repair path, and append a stage report explaining why.
4. Wake the executor, not just the ledger.
   - Dispatch pending signals if applicable.
   - Run the scheduled job or one-shot scheduler tick when the user asked to continue now.
   - Watch for prompt creation and real stage reports, not only a changed `next_run_at`.
5. If the mission tick exposes a downstream taskpool/reconcile gate, clear that gate through the canonical taskpool command before claiming the system can self-advance.
   - Typical pattern: `brain_task_orchestrator.py reconcile --write --json`, then `reconcile --promote-due-retry --write --json` if retry-due items exist.
   - Verify with `dispatch-dry-run --json` and `selfcheck --json`; expected evidence is `dispatchable: true` and selfcheck PASS or clearly scoped non-blocking warnings.
   - Treat oversized command JSON as an output-management issue; summarize the fields that prove state rather than pasting the whole task body.
6. Verify with read-back.
   - Board/status should show active/no open decision; if budget is exactly exhausted, record whether the next action is a budget-continuation gate rather than hiding it.
   - Cron/job state should show a fresh successful run or due next run.
   - Mission report should include a new evidence-backed stage report when the tick produced one.
   - If code changed, run focused tests and commit only scoped files.

## Pitfalls

- A dashboard button or option JSONL can be an operator projection, not the canonical decision ledger.
- `dispatch-events` or setting a job due may not by itself run the agent; use the scheduler/job run path and verify `last_run` or new mission events.
- `next_step: mission report` is often generic board output, not proof that no work remains. Check status, decisions, budget, and stage reports together.
- Stale flow signals are a warning to triage, not necessarily the immediate blocker when cron exists and the mission is active.
- Do not silently broaden scope from “continue” into push/deploy/delete/secrets/external delivery. Preserve the narrow authorization in the ledger evidence.
