# Async certification follow-up and non-mainline rollout

Use this pattern when a multi-model review finishes asynchronously after docs/plans were already written, or when architecture direction is plausible but not truth-certified.

Key rules:
- Model fan-out success is not certification. Treat `models_consulted` / `discussion_result.json` as participation evidence only.
- Truth comes from the certification artifacts: `truth_assessment`, `certification_status`, `can_claim_complete_certification`, `agreement_matrix_min`, and unresolved issue lists.
- If later background output downgrades confidence (for example `not_certified`, `needs_link_review`, `evidence_coverage=0.0`), immediately reopen the written ADR/plan and downgrade wording from adopted/decided to candidate/proposed/preferred direction.
- Record the downgrade explicitly in the plan/log so later sessions do not treat weak consensus as certified truth.

Recommended response pattern:
1. Read `discussion_result.json` and `final/certification_manifest.json`.
2. Separate three layers in your write-up:
   - participation: which models ran
   - weak consensus: direction many models lean toward
   - certified truth: only what passed the gate
3. If certification failed, state the exact blockers (`needs_link_review`, low agreement threshold, unresolved high-severity issues).
4. Preserve low-risk progress by landing contract/adaptor/test work that does not depend on disputed claims.
5. Defer mainline wiring (for example `conversation_loop.py`) until link review / certification disputes are resolved.

Good wording:
- "candidate long-term direction"
- "weak consensus, not truth-certified"
- "non-mainline rollout first"
- "adapters/contracts landed; default runtime path unchanged"

Avoid wording like:
- "certified architecture decision"
- "consensus proved"
- "safe to wire into main loop" unless the certification artifacts actually support it.

Useful boundary for architecture work:
- Safe now: new state contracts, stage wrappers, fail-soft pipeline scaffolding, targeted tests, docs/ADR updates.
- Wait for evidence: declaring canonical entrypoints, changing default routing/policy behavior, wiring the real conversation loop, or promoting candidate architecture to settled truth.
