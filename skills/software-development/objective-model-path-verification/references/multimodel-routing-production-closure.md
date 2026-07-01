# Multimodel Routing Production Closure

Scope: production-grade model-router / multi-model execution loops where a host router selects producer and reviewer models for a downstream app or gateway.

Applicability: use when a task asks to move from advisory routing metadata toward a real producer + reviewer + certification loop. Anti-condition: do not use for simple model selection, one-off prompt fan-out, or non-production experiments where persisted replay/readback is irrelevant.

## Closure ladder

1. Separate advisory metadata from execution.
   - `routingDecision.selectedProvider/selectedModel` proves only what the router selected.
   - Production closure needs proof that the execution layer consumed the selected route.

2. Add actual execution readback.
   - Prefer structured fields such as `actualExecution.provider`, `actualExecution.model`, `source`, and `matchesRoutingDecision`.
   - Treat CLI and API paths as separate contracts. CLI may return plain text; if it can return JSON, parse structured readback without breaking text compatibility. API must be tested for both request override (`provider`, `model`, routing metadata) and response readback.

3. Persist the whole first-turn decision surface.
   - Idempotent replay must not re-invoke router, producer, or reviewer.
   - It should replay the stored assistant result plus routing/reviewer/actual-execution metadata so mobile clients see the same audit state on retry.
   - If persistence only stores assistant content and delivery state, the replay path is not production-grade for multi-model routing.

4. Keep reviewer execution distinct from arbitration.
   - A reviewer lane that returns `verdict`/`summary` is evidence, not a policy gate.
   - If reviewer output should block, retry, rewrite, or trigger an arbiter, land that as an explicit arbitration policy with tests and user-visible boundaries.

5. Treat router readiness as a governed gate, not a code bug by default.
   - Readiness failures such as diversity/dominance/quota-confidence can be correct fail-closed governance.
   - Auto-certification may clear quota/certificate blockers but still leave diversity warm-up requirements.
   - If the router reports many required non-dominant calls or `route_mutation_allowed=false`, stop at a human gate before consuming external model budget or changing the policy/window.

## TDD slices that work well

- RED: repeated mobile turn with the same idempotency key should return stored routing/reviewer/actual-execution metadata and should not call router/producer/reviewer again.
- RED: CLI structured JSON response with `actualExecution` should become assistant content plus `actualExecution.source=cli_structured_output`.
- RED: API path should send provider/model override and surface `actualExecution.source=api_response`.
- RED: readiness `FAIL_CLOSED` must short-circuit before producer/reviewer/executor calls.
- GREEN: keep plain-text CLI compatibility while adding structured parsing.
- GREEN: for budget-sensitive closure, add a **no-token-spend local executor verifier** that still runs the real router, records `routingDecision`, passes the selected provider/model into an execution seam, persists `actualExecution`, records reviewer-lane metadata, and proves idempotent replay. This verifier can clear the “metadata not consumed by execution” gap without claiming live model quality.
- VERIFY: run targeted gateway/router tests, router readiness gate, provider availability probe, persisted closure first-run + replay readback, production gate, full production verify, and one real provider smoke for the producer/reviewer chain if safe.

## No-token-spend closure verifier pattern

Use when the user asks to make smart routing “pass” but spending additional model calls is not explicitly authorized or the system already has a fresh autonomy certificate. The verifier should:

1. Load the real router readiness gate and fail closed before execution when it is not `PASS`.
2. Call the real `select_pair` / route selector for producer and reviewer.
3. Pass the selected producer `{provider, model}` into a local execution seam that emits deterministic content/readback and marks `externalModelCallExecuted=false`.
4. Persist `routingDecision`, `actualExecution`, `reviewerExecution`, arbitration policy, idempotency key, and readiness snapshot.
5. On replay, return the persisted surface without invoking router, producer, reviewer, or executor.
6. Label the boundary honestly: this proves route-consumption and replay contract, not live reasoning quality or provider budget handoff.

Pitfall: do not treat a no-token-spend verifier as a substitute for the existing autonomy certificate or a live provider smoke. It complements those artifacts: certificate/probe proves providers are callable; closure verifier proves the selected route is actually consumed and replayed by the execution contract.

## Human intervention packet

When readiness remains fail-closed after local reversible work, produce a small packet:

- Current readiness status and remaining blockers.
- Evidence artifact path for the readiness JSON.
- Whether any certificate/quota blocker was cleared.
- Exact external cost/authority request, e.g. number of non-dominant warm-up calls.
- Alternatives: authorize warm-up, adjust diversity policy/window, or accept fail-closed default.
- Safe default if no authorization is given.
