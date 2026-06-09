# Bounded evolution child evidence tranche

Use this when the pool is healthy but a blocked evolution parent is waiting on non-convergence child axes, and the user asks you to actively handle/advance it rather than only inspect.

## Pattern

1. Re-baseline first: `list --json`, `next --json`, `dispatch-dry-run --json`, `eligibility-check --json`, `autorun-runner --json`, `selfcheck --json`.
2. Prefer the current `next` evolution child if it is a child of the blocked parent and has a concrete `auto_subtask_axis`.
3. Claim and move exactly one child to `running` before writing evidence.
4. Read the task note and land a bounded narrowed brief that matches the child axis, not the whole parent objective.
5. Mark the child acceptance/workpad checkboxes complete only for the bounded axis.
6. Add explicit handoff language: the child axis is complete, but parent remains blocked until sibling axes and parent ratification refresh are done.
7. Run deterministic gates (`proof-check`, `selfcheck`) and compute a note hash.
8. Transition the child to `review` with structured evidence: `proof:<sha256>`, `command:proof-check PASS`, `command:selfcheck PASS`, and `classification:axis=<axis>_complete_parent_still_blocked`.
9. Re-run `list`, `next`, `dispatch-dry-run`, `blocked-resolve-step`, `proof-check`, `evidence-spine`, and `selfcheck`.

## Axis brief examples

### `fallback_threshold`

Record:
- trigger thresholds (no-op, advisory deposit, patch candidate, adoption);
- budget/quota exhaustion fallback;
- noop vs change criteria;
- frozen parent dependency order.

Durable rule: quota/provider uncertainty must not lower the truth gate or mark the parent done.

### `quota_observability`

Record:
- file-backed evidence locations;
- a minimum `quota_state` schema with expected/seen canonical participants, noncanonical participants, unavailable participants, parse errors, confidence, and staleness;
- confidence levels (`high`, `medium`, `low`, `unknown`);
- unknown/unobservable handling.

Durable rule: noncanonical model output and missing canonical participants are diagnostic evidence, not approval evidence.

## Multimodel streaming process hygiene

Claim/transition may spawn `multimodel-intervention-step` processes for the task. After manual bounded advancement:
- check for duplicate intervention-step processes for the same task;
- avoid leaving multiple concurrent writers on the same note;
- if duplicates were caused by your repeated claim/transition attempts and are still long-running, terminate the duplicates before final verification;
- verify `claimed/running=0` or exactly the intended running task, and `stale_claims=0`.

This is process hygiene, not a reason to disable multimodel intervention globally.

## Good final state

- The child axis moved to `review` with structured evidence and deterministic gates.
- The blocked parent may still be blocked with `await_auto_subtasks`; that is correct if siblings remain open or parent ratification has not refreshed.
- `next` should either move to the next sibling axis or to the next non-evolution dispatchable task.
- The pool should have no accidental duplicate intervention processes and no stale claim.