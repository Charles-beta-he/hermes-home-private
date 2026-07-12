# Taskpool Architecture and Test-Matrix Inventory

## Applicability

Use for read-only requests to inventory a taskpool/control-plane implementation across lifecycle, controllers, stores, projections, proof/ratification, retry/reconcile, worker bridge, APIs, dashboard, and tests.

Anti-conditions:
- This procedure does not authorize task lifecycle writes, worker dispatch, cron changes, cleanup, or external actions.
- Do not turn project-local paths, state names, or test counts into universal architecture facts.
- Do not classify a filename as production or covered until its behavior and assertions are read.

## Procedure

1. **Establish the requirements baseline.** Read the newest convergence/spec document first. Convert each material requirement into a row: authority source, transition, gate, failure behavior, and required evidence.
2. **Separate control planes before mapping.** Identify every durable state model independently. Common examples are a canonical task-note store, a SQLite Kanban kernel, an execution-envelope ledger, and derived dashboards. Never merge their states merely because they all say `running` or `done`.
3. **Name authority per surface.** For each store/projection, record whether it is canonical, an execution-attempt ledger, a one-way mirror, a cache, or a UI projection. Trace actual writes; comments such as “observability only” are not proof of read-only behavior.
4. **Extract lifecycle and ownership from code.** Record valid states, allowed transitions, aliases, terminal states, claim-bound states, lease/run ownership, CAS predicates, force paths, evidence requirements, and which controller owns each transition.
5. **Inventory controllers as loops, not files.** For dispatch, autorun, event runner, guardian, drain, retry, and reconcile controllers, record input signal, eligibility SSOT, mutations, lock/dedupe mechanism, stop condition, retry budget, timeout cleanup, and proof/readback.
6. **Trace adapters and projections end to end.** For every bridge, store adapter, dashboard, API, or notifier, map producer → transform/status mapping → writer → event/hook path → consumer. Check whether direct DB writes bypass lifecycle functions, CAS, hooks, or run ledgers.
7. **Map tests by asserted behavior.** Use AST or test-name enumeration only for discovery. Read assertions and map each test to a behavior row. Distinguish unit, integration, service/API, process/concurrency, and true end-to-end evidence.
8. **Run the narrow convergence suite first, then adjacent subsystems.** Use the interpreter and dependency runner declared by the project. A system interpreter collection failure is an execution-environment mismatch; rerun under the project runner before classifying product coverage.
9. **Report fresh outcomes exactly.** Preserve command, pass/fail/skip totals, and failure class. Do not convert “many tests exist” into “covered,” and do not call the whole architecture certified when any material suite failed or a high-risk surface has no test.
10. **Converge requirements to evidence.** For each spec row, cite source code plus test/runtime evidence, or mark the gap as missing implementation, missing test, duplicate authority, bypass path, ambiguous ownership, or environment-only execution issue.

## Recommended matrix

| Domain | Authority / production surface | States or contract | Controller / writer | Tests and evidence | Gap / risk |
|---|---|---|---|---|---|
| Canonical lifecycle | | | | | |
| Claim / lease / CAS | | | | | |
| Completion proof | | | | | |
| Ratification | | | | | |
| Retry / reconcile | | | | | |
| Worker execution | | | | | |
| Attempt/envelope ledger | | | | | |
| Adapter / mirror | | | | | |
| API / dashboard | | | | | |
| Notifications / gateway | | | | | |

## High-risk patterns to flag

- **Dual or triple state machines without contract tests.** Status mappings can erase lease, retry, certification, or terminal semantics.
- **“Read-only/observability” bridge that writes.** Verify both destination DB writes and provenance/backlink writes to the canonical source.
- **Direct SQLite updates around a lifecycle kernel.** These may bypass CAS, run creation/closure, hooks, parent gates, circuit breakers, or audit events.
- **Derived-view tests that mock the projector.** Mock-based mutation tests do not prove atomic regeneration, partial-failure recovery, or consistency across multiple projections.
- **Guardian/drain tests limited to parsers and timeout helpers.** Full-cycle stale-claim, partial-step failure, reentrancy, and “never mark done directly” behavior remain unproven.
- **Standalone proof gate plus embedded proof gate.** Treat as duplicate-authority drift until call graph and equivalence tests prove one is canonical or compatibility-only.
- **PID-file lock implemented as read/check/overwrite.** Without an atomic create or OS lock, concurrent cron starts may both enter; require a multi-process race test.
- **API endpoint counts mistaken for endpoint coverage.** Map route handlers to explicit success, denial, ownership, conflict, and readback tests.
- **Exact-dict tests after metadata enrichment.** If the product intentionally appends provenance/prompt/proof metadata, tests should assert caller fields are preserved plus required enrichment fields, not stale whole-dict equality. First confirm the enrichment contract; do not weaken assertions merely to make failures disappear.

## Verification checklist

- [ ] Requirements/spec baseline was read before cataloging files.
- [ ] Every durable state model and SSOT was named separately.
- [ ] State aliases/mappings and lost semantics were documented.
- [ ] Every mutation path names its controller and gate.
- [ ] Bridges were checked for direct writes and lifecycle bypass.
- [ ] Tests were mapped from assertions, not filenames alone.
- [ ] Project-declared Python/runtime was used for final test evidence.
- [ ] Narrow convergence and adjacent subsystem suites were both exercised.
- [ ] Pass/fail/skip totals and unresolved failures were reported exactly.
- [ ] Untested high-risk behavior was separated from concrete product failures.
- [ ] No write or dispatch occurred during a read-only audit.
