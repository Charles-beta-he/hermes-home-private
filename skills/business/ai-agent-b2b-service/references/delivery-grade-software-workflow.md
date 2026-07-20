# Delivery-Grade B2B AI-Assisted Software Workflow

## Scope

Use this protocol when the service outcome is not merely advice or an Agent installation, but a client-operable, evidence-backed workflow for software delivery, migration, cross-platform parity, or AI-assisted engineering governance.

Anti-conditions:
- Do not use it to claim production readiness from documents, mocks, builds, or screenshots alone.
- Do not place client names, domains, credentials, private repository paths, or internal business fields in public templates/cases.
- Do not force a Pi package when the client outcome is a governed workflow rather than a packaged conversational Agent.

## Delivery Contract

A delivery-grade engagement must provide five things:

1. **Outcome contract** — business problem, measurable result, completion boundary.
2. **Truth-source contract** — canonical requirements, reference implementation, target implementation, runtime evidence and freshness.
3. **Execution contract** — capability backlog, smallest safe slices, owners, dependencies and rollback.
4. **Authority contract** — what the Agent may do locally and which external actions require exact human authorization.
5. **Acceptance contract** — claim-linked positive and negative evidence, client acceptance, known limitations and operations handoff.

The engagement is not complete merely because the Agent produced code or documentation.

## Lifecycle

```text
S0 Qualification
 → S1 Discovery & Baseline
 → S2 Commercial / Spec / Authority Contract
 → S3 Solution & Delivery Workspace
 → S4 Pilot Slice
 → S5 Production Delivery
 → S6 Acceptance & Handover
 → S7 Operations, Measurement & Ratchet
```

### S0 — Qualification

Inputs:
- client/problem signal;
- sponsor and operator candidates;
- budget, urgency and security constraints.

Required artifacts:
- qualification card;
- decision-maker map;
- initial stop conditions.

Exit gate:
- pain is concrete and repeated;
- sponsor, operator and decision path are named;
- service is feasible without unsafe promises;
- next paid or explicitly bounded diagnostic step is agreed.

### S1 — Discovery & Baseline

Inputs:
- interviews;
- current process/repositories/tools;
- canonical requirements and historical evidence.

Required artifacts:
- needs diagnosis;
- current-state process map;
- Truth Source Map;
- baseline metrics and evidence gaps;
- data/security classification.

Exit gate:
- facts, assumptions and interpretations are separated;
- each source has scope and freshness;
- conflicts are unresolved explicitly, never averaged;
- measurable baseline or instrumentation gap exists.

### S2 — Commercial / Spec / Authority Contract

Required artifacts:
- statement of work and exclusions;
- Spec Packet;
- acceptance matrix;
- Authority Matrix;
- change-control and payment milestones;
- confidentiality/public-case policy.

Exit gate:
- scope and completion boundary are signed or explicitly accepted;
- success metrics and negative requirements are observable;
- external actions name target, rollback and readback;
- credentials/payment remain human-entered;
- public-case rights are explicit, never inferred.

### S3 — Solution & Delivery Workspace

Required artifacts:
- architecture and integration map;
- Capability Backlog;
- risk register;
- delivery manifest;
- evidence index;
- state/event/decision log;
- continuity and recovery procedure.

Exit gate:
- every backlog item names objective, owner, dependencies, risk, acceptance evidence and anti-drift check;
- SSOT location is agreed;
- local-safe and external actions are separated;
- no placeholder data is presented as acceptance evidence.

### S4 — Pilot Slice

Required artifacts:
- one smallest valuable Slice Spec;
- scoped implementation/configuration;
- positive and negative tests;
- runtime/UI/API proof where applicable;
- pilot evidence packet;
- sponsor feedback and go/no-go decision.

Exit gate:
- the slice demonstrates one measurable business outcome end to end;
- all verified claims have scope, evidence and limitations;
- unresolved contradictions block acceptance;
- pilot success does not imply whole-system production readiness.

### S5 — Production Delivery

Required artifacts:
- dependency-ordered production backlog;
- implementation and integration evidence;
- security/privacy/access review;
- observability and cost controls;
- deployment/runbook/rollback plan;
- release provenance and environment readback.

Exit gate:
- production target is exact;
- build/test/API/UI/log evidence covers material acceptance claims;
- failure, timeout, stale data, permission denial and rollback paths are exercised;
- no mock-only or local-only evidence is promoted to production acceptance.

### S6 — Acceptance & Handover

Required artifacts:
- Converge Matrix;
- client UAT record;
- known limitations and residual risk register;
- operator manual;
- training evidence;
- support/SLA/escalation contract;
- source/config/data ownership handoff.

Exit gate:
- every material claim maps to evidence;
- every negative requirement has negative evidence or an accepted gap;
- client acceptance identity/date/scope are recorded;
- operator can execute normal and recovery procedures without the vendor;
- closure state is `accepted`, `waiting_acceptance`, `blocked`, `rolled_back`, or `superseded`.

### S7 — Operations, Measurement & Ratchet

Required artifacts:
- service health and business KPI readback;
- incident/change log;
- monthly/quarterly review;
- renewal/expansion decision;
- reusable pattern and regression writeback.

Exit gate per cycle:
- KPI change is compared with baseline;
- failures become regression tests or process changes;
- reusable patterns are stripped of client facts before skill/template promotion;
- low-value or unsafe automation is removed or kept behind a gate.

## Engagement Manifest

Use `templates/delivery-engagement-manifest.json` as the machine-readable control surface. The checked-in template is intentionally RED until every placeholder is replaced; it is not acceptance evidence. A populated `in_progress` manifest may keep future stages `not_started` without pretending that the target completion boundary has already been reached.

Validate it with:

```bash
python3 ~/.hermes/skills/business/ai-agent-b2b-service/scripts/verify_delivery_workflow.py <manifest.json>
```

The verifier intentionally fails closed for:
- malformed or future-dated source metadata;
- missing absolute local evidence or a mismatched SHA-256;
- claim, stage, metric or artifact references to unknown IDs;
- unresolved contradictions;
- verified claims without scope/evidence, or accepted closures without any verified outcome or containing unverified/disputed claims;
- `accepted_risk` contradictions without an approver, acceptance date, compensating controls and known evidence references;
- active stages without owners, accepted stages without artifacts/evidence, and out-of-order stage progress;
- closure states that do not match the completion-boundary stage;
- S6/S7 progress without explicit client acceptance;
- unknown external action names, enabled credential/payment actions, or allowed actions without exact target, scope, grant reference, rollback and readback;
- public cases without `confidentiality=public`, publication-rights evidence and anonymization-review evidence;
- accepted client records without identity/date/scope and known acceptance evidence references;
- duplicate source, artifact, claim, contradiction, action, metric or risk IDs.

Evidence semantics:
- `truth_sources` are claim/stage/metric evidence IDs;
- `artifacts` are produced-output IDs referenced by stages;
- accepted stages must carry the stage-specific artifact types below, not generic labels:
  - S0: `qualification`;
  - S1: `baseline`;
  - S2: `spec`, `authority_matrix`;
  - S3: `solution_workspace`, `risk_register`;
  - S4: `pilot_evidence`, `test_evidence`;
  - S5: `release_provenance`, `runtime_evidence`, `rollback_plan`;
  - S6: `client_acceptance`, `handover`;
  - S7: `kpi_readback`, `operations_log`;
- an absolute local `ref` must exist and carry a matching lowercase SHA-256;
- URLs and logical artifact URIs remain declarations: this validator does not fetch or authenticate remote systems;
- a PASS means the declared snapshot satisfies these manifest gates, not that business code, CI, deployment, production behavior or client acceptance happened.

Boundary and closure semantics:
- `completion_boundary` is both the promised target and the maximum active stage; stages beyond it must remain `not_started` or `superseded`;
- `in_progress`: target boundary is declared, but no boundary acceptance is implied;
- `ready_for_review`: all prior stages are accepted and the boundary stage is ready for review;
- `accepted`: every stage through the boundary is accepted;
- `waiting_acceptance`: boundary is `acceptance`, S0–S5 are accepted, S6 is ready, and client acceptance is pending;
- `blocked`: at least one stage within the boundary is blocked;
- `rolled_back`: at least one stage within the boundary is rejected or superseded.

## Required Client-Facing Deliverables

Minimum diagnostic package:
- executive diagnosis;
- current-state process and Truth Source Map;
- opportunity/backlog shortlist;
- baseline/ROI measurement plan;
- proposed scope, exclusions and quote.

Minimum pilot package:
- all diagnostic artifacts;
- Spec and Authority Matrix;
- one working end-to-end slice;
- test/runtime evidence packet;
- pilot result and production go/no-go recommendation.

Minimum production package:
- all pilot artifacts;
- production implementation/integration;
- release, rollback, observability and security evidence;
- UAT, handover, training, SLA and known limitations;
- machine-readable final manifest and Converge Matrix.

## Claim Rules

Every claim must contain:
- `text`: exact claim;
- `scope`: component, workflow, environment and user state;
- `status`: verified, disputed, unverified or superseded;
- `evidence_refs`;
- limitations and negative evidence where material.

Forbidden examples:
- “100% complete” with no denominator;
- “production-ready” from local build/tests;
- “secure” from absence of observed errors;
- “event-driven” when the runtime is polling;
- “client accepted” without acceptance identity, date and scope.

Preferred example:

```text
At 390×844 in an anonymous local test session, the market-detail-to-trade route preserves the bounded identity fields; targeted lint, build and interaction smoke passed. Authenticated order placement, real-device behavior, remote CI and deployment are not covered.
```

## Authority Matrix

Classify actions:

- local read-only;
- local reversible write;
- repository commit;
- remote push/merge;
- deployment/release;
- external message/data transfer;
- credential entry;
- payment;
- production/destructive mutation.

Only local read-only and reversible local writes are open by default. External action names must be allowlisted. Every allowed external action must include exact target, scope/payload, grant reference, rollback/escape path and post-action readback. `credential_entry` and `payment_or_funds` are human-only and cannot be enabled by this Manifest. A manifest grant record is evidence about authority, not execution permission for the current Agent session; live execution still requires the applicable runtime/user authorization. Never type credentials or payment details.

## Change Control

A change request must record:
- source/requester;
- reason and business impact;
- scope delta;
- acceptance/evidence delta;
- price/schedule/SLA impact;
- authority impact;
- decision and approver.

Do not absorb scope growth into an existing milestone silently.

## Delivery State and Stop Rules

Valid stage states:
- `not_started`;
- `in_progress`;
- `blocked`;
- `ready_for_review`;
- `accepted`;
- `rejected`;
- `superseded`.

Stop or downgrade when:
- source facts conflict;
- acceptance denominator changes;
- real environment/credential/device evidence is missing;
- external target, rollback or readback is absent;
- data handling or legal/privacy approval is unresolved;
- client operator cannot perform handover procedures.

## Project-Progress Trial Pattern

To test the workflow against an existing project:

1. Snapshot the latest project state; do not mutate business code.
2. Extract truth sources, claims, stages, authority and metrics into a private manifest.
3. Add known contradictory claims as `contradictions` with `unresolved` status.
4. Run the verifier and require RED.
5. Reconcile by narrowing/superseding claims or producing stronger evidence; never delete history to get GREEN.
6. Run the verifier again.
7. A structural GREEN proves workflow consistency only. It does not prove production or client acceptance beyond the manifest completion boundary.
8. Keep the public case `not_ready` until anonymization and publication rights are verified.

## Converge Checklist

- Outcome: the promised client boundary exists and is operable.
- Scope: no whole-project claim exceeds its denominator.
- Evidence: every accepted claim has current source and runtime/test proof as applicable.
- Negative evidence: forbidden deletion, fallback, leakage and unauthorized side effects were checked.
- Authority: external actions have exact grants and readback.
- Handover: client operator can run and recover the workflow.
- Confidentiality: public material is anonymized and authorized.
- Operations: metrics, SLA, escalation and change control are active.

## Pitfalls

1. Selling internal governance vocabulary instead of client outcomes.
2. Confusing a successful pilot with production readiness.
3. Treating an evidence directory as proof without claim linkage.
4. Keeping stale percentages and newer module plans simultaneously as current truth.
5. Letting Profile files grow into unmaintainable session logs.
6. Calling polling “event-driven”.
7. Publishing client evidence without explicit rights and anonymization.
8. Making the client dependent on the consultant for ordinary operations.
