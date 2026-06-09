# Evolution Lane Certification Loop — Root Cause & Prevention

## Problem Pattern

Evolution lane tasks get stuck in `CONTINUE_LOOP` because:
1. Exploratory tasks (repo analysis, strategy design) naturally produce model disagreement
2. Certification gate requires `agreement_above_threshold(0.65)` on approach/framing/implementation_order
3. After 2+ retries, `loop_non_convergence` is triggered → requires multimodel certification → guaranteed disagreement → infinite loop

## Failure Signatures

```yaml
multimodel_last_failures:
  - "agreement_below_threshold:approach:0.65"
  - "agreement_below_threshold:framing:0.65"
  - "agreement_below_threshold:implementation_order:0.65"
  - "best_within_constraints_missing:claude-opus-4-7"
  - "non_approve_vote:claude-opus-4-7:amend"
  - "non_approve_vote:deepseek-v4-pro:amend"
```

## Root Causes

1. **Threshold mismatch**: 0.65 agreement threshold too high for exploratory tasks
2. **Retry trigger too aggressive**: `retry_count() >= 2` triggers strong certification
3. **No exit condition**: `CONTINUE_LOOP` has no max_rounds limit
4. **amend counted as reject**: "amend" is conditional approval, not rejection
5. **No auto-ratification**: Subtask completion doesn't auto-trigger parent ratification

## Prevention Recommendations

1. Per-lane thresholds: evolution=0.50, delivery=0.70
2. Max 3 certification rounds → auto `RATIFY_WITH_RESERVATIONS`
3. amend vote weight = 0.7 (approve=1.0, reject=0.0)
4. Auto-trigger parent ratification when all children done
5. `loop_non_convergence` trigger: `retry >= 3 AND no_progress`

## Code Locations

- `scripts/brain_task_orchestrator.py:1730-1750` — certification reason generation
- `scripts/brain_task_orchestrator.py:3636-3638` — blocked resolver auto-generates convergence subtasks
- `scripts/brain_task_orchestrator.py:2224-2326` — non_convergence axis classification
