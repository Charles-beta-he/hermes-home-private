# Dynamic Self-Check Coverage Control Plane

Scope: Hermes Agent self-check / self-architecture operations. Applicability: use when self-check must adapt to Hermes updates, runtime failures, cron/gateway/provider/taskpool/profile drift, or user-specific enabled systems. Anti-conditions: do not use this pattern to authorize external delivery, GitHub writes, push/deploy/publish, credential entry, destructive cleanup, or broad fanout without an exact authority grant, receipt, rollback, and readback.

## Pattern

Treat self-check as a gated MAPE-K control loop:

1. Monitor: discover active systems from local scheduler, profiles, tools/MCP, providers, gateway/delivery paths, repositories, taskpool, storage, and script pool.
2. Analyze: build a Coverage Registry with current checks, missing checks, stale checks, risk, freshness, and evidence refs.
3. Plan: map events/changes to checks using change-impact rules. Examples: doctor changes require doctor CLI/fix/post-update checks; provider adapter changes require provider smoke and route eligibility; prompt changes require prompt/cache/role checks; scheduler/gateway changes require delivery readback; taskpool changes require boundary/evidence/stale-claim checks.
4. Propose: generate workflow proposals with reason, evidence, schedule, script, success/failure behavior, side-effect class, authority needed, rollback, and first-run verification.
5. Execute: auto-promote only read-only/local-only/no-agent/success-silent monitors with deterministic dry-run/readback.
6. Know/ratchet: write local evidence artifacts and retire stale/duplicate coverage.

## Required boundaries

- Dynamic coverage discovery and proposal generation may be automatic.
- Workflow promotion is gated.
- Model reviews are advisory unless quorum and objective evidence gates pass.
- Cron jobs must not recursively create cron jobs.
- Success-silent local monitors are preferred to reduce alert fatigue.
- User-facing delivery failures must be surfaced as local repair packets unless external delivery is separately authorized.

## Minimal artifact set

- `user_system_profile.json`: discovered systems and counts.
- `coverage_registry.json`: covered/missing/stale/risk/evidence refs.
- `coverage_plan_<timestamp>.json`: event-to-check mapping.
- `coverage_proposals.json`: gated workflow proposals.
- `last_run.json`: receipt/readback summary.
- `cron_error_clusters.json`: local clustering of failed cron jobs into actionable groups such as delivery proxy, model/provider/quota, script runtime, storage/cleanup, or other.
- `provider_health_snapshot.json`: local consult-models selfcheck/status snapshot; explicitly not certification unless quorum/evidence gates later pass.
- `repair_packets.json`: local-only repair packets that name next actions and authority required before external send/provider config/credential changes.
- `delivery_proxy_diagnostics.json`: local readback of affected cron output files plus gateway/proxy environment/process scan; never resends by itself.
- `coverage_lifecycle.json`: lifecycle ledger for each coverage gap/check, including first_seen_at, last_seen_at, seen_count, absent_count, active/resolved/retired states, severity-specific review SLA, and resolved-retention runs before pruning.

## Verification

- Run unit tests for discovery, registry, planner, proposal, and artifact writes.
- Run the script once on the live Hermes home and read back artifact paths/summaries.
- If a cron is promoted, verify `cronjob list`, manual `cronjob run`, `last_status=ok`, `deliver=local`, `no_agent=true`, and artifact refresh.
