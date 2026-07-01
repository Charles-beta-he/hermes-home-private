# Kanban blocked-card structured unblock audit

Use after Kanban mirror/provenance repair when `kanban-sync-coverage` remains low because `blockage_coverage` is the bottleneck, or when the user asks to review remaining blocked cards before unblocking/closing them.

Goal: classify blocked cards by the next safe action without mutating task state. A blocked audit is not authority to auto-complete cards.

Read-only evidence to collect:

1. Coverage snapshot:
   - `python3 ~/.hermes/scripts/kanban_coverage.py --json`
   - Record score, bottleneck, `agent_coverage_v2.metrics`, `stale_projection_tasks`, `projection_drift_tasks`, and caps.
2. Blocked task rows from `~/.hermes/kanban.db`:
   - id, title, assignee, status, `block_kind`, `block_recurrences`, workspace path, session/run ids, body/result excerpts, last spawn/failure errors.
3. Recent events and comments:
   - latest `blocked` event and reason payload.
   - latest task comment/handoff.
   - recent `spawned`, `claimed`, `crashed`, `gave_up`, `heartbeat`, `commented` events.
4. Run/workspace evidence:
   - latest `task_runs` rows.
   - workspace exists / proof-like files (`proof`, `evidence`, `report`, `summary`, `ledger`, `test`, `result`).

Structured-unblock fields to check per card:

- `block_kind` is typed, preferably `needs_input`, `dependency`, `capability`, or `transient`.
- blocked reason exists and states the exact gate.
- review marker exists when appropriate: `review-required`, `human review`, `needs human review`, `needs eyes`, or `blocked for review`.
- workspace path exists and can be inspected.
- latest comment/handoff exists for review-required cards.
- run history exists.
- source status is known when the card is a `brain-mirror` projection.
- proof pointer exists: artifact path, test result, commit, proof log, or explicit non-applicability evidence.

Recommended categories:

1. `human_review_ready`
   - Has review-required reason, handoff/comment, run history, workspace/proof pointer, and no source/projection contradiction.
   - Next action: ask/perform human review. If accepted, close with normal Kanban complete/transition command and a result summary. Do not auto-complete from the audit alone.
2. `certification_or_multimodel_gate`
   - Mentions `degraded_not_certified`, ratification, quorum, provider-diversity tradeoff, or verifier gate.
   - Next action: keep blocked until ratification refresh/provider health recovers, or until explicit reviewer approval accepts the tradeoff.
3. `projection_drift_or_incomplete_source`
   - Kanban is blocked/review-required but source status is still `running`, `proposed`, or otherwise not terminal/aligned.
   - Next action: reconcile the source task/note first; do not unblock only the Kanban projection.
4. `worker_crash_unstructured`
   - Has `pid ... not alive`, `crashed`, or `gave_up` without a review-required handoff.
   - Next action: rerun or triage failure; add typed block reason and proof/failure pointer before unblock.
5. `unstructured_or_legacy_block`
   - Missing block reason, block kind, comment, source status, or proof pointer.
   - Next action: create a typed block/handoff packet or decide archival/retry based on evidence.

Audit output contract:

- Count blocked cards and category counts.
- For each card include: id, title, assignee, block_kind, source_status, workspace, latest block reason, structured fields present, missing fields, proof candidates, last failure, and recommendation.
- End with a prioritized queue: unstructured/crash first, source/projection mismatch second, certification gates third, human-review-ready batch last.
- Run a final read-only check that blocked count/coverage are unchanged unless the user explicitly authorized lifecycle writes.

Pitfalls:

- Do not close cards merely because proof text says tests pass; `review-required` is a gate.
- Do not unblock `brain-mirror` cards whose source status is still `running` or `proposed`; source-of-truth must move first.
- Do not treat `blockage_coverage` failure as a reason to force-close blocked backlog. Low blockage coverage means missing unblock structure, not proof of completion.
- Do not rely on `hermes kanban list --json | python ...` pipelines that can break stdout and cause `BrokenPipeError`; write JSON to a temp file or query SQLite directly for audits.
