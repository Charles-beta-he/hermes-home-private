# Retry-first drain and dispatch pattern

Use when the user asks to clear or prioritize `retry` tasks in the local brain/taskpool.

## Landing-zone classification

This is a reusable control-plane procedure and verification checklist. It is not a record of one session's task progress.

## Procedure

1. Snapshot retry and active state first.
   - Read `brain_task_orchestrator.py list --json` and summarize counts by status.
   - List `retry` task ids/titles/lanes/projects, plus all `claimed`/`running` tasks with `claimed_by`, `claim_expires_at`, and `stale_claim`.
   - Read `agent_team_controller.py worker-jobs --json` to see whether claimed/running tasks have live worker coverage.

2. Do not force-close retry tasks.
   - `retry` means the task needs governed re-entry, not a permission to mark done.
   - Preserve lifecycle/proof/multimodel gates; workers may produce proof or block, but only the controller can close.

3. Promote due retry via reconcile before claiming.
   - Dry-run or readback first when the pool state is unclear.
   - Then use governed reconcile with `--write --promote-due-retry` when safe.
   - Treat parent/child progress sync as useful housekeeping, not proof of completion.

4. Dispatch only through governed autorun/handoff.
   - Use `brain_task_dispatch_tick.py --summary --print-always --parallel-autorun ...` when dispatch reports selectable work.
   - If dispatch reports `wait_for_running_or_claimed_completion`, stop claiming and wait/poll; forcing more claims creates duplicate work and boundary pressure.
   - If dispatch reports boundary conflicts, prefer boundary/refinement or batch-merge planner rather than manual status edits.

5. Repair uncovered claimed tasks.
   - If a task is `claimed` but has no live worker and no matching handoff, release it to `retry` or `pending` with an explicit reason using the orchestrator release path.
   - If a task is `claimed` and has a handoff but no live worker, start `agent_team_controller.py consume-claimed --claimed-json ...` for that exact handoff instead of re-claiming it.
   - Verify worker creation with `worker-jobs --json` and process table readback.

6. After workers finish, run the gate-maintenance loop.
   - `blocked-resolve-step`
   - `review-gap-scan`
   - `auto-close-review`
   - a fresh dispatch tick
   Each step must be bounded and followed by list/selfcheck/dispatch readback.

## Pitfalls

- A lower retry count alone is not success; retry tasks may legitimately move to running, review, blocked, or pending depending on proof output.
- Review-gap scans can be long-running when they spawn repair/certification work. Prefer bounded max-tasks and fresh readback; do not treat a timeout as evidence of failure if worker processes are still alive.
- Do not use shell pipelines that combine a producing command with `python - <<'PY'`; the heredoc occupies stdin and can cause empty JSON reads/BrokenPipe. Use `execute_code` with `subprocess.run(..., stdout=PIPE)` or write to a temp file before parsing.
- Do not call a task complete from worker self-report alone. Read back task status, proof artifacts, selfcheck, dispatch, and stale-claim state.

## Verification checklist

- `brain_task_orchestrator.py selfcheck --json` returns PASS.
- `brain_task_dispatch_tick.py --summary --print-always --no-state` returns OK.
- `stale_claim_reclaim.candidate_count == 0` or reclaimed candidates are explicitly reported.
- `worker-jobs --json` matches expected alive/completed workers.
- Status counts explain where retry tasks went: running/review/blocked/pending/done, not just a raw delta.
