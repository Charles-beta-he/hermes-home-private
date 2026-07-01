# Blocked drain root-cause packets

Applicability: Hermes/local-brain taskpool drain work where `list --json` or watch reports show blocked/retry/running churn and the user authorizes continuing, but no exact permission exists to force `done` or bypass proof/certification gates.

Anti-conditions:
- Do not use this pattern to force-close tasks, fabricate proof, delete evidence debt, kill fresh active workers, or bypass multimodel certification.
- Do not treat `blocked=0` as full completion when retry/running/claimed tasks remain; report the residual lifecycle state.
- Do not store one session's blocked task IDs as a durable rule; regenerate packets from live taskpool state each time.

## Procedure

1. Read live state with `brain_task_orchestrator.py list --json` and summarize counts for `blocked`, `retry`, `pending`, `running`, `claimed`, and `review`.
2. For each blocked task, create a compact root-cause packet with:
   - task id/title/project/lane/priority/retry_count;
   - completion gate and required authority;
   - latest multimodel gate/decision/failures;
   - evidence/artifact refs head only, not full dumps;
   - class, e.g. `multimodel quorum incomplete`, `multimodel disagreement`, `design packet incomplete`, or `evidence/certification unresolved`;
   - safe next action and explicit boundary: no force-done; require fresh proof/readback for lifecycle closeout.
3. Write the packet to an ignored evidence/report location such as `~/.hermes/evidence/taskpool/...` if available. Treat it as operator evidence, not a global memory.
4. Run the safe drain loop, reading back after each step:
   - `reconcile --write --promote-due-retry`
   - `blocked-resolve-step --authority dispatch-hint`
   - `auto-close-review`
   - `dispatch-dry-run` / `parallel-dispatch-dry-run`
5. If blocked tasks are released to retry/pending, verify whether workers or multimodel jobs are now active. Fresh `running`/`claimed` inside TTL is progress, not a stale claim.
6. For eligible certification gaps, start only the governed path:
   - `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 brain_task_orchestrator.py multimodel-intervention-step --task <id> --background --json`
   - or `parallel-claim-and-handoff --write` followed by the controller consumer when the command returns claimed handoffs.
7. Monitor active jobs/processes until they complete or reach TTL. Then run another reconcile/blocked-resolve/auto-close cycle.
8. Finish with readback evidence: selfcheck, proof-check, watch report, lifecycle counts, dispatchable count, active tasks, and scoped git status.

## Pitfalls

- `blocked-resolve-step` can legitimately return `resolved` while the task moves to `retry` rather than `done`; this means the next repair/certification route is open, not that the work is complete.
- Parent tasks with all auto-subtasks done may still require parent certification refresh. Do not mark them done from child evidence alone.
- `PASS_ADVISORY_ONLY` is not completion authority for work/product/evolution closeout. It can unblock or inform the next slice, but lifecycle closeout still needs implementation/project evidence and the configured completion gate.
- If a controller command is backgrounded manually, quote JSON safely. Prefer writing claimed handoffs with `python3 -c '...' > /tmp/claimed.json` and passing `--claimed-json "$(cat /tmp/claimed.json)"`; malformed heredocs can fail before the controller sees the claims.
- A final state such as `blocked=0, retry>0, running>0` is a valid safe-drain boundary. Report it honestly and continue only after active jobs finish or TTL/stale-claim policy applies.

## Verification checklist

- [ ] Root-cause packet exists and cites live readback, not stale session notes.
- [ ] No task was force-closed or marked done by a worker.
- [ ] All lifecycle mutations were through orchestrator commands with JSON readback.
- [ ] Fresh active workers/jobs are either monitored or left within TTL with their task ids reported.
- [ ] `selfcheck` is PASS or failures are classified.
- [ ] `proof-check` is PASS or remaining warnings/failures are classified.
- [ ] Watch report returns and does not hang.
