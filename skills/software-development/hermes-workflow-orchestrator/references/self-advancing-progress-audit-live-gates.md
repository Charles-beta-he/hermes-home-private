# Self-advancing progress audit: live gates and interpretation

Use when the user asks to check the current progress of a self-advancing Hermes project, mission, or taskpool.

## Read-only audit sequence

1. Identify the Mission ID from `hermes mission board --json` when the user did not provide one.
2. Run mission checks with the ID:
   - `hermes mission doctor <mission_id> --json`
   - `hermes mission inbox --json`
   - `hermes mission signals <mission_id> --json`
3. Do not assume every mission subcommand supports `--json`. If `hermes mission report <mission_id> --json` rejects the flag, rerun or omit without treating the mission as unhealthy.
4. Check taskpool and workers together:
   - `brain_task_orchestrator.py list --json`
   - `brain_task_orchestrator.py next --json`
   - `brain_task_orchestrator.py dispatch-dry-run --json`
   - `brain_task_orchestrator.py proof-check --json`
   - `brain_task_orchestrator.py selfcheck --json`
   - `agent_team_controller.py worker-jobs --json`
   - multimodel async jobs where available.
5. Check cron state for the mission tick, taskpool auto-completer, follow-through/evidence loops, guardian, and any relevant health/check jobs.

## Interpretation rules

- `blocked_on_human` plus an open `mission inbox` decision is a real stop gate for the Mission, even if taskpool workers are still active.
- `pending_flow_signals` that are also stale indicate backlog/debt in the Mission event bridge, not necessarily dead execution. Report them separately from taskpool liveness.
- In `brain_task_orchestrator.py list --json`, active task rows may live under `rows`, not `tasks`. Count by `rows[].status` before saying the pool is empty.
- Claims can transition from `claimed` to `running` while you are auditing. Re-read the task list after checking worker-jobs before finalizing counts.
- `dispatch-dry-run` with `dispatchable=false` and message `Reconcile is required before dispatch` means new dispatch is gated by canonical task-note fixes, not that there is no work. The recovery path is `reconcile --write --json`, then `reconcile --promote-due-retry --write --json` if due retries remain, followed by `next`, `dispatch-dry-run`, and `selfcheck` readback.
- If live worker batches exist, do not immediately run write-mode reconcile or start duplicate dispatch unless the user asked for recovery. Report that current workers should finish or reach claim expiry first.
- Distinguish proof debt from hard failure: `proof-check status=PASS` with historical invalid autorun proof-hash warnings is quality debt, not a current dispatch blocker.

## Report shape

Use concise bullets:
- Mission status, tick budget, open decisions, next cron.
- Taskpool active counts, running/claimed/retry/pending, P1/P2 split, project split.
- Worker-job alive count and which task IDs are running.
- Dispatch gate status: dispatchable, reconcile_required, blocked_on_human, or normal next task.
- Cron health: last/next run for mission, auto-completer, follow-through, evidence/autoclose, guardian.
- Bottleneck ordering and exact safe next commands if the user asks to recover.

## Anti-conditions

- Do not mark a Mission healthy just because cron last_status is ok; inspect the mission ledger and open decisions.
- Do not claim taskpool is idle from `next=null` alone; inspect the accompanying message and worker-jobs.
- Do not auto-answer human decisions or perform write-mode reconcile when the user only requested a progress check.
