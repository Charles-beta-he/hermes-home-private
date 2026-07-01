# Local lifecycle readback after governed dispatch authorization

## Applicability

Use this for local taskpool/control-plane work when an operator-facing status surface needs to show real lifecycle state, or when the user has explicitly authorized local-only lifecycle writes. Scope is local taskpool state, local proof/handoff logs, derived local dashboards, and read-only local status projection.

## Anti-conditions

Do not use this to justify external adapter writes, message sending, publishing, deployment, credential entry, payment, destructive actions, broad fan-out, or force-completion. Completion remains governed by lifecycle/proof/certification gates.

## Authorized local dispatch pattern

1. Fresh readback first:
   - `brain_task_orchestrator.py selfcheck --json`
   - `brain_task_orchestrator.py dispatch-dry-run --json`
   - optionally `brain_task_orchestrator.py list --json` for exact state.
2. If dispatch dry-run says reconcile is required, run local reconcile only after authority is present:
   - `brain_task_orchestrator.py reconcile --write --json`
   - Bound repeats and stop if the reconcile signature repeats.
3. Prefer official control-plane paths over hand-mutating task notes:
   - `auto-claim-and-handoff` for claim/proof handoff.
   - `autorun-runner` for bounded claim+handoff.
   - `brain_task_dispatch_tick.py --print-always --autorun-step --parallel-worker-foreground --event-next-tick-depth 1` for official worker consumption.
4. Read back after each side effect:
   - `selfcheck --json`
   - `dispatch-dry-run --json`
   - `agent_team_controller.py worker-jobs`
   - focused task state inspection for claimed/running/review/blocked/retry/pending.
5. If a worker releases a task to `blocked`, treat it as a governed outcome. Diagnose rather than retry-loop:
   - `blocked-resolve-step --task <id> --authority <authorized-tier> --json`
   - `review-gap-scan --task <id> --authority <authorized-tier> --json`
   - retry/promote only if resolver/readback says it is safe.

## Read-only projection pattern

When projecting local taskpool state into a status surface:

- Keep the endpoint read-only. It may call readback commands; it must not run reconcile, claim, dispatch, or lifecycle transitions.
- Project real lifecycle counts and task identifiers, not just dry-run messages.
- Prioritize blocked-task needs-human cards over generic warning noise in top mobile/operator cards; otherwise real blocked work can be hidden behind warnings.
- If full task-list JSON includes large task bodies/evidence, child stdout can exceed small buffers. Prefer a bounded summary command when available; otherwise set a realistic bounded buffer and prove it with live smoke. Capture the retry/fix pattern, not a permanent negative claim about the tool.

## Verification checklist

- Contract test: selfcheck + dispatch dry-run + task-list fixtures produce blocked count, active-task todos, and blocked-task cards.
- Mobile/operator merge test: warnings plus one blocked item still surfaces the blocked item in top needs-human cards.
- Live smoke reads the local status endpoint and returns the expected projection schema.
- Relevant full local gate passes.
- Read back no residual smoke process/port before final reporting.

## Reporting rule

Claim/handoff, running worker, blocked, pending, review, and done are distinct states. Report exactly which state occurred and cite fresh readback. Do not call a task complete because a handoff was created or a worker started.
