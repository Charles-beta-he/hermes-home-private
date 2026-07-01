# Autonomous runtime governance P4 bootstrap boundary

Scope: agent-control-plane / autonomous-runtime governance work after P0-P3 read-only layers are already landed: documentation/local-brain takeover, schema gate, read-only runtime audit, and EvidenceNode projection.

Applicability:
- The user explicitly accepts an exact P4 runtime-promotion authorization packet.
- The packet names allowed target files/stores, allowed actions, not-allowed actions, backup/rollback, idempotency, and readback requirements.
- The intended next step is local runtime/domain-store bootstrap plus an execute=false reconciliation plan.

Anti-conditions:
- Do not use this pattern to open scheduler/cron mutation, taskpool/mission lifecycle writes, gateway outbox mutation, external dispatch, worker spawn/lease, compensation execution, publish/deploy/push, payment/credential entry, broad fanout, or destructive actions outside the exact listed local targets.
- Do not treat broad “system-level authorization” as sufficient; broad authorization can drain read-only layers, but local runtime mutation needs the exact packet.

Procedure:
1. Preflight the local Agent OS/control-plane route if available; treat it as advisory evidence, not execution permission.
2. Write RED tests before implementing the executor:
   - success path writes only the exact allowed targets;
   - target drift is rejected;
   - receipt is idempotent;
   - all reconciliation actions remain `execute=false` and adapter/compensation flags stay disabled.
3. Validate the authorization packet before any write:
   - expected packet id/status;
   - exact allowed target set;
   - no unexpected target paths;
   - upstream P3 EvidenceNode projection is ok.
4. Back up/read existing target hashes before writing.
5. Write only the local runtime state, receipt ledger, and execute=false reconciliation plan named by the packet.
6. Receipt shape should include: schema version, idempotency key, request digest, boundary name, before/after hashes, authority gate path, readback counts, and explicit `external_side_effects_executed=false` / `compensation_executed=false`.
7. For idempotency, do not include volatile fields such as generated timestamps in the stable digest. Prefer a semantic digest over gate id, exact targets, stable source projection hash, and idempotency key. A replay with the same idempotency key must not append another receipt or mutate state/plan.
8. Read back the state/plan/receipt files and assert:
   - evidence node count matches the source projection;
   - plan action count matches evidence nodes;
   - top-level `execute=false`;
   - every action has `execute=false`, `adapter_enabled=false`, and `compensation_enabled=false`;
   - no neighboring side-effect boundary was touched.
9. Save report artifacts and update the project profile/progress ledger with exact commit/readback evidence.

Pitfall from session:
A first idempotency implementation used a source report hash that included generated timestamps, so each replay produced a new request digest and appended another receipt. The durable lesson is not the transient duplicate receipt; it is to derive idempotency from stable semantic inputs and ignore volatile timestamps. If historical duplicate receipts exist, do not delete or rewrite them; record the final idempotency readback honestly.
