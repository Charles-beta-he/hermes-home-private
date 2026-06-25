# Multi-model analysis request: Taskpool parent/child stall scenarios

We just implemented a read-only `parent_aggregation` diagnostic for Hermes taskpool `blocked-resolve-step` so a blocked parent whose auto-generated children are all done is reported as `keep_blocked_certification_required` instead of being incorrectly reopened when multimodel certification still fails.

Known live case:
- Parent: `2026-06-21-freeze-mobile-offline-avatar--travel-ssot`
- Parent status: blocked
- Children done: framing, patch_normalization, quota_observability
- Resolver output: `ready_for_parent=true`, `action=keep_blocked_certification_required`, `suggested_next=parent_ratification_refresh`
- Remaining gate: explicit multimodel/certification (`explicit_requires_multimodel`, `loop_non_convergence`)

Implementation files:
- `/Users/charles/.hermes/scripts/brain_task_orchestrator.py`
- `/Users/charles/.hermes/scripts/taskpool_parent_evidence_aggregator.py`
- `/Users/charles/.hermes/scripts/test_brain_task_orchestrator.py`
- `/Users/charles/.hermes/scripts/test_taskpool_parent_evidence_aggregator.py`

Question:
Identify other likely taskpool stall scenarios caused by parent/child decomposition, concurrency boundaries, evidence aggregation, certification, claim lifecycle, or stale derived state. For each scenario provide:
1. Failure shape / symptoms
2. Root cause model
3. Detection signal to add
4. Minimal safe resolver behavior
5. Test case to add
6. Priority and risk

Constraints:
- Do not propose force-closing tasks or bypassing proof/multimodel gates.
- Prefer deterministic read-only diagnostics before lifecycle mutations.
- Preserve fail-closed semantics for external side effects.
- Keep recommendations implementable in small TDD slices.

Acceptance criteria:
- At least 8 distinct scenarios.
- Must include concurrency false contention, stale claims, stale child evidence, missing child files, child finished but parent evidence not backfilled, cyclic/too-deep splits, hidden blocked child under apparently ready parent, and stale derived views/dashboard mismatch.
- Include which scenarios should be implemented next.
