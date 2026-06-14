# Blocked / retry recovery after control-plane repair

Scope: Hermes local taskpool operation after a scheduler, reconcile, blocked-resolver, retry, or envelope-escape control-plane fix has already been made and verified.

Applicability: use when the pool contains a mixture of `blocked`, `retry`, and `review` tasks and the operator asks to advance them without bypassing lifecycle/proof/multimodel gates.

Anti-conditions: do not use this to mark tasks `done`, bypass multimodel certification, delete/archive evidence, or promote retry tasks when the original infrastructure/control-plane blocker is still unresolved.

## Pattern

1. Establish a broad status baseline.
   - Use the canonical task list JSON and locally group by status.
   - Include `blocked`, `retry`, `review`, `pending`, `claimed`, and `running`; do not trust a single `next` result.
   - Record `dispatchable`, `retry_count`, `next_attempt_at`, `multimodel_status`, `multimodel_last_gate_status`, and `multimodel_last_decision`.

2. Run blocked resolver before forcing retry promotion.
   - Run the blocked resolver across enough tasks for the active set.
   - Expected safe outcomes:
     - `resolved_to_retry` for transient / unknown multimodel state;
     - `resolved_to_review` when existing evidence is enough to re-enter review;
     - `await_auto_subtasks` when a parent is waiting on child evidence;
     - `keep_blocked_missing_taxonomy_artifact` when historical discussion artifacts are gone;
     - `keep_blocked` when certification remains FAIL / CONTINUE_LOOP.
   - Error count must be 0 before treating the resolver as healthy.

3. Run review closeout and gap creation.
   - Run auto-close-review first, to close anything already valid and expose skipped gate failures.
   - Run review-gap-scan with write only when review items are repairable.
   - Be aware that review-gap write can create repair child tasks and event hooks may immediately start bounded autorun or multimodel jobs. Re-list after it runs.

4. Promote retry tasks only after the control-plane blocker is fixed.
   - If retry delay is only from a now-fixed infrastructure/control-plane issue, force-transition to `pending` with a reason and structured evidence naming the fix.
   - Some tasks may already be promoted by reconcile between list and transition; a no-op pending-to-pending transition means refresh state, not failure.
   - Never promote a task just to make it run if the underlying blocker is still real certification/evidence failure.

5. Dispatch carefully.
   - Prefer a bounded parallel dispatch tick or parallel claim-and-handoff followed by controller consume in background.
   - If consume returns human escape, it should release claimed tasks back to retry; do not treat that as dispatch success.

6. Human escape triage before ack.
   - Inspect agent-team controller status and `envelope_stats.escape_info.since_ack`.
   - Query post-ack `FAILED` / `BLOCKED` envelopes in the envelope bus DB using `coalesce(completed_at, updated_at) > acked_at`.
   - Classify errors. If they are understood, and affected tasks were requeued / converted to proof-gated repair tasks, acknowledge escape with an explicit reason.
   - After ack, verify `human_escape_triggered=false` and since-ack failures/blocks are zero.

7. Interpret a clean idle state correctly.
   - If `next=null`, parallel dry-run selects zero tasks, and the dynamic runner reports no additional boundary-safe slots, check live multimodel/worker jobs.
   - If live jobs exist and active slots are occupied, this is healthy backpressure, not a stall.
   - If no live jobs and all remaining rows are `blocked`, `review`, or future-window `retry`, report the remaining real gates instead of forcing lifecycle transitions.

## Pitfalls

- `auto_subtask_progress_synced` for a blocked parent with open children is observational; it should not be treated as a hard `reconcile_required` dispatch blocker.
- Missing historical discussion artifacts must remain diagnostic warnings for resolver taxonomy. Do not let missing artifacts crash unrelated dispatch, and do not invent replacement artifacts.
- Review-gap write is not inert: event hooks can start child multimodel jobs. Re-check live jobs afterward.
- Direct claim without checking envelope escape can create claim/release churn: claimed tasks are immediately returned to retry by consume.
- `PASS_ADVISORY_ONLY` is not enough to close implementation/evolution work. Create repair evidence tasks or keep review blocked by normal gates.

## Verification bundle

After repair/advance, verify:

- canonical list status distribution;
- next task / dispatch dry-run;
- parallel dry-run selection count;
- live multimodel jobs;
- agent-team controller escape state;
- selfcheck and proof-check.

Acceptable end states:
- `running > 0` with matching live jobs;
- no dispatchable work because all active slots are occupied;
- only real blocked/review/future retry gates remain, with selfcheck/proof PASS.
