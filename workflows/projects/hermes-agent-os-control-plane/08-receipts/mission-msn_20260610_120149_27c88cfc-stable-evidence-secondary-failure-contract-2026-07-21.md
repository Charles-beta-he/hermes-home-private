# Stable evidence post-publication secondary-failure contract

Scope: the isolated `persist_stable_evidence_bundle` helper only. The helper remains disconnected from live quorum execution; this contract selects no provider/model, production retention root, cleanup policy, or runtime call site.

## Objective model

- Success means only a bundle that passes final byte/hash readback remains in the success namespace.
- The primary post-publication verification failure must remain visible even when diagnostic recovery also fails.
- Quarantine is the authoritative fail-closed state transition; a failure receipt is best-effort diagnostics after that transition.
- No destructive fallback is allowed: failure handling must not delete the published or quarantined bytes.

## Executable negative contracts

1. **Quarantine rename failure**: raise a composite `RuntimeError` containing both the primary readback failure and the secondary quarantine failure. The directory may remain at the former success path because moving it failed, but the call must fail and no success result or diagnostic receipt may be returned.
2. **Failure-receipt publication failure**: after successful quarantine, raise a composite `RuntimeError` containing both the primary readback failure and the secondary receipt-publication failure. The quarantine remains authoritative, no receipt is claimed, and receipt temporary files are cleaned best-effort.

These contracts intentionally fail against the current helper. A later bounded slice may implement a dedicated composite-error path while preserving the established nine green contracts.
