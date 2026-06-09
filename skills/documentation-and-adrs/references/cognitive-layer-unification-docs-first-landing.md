# Cognitive layer unification: docs-first landing pattern

Use this reference when an architecture task needs a durable, one-time landing plan but current evidence is strong enough for direction and not strong enough for a safe big-bang refactor.

When this pattern applies:
- Multi-model analysis converges on an architectural direction.
- The codebase contains partial or orphaned components that should be unified.
- Truth/certification is sufficient to choose direction, but evidence/linking gaps make immediate code rewiring too risky.
- The user wants a long-term landed plan now, not just verbal advice.

Recommended landing sequence:
1. Capture a state/evidence bundle for the architecture question.
2. Run real multi-model review and keep the merged-plan artifact.
3. If models converge on direction but caution against speculative rewiring, land docs immediately instead of forcing code changes.
4. Write three artifacts in the repo:
   - session plan file with goal, step checklist, decisions, resume protocol
   - ADR with context, decision, alternatives, consequences, non-goals
   - implementation plan with phases, exact files, tests, verification commands, risks, and commit sequence
5. Read the generated docs back and update the session plan status to completed.
6. Preserve the evidence artifact paths in the plan so later implementation can trace back to the certification inputs.

Key architecture rule from this session:
- If multiple cognition-oriented helpers exist (`task_router`, intent/retrieval/anatomy/budget/policy/compression helpers), converge them behind one canonical pre-model seam instead of adding more ad-hoc overlay wiring.
- In Hermes, `agent/conversation_loop.py` is the right canonical per-turn seam for such a unification plan.

What to include in the implementation plan:
- target typed state object
- pipeline/stage contract
- exact stage mapping from current modules to the new pipeline
- rollout order
- verification commands per phase
- degradation/fail-soft rules
- acceptance criteria
- recommended commit sequence

Why this matters:
- Prevents speculative big-bang refactors when evidence is incomplete.
- Still gives the user a concrete landed artifact set they can implement from immediately.
- Reduces drift by naming the canonical seam and migration path up front.
