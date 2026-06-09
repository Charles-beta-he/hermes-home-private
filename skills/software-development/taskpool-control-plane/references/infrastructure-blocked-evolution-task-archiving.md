# Infrastructure-Blocked Evolution Task Archiving

When an evolution lane task's analysis is complete but multimodel certification is blocked by infrastructure (missing API keys, quota expired, provider unavailable), the task can be archived with evidence of completion.

## Pattern

1. Verify the task's analysis is actually complete (gap analysis, prototype design, evidence deposited)
2. Verify the blocker is infrastructure, not analysis quality (check `multimodel_last_failures`)
3. Archive the task with structured evidence of completion

## Proven Commands

```bash
# Archive advisory task with no evidence (P3, stale)
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition "<task-id>" --to archived --actor hermes --authority claim-and-handoff --reason "P3 advisory with no evidence deposited; archive to clear pool" --force --json

# Archive evolution task blocked on infrastructure
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition "<task-id>" --to archived --actor hermes --authority claim-and-handoff --reason "analysis_complete_blocked_on_multimodel_certification_gpt55_quota_expiry; gap_analysis_and_prototype_deposited" --force --json
```

## Key Pitfalls

- `--force` does NOT bypass `multimodel_certification_required_before_done` gate
- `--evidence` flags don't bypass the multimodel certification gate either
- `blocked-resolve-step` is a no-op when the blocker is infrastructure (missing API keys)
- `auto-close-review` is a no-op for tasks in `blocked` status (only works for `review`)

## When to Archive vs Keep Blocked

Archive when:
- Analysis is complete with evidence deposited
- Blocker is infrastructure (quota, credentials, provider outage)
- Task is P2/P3 (not P1 critical path)
- Pool needs cleanup to restore dispatchability

Keep blocked when:
- Analysis is incomplete
- Blocker is analysis quality (multimodel FAIL due to framing/approach)
- Task is P1 critical path
- Infrastructure blocker is expected to resolve soon

## Verification

After archiving:
1. `list --json` should show reduced active_count
2. `selfcheck --json` should show PASS
3. `next --json` should show dispatchable task or null
4. `dashboard --write` should regenerate clean state
