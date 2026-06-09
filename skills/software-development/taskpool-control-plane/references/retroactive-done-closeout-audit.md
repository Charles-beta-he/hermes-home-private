# Retroactive done closeout audit

Use this when a taskpool closeout rule changes, or when one false-positive `done` task suggests older tasks may have been closed with the same weak evidence pattern.

## Trigger signals

- User says a completed task did not implement the promised feature.
- A new closeout rule now distinguishes task types (implementation/integration vs advisory/research vs governance).
- Many `done` tasks were closed by autorun using only `py_compile_taskpool PASS`, proof hashes, or multimodel discussion artifacts.
- Acceptance checkboxes remain unchecked in a task marked `done`.

## Audit sequence

1. Scan all task markdown files with `status: done`.
2. Classify each task by type:
   - `implementation/integration`: promises a feature path, hook, cron, runner, ingest, workflow, automation, script, UI/backend behavior, or pipeline.
   - `research/advisory`: promises analysis, extraction, evaluation, gap map, decision memo, or recommendation.
   - `governance/policy`: promises rules, gates, permission boundaries, lifecycle policy, or proof semantics.
3. Score closeout evidence by task type:
   - Implementation/integration must show real-chain validation: live hook/cron invocation, generated artifact/readback, real input dry run, relevant test, browser/API verification, or explicit taskpool add/ingest result.
   - Research/advisory must show a concrete report/artifact plus acceptance mapping to the original question.
   - Governance/policy must show the rule/gate landed in the actual control-plane surface and was exercised by a deterministic check or representative fixture.
4. Treat these as weak evidence only, never sufficient alone for implementation tasks:
   - `py_compile_taskpool PASS`
   - generic `proof-check` / `selfcheck`
   - proof hashes with no human-readable artifact
   - multimodel artifact without target-bound implementation evidence
5. Split results into action buckets:
   - High-confidence false done: implementation/integration task closed with py_compile/hash/multimodel-only evidence and no real-chain validation.
   - Needs manual review: unchecked acceptance or advisory task with ambiguous artifact mapping.
   - Plausible done: has task-type-appropriate artifact/readback/validation.
6. Reopen only high-confidence false done tasks in bulk. Prefer P1 first.
   - Transition `done -> pending` or `review` with explicit audit reason.
   - Add structured evidence such as `proof:manual_done_closeout_audit_<date>` plus the audit report/artifact path.
7. Verify after repair:
   - rerun audit to confirm counts changed;
   - `brain_task_orchestrator.py selfcheck --json`;
   - `brain_task_orchestrator.py proof-check --json`;
   - `brain_task_orchestrator.py next --reconcile --json` so reconcile-required state does not mask dispatchability.
8. Write a review note under `Documents/brain/06-治理与评审/reviews/` with baseline counts, reopened task IDs, remaining buckets, and verification results.

## Bulk reopen guardrail

Do not bulk-reopen every suspicious task. First reopen the high-confidence P1 false-done set, then leave P2/P3 and advisory ambiguity as a report-backed queue. This avoids converting a useful audit into uncontrolled taskpool churn.

## Implementation note

A deterministic scanner can live outside the skill, e.g. `~/.hermes/scripts/taskpool_done_closeout_audit.py`, but the skill should preserve the classification criteria above so future scanners use task-type-specific closeout semantics rather than generic string matching.
