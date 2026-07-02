---
name: taskpool-runtime-reconciliation
description: Use when Hermes taskpool drain/dispatch stalls on claimed/running/retry rows, resource ceilings, orphaned worker claims, multimodel async jobs, or false active accounting.
---

# Taskpool Runtime Reconciliation
## When to Use

- Use when the user's request explicitly matches `taskpool-runtime-reconciliation` or this skill's documented domain.
- Use when this skill is already selected by the Hermes skill router and the task still fits the current goal.
- Don't use for: adjacent workflows with a more specific skill, generic Q&A, or tasks that lack evidence for this skill's domain.


Use this skill when taskpool is not draining because rows remain `claimed`, `running`, or `retry`, especially when `worker-jobs` appears empty or dispatch reports resource ceiling / already claimed conflicts.

## Core rule

Never mark a stuck `claimed` or `running` task done. Reconciliation may release an orphaned active row to `retry`/over-retry with evidence, but completion must still go through normal proof/lifecycle gates.

## Orphaned active claim checklist

Before releasing a claimed/running row, prove that it has no live owner:

1. Read taskpool rows with `brain_task_orchestrator.py list --json`.
2. Read agent worker registry with `agent_team_controller.py worker-jobs --json`.
   - If a live worker lists the task id, wait/read back instead of reclaiming.
3. Read multimodel async registry with `brain_task_orchestrator.py multimodel-intervention-jobs --json`.
   - If a live multimodel job lists the task id, wait/read back.
4. Inspect live process text for task id or run id in known owner commands:
   - `agent_team_controller.py`
   - `team-worker`
   - `hermes -p`
   - `multimodel_intervention`
   - `brain_task_orchestrator.py transition`
   - `parallel-claim-and-handoff`
5. Only when all owner checks are empty may canonical reconcile release the row to retry/over-retry with evidence such as `command:reconcile_orphaned_active_claim_no_live_owner`.

## Provider-health recovery before repeated multimodel drain

When many blocked tasks share `missing_required_model_consulted:<model>` / `missing_required_model_vote:<model>` and multimodel economy gates report `failed T3 rounds (max=5)`, do not keep running `blocked-resolve-step` in a loop. First separate live runtime availability from stale health/circuit-breaker state:

1. Run a real minimal provider/model smoke/probe for the missing required participant.
2. Read `~/.hermes/state/model-health.json`; if the smoke passed but the model remains `unhealthy`, fix the smoke/probe path to call `consult_models.record_model_health(..., ok=True)` so router/taskpool candidate filtering sees the recovery.
3. Rerun router/readiness and `multimodel-intervention-dry-run`.
4. Only allow a recovery rerun when the newly healthy required model observation is newer than the last failed multimodel round. This prevents unlimited retry loops while permitting a targeted evidence repair to reopen paused T3 gates.
5. If the rerun still fails on agreement, non-approve votes, provider parse errors, or unresolved severity issues, stop treating it as provider recovery and produce a targeted evidence/human-review packet instead of draining status again.
6. If the provider flaps during the real multimodel fanout (smoke PASS, then fanout timeout re-marks `model-health.json` unhealthy), do not keep smoke→retry looping. Finish any live jobs, read worker/multimodel logs, record which tasks returned to blocked, and stop at human/targeted-evidence gate unless a concrete adapter/timeout fix is in scope.

## Drain loop after reconciliation

Run the normal safe loop:

1. `reconcile --write --promote-due-retry`
2. `auto-close-review`
3. `auto-subtask-sync --write`
4. `blocked-resolve-step`
5. `boundary-reclassify-step --lane all --write` when boundary-safe advisory/evolution tasks may need reclassification
6. dispatch/dynamic runner
7. wait for live workers, then read back jobs/counts before acting again

If a single-lane dynamic runner reports idle/no dispatchable task after recovery, do not stop there. Compare `dispatch-dry-run --json` and `parallel-dispatch-dry-run --max-agents <n> --json`; if reconcile is required, run it again, and if parallel dry-run reports safe slots, use an explicit bounded `brain_task_dispatch_tick.py --summary --print-always --parallel-autorun --max-agents <n>` and then read back `worker-jobs` plus canonical row counts. See `references/human-escape-to-parallel-progress.md`.

## Human-escape / terminal-envelope recovery

When `taskpool_escape_guard.py --json` shows `post_ack_terminal_count` or `worker_timeout_count`, do not blindly dispatch. First classify whether the breaker is actually active:

1. If `human_escape_triggered=true`, inspect `post_ack_terminal_rows`, latest taskpool worker logs, canonical task statuses, `worker-jobs`, multimodel jobs, and process text.
2. If every terminal envelope maps to a lifecycle transition already recorded as `retry`/`blocked` and no live owner remains, acknowledge with `taskpool_escape_guard.py --ack-reviewed --reason '<review receipt>' --json`, then read back `human_escape_triggered=false` before dispatching.
3. If `human_escape_triggered=false` but `post_ack_terminal_count>0`, treat it as a warning, not an automatic stop. Record/mention the residual terminal row, but only ack if the guard accepts it; otherwise continue bounded safe cleanup such as `blocked-resolve-step` and readback.
4. Never convert FAILED/TIMEOUT terminal envelopes into `done`; they only justify retry/blocked recovery or a human-intervention packet.

## Orphaned parallel handoff / actor-mismatch release

Parallel dispatch can leave handoff-only claims: the task is `claimed`, `worker-jobs` has no alive job, no taskpool-worker log exists for the batch, and process text has no `run_id`/task owner. Release these only after the full owner checklist is negative.

- A normal `release` may fail because the task is claimed by `hermes-parallel` while the operator actor is different.
- Use `--force` only after documenting: `worker-jobs alive=0`, multimodel alive=0, no matching process owner, and only handoff files exist for the batch.
- Release to `retry` (or policy-selected recovery status), never `done` or `review`.
- Re-read immediately; dynamic runners can race and claim another task while you are reconciling.

## Mission-envelope boundary repair during drain

If dispatch/dry-run fails with `mission_envelope_missing` or `evolution_architecture_alignment_missing`, do not bypass the boundary gate or force lifecycle advancement. Repair the task note's structural contract first, then require fresh readback from `selfcheck` / `boundary-check`.

- Use known `architecture_target` values only; an unknown target can keep the entire boundary check failed.
- Add `anti_drift_check` alongside `capability_delta` and `acceptance_evidence` for evolution-lane tasks.
- Mission envelope refs must be structured evidence refs. Plain strings such as `pending` may still fail as `handoff_artifacts:structured_ref`, `proof_artifacts:structured_ref`, or `ratification_artifact:structured_ref`; prefer explicit placeholders like `proof:handoff-pending`, `proof:implementation-proof-pending`, and `proof:ratification-pending`.
- Treat this repair as dispatch eligibility only. It is not delivery proof and never justifies `done`.

## Foreground consume timeout recovery

If a foreground `agent_team_controller.py consume-claimed ...` or terminal wrapper times out, it can leave a task in `running` even after the worker registry is empty. Handle this as an orphaned active claim: prove `worker-jobs` empty for the task, multimodel jobs empty for the task, and no process owner contains the task id/run id; then release to `retry` only with an evidence-bearing reason. Never mark done from a timeout or from absent worker state.

## Pitfalls

- `worker-jobs` being empty is not enough; check multimodel job registry and process text too.
- Dispatch can fail with “task already claimed” after a race; re-read canonical rows and worker registry before patching anything.
- A background dynamic runner may claim new work during manual reconciliation; wait for any visible `agent_team_controller.py cycle`/`consume-claimed` process to exit before declaring a claim orphaned.
- `auto-close-review` may legitimately move a `review` task back to `retry`/`pending` when multimodel certification fails; this is correct gate behavior, not a failed closeout.
- `await_auto_subtasks` and `keep_blocked_transient_retry_cap` are usually true evidence/backoff boundaries, not proof-gate bugs.
- Fix repeated false-active stalls in canonical `reconcile`/dispatch accounting; avoid one-off task-frontmatter edits except as audited emergency repair.

## References

- `references/orphaned-active-claim-reconciliation.md` — condensed procedure and anti-conditions captured from a blocked-drain repair session.
- `references/human-escape-terminal-envelope-recovery.md` — post-ack terminal envelope review, human-escape ack, and handoff-only claim recovery checklist.
- `references/mission-envelope-and-foreground-consume-recovery.md` — boundary repair for mission-envelope invalids and foreground consume timeout/orphaned-running recovery.
- `references/human-escape-to-parallel-progress.md` — bounded sequence for acking reviewed terminal envelopes, deterministic cleanup, and using explicit parallel dry-run/autorun when single-lane dynamic runner idles.
## Common Pitfalls

1. Applying this skill mechanically after the user's goal has shifted. Re-check the current request before acting.
2. Treating a plan, stale memory, or prior report as proof of completion. Verify with fresh readback.
3. Ignoring neighboring skills or narrower workflows that better match the task. Prefer the most specific applicable skill.
## Verification Checklist

- [ ] The current user request still matches this skill's trigger class.
- [ ] Required files, tools, commands, or external state were checked before action.
- [ ] Outputs, edits, or side effects were verified by readback or direct inspection.
- [ ] Boundaries, unresolved assumptions, and any deferred work were stated clearly.
