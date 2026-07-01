# Mainloop/multi-model certification boundary: routed, truth-grounded, not certified

Use when a multi-model run produced planner artifacts but final certification did not pass.

## Distinguish four layers

1. Route/shadow route: capability selection only; no model panel and no certification.
2. Fan-out quorum: enough planners returned. This can be `multi_model_certified=true` only for the fan-out surface.
3. Truth gate: factual claims are grounded in non-model evidence, e.g. `evidence_coverage=1.0` and `can_certify_truth=true`.
4. Final ratification/certification: requires approvals, `best_within_constraints=true`, no unresolved severity>=3 issues, sufficient agreement, and resolved noop-vs-change intent.

Never collapse these into one word. A safe report may be:

`multi-model routed / fanout quorum met / truth-grounded / not fully certified`

## Required wording

- If all model votes are `amend`, say `not certified` even when every model participated.
- If the discussion status is `not_certified`, do not claim a certified plan.
- If `fanout_quorum_met` and `truth_grounded` are true, you may use the plan as an evidence-grounded amend-stage roadmap.
- If `planner_patch_intent=unresolved_noop_vs_change`, require a follow-up packet that separates advisory no-op from concrete implementation authorization.

## Pitfall: claim-id normalization

When building a state with claims and evidence, ensure `evidence[].supports` exactly matches canonical claim ids consumed by the truth gate.

Bad:
- claim id normalized to `C-001`
- evidence supports `C1`

Result:
- evidence exists but `evidence_coverage=0.0`
- claims marked unsupported
- models may correctly diagnose schema mismatch instead of missing evidence

Good:
- claim: `C-001: ...`
- evidence supports: `["C-001"]`

Then rerun the state/fanout before interpreting model disagreement.

## Interpreting amend-stage architecture plans

If models agree directionally but disagree on exact files or no-op vs change:

1. Preserve the plan as an amend-stage roadmap, not a certification.
2. Run a read-only file/path discovery pass.
3. Build a concrete implementation packet with exact target files and verification commands.
4. Re-run multi-model certification on the concrete packet.

Do not implement from patches whose target is only “implementation file to be located before edit”.
