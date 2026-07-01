# Long-running safe taskpool drain after MAX_CYCLES

Applicability: authorized taskpool drain/continuation sessions where the operator has asked to keep progressing safely with pending child tasks and targeted evidence repair children.

Do not treat a loop summary as final state. When a background drain loop ends with `MAX_CYCLES_REACHED`, immediately read live state again:
- `brain_task_orchestrator.py list --json`
- `agent_team_controller.py worker-jobs --json`
- `brain_task_orchestrator.py multimodel-intervention-jobs --json`
- `brain_task_orchestrator.py selfcheck --json`

Default safe drain sequence:
1. `auto-close-review --max-tasks 1000 --authority autonomous-execution --json`
2. `reconcile --write --promote-due-retry --actor safe-pending-child-targeted-repair --json`
3. `auto-subtask-sync --write --actor safe-pending-child-targeted-repair --json`
4. `blocked-resolve-step --max-tasks 1000 --authority autonomous-execution --actor safe-pending-child-targeted-repair --force --retry-delay-minutes 10 --json`
5. `review-gap-scan --max-tasks 300 --write --actor targeted-evidence-repair --json`
6. `parallel-dispatch-dry-run --max-agents 8 --lane all --json`
7. If selected tasks exist, `parallel-claim-and-handoff --max-agents 8 --lane all --write --actor hermes-parallel --json`, then `agent_team_controller.py consume-claimed ... --background`.
8. Wait briefly and verify `worker-jobs --json` plus pool counts.
9. If still active, start another bounded background drain loop with `notify_on_complete=true`.

Interpretation rules:
- `blocked=0` plus live workers means normal flow.
- `blocked=0`, no live workers, and `selected_count=0` means retry backoff window, not a hard boundary; keep a background loop waiting for retry due.
- `claimed` with `worker_alive_count=0` is suspect orphaned active state; run reconcile before any force action.
- Task status can lag worker registry. If a task id is present in a live worker job, do not force complete or destructively edit it; let the live worker finish, then reconcile.
- Human escape guard after a previous ack may block consume on stale terminal rows. Inspect `taskpool_escape_guard.py --json`; only use `--ack-reviewed` when rows are stale/failed envelopes, no live worker owns them, and proof/lifecycle gates stay intact.
- Never mark tasks done just to empty the pool. Preserve evidence/proof gates, API/browser/UI readback hard boundaries, and targeted evidence repair children.

Anti-conditions:
- Do not use this to bypass credentials, external adapter, publish/deploy, browser/UI proof, or payment gates.
- Do not turn project-specific task IDs or temporary retry times into durable rules.
