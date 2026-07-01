# Taskpool status inspection checklist

Use this when the user asks to “检查任务池状态” or asks why local-brain/taskpool is stalled.

## Landing zone

Reusable debugging path and verification checklist for taskpool/control-plane status inspection. This is not a record of one taskpool run; apply it to future inspections.

## Checklist

For full-push / “并行全盘推进” execution, also see `references/taskpool-fullpush-timeout-boundaries.md` before running worker cycles; it covers retry-lane throttling, tracked execution, and timeout/authority boundaries.

1. Start with canonical control-plane health:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
   - Summarize PASS/FAIL plus hard warnings.

2. Inspect active work and dispatchability:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --json`
   - Report counts by `pending/claimed/running/review/blocked/done`.
   - Call out `dispatchable=0` separately from “system unhealthy”.

3. Check cron and runner liveness:
   - Find `local-brain-taskpool-auto-completer` in cron listing.
   - Report enabled/state, last_run_at, next_run_at, last_status, script, workdir.
   - Read `~/.hermes/state/taskpool_dynamic_runner.json`.
   - Read only the latest compact entries from `~/.hermes/logs/taskpool_dynamic_runner.jsonl`; do not load the whole JSONL log.

4. Distinguish common non-bug states:
   - Cron `last_status=ok` plus `human_escape.triggered=true` means the runner is doing a protective preclaim no-op: no claim and no autorun.
   - `dispatchable=false` with only `review/blocked` active tasks is idle by policy, not a claim bug.
   - `selfcheck=PASS` can coexist with proof/quality warnings that prevent scale-up or closure.

5. Safe probes:
   - `python3 ~/.hermes/scripts/taskpool_dynamic_runner.py` should print nothing on unchanged no-op.
   - `python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --print-always --no-state` exposes gates and scheduler decision.
   - Treat `proof-check` failures as quality/proof-gate signals, not necessarily cron failure.

6. Review tasks:
   - Use `python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-close-review --authority dry-run --json` to see whether a review task is closable.
   - Do not perform the real close when the user only asked for inspection.

## Final report shape

Separate the answer into:

- task inventory;
- dispatch/claim state;
- cron/runner state;
- human_escape/kill-switch gates;
- proof/quality gates;
- safe next actions.

## Anti-conditions

Do not save specific task IDs, proof hashes, timestamps, or one-run counts here. Those belong in the current answer or project/task artifacts, not durable skill instructions.
