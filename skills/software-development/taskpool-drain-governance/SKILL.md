---
name: taskpool-drain-governance
description: Use when draining a governed Hermes/local-brain taskpool toward zero blocked/pending work, especially when child evidence repair, retry backoff, multimodel gates, or orphaned active claims appear.
---

# Taskpool Drain Governance
## When to Use

- Use when the user's request explicitly matches `taskpool-drain-governance` or this skill's documented domain.
- Use when this skill is already selected by the Hermes skill router and the task still fits the current goal.
- Don't use for: adjacent workflows with a more specific skill, generic Q&A, or tasks that lack evidence for this skill's domain.


Use this for bounded “drain until empty / continue safe pending child execution / targeted evidence repair” work on the local taskpool.

## Core loop

Run the drain as a governed loop, not a force-complete operation:

1. Read current `list --json` counts and classify `blocked` by `blocked_resolve_last_action`.
2. Read live worker state: `agent_team_controller.py worker-jobs --json`.
3. Read live multimodel state when relevant: `brain_task_orchestrator.py multimodel-intervention-jobs --json`.
4. Run `auto-close-review`.
5. Run `auto-subtask-sync --write`.
6. Run `blocked-resolve-step`.
7. Dispatch/autorun only when there are real pending/due retry rows and no live worker ceiling conflict.
8. Wait for workers, then repeat.

## Safety rules

- Never mark `done` from stale claims, timeout, retry exhaustion, or model agreement alone.
- Release orphaned `claimed`/`running` rows only to `retry` or `pending`, with command evidence.
- Treat `blocked` increases after creating narrowing/evidence children as possible progress, not automatically regression; reclassify the new blocks.
- If retry rows are not due yet, do not immediate-spin the same loop unless explicitly promoting due retries through the governed reconcile path.

## Orphan active claim recovery

When `claimed` or `running` rows hold the active ceiling but no process owns them, use the checklist in `references/drain-to-empty-orphan-active-claim-reconciliation.md`.

Short version:

- prove `worker-jobs` alive count is zero for the relevant batch/task;
- prove `multimodel-intervention-jobs` has no live job for multimodel-owned tasks;
- prove `ps` has no matching worker, multimodel, transition, proof-check, or parallel claim process;
- then release the row to `retry`/`pending`, never `done`.

## Stop conditions

Stop and report a Decision/Continuation packet when all safe reversible work has been drained and the remaining rows are only:

- waiting for child evidence;
- retry backoff not yet due;
- retry-cap or T3 pause requiring targeted evidence/certification;
- live worker/multimodel processes still running;
- a true human/evidence/authority gate.

## Verification before reporting

Always read back:

- `py_compile` for modified scripts;
- `selfcheck --json`;
- `list --json` counts;
- `worker-jobs --json`;
- `multimodel-intervention-jobs --json` when relevant;
- diff stat for changed taskpool code/skills.
## Common Pitfalls

1. Applying this skill mechanically after the user's goal has shifted. Re-check the current request before acting.
2. Treating a plan, stale memory, or prior report as proof of completion. Verify with fresh readback.
3. Ignoring neighboring skills or narrower workflows that better match the task. Prefer the most specific applicable skill.
## Verification Checklist

- [ ] The current user request still matches this skill's trigger class.
- [ ] Required files, tools, commands, or external state were checked before action.
- [ ] Outputs, edits, or side effects were verified by readback or direct inspection.
- [ ] Boundaries, unresolved assumptions, and any deferred work were stated clearly.
