---
name: multi-model-certification-round
description: "Use when evaluate a multi-model certification packet (Round N) and produce structured vote output."
triggers:
  - "multi_model_comm_packet_v1 with mode manifest_delta"
  - "certification round vote request"
---

# Multi-Model Certification Round Protocol

## Overview

Evaluate a multi-model certification packet (Round N) and produce structured vote output. It is organized as a gated workflow: advance through explicit stages, preserve evidence at each boundary, and leave neighboring domains to their own skills.

## When to Use

Use this skill when the request matches the `multi-model-certification-round` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

When receiving a `multi_model_comm_packet_v1` with `mode: manifest_delta`:

## Decision Framework

1. **Check round_delta.unresolved_issues** -- if non-empty, these MUST be addressed before approving
2. **Check truth_gate** -- `can_certify_truth` must be true; all claims must be `verified_by_evidence`
3. **Check certification_intent** from planner_patch_summary:
   - `no_action_certification` + `concrete_patch_count == 0` → empty patches list is NOT a blocker (planners explicitly signed off with noop)
   - `unresolved_noop_vs_change` → do NOT claim patches were dropped; resolve the ledger first
4. **Check evidence coverage** -- `evidence_coverage` should be 1.0
5. **Identify novel severity >= 3 blockers** -- only discuss these, not resolved/repeated issues

## Vote Logic

- **approve**: truth gate permits, no unresolved issues, no novel blockers, `best_within_constraints: true`
- **amend**: specific corrections needed (cite evidence IDs)
- **reject**: fundamental blocker that cannot be amended

## Output Format

```
critiques: [{target_model, severity (1-5), claim, evidence ref, correction, novel: bool}]
evidence_requests: [{claim_id, tool_needed, command, why}] (only if omitted detail needed)
vote: approve|amend|reject
best_within_constraints: true|false
reasoning: <=600 chars, cite issue/evidence IDs
```

## Repair Pattern: link-review + no-action recertification

When a packet fails because claims are stuck at `needs_link_review` or because a normative architecture recommendation was mixed into truth-gated claims:

1. Split the packet into two layers:
   - factual claims that can be grounded directly in repo evidence
   - design/ADR conclusions that should NOT be truth-gated as repository facts
2. Rewrite over-strong integration claims to the narrowest provable wording.
   - Example: prefer "tested/local integration" over "live main-path integration" unless a canonical caller is proven.
3. Add explicit `supports` links on every evidence item so the truth gate can mark each factual claim `verified_by_evidence`.
4. If the goal of the round is certification only, constrain the packet explicitly:
   - evidence ratification only
   - no code changes requested
   - expect `planner_patch_summary.certification_intent == no_action_certification`
5. Treat canonical main-path absence as a scoped fact, not a universal absence claim.
   - State which entrypoints were checked (for Hermes, often `run_agent.py` and `agent/conversation_loop.py`).
6. If the packet is reviewing a future implementation seam, explicitly decide whether the round is:
   - review-package ratification only, or
   - implementation authorization.
   Do not leave this implicit.
7. When a round keeps failing on noop-vs-change ambiguity, reframe it as review-package-only and move actual code landing to a later guarded implementation step.

See also: `references/factual-vs-normative-claim-repair.md`, `references/design-review-panel-variant.md`.

## Key Pitfalls

- NEVER assume omitted payload bodies; use evidence_requests if detail needed
- NEVER claim patches were dropped when certification_intent explains why patches list is empty
- Empty unresolved_issues means no blockers from prior rounds to carry forward
- Previous round "amend" votes may have been resolved; re-evaluate independently
- Do NOT force normative architecture guidance through the same truth gate as factual repo claims; move it into ADR/design rationale
- If truth is the target, ensure every evidence item is in the orchestrator-visible top-level `evidence` array (or the exact field consumed by `build_evidence_bundle`) and has explicit `supports`/`contradicts` links before rerunning certification; evidence buried under ad-hoc keys such as `context.current_evidence` will be ignored and produce `evidence_coverage=0.0`.
- Report fanout quorum, truth gate, and discussion/ratification as separate statuses. `fanout_quorum_met` only proves enough planners returned; complete certification still needs `truth_gate.can_certify_truth=true` and a certified discussion/manifest when that mode is used.
- If an asynchronous consult result arrives after implementation or push, still record it in the decision artifact. Preserve the distinction: `truth_status=grounded` / `can_certify_truth=true` corroborates evidence, while `certification_status=degraded_not_certified` or “planner fan-out below quorum” means do NOT claim full multi-model certification.
- Do not mix review-package approval with immediate implementation authorization unless the packet unambiguously carries concrete patch intent and corresponding evidence.
- If planners and reviewers disagree about whether the round is noop or change-bearing, stop and rewrite the packet scope before rerunning models.

## Common Pitfalls

1. Advancing stages without a gate, evidence artifact, or closure-state check.
2. Skipping prerequisite checks and assuming the environment already matches the workflow.
3. Reporting success before reading back the actual outputs, files, or external side effects.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Every stage passed its gate before the next stage advanced, with evidence recorded.
