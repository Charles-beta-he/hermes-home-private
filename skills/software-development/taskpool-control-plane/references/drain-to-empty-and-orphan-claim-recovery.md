# Taskpool drain-to-empty and orphan-claim recovery

Use when the user asks to continue operating the taskpool until it is empty, or to keep unblocking/re-dispatching tasks until a real gate is reached.

## Applicability

- The user has explicitly authorized continued local taskpool advancement.
- The work stays inside the local taskpool/control-plane: task notes, dispatch ticks, retry/review/blocked lifecycle, evidence artifacts, and local workers.
- You still must not bypass proof, multimodel certification, completion gates, external side effects, credentials, destructive actions, or `done` authority.

## Objective model

Success is not “force all tasks to done.” Success is:

1. Drain every safe local/reversible lifecycle transition available.
2. Keep workers running only through governed claim/handoff/consume paths.
3. Convert stale/orphaned execution state to retry/review/blocked through existing lifecycle commands.
4. Stop only when active count reaches zero or the remaining tasks are blocked by a hard gate such as missing proof, missing artifact, multimodel quorum, credentials, external side effects, or destructive authority.
5. Report the smallest actionable intervention packet if a hard gate remains.

## Safe drain loop

A governed drain loop should repeatedly run these, with readback after each cycle:

1. `auto-close-review --authority autonomous-execution` — never force `done`.
2. `blocked-resolve-step --authority autonomous-execution` — let parent/child state sync naturally.
3. `reconcile --write --promote-due-retry` — use retry promotion rather than manual status edits.
4. `boundary-reclassify-step --write` — only for safe pending/retry advisory boundary splits.
5. `review-gap-scan` — discover missing proof/evidence; do not invent it.
6. `auto-subtask-sync --write` — sync child progress to parents.
7. `brain_task_dispatch_tick.py --parallel-autorun ...` — claim and consume only when scheduler gates allow.
8. If multimodel intervention is queued, use the governed `multimodel-intervention-step` path; if it skips or fails closed, record that gate rather than forcing closure.

Between cycles:

- Read `agent_team_controller.py worker-jobs --json`.
- If workers are alive, wait instead of double-claiming.
- If scheduler says `wait_for_running_or_claimed_completion`, do not blindly claim more work.
- If scheduler says `boundary_refinement_or_batch_merge`, prefer boundary reclass/merge planning over more claims.

## Human escape watermark

If event-driven workers silently skip consumption, check `envelope_bus.human_escape_check()`. When the only blockers are already-reviewed stale/terminal FAILED envelopes, it is valid to move the local escape watermark with `envelope_bus.py ack-escape <reason>` and then retry the governed claim/consume path.

Do not treat this as clearing the failed envelopes themselves. It only records operator review of the escape watermark.

## Orphaned running claims

A common drain blocker is `running` tasks with `claimed_by=hermes-parallel` and a `run_id`, but no live `agent_team_controller.py consume-claimed` or `hermes ... chat -q` process containing that run id.

Recovery pattern:

1. Compare running task `run_id`s with the live process table.
2. If no active worker exists for a running claim, release it through the orchestrator, not by editing files:
   - `brain_task_orchestrator.py release <task_id> --to-status retry --actor hermes-drain-loop --force --reason 'orphaned running claim: no active worker process for run_id; forced release to retry for governed redispatch, not done' --json`
3. Reconcile/promote due retry, then let dispatch tick redispatch.

Implementation pitfall: do not build the release command by shell-interpolating JSON-escaped task ids. Some task ids contain spaces, Chinese text, and suffixes; shell quoting mistakes lead to `task not found`. Prefer subprocess argument arrays, or exact single-quoted ids in a direct terminal command.

## Artifact-missing child tasks

Temporary workers may move a blocked child to running and then back to blocked when the child’s source artifact is missing. That is a valid result, not a worker failure.

- If the task’s `auto_subtask_parent_artifact` path does not exist, do not synthesize the missing artifact.
- Either leave the child blocked/retry with the missing artifact as blocker, or create a narrow evidence artifact only if enough real source evidence exists elsewhere.
- If you create a narrow brief or proof artifact, move the child only to `review`, not `done`.

## Background drain helper pattern

For a long drain-to-empty request, a bounded background helper can be useful. Requirements:

- It must call only existing governed taskpool commands.
- It must log every step as JSONL under `~/.hermes/logs/`.
- It must have a max-cycle/stall limit.
- It must not kill workers, mark done, edit task notes directly, or bypass proof gates.
- Its final status should be either `empty` or a hard boundary reason.

Report the helper path, process id/session id, log path, and fresh readback counts. Do not claim the taskpool is empty until active count is actually zero and selfcheck passes.
