# Mainline review-package then guarded landing

Use this pattern when a local Hermes enhancement is already implemented off-mainline, but the risky step is wiring it into a canonical runtime seam.

## Why split the work

Trying to certify both of these in one packet causes avoidable ambiguity:
- factual claims about seam existence, gating feasibility, and advisory-only boundaries
- normative approval to implement immediately

That ambiguity often shows up as noop-vs-change disagreement in multi-model certification.

## Recommended sequence

1. Build a review package only.
   - Identify the canonical seam.
   - State exact insertion point.
   - Separate factual claims from design claims.
   - Define non-goals for v1.

2. Certify the package as no-action.
   - Facts: seam exists, gate can be default-off, v1 can remain advisory-only.
   - Design claims: best seam, safest rollout shape.
   - Do not ask the truth gate to approve code changes in this round.

3. Land the seam with TDD.
   - RED tests first: disabled, enabled, exception fail-soft.
   - Add top-level config gate.
   - Add env kill switch.
   - Execute once per turn at the certified seam.
   - Stash runtime state only; do not force provider/model/tool/memory side effects.

4. Verify the guarded landing.
   - Disabled path unchanged.
   - Enabled path runs exactly once.
   - Exceptions degrade to no-op, not turn failure.
   - Downstream consumers remain optional follow-up work.

## Hermes-specific notes from this session

- For cognitive pipeline mainline wiring, the successful shape was:
  - config key: `agent.cognitive_pipeline.enabled`
  - env override: `HERMES_COGNITIVE_PIPELINE_ENABLED=1`
  - once-per-turn execution in `agent/conversation_loop.py`
  - advisory-only state stashing on the agent
  - fail-soft on pipeline init and per-turn execution

- The implementation became straightforward after the certification packet was reframed as review-package-only rather than implied implementation authorization.
