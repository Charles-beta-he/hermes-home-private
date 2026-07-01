# Full taskpool drain flow normalization

Use when the user asks to push the taskpool to normal flow, zero `blocked`, or drain all executable work.

## Reusable loop

1. Read live state first: task counts, `worker-jobs --json`, `multimodel-intervention-jobs --json`, and selfcheck.
2. Repeat bounded cycles:
   - `auto-close-review --max-tasks 1000 --authority autonomous-execution --json`
   - `reconcile --write --promote-due-retry --actor <actor> --json`
   - `auto-subtask-sync --write --actor <actor> --json`
   - `blocked-resolve-step --max-tasks 1000 --authority autonomous-execution --actor <actor> --force --retry-delay-minutes 10 --json`
   - `parallel-dispatch-dry-run --max-agents 8 --lane all --json`
   - if selected, `parallel-claim-and-handoff --max-agents 8 --lane all --write --actor hermes-parallel --json`, then `agent_team_controller.py consume-claimed --claimed-json ... --background`.
3. Wait for live workers before reclaiming running/claimed rows. Re-check `worker-jobs` and process liveness before calling a claim orphaned.
4. Continue until either active rows are empty, or only hard gates remain (human/browser/API proof, credential/payment/external side effect, or true proof/certification boundary).

## Flow-normalization pitfall

Some parent tasks can appear `blocked` only because they are waiting for auto-generated child evidence or certification refresh. If the operator asks for normal taskpool flow, do not force these parents to `done` and do not fabricate evidence. Instead:

- move flow-wait parents to `pending` or retry-like flow with an explicit evidence note,
- add dispatch blockers so parents waiting for unfinished child evidence are not executed prematurely,
- let child tasks and targeted repair run,
- keep proof/certification gates intact.

## Orphaned active claim reconciliation

When `claimed`/`running` rows have no live worker job, no multimodel job, and no matching process text for the task/run id, `reconcile` may safely release them to `retry`/`over_retry` with evidence such as `command:reconcile_orphaned_active_claim_no_live_owner`. Never mark these rows `done`.

## Reporting standard

For drain requests, report latest verified counts and live jobs. Do not claim complete from old loop output: re-read current counts/jobs/selfcheck in the same slice. If workers are alive, state the live-worker boundary and continue or leave a bounded background drain loop with its session id/log path.
