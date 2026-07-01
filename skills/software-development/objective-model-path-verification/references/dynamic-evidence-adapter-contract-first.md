# Dynamic Evidence Adapter: Contract-First Landing

Use when a governed agent needs live/dynamic facts (weather, road status, tickets, map ETA, market/runtime state) but external calls or execution are not yet authorized.

## Reusable pattern

1. **Land the contract before live sources**
   - Define a dynamic evidence fact with stable fields: `id`, `sourceKind`, `subjectGateIds`, `claim`, `observedAt`, `expiresAt`, `sourceName/sourceUrl`, `confidence`, `outcomeHint`, optional `actionHint/fallbackHint/doNotDo`.
   - Define adapter request/response boundaries and explicitly mark authority (`read_only`, `local_fixture`, etc.).

2. **Make freshness a first-class gate**
   - Evaluate `fresh`, `stale`, `future`, and `undated` from `observedAt/expiresAt` against `now`.
   - Treat stale/missing/undated evidence as `blocked` or fail-closed for safety-relevant gates.

3. **Project evidence into the domain state, not memory**
   - Attach dynamic fact IDs to the affected gate(s).
   - Add normalized evidence records to the domain state/SSOT with source type and freshness.
   - Do not save temporary live values into long-term memory.

4. **Generate a gate manifest candidate**
   - Convert fresh facts into a `DynamicGateManifest` or equivalent.
   - A fresh positive fact can make `decision=pass`, but must remain `status=advisory` unless the certification rule is satisfied.
   - Require independent safety/evidence/arbiter coverage (or the project’s equivalent) before calling it certified.

5. **Fixture-first tests**
   - Add a local fixture adapter that proves contract behavior without network calls.
   - Tests should cover fresh, stale, missing, state projection, advisory-vs-certified, and fail-closed behavior.

6. **Only then add live adapters one at a time**
   - Start with the lowest-risk read-only source.
   - Each live adapter needs source-specific readback, TTL, no-credential/exact-credential boundary, and fail-closed tests.

## Anti-conditions

- Do not call live APIs, buy tickets, send messages, start navigation, deploy, publish, or mutate external systems under a vague “continue/authorize” unless the exact target/action/rollback/readback gate is already open.
- Do not treat a fixture as live evidence.
- Do not treat model or role agreement as evidence unless it cites concrete claim-linked artifacts.

## Verification checklist

- Contract types compile.
- Fixture adapter works with no external side effects.
- Stale/missing evidence blocks.
- Fresh evidence updates state/gate evidence IDs.
- `pass` remains advisory until independent certification votes are present.
- Full package tests/build and any downstream import/Jest/module-mapper surfaces still pass.
