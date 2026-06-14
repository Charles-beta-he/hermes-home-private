# Selfcheck Alert Noise Governance

Use when Hermes selfcheck/sentinel alerts spam Telegram or repeatedly report `repeated finding(s) coalesced inside debounce window` / `repair plan(s) waiting for judgement`.

## Signal

Typical symptoms:

- Telegram receives many messages like `Hermes selfcheck alert: N repeated finding(s) coalesced inside debounce window`.
- `state/selfcheck/health_summary.json` shows `overall_status: yellow` and nonzero `waiting_for_judgement`.
- `state/selfcheck/sentinel_status.json` shows large `pending_local_alerts`, `notification_outbox_tail`, or `local_delivery_dry_runs_tail`.
- The Telegram sender cron reports many `sent_verified` receipts in one run.

## First principles

Selfcheck is a control-plane ledger, not a chat notification firehose. Do **not** solve this by disabling selfcheck globally or deleting evidence ledgers.

Preserve these boundaries:

- Keep findings, wakeups, diagnosis packets, dry-runs, and receipts append-only where possible.
- Live Telegram sends are external side effects and should be default-off unless explicitly enabled.
- L0 `diagnose.*` repair plans can be closed with governed dry-run/readback evidence; they should not keep generating `waiting_for_judgement` noise forever.
- Failed platform sends should be terminal for the automatic sender; replay requires a fresh governed action.

## Diagnostic sequence

1. Inspect projections first:
   - `~/.hermes/state/selfcheck/health_summary.json`
   - `~/.hermes/state/selfcheck/sentinel_status.json`
   - `~/.hermes/state/selfcheck/component_status.json`
   - `~/.hermes/state/selfcheck/latest_findings.json`
2. Tail ledgers:
   - `wakeups.jsonl`
   - `coalesced.jsonl`
   - `repair_plans.jsonl`
   - `repair_attempts.jsonl`
   - `pending_alerts.jsonl`
   - `notification_outbox.jsonl`
   - `delivery_dry_runs.jsonl`
   - `delivery_receipts.jsonl`
3. Check cron jobs for the sentinel and sender scripts:
   - `selfcheck_sentinel_tick.py`
   - `selfcheck_telegram_sender_tick.py`
4. Verify whether live send is enabled by environment/config. Default-safe behavior should be no live Telegram send unless `HERMES_SELFCHECK_TELEGRAM_LIVE_SEND=1` is explicitly set.

## Durable repair pattern

If editing Hermes selfcheck code, prefer these guardrails:

- Telegram live sender default-off:
  - `HERMES_SELFCHECK_TELEGRAM_LIVE_SEND=0` by default.
  - Require explicit truthy opt-in (`1`, `true`, `on`, `yes`, `enabled`) for platform send.
- Batch-limit live delivery:
  - Add/use `HERMES_SELFCHECK_TELEGRAM_BATCH_LIMIT` with a small default (for example 5) and hard cap (for example 20).
- Do not retry failed receipts forever:
  - Treat both `sent_verified` and `send_failed` receipts as terminal for automatic sender dedupe.
- Avoid self-referential repeated-finding loops:
  - Count only real `debounced_recent_fingerprint` records with a `finding_id`.
  - Do not count `debounced_recent_wakeup`; that is sentinel bookkeeping, not a user/runtime finding.
- For L0 `diagnose.*` repair plans:
  - Run governed `run_repair_plan_dry_run(plan_id, request_digest=...)` or equivalent readback-only path.
  - Rebuild projections afterward.
  - Verify `waiting_for_judgement` drops without external side effects.

## Verification

Minimum evidence before reporting completion:

- Focused tests for selfcheck operator pass.
- `py_compile` passes for changed selfcheck/sender scripts.
- Direct sender script run exits 0 and emits no output when live send is default-off.
- Direct sentinel script run exits 0.
- `health_summary.json` shows `waiting_for_judgement: 0` if L0 plans were dry-run closed.
- Taskpool selfcheck still passes or any warnings are classified separately.
- Scoped commit only includes selfcheck/sentinel/sender changes and the parent gitlink if a submodule was updated.

## Pitfalls

- Do not delete selfcheck JSONL ledgers just to make projections green.
- Do not silence all P1/P0 wakeups; reduce live delivery noise while preserving local evidence.
- Do not let a local dry-run outbox imply external send authorization.
- Do not bundle unrelated brain/skill/profile overlay changes into the selfcheck repair commit.
