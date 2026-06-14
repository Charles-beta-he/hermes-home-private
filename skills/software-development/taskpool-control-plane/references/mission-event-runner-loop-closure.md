# Mission event runner loop closure

Use this when a Mission/taskpool bridge appears to be event-driven but still only *shows* or *schedules* work instead of proving that the governed runner executed.

## Failure signature

- `taskpool_status_changed` or another actionable mission event creates `mission_flow_signals`.
- `hermes mission dispatch-events <mission_id>` reports a cron job was triggered / `next_run_at=now`.
- But no synchronous evidence exists that the existing cron scheduler actually ran the mission tick script, invoked the cron agent, and produced a stage report or handoff.
- Doctor may keep showing pending/stale signals even though the dashboard/projection looks wired.

## Correct closure pattern

1. Keep the default bridge safe: event hooks should append Mission ledger events and schedule already-installed cron jobs only. Do not execute agents inline from taskpool mutation hooks.
2. Add or use an explicit manual/recovery path such as:
   - `hermes mission dispatch-events <mission_id> --run-due --json`
3. The `--run-due` path should:
   - call `cron.jobs.trigger_job(job_id)` for matching mission cron jobs;
   - then call the governed scheduler once, synchronously: `cron.scheduler.tick(verbose=False, sync=True)`;
   - return runner read-back such as `runner.status=ran` and `runner.executed_jobs=N`.
4. Verify all layers, not just the CLI response:
   - cron job `last_run_at`, `last_status`, and latest output file under `~/.hermes/cron/output/<job_id>/`;
   - latest cron output contains the Mission Tick prompt and agent response;
   - mission ledger has `tick_prompt_created` and/or a real `stage_report` / `handoff` from the cron agent;
   - `hermes mission doctor <id> --json` shows `pending_flow_signals=0`, `stale_flow_signals=0`, and no open decisions unless intentionally blocked.

## Critical pitfall: stage reports must not self-trigger

Cron mission agents are instructed to end by writing `hermes mission stage-report ...`. If `stage_report` is itself an actionable flow event, every successful cron tick creates the next pending signal and can self-trigger indefinitely:

`tick -> stage_report -> flow signal -> trigger cron -> tick -> ...`

Treat `stage_report` as durable evidence/read-back only. It should appear in reports and dashboards, but it should not normally enqueue a fresh flow signal. Actionable events should be state transitions or external wake signals, for example `mission_enabled`, `mission_resumed`, `decision_recorded`, or scoped `taskpool_status_changed`.

## Control Tower projection guidance

Dashboard/Control Tower projections should remain read-only:

- `mission_flow_signals`: pending/stale counts, pending age, dispatched count, maintenance tick count, consumed count, consumed latency.
- `mission_taskpool_bridge`: recent `taskpool_status_changed` events and whether each has a pending bridge signal.

These panels read the Mission ledger only. They are not taskpool owners, mission owners, or executors.

## Verification bundle

A complete proof should include:

- focused pytest over Mission and Control Tower tests;
- `py_compile` for changed runtime modules;
- `git diff --check`;
- post-update/selfcheck guard if this is Hermes core work;
- live `--run-due` smoke with cron output read-back;
- a durable mission stage report with commit hashes and command evidence.
