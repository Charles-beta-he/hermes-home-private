# Subscription recovery full-pool advance

Use when Claude Code / Gemini / other subscription-backed model routes recover and the user asks to unblock or fully advance the taskpool.

## Core lesson

Subscription recovery is only a provider availability signal. It does not automatically unblock tasks whose task notes still record failed / advisory multimodel certification, loop non-convergence, open convergence children, or stale `running` claims. Advance through the taskpool gates and write fresh evidence; do not bulk-edit blocked tasks to pending/done.

## Safe sequence

1. Re-baseline first:
   - `brain_task_orchestrator.py list --json`
   - `brain_task_orchestrator.py next --json`
   - `brain_task_orchestrator.py dispatch-dry-run --json` or `parallel-dispatch-dry-run --json`
   - `brain_task_orchestrator.py multimodel-intervention-jobs --json`
   - `agent_team_controller.py status --json`
   - `taskpool_dynamic_runner.py --json`
   - `brain_task_orchestrator.py selfcheck --json`

2. If `taskpool_dynamic_runner.py --json` says `human_escape_active_preclaim`, diagnose post-ack failures before acknowledging:
   - Read `agent_team_controller.py status --json`.
   - Query post-ack `FAILED` envelopes from `~/.hermes/state/envelope_bus.db` using `coalesce(completed_at, updated_at) > acked_at`.
   - If failures are understood historical worker timeouts / max retries and the user has approved full-pool advance, use `envelope_bus.py ack-escape "reason"`.
   - Verify `human_escape_triggered=false` and `since_ack.failures=0 blocks=0`.

3. Run the normal automation path after escape is clear:
   - `taskpool_dynamic_runner.py --json`
   - Interpret `no_additional_boundary_safe_slots` as healthy capacity/boundary saturation, not failure.

4. Check for false-running multimodel claims:
   - `list --json` may show tasks `running` with `claimed_by=hermes-multimodel`.
   - `multimodel-intervention-jobs --json` may show `alive_count=0` and matching job logs may be empty.
   - This is not proof of completion. Requeue the task with structured evidence, e.g.:
     `transition <task-id> --to pending --actor hermes-full-pool-advance --authority budget-handoff --reason full_pool_advance_requeue_false_running_no_live_multimodel_process_or_job_output --evidence command:multimodel-intervention-jobs alive_count=0 --force --json`

5. Prefer foreground certification to prove provider recovery:
   - Run one targeted `multimodel-intervention-step --task <id> --json` in foreground when async jobs repeatedly exit with empty logs or false-running state.
   - A good proof includes `models_consulted` showing recovered routes such as Claude/Gemini, a `discussion_result.json` artifact path, and gate fields.
   - Treat `PASS_ADVISORY_ONLY` as evidence, not closeout authority. It usually requeues to `pending` with `CONTINUE_LOOP`.

6. After real multimodel writeback, rerun:
   - `blocked-resolve-step --json`
   - `next --json`
   - `selfcheck --json`
   - `proof-check --json`
   - `evidence-spine --json`

## Interpretation rules

- `certified/PASS/passed` means the task can proceed to implementation/review evidence; it is not automatically `done`.
- `PASS_ADVISORY_ONLY` proves advisory consultation only; do not close implementation/evolution tasks with it.
- `loop_non_convergence` parents with open children should wait for children; parents with completed children often need targeted parent ratification refresh, not more random decomposition.
- If async model workers exit with `-15` or empty logs but foreground runs succeed, capture the false-running recovery and leave a follow-up to fix the async control-plane path rather than declaring provider failure.

## Good final state

- Human escape is clear or explicitly identified as the remaining boundary.
- False-running claims are either active with live jobs or requeued with evidence.
- At least one real foreground or background certification produced a durable `discussion_result.json`.
- Health gates (`selfcheck`, `proof-check`, `evidence-spine`) pass or have classified non-blocking historical debt.
- Remaining blocked tasks are named by blocker class: certification not PASS, open convergence children, missing historical taxonomy artifact, or implementation evidence not landed.
