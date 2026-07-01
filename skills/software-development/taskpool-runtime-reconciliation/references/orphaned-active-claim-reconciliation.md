# Orphaned active claim reconciliation during blocked-drain

Applicability: taskpool drain sessions where `claimed` or `running` rows remain after worker/multimodel execution, especially when draining with the safe strategy “execute pending child tasks + targeted evidence repair child”.

Do not manually mark stuck `claimed`/`running` tasks done. First prove whether the active row still has a live owner:

1. Read canonical state: `brain_task_orchestrator.py list --json` and classify `claimed`/`running`/`retry`/`blocked`.
2. Read worker registry: `agent_team_controller.py worker-jobs --json`; keep claims alive if a live job lists the task id.
3. Read multimodel registry: `brain_task_orchestrator.py multimodel-intervention-jobs --json`; keep claims alive if a live multimodel job lists the task id.
4. Check process text for task id or run id in known owner commands: `agent_team_controller.py`, `team-worker`, `hermes -p`, `multimodel_intervention`, `brain_task_orchestrator.py transition`, `parallel-claim-and-handoff`.
5. Only when all owner checks are empty should reconcile release the active row to `retry`/over-retry with explicit evidence such as `command:reconcile_orphaned_active_claim_no_live_owner`. Never close it as done.
6. After releasing, run the normal loop: `reconcile --write --promote-due-retry`, `auto-close-review`, `auto-subtask-sync --write`, `blocked-resolve-step`, then dispatch/dynamic runner.
7. If any worker is alive, wait and read back; do not reclaim live work.

Pitfalls:
- Resource ceiling can be held by false active rows even when `worker-jobs` is empty; verify multimodel registry and process text before acting.
- The durable fix belongs in canonical `reconcile` / dispatch accounting, not one-off manual task edits.
- Do not confuse true `await_auto_subtasks` or `keep_blocked_transient_retry_cap` with systemic gate bugs. Those require child evidence, retry backoff, or targeted repair, not proof-gate bypass.

Anti-conditions:
- Do not use this to override a live worker, live multimodel job, human-input gate, external proof gate, or credential/payment boundary.
- Do not encode a particular task id, branch, or project path as a global rule; those belong in project profile or task evidence.
