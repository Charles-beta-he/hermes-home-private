# Taskpool concurrency certification pattern

Use this as an adjunct when multi-model certification is applied to taskpool concurrency expansion or similar control-plane capacity changes.

## Lessons

1. Route by verification surface, not just by task tier.
   - Architecture/control-plane model: state machine, locks, pool separation.
   - Adversarial/safety model: false completion, stale claims, boundary collisions, quota unknowns.
   - Runtime/implementation model: concrete files, tests, read-only vs mutation boundary.

2. Separate statuses in the final report.
   - `fanout_quorum_met` means enough planners returned.
   - `truth_can_certify=true` means claims are grounded in evidence.
   - Final `discussion_status=certified` / manifest `can_claim_complete_certification=true` is still required before saying “fully certified”.
   - If final discussion is `not_certified`, report “multi-model routed, truth-grounded, not fully certified”.

3. Avoid claim/evidence ID mismatch.
   - If the state builder normalizes claim IDs to `C-001`, evidence must use `supports: ["C-001"]`.
   - `supports: ["C1"]` can leave `evidence_coverage=0.0` despite valid raw evidence.

4. Fresh readback can downgrade the plan.
   - If earlier evidence suggested selected_count=8 but fresh dry-run shows selected_count=1 or resource_ceiling=2, revise the recommendation immediately.
   - Do not carry forward stale optimistic capacity claims.

5. If models propose implementation against unlocated targets, do a file-discovery certification slice first.
   - Examples of invalid targets: “provider health/routing implementation file to be located before edit”.
   - Bind changes to exact files/functions before implementation authorization.

6. Architecture-only/no-action certification is valid but limited.
   - It may certify a direction or next guard/metrics slice.
   - It must not authorize config mutation, max-agent raises, or lifecycle completion.

## Recommended taskpool concurrency packet shape

Claims should be scoped and evidence-linked:

- Current safe concurrency / cap, supported by config + dynamic tick summary.
- Candidate supply after lane priority, supported by parallel-dispatch dry-run.
- Boundary/provider/review blockers, supported by selfcheck and tick resource probes.
- Concrete next implementation surfaces, supported by search/readback evidence.
- Explicit non-goal: no concurrency raise in the certification run.

## Output phrasing

Use:

- “fanout/truth grounded but not fully certified” when final ratification fails.
- “next certifiable slice is read-only readiness/guard instrumentation” when capacity inputs are degraded.
- “do not raise persistent concurrency now” when selected_count, quality_slots, provider confidence, or boundary warnings fail.

Avoid:

- “multi-model certified” unless the final certification manifest allows it.
- “safe to raise to 6/8” based only on dry-run candidate availability.
- Treating transient provider timeouts as durable bans.
