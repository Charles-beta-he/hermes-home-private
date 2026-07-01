# Authorized local taskpool dispatch write + readback

Use when the user explicitly authorizes local taskpool lifecycle/dispatch execution after a DecisionPacket-style gate, e.g. “C 真正写入”.

Applicability:
- Scope is local taskpool/brain lifecycle state only.
- User has authorized the exact previously named boundary: claim / reconcile / dispatch / worker consume.
- External adapters, notifications, deploy/push, credentials, and destructive actions remain closed unless separately named.

Anti-conditions:
- Do not treat this as authority to mark `done`, force close, push/deploy, write Apple/Lark/Kanban, or bypass multimodel/proof gates.
- Do not execute stale handoff payloads after readback says the task is no longer claimed.
- Do not claim “complete” when worker exits to `blocked`; report the real terminal/intermediate state.

Procedure:
1. Preflight and classify.
   - If Agent OS routing is active, run status/route preflight and treat it as advisory evidence only.
   - State the smallest opened boundary: local taskpool lifecycle/dispatch write.

2. Fresh readback before write.
   - Run `brain_task_orchestrator.py selfcheck --json`.
   - Run `brain_task_orchestrator.py dispatch-dry-run --json`.
   - Capture `dispatchable`, `next.id`, lane, status, invalid_count, and dispatchable_count.

3. If dispatch-dry-run says reconcile required, run bounded reconcile.
   - `brain_task_orchestrator.py reconcile --write --json`.
   - Repeat only until dispatchable becomes true or the action signature repeats; stop on repeat to avoid reconcile loops.
   - Re-read selfcheck and dispatch-dry-run after each bounded loop.

4. Open the official write path, not manual lifecycle forcing.
   - Prefer `brain_task_dispatch_tick.py --print-always --autorun-step --parallel-worker-foreground --event-next-tick-depth 1` for governed claim -> running -> review/retry/blocked handling.
   - `auto-claim-and-handoff` / `autorun-runner` may legitimately stop at handoff-only; that is a receipt, not worker execution.
   - If a precise `consume-claimed --claimed-json ...` attempt returns `not_claimed:pending`, discard that handoff as stale and do fresh readback; do not replay it.

5. Worker readback.
   - Inspect `agent_team_controller.py worker-jobs` for alive_count, job_id, batch_id, task_ids, and log path.
   - Wait bounded windows for the worker; do not kill a live worker unless it is stale/unsafe by policy.
   - After worker exit, run list/selfcheck and record final per-task states.

6. Report actual state.
   - Valid outcomes include `review`, `retry`, `blocked`, `pending`, or still `running`; only report `done` if proof-gated review->done actually happened.
   - If target ends `blocked`, read the task note tail and cite the latest lifecycle proof line such as `running -> blocked ... worker blocked`.
   - Preserve the distinction: “true write executed” can be complete even when the task’s product work is blocked.

Verification checklist:
- selfcheck PASS after writes.
- invalid_count remains 0.
- No stale claim remains unless a live worker is still legitimately running.
- Worker alive_count read back before final status claim.
- External side effects explicitly remain unopened unless separately authorized.
