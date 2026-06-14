# Proof debt classifier slice

status: FAIL
checked_count: 328
failure_count: 72
warning_count: 14

## Classes
- other_failure: 5
- potentially_auto_normalizable_evidence_ref_if_existing_artifact_or_proof_is_present: 62
- requires_real_ratification_artifact_or_human_acceptance: 5
- warning/terminal_invalid_autorun_proof_hash_warning: 14

## Boundary
Read-only classification only. No ledger/task mutation, no push/deploy/secrets/external sends/deletes.

## Next
Build a dry-run supplement candidate constrained to auto-normalizable existing refs; handoff any missing real ratification artifacts.
