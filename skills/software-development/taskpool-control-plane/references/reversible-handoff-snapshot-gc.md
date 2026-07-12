# Reversible Handoff and Snapshot GC for A+ Control-Plane Closure

Use when taskpool/selfcheck is otherwise healthy but warns about handoff backlog, snapshot bloat, or maintenance cron drift.

## Principles

- Prefer no-agent deterministic scripts for routine maintenance. Provider-dependent prompt jobs are fragile for GC/health tasks.
- Archive or move; do not delete. Every GC action should leave a manifest with source path, destination path, count, and hash/receipt where practical.
- Dry-run first, then apply, then run the same selfcheck that produced the warning.
- Keep safety boundaries explicit: local artifact archival is not task lifecycle mutation, external dispatch, deployment, or credential access.

## Handoff backlog pattern

1. Inspect the backlog count from selfcheck or the handoff GC report.
2. Run `handoff-gc.py --archive --keep-newest <N>` as a plan.
3. If the plan is reasonable, run `handoff-gc.py --archive --apply --keep-newest <N>`.
4. Record manifest paths for each moved directory.
5. Re-run `brain_task_orchestrator.py selfcheck --json`; closure requires `status=PASS`, `failures=[]`, and no handoff warning.

A practical default for Hermes local taskpool is `keep-newest 80`, but treat this as a policy knob, not a universal constant.

## Snapshot/evolve log cron pattern

- Replace prompt-only maintenance crons with `no_agent=True` scripts when the output can be a deterministic JSON receipt.
- For snapshots: move old files into a quarantine/archive directory rather than deleting them.
- For append-only logs such as `evolve.log`: copy to a timestamped/monthly archive before truncating, and only truncate after successful copy.
- Cron success should be based on script exit code and receipt, not an LLM summary.

## Pitfalls

- Do not treat backlog cleanup as permission to alter task lifecycle state.
- Do not hide historical proof/hash debt by deleting evidence; classify it separately and create a burn-down plan if needed.
- Do not mark a timeout-prone model consult as hard-failed maintenance if the accepted behavior is bounded degradation; make the wrapper exit and status semantics explicit.
