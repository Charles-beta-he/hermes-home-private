# Safe taskpool drain loop: pending children + targeted evidence repair

Applicability:
- Use when the user asks to continue/drain the taskpool, restore normal flow, or run until no executable work remains.
- Applies to local taskpool control-plane operations where task notes are the SSOT and workers may run asynchronously.
- Does not authorize forced completion, fabricated evidence, external side effects, credential entry, broad dispatch, publish/deploy/push, or destructive actions.

Default safe strategy:
1. Treat `auto-close-review -> reconcile --write --promote-due-retry -> auto-subtask-sync --write -> blocked-resolve-step -> review-gap-scan --write -> parallel-dispatch-dry-run -> parallel-claim-and-handoff -> consume-claimed --background` as the standard drain cycle.
2. Use an actor name that encodes intent, e.g. `safe-pending-child-targeted-repair`.
3. Prefer `parallel-dispatch-dry-run --max-agents 8 --lane all --json` before claims; only consume tasks that were actually claimed.
4. Start bounded background loops with notify/readback and keep polling real state; do not infer completion from old loop summaries.
5. Re-check `worker-jobs`, `multimodel-intervention-jobs`, task counts, and selfcheck before any completion claim.

Blocked normalization pattern:
- If a parent is blocked only because auto-generated child subtasks are still open, move/keep it in a flow state such as `pending` and protect it with dispatch blockers until children finish.
- If a parent's children are all done but multimodel/certification is still not PASS, release to retry/targeted repair flow rather than leaving it permanently `blocked`.
- If a task requires true browser/UI/API proof, FixtureKit proof, credentialed external access, or human proof, keep it as a hard boundary; do not synthesize evidence.

Targeted evidence repair child pattern:
- Run `review-gap-scan --max-tasks <n> --write --actor targeted-evidence-repair --json` during drain cycles.
- `created_count=0` is an acceptable no-op; still continue reconciliation/dispatch if dry-run shows eligible tasks.
- For retry-cap or non-convergence items, create/execute narrowed child work only when it preserves the parent objective and red lines.

Orphaned active claim pattern:
- If task status is `claimed` or `running` but `worker-jobs` has no live owner and process readback does not show the task/run id, reconcile should release it to retry/over_retry with an evidence entry.
- Never mark orphaned work done.
- After background notifications, re-read live jobs and task state before claiming the pool is clear.

Completion/readback checklist:
- `python3 -m py_compile ~/.hermes/scripts/brain_task_orchestrator.py` if code changed.
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json` => PASS with no failures/warnings.
- `python3 ~/.hermes/scripts/agent_team_controller.py worker-jobs --json` for live worker count and task ids.
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-jobs --json` for live multimodel jobs when applicable.
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json` summarized by status.
- Report honestly: `blocked=0` + live workers means normal flow, not full completion. Full completion requires no active task rows or an explicit hard-boundary packet.

Anti-conditions:
- Do not store one session's task ids as reusable instructions; examples are only diagnostic shape.
- Do not bypass proof/lifecycle gates to satisfy a request for zero blocked.
- Do not claim UI/UX or external proof completion from advisory/model output alone.
