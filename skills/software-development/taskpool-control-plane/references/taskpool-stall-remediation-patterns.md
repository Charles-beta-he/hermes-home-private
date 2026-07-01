# Taskpool stall remediation patterns

Applicability: Hermes-style local taskpool/control-plane systems with governed lifecycle states, envelope timeout checks, dynamic dispatch runners, model-health gates, and worker claim handoff. Use as a class-level troubleshooting reference, not as proof of any specific project state.

Anti-conditions: Do not apply these steps to production/external task systems without their own lifecycle release command and operator authorization. Do not treat the specific command names as universal outside Hermes local taskpool. Do not mark tasks done, delete tasks, or lower proof gates from this pattern.

## Classify the stall before mutating state

Separate these failure classes; they need different fixes:

1. **human_escape preclaim breaker**
   - Symptom: dynamic runner reports `human_escape_active_preclaim`, `human_escape_triggered=true`, or post-ack FAILED/BLOCKED counts.
   - Check envelope stats and post-ack terminal rows before claiming more work.
   - Keep terminal rows for audit; only move the escape acknowledgement watermark after operator review.

2. **write-guard / autonomy precondition fail-closed**
   - Symptom: dynamic runner can see dispatchable work but an autonomy/write guard blocks claim/handoff.
   - Verify local health, autonomy precondition, and self-test output.
   - If a deterministic selfcheck depends on live model/provider health, split config-invariant checks from runtime health filtering.

3. **active-accounting saturation**
   - Symptom: dispatch dry-run shows `dispatchable=false`, `selected_count=0`, and nonzero claimed/running accounting; a higher-level kanban view may still show no running tasks.
   - List canonical task records and inspect `claimed/running`, `run_id`, `claimed_by`, `claim_expires_at`, and `parallel_boundary`.
   - Compare active claims against live worker processes by `run_id` or task id.
   - Release only orphaned claims through governed lifecycle commands; do not edit task files or mark done.

## UTC timestamp pitfall for envelope timeouts

Envelope timestamps ending in `Z` are UTC. Timeout code must parse them as UTC, e.g. Python `calendar.timegm(time.strptime(value, ISO_FORMAT))`, not `time.mktime(...)` which interprets the struct as local time. On non-UTC hosts this can turn a fresh short run into an apparent multi-hour timeout and trip human_escape.

Regression checklist:

- Insert or patch a RUNNING envelope with `started_at` as an ISO `Z` timestamp.
- Mock/compute `now` about 1–2 minutes later in UTC.
- Assert timeout detection returns no timeout when `appetite_seconds` is much larger.

## Active-claim guard pattern

A reusable guard should:

- Read canonical task JSON.
- Select tasks with status `claimed`/`running` or non-empty `run_id`/`claimed_by`.
- Inspect local process table for matching `run_id` or task id.
- Classify rows as `live_or_unknown` vs `orphan_active_claim`.
- Default to report-only.
- With explicit operator authorization, release only `orphan_active_claim` rows using the system's governed lifecycle release command back to a dispatchable state.
- Never delete tasks, mark done, weaken proof gates, or rewrite lifecycle history.

Verification after release:

- Guard reports `orphan_count=0`.
- Dispatch dry-run shows no stale claimed/running saturation, or only live workers.
- If dynamic runner starts workers, a later dry-run may correctly show no slots because live workers occupy capacity; confirm with process readback before calling it stuck.

## Deterministic selfcheck vs live health

A deterministic selfcheck for configuration invariants must not be polluted by transient provider/model health. Pattern:

- Keep runtime dispatch health filtering enabled for real fanout/worker calls.
- Add an explicit switch such as `filter_health=False` for deterministic selfchecks and unit tests.
- Runtime entrypoints must pass `filter_health=True` intentionally.
- Tests should cover both: resident planners/config invariants survive skip flags, and runtime dispatch still honors health filters.

## Closeout evidence to collect

Before declaring taskpool unstuck, cite fresh evidence for:

- self-test all pass or scoped tests relevant to the fix;
- local health grade/status and warnings;
- human_escape false and post-ack counts zero;
- active-claim guard orphan count zero;
- dispatch dry-run status and active accounting;
- process readback when live workers are expected.
