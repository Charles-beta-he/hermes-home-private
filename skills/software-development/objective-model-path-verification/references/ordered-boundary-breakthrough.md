# Ordered Boundary Breakthrough

Scope: governed workflow/control-plane work where the user explicitly asks to proceed in order, break through boundaries, or reach full functional coverage after local/reversible drain is complete.

Applicability: use when an existing authorization ladder, manifest, policy gate, rate limit, idempotency key, target allowlist, or receipt ledger already exists. This is not for ad-hoc external publishing or destructive work without a prior gate packet.

Anti-conditions: do not use this to bypass credentials, payment, legal/safety gates, destructive cleanup, publish/deploy/push, or broad external mutation. Do not weaken idempotency/rate limits silently just because the user said "break through boundary".

## Procedure

1. Reconstruct the ordered ladder from existing artifacts: packet -> decision -> exact target/payload/purpose -> execution command -> receipt ledger -> projection/readback.
2. Consume the smallest next boundary in order. Prefer existing exact manifest/target/payload/idempotency over inventing a new payload.
3. If the next layer is an execute path, actually run the governed executor rather than stopping at another packet/report.
4. Treat policy refusal as valid functional coverage when it is the intended behavior: duplicate idempotency, daily limit exhaustion, kill-switch, target-disabled, payload guard, or allowlist mismatch should append/read back a blocked receipt and prove no side effect was executed.
5. Add regression tests for both sides of the boundary when possible: allowed execute path and blocked duplicate/rate-limit path.
6. Refresh operator projections/fail-closed summaries after execution or blocked execution.
7. Stage-report the precise boundary consumed, the exact blockers if blocked, and whether external side effects executed.
8. Commit only scoped code/tests/artifacts.

## Verification checklist

- Existing packet/manifest/target/payload/idempotency were identified before execution.
- The executor was invoked with exact target selection.
- Receipt ledger records executed=true for success or a specific blocked reason for refusal.
- For blocked duplicate/rate-limit paths, send_result/raw_send_result is null and external_side_effects_executed=false.
- Tests cover allowed send-once and blocked repeat behavior.
- Live/control-tower/fail-closed readback still shows neighboring gates closed unless separately authorized.

## Pitfalls

- Boundary-breakthrough is not policy deletion. If rate-limit/idempotency blocks a same-day repeat, that is a successful safety outcome, not an excuse to edit the policy.
- A historical successful one-shot send plus a current blocked duplicate can together prove full coverage: success path is evidenced, repeat path is governed.
- Do not create a new payload or target merely to force another external send unless the user supplied exact content/target or the existing gate packet already authorizes that variation.
