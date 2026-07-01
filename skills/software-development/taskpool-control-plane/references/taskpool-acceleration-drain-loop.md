# Taskpool acceleration drain loop

Use when the user asks to accelerate or fully push the local taskpool until tasks complete.

## Durable pattern

Acceleration is not the same as forcing completion. The safe target is to maximize governed throughput while preserving lifecycle/proof/multimodel gates. Stop only at a real boundary: all safe slots are occupied by non-stale running/claimed workers, dispatch returns `wait_for_running_or_claimed_completion`, review closeout is blocked by explicit evidence gaps, or certification/multimodel gates cannot pass.

## Sequence

1. Read current state: `list --json`, `selfcheck --json`, `brain_task_dispatch_tick.py --summary --print-always --no-state`, and `agent_team_controller.py worker-jobs --json`.
2. Run maintenance gates before claiming more work:
   - `auto-close-review --authority autonomous-execution --json`
   - `blocked-resolve-step --authority autonomous-execution --json`
   - `review-gap-scan --authority autonomous-execution --write --json`
   - `auto-subtask-sync --write --actor <actor> --json` when parent/child state may be stale.
3. If dispatch reports boundary conflict, run `brain_task_dispatch_tick.py --parallel-autorun ...` to materialize a batch-merge manifest. Treat the manifest as propose-only unless explicitly approved by policy/user; it does not itself execute work.
4. If a task is `claimed` but has no handoff path and no live worker coverage, release it through the governed command back to `retry` or `pending` with a precise reason, then let normal dispatch reclaim it. Do not use `--force` unless a fresh manual review proves the claim is invalid.
5. To use the batch executor/merge plan under explicit acceleration authority, set `HERMES_TASKPOOL_BATCH_EXECUTOR_APPROVED=1` for the tick command rather than editing config. The executor still only claims and hands off work; it must not mark tasks done.
6. When `parallel-claim-and-handoff` reports a claimed task but a generic `consume-claimed` skips, reconstruct explicit `--claimed-json` from readback/handoff fields and start `agent_team_controller.py consume-claimed --claimed-json ...` as a tracked background process.
7. Poll both worker jobs and canonical task state. Empty worker stdout is not failure; trust `worker-jobs`, `list --json`, and stale-claim readback.
8. When active workers fill the safe slots and dispatch says `wait_for_running_or_claimed_completion`, stop claiming and let workers drain. Continue only after running tasks transition to review/blocked/retry or stale-claim reclamation finds candidates.

## Verification evidence to report

- Status counts before/after.
- Which tasks moved claimed->running, running->review, or blocked/retry/pending.
- Worker job IDs and alive count.
- `selfcheck` result, stale-claim count, dispatch action, selected count, resource ceiling, skipped reasons.
- Auto-close closed/skipped counts and explicit missing evidence when skipped.

## Pitfalls

- `resource_ceiling` in the scheduler summary may be reduced by runtime policy even when max agents is larger; do not override it by starting unbounded workers.
- `boundary_refinement_or_batch_merge` is a throughput boundary, not an error. Generate/record merge manifests and use only governed claim/handoff paths.
- `auto-close-review` closing zero tasks is correct when it reports missing API/browser/command proof or certification not passed.
- Re-running broad ticks in foreground can exceed tool timeouts; prefer bounded ticks plus background worker tracking.
