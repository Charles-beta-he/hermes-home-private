# Autonomous runtime governance takeover → read-only gates

Scope: Hermes/control-plane or agent-runtime architecture work after a canonical architecture packet has been accepted and the user says to continue until safe boundaries.

Applicability:
- A new canonical architecture/SSOT packet has taken over interpretation from older local-brain or phase documents.
- Old sources must remain as evidence/history, not be physically overwritten.
- The next goal is to move from documentation governance into executable, verifiable runtime scaffolding without opening mutation/side-effect gates.
- The user gives broad/project/system-level authorization, but no exact runtime mutation target has been accepted yet.

Anti-conditions:
- Do not use this to authorize scheduler/taskpool/gateway mutation, external dispatch, publish/deploy/push, destructive actions, credential entry, broad fan-out, or physical/payment actions.
- Do not treat a documentation doctor, schema status, runtime audit, or EvidenceNode projection as proof that runtime reconciliation/compensation is implemented.
- Do not delete or rewrite historical receipts/ledgers to make the new structure look clean.
- Do not create or mutate a runtime domain store unless an exact promotion packet names targets, allowed actions, backup/rollback, and readback.

## Pattern

1. Complete canonical takeover first.
   - Create a single canonical packet/index.
   - Add disposition banners or manifest entries for old source docs.
   - Keep old ledgers/receipts/profile/evidence files as source artifacts.
   - Add a read-only doctor proving required files, source dispositions, profile pointers, and no missing canonical landings.

2. Record the takeover in the scoped project profile and progress ledger.
   - Project profile should point to the canonical packet and record the current component state.
   - Ledger should state the boundary: interpretation/write-target takeover only; no runtime mutation.

3. Move to P1 as an executable read-only schema gate.
   - Add a CLI/API status surface that validates canonical domain sections and side-effect taxonomy.
   - Validate required objects such as IntentRecord, CapabilityNode, AgentWrapper, AuthorityGrant, ExecutionLease, EvidenceNode, GateDecision, ProjectionRecord, CompensationRecord, and ClosureRecord.
   - Validate S0-S7 side-effect coverage and S4-S7 default-off semantics.
   - Validate `runtime_mutation=false` for the relevant projection.
   - Write a report artifact; do not migrate domain stores.

4. Move to P2 as a read-only runtime audit.
   - Classify local sources into pass/warn/fail divergence records with evidence refs and next-safe-action hints.
   - Initial surfaces can include canonical schema, capability projection, cron jobs, gateway outbox, shadow router, and scoped project profile.
   - Audit may write a local report artifact, but must not compensate, mutate lifecycle state, send messages, or repair sources.

5. Move to P3 as read-only EvidenceNode projection.
   - Map P2 audit findings into canonical EvidenceNode-shaped records, not into a durable domain store.
   - Each node should have a stable id, kind, claim_ids, trust_level, freshness, verification_status, source_ref, divergence_class, and next_safe_action.
   - Include fail-closed behavior: if an audited source is malformed/unreadable, the projected EvidenceNode must carry `verification_status=fail` and the projection must not be `ok=true`.
   - Report `runtime_mutation=false` and `domain_store_mutation=false` explicitly.
   - Write a local report artifact and link it from the canonical index.

6. Stop at P4 runtime-promotion authorization when the next step would write state.
   - Broad wording such as “system-level authorization” should be consumed only to drain safe read-only/local report layers.
   - The next mutable slice needs an exact packet with: allowed target files/stores, allowed actions, explicit non-authorized actions, backup requirement, rollback strategy, idempotency/readback evidence, and acceptance checks.
   - A safe P4 example is local runtime domain-store bootstrap + dry-run reconciliation plan only, with `execute=false`; still require exact target paths and backups before writing.
   - Keep scheduler/taskpool/gateway mutation, worker spawn/lease, compensation, external send, publish/deploy/push, destructive actions, credential entry, and broad fan-out closed unless separately exact-authorized.

7. Use strict TDD for executable gates.
   - RED: missing CLI function/import or failing schema/audit/projection expectations.
   - GREEN: minimal read-only implementation.
   - Verify with focused tests, py_compile, live CLI readback, report artifact, and scoped commit.

## Verification bundle

Minimum evidence before claiming a slice complete:
- Focused tests pass and at least one RED failure was observed for new behavior.
- Live CLI readback returns `ok=true` and empty/zero failing findings for the expected environment.
- Report artifact exists and is linked from the canonical packet/index.
- Project profile and progress ledger record the slice and boundary.
- Scoped commit includes only the slice’s files; unrelated dirty files remain unstaged.
- For P4 or later, the exact authorization packet exists before any runtime store mutation.

## Common pitfalls

- Stopping after documentation takeover when safe read-only runtime gates remain available.
- Treating old local-brain structure as obsolete and overwriting/deleting receipts or ledgers.
- Opening compensation or external side effects just because schema/audit/evidence gates passed.
- Treating a broad “system-level authorization” as permission to mutate runtime stores without exact targets and rollback.
- Mixing unrelated dirty workflow receipts into the scoped commit.
- Calling `status=pass` a runtime completion claim; it only proves the named read-only gate.
- Writing a reconciliation plan without `execute=false` and explicit adapter/side-effect disabled fields.
