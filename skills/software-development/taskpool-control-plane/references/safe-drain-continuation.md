# Safe taskpool drain continuation after bounded loops

Use this reference when a long taskpool drain loop exits with `MAX_CYCLES_REACHED`, when the user asks to continue until the pool is healthy, or when `claimed`/`running` counts diverge from the live worker registry.

## Class-level procedure

1. Treat `MAX_CYCLES_REACHED` as a checkpoint, not success or failure.
2. Fresh readback before acting:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json`
   - `python3 ~/.hermes/scripts/agent_team_controller.py worker-jobs --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-jobs --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
3. If `worker_alive_count=0` but tasks remain `claimed` or `running`, run canonical reconcile:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py reconcile --write --promote-due-retry --actor safe-pending-child-targeted-repair --json`
   - Never mark orphaned active tasks `done` directly.
4. Apply the default safe drain sequence:
   - `auto-close-review --max-tasks 1000 --authority autonomous-execution --json`
   - `reconcile --write --promote-due-retry --actor safe-pending-child-targeted-repair --json`
   - `auto-subtask-sync --write --actor safe-pending-child-targeted-repair --json`
   - `blocked-resolve-step --max-tasks 1000 --authority autonomous-execution --actor safe-pending-child-targeted-repair --force --retry-delay-minutes 10 --json`
   - `review-gap-scan --max-tasks 300 --write --actor targeted-evidence-repair --json`
   - `parallel-dispatch-dry-run --max-agents 8 --lane all --json`
   - `parallel-claim-and-handoff --max-agents 8 --lane all --write --actor hermes-parallel --json`
   - `agent_team_controller.py consume-claimed --claimed-json ... --max-agents 8 --batch-id ... --background`
5. If `blocked` parents are only waiting on child evidence, normalize them back into pending/retry flow and let child/targeted-repair tasks run. Preserve proof, evidence, and multimodel gates.
6. If a real worker starts, report `batch_id`, `pid`, task ids, counts, and selfcheck status. Do not claim “全部执行完” while `active_total > 0` or any live worker/multimodel job remains.

## Default safe strategy

For advisory/social-intake/repair work, use this default unless the user narrows scope:

`自动执行 pending child tasks + targeted evidence repair child`

This authorizes bounded internal taskpool progression only. It does not authorize external login, credential entry, public publishing, platform bypass downloads, destructive operations, or fabricated evidence.

## Pitfalls

- Do not treat stale loop output as final state; always read live state after a background notification.
- Do not equate `claimed` with live execution; verify against `worker-jobs`.
- Do not clear `blocked` by weakening gates; move eligible tasks to retry/pending and create/execute repair children.
- Do not report taskpool completion when the actual state is healthy flow (`blocked=0`, live workers running) but `active_total` is still nonzero.
