# Cron startup audit and compensation filtering

Use when a scheduled report/reminder appears to have generated locally but the cron job record or Telegram delivery evidence did not complete, especially after gateway restart, manual `cron run`, network turbulence, or long-running cron execution.

## Core invariant

Do not remove the existing at-most-once safety behavior. `advance_next_run()` moving `next_run_at` before execution is intentional: it prevents crash loops and backlog burst-fires. The missing piece is observability and bounded compensation, not reverting to blind at-least-once execution.

## Failure shape to detect

Split state can happen when execution progresses through only part of:

1. `tick()` finds a due job.
2. `advance_next_run(job_id)` provisionally moves `next_run_at` forward.
3. Worker runs `run_job()`.
4. Job writes its own artifact, e.g. `~/.hermes/notes/reports/aihot-daily-YYYY-MM-DD.md`.
5. Scheduler `save_job_output()` writes `~/.hermes/cron/output/<job_id>/<timestamp>.md`.
6. `_deliver_result()` sends to Telegram/local/origin.
7. `mark_job_run()` updates `last_run_at`, `last_status`, `last_delivery_error`, and re-anchors `next_run_at`.

If the process stops between 2 and 7, `next_run_at` may be in the future while `last_run_at` is stale. A report may exist locally without a cron completion record or Telegram delivery receipt.

## Startup audit: read-only first

On gateway/scheduler startup, run an audit before any automatic compensation. Read:

- `~/.hermes/cron/jobs.json`: `id`, `name`, `schedule`, `enabled`, `state`, `next_run_at`, `last_run_at`, `last_status`, `last_error`, `last_delivery_error`, `deliver`, `no_agent`, `script`, `repeat`.
- Ticker heartbeat files: `ticker_heartbeat` and `ticker_success`; heartbeat fresh but success stale means the loop is alive but tick may be failing.
- `~/.hermes/cron/output/<job_id>/` for scheduler-owned output files.
- Job-specific artifacts, for example daily reports under `~/.hermes/notes/reports/aihot-daily-YYYY-MM-DD.md` and `.tasks.json`.
- Recent `gateway.log` / `gateway.error.log` lines for `completed successfully`, `delivered to telegram`, `delivery error`, `missed its scheduled time`.
- `~/.hermes/state/gateway_delivery_outbox.jsonl` for `pending`, `sent`, `dead_letter`, and `sent_message_id`.

Classify every relevant scheduled slot into one of:

- `OK_COMPLETED`: `last_run_at >= scheduled_slot`, status recorded, and delivery evidence exists when delivery is expected.
- `OK_SILENT`: no-agent/silent/local case where no external delivery is expected.
- `RUNNING_IN_FLIGHT`: fresh running ledger/claim/heartbeat; do not compensate.
- `STALE_IN_FLIGHT`: running marker older than TTL; inspect artifacts before deciding.
- `UNTRIGGERED_WITHIN_WINDOW`: expected slot passed, no ledger/output/artifact, still inside compensation window.
- `MISSED_TOO_OLD`: expected slot passed beyond compensation window; record missed/manual intervention, do not auto-run backlog.
- `GENERATED_UNMARKED`: artifact or scheduler output exists but `last_run_at` is stale.
- `DELIVERED_UNMARKED`: Telegram/outbox send evidence exists but cron mark did not complete; mark/ledger only, never resend.
- `DELIVERY_FAILED`: output exists and delivery failed; eligible only for bounded resend if not ambiguous.
- `DELIVERY_UNKNOWN`: output/artifact exists but no delivery success/failure evidence; default manual unless explicitly allowlisted.

## Compensation filter

Default mode is audit-only. Automatic compensation requires all of:

- job ID is explicitly allowlisted;
- target scheduled slot is the latest relevant slot, not a backlog range;
- within configured max age/window;
- no fresh running/in-flight marker;
- idempotency key is not already completed;
- compensation attempts are below limit;
- delivery target is exact and appropriate;
- Telegram duplicate checks pass (`gateway_delivery_outbox` sent/message_id and recent delivered logs absent).

Recommended idempotency key forms:

- Daily report: `cron:<job_id>:<logical_date>`.
- Generic scheduled slot: `cron:<job_id>:<scheduled_slot_iso>`.

Decision table:

| State | Default action | Auto action if allowlisted |
|---|---|---|
| `OK_COMPLETED`, `OK_SILENT`, `RUNNING_IN_FLIGHT` | skip | skip |
| `UNTRIGGERED_WITHIN_WINDOW` | audit | requeue once (`next_run_at=now`) |
| `MISSED_TOO_OLD` | missed/manual | skip, do not backlog-run |
| `STALE_IN_FLIGHT` with artifact | audit | artifact-based delivery/mark path |
| `STALE_IN_FLIGHT` without artifact | manual | requeue once only within window |
| `GENERATED_UNMARKED` | audit | mark-only for local; otherwise inspect delivery |
| `DELIVERED_UNMARKED` | mark-only | mark-only, no resend |
| `DELIVERY_FAILED` | manual | resend existing output once if not ambiguous |
| `DELIVERY_UNKNOWN` | manual | for explicitly safe report jobs, resend existing artifact once; do not regenerate |

Telegram caution: read/write timeouts are ambiguous because Telegram may have received the message. Treat them as manual or require outbox/message-id evidence before retrying.

## Minimal run ledger

Add or use a JSONL run ledger such as `~/.hermes/state/cron_run_ledger.jsonl`:

```json
{
  "schema": "cron_run_ledger_v1",
  "fire_id": "uuid",
  "job_id": "c01e3574e31c",
  "job_name": "aihot-daily-report",
  "scheduled_slot": "2026-06-30T09:00:00+08:00",
  "logical_date": "2026-06-30",
  "idempotency_key": "cron:c01e3574e31c:2026-06-30",
  "status": "fired|queued|running|generated|output_saved|delivering|sent|failed|dead_letter|compensated|skipped",
  "attempt": 1,
  "compensation_attempt": 0,
  "started_at": "...",
  "updated_at": "...",
  "completed_at": null,
  "output_file": null,
  "artifact_refs": [],
  "deliver": "telegram:he cheng (dm)",
  "delivery_expected": true,
  "delivery_status": "none|sent|failed|unknown|not_required",
  "delivery_message_id": null,
  "delivery_error": null,
  "source": "scheduler|startup_audit|manual_compensation"
}
```

The ledger should be append-only/transition-based and compactable. Treat `jobs.json` as schedule configuration; treat the ledger/outbox as run/delivery facts.

## Daily report specialization

For `aihot-daily-report` and similar report jobs, prefer logical-date idempotency and artifact reuse:

1. Check `cron/output/<job_id>/YYYY-MM-DD*.md`.
2. Check `notes/reports/aihot-daily-YYYY-MM-DD.md` and `.tasks.json`.
3. Check `jobs.json last_run_at` against the scheduled slot.
4. Check gateway delivered logs and delivery outbox `sent_message_id`.

If report artifacts exist but `last_run_at` and delivery evidence are missing, classify as `GENERATED_UNMARKED + DELIVERY_UNKNOWN`. Do not rerun model generation. Either request manual approval or, if allowlisted, resend the existing artifact/summary once and record the message ID in the ledger.

## Implementation slices

- P0: `hermes cron audit-startup --json` / startup read-only audit; write `~/.hermes/state/cron_startup_audit.json`; no mutation.
- P1: run ledger events around fire, worker start, output saved, delivery, and mark completion.
- P2: manual `hermes cron compensate --job <id> --slot <slot> --dry-run|--execute` with allowlist/time-window/idempotency/max-attempt checks.
- P3: optional dashboard/health projection for `generated_unmarked`, `delivery_failed`, `stale_in_flight`, and `missed_too_old`.

## Verification checklist

- Simulate crash after `advance_next_run` but before `mark_job_run`; audit must detect stale `last_run_at` + future `next_run_at`.
- Simulate report artifact exists without scheduler output; classify `GENERATED_UNMARKED`, not `OK_COMPLETED`.
- Simulate outbox `sent_message_id`; compensation must suppress resend.
- Simulate no-agent empty output; classify `OK_SILENT`.
- Simulate deliver=local; do not require Telegram delivery.
- Run dry-run compensation twice; second execution must be `suppressed_duplicate` if the first wrote sent/compensated ledger evidence.
