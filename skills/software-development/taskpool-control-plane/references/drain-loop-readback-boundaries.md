# Governed drain loop readback boundaries

Applicability: user asks to continue/drain a Hermes taskpool after proof-check and selfcheck are already green, but live `taskpool_watch_report.py` still reports blocked/retry/pending items. Anti-condition: do not use this to force `done`, bypass multimodel certification, or repeatedly churn retry/blocked tasks.

## Procedure

1. Establish compact objective model:
   - success = remove stale control-plane blockers and expose next dispatchable work;
   - minimize false completion, retry churn, and proof debt hiding;
   - preserve lifecycle/proof/multimodel gates.
2. Read current state with `list --json`, `selfcheck --json`, `proof-check --json`, and watcher output.
3. If `next` or dispatch reports reconciliation required, run:
   - `reconcile --write --actor <drain-actor> --promote-due-retry --json`
   - read back `action_count`, status counts, and next/dispatchability.
4. Run one bounded blocked resolver pass:
   - `blocked-resolve-step --actor <drain-actor> --max-tasks <N> --authority dispatch-hint --json`
   - read back `checked/resolved/kept/errors` and the resulting status counts.
5. Run review close and a second reconcile pass if review items exist:
   - `auto-close-review ... --json`
   - `reconcile --write ... --json`
6. Re-read list/selfcheck/proof/watch. Stop if the same items cycle between `retry` and `blocked` without new evidence; continuing the same batch pass becomes churn.

## Important boundaries

- `blocked-resolve-step` resolving a task to `retry` is not completion. It is a controlled release for targeted evidence/certification repair.
- If the next readback shows those tasks return to `blocked`, do not keep batch-releasing them. Produce per-task root-cause packets.
- If workers are active (`claimed`/`running`), poll/read back before claiming no residual process or running another broad dispatch.
- `proof-check PASS` with warnings means no hard proof failure, not that historical debt is gone.
- `selfcheck PASS` + `boundary PASS` proves control-plane health, not task completion.

## Readback summary to report

Always include:

- status counts: `blocked/pending/retry/running/claimed/review`
- `dispatchable_count`
- `selfcheck` status/failure/warning counts
- `proof-check` status/failure/warning counts
- watcher summary
- whether any active workers remain
- whether blocked items are true gates versus stale-claim/control-plane residue

## Stop condition

Stop the drain loop and hand back a compact intervention packet when:

- blocked tasks reappear after a resolver/reconcile cycle;
- remaining warnings are true autorun proof debt needing append-only log/readback or task-specific evidence repair;
- multimodel certification or provider/quorum evidence is missing;
- the next step would spawn broad execution beyond dispatch-hint authority.
