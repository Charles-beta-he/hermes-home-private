# Root-cause classification for Hermes self-audit

Use this when self-check output is technically correct but operationally misleading: a health score is degraded, cron has error jobs, taskpool has no running work, or humans ask for 根因/长期稳定方案.

## Core lesson

Do not report a flat error list. Classify each finding by blast radius, freshness, and what it actually blocks.

Required fields for each finding:
- `class`: `LIVE_BLOCKER`, `SAFETY_PAUSE`, `EXTERNAL_PROVIDER`, `DELIVERY_FAILURE`, `HISTORICAL_DEBT`, `DUPLICATE_CANDIDATE`, `TELEMETRY_WARNING`, `NOOP_OK`
- `scope`: `cron`, `delivery`, `provider`, `taskpool`, `envelope`, `proof`, `edge_node`, `continuation`, `historical_terminal`
- `freshness`: `live`, `since_ack`, `current_tick`, `historical`
- `blocks_what`: `user_work`, `autorun_preclaim`, `review_close`, `delivery_only`, `nothing`
- `evidence`: exact command/log/job/task id evidence
- `next_action`: human ack, provider fallback, outbox retry, quarantine, dedupe, observe-only, etc.

## Triage pattern

1. Separate scheduler health from job health.
   - A single business cron job error is not automatically a scheduler failure.
   - Split `scheduler_triggered`, `generation_status`, `ingest_status`, and `delivery_status`.

2. Separate provider failure from task semantics.
   - Example: Codex/OpenAI backend 90s no-event timeout is `EXTERNAL_PROVIDER`, not proof that the report logic is wrong.
   - Prefer job-level model/provider pinning, fallback chain, and circuit breaker over retrying the same default model.

3. Separate delivery from content generation.
   - Telegram/Feishu timeout is `DELIVERY_FAILURE` and should go through an outbox/retry path.
   - Do not mark generated content as failed solely because delivery failed.

4. Separate taskpool live blockers from historical governance debt.
   - `proof-check PASS` with terminal debt warnings means historical debt is visible, not necessarily blocking.
   - Only promote historical debt to live blocker when it touches current claimed/running/dispatchable P0/P1 work or newly appears since ack.

5. Treat human-escape as a safety pause, not a generic deadlock.
   - Report whether it blocks only autorun/preclaim or also user work.
   - Include live worker count, claimed/running count, and since-ack failure classes.

6. Explain `next=null` precisely.
   - Use classes such as `no_user_work_dispatchable`, `p2_evolution_only`, `human_escape_active`, `boundary_conflict`, `active_slots_full`, `reconcile_required_with_plan`, `proof_gate_blocking`, `duplicate_candidate`.

## Report shape for this user

Prefer a P0/P1/P2 decision view:

- P0 live blockers: user-visible work blocked, running/claimed wedged, scheduler not firing, proof gate bypass.
- P1 control-plane safety: human_escape active, provider circuit breaker needed, autorun wrapper misclassifies safe pause as error, duplicate dispatch candidates.
- P2 historical debt: terminal mission-envelope debt, proof-hash debt, continuation/archive volume, stale edge-node warnings, historical envelope failures.

If there is no P0/P1 user-work blocker, state that explicitly before discussing debt.

## Durable fixes to propose

- DAG/checkpoint/outbox for high-coupling report cron jobs.
- Job-level provider/model policy with fallback and no-event circuit breaker.
- Delivery outbox with idempotency and retry/backoff.
- Root-cause classes in selfcheck/diagnostics instead of long flat warning lists.
- Historical debt ledger that stays visible but non-blocking by default.

## Anti-patterns

- Treating `cron-job-health FAIL` as proof the scheduler is broken without checking last_run/next_run and job-specific error.
- Reporting historical proof debt as if it blocks current dispatch.
- Saying taskpool is deadlocked when `claimed=0`, `running=0`, and only P2/evolution candidates exist behind a safety pause.
- Retrying the same provider/model after a known no-event timeout instead of using fallback/circuit breaker.
- Letting delivery timeout erase or fail a generated report artifact.
