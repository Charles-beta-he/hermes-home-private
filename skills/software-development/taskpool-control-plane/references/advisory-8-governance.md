# Advisory-lane concurrency governance

Use when promoting or stabilizing Hermes taskpool concurrency for a lane-scoped advisory pool, especially when `max_parallel_agents` is already raised but live running count does not stay at the target.

## Applicability

- Taskpool concurrency is lane-scoped, e.g. `parallel_dispatch_lane=advisory`.
- Readiness gates include resource/quality/API quota/boundary/handoff backlog signals.
- Provider calls include local/OAuth/subscription providers that may succeed without quota headers.
- The goal is governed local taskpool operation, not global concurrency, deploy/push, external dispatch, payment, credential entry, or destructive cleanup.

## Anti-conditions

- Do not treat a transient task shortage as proof that the configured concurrency cap failed.
- Do not claim exact remaining quota for providers that expose no quota/balance headers.
- Do not bypass human-escape, lifecycle, proof, or boundary gates just to reach a numeric running count.
- Do not persist a task/session narrative; record only the reusable gate/diagnostic pattern.

## Procedure

1. Separate four layers before changing anything:
   - Config cap: `max_parallel_agents`, `dynamic_max_parallel_agents`, lane filter.
   - Capacity gates: resource ceiling, quality slots, API slots, quota confidence.
   - Pool supply: dispatchable lane count, active count, selected count, projected active count.
   - Safety/debt gates: boundary warnings/conflicts, stale claims, handoff backlog, human escape.
2. Prove the cap with a read-only lane dry run before autorun. A valid preflight should show the requested lane, selected/projected active count, boundary readiness, and zero stale claims.
3. If provider confidence fails for no-header subscription/OAuth providers, refresh real success evidence, but normalize it as documented no-header policy evidence:
   - status `ok`
   - observability `estimated_subscription_window`
   - quota type `documented_no_quota_header_policy`
   - confidence bounded (not exact)
   - no remaining token/request/USD claims
4. Preserve exact/safety evidence precedence:
   - Exhausted/rate-limited/malformed snapshots can replace optimistic estimates.
   - Fresh exact balance/rate-window evidence should not be overwritten by empty response headers.
   - Successful no-header calls for documented providers should not downgrade recent documented budget evidence to `unknown`/`unobservable`.
5. Add or inspect boundary capacity diagnostics when target concurrency is not reached:
   - slot deficit
   - unique selected boundary count
   - unique blocking boundary count
   - top limiting boundaries
   - recommended actions such as refill/unblock lane supply or split conflict groups.
6. Treat successful `claim_count == N` separately from running worker count. A claim can be followed by human-escape or worker trigger SKIP; read back worker state and task states before declaring live concurrency.
7. If human-escape trips, do not silently bypass it. Read envelope stats, identify post-ack failures/blocks, verify no live timeout/orphan remains, then only advance the escape watermark if the reviewed rows are terminal/auditable and the operation is within the user-authorized local boundary.
8. After any governance code change, run focused tests for the changed gate and a live readback of the current lane. Classify unrelated legacy test failures explicitly.

## Verification checklist

- `py_compile` passes for changed scripts and tests.
- Focused model-quota tests cover no-header success normalization and anti-downgrade behavior.
- Focused boundary/readiness tests cover capacity diagnostics for below-target concurrency.
- Quota confidence for the selected model set is PASS or the remaining failure is a true provider boundary.
- Dispatch tick shows whether blockers are provider confidence, pool supply, boundary, or backlog — not an ambiguous generic fail.
- Final report distinguishes:
  - configured concurrency cap,
  - readiness PASS/FAIL,
  - claimed count,
  - live running count,
  - active lane(s),
  - remaining blockers.

## Common pitfalls

- “8 configured” is not the same as “8 live workers.” Verify selected/projected/claimed/running separately.
- A discussion can be truth-grounded but not certified because of no-op-vs-change planner conflict; report the degraded certification boundary instead of calling it certified.
- Response-header snapshots with no quota fields are low-value evidence; do not let them erase fresher exact or documented-policy budget evidence.
- When the pool only has same-boundary advisory work left, more cap will not create more safe parallelism; unblock/refill/split boundaries instead.
