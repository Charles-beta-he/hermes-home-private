# Proof source recovery and live taskpool migration notes

Use this reference when cleaning taskpool proof debt or running live-but-reversible migrations on Hermes brain/taskpool state.

## Core proof rule

`proof:sha256:<hash>` for autorun-audited done tasks is not a generic file digest. It must correspond to an `event_hash` in the append-only autorun proof log (`~/.hermes/state/auto_run_proof.jsonl`) and the proof chain must verify. A local artifact file with the same SHA shape is not enough.

## Safe recovery procedure

1. Run a baseline first:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
   - `python3 ~/.hermes/scripts/v_state.py --json` when health impact matters.
2. Enumerate invalid `proof:sha256` warnings and group by bad hash and task id.
3. Search only real proof sources before editing task notes:
   - active `~/.hermes/state/auto_run_proof.jsonl`
   - old backup archives containing `state/auto_run_proof.jsonl`
   - migration backups / proofcheck snapshots for diagnostics
   - source artifacts only to understand provenance, not as substitute proof hashes.
4. Accept a replacement only when it is a real proof-log `event_hash` and it is linked to the same task, the same parent review-gap chain, or an explicitly documented same-chain closure event. Do not borrow an unrelated event just because it satisfies the parser.
5. If no same-chain event exists, stop and produce a DecisionPacket: request older/external proof log access or explicit authorization to mark as legacy unrecoverable debt. Do not forge proof and do not delete the warning.
6. Re-run `proof-check`, `selfcheck`, and `v_state`; record an evidence note with searched sources, replacements, remaining warnings, and rationale.

## Live migration safety pattern

- Backup runtime surfaces before apply: task notes, kanban DB/state, continuation state, handoffs, and before snapshots of selfcheck/proofcheck/v_state.
- Prefer dry-run tooling first, then `--apply` with narrow caps.
- For markdown/frontmatter task notes, use line-preserving edits for evidence normalization. Full YAML/frontmatter dumps can change inline lists into block lists and break lightweight parsers.
- Archive rather than delete backlog objects unless the cleanup tool has an explicit retention policy and rollback manifest.
- Commit code/tooling changes separately from runtime brain/kanban state, because task notes and DBs may be outside the `.hermes` git repo. Preserve runtime effects with backups and evidence reports.

## Anti-conditions

Do not use this reference to justify:

- Treating model consensus as proof.
- Treating any artifact SHA as an autorun `proof:sha256` unless the verifier explicitly accepts that class.
- Marking tasks done or changing lifecycle state merely to clear proof warnings.
- Silencing warnings without a recovery source or explicit legacy-debt decision.
