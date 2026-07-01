# Capability-boundary routing and evidence-authoritative acceptance

Use this when designing or reviewing a Hermes main-loop or taskpool multi-model path where the question is not merely "did enough models vote?" but "which model is qualified for this verification surface, and what non-model evidence is required?"

## Core lesson

Multi-model certification should not default to all-model voting for every task. Route by verification surface first, and vote only when surfaces overlap or risk is high.

Recommended surface mapping:

- `ui_visual`: Gemini as visual verifier; objective evidence still requires screenshots, browser/DOM snapshots, console/network checks, and interaction smoke.
- `code_correctness`: GPT/Codex may implement; DeepSeek should review; final evidence is diff + tests/build/runtime smoke.
- `architecture_boundary`: Claude may draft/arbiter; DeepSeek should critic; final evidence is repo/config references, risk matrix, and rollback path.
- `completion_claim`: Hermes evidence gate is the authority; models are advisory only.

## Role separation rule

The producer/implementer model must not be the primary verifier for certification-critical claims.

- Implementer self-report may explain intent or summarize work.
- Implementer self-report must not count toward certification quorum.
- Prefer a different model; prefer a different provider when an equivalent verifier exists.
- If no independent verifier is available, report `degraded_not_certified` or `advisory_only`, not certified.

## Evidence-authority rule

Model judgment is advisory unless it cites objective evidence. At least one non-model evidence source is required for any acceptance claim.

Reject or downgrade to advisory when:

- votes have no `evidence_refs`;
- evidence refs point to missing or stale evidence;
- all available approvals are from the implementer;
- a model-only panel approves without tool/readback evidence;
- a visual model approves UI without screenshots/browser/interaction/console evidence;
- model quorum passes but tests/build/API/browser readback fail.

## Overlap voting trigger

Use overlap voting when any of these is true:

1. Two or more verification surfaces are involved, e.g. UI component work combines `ui_visual`, `code_correctness`, `interaction_runtime`, and `accessibility`.
2. Risk tier is T2 or higher.
3. A specialist verifier reports severity >= 3.
4. Tool evidence contradicts model judgment.
5. The user requests production-grade, A+/uIMax, long-term stable, or multi-model certified acceptance.
6. The capability profile is uncertain or a preferred provider degraded.

Voting is surface-weighted, not simple majority. Each required surface must have no blocker and must cite its objective evidence.

## Minimal structured verdict

Each model/verifier vote should include:

```json
{
  "model": "deepseek-v4-pro",
  "role": "code_reviewer",
  "reviewed_surface": "code_correctness",
  "is_implementer": false,
  "vote": "approve|amend|reject",
  "severity": 1,
  "claim_ids_checked": ["C-001"],
  "evidence_refs": ["E-test-output"],
  "unsupported_claims": [],
  "blockers": [],
  "best_within_constraints": true
}
```

If `is_implementer=true`, set `vote_counts_for_certification=false`.

## Acceptance statuses

Use distinct statuses rather than collapsing everything into done:

- `certified`: independent specialist/quorum passes and evidence gate passes.
- `certified_with_minor_risks`: evidence complete, no severity >= 3 blocker.
- `tool_verified`: objective tool evidence passed, but no multi-model certification claim.
- `advisory_only`: model advice exists but objective evidence, refs, or independent verifier are missing.
- `degraded_not_certified`: quorum/provider/capability route failed.
- `not_certified` or `rejected`: blocker, contradiction, self-certification, or failed evidence gate.

## Implementation contract pattern

For Hermes runtime integration, land this as a default-off/advisory contract before blocking the main loop:

1. Add a capability profile SSOT with models, surfaces, role separation, overlap voting, and acceptance governance.
2. Add a router that returns `surface_routes`, `required_evidence`, `certification_participants`, and `truth_authority=hermes_evidence_gate` without calling external models.
3. Add an acceptance gate that rejects model-only approvals, self-certification, missing evidence refs, and unknown evidence refs.
4. Wire the conversation loop only to record advisory route metadata first; do not block or fan out models until separate authorization.
5. Verify with focused tests and CLI smoke proving model-only approval downgrades to advisory and independent evidence-backed approval can certify.

## Anti-conditions

Do not capture project-specific paths, branches, commit hashes, or provider setup failures as universal rules. Store those in project profiles or scoped acceptance records. This reference is for the reusable procedure and gate semantics only.
