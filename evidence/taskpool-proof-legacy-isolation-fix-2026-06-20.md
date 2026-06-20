# Taskpool proof legacy isolation fix — 2026-06-20

## Objective

Fix the remaining three `terminal invalid autorun proof hash debt` warnings after exhaustive source recovery failed.

## Boundary

The invalid hash was not promoted to valid proof. No unrelated proof event was substituted. The fix converts the bad `proof:sha256:*` entries into explicit structured legacy-debt classification plus an artifact pointer to the source-recovery report.

## Background evidence

Source recovery reports:

- `/Users/charles/.hermes/evidence/taskpool-proof-source-recovery-2026-06-20.md`
- `/Users/charles/.hermes/evidence/taskpool-proof-source-recovery-continued-2026-06-20.md`

These reports document that the remaining hash was not found in:

- active `/Users/charles/.hermes/state/auto_run_proof.jsonl`,
- discovered older proof logs in Hermes backup zips,
- visible archives under `.hermes`, Documents, Desktop, Downloads, iCloud local folder,
- mounted `/Volumes`,
- Time Machine local snapshots,
- session DB,
- workflow private artifacts by digest.

## Modified task notes

In each affected task, replaced:

`proof:sha256:0cd6ac5a5e4faaf36f6453051e5952dc17e68f7de3dd3c4709da605cd0a7ee44`

with:

- `classification:legacy_unrecoverable_autorun_proof_debt:sha256:0cd6ac5a5e4faaf36f6453051e5952dc17e68f7de3dd3c4709da605cd0a7ee44`
- `artifact:/Users/charles/.hermes/evidence/taskpool-proof-source-recovery-continued-2026-06-20.md`

Affected tasks:

1. `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-13-workflow-kernel-consolidated-candidatemodel-routes.md`
2. `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-13-workflow-kernel-consolidated-candidatemodule-contracts.md`
3. `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-13-workflow-kernel-consolidated-candidatesafety-flags.md`

## Verification

Final command results after the fix:

- `python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py proof-check --json`
  - status: PASS
  - checked_count: 325
  - warnings_count: 0
  - failures: []
- `python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
  - status: PASS
  - task_count: 400
  - warnings: []
  - failures: []
- `python3 /Users/charles/.hermes/scripts/v_state.py --json`
  - V: 0.997
  - grade: HEALTHY
  - bottleneck: cron
  - orchestrator/dynamic_n/classifier/continuation/envelope/kanban: 1.0
  - cron: 0.983

## Rollback

The task note changes are line-level replacements. Rollback options:

1. Restore task notes from `/Users/charles/.hermes/backups/taskpool-live-migration-20260620-201256/tasks.tgz`.
2. Revert the exact three line replacements in the affected task notes.

Do not restore the invalid `proof:sha256:*` entries unless intentionally reproducing the old proof-check warnings.
