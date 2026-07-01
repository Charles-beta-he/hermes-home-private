# Open-source absorption module registry pattern

Use when the user asks to梳理/扩展/治理 previously learned open-source project tasks, or asks whether the results are synced to local brain and whether there is a formal follow-up flow from minimum slice to durable delivery.

## Objective

Turn scattered source-review / repo-learning / absorption tasks into a reusable module system without pretending that a summary is implementation.

## Landing-zone classifier

- Historical task details remain in the original task notes.
- Machine-readable projection belongs in a registry JSON, not memory.
- Human operating map belongs in a compiled markdown note.
- Local-brain sync should be a compiled knowledge entry plus a governance/process note.
- Concrete future engineering work becomes taskpool candidates, not fake skills.
- Stable user preferences go to memory/user profile only if they are general and durable.

## Recommended artifacts

For a Hermes-style local setup, adapt paths but preserve roles:

- Registry JSON: `~/.hermes/notes/open-source-absorption/module-registry.json`
- Human map: `~/.hermes/notes/open-source-absorption/open-source-absorption-modules.md`
- Verifier: `~/.hermes/notes/open-source-absorption/verify_registry.py`
- Local-brain compiled knowledge: `~/Documents/brain/03-知识库/open-source-absorption-modules.md`
- Local-brain governance flow: `~/Documents/brain/06-治理与评审/open-source-absorption-delivery-flow.md`

## Procedure

1. Define the top-level module count and anti-fragmentation rule before scanning. Example: keep 18 top-level modules; route cross-domain areas like Data Agent/MLOps under evidence/vision modules rather than creating a 19th top-level module.
2. Scan historical tasks with a strict source-learning filter:
   - include titles/files with evaluation, learning, source-review, absorption, repo, GitHub, open-source, README, license, etc.;
   - exclude ordinary product/project tasks unless they explicitly contain source-review/repo-learning evidence.
3. For each module, record:
   - `id`, human name, priority tier, scope;
   - stable target / desired end state;
   - next verifiable slice;
   - representative task refs and status counts.
4. Add a verifier that checks:
   - schema version;
   - exact module count;
   - unique module ids;
   - representative task paths exist;
   - matched refs and primary refs are nonzero and internally consistent.
5. Sync to local brain as compiled knowledge, not as a new authority source. Include exact pointers back to the registry and original task notes.
6. Write a governance flow for minimum-slice-to-durable-delivery:
   - M0 Intake: source enters with URL/repo/license/uncertainty;
   - M1 Source Review: read-only source validation, no third-party execution;
   - M2 Module Mapping: primary module plus optional secondary tags;
   - M3 Minimal Verifiable Slice: objective, I/O contract, safety boundary, proof requirement, rollback, verifier/readback;
   - M4 Implementation Landing: skill/doc/script/code/dashboard depending on impact;
   - M5 Acceptance/Ratification: correctness, grounding, regression, safety, rollback;
   - M6 Durable Promotion: promote only after evidence to skill/profile/ADR/dashboard/automation.
7. If committing generated notes, expect local git guards to flag secret-like variable names in prose. Redact or rename generic words that trigger scanners, but do not weaken the guard or bypass policy unless the user explicitly authorizes that scope.

## Verification checklist

- [ ] The registry is machine-readable and has a deterministic verifier.
- [ ] Original task notes remain the historical SSOT.
- [ ] The local-brain page is explicitly a compiled knowledge/index layer.
- [ ] The governance note distinguishes plan, minimum verifiable slice, implementation, ratification, and durable promotion.
- [ ] Future work is represented as taskpool candidates/proposals, not as completed skills.
- [ ] No memory entry stores bulky project/task state.

## Pitfalls

- Do not treat a module map as completed implementation.
- Do not over-broaden filters so ordinary product tasks become repo-learning evidence.
- Do not create one narrow skill per source repo; update an umbrella and add references.
- Do not let a dashboard become lifecycle owner; it should remain read-only unless a governed write gate exists.
- Do not let `/goal` or hooks auto-promote external project lessons into taskpool/mission/cron without a proof and permission boundary.
