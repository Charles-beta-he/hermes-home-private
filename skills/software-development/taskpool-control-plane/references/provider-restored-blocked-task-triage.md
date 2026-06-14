# Provider-restored blocked task triage

Use this when the user says a provider/subscription recovered (for example Claude Code or Gemini) and asks why taskpool items are still `blocked`.

## Core distinction

Provider recovery does not automatically unblock historical task states. Separate:

1. Current provider availability / live jobs
   - CLI/provider can be present and fresh probes may succeed.
   - `skipped_due_to_quota: []` means the current router is not explicitly skipping the model for quota.
   - Live `multimodel-intervention-*` / `consult_models.py` processes mean new certification work may already be running.

2. Historical certification state in task notes
   - `multimodel_last_gate_status: FAIL`, `multimodel_last_decision: CONTINUE_LOOP`, `not_certified`, `PASS_ADVISORY_ONLY`, and `loop_non_convergence` remain blockers until fresh evidence/discussion is written back.
   - Failures like `best_within_constraints_missing:<model>` or `non_approve_vote:<model>:amend` are not the same as current quota failure. Treat them as certification results unless paired with a live provider/quota error.

3. Worker control-plane escape
   - `human_escape_active_preclaim` / `human_escape_triggered=true` blocks ordinary agent-team claims even when provider subscriptions are back.
   - Inspect post-ack failures before ACK/retry. Repeated `Worker timeout, max retries` after the latest ACK is a worker/proof/timeout problem, not proof that the provider is still unavailable.

## Read-only evidence sequence

Run/read these before changing task state:

```bash
ps aux | grep brain_task_orchestrator.py | grep -v grep || true
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py lifecycle --json
python3 ~/.hermes/scripts/agent_team_controller.py status --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-jobs --json
python3 ~/.hermes/scripts/taskpool_dynamic_runner.py --json
```

If `human_escape_triggered=true`, inspect the envelope bus with `coalesce(completed_at, updated_at)` relative to the latest ACK:

```bash
cat ~/.hermes/state/envelope_escape_ack.json
sqlite3 -json ~/.hermes/state/envelope_bus.db \
  "SELECT project,error,count(*) AS cnt FROM envelopes WHERE status='FAILED' AND coalesce(completed_at, updated_at) > '<ACKED_AT>' GROUP BY project,error ORDER BY cnt DESC;"
sqlite3 -json ~/.hermes/state/envelope_bus.db \
  "SELECT id,type,status,project,title,error,retry_count,updated_at,completed_at FROM envelopes WHERE status='FAILED' AND coalesce(completed_at, updated_at) > '<ACKED_AT>' ORDER BY coalesce(completed_at, updated_at) DESC LIMIT 20;"
```

## Classification rules

For each blocked task, classify as one of:

- `fresh-provider-rerun-candidate`: provider was previously blocked or result is stale, no open convergence children, and a new multimodel run is appropriate.
- `awaiting-convergence-children`: resolver reports `await_auto_subtasks` / open children; finish children before parent ratification.
- `parent-targeted-refresh-needed`: children are done or advisory pass exists, but parent remains `FAIL` / `PASS_ADVISORY_ONLY` / missing taxonomy artifact; do a parent-level targeted evidence refresh rather than blindly requeueing.
- `ordinary-worker-escape`: blocked by `human_escape_active_preclaim` or post-ack worker failures; inspect and clear escape only after failures are understood.
- `historical-lifecycle-debt`: `lifecycle --json` fails on old evidence/format drift; report separately and do not confuse it with current blocked root cause.

## Safe reporting pattern

Report:

1. Active status counts (`running`, `blocked`, `pending`).
2. Whether live multimodel jobs/processes are running.
3. Whether provider recovery is visible as current availability or only inferred.
4. For each blocked task: title/id, priority/lane/project, certification state, resolver action, and safest next action.
5. The immediate global blocker if present (`human_escape_active_preclaim`, no dispatchable task, stale claim, etc.).

Do not bulk-promote blocked tasks to `pending` just because subscriptions recovered. Provider recovery only justifies fresh certification attempts where the task has no unresolved child/evidence prerequisite and no active duplicate run.