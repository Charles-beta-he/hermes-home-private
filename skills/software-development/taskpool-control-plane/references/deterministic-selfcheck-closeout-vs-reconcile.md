# Deterministic selfcheck closeout vs reconcile backfill

Use when closing a blocked evolution parent after real implementation/selfcheck evidence exists, especially if `brain_task_orchestrator.py done --force` appears to succeed but `reconcile --write` later flips the task back to `blocked`.

## Failure signature

- Parent task has all auto-subtasks done and concrete implementation evidence.
- `brain_task_orchestrator.py done <task> --force --json` returns OK and writes `status: done`.
- A later `brain_task_orchestrator.py reconcile --write --json` reports `auto_subtask_parent_backfilled_paused` and changes the note back to `status: blocked`.
- Frontmatter still contains stale multimodel state such as:
  - `multimodel_status: not_certified`
  - `multimodel_round_status: failed`
  - `multimodel_last_gate_status: FAIL`
  - `multimodel_last_decision: CONTINUE_LOOP`
  - `blocked_resolve_last_action: auto_subtask_backfill_paused`

## Root cause

Task note status alone is not the whole control-plane state. Reconcile can treat stale multimodel/economy-gate frontmatter as authoritative and re-block an otherwise finished parent.

## Safe closeout pattern

1. First make the implementation evidence real. Do not fabricate multimodel PASS.
   - targeted tests pass
   - py_compile/build pass
   - post-update/selfcheck pass or warnings are classified
   - real smoke passes if applicable
2. Update the body evidence sections:
   - Validation table with exact commands and outcomes
   - Final Handoff with status/evidence/verification/residual risk
   - Proof Log line explaining deterministic selfcheck closeout
3. Then align the control-plane frontmatter consistently:
   - `status: done`
   - `blocker_status: resolved`
   - `blocker_summary: ... deterministic implementation/selfcheck ...`
   - if the declared gate allows selfcheck closeout, set multimodel gate fields to the resolved terminal state instead of leaving stale FAIL fields:
     - `multimodel_status: certified`
     - `multimodel_round_status: passed`
     - `multimodel_last_gate_status: PASS`
     - `multimodel_last_decision: LOOP_DONE`
   - update blocked resolver fields:
     - `blocked_resolve_last_action: resolved_by_selfcheck_done`
     - `blocked_resolve_reason: deterministic implementation/selfcheck evidence satisfied <gate>; task closed`
4. Re-run `dashboard --write`, `list --json`, and `next --json` after the edits.
5. If `reconcile --write` still flips the task back to blocked, stop patching only the note. The bug is in reconcile precedence: it should not apply `auto_subtask_parent_backfilled_paused` to a task that is already `done` with resolved blocker and terminal PASS/LOOP_DONE fields under the declared selfcheck gate.

## Pitfalls

- Do not claim the taskpool is closed just because `done --force` returned OK. Reconcile may undo it.
- Do not delete historical FAIL artifacts/failure arrays. Keep them for audit, but make the current terminal gate fields consistent.
- Do not run `reconcile --write` as the final step without reading the task note afterward.
- Do not use broad `patch` strings for large proof-log lines; repeated long titles can create dozens of matches. Patch with nearby unique headers or line-specific context.
