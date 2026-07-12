# Fail-closed projection and lifecycle counterexamples

Use this checklist when a registry, evaluator, lifecycle reconciler, read-only projection, or dashboard can influence promotion/certification or operator decisions.

## Applicability

- Receipt or attestation freshness can open a gate.
- An evaluator consumes records from another producer.
- Demotion/revocation changes top-level and nested lifecycle metadata.
- An API/UI consumes JSON outside its own static type system.

Anti-condition: skip for display-only data that cannot affect execution, promotion, certification, or operator decisions.

## Counterexample-first review

Write and run one RED test per boundary before production changes:

1. **Future-dated freshness**
   - Supply a timestamp far beyond `now`.
   - Never rely only on `max(0, now - timestamp)`: it turns future evidence into age zero.
   - Reject beyond a small explicit clock-skew allowance and expose a machine-readable `future_dated` result.

2. **Evaluator envelope validation**
   - Keep the body valid while independently mutating `schema`, producer/generator, and top-level pre-evaluation status.
   - The independent evaluator must veto each wrong envelope field before body completeness can produce PASS.

3. **Lifecycle coherence**
   - Demote/reopen a promoted object and read back both top-level status and nested promotion metadata.
   - Clear the active promotion state; preserve previous state, transition event, and timestamp for audit.
   - Verify idempotence and history-prefix preservation.

4. **Nested projection validation**
   - Replace an axis with `{}`, an array, missing fields, wrong scalar types, and malformed list entries.
   - Backend: validate nested required fields, reject booleans where integer counters are expected, filter malformed entries, mark projection untrusted, and return safe partial/empty values.
   - Frontend: retain runtime guards and safe fallbacks even when TypeScript types claim the payload is valid.

## Closure evidence

- Preserve RED output proving each counterexample originally failed.
- Run narrow GREEN tests, then the smallest relevant aggregate suites.
- Run typecheck/build for frontend projection changes.
- Read back the real local status surface and confirm certification/promotion remains closed.
- Stage exact files only; exclude generated artifacts and unrelated lockfile drift.
- If a broad suite times out or has unrelated failures, confirm residual processes ended, report it separately, and do not convert scoped passing evidence into an all-green claim.

This closes code-level counterexamples only. It does not establish external E2E freshness, provider quorum, or global certification.