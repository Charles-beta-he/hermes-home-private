# Taskpool lifecycle/dashboard/proof read-only verification — 2026-06-12T17:25 +08:00

Scope: one bounded local-only mission slice after taskpool_status_changed signal. No push/deploy/secrets/external sends/destructive actions. Runtime env gate used: `HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN=1`.

Commands run from `/Users/charles`:

```bash
export HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN=1
python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py lifecycle --json
python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py dashboard --json
python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py proof-check --include-active --json
python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py list --json
python3 /Users/charles/.hermes/scripts/agent_team_controller.py worker-jobs --json
```

Observed outputs:

- `lifecycle --json`: `status=FAIL`, `task_count=323`, `invalid_count=75`; invalid sample begins with mission envelope missing `evidence_refs:structured_ref` / `ratification_artifact:structured_ref` on historical done tasks.
- `dashboard --json`: `status=OK`, `write=false`, dashboard paths resolved, `active_count=6`, `multimodel_convergence.total_active=6`, `multimodel_triggered=4`, `pending_ids` include uumit/qdrant/cloakbrowser/turbovec parent tasks.
- `proof-check --include-active --json`: `status=FAIL`, `checked_count=323`, `failure_count=72`, `warning_count=14`; failure categories: 67 `mission_envelope_structured_ref`, 5 `unstructured_evidence`; warnings are terminal invalid autorun proof hash debts.
- `list --json`: status counts were `retry=1`, `blocked=4`, `review=1`; active-like tasks: turbovec retry; uumit/qdrant parent tasks blocked; uumit relay-ordering blocked; qdrant framing blocked; cloakbrowser parent review.
- `agent_team_controller.py worker-jobs --json`: `status=OK`, `alive_count=0`, `job_count=147`; no live multimodel worker remained after the read-only gated slice.

Conclusion: dashboard read-only projection is OK, but lifecycle/proof-check must remain non-green due to existing structured mission-envelope and unstructured evidence debt. The local no-multimodel env gate did not leave live agent-team jobs in this slice.
