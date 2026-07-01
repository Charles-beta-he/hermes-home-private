# Taskpool proof source recovery and legacy isolation

Use this reference when `brain_task_orchestrator.py proof-check --json` reports `terminal invalid autorun proof hash debt` for done tasks.

## Principle

A `proof:sha256:<hash>` attached to an autorun-audited done task is not a generic file digest. It must resolve to an `event_hash` in the append-only autorun proof log (`~/.hermes/state/auto_run_proof.jsonl`) with the proof chain intact. Do not repair these warnings by substituting arbitrary artifact SHA-256 values, model agreement, or unrelated proof events.

## Recovery workflow

1. Run `brain_task_orchestrator.py proof-check --json` and enumerate invalid `proof:sha256:*` entries by task id.
2. Search only valid proof sources first:
   - active `~/.hermes/state/auto_run_proof.jsonl`;
   - known Hermes backups containing `state/auto_run_proof.jsonl`;
   - migration backups / archived `.hermes` exports;
   - mounted external/Time Machine/NAS/old-machine exports if the user authorizes them.
3. Accept an automatic replacement only when the replacement hash is present in an intact proof log and is linked to the same task, same parent repair chain, or clearly same governed closeout event.
4. If a task carries an `artifact:` path near the invalid proof, you may compute the artifact digest for diagnosis, but do not re-label it as `proof:sha256:*`. Artifact digests are not autorun event hashes.
5. After each bounded repair, rerun:
   - `brain_task_orchestrator.py proof-check --json`;
   - `brain_task_orchestrator.py selfcheck --json`;
   - health scoring such as `v_state.py --json` when available.

## Legacy isolation when source proof is exhausted

When source recovery is exhausted and the user authorizes fixing the remaining warnings, preserve the historical debt explicitly instead of pretending proof exists:

- Replace the invalid `proof:sha256:<missing>` evidence with a structured classification such as:
  - `classification:legacy_unrecoverable_autorun_proof_debt:sha256:<missing>`
- Add an `artifact:` pointer to the source-recovery evidence report that documents searched locations and why the proof is unrecoverable.
- Do not change lifecycle status, certification status, or completion claims as part of this isolation.
- Verify `proof-check` goes to zero warnings/failures while the task note still records the debt.

## Evidence report contents

A useful source-recovery report should include:

- exact invalid hashes and affected task ids;
- proof logs/backups/archives searched;
- whether the hash appeared as an event hash, file digest, task note copy, or only warning text;
- accepted replacements and why they are same-chain;
- remaining unrecoverable items and the human authority used to isolate them;
- final `proof-check`, `selfcheck`, and health readback.

## Anti-conditions

- Do not modify the proof verifier to ignore bad hashes just to make checks green.
- Do not keep the bad value under a `proof:sha256:` prefix if it is not in the autorun proof log.
- Do not use arbitrary `sha256sum` of a private artifact as an autorun proof event.
- Do not delete the evidence entry without recording a structured debt classification and recovery report.
