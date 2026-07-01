# Taskpool running takeover and nested event-hook pitfall

Use when a taskpool appears healthy but active slots are occupied by running/review/claimed tasks, or when a manual takeover needs to keep the pool flowing without false completion.

## Reusable procedure

1. Read the live state first:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json`
   - `python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --print-always --no-state`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
   - `ps -eo pid,ppid,etime,stat,command | grep -E 'agent_team_controller|consult_models.py run|hermes .*team-worker' | grep -v grep`
2. If a task is `review`, do not let it occupy the active path indefinitely. Run review closeout through the gate:
   - Dry run: `python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-close-review --authority dry-run --max-tasks 10 --json`
   - Apply only the governed result: `python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-close-review --authority autonomous-execution --max-tasks 10 --actor <actor> --reason '<reason>' --json`
3. If certification is `certification_inconclusive`, `PASS_ADVISORY_ONLY`, `allowlist_miss`, or otherwise not PASS/LOOP_DONE, do not force `done`. Let the gate move/keep it as blocked/retry/review according to policy; this frees the slot without inventing completion.
4. When slots are available, let the scheduler select the next safe item rather than hand-picking unless the user gave an exact target:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-claim-and-handoff --max-agents <N> --write --actor <actor> --ttl-minutes 90 --json`
   - Pass `claimed_tasks` to `agent_team_controller.py consume-claimed --claimed-json ... --max-agents <N> --batch-id <id> --background`.
5. Read back after each claim/consume:
   - status counts and active tasks from `list --json`
   - scheduler action / active_count / resource_ceiling from dispatch tick
   - stale reclaim result; it should normally be `candidate_count: 0` and `reclaimed_count: 0` after takeover.

## Nested event-hook pitfall

Agent-team workers already own the follow-through loop from claimed -> running -> review/retry/blocked. If their internal lifecycle transitions trigger the taskpool event hook recursively, a parallel batch can serialize or hang before all claimed items enter `running`, producing misleading states such as one task running and another claimed/running without live worker ownership.

Implementation guard: worker-owned transition calls should set `HERMES_TASKPOOL_EVENT_HOOK_DISABLED=1` in the subprocess environment. Keep top-level operator transitions and cron dispatch paths hook-enabled; disable only nested worker-owned transitions.

Regression shape:
- Unit test `transition_task` or equivalent wrapper to assert subprocess env carries `HERMES_TASKPOOL_EVENT_HOOK_DISABLED=1` for worker-owned transitions.
- Run focused worker safety tests and `py_compile` after patching.
- Then prove live flow with `selfcheck PASS`, `dry_tick OK`, no stale claims, and multiple real `running` tasks with matching live worker processes.

## Anti-conditions

- Do not use this to bypass proof/certification gates or mark review tasks done directly.
- Do not kill or release active tasks unless readback shows no live worker ownership, a stale claim, expired lease, or a false-running pre-fix condition.
- Do not interpret task-level `blocked` as system-level blockage; inspect resolver reasons and child progress first.
