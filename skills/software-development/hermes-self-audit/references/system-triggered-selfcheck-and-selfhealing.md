# System-triggered self-check and governed self-healing

Scope: Hermes Agent self-governance/control-plane only. Applicability: designing, operating, or debugging Hermes resident self-check/self-healing behavior. Anti-condition: do not apply this heavy operator pattern to ordinary project Q&A, one-off scripts, or non-Hermes app health checks unless the user explicitly asks for a similar control plane.

## Core rule

CLI is a debug/manual surface only. Product behavior comes from runtime triggers:

- user intent: "自检", "没执行", "没发", "卡住", "为什么又坏了";
- lifecycle boundary: conversation turn end, task done gate, cron fire, gateway delivery, provider fallback;
- runtime event: tool failure, provider error, delivery failure, cron miss, budget/max-iteration exhaustion;
- trend: repeated fingerprint, stale claims, memory pressure, FD growth, backlog growth.

## MAPE-K mapping

- Monitor: runtime code emits compact events.
- Analyze: classify severity/freshness/blast radius/fingerprint.
- Plan: emit repair plans with safety level and evidence requirements.
- Execute: separate governed executor only; never from a hot-path checker.
- Knowledge: append-only ledger under `~/.hermes/state/selfcheck/`.

## Safety rules

1. Checks and analyzers are side-effect-free.
2. LLM/multi-model output is proposal/review, not authority.
3. Hot-path operator code never runs shell commands or external sends.
4. Repair plans stay `waiting_for_judgement` until an executor consumes exact digest/TTL/evidence.
5. The first executor boundary is dry-run/readback only: consume an exact plan id/digest, append `repair_attempts.jsonl`, and prove no shell/send/lifecycle mutation occurred.
6. Enterprise authorization boundary: before any governed executor call beyond compatibility dry-run, append `repair_authorizations.jsonl` with exact plan id, request digest, actor, TTL, decision, and secret-free evidence refs; executor must reject digest drift, expired authorization, non-approved decision, and unsupported mode.
8. Sentinel wakeups are allowed to run automatically: they may read ledgers/projections and append `wakeups.jsonl`, `diagnosis_packets.jsonl`, and local-only `pending_alerts.jsonl`; they must not send platform messages.
9. L1 auto-repair is open only for strict allowlisted ledger-local maintenance (`selfcheck.l1.rebuild_projections`, `selfcheck.l1.archive_expired_authorizations`). These actions append `repair_attempts.jsonl`, verify before/after readback, and must record `external_send_executed=false`, `shell_executed=false`, `lifecycle_mutated=false`, and `adapter_mutated=false`. Disable with `HERMES_SELFCHECK_AUTO_REPAIR=0`.
10. L2 notification intent is open for local outbox/delivery dry-run only: `pending_alerts.jsonl` may be converted into `notification_outbox.jsonl`, `delivery_authorizations.jsonl`, and `delivery_dry_runs.jsonl` with `channel=local`, `target_id=selfcheck-local`, `payload_body_stored=false`, `send_executed=false`, and `token_read=false`. Disable with `HERMES_SELFCHECK_NOTIFICATION_OUTBOX=0`.
11. Telegram delivery is opened as the first live platform boundary: Telegram dry-runs use exact `HERMES_SELFCHECK_TELEGRAM_TARGET` (default `telegram:he cheng`), and `run_telegram_delivery_tick()`/`selfcheck_telegram_sender_tick.py` consume only `telegram_delivery_dry_run_verified` records. Receipts go to `delivery_receipts.jsonl` with `token_value_persisted=false` and `payload_body_persisted=false`. Disable live sender with `HERMES_SELFCHECK_TELEGRAM_LIVE_SEND=0`.
12. Repeated fingerprints debounce/coalesce to prevent self-check storms.
13. Task lifecycle advancement requires canonical lifecycle gates, never a self-healer finding alone.

## Resident operator shape

The operator should be import-safe and callable from existing runtime seams:

- conversation finalizer;
- tool executor failure branch;
- cron scheduler job/delivery result;
- gateway send failure branch;
- provider/router failure branch;
- taskpool transition/worker hooks.

Ledger outputs:

- `events.jsonl`
- `findings.jsonl`
- `repair_plans.jsonl`
- `repair_authorizations.jsonl`
- `repair_attempts.jsonl`
- `archived_authorizations.jsonl`
- `wakeups.jsonl`
- `diagnosis_packets.jsonl`
- `pending_alerts.jsonl`
- `notification_outbox.jsonl`
- `delivery_authorizations.jsonl`
- `delivery_dry_runs.jsonl`
- `delivery_receipts.jsonl`
- `coalesced.jsonl`

Derived projections:

- `health_summary.json`
- `latest_findings.json`
- `component_status.json`
- `sentinel_status.json`

## Reporting semantics

Say "waiting for judgement" when a plan exists but no governed executor/human authorization has consumed it. Say "healed" only after before/after/readback verification is recorded.
