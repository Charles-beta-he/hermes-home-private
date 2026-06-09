# Non-work validation baseline for Hermes taskpool

Use this reference when you need standard smoke tasks that validate taskpool -> worker -> delegate without relying on business/work tasks.

## Required checks for every non-work validation task

1. task claimed successfully
2. worker spawned successfully
3. required skills loaded successfully
4. `delegate_task` invoked successfully when the template requires it
5. task completed with a summary

## Recommended template frontmatter

```yaml
---
tenant: validation
capability: delegate-validation
template_id: validation-default-delegate-smoke
assignee: default
profile_hint: default
proof_policy: summary-only
retry_policy: replay-safe
skills:
  - kanban-worker
---
```

## Suggested standard validation set

- default delegate smoke
- brain-mirror delegate smoke
- worker bootstrap smoke
- control-plane readonly smoke

## Design rules

- make the task explicitly `NON-WORK VALIDATION TASK`
- keep validation tasks read-only unless a tiny workspace-local proof artifact is explicitly allowed
- use them as the primary control-plane acceptance baseline instead of mixed work/Lark tasks
- prefer short-lived replay-safe tasks so failures point to infrastructure, not business ambiguity

## Evidence expectations

Validation summaries should report:
- whether the worker was claimed and spawned
- whether the delegate fan-out happened when required
- what source of truth was read (DB rows, run summaries, file counts, workspace path)
- a concise final health verdict

## Anti-pattern

Do not use business delivery tasks as the main control-plane smoke suite. They mix infrastructure validation with product ambiguity, review gates, and missing external inputs.