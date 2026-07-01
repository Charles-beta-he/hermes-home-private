# Daily-report intake and dream-idle historical replay

Applicability: use when debugging Hermes/local-brain daily report ingestion, external-source taskpool candidates, or autonomous-evolution/dreaming runs that appear healthy but repeatedly produce no state advancement. Anti-conditions: do not store a specific day's task progress as a durable rule; use this only as a replay/verification pattern and resolve current file paths from the active profile.

## Daily report external-signal intake replay

When a daily report contains GitHub Trending, Product Hunt, AIHOT, or similar external signals but no tasks appear:

1. Separate the two stages:
   - report/body -> `*.tasks.json` sidecar candidates;
   - sidecar -> `daily_report_task_ingest.py` -> taskpool.
2. First run the original sidecar through ingest in dry-run mode. If `proposal_count=0`, the failure is candidate generation, not taskpool ingestion.
3. Build a replay sidecar from the report body using the same governed candidate schema. Include both high-confidence P2 items and lower-confidence P3/watch items when the user expects broad absorption; do not limit candidates to architecture-only findings.
4. Run ingest dry-run and assert: candidate count, all actions `dry_run`, `invalid_count=0`, and multimodel eligibility normalization is visible.
5. Run a write replay only against an isolated temporary brain vault with a separate state path and manual-request path. Never use the real taskpool for replay unless the user explicitly asks for production ingestion.
6. Run the same isolated write twice. The first pass should create the expected tasks; the second should create zero and skip via `already_emitted_for_report`/dedupe state.
7. If `brain_task_orchestrator.py add` rejects a candidate, check CLI enums before changing business logic. In this setup, `architecture_target` is constrained; map broad product/source labels like `hermes-agent` or `browser-automation` to an allowed value such as `taskpool`, `local-brain`, `provider-quota`, `skill-graph`, `L*`, or empty.
8. Record artifacts: original sidecar baseline, replay sidecar, dry-run JSON, isolated write JSON, and the temp vault path. State explicitly whether the break is candidate generation or ingest/taskpool.

## Product Hunt / GitHub absorption gating

- Product Hunt and GitHub Trending items can be legitimate taskpool candidates even when they are not architecture-layer changes. Product/workflow/business/open-source capability candidates are valid if they have evidence and a clear mapping to Hermes, the user's workflow, or a watch/P3 decision.
- Product Hunt candidates should request competitor/customer/feature/monetization/risk analysis, and should preserve open-source/link-resolution state (for example unresolved GitHub evidence) rather than flattening it to `unknown`.
- Only suppress ordinary news with no transfer path, no evidence, or no user/Hermes mapping.

## Dream/autonomous-evolution idle replay

When a nightly dream/autonomous-evolution job looks green but repeatedly audits the same target with `state_advanced=false`:

1. Collect three evidence layers:
   - cron output files for the job id;
   - dream ledger (`state/dreaming/canonical_state.jsonl`);
   - autonomous-evolution/event logs.
2. Classify records by target, score change, `= 无变化`, `state_advanced`, reason, and proof hash. Report both the earliest historical log evidence and the stricter ledger-backed interval.
3. Build a temporary Hermes home / temporary confidence DB with the repeated target plus at least one plausible alternative target. Do not mutate the real DB.
4. Replay representative real no-change records through the fixed selector state path. A useful regression is:
   - initial selector is the repeated target;
   - after one no-change, selector rotates away;
   - after the configured threshold, `consecutive_no_change` reaches the threshold, `audit_cooldown_until` is set, and `audit_blocked_reason=repeated_no_state_change`;
   - final selector is not the repeated target.
5. Preserve a JSON artifact with input window counts, first/last evidence records, replay steps, final selector state, and `passed=true/false`.
6. Re-run the focused evolution store / nightly tests after replay and attach the command output to the task proof log.

## Pitfalls

- Do not call a run healthy just because cron returned OK. For evolution loops, distinguish runtime health from effective state advancement.
- Do not use copy/pasted selectors or duplicated routing logic in tests. Import the real script/module functions and redirect only paths/state to a temp fixture.
- Do not write historical replay outputs into the real taskpool or real confidence DB unless the user explicitly asks for production ingestion/migration.
- Do not encode a one-day report or one skill name as a permanent rule; encode the replay method and gate shape.
