# Cross-Implementation Behavioral Contract Parity

Use this reference when one client, platform, legacy implementation, or service is the behavioral contract for another implementation (for example Android → React H5, iOS → web, legacy API → replacement API).

## Applicability

Apply when acceptance language includes `parity`, `对齐`, `same behavior`, `preserve intent`, route/deep-link migration, auth gates, state restoration, or cross-platform contract compatibility.

Anti-conditions:

- Pure visual similarity with no state, navigation, auth, API, or intent semantics.
- The named implementation is only inspiration rather than an authoritative contract.
- A backend/domain specification supersedes both clients; review against that stronger source instead.

## Contract extraction

Do not compare only the named producer method. Trace the full reference chain:

1. **Trigger:** button/event/action and its input values.
2. **Carrier:** intent extras, query parameters, payload, store event, or broadcast.
3. **Consumer:** exact downstream reader of every material field.
4. **Observable effect:** selected tab/mode/pair, checked state, request/no-request behavior, navigation target, or rendered state.
5. **Negative cases:** anonymous user, unknown identity, missing field, stale state, repeated click, or forbidden mutation.

A field written by the target but never consumed is not parity. It is only inert serialization.

## Producer–consumer verification procedure

1. Pin the reference revision and inspect the reference file from that commit object, not only the dirty working tree.
2. Identify each material contract field and search for its downstream reader in the reference implementation.
3. Inspect the target producer and target consumer independently.
4. Build a compact matrix:

| Field/guard | Reference producer | Reference consumer/effect | Target producer | Target consumer/effect | Verdict |
|---|---|---|---|---|---|
| identity | writes ID/symbol/name | selects requested entity | writes query/payload | resolves requested entity | PASS/FAIL |
| action intent | writes BUY/SELL | selects buy/sell mode | writes query/payload | must select corresponding mode | PASS/FAIL |
| auth gate | checks token first | no mutation and login redirect | checks auth first | no request and login redirect | PASS/FAIL |

5. Require both positive and negative evidence. For an auth-gated action, prove the anonymous path issues no status/mutation request; for a route intent, prove both BUY and SELL cause different observable target states.
6. Run fresh scoped lint/build/tests and read back final repository status. Do not modify files during an independent review unless explicitly authorized.

## Declared-constraint verification

Applicability: cross-implementation reviews where the target advertises a bounded rule, eligibility rule, tier, rounding sequence, or unavailable state. Anti-condition: skip this extension for purely visual parity with no business-rule claim, and never promote one implementation's project-specific constants into a global rule.

For every declared constraint, add the authoritative rule, UI claim, shared enforcement point, lower/upper boundaries, invalid cases, and expected user-visible behavior to the parity matrix. Probe below-minimum, minimum, maximum, and above-maximum values at the shared formula or service boundary and through the UI when practical. Check cross-surface consistency: an unavailable placeholder in one helper is insufficient if another surface still computes from the same invalid state. Verify rounding stages, tier selection, mode-specific data isolation, stale-request protection, identity propagation, and fallback guards—not only happy-path outputs. Treat runtime harness evidence as claim-scoped; viewport, route, and happy-path assertions do not prove unexercised domain boundaries. An advertised but unenforced invariant is an **AMEND** blocker even when tests, typecheck, build, and smoke checks pass.

When a changed legacy file fails whole-file lint outside the changed hunk, position-verify the finding and use blame or parent-revision readback to establish whether it predates the slice. Then run focused lint on the new or materially changed feature files and report both facts: scoped changes are clean, while the containing file retains baseline debt. Baseline attribution never excuses a newly introduced lint issue.

## Evidence rules

- A URL containing a parameter proves carriage, not consumption.
- A screenshot proves only visible pixels at that moment; it cannot prove request absence, authentication, or post-click navigation without correlated trace/readback.
- A JSON report is a claim until bound to the reviewed commit and backed by raw runtime/log/browser evidence. Check its timestamp, target commit, file hashes when available, and certification boundary.
- Evidence generated before the reviewed commit or omitting the target commit has weak provenance even if current source looks similar.
- Build/lint success proves compilability/static quality, not semantic contract parity.
- Prefer fresh source/readback evidence over self-declared `PASS` fields in prior reports.

## Late asynchronous verifier results

A verifier verdict can arrive after the branch has advanced. Treat it as a hypothesis against the current baseline, not as an automatic instruction and not as stale noise.

1. Record the verifier's reviewed commit, timestamp, and exact failing contract link.
2. Re-read current `HEAD` and test whether the same producer → consumer → observable-effect gap still exists.
3. If current code already closes it, attach fresh evidence and mark the old verdict superseded; do not reapply the historical patch.
4. If the gap remains, create a current-baseline RED that reproduces the verifier finding before editing.
5. Apply the smallest consumer/effect fix, then prove both directions and negative behavior. For action intent, verify BUY and SELL select different observable states while neither path triggers the action itself.
6. Rerun scoped lint/build/runtime checks, bind evidence to the new commit, perform clean-status/log/show readback, and re-dispatch an independent verifier for the remediation commit.
7. Keep certification at the local evidence level until the new verifier returns; an AMEND on an ancestor does not certify or condemn later commits by itself.

Avoid turning a late verdict into a broad rewrite. The correct unit of remediation is the still-reproducible behavioral contract gap on current `HEAD`.

## Verdict calibration

Return **APPROVE** only when every material reference effect has an implemented and evidenced target consumer/effect.

Return **AMEND** when any material field is merely forwarded, ignored, mapped to the wrong state, or supported only by evidence that does not prove the claimed behavior. State the smallest concrete correction and the exact runtime assertion needed to close it.

Partial results may be reported explicitly (for example, identity PASS, action intent FAIL, anonymous auth gate PASS), but any material FAIL makes the overall verdict AMEND.
