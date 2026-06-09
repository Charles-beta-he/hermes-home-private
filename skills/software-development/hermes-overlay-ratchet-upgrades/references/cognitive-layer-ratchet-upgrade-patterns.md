# Cognitive-layer ratchet upgrade patterns

Use this reference when an upstream-tracking Hermes checkout contains local overlays plus proposed architectural changes.

## Durable patterns from a successful session

### 1) Inspect stash before any ratchet or replay
- Treat `git stash` as unreviewed code, not a safe backlog.
- Review the stash diff before replaying it onto a newer upstream base.
- If the stash contains risky flags or behavior drift (example: `verify=False`), archive it to a disk patch for traceability, then drop it instead of blindly applying it.
- This keeps stale experiments from contaminating the upgraded worktree.

### 2) Separate certified facts from weak-consensus architecture claims
- Multi-model discussion can produce useful design direction without producing truth-certified conclusions.
- Record disputed claims explicitly as weak consensus when evidence coverage is incomplete.
- Do not wire disputed claims into the hot path until certification or direct code evidence closes the gap.

### 3) Implement low-risk contract layers first
When the architecture direction is promising but disputed, start with additive seams that are easy to verify and do not change runtime behavior:
- data contracts / state containers
- stage protocols / interfaces
- pipeline skeletons with fail-soft behavior
- observability fields like timings, skipped stages, and confidence capture

These are safer than immediately rewiring the main conversation loop.

### 4) Follow TDD in ratchet upgrades that add new seams
Recommended order:
1. Write contract tests for the new seam.
2. Confirm RED from missing module / missing behavior.
3. Implement the minimal additive layer.
4. Run narrow GREEN tests.
5. Run adjacent regressions to verify no existing overlay was damaged.

### 5) Delay hot-path wiring until evidence is stronger
For architectural upgrades, the last step should be connecting the new seam into the production path (for example, `conversation_loop.py`).
Before that, prefer adapter stages around existing modules so behavior can be verified in isolation.

### 6) Good intermediate target shape
A safe intermediate state is:
- new contract files added
- no replacement of existing routing/policy logic yet
- targeted tests passing
- adjacent regressions passing
- ADR / plan documents clearly marking disputed claims as disputed

This creates a ratchet: the codebase gains reusable structure without taking on uncertified behavior changes.
