# Profile-driven surface router coverage

Scope: Hermes-style multi-model routers that claim theoretical coverage across verification surfaces. Applicability: use when raising routing coverage, auditing smart routing, or connecting model capability profiles to producer/reviewer selection. Anti-condition: do not use theoretical coverage as production readiness; live provider auth, quota confidence, diversity/dominance, and budget-handoff gates remain separate fail-closed checks.

## Pattern

1. Define a single capability profile with each surface's `implementers`, `verifiers`, optional `fallback_verifiers`/`arbiters`, and `final_evidence` classes.
2. Make the router consume the profile directly before generic keyword/specialist heuristics.
   - `task_class` should resolve to a declared surface.
   - Producer routes prefer `implementers` first.
   - Reviewer routes prefer `verifiers` / `fallback_verifiers` first.
   - Non-model gates such as `hermes_evidence_gate` must be representable as a route with `model: null`, not silently replaced by a model.
3. Every route decision that comes from the profile should carry inspectable metadata:
   - `profile_surface`
   - `profile_role`
   - `routing_scope: profile_surface`
   - `required_evidence`
   - declared profile models or gate id
4. `select_pair` should preserve the same metadata at pair level so producer/reviewer separation can be audited.
5. Keep older availability, quota, capability, cost, exploration, sticky, and diversity gates intact. Profile coverage expands the theoretical route map; it must not weaken runtime readiness.

## TDD / verification

- RED: for every declared surface, call the real router and assert `profile_surface == surface`, `routing_scope == profile_surface`, and `required_evidence == final_evidence`.
- RED: for a surface with distinct verifier, assert `select_pair` picks the profile verifier in the reviewer lane.
- GREEN: implement only enough profile loading/resolution and metadata propagation to pass.
- Regression: run the router quota/diversity/closure suites.
- Coverage audit: calculate `covered_surfaces / declared_surfaces`; 100% theoretical coverage requires all declared surfaces to be resolved by profile metadata, including non-model evidence gates.
- Readiness audit: rerun live readiness/probe and report it separately. `FAIL_CLOSED` can be correct even when theoretical coverage is 100%.

## Pitfall

Do not describe `100% theoretical coverage` as `production healthy` or `autonomy certified`. If readiness still fails due to dominance, quota confidence, unavailable providers, or stale autonomy certificates, report the boundary and next authority-gated work separately.
