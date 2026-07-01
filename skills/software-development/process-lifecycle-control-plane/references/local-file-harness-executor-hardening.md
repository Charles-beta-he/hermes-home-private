# Local-file harness executor hardening

Scope: Hermes/control-plane authority ladders where the first executor rung writes only to a local JSON harness and receipt ledger. Applicability: before real taskpool/Kanban/Lark/Telegram/external adapter write-through. Anti-condition: this pattern is not authorization for real external or lifecycle mutation.

## Required contract

1. Keep the feature default-off in config and prompt-readback surfaces.
2. Split authorization and execution:
   - `authorize-*` records a non-executing exact tuple.
   - `execute-*` consumes exactly that tuple.
3. Bind the tuple to all of:
   - `authorization_id`
   - `intent_id`
   - `adapter`
   - `target_ref`
   - `target_status`
   - sorted non-empty `evidence_refs`
   - exact `adapter_state_path`
   - explicit `external_side_effects_authorized=false`
4. Execution may mutate only the SSOT-local harness state and receipt ledger.
5. Return explicit booleans: `executed`, `verified`, `idempotent`, `external_side_effects_executed=false`, `real_taskpool_write_executed=false`.

## Path-safety rules

- For the first rung, prefer direct-child-only files under the executor directory; reject subdirectories, `.`, `..`, and traversal strings such as `foo/../state.json`.
- Reject final-file symlinks and reject the executor directory itself if it is a symlink.
- Use descriptor-relative/openat-style reads/writes/appends anchored to a verified executor directory; use `O_NOFOLLOW` where available.
- Do not pass caller-derived parent paths to `mkdir`, `open`, `read_text`, or `write_text` after validation.
- Add tests for outside paths, final symlinks, symlinked subdirectories that point inside, and parent traversal.

## Receipt/state transaction

- The receipt is part of the execution contract, not a best-effort log.
- If state write succeeds but receipt append fails, attempt rollback for every exception class, not only `ValueError`.
- If rollback fails, report it explicitly, e.g. `rollback_failed=true` and `blocked_reason=receipt_append_failed_rollback_failed`; do not claim `executed=false` when state may remain changed.

## Idempotency

- Idempotency keys must include adapter state path and evidence refs, not only authorization/target/status.
- On duplicate, re-read state and prove the target already has the requested status before returning success.
- Mismatched evidence or path should fail with an authorization mismatch, not reuse a prior receipt.

## Verification checklist

- RED/GREEN tests for disabled flag, missing evidence, missing authorization record, tuple mismatch, allowed execute, duplicate execute, path escape, symlink escape, traversal path, receipt append failure rollback, and rollback failure reporting.
- Live CLI smoke: authorize returns `executed=false`; execute returns `executed=true verified=true`; duplicate returns `executed=false idempotent=true`.
- Independent reviewer checks side effects and path safety; loop until `security_concerns=[]` and `logic_errors=[]`.
- Multi-model/truth gate can certify the boundary only when evidence IDs bind to normalized claim IDs (e.g. `C-001`).
