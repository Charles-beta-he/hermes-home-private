# Scientific Inquiry & Evidence Update — Self-Optimization SSOT

Date: 2026-07-19
Scope: local Hermes skill ecosystem only
Status: v1.1 second amendment implemented and locally verified after independent re-review found residual evidence/probe relation gaps; final independent re-review pending; full multi-model certification remains degraded by planner quorum

## Goal

Establish one class-level, cross-domain protocol for resolving material uncertainty through competing hypotheses, discriminating predictions, valid probes, calibrated evidence updates, intervention verification, reproduction, and bounded closure.

## Non-goals

- Replace `systematic-debugging`, `research`, `qian-meta-synthesis`, `objective-model-path-verification`, or `spec-stateful-sdd-workflow`.
- Turn ordinary lookups, translations, brainstorming, or routine implementation into a heavy research ceremony.
- Treat model agreement, expert agreement, test pass, correlation, or absence of evidence as proof.
- Grant authority for external dispatch, runtime mutation, deploy/publish/push, destructive action, credentials, payment, legal/medical/device action, or lifecycle writes.

## Source facts and boundaries

- Existing capabilities provide pieces of the loop but no indexed class-level owner was found for the full contract.
- `systematic-debugging` owns ordinary software root-cause investigation.
- `research` owns source and literature discovery.
- `qian-meta-synthesis` owns heterogeneous expert/source synthesis and preserved dissent.
- `objective-model-path-verification` owns objective/path selection and consequence verification.
- `spec-stateful-sdd-workflow` owns canonical stateful specification and evidence-gated delivery.
- The new skill owns only the shared epistemic invariant across these domains.

## Chosen path

Create `workflow/scientific-inquiry-evidence-update` as a bounded class-level skill with:

- Lite, Standard, and Strong modes;
- a state machine from framing through ratification;
- multiple working hypotheses and a null/alternative hypothesis;
- explicit predicted observations and falsifiers;
- probe validity and evidence-update rules;
- separate intervention and reproduction gates;
- a JSON packet template, valid example, structural validator, unit tests, theory map, and routing eval matrix;
- one-way body-level integration pointers from neighboring skills, avoiding metadata cycles.

## Canonical artifacts

- `skills/workflow/scientific-inquiry-evidence-update/SKILL.md`
- `skills/workflow/scientific-inquiry-evidence-update/templates/inquiry-packet.json`
- `skills/workflow/scientific-inquiry-evidence-update/assets/example-inquiry-packet.json`
- `skills/workflow/scientific-inquiry-evidence-update/scripts/validate_inquiry_packet.py`
- `skills/workflow/scientific-inquiry-evidence-update/scripts/test_validate_inquiry_packet.py`
- `skills/workflow/scientific-inquiry-evidence-update/references/theory-to-engineering-map.md`
- `skills/workflow/scientific-inquiry-evidence-update/evals/prompts.csv`
- `skills/workflow/scientific-inquiry-evidence-update/evals/baseline.md`

Integration pointers:

- `skills/software-development/systematic-debugging/SKILL.md`
- `skills/software-development/objective-model-path-verification/SKILL.md`
- `skills/software-development/spec-stateful-sdd-workflow/SKILL.md`
- `skills/workflow/qian-meta-synthesis/SKILL.md`

## Evidence requirements

Closure requires fresh evidence for:

1. Skill frontmatter and conditional accessory loading.
2. Valid example accepted by the validator.
3. Invalid/incomplete packets rejected.
4. Unit tests passing.
5. Positive, neighbor, forbidden, and no-load routing cases present.
6. New skill introducing no graph cycle, excessive-depth chain, missing dependency, or ambiguous dependency.
7. Integration pointer readback.
8. Independent review with no unresolved P0/P1.
9. Scoped Git readback preserving unrelated staged blobs.

## Current evidence

- Validator unit tests: 28 passed after schema 1.1 migration and adversarial evidence/probe relation repair.
- Valid schema 1.1 example: accepted with zero errors.
- Incomplete schema 1.1 template: rejected with 21 structural/provenance errors until populated.
- Routing matrix: 10 cases, IDs unique, required fields present; actual cross-model routing remains advisory/unexercised.
- Scoped graph projection: no cycle, excessive depth, missing dependency, or ambiguous dependency involving the new skill.
- Global graph still reports unrelated pre-existing depth/missing/ambiguous violations; this task does not claim global graph health.
- Integration pointer search found all four intended neighbors.
- Fresh `skills_list(category="workflow")` readback discovered both `qian-meta-synthesis` and `scientific-inquiry-evidence-update`; current-profile discovery is active.
- Independent review state v3 grounded 6/6 claims with evidence coverage `1.0`, including direct readback of conditional theory-map loading. It has no unsupported or contradicted claims, no unresolved issue-ledger entries, no remaining evidence requests, and three ratification approvals (`gpt-5.5`, `mimo-v2.5-pro`, `deepseek-v4-pro`).
- The final certification manifest remains `degraded_not_certified`: only 1/3 planner calls completed successfully, below the 2-planner minimum, even though all three discussion participants approved the constrained truth-grounded/no-action package. This is an infrastructure/quorum boundary, not a full multi-model certification pass.
- Final review artifacts: `tick-20260719-042324-575821-p65939-24ede8ed-53e9c2ae/discussion_result.json` and `tick-20260719-042324-575821-p65939-24ede8ed-53e9c2ae/final/certification_manifest.json`.
- A delayed pre-implementation architecture audit preferred a `research` reference over a new class-level skill until independent triggers and routing evidence exist. Projected onto the completed artifact, its useful promotion criteria are now represented by 4 positive, 3 neighbor, 2 forbidden, and 1 no-load static cases plus explicit neighbor boundaries. The dissent remains material because the fresh skill-loader/model routing harness has not run; failure of that harness, route stealing, or evidence that the artifact adds no behavior beyond `research` is the explicit demotion/absorption trigger.
- Delayed independent terminal review `deleg_d4078b85` returned `AMEND / 暂不 ratify` with 0 P0, 4 P1, and 4 P2. The first v1.1 amendment addressed mode cardinality, schema/enums/basic cross-references, the provenance ledger, freshness, wording, and safe P2 items. Metadata dependency edges were intentionally not added because one-way body pointers preserve the already-verified scoped acyclic graph.
- Independent re-review `deleg_d1f720ab` found no new P0/P1 but correctly demonstrated two residual fail-open paths: cross-probe evidence could update hypotheses whose claims it did not cover, and fresh verified evidence from an `invalid_probe` could ratify closure. The second amendment now requires every update evidence item to match the update probe, the cited claim union to cover all updated hypotheses, hypothesis updates to use a `valid_result` probe, and ratification evidence to come from a `valid_result` probe. Two adversarial classes plus the ratification message regression are covered in the 28-test suite. Final independent re-review remains required before ratification.

## Open limits

- Fresh cross-model routing evaluation has not yet been executed.
- Global skill graph debt remains outside this scope.
- Full multi-model certification remains unavailable until a fresh run reaches planner quorum.
- Scoped local commit/readback completed; no push, deploy, publish, or external dispatch is included.

## Rollback

If the new skill steals neighbor routes or adds no incremental behavior:

1. absorb the useful theory/protocol material into an existing umbrella;
2. remove the candidate using skill deletion with an explicit `absorbed_into` target;
3. remove the four body-level integration pointers;
4. rerun structural, routing, graph, and readback checks.
