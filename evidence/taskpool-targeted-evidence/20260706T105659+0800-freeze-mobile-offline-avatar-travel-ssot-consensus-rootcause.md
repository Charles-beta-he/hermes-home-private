# Consensus root-cause packet — 2026-06-21-freeze-mobile-offline-avatar--travel-ssot

Generated: 2026-07-06T02:56:59.175740+00:00

## Root cause
Previous T3 retries failed because the parent ratification input mixed already-converged child evidence with unresolved parent-level disagreement. The repair is to split consensus regions from disagreement regions, accept the targeted evidence as human-reviewed ratification input, and allow exactly one bounded parent refresh.

## Consensus regions
- C-001: Parent objective stays frozen: review and accept canonical project model, constraints, and runtime decision gates; do not broaden into new implementation work.
- C-002: Child convergence is clean: 13/13 children done, no open/missing children, stale child evidence count is zero.
- C-003: Historical split axes have been covered by done child evidence: framing, patch_normalization, quota_observability, relay_ordering.
- C-004: Mobile/offline avatar/travel runtime remains projection/draft/handoff only; it must not write canonical facts or create a second source of truth.
- C-005: This packet and the targeted evidence packet are ratification inputs only; they are not done authority.

## Previously inconsistent regions and resolution
- approach: agreement_below_threshold:approach:0.65 -> Constrain the approach to parent ratification refresh using frozen objective + completed child evidence; no ordinary worker redispatch and no scope expansion.
- framing: agreement_below_threshold:framing:0.65 / non_approve_vote / no_claims -> Frame the parent as SSOT/runtime-gate acceptance, not product feature completion; child framing evidence is done and stale child evidence is zero.
- implementation_order: agreement_below_threshold:implementation_order:0.65 -> Next step order is deterministic: targeted evidence accepted -> one bounded parent ratification refresh -> ratification-gate readback; if fail, pause again.
- long_term_goal_alignment: long_term_goal_alignment_missing -> Explicitly bind to MOAT authority chain: Hermes/Brain canonical facts remain SSOT; mobile/Gateway are projections/sync boundaries only.
- I-001: unresolved_severity_3:I-001 -> Original discussion artifact is missing, so I-001 cannot be replayed directly; treat residual issue as artifact-inventory/readback gap and require ratification to either close it or name exact remaining axis.

## Final consensus points
- The only authorized automatic move is one bounded parent ratification refresh; completion remains gated by ratification PASS and local proof/lifecycle checks.
- A later failed ratification round consumes this allowance because multimodel_last_checked_at becomes newer than targeted_evidence_accepted_at.
- If ratification still fails or the missing discussion artifact remains decisive, keep blocked and report the exact remaining axis; do not loop indefinitely.

## Safety
- Not done authority.
- Opens one bounded parent ratification refresh only.
- A later failed T3 round consumes this allowance.
- If ratification fails again, keep blocked and report the exact axis.

JSON packet: `/Users/charles/.hermes/evidence/taskpool-targeted-evidence/20260706T105659+0800-freeze-mobile-offline-avatar-travel-ssot-consensus-rootcause.json`
SHA256(JSON): `56d16d5c51e89d9f34611066b9a22c4597d450a741a07da18671090a92eb5c49`
