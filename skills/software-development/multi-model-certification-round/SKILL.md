---
name: multi-model-certification-round
description: "Use when evaluate a multi-model certification packet (Round N) and produce structured vote output."
triggers:
  - "multi_model_comm_packet_v1 with mode manifest_delta"
  - "certification round vote request"
---

# Multi-Model Certification Round Protocol

## Overview

Evaluate a multi-model certification packet (Round N) and produce structured vote output. It is organized as a gated workflow: advance through explicit stages, preserve evidence grounding, and emit machine-readable verdicts.

When certification failures are caused by provider routing/health rather than code evidence, use `references/provider-health-routing-recovery.md` before changing quorum: classify model-name migration vs endpoint/API-key scope vs local transport, prefer bounded direct adapters/probes, preserve min_quorum, and use TTL health breakers instead of permanent model removal.

When improving or auditing smart multi-model routing coverage, use `references/profile-driven-surface-router-coverage.md`: drive route selection from a capability profile's surfaces/roles/final evidence, assert every declared surface resolves to inspectable `profile_surface` + `required_evidence` metadata, and keep theoretical coverage separate from live readiness/autonomy certification.

When checking whether a provider has new or usable model participants, use `references/provider-model-catalog-vs-live-availability.md`: compare Hermes static/cache catalogs against external registries such as models.dev, then smoke-test the exact provider/model route before marking a model available for certification or routing.

## When to Use

Use this skill when the request matches the `multi-model-certification-round` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

When receiving a `multi_model_comm_packet_v1` with `mode: manifest_delta`:

## Decision Framework

1. **Classify verification surfaces and model capability boundaries** before voting.
   - Prefer a surface specialist (for example Gemini for visual UI review, DeepSeek for adversarial/code review, Claude for architecture/arbitration) instead of all-model voting by default.
   - When surfaces overlap or risk is T2+, use overlap voting; do not reduce it to simple majority.
2. **Enforce role separation** -- producer/implementer self-report is not certification evidence and must not count toward quorum for completion-critical claims.
3. **Require objective evidence authority** -- model judgment alone is advisory. Every certification-critical vote must cite evidence refs, and at least one non-model evidence source must support each acceptance claim.
4. **Check round_delta.unresolved_issues** -- if non-empty, these MUST be addressed before approving
5. **Check truth_gate** -- `can_certify_truth` must be true; all claims must be `verified_by_evidence`
6. **Check certification_intent** from planner_patch_summary:
   - `no_action_certification` + `concrete_patch_count == 0` → empty patches list is NOT a blocker (planners explicitly signed off with noop)
   - `unresolved_noop_vs_change` → do NOT claim patches were dropped; resolve the ledger first
7. **Check evidence coverage** -- `evidence_coverage` should be 1.0
8. **Identify novel severity >= 3 blockers** -- only discuss these, not resolved/repeated issues

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

See also: `references/routed-truth-grounded-not-certified.md` for reporting runs that are multi-model routed and truth-grounded but still not fully certified, including the claim-id normalization pitfall (`C1` vs `C-001`) and noop-vs-change follow-up packet pattern, `references/factual-vs-normative-claim-repair.md`, `references/design-review-panel-variant.md` for replacing a required model participant without confusing fallback responses with certification evidence, `references/no-action-repair-child-recertification.md` for repair-child/closeout recertification after a later degraded round, `references/mainloop-multimodel-integration-boundary.md` for designing Hermes main conversation-loop multi-model routing without turning normal chat into always-on parallel voting or mistaking degraded advisory rounds for certification, `references/capability-boundary-and-evidence-authority.md` for capability-surface routing, implementer/verifier separation, overlap voting, and model-judgment-as-advisory acceptance gates, `references/route-review-gate-stable-plan.md` for final long-term RouteReviewGate plans that route by surface/risk/capability/side-effect/evidence-state and explicitly separate theoretical route coverage from live model readiness, `references/mainloop-verification-gate-consumer.md` for landing a bounded final-response gate consumer that blocks or downgrades completion claims until objective evidence and independent verifier votes are linked, `references/mainloop-background-certification-queue.md` (scope: conversation-loop certification systems; anti-condition: not for generic one-off project task queues) for durable queue/worker/cron follow-through after a completion claim is blocked or downgraded, `references/mainloop-route-required-evidence-ledger.md` for preventing false acceptance when claim-level truth coverage is green but route-required evidence classes are missing, and `references/multimodel-adapter-health-and-internal-projections.md` for debugging MiMo/Xiaomi timeouts, Claude Code `error_max_turns`, health-gated optional participants, and internal JSON/auto-relay projections that should not enqueue completion-claim certification jobs.

## Repair Pattern: taskpool blocked certification rebuild

When a taskpool task is blocked because `multimodel_last_discussion_artifact` is missing, the old `tick-*` directory was pruned, or a previous T3 loop needs to be rebuilt, follow `references/taskpool-blocked-certification-rebuild.md`. The key pitfall is status separation: `fanout_quorum_met`, `truth_status=grounded`, and `evidence_coverage=1.0` do not equal full certification when required participant approvals or `best_within_constraints=true` signatures are missing. Rebuild from `multimodel_last_state_path`, stamp task binding before ratification/writeback, then rerun the blocked resolver.

## Repair Pattern: replace a required model participant

When a certification round is blocked because a required participant slug is stale or must be replaced:

1. Update the active ratification policy, tier planner lists, and any arbiter/router/pricing metadata that select the old slug.
2. Run the status command that shows resolved planners/arbiters before rerunning certification; verify the old slug is gone from the active panel.
3. Smoke-test the provider path that the certification runner uses, but do not count a generic fallback response as evidence that the requested model participated.
4. Rerun the certification step and inspect `models_consulted` plus the gate result. If the new required participant still fails due to setup/auth/quota, report that as the boundary rather than closing from the other approvals alone.
5. Keep transient credential/setup failures out of durable rules; capture the verification sequence and fallback-evidence boundary instead.

## Key Pitfalls

- `references/taskpool-concurrency-certification.md` captures the pattern for taskpool concurrency expansion reviews: use fresh capacity readback, exact claim/evidence IDs, concrete implementation-file discovery, and report fanout/truth grounding separately from final ratification.
- When designing multi-model routing, do not route only by task complexity. Route by verification surface and capability boundary first; use overlap voting only when surfaces cross, risk is high, or evidence/model judgments conflict.
- Never let the implementation/producer model certify its own completion-critical output. Its self-report can be retained as context but must not count toward certification quorum.
- Never accept model-only certification. A model vote without objective `evidence_refs`, or a panel approval without non-model tool/readback evidence, is `advisory_only` even when multiple models agree.
- UI/visual acceptance is not Gemini-only acceptance: Gemini can be the visual verifier, but certification still needs screenshot/browser/interaction/console evidence and the Hermes evidence gate.
- When taskpool `multimodel-intervention-dry-run` pauses a task because T3 rounds are exhausted, do not bypass the economy gate by rerunning `multimodel-intervention-step` or moving the task to `done`. If `blocked-resolve-step --authority dry-run` also reports a missing `discussion_result.json`, produce an intervention packet instead: restore the missing artifact, create a targeted evidence fix for the failed axis, or request audited human closure as terminal advisory/not-done.
- NEVER assume omitted payload bodies; use evidence_requests if detail needed
- NEVER claim patches were dropped when certification_intent explains why patches list is empty
- Empty unresolved_issues means no blockers from prior rounds to carry forward
- Previous round "amend" votes may have been resolved; re-evaluate independently
- Do NOT force normative architecture guidance through the same truth gate as factual repo claims; move it into ADR/design rationale
- If truth is the target, ensure every evidence item is in the orchestrator-visible top-level `evidence` array (or the exact field consumed by `build_evidence_bundle`) and has explicit `supports`/`contradicts` links before rerunning certification; evidence buried under ad-hoc keys such as `context.current_evidence` will be ignored and produce `evidence_coverage=0.0`.
- With `consult_models.py state --evidence-json`, pass each evidence item as a separate JSON argument with its own `id` and `supports`; do not pass one nested bundle containing `{claims, evidence}` as a single evidence object, or high-severity claims may remain at `needs_link_review` despite valid raw evidence.
- For single-claim chunked self-checks, verify the generated truth bundle's normalized claim id before running the round. The state builder may normalize the claim to `C-001`; if evidence supports a chunk label like `C2-mainloop-integration` instead, `evidence_coverage` can fall to 0.0 despite valid raw evidence.
- Claim-level `evidence_coverage=1.0` is not enough for route-based mainloop certification. Also compute `route_required_evidence` coverage from the router's `required_evidence`; missing required evidence classes on T3/blocking tiers must downgrade or block certification.
- When a model repeatedly times out or returns low-confidence shadow plans, first run a tiny provider probe to distinguish packet-size/prompt issues from adapter/provider health. If the provider is unhealthy, exclude it with a workflow-scoped health gate and keep certification quorum independent; do not permanently encode a global model ban.
- Claude Code planner/verifier calls with `--max-turns 1` can fail with `error_max_turns` when tools are enabled and the model attempts `tool_use`; for evidence-only JSON/text certification calls, disable tools (for example `--tools ""`) instead of increasing turns blindly.
- Internal planner JSON, ContextCard JSON, and auto-relay continuation handoffs can contain completion words but are not user-facing completion claims. Skip these internal projections before enqueuing mainloop certification, or the gate may create JSON-fragment claims that produce `schema_mismatch` / `needs_link_review`.
- Report fanout quorum, truth gate, and discussion/ratification as separate statuses. `fanout_quorum_met` only proves enough planners returned; complete certification still needs `truth_gate.can_certify_truth=true` and a certified discussion/manifest when that mode is used.
- If an asynchronous consult result arrives after implementation or push, still record it in the decision artifact. Preserve the distinction: `truth_status=grounded` / `can_certify_truth=true` corroborates evidence, while `certification_status=degraded_not_certified` or “planner fan-out below quorum” means do NOT claim full multi-model certification.
- For architecture-direction questions, a degraded panel can still inform an ADR as `degraded multi-model review` when at least one substantive model response is available, but the ADR must explicitly list missing/failed participants and must not treat the result as quorum certification.
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
