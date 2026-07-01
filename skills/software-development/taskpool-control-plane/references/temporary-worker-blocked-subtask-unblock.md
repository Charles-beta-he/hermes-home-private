# Temporary worker pattern for blocked-parent child unblock

Use when the user asks to unblock `blocked` taskpool parents by advancing their open child tasks, especially convergence/narrowing children.

## When to use

- `blocked-resolve-step --authority dry-run --json` says a parent is `await_auto_subtasks`.
- The parent has open children in `pending`, `retry`, or `blocked`.
- The user explicitly wants a temporary worker / single worker rather than broad dispatch.

## Safe sequence

1. Read current task state and blocked resolver dry-run.
   - Collect parent id, open child ids, child status, lane/project, and `auto_subtask_parent_artifact` / discussion artifact path.
2. Prefer a child whose required discussion artifact exists.
   - If the artifact path is missing, do not expect the worker to complete; either pick another child or produce a bounded blocker explaining the missing evidence.
3. Check human escape before spawning a worker.
   - If `human_escape_check()` is active, inspect post-ack FAILED/BLOCKED envelopes.
   - Only advance the escape watermark after classifying them as reviewed terminal stale/timeout rows and ensuring there is no live orphan that would make the next worker unsafe.
   - Do not change envelope terminal states just to clear escape.
4. Claim exactly one child with a distinct actor/run id, for example `hermes-temp-unblock-worker`.
   - Use normal lifecycle claim first.
   - If `auto-claim-and-handoff` returns `allowlist_miss` but the child is a legitimate open subtask and the user requested a temp worker, a direct governed `claim` is acceptable; do not mark done.
5. Start `agent_team_controller.py consume-claimed` with `--claimed-json` containing only that child and `--max-agents 1`.
6. Wait/read back the worker result.
   - If it reaches `review`, run `auto-close-review` / `blocked-resolve-step` normally.
   - If it returns `blocked`, read the task note and envelope trace to identify the exact missing evidence.
7. If the worker blocked only because it failed to bind an already-existing artifact, a bounded manual evidence repair is allowed:
   - write a concise artifact under an evidence path,
   - hash it,
   - move the child to `review` with `artifact:` and `proof:sha256:` evidence,
   - do not transition parent to `done`.
8. Rerun `blocked-resolve-step` and read back selfcheck/list counts.

## Pitfalls

- `human_escape_active` will cause `consume-claimed` to release the child to `retry` without executing. Treat this as a safety gate, not a worker failure.
- Many old convergence children reference historical `discussion_result.json` paths that no longer exist. These usually cannot be completed by a worker without reconstructing evidence; prefer a sibling with an existing artifact.
- A worker may report `blocked` even when it produced useful diagnostic output; always inspect the task note/proof/evidence before requeueing blindly.
- Do not use `--force` to move a parent or child to `done`. If a force is needed only because the worker already released the claim and you have real artifact evidence, force at most `blocked -> review` and explain why in the transition reason.
- Keep the scope at one child per temp worker unless the user explicitly asks for batch unblock.

## Verification checklist

- Human escape is false or a new ack receipt exists with reviewed terminal failures only.
- Temporary claim has actor/run id and a finite TTL.
- Worker process exited or its live PID is known.
- Child status changed or a precise blocker was recorded.
- Evidence artifact path and sha256 are attached for any manual `review` transition.
- Parent remains blocked/review until normal proof/multimodel gates pass.
