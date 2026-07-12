# Structured semantic authority gates

## Scope

Use this pattern when a task/control-plane executor consumes a structured semantic envelope to choose a lane, brain/profile, task class, review mode, learning scope, or executable lifecycle.

Applicability: the envelope is intended to replace surface-text heuristics as runtime authority, especially in strict task roots or governed queues.

Anti-conditions:

- Do not require executable authority for read-only reports or compatibility inspection that never enters claimed/running/review/certified/done.
- Do not treat a model/verifier vote as authority for external write, deploy, payment, credentials, destructive action, or publication.
- Do not copy project-specific paths, registry rows, or current test counts into the class-level contract.

## Authority separation

A valid route is not an execution grant. Keep these decisions distinct:

1. Schema validity: is the envelope well-typed, sourced, confident, and known?
2. Routing authority: may it select lane/brain/profile/task class?
3. Execution authority: is `policy.may_execute` explicitly true?
4. Learning authority: may it write task/project learning, or must durable Memory/Skill/ratchet writeback remain gated?
5. Side-effect authority: does an independent exact-target grant exist for external/high-risk action?

For strict executable states, require both:

- `decision == route`
- `policy.may_execute is True`

Otherwise fail closed with a stable machine-readable reason. Apply the same helper in dispatchability and every executable lifecycle transition. `force` must not suppress semantic/authority failures.

If advisory work needs lifecycle tracking, use a state/path that does not imply execution authority. Do not reuse executable states merely because the envelope routed successfully.

## Envelope validation checklist

Reject rather than coerce:

- missing required keys;
- empty/non-string outcome;
- bool where a numeric confidence is expected;
- list fields supplied as string/dict/scalar;
- empty or non-string list items;
- unknown capability or intent;
- malformed routing or multimodel objects;
- capability/routing/profile/task-class conflicts;
- unknown registry schema or malformed registry rows.

Validate the capability registry with the same canonical validator used by the evaluator and readiness. A shallow readiness check that only tests field presence can produce false PASS.

## Negative test matrix

At minimum prove:

- identical envelope + adversarial/negated/quoted surface text gives identical authority;
- identical text + different valid envelopes gives constrained, different routing;
- malformed nested types and empty items all fail closed;
- missing/invalid envelope cannot pass intake, `is_dispatchable`, manual claim, transitions, or `force`;
- valid route with `may_execute=false` cannot enter any executable state;
- safe delivery with local/no side effects can pass the semantic execute gate;
- external write remains authority-blocked even when routing is valid;
- forbidden multimodel mode cannot be overridden by retry/stale runtime triggers unless the formal contract explicitly defines that override;
- durable reusable learning remains evidence/writeback-gated;
- a non-empty queue fixture covers valid, missing, invalid, and route-without-execute-authority cases; do not certify only from an empty live queue.

## Verification loop

1. Run focused semantic contract and integration tests.
2. Run the full orchestrator/control-plane regression suite.
3. Run compile/schema/diff checks.
4. Read back readiness, including registry-validation failures and live-queue observation.
5. Exercise an isolated lifecycle/proof-gate path where feasible.
6. Generate a stable code/config review artifact that excludes self-referential evidence docs.
7. Ask an independent verifier to construct adversarial probes against the latest code, not to review stale summaries.
8. Treat every real counterexample as a blocker, patch it, rerun all affected evidence, and request a new latest-slice vote.
9. Promote to scoped certification only when the latest verifier reports no blocking/material issue and the evidence document is read back after update.

## Common pitfall

A green readiness result with an empty queue proves safe idle observation, not active-task enforcement. Pair it with explicit non-empty fixtures and direct lifecycle probes. Likewise, broad regression counts do not replace a targeted route-vs-execute test.
