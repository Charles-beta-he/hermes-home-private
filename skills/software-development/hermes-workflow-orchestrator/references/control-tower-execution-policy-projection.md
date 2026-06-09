# Control Tower execution-policy projection pattern

Scope/applicability: use for Hermes Workflow Orchestrator control-plane work when a workflow UI or dashboard is moving from proposal/dry-run planning toward real execution authority. This is not a rule for ordinary application features or already-authorized executors.

Anti-conditions: do not apply when the user explicitly asks only for a read-only status report, when execution authority and adapter mutation contracts are already implemented and verified, or when the system is not a control-plane/workflow-orchestration surface.

Falsifier: if a future Control Tower ADR explicitly enables a real executor with whitelist, role matrix, approval binding, evidence rules, rollback path, and adapter mutation contract, then this pattern becomes a pre-execution review step rather than a hard stop.

## Durable lesson

Before enabling any real executor or write-through adapter, add a non-executing execution-policy projection layer. This lets the dashboard/operator see what would happen, which writes would be attempted, and whether rollback/escape is available, while preserving the hard boundary that no lifecycle action executes yet.

## Recommended sequence

1. Keep command proposal, approval, and executor-plan generation separate:
   - proposed command records operator intent;
   - human approval records authorization intent;
   - executor plan records copy-command/dry-run intent.
2. Add a policy-review projection before real execution:
   - one review per executor plan;
   - idempotent repeat returns existing review;
   - missing/non-planned/non-dry-run plans fail closed.
3. Persist policy review as ledger data, not as adapter state:
   - `policy_status = execution_blocked` until real executor policy exists;
   - `allowed_to_execute = false`;
   - `writes_enabled = false`;
   - `blocked_reason = real_executor_policy_not_enabled`;
   - `adapter_writes = []` while writes are disabled;
   - rollback preview explicitly says unavailable because no mutation occurred.
4. Emit an audit event such as `ExecutionPolicyProjectionRecorded`.
5. Expose the projection in snapshot/UI with `real_executor_enabled=false` and `writes_enabled=false`.
6. Stop before real execution until these are explicitly decided:
   - executor whitelist;
   - role/approver matrix;
   - approval expiration and payload-digest binding;
   - risk-level evidence requirements;
   - rollback/escape path;
   - adapter mutation contract.

## Tests to require

- Ledger schema includes the policy-review table.
- Policy review records `execution_blocked`, `allowed_to_execute=false`, `writes_enabled=false`, and `execution=not_executed`.
- Policy review is idempotent and does not duplicate audit events on repeat.
- Missing plan and non-planned plan fail closed.
- Snapshot includes execution-policy projection and never reports real executor enabled.
- Dashboard/API policy-review endpoint returns the projection without lifecycle mutation.
- Smoke test verifies command status remains `proposed` after approval, plan, and policy review.

## Review pitfalls

- Do not let "policy reviewed" become implicit execution authority. It is only a preview until an explicit executor policy is implemented.
- Revalidate existing plans before returning them; a stale plan for a command or plan that later became ineligible should fail closed.
- Prefer parameterized SQL for all IDs. For dashboard route IDs, use URL encoding.
- Consider handling concurrent duplicate review creation around the unique constraint so races return the existing review rather than surfacing an integrity error.
- Convert API-layer `ValueError` into explicit 400/404 once UX matters; fail-closed 500 is safe but less legible.
