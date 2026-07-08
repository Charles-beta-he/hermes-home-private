# Remaining-Scope Authority and Cooperation Matrix

Timestamp: 2026-07-08T05:25:00Z

User direction: authorization granted, and future reports must say what user cooperation is required for any remaining unclaimed scope.

## How this authorization is consumed

The broad authorization is recorded as permission to continue safe local/reversible slices without stopping at roadmap wording. It is not treated as unlimited authority for high-side-effect surfaces. For each high-side-effect surface, execution still requires exact target, rollback/escape hatch, and readback evidence before action.

Agent OS route preflight classified the current continuation intent as `critical` and reported `S5 requires AuthorityGrant before execution`; route result was shadow-only and executed nothing.

## Matrix

| Scope not yet claimed | Category | What is already authorized | What I still need from the user before claiming/executing | Next safe action without more user input |
| --- | --- | --- | --- | --- |
| uIMax/A+ UI certified | Evidence/acceptance gap | Permission to keep auditing and fixing local UI | Only if A+ is required: acceptance threshold/taste target; otherwise no user input needed | Run targeted/full uIMax audit, fix local UI/accessibility issues, record report |
| Full product certified | Scope expansion | Permission to continue local certification ladder | Product-scope definition: which surfaces count as full product; whether push/deploy/external delivery included | Build claim matrix and certify additional local/read-only surfaces only |
| Runtime prompt injection certified | Design/implementation/verification gap; high risk | Permission to prepare design/test packet | Before code integration: exact config key, rollback, acceptance tests, whether prompt assembly may change | Create default-off design packet and regression tests; no runtime mutation yet |
| Prompt-cache/core integration certified | Design/implementation/verification gap; high risk | Permission to prepare cache-safe proof | Before core change: explicit go/no-go for modifying prompt assembly/cache boundaries | Produce cache-safety design and tests around stable/context/volatile prompt parts |
| Agent loop mutation | Exact authority + architecture gate | Permission to design and simulate | Exact mutation target, rollback command, route preflight, fresh tests, independent review | Shadow-only route/review packet; no conversation-loop mutation yet |
| Taskpool lifecycle writes | Exact execution authority | General authorization acknowledged | Exact board/task/mission id, intended action/status, idempotency key, evidence ref, readback command | Prepare task-intake/lifecycle contract; no lifecycle write |
| Scheduler/cron/watchdog | Exact execution authority | General authorization acknowledged | Exact script path, schedule, no-agent flag, deliver=local or exact gateway target, remove/rollback command | Prepare local-only watchdog design; no cron creation |
| External dispatch | Exact external authority | General authorization acknowledged | Exact platform, target/channel/user, payload, receipt/readback method | Prepare payload/receipt packet only |
| Publish/deploy/push | Exact release authority | General authorization acknowledged | Exact repo/remote/branch/env, push/deploy command, rollback path, post-action readback | Keep local commits and release notes; no push/deploy |
| Destructive operations | Exact destructive authority | General authorization acknowledged | Exact resource, destructive operation, backup/restore path, receipt/readback | Prepare cleanup proposal only |
| Payment/credential entry | Human-only gate | Not consumed by agent | Human must enter secrets/payment directly; never send/type secrets through agent | Stop at instruction packet |

## Reporting Rule Going Forward

Every future `not claimed` item must include one of these labels:

- `needs-user-target`: exact target/id/platform/env missing.
- `needs-user-payload`: exact message/payload/command missing.
- `needs-user-acceptance`: taste/grade/scope threshold missing.
- `needs-human-secret`: password/API key/payment/credential must be entered by user.
- `no-user-input-needed`: safe local/reversible work remains; continue without asking.

## Current next action

Proceeding with `no-user-input-needed`: uIMax targeted audit and local portability fix for the dashboard Context Engineering preflight panel.
