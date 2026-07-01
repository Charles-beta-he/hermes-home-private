# Mainloop background certification queue and worker

Applicability: Hermes self-modification or governance work where the main conversation loop must block/downgrade completion claims and then automatically pursue independent certification later. Use after a bounded final-response gate consumer already exists.

## Pattern

1. Keep the synchronous gate small and deterministic.
   - Detect completion/T3 claims.
   - Extract objective evidence from current tool/readback messages.
   - Run the acceptance gate with `require_objective_evidence`, `require_evidence_refs_for_votes`, `require_independent_verifier_vote`, and `forbid_self_certification`.
   - If not certified, downgrade or block the completion claim in the visible final response.

2. Persist unresolved certification requests to a durable queue.
   - Use deterministic job ids from a digest of the request so retries are idempotent.
   - Store enough request data to recreate the certification packet: user message, final response under review, implementer model, gate decision, claims, evidence, route, and acceptance result.
   - Explicitly stamp safety fields such as `allowed_to_mark_done=false` and `external_side_effects_enabled=false`; background certification is evidence gathering, not task lifecycle authority.

3. Add a worker CLI and a silent wrapper.
   - CLI commands should list jobs and run queued jobs.
   - The real runner should build a structured `consult_models.py state` packet, pass each evidence item separately with explicit `supports`, and run consult models with a recursion guard environment variable.
   - The shell wrapper should emit nothing when no queued jobs are processed; only emit JSON when work actually happened or failed.

4. Schedule the worker separately.
   - Use a no-agent cron/script job for deterministic polling.
   - The cron job should be silent on empty queues and should not recursively create more cron jobs.

5. Verify with both negative and positive gates.
   - No evidence / no independent verifier vote => `not_certified` or equivalent degraded status.
   - Objective evidence + independent verifier vote => `certified`.
   - Worker no-op smoke: wrapper stdout byte count should be zero when queue is empty.
   - Cron readback should show enabled schedule, script path, and no-agent mode.

## Pitfalls

- Internal projection jobs can look like completion claims. For Hermes ContextCard or similar internal JSON projection prompts, add an explicit skip rule (for example `skipped_internal_projection`) so generated summaries do not trigger certification loops.
- Do not let the background worker mark tasks done, alter lifecycle state, or perform external side effects. It may attach evidence and certification results only.
- Do not pass a nested `{claims, evidence}` bundle as one evidence object to `consult_models.py state`; pass each evidence item separately with `supports` links or truth coverage can drop to zero.
- Treat `fanout_quorum_met` as planner availability only. Final closure still needs truth grounding and, when required, independent verifier approval.

## Minimal evidence set

- focused tests for queue idempotency, authority-smuggling rejection, worker status writeback, main-loop enqueue, low-risk skip, and internal-projection skip;
- syntax/compile check for modified runtime and scripts;
- worker silent smoke on empty queue;
- post-update or project health check;
- cron/list readback for scheduled worker;
- independent verifier result citing evidence ids and no severity>=3 blockers.
