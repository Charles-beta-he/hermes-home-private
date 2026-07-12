# Projection-to-native-surface advancement for Agent OS work

Use when a user authorizes broad Agent OS / personal AI OS / control-plane advancement and explicitly says not to stop at a phase label or generic human-intervention boundary.

## Reusable pattern

1. Treat completed planning packets, schemas, ledgers, and projections as intermediate artifacts, not stopping points.
2. Continue to the next safe local surface when authority allows it:
   - read-only CLI command over the packet;
   - authenticated dashboard/API projection endpoint;
   - local status/doctor/backlog/panels/capability summaries;
   - operator UI over the authenticated projection;
   - local-only filters/deep links for reproducible control-room state;
   - read-only receipt/handoff packet builders that summarize counts, boundaries, and open external dependencies;
   - tests, py_compile/build, CLI/API readback, and browser/console verification.
3. For each UI/API surface, prefer a small TDD ladder:
   - add a seeded-packet fixture test for the CLI/API output before implementation when practical;
   - prove the missing command/route fails, then implement the smallest read-only projection;
   - wire the dashboard only after the authenticated API is green;
   - verify the live browser state, including URL hydration/filter behavior when deep links are involved;
   - write proof back to the SSOT/backlog/ledger and commit code and SSOT changes in their respective repos.
4. Preserve the execution boundary explicitly:
   - no capability invocation;
   - no scheduler/taskpool/mission lifecycle write;
   - no external dispatch;
   - no secret entry, payment, legal signature, destructive action, or physical-device effect.
5. If the next desired capability crosses one of those boundaries, emit a structured AuthorityBoundary / ExternalDependency / SealedSecretHandoff / LocalSimulation artifact instead of asking vaguely for “human intervention”.
6. Record proof back into the canonical SSOT/backlog/ledger, then keep advancing any remaining safe internal projection surfaces.

## Verification checklist

- Packet doctor/status passes after each projection update.
- New native surface has a direct test fixture with seeded packet data.
- CLI/API endpoint returns JSON readback from the packet, not invented runtime state.
- Dashboard/API route is not made public unless the payload is intentionally public-safe; prefer authenticated read-only endpoints for operational projections.
- Git commit is scoped separately for runtime code and SSOT/ledger documentation when they live in different repos/worktrees.
- Final report distinguishes completed local surfaces from external ecosystem dependencies without treating dependencies as a generic stop reason.

## Anti-conditions

Do not use this pattern to open executor gates, lifecycle writes, external sending, payment/credential handling, production mutation, or physical-device control. Those require exact target, rollback/readback, and a separate authority gate.
