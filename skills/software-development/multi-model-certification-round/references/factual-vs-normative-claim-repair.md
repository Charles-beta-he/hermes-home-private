# Factual vs Normative Claim Repair for Certification

Use this when an initial multi-model packet fails because truth-gated claims mixed together:
- repository facts
- architecture recommendations
- implementation-change proposals

## Durable repair recipe

1. Keep only directly provable facts in `claims`.
   - symbol/module existence
   - tested/local integration
   - scoped main-path presence or absence

2. Narrow wording to the strongest statement the evidence actually proves.
   - Good: "tested/local integration"
   - Too strong unless proven: "live canonical main-path integration"

3. Explicitly attach evidence links with `supports`.
   - Missing links often cause `needs_link_review` even when the evidence text is present.

4. Move recommendations out of truth-gated claims.
   - Put long-term architecture direction in ADR/design rationale instead of factual certification scope.

5. If the round is certification-only, say so in constraints.
   Suggested constraints:
   - evidence ratification only
   - no code changes requested
   - if sufficient, vote noop / no_action_certification

6. Scope negative wiring claims precisely.
   - Example: "not wired into `run_agent.py` + `agent/conversation_loop.py`" is safer than claiming global non-use everywhere.

## Expected good outcome

A repaired packet should converge to:
- `truth_gate.can_certify_truth == true`
- all factual claims `verified_by_evidence`
- `planner_patch_summary.certification_intent == no_action_certification`
- certified discussion/manifest with zero rejects
