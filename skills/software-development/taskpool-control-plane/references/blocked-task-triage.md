# Blocked taskpool triage: loop non-convergence vs ordinary blockage

Use this when the user asks to check blocked taskpool items.

Procedure:

1. Query broad list first, not only `list --status blocked`.
   - Some CLI versions may not accept every status filter consistently; `list --json` and local filtering by `status == blocked` is more robust.

2. For each blocked task, report:
   - id/title/path
   - priority/lane/project
   - dispatchable flag
   - multimodel_intervention_required and reasons
   - whether it is ordinary blocked work or evolution-loop non-convergence

3. Treat `evolution_lane` + `loop_non_convergence` specially.
   - Do not simply change it back to `pending`.
   - Inspect task evidence, acceptance criteria, ratification artifact, and non-convergence reason.
   - Recommend evidence-first unblock or real multimodel certification before changing status.

4. Run control-plane health checks separately:
   - `brain_task_orchestrator.py selfcheck --json`
   - `brain_task_orchestrator.py lifecycle --json`
   - Distinguish blocked task count from lifecycle evidence-format drift. A lifecycle FAIL caused by historical `evidence_not_structured` is not necessarily the cause of current blocked tasks.

Reporting style:
- Start with the blocked count.
- Then list each blocked item with why it is blocked and the safest next action.
- End with a prioritized unblock recommendation.
