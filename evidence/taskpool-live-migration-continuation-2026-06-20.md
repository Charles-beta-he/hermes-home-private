# Taskpool Live Migration Continuation Evidence — 2026-06-20

## Objective

Continue from the prior taskpool live migration and drain remaining safe reversible governance debt: handoff backlog warning, edge node warnings, and recoverable autorun proof hash warnings.

## Completed actions

### Handoff backlog

- Extended `handoff-gc.py` from read-only report to reversible archive mode.
- Archived oldest 35 files from `/Users/charles/.hermes/state/auto_run_handoffs` into:
  `/Users/charles/.hermes/state/auto_run_handoffs/archived/20260620T123643Z`
- Manifest:
  `/Users/charles/.hermes/state/auto_run_handoffs/archived/20260620T123643Z/manifest.json`
- Kept newest 80 source handoffs; no deletion.
- Result: selfcheck handoff warning cleared.

### Edge node policy and heartbeat

- Refreshed local edge registry via `edge_node_registry.py register-local --json`.
- Added explicit local standalone/read-only smoke policy in edge config:
  - `worker.standalone_mode: true`
  - `security.lease_policy: local-readonly-smoke-allowlist-v1`
- Updated `edge_node_registry.py` so successful live `/health` probe clears stale heartbeat warning instead of relying only on registry timestamp.
- Result: edge selfcheck PASS, no warnings.

### Autorun proof hash debt

- Parsed 20 remaining invalid autorun proof hash warnings.
- Verified that `verify_autorun_proof_hash()` only accepts hashes present as `event_hash` in `/Users/charles/.hermes/state/auto_run_proof.jsonl` with a valid chain.
- Replaced recoverable invalid proof refs with exact same-task proof-log event hashes.
- Warnings reduced from 20 to 4.
- No synthetic proof was written.

## Remaining DecisionPacket / human gate

Four historical proof refs remain invalid because no exact same-task event exists in `auto_run_proof.jsonl`:

1. `2026-06-04-补证闭环task---hermes-ux-9-devicetwin-diagnose-taskpool-multimodel-verifier-first-im`
   - invalid: `proof:sha256:e964e1e15dd71116481ce1808ac109779ece5e2ca30b4cc57f27a15737734812`
2. `2026-06-13-workflow-kernel-consolidated-candidatemodel-routes`
   - invalid: `proof:sha256:0cd6ac5a5e4faaf36f6453051e5952dc17e68f7de3dd3c4709da605cd0a7ee44`
3. `2026-06-13-workflow-kernel-consolidated-candidatemodule-contracts`
   - invalid: `proof:sha256:0cd6ac5a5e4faaf36f6453051e5952dc17e68f7de3dd3c4709da605cd0a7ee44`
4. `2026-06-13-workflow-kernel-consolidated-candidatesafety-flags`
   - invalid: `proof:sha256:0cd6ac5a5e4faaf36f6453051e5952dc17e68f7de3dd3c4709da605cd0a7ee44`

Requested authority to clear them: locate an external/archived autorun proof log containing those event hashes, or explicitly mark these four task notes as legacy/unrecoverable proof debt with an auditable non-completion semantic. Do not fabricate event hashes.

## Final verification

- `brain_task_orchestrator.py selfcheck --json`: PASS, task_count=400, warnings=[], failures=[]
- `brain_task_orchestrator.py proof-check --json`: PASS, checked_count=325, warnings_count=4, failures=[]
- `v_state.py --json`: V=0.997, grade=HEALTHY, bottleneck=cron
- Components: orchestrator=1.0, dynamic_n=1.0, classifier=1.0, continuation=1.0, envelope=1.0, cron=0.983, kanban=1.0
- Focused tests: `test_handoff_gc.py` 4 OK, `test_edge_node_registry.py` 6 OK, `test_proof_debt_migration_dry_run.py` 5 OK

## Rollback / escape hatch

- Handoff archive can be restored by moving files back from archived manifest path.
- Task note proof-hash replacements can be restored from backup root `/Users/charles/.hermes/backups/taskpool-live-migration-20260620-201256/tasks.tgz` if needed.
- Code changes are scoped commits in `/Users/charles/.hermes`.
