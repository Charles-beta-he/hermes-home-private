# Iceberg Tier Integration into Dispatch System

Pattern for integrating a task classification dimension (iceberg tier, capability level, etc.) into the orchestrator dispatch pipeline. Applied in the uvisa project for S0/F/L/B/M/V tiers but the pattern generalizes.

## The 4 Integration Points

When adding a classification dimension to an existing orchestrator, touch these surfaces:

### 1. Score/priority weighting (`Task.score()`)
Add tier-based bonus/penalty to the ranking function. Direction depends on business goal:
- Higher tier = faster completion → positive weight (S0: +12, S1: +10, F: +8)
- Lower tier = more coordination needed → negative weight (L: -3, B: -15)
- This pushes self-contained tasks to the front of the dispatch queue

### 2. Preflight gate (`Task.is_dispatchable()`)
Add tier-aware blockers that prevent claiming when prerequisites are missing:
- Example: `lane=work` tasks with a project must have `source_weighting_policy_ref`
- Different tiers can have different minimum requirements
- Return `False` from `is_dispatchable()` so dispatch tick skips them cleanly

### 3. Work contract acceptance atoms (`generate_acceptance_atoms()`)
Add tier-specific verification atoms to the acceptance contract:
- L (requires backend): `A-backend-contract` — API contract + business semantics verification
- B (needs human): `A-human-confirmation` — explicit user authorization before proceeding
- Pass `iceberg_tier` as a parameter to `generate_acceptance_atoms()` from the row data
- The tier parameter should default to empty string so non-tiered tasks are unaffected

### 4. Dashboard visualization
Add a tier distribution section and a Tier column to the sorted table:
- Distribution block shows count per tier for active work tasks
- Table column shows each task's tier in the dispatch order

## Implementation Checklist

1. Add `iceberg_tier` property to the Task dataclass/row model
2. Modify `score()` to add tier weighting (bigger delta = stronger priority influence)
3. Modify `is_dispatchable()` to add tier-based preflight gates
4. Add `iceberg_tier` parameter to `generate_acceptance_atoms()` signature
5. Add tier-conditional atoms inside `generate_acceptance_atoms()`
6. Update `ingest_task_rows()` call to pass `iceberg_tier` from the row dict
7. Add tier distribution section to dashboard generator
8. Add tier column to the sorted table
9. Run existing tests to verify no regressions
10. Commit with descriptive message

## Pitfalls

- Don't forget to pass the tier through the call chain: row dict → `generate_acceptance_atoms()` → atom generation. A missing pass results in all tasks getting empty-tier treatment silently.
- Work contract tests may not cover the new tier parameter — add test cases for L and B tier atoms.
- Dashboard table column count changes require updating both the header row and separator row.
- Tier weighting should be a bonus/penalty on top of existing priority score, not a replacement. Existing P1/P2/P3 priority must still be the dominant signal.
