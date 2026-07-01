# Ledger-only executor consumer slice pattern

Extracted from `/Users/charles/.hermes/skills/incremental-implementation/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Ledger-only executor consumer slice pattern

Scope: domain-level pattern for workflow/control-plane systems that are adding their first bounded executor after a separate eligibility or policy-review projection.

Applicability:
- The executor is intentionally limited to read-only or no-external-side-effect actions.
- A durable ledger stores command, plan, policy-review, run, and audit-event state.
- The next authority boundary would be adapter write-through, lifecycle mutation, shell execution, or closeout.

Anti-conditions:
- Do not use this as permission to execute arbitrary commands or mutate external systems.
- Do not apply exact tuple matching blindly if the reviewed action does not depend on payload/target identity; choose the tuple fields that define the reviewed authority.
- Do not turn project-specific command names into global requirements; keep whitelist names in the local reference or project docs.

Falsifier:
- If later architecture uses cryptographic plan digests or immutable command snapshots, replace exact tuple re-checks with the stronger digest/snapshot contract.

Process:

1. Keep the first consumer ledger-only.
   - It may insert run rows and audit events in the control-plane ledger.
   - It must not write adapters, close tasks, mutate external task lifecycle state, or run arbitrary shell.

2. Gate execution on durable plan + policy state.
   - Require the executor plan to still be planned/not-executed and write-disabled.
   - Require a policy review that is explicitly read-only eligible, allowed, and write-disabled.
   - Require the command to still be in the expected pre-execution ledger state.

3. Treat policy freshness as exact tuple matching, not just class eligibility.
   - Persist the reviewed/generated command tuple in the plan, including the fields that define authority, typically command type, risk level, and payload.
   - Before execution, re-read the current command and require exact tuple equality with the generated plan.
   - Recompute read-only eligibility from the current tuple.
   - Fail closed even if a stale command changed from one allowed low-risk type to another allowed low-risk type.

4. Make idempotency concurrency-safe.
   - Use a unique run key such as `plan_id`.
   - Return an existing run on ordinary retry.
   - Catch unique-constraint races and re-read the existing run before raising.

5. Verify the boundary explicitly.
   - Tests must assert no task rows/lifecycle state and no adapter observations/writes changed.
   - Smoke tests should create command → plan → policy review → read-only run → repeated run, then inspect ledger rows/events.

See also: `references/control-plane-read-only-executor-consumer.md` for the session-specific command whitelist and verification bundle that motivated this pattern.
