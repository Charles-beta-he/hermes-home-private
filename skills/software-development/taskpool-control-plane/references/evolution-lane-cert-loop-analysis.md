# Evolution Lane Certification Loop — Root Cause Analysis

Date: 2026-05-16
Affected tasks: 3 blocked (缓存命中率/预算接力/evoagentx)

## Failure Reasons (from multimodel_last_failures)

```
agreement_below_threshold:approach:0.65
agreement_below_threshold:framing:0.65
agreement_below_threshold:implementation_order:0.65
best_within_constraints_missing:claude-opus-4-7
best_within_constraints_missing:gpt-5.5
best_within_constraints_missing:mimo-v2.5-pro
non_approve_vote:claude-opus-4-7:amend
non_approve_vote:deepseek-v4-pro:amend
```

## Root Causes (5)

1. **Task nature vs gate mismatch** — Evolution tasks are exploratory (repo analysis, strategy design). Model disagreement on approach/framing is healthy, but gate requires agreement > 0.65.
2. **retry_count trigger too aggressive** — L1741: `retry_count() >= 2` triggers `loop_non_convergence` → strong certification required → guaranteed failure for exploratory tasks.
3. **No CONTINUE_LOOP exit condition** — No max_rounds cap. Can loop forever until manual intervention.
4. **amend counted as reject** — `non_approve_vote:amend` is conditional approval, but gate treats it as rejection → pass rate artificially low.
5. **Subtask completion lacks auto-ratification** — After narrowed subtasks complete, parent ratification doesn't auto-trigger. Requires external push.

## Prevention Mechanisms (code-level)

1. **Per-lane thresholds**: evolution=0.50, delivery=0.70
2. **Max rounds**: `if rounds >= 3: decision = RATIFY_WITH_RESERVATIONS`
3. **amend weight**: approve=1.0, amend=0.7, reject=0.0
4. **Auto-ratification**: `if all_children_done(parent_id): schedule_parent_ratification(parent_id)`
5. **Tighter trigger**: `retry >= 3 AND rounds_since_last_progress <= 1`

## Governance Rules

1. Exploration Diversity Rule — divergence = positive signal for evolution lane
2. Three-Strike Escalation — 3 CONTINUE_LOOP rounds → human_review
3. Amend-as-Qualified-Approval — amend+approve >= 70% and no reject = pass
4. Subtask-First Gate — pre-generate convergence subtasks at task creation, not after block
5. Max Certification Rounds — cap at 3, auto RATIFY_WITH_RESERVATIONS

## Key Code Locations

- `scripts/brain_task_orchestrator.py:1730-1750` — certification reason generation
- `scripts/brain_task_orchestrator.py:3636-3638` — blocked resolver auto-generates convergence subtasks
- `scripts/brain_task_orchestrator.py:2224-2326` — non_convergence axis classification + subtask spec building
- `scripts/brain_task_orchestrator.py:1808-1810` — task_multimodel_certification_reasons()
