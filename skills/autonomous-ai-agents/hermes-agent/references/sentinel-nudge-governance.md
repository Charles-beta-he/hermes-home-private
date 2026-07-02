# Sentinel Nudge Governance

Scope: proactive nudges, scheduled agents, reminders, Mission event ticks, cron jobs, gateway notifications, and any assistant-initiated follow-up. Applicability: use when a reference project or product pattern suggests “sentinel”, “scheduled nudges”, “proactive memory”, “always-on worker”, “autonomous reminder”, or “digital worker” behavior. Anti-condition: pure local read-only health checks that write no user-visible output can use lighter local watchdog rules.

## Source pattern

Derived from Raven/EverOS absorption:

- SSOT: `/Users/charles/wechat_video_analysis/project_absorption/raven-everos-absorption-ssot/`
- Graph node: `sentinel_nudge_governance`
- Experience atom: `raven-everos-absorption-57aedd509df9`

Raven advertises sentinel / proactive memory / scheduled nudges. Hermes should absorb the governance pattern, not the runtime defaults.

## Default policy

Proactive scheduled behavior defaults to local receipt-only operation:

- local state/readback is allowed when the task is already authorized;
- success should stay silent unless the user asked for a report;
- external delivery requires exact platform, target, payload class, receipt, and post-send readback;
- broad fan-out, publish/deploy, destructive operations, credential/payment entry, and physical/device actions remain separately gated.

## Nudge packet

Any proactive nudge or scheduled worker that may surface to a human must have:

```yaml
id: string
source_event: string
user_goal: string
trigger:
  kind: schedule | event | manual | watchdog
  cadence_or_event: string
scope:
  allowed_inputs: []
  allowed_outputs: []
  forbidden_outputs: []
budget:
  max_runtime: string
  max_tool_calls: int
  max_external_reads: int
delivery:
  mode: local_only | exact_target_required
  platform: string | null
  target: string | null
  payload_class: string
receipts:
  ledger_path: string
  success_silent: true | false
  failure_alert: true | false
rollback:
  pause_command: string
  remove_command: string
readback:
  required_commands: []
```

## Execution ladder

1. **Local dry-run** — collect state and write a local receipt; no user-visible delivery.
2. **Local report** — create local markdown/JSON output; no external delivery.
3. **Single exact-channel delivery** — only after platform/target/payload/readback are named.
4. **Recurring exact-channel delivery** — only after duplicate suppression, failure policy, pause/remove commands, and receipt ledger exist.
5. **Broad fan-out or external side effect** — requires explicit allowlist and separate high-risk boundary.

## Hard stops

Stop before execution, but continue local packet preparation, when any of these are missing:

- exact delivery target;
- payload class;
- credential/secret boundary;
- rollback/pause command;
- receipt/readback location;
- duplicate suppression for recurring reports;
- authority for external write, publish/deploy, destructive action, payment, credential entry, or broad fan-out.

## Local dry-run harness

Use `scripts/sentinel_nudge_dry_run.py <packet.json>` to validate a nudge packet and append a local receipt without sending anything. A generic sample lives at `templates/sentinel-nudge.local-only.sample.json`; regression tests live at `scripts/test_sentinel_nudge_dry_run.py`.

## Verification

- For cron jobs, list/read job configuration after creation or update.
- For no-agent local watchdogs, verify success-silent and failure-alert semantics.
- For external delivery, read back the send receipt and target state if the platform supports it.
- For Mission/taskpool nudges, read the ledger/board/doctor projection after the tick.
