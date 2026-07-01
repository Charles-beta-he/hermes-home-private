# Drain-to-normal-flow mode

Use this reference when the operator asks to restore normal taskpool flow, eliminate `blocked`, or push until the pool is actively draining. Goal is not to force completion; goal is to keep proof-gated work moving through `pending` / `retry` / `claimed` / `running` while preserving completion gates.

## Objective model

Success criteria:
- `blocked_count=0` from a fresh `brain_task_orchestrator.py list --json` readback.
- Live concurrency exists when requested: fresh `agent_team_controller.py worker-jobs --json` shows live jobs and task ids.
- `py_compile` and `selfcheck --json` pass after code changes.
- No task is marked done without proof-gated evidence.

Non-goals:
- Do not fake evidence.
- Do not force parent tasks to `done` merely because they are flow-normalized.
- Do not reclaim `claimed` / `running` tasks while a real worker or multimodel process is alive.

## Operational loop

1. Snapshot state:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json`
   - `python3 ~/.hermes/scripts/agent_team_controller.py worker-jobs --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-jobs --json`
2. Run the canonical lifecycle pass:
   - `auto-close-review --max-tasks 1000 --authority autonomous-execution --json`
   - `reconcile --write --promote-due-retry --actor <actor> --json`
   - `auto-subtask-sync --write --actor <actor> --json`
   - `blocked-resolve-step --max-tasks 1000 --authority autonomous-execution --actor <actor> --force --retry-delay-minutes <N> --json`
3. If a parent is blocked only because it waits for narrowed child evidence, move it into flow (`pending`) and rely on dispatch blockers to prevent unsafe parent execution until child evidence is ready.
4. If retry-cap, loop-non-convergence, or certification debt remains, release to `retry` for targeted repair rather than parking indefinitely in `blocked`; completion gates remain closed.
5. Run `parallel-dispatch-dry-run --max-agents <N> --lane all --json` and inspect selected tasks.
6. If dry-run selects safe independent tasks and dynamic tick is too conservative, run:
   - `parallel-claim-and-handoff --max-agents <N> --lane all --write --actor hermes-parallel --json`
   - Then pass `claimed_tasks` to `agent_team_controller.py consume-claimed --claimed-json ... --max-agents <N> --batch-id <batch> --background`.
7. Wait for live workers, then repeat close/reconcile/sync/resolve/dispatch until active count is zero, only future retry backoff remains, or a true hard gate appears.

## Orphaned active claim handling

Canonical reconcile may release orphaned active claims only when evidence shows there is no live owner:
- `worker-jobs` has no live job for the task.
- `multimodel-intervention-jobs` has no live job for the task.
- Process readback does not show the task id or run id.

Action should be `retry` or `pending` with receipt evidence, not `done`.

## Pitfalls

- `blocked-resolve-step` can create a child and leave the parent `blocked` in the same pass. Rerun a focused `blocked-resolve-step --task <parent>` after child creation to convert the parent into flow-waiting.
- `auto-subtask-sync` may backfill ready parents into a paused/blocked-looking state; follow it immediately with blocked-resolve normalization.
- A live job registry can lag task frontmatter. Always use both task-list and worker-job readbacks before claiming no active work.
- Long-running drain loops may continue in the background, but final user-facing claims still require fresh same-slice readback.

## Verification packet

Before reporting success, include:
- `py_compile` result.
- `selfcheck` result.
- Counts: active_total, blocked, pending, retry, claimed, running, review.
- Worker jobs: alive_count, batch ids, task ids.
- Explicit distinction between “normal flow restored” and “all tasks completed.”
