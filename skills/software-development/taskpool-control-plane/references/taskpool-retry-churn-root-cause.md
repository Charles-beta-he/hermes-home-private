# Taskpool retry-churn root-cause repair

Use when taskpool retry count grows repeatedly on advisory/evolution review-gap tasks, especially titles containing repeated `补证闭环` or failures cycling through `missing_advisory_artifact`, `missing_multimodel_certification`, `gate=UNKNOWN`, or `round=unknown`.

## Symptom pattern

- Many tasks sit in `retry` with high `retry_count` and similar `blocked_resolve_reason`:
  - `transient multimodel status gate=UNKNOWN round=unknown; retry certification/execution`
- Existing task notes contain real evidence (`artifact:`, `file:`, `proof:sha256:`), but `task_multimodel_passed()` still returns false.
- `review-gap-scan` creates recursive repair children: `补证闭环｜补证闭环｜...`.
- `blocked-resolve-step` keeps moving blocked tasks back to retry instead of stopping at a hard gate.

## Root-cause checklist

1. Classify the retry set.
   - Count by `lane`, `project`, `priority`, and `review_gap_type`.
   - Identify whether retry tasks are repair children (`review_gap_parent` set) or original parent tasks.
2. Compare evidence existence with recognizer truth.
   - Check whether PASS/LOOP_DONE JSON exists only in `evidence_refs` / `evidence`, not in `ratification_artifact` / `multimodel_last_discussion_artifact`.
   - Check whether JSON schema is a historical compact shape such as `advisory_multimodel_ratification_v1`.
3. Verify target binding before accepting historical packets.
   - Accept only local JSON artifacts with task-bound or explicit parent-bound repair-child target (`target_task_id`, `parent_task`, `repair_child_task`, or context task id).
   - Do not treat opaque `proof:` or `command:` strings as ratification artifacts.
4. Stop recursive repair creation.
   - `review-gap-scan` should not create repair children for tasks that already have `review_gap_parent`; repair children are the remediation surface, not parents for grandchildren.
5. Add a transient retry cap.
   - `blocked-resolve-step` may retry transient multimodel infrastructure failures once or twice, but after a small cap (default 3) keep blocked with a hard-gate reason requiring targeted certification or evidence-contract repair.

## Safe repair pattern

- Patch recognizers read-compatibly rather than weakening lifecycle gates:
  - Extend legacy packet recognition for target-bound historical schemas.
  - Scan local JSON refs in `evidence_refs` / `evidence`, including comma-separated refs, but handle invalid/too-long paths safely.
- Patch resolver behavior:
  - If retry count exceeds `HERMES_BLOCKED_RESOLVE_TRANSIENT_RETRY_CAP` (default 3), keep blocked instead of returning to retry.
  - Keep `done` closure under normal `auto-close-review` and `lifecycle_gate`.
- Patch review-gap behavior:
  - Skip creating new review-gap children when the candidate already has `review_gap_parent`.

## Verification

After patching:

1. Recompute retry diagnostics:
   - expected: high-count retry tasks either resolve to review if evidence is now recognized, or become blocked with `keep_blocked_transient_retry_cap`.
2. Run `blocked-resolve-step` and inspect:
   - `resolved_to_review` for now-recognized evidence.
   - `kept_blocked` for unresolved or capped tasks.
   - `error_count == 0`.
3. Run `auto-close-review`:
   - close only tasks whose normal done gate passes.
   - skipped tasks should cite missing concrete proof surfaces, not `multimodel_certification_required_before_done` caused by stale recognizer gaps.
4. Run `selfcheck` and dispatch summary:
   - selfcheck PASS.
   - retry count drops; remaining retry tasks should be below cap or have explicit future `next_attempt_at`.

## Anti-conditions

- Do not mark tasks done directly to drain retry count.
- Do not accept unbound or non-local artifacts as certification proof.
- Do not encode one session's task IDs or artifact paths into global code or skill instructions; use them only as examples in local evidence notes if needed.
- Do not treat advisory-only discussion as certification unless the task's explicit repair contract allows parent-bound historical PASS/LOOP_DONE evidence and deterministic checks pass.
