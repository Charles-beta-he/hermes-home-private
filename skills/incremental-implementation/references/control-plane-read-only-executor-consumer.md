# Control-plane read-only executor consumer pattern

Use this reference when a workflow/control-plane project moves from a non-executing eligibility projection to a tightly bounded read-only executor consumer.

## Durable pattern

1. Keep the first executor consumer ledger-only.
   - It may record run rows and audit events in the control-plane ledger.
   - It must not write task/adapters, close tasks, mutate lifecycle state, or run arbitrary shell.

2. Gate execution on the previously reviewed plan and policy.
   - Plan exists and is still `planned` / `not_executed`.
   - Plan has `writes_enabled = false`.
   - Execution-policy review exists.
   - Review status is `read_only_eligible`.
   - Review has `allowed_to_execute = true` and `writes_enabled = false`.
   - Command is still in the expected pre-execution ledger state.

3. Make policy freshness exact, not just class-compatible.
   - Persist the reviewed/generated command tuple in the executor plan, including `command_type`, `risk_level`, and payload.
   - Before execution, re-read the current command and require exact tuple equality with the generated plan.
   - Recompute read-only eligibility from the current tuple.
   - Fail closed if the command changed, even if it changed from one whitelisted L0/L1 command to another.
   - Consider adding target identity to the tuple if the read-only action depends on target_type/target_id.

4. Make idempotency robust.
   - Put a unique constraint on the consumer run identity, usually `plan_id`.
   - Check for an existing run before executing.
   - Catch `sqlite3.IntegrityError` from a concurrent insert and return the existing run as `created=false`.

5. Verify the negative boundary, not only the happy path.
   - Missing policy review fails closed.
   - Blocked policy fails closed.
   - Risk or command type changed after review fails closed.
   - Payload changed after review fails closed.
   - Repeated execution returns the same run without a second audit run.
   - Task table and adapter-observation/write tables remain unchanged.
   - Snapshot explicitly reports write-through/closeout disabled.

## Verification bundle used in the session

- Focused pytest over core + plugin tests.
- `py_compile` for touched Python files.
- `git diff --check` before commit.
- Coverage with fail-under target.
- Smoke test that creates command -> plan -> policy review -> read-only run -> repeat run, then checks:
  - run is `read_only_completed`;
  - repeat has `created=false`;
  - tasks count is unchanged;
  - adapter observations/writes count is unchanged;
  - audit events include the read-only run event.
- Static scan for hardcoded secrets, shell execution, and dangerous eval/exec/pickle/string-formatted SQL.
- Independent pre-commit review focused on fail-closed freshness, idempotency, and no write-through mutation.
