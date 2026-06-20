# Taskpool proof source recovery — 2026-06-20

## Objective

Recover remaining invalid `proof:sha256:*` task evidence from real append-only autorun proof sources only. No proof forging, no deletion of warnings, no arbitrary unrelated proof substitution.

## Authority

User selected option `1允许`: allow searching earlier/external archived `auto_run_proof.jsonl` or source artifacts to recover true proof hashes.

## Sources searched

- Active proof log: `/Users/charles/.hermes/state/auto_run_proof.jsonl`
  - lines/events: 3302
  - chain already verified by `brain_task_orchestrator.py proof-check --json`.
- Hermes backup archives containing proof logs:
  - `/Users/charles/.hermes/backups/pre-update-2026-05-16-210747.zip!/state/auto_run_proof.jsonl`
  - `/Users/charles/.hermes/backups/pre-update-2026-05-25-121602.zip!/state/auto_run_proof.jsonl`
- Migration backup diagnostics:
  - `/Users/charles/.hermes/backups/taskpool-live-migration-20260620-201256/proofcheck.before.json`
  - `/Users/charles/.hermes/backups/taskpool-live-migration-20260620-201256/proof-debt-dryrun.before.json`
- Local mission/classifier evidence:
  - `/Users/charles/.hermes/evidence/mission-msn_20260610_120149_27c88cfc/20260612-proof-debt-classifier/proof-debt-classification-summary.json`
- Workflow private artifacts under:
  - `/Users/charles/.hermes/hermes-agent/docs/private/workflow-kernel-candidate-consolidations/`
  - `/Users/charles/.hermes/hermes-agent/docs/private/workflow-kernel-runtime-*`
- Spotlight-discovered external archive candidate:
  - `/Users/charles/Downloads/personal-hermes-brain-main.zip`

## Recovery performed

Recovered 1 additional invalid proof hash in:

`/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-04-补证闭环task---hermes-ux-9-devicetwin-diagnose-taskpool-multimodel-verifier-first-im.md`

Replacement:

- old invalid: `proof:sha256:e964e1e15dd71116481ce1808ac109779ece5e2ca30b4cc57f27a15737734812`
- recovered legal proof-log event: `proof:sha256:02c6825e22ba87525e2f9461fbd261e4f794b1e7e453948df7f55da00fade69c`

Reasoning:

- The recovered hash exists in active append-only `auto_run_proof.jsonl`.
- Event actor: `hermes-autorun-review-close`.
- Event task: `2026-05-31-hermes-ux-9-devicetwin-diagnose-taskpool-multimodel-verifier-first-implementatio`.
- The repaired child task explicitly references this parent review-gap evidence chain.
- Event base evidence includes deterministic selfcheck/proof-check/p10-health evidence and UX9 implementation evidence linked to the same closure chain.

## Remaining unresolved proof debt

`proof-check` now reports 3 warnings, all sharing the same invalid hash:

`proof:sha256:0cd6ac5a5e4faaf36f6453051e5952dc17e68f7de3dd3c4709da605cd0a7ee44`

Affected tasks:

1. `2026-06-13-workflow-kernel-consolidated-candidatemodel-routes`
2. `2026-06-13-workflow-kernel-consolidated-candidatemodule-contracts`
3. `2026-06-13-workflow-kernel-consolidated-candidatesafety-flags`

Findings:

- `0cd6...` is not present as an `event_hash` in active `auto_run_proof.jsonl`.
- `0cd6...` is not present in the two discovered older proof logs.
- The exact consolidated workflow task ids do not appear in the discovered proof logs.
- `0cd6...` is not the sha256 digest of the checked workflow private artifacts under docs/private.
- `personal-hermes-brain-main.zip` does not contain `auto_run_proof` or the relevant workflow consolidation ids.

## Verification after recovery

Final command results:

- `python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py proof-check --json`
  - status: PASS
  - checked_count: 325
  - warnings_count: 3
  - failures: []
- `python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
  - status: PASS
  - task_count: 400
  - warnings: []
  - failures: []
- `python3 /Users/charles/.hermes/scripts/v_state.py --json`
  - V: 0.995
  - grade: HEALTHY
  - bottleneck: cron

## Decision boundary

The remaining 3 workflow-kernel warnings require either:

1. A still-older or external `auto_run_proof.jsonl` containing the true `event_hash` for the consolidation/write event; or
2. A deliberate governance decision to mark these three as `legacy_unrecoverable_autorun_proof_debt` / historical import-candidate debt without treating them as valid autorun proof.

No automatic source recovery path remains from the currently visible local evidence.
