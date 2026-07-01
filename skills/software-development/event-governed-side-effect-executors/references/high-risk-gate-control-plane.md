# High-risk gate control plane pattern

## Scope / applicability / anti-conditions

Scope: agent or workflow control planes where a human asks to enable multiple high-risk side-effect classes at once: runtime hard gates, lifecycle write-through, scheduled worker status writes, external dispatch, publish/deploy/push, destructive actions, or credential/payment boundaries.

Applicability: use when the system can represent capability state, append receipts, and read back local artifacts before any live adapter call.

Anti-conditions: do not use this as permission for arbitrary live sends, deploys, pushes, production deletes, credential entry, payment, broad fan-out, or direct lifecycle closeout. Those remain separate exact-target executor boundaries.

## Core lesson

Treat the request as authority to open a governed control plane, not as authority to execute arbitrary live side effects. "Enabled" should mean each class has an explicit gate, state/readback, receipts, and fail-closed exact-target requirements.

## Safe landing pattern

1. Run routing/preflight first when available and classify risk/side-effect tier.
2. Create or update a local gate state artifact with one record per requested class:
   - `enabled=true`
   - mode such as `enforcing`, `exact_local_target_required`, `local_heartbeat_write_enabled`, `exact_allowlist_required`, `exact_target_required`, `exact_target_and_backup_required`, or `human_secret_entry_required`
   - `stores_secrets=false`
   - `token_read_allowed=false`
   - `requires_post_action_readback=true`
3. Append receipts for enablement and every subsequent authorization attempt.
4. For lifecycle write-through, first open a local ledger boundary with exact object id, exact status/action, evidence refs, and readback. Do not mutate real external adapters until a later adapter-specific boundary consumes that receipt.
5. For scheduled worker auto status, first create a no-agent/local heartbeat script or equivalent that writes append-only status and stays silent on success.
6. For external dispatch and publish/deploy/push, mark the class enabled but live execution fail-closed until exact target, payload hash, rollback where applicable, and post-action readback are supplied.
7. For destructive actions, prove only a disposable local canary unless the user supplies an exact real resource plus backup/restore path and readback.
8. For credential/payment, open only the human-secret-entry boundary. The agent must never type, read, or persist passwords, tokens, cards, or payment secrets.
9. Feed gate status back into the main preflight/readback output so later safety checks can see runtime enablement.
10. Verify with tests for enable-all, missing exact target blocks, local canary, lifecycle ledger write, heartbeat write, syntax checks, and gate status readback.

## Reporting language

Say clearly which classes are enabled as local/fail-closed gates and which live actions remain blocked pending exact targets. Do not claim external send, deploy/push, destructive production change, or credential/payment execution unless it actually occurred and was read back.
