# Technical Audit Report — UAEC ToB Delivery Workflow

Date: 2026-07-20
Audit target: `b2b_delivery_workflow_v1` and its UAEC project trial
Audit boundary: workflow specification, manifest contract, validator, regression tests, RED/GREEN fixtures and evidence integrity. UAEC business code, remote CI, deployment and real-device behavior are outside this audit.

## Executive verdict

The workflow is technically usable as a **local, fail-closed delivery-governance control surface at the declared `pilot` boundary** after the fixes in this audit.

It is not a workflow engine and is not yet certified for autonomous production delivery. It validates a declared snapshot; it does not collect all facts automatically, execute stages, enforce external authorization at runtime, fetch remote evidence, deploy software or obtain client acceptance.

## Objective model

Success criteria:

1. A populated in-progress manifest can be used without faking completion.
2. An accepted boundary cannot skip prior stages.
3. Claims, evidence, artifacts and metrics have referential integrity.
4. Local evidence can be pinned and tampering is detected.
5. Malformed inputs fail closed instead of crashing.
6. External side effects remain closed without exact grant metadata.
7. UAEC contradictory progress claims stay RED; the bounded reconciled pilot stays GREEN.

Non-goals:

- modify UAEC business code or project status;
- prove H5 behavior, CI, deployment, production or client acceptance;
- authorize push/deploy/message/credential/payment actions;
- publish client evidence.

## Initial audit findings and repairs

The adversarial audit rounds found twenty-five reproducible issues:

| ID | Initial issue | Severity | Repair |
|---|---|---:|---|
| F1 | unknown claim evidence ID could PASS | P1 | claim/stage/metric references must resolve to truth-source IDs |
| F2 | missing absolute evidence path could PASS | P1 | absolute refs must exist and be regular files |
| F3 | invalid `observed_at` could PASS | P1 | ISO date validation; future dates rejected |
| F4 | S6 could be accepted without client acceptance | P0 | ordered stage gate plus explicit S6/S7 acceptance contract |
| F5 | string values could masquerade as local authority booleans | P1 | strict boolean validation |
| F6 | malformed negative-evidence type could PASS | P1 | strict list and referential-integrity validation |
| F7 | duplicate risk IDs could PASS | P2 | duplicate detection across governed identifier sets |
| F8 | public case could be ready while manifest remained confidential | P0 | `ready` requires `confidentiality=public`, rights and anonymization |
| F9 | starter `in_progress` manifest was forced to have S0–S4 accepted | P0 | completion boundary is now a target; acceptance is required only by matching closure semantics |
| F10 | generic artifact labels could satisfy accepted stages without the required delivery outputs | P1 | each accepted S0–S7 stage now requires explicit semantic artifact types |
| F11 | stages beyond the declared completion boundary could remain active/accepted | P1 | completion boundary is now enforced as the maximum active stage |
| F12 | unknown external actions and manifest-enabled credential/payment operations could PASS | P0 | external actions are allowlisted; credential/payment operations remain human-only and cannot be enabled |
| F13 | an `accepted` closure could retain unverified or disputed claims | P0 | accepted closures now require every claim to be `verified` or `superseded` |
| F14 | an `accepted_risk` contradiction could rely on resolution prose alone | P1 | approver, acceptance date, compensating controls and known evidence references are mandatory |
| F15 | public-case rights and anonymization could be asserted by booleans alone | P1 | public-ready now requires known rights and anonymization evidence references |
| F16 | client acceptance could omit evidence and use an invalid date | P0 | accepted client records require ISO date and known non-empty acceptance evidence references |
| F17 | the new accepted-closure claim check crashed on list/dict claim states | P1 | explicit string guard plus malformed-status regression coverage |
| F18 | an accepted closure could contain only superseded claims and no verified outcome | P1 | accepted closure now requires at least one verified claim |
| F19 | ready-for-review and waiting-acceptance stages could omit all review artifacts/evidence | P1 | accepted and reviewable stages now require semantic artifacts, evidence and no blockers |
| F20 | client_acceptance could be accepted while S6 remained not_started | P1 | accepted client records now require S6 accepted |
| F21 | accepted_by and scope accepted placeholder values | P1 | exact placeholder tokens such as TBD/TODO/N/A/unknown are rejected without rejecting legitimate qualifiers such as `[US]` |
| F22 | superseded closure accepted weak free-text successors | P1 | `superseded_by` must resolve to an evidence-backed registered successor engagement with a valid lifecycle state |
| F23 | enabled actions accepted arbitrary or unrelated registered grant refs | P1 | grant_ref must resolve to a typed authority grant with grantor/date/evidence and matching action/target/scope |
| F24 | production acceptance could be supported only by a pilot-scoped claim | P1 | verified claims declare `max_stage`; stage_refs beyond that stage are rejected and cannot support accepted stages |
| F25 | the new reviewable-stage membership check crashed on list/dict status values | P1 | string guard plus malformed-stage-status regression coverage |
| F26 | integer `contradictions[].claim_refs` caused an uncaught TypeError | P1 | unresolved-claim aggregation now runs only for list refs and has a regression test |
| F27 | unrelated known sources could serve as public-rights, anonymization or client-acceptance evidence | P2/P1 | those gates now require purpose-specific truth-source types |
| F28 | verified claims allowed an empty limitations list | P2 | verified claims require a non-empty string limitations list |
| F29 | immutable candidate GREEN depended on dirty/untracked facts outside the commit | P1 | four exact source snapshots are now included under the test packet and manifests pin their bytes |
| F30 | claim `max_stage` was still independently self-declared and could be raised with its `stage_refs` | P1 | every truth source now declares a stage capability and a verified claim cannot exceed the highest capability among cited evidence |
| F31 | successor registration accepted an ordinary known source rather than succession-specific evidence | P2 | successor and supersession records now require `successor_engagement`-typed evidence |

A subsequent malformed-type test exposed validator crashes on list/dict values. Type guards and filtered reference handling were added. A seeded 20,000-mutation robustness run then completed with zero validator crashes.

A later two-lane review was replayed rather than trusted by age: its evidence-report lane accepted only the local structural pilot boundary, while its architecture lane found five current false-PASS/crash paths. The first amendment commit was then independently rejected again because placeholder, successor, grant and claim-stage semantics remained too weak and because GREEN depended on bytes outside the immutable commit. Those findings were reproduced and hardened as F21–F31. A fresh post-fix independent vote is still required before certification. Remaining advisory items—an executable recovery/event ledger, routing evals, reusable handover templates, deep anonymization scanning and production/S7 adapters—remain outside this local validator pilot and prevent production certification.

## Multi-dimensional result matrix

| Dimension | Result | Evidence | Remaining boundary |
|---|---|---|---|
| Syntax and executable entry point | PASS | `py_compile`; CLI exit contract exercised | no package/CLI distribution |
| Unit behavior | PASS | 51 tests, all passing in the latest worktree run | standard-library unittest only; final commit-bound rerun required |
| Input robustness | PASS | seeded 20,000 field mutations, zero crashes | not a formal parser proof |
| Missing/corrupt input | PASS | missing and malformed JSON return exit 2 | no JSON Schema publication yet |
| Claim/evidence integrity | PASS | unknown IDs rejected; verified claims require evidence, limitations, stage_refs and a claim/source capability bound; accepted stages require an eligible linked claim | source capability is structurally declared; semantic truth still requires human/domain verification |
| Artifact integrity | PASS | accepted-stage IDs resolve and required S0–S7 semantic artifact types are enforced | remote/logical artifact URIs are declarations |
| Local evidence immutability | PASS | absolute refs require matching SHA-256; tamper test returns exit 1 | mutable source updates require deliberate hash refresh |
| Evidence freshness | PASS | malformed and future dates rejected | no configurable age/SLA threshold |
| Stage ordering and boundary | PASS | prior stages must be accepted; stages beyond completion boundary cannot be active | no event-sourced transition ledger |
| Closure-state contract | PASS | in-progress/review/accepted/waiting/blocked/rollback/superseded rules tested | remains a snapshot, not an event runtime |
| Client acceptance | PASS | accepted client record and S6 acceptance imply each other; identity/scope reject exact placeholder tokens; date and typed evidence are checked | does not contact or authenticate the client |
| Authority safety | PASS, structural | action names are allowlisted; enabled actions require target/scope, a typed evidence-backed matching authority grant, rollback and readback; credential/payment stay human-only | manifest does not itself grant live execution authority |
| Confidentiality/publication | PASS, structural | public-ready requires public classification, rights/anonymization evidence and no markers | no deep secret/PII content scanner |
| Contradiction handling | PASS | UAEC RED returns exactly three conflict errors; accepted-risk needs approval, controls and evidence | reconciliation quality remains reviewer-dependent |
| UAEC bounded pilot | PASS | GREEN reports boundary=pilot, closure=accepted | does not prove UAEC software delivery |
| Recovery semantics | PARTIAL | blocked/rolled-back states are checked | no executable rollback orchestrator or recovery drill |
| Continuation/concurrency/idempotency | PARTIAL | snapshot is deterministic and side-effect free | no lease/event/transition writer for concurrent operators |
| Project-state ingestion | PARTIAL | real UAEC sources are referenced and hash-pinned | manifest extraction/refresh is still manual |
| Remote evidence verification | NOT IMPLEMENTED | explicitly outside validator behavior | URLs are not fetched, authenticated or hash-pinned |
| CI integration | NOT IMPLEMENTED | no CI job installed | must be wired into a chosen repository/pipeline |
| Skill routing and adoption | PARTIAL | delayed reviewer confirmed the branch is usable for diagnosis/pilot | overlaps an adjacent delivery skill; no route evals or reusable S6/S7 handover template pack |
| Cross-project portability | UNVERIFIED | generic skill/template exists | only UAEC has a real project trial |
| Business engineering gate | NOT RUN | out of audit scope | no UAEC lint/build/E2E/remote CI/deploy/device run |

## Executed verification

### Regression and GREEN

```text
...................................................
Ran 51 tests in 0.013s
OK
PASS .../uaec-progress-green.json: manifest gates passed (boundary=pilot, closure=accepted)
```

### RED contradiction fixture

```text
FAIL .../uaec-progress-red.json: 3 error(s)
- unresolved contradiction: X_SCOPE_100
- claim C_GLOBAL_100 cannot remain verified in unresolved contradiction
- claim C_MODULE_GAPS cannot remain verified in unresolved contradiction
RED_EXIT=1
```

### Draft-template gate

The distributed template intentionally remains RED until placeholders are replaced. The observed result is exit 1 with 38 placeholder/date/capability errors across the engagement fields and the 15 required semantic artifact examples. A populated `in_progress` manifest with future stages `not_started` is covered by a passing unit test.

### Robustness

```text
MUTATIONS=20000 CRASHES=0
```

### Input and tamper exits

```text
MALFORMED_EXIT=2 EXPECTED=2
MISSING_EXIT=2 EXPECTED=2
HASH_TAMPER_EXIT=1 EXPECTED=1
```

`ruff` and `mypy` were not available in the active Xcode Python environment; this is recorded as a degraded static-analysis dimension, not reported as a pass.

## Negative evidence

- No UAEC business source code was changed.
- No remote push, deployment, external message, credential entry, payment or production write was performed.
- No historical progress source was deleted or rewritten.
- Public-case status remains `not_ready`.
- Client acceptance remains `not_requested`.
- The GREEN result is not promoted beyond the internal pilot boundary.

## Usability decision

Usable now for:

- private engagement initialization after replacing placeholders;
- bounded claim/evidence modeling;
- fail-closed stage and closure review;
- exact local evidence pinning;
- RED/GREEN project-progress reconciliation;
- pre-commit or CI policy checks once explicitly wired.

Not yet usable as:

- an autonomous project-state collector;
- a multi-operator workflow runtime;
- a deployment/rollback executor;
- a remote evidence attestation service;
- proof of UAEC technical delivery or client acceptance;
- a certified cross-client product.

## Next certification gates

1. Build a read-only adapter that regenerates a manifest candidate from project Profile/SSOT without overwriting reviewer decisions.
2. Add event/transition receipts and optimistic concurrency or idempotency keys for multi-operator updates.
3. Add authenticated remote-evidence adapters with immutable receipts.
4. Install the validator as a repository/CI gate for one explicitly chosen project.
5. Run the same workflow on a second unrelated project.
6. Add route evals and a reusable UAT/runbook/SLA/ownership/recovery handover template pack.
7. Separately run UAEC business lint/build/test/E2E/CI/device gates before making any product-delivery claim.

## Final status

`pilot / technically usable as a local governance validator / not production-certified`
