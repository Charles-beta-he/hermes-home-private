# Goal workflow governed local execution boundary

Applicability: Hermes/self-architecture workflow executors where a user broadly authorizes target nodes, worker limits, toolsets, write boundary, rollback/readback, and taskpool/mission integration, but the implementation is still moving through event-governed side-effect layers.

Anti-conditions: Do not use this pattern to justify live LLM/subagent spawning, taskpool/mission/cron adapter write-through, external dispatch, push/deploy/publish, destructive operations, or credential/payment entry. Those remain separate adapter- or sender-specific boundaries with their own receipts and readback.

## Pattern

1. Treat broad authorization as opening only the next narrow boundary, not every future boundary at once.
2. Bind the execution request to exact target nodes and current node state. Execute only nodes that are currently `ready`; reject missing, completed, blocked, or human-gated nodes.
3. Enforce budget caps strictly:
   - `max_workers` must be a positive integer.
   - `max_turns` must be a positive integer.
   - `max_cost` must be a non-negative number.
   - Reject invalid or non-positive values; do not silently coerce them to permissive defaults.
   - Reject when `len(target_nodes) > max_workers * max_turns`.
4. Record allowed toolsets as part of the receipt. If the local boundary does not actually launch tools, say so explicitly and keep tool invocation counts at zero.
5. Keep the first execution boundary local: mutate only the local workflow run/checkpoint and append execution receipts in the canonical local ledger/state store.
6. If taskpool/mission integration is requested but the adapter boundary is not implemented in the same slice, record it as `authorized_not_written`; do not write through implicitly.
7. Include rollback/readback in the returned packet:
   - previous workflow-run snapshot or exact rollback key;
   - completed/ready counts;
   - worker dispatch count;
   - checkpoint/receipt write flags;
   - external side effects list, usually `[]` for this boundary.
8. Add tests for both success and rejection paths before implementation. Include invalid caps, unready target rejection, local readback, and no external side effects.
9. Run a temp-home smoke that proves durable readback from storage, not just the in-memory return value.

## Pitfall: silent authority normalization

Do not normalize unsafe user-supplied authority into safe-looking defaults. A bug found during the goal workflow implementation accepted `max_workers=0`, `max_turns=0`, and non-numeric caps by converting them to `1` or `0`. That violates exact authority: invalid authority must fail closed with a clear error.

## Verification checklist

- Focused tests cover success plus invalid authority rejection.
- `py_compile`/static checks pass for command surfaces and tests.
- Temp-home smoke shows:
  - selected exact ready node ids;
  - local write executed;
  - readback from persisted state;
  - `adapter_write_enabled=false` unless an adapter-specific boundary is being tested;
  - `external_side_effects=[]`;
  - taskpool/mission states are `authorized_not_written` until adapter write-through exists.
