# Taskpool acceleration loop

Use when the user asks to “推进任务池”, “加速任务池”, or otherwise wants real local-brain/taskpool progress rather than a read-only health report.

## Goal

Increase throughput while preserving lifecycle/proof gates. Acceleration means moving eligible tasks through governed states (`pending/blocked/retry -> claimed/running/review`), creating bounded repair tasks, syncing parent/child evidence, and producing merge/refinement manifests. It does **not** mean force-closing tasks or bypassing multimodel/truth gates.

## Safe sequence

1. Establish boundary and objective compactly.
   - Success: real task lifecycle or evidence/projection changes, plus fresh readback.
   - Hard constraints: no hand-edited `done`, no forged proof, no forced lifecycle closeout, no external side effects, no credential/payment/destructive work.

2. Read current state.
   - `brain_task_orchestrator.py selfcheck --json`
   - `brain_task_orchestrator.py list --json`
   - `brain_task_orchestrator.py dashboard --json`
   - `brain_task_dispatch_tick.py --summary --print-always --no-state`
   - `agent_team_controller.py worker-jobs --json`

3. Drain live/claimed work before opening more parallelism.
   - If worker jobs are alive or tasks are running with non-stale claims, let them finish or poll boundedly.
   - Do not reclaim non-stale `hermes-parallel`/`hermes-auto-evidence` claims.

4. Run governed local acceleration actions, in this order:
   - `auto-subtask-sync --write --actor hermes-accelerator --json`
   - `review-gap-scan --max-tasks N --authority autonomous-execution --write --json`
   - `blocked-resolve-step --max-tasks N --authority autonomous-execution --json`
   - `auto-close-review --max-tasks N --authority autonomous-execution --json`

5. Try dispatch/parallel only if gates allow it.
   - `brain_task_dispatch_tick.py --summary --print-always --parallel-autorun --max-agents N --review-close-max-tasks M`
   - If it reports `task already claimed`, treat it as correct fail-closed behavior, not a failure to override.
   - If it starts an async worker, poll `agent_team_controller.py worker-jobs --json` until `alive_count` returns to 0 or a bounded timeout is reached.

6. If dispatch says `boundary_refinement_or_batch_merge`, stop blind claiming and materialize the boundary work.
   - Check/write batch merge manifests under `~/.hermes/state/taskpool-batch-merge-plans/`.
   - Treat manifests as propose-only unless a separate exact approval exists.
   - Report the top conflict groups and sample task IDs; do not execute merged work from a manifest without proving per-task acceptance compatibility.

7. Verify with fresh readback before reporting.
   - status counts, running/claimed/review IDs, stale-claim count, worker `alive_count`, selfcheck status, dispatch action, auto-close counts.

## Interpretation rules

- `worker_result: done` from `agent_team_controller` is not taskpool `done`; workers can only produce proof and move to review/blocked/retry. Only certified controller closeout may perform `review -> done`.
- `conductor_not_certified` means the task may have real worker proof but cannot close; report it as review/blocked evidence, not completion.
- `closed_count: 0` with skipped gate failures is a healthy fail-closed result when evidence is missing.
- `multimodel_passed: 0` prevents completion/certification claims even if deterministic evidence exists.
- `parallel_boundary_conflict` with resource headroom means the bottleneck is boundary/merge planning, not compute capacity.

## Reporting format

Keep the report compact and evidence-bound:

- What actually changed: lifecycle transitions, repair tasks created, manifests written, workers completed.
- Current counts and live work.
- Gates that correctly refused progress.
- The smallest next boundary: e.g. browser/API proof gap, multimodel certification, or merge planner approval.

Avoid long raw JSON dumps unless debugging a tool. Summarize counts and cite paths/commands.
