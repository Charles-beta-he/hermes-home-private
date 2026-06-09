# Design Review Panel — Multi-Model Variant

When the goal is to review an architecture/design proposal (not certify code changes), use a lighter variant of the certification round protocol.

## Differences from Certification Round

| Aspect | Certification Round | Design Review Panel |
|--------|-------------------|-------------------|
| Input | manifest_delta with evidence bundle | Design proposal + context |
| Gate | truth_gate, evidence_coverage=1.0 | No truth gate — opinion-based |
| Output | approve/amend/reject with evidence refs | Structured JSON with critiques, additions, removals |
| Models | Typically 2-3 reviewers | 3 models with distinct roles |
| Blocking | Unresolved issues block approval | Consensus emerges from independent reviews |

## Model Role Assignment

Each model gets a distinct lens to prevent echo-chamber agreement:

- **Architect model** (e.g., Claude Code): Focus on system design, failure modes, concurrency, security. Reviews against existing infrastructure patterns.
- **Implementation model** (e.g., DeepSeek): Focus on code details, error handling, retry strategies, race conditions. Produces pseudocode sketches.
- **User-perspective model** (e.g., MiMo): Focus on simplicity, user workflow fit, over-engineering detection. Asks "what would the actual user care about?"

## Output Format

Each model produces independent JSON:
```json
{
  "model": "model-name",
  "overall_assessment": "approve|amend|reject",
  "critiques": [{"area": "...", "severity": 1-5, "issue": "...", "recommendation": "..."}],
  "additions": ["..."],
  "removals": ["..."],
  "reasoning": "<=600 chars"
}
```

## Synthesis Rules

1. **Collect all critiques** — group by area, keep highest severity per area
2. **Find consensus** — if all 3 models flag the same issue, it's a definite blocker
3. **Find disagreements** — if models disagree, the user-perspective model's opinion carries weight for UX decisions, the architect's for system design
4. **Produce phased plan** — if models disagree on scope (e.g., "too complex" vs "need more"), propose MVP + enhancements

## Pitfalls

- Do NOT give all models the same prompt — role differentiation is critical for useful diverse feedback
- Do NOT ask models to vote on each other's outputs — independent reviews only
- If all 3 models agree, the consensus is very strong — rarely wrong
- If 2/3 agree and 1 dissents, investigate the dissent before dismissing
- The user-perspective model often catches over-engineering that technical models miss

## Example: Problem Pattern Registry (2026-05-29)

All 3 models voted "amend" on a proposed problem-pattern registry:
- Claude Code: flagged injection risk, concurrency, FD exhaustion
- DeepSeek: specified retry/backoff, oscillation detection, audit trail
- MiMo: said "over-engineered, start with markdown file"

Consensus: detect-and-report over auto-fix, phased implementation (markdown → cron → JSON).
