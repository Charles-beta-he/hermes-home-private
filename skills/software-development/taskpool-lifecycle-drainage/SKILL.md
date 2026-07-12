---
name: taskpool-lifecycle-drainage
description: "Use when draining Hermes brain/taskpool blocked/review/retry states, diagnosing no-done stalls, or deciding whether remaining blocked tasks are safe to auto-resolve versus human/evidence gated."
---

# Taskpool Lifecycle Drainage
## When to Use

- Use when the user's request explicitly matches `taskpool-lifecycle-drainage` or this skill's documented domain.
- Use when this skill is already selected by the Hermes skill router and the task still fits the current goal.
- Don't use for: adjacent workflows with a more specific skill, generic Q&A, or tasks that lack evidence for this skill's domain.


Use this with `taskpool-control-plane` when the user asks to clear `blocked`, fix no-done stalls, or keep draining the Hermes taskpool until only true gates remain.

## Objective model

Do not treat `blocked=0` as a status-edit target. Treat it as a proof-preserving lifecycle-drain objective:

1. Snapshot counts, workers, selfcheck, review closeout, and blocked resolver output.
2. Classify blockers by `blocked_resolve_last_action` and gate failure, not by status alone.
3. Patch only systemic gate false positives or deterministic fallback gaps.
4. Drain via controller paths only.
5. Stop at explicit evidence/certification/human gates and emit a DecisionPacket/ContinuationPacket.

## Standard drain loop

Run the reversible loop, verifying after each cycle:

1. `brain_task_orchestrator.py auto-close-review --max-tasks <N> --authority autonomous-execution --json`
2. `brain_task_orchestrator.py auto-subtask-sync --write --actor <actor> --json`
3. `brain_task_orchestrator.py blocked-resolve-step --max-tasks <N> --authority autonomous-execution --actor <actor> --json`
4. If `next --json` says reconcile is required, do not stop at the advisory message. Run `brain_task_orchestrator.py reconcile --write --promote-due-retry --actor <actor> --json`, then re-run `next --json`.
5. `taskpool_dynamic_runner.py` or dispatch tick.
6. `agent_team_controller.py worker-jobs --json` and wait/read logs for live workers.
7. Re-read `list --json` counts and blocked classification.

## Active follow-through rule

When the user asks to “协助推进”, “继续推进”, “不要踢皮球”, or equivalent, do not merely report gates or recommend a next task. After safe resolver/reconcile steps, take the next dispatchable advisory/evolution card and advance one bounded evidence slice yourself: read its existing evidence, verify authoritative sources when needed, write a scoped evidence note, transition through normal lifecycle gates, and re-run `selfcheck/list/next`. Stop only at a real authority/proof boundary such as missing API/UI/readback evidence, explicit human approval, credentials/secrets, destructive changes, or external dispatch.

## Blocked classification

- `await_auto_subtasks`: parent is waiting for child evidence. Do not force parent done. Dispatch/finish child tasks first.
- `keep_blocked_missing_taxonomy_artifact`: historical discussion artifact may be pruned. If `multimodel_last_failures` yields taxonomy axes, use that deterministic fallback; only stop if both artifact and fallback taxonomy are unavailable.
- `keep_blocked_transient_retry_cap`: retry cap is preventing infinite churn. Require targeted evidence repair/certification; do not blind-retry.
- `keep_blocked`: inspect multimodel/proof failure. Treat explicit certification FAIL/T3 pause as a real gate.

## Known false positives

Advisory/evidence tasks often mention UI, browser, API, contracts, or fixtures as source material. Do not apply implementation UI/API closeout proof unless the task is actually an implementation/work closeout.

Pitfall examples:
- `FixtureKit` matching `fix`.
- `capability` matching `API`.
- `guidance` or metadata matching `UI`.

Use word-boundary regexes for English implementation hints and keep advisory `advisory-evidence-review-done` gated by deposited advisory evidence/report artifacts.

## Stop boundary

Stop and report a human/evidence gate when remaining blockers are:

- unfinished child subtasks;
- T3 rounds paused at max failures;
- retry cap reached without sufficient evidence;
- explicit multimodel certification FAIL;
- missing deposited advisory artifact.

Never force `done`, fabricate evidence, or downgrade product/work proof gates just to reach `blocked=0`.

## Reference

Detailed session-derived reference: `references/blocked-drain-gate-repair-2026-06-28.md`.
## Common Pitfalls

1. Applying this skill mechanically after the user's goal has shifted. Re-check the current request before acting.
2. Treating a plan, stale memory, or prior report as proof of completion. Verify with fresh readback.
3. Ignoring neighboring skills or narrower workflows that better match the task. Prefer the most specific applicable skill.
## Verification Checklist

- [ ] The current user request still matches this skill's trigger class.
- [ ] Required files, tools, commands, or external state were checked before action.
- [ ] Outputs, edits, or side effects were verified by readback or direct inspection.
- [ ] Boundaries, unresolved assumptions, and any deferred work were stated clearly.
