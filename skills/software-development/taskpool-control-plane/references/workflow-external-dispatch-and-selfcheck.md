# Workflow external dispatch and architecture self-check landing notes

Use when a modular workflow kernel has already reached local adapter write-through / external side-effect gates and the next work is to make external dispatch safe, auditable, and policy-governed.

## Landing sequence after adapter write-through

Preferred ladder:

```text
External Side-effect Human Gate
  → External Apply Executor Scaffold
  → External Apply Requirements / Target Adapter Contract
  → Local External Apply Outbox Recorded
  → Single Explicit External Dispatch Smoke Test
  → Governed Notification Policy
  → Guarded Manual-send Runner
  → Unattended Dispatch Policy Gate
```

Do not jump from a local outbox/contract directly to unattended dispatch.

## External apply requirements contract

Before any real apply target can run, land a contract packet that enumerates:

- target adapter options;
- whether each adapter is local-only, dry-run-only, or external;
- required authority per adapter;
- required inputs and target identifiers;
- blast radius;
- post-apply readback;
- receipt schema;
- rollback evidence schema;
- safe default.

Expected fail-closed state before target selection:

```text
real_apply_enabled=false
external_side_effects_enabled=false
selection_status=target_adapter_options_fully_enumerated_pending_selection
contract_status=real_apply_contracts_defined_no_target_selected
```

## Local outbox simulator target

When the user authorizes full advancement but has not selected a user-visible external target, the safe default target is a local simulator such as `taskpool_outbox_simulator`.

It may write local evidence artifacts and taskpool markers, but it must not dispatch externally.

Expected state:

```text
apply_status=local_outbox_simulator_apply_recorded
apply_mode=local_real_apply_no_external_dispatch
external_side_effects_enabled=false
readback_verified=true
```

Rollback evidence should be `not_needed_no_external_mutation`; retain local outbox artifacts for audit rather than deleting proof.

## Single explicit external dispatch smoke test

A user message like “接 TG 消息发送，系统测试” is narrow authorization for exactly one Telegram smoke-test message to the current/home Telegram target. It does not authorize repeated, unattended, or cross-adapter sends.

Record:

- exact target adapter and operation;
- tool receipt (`success`, platform, chat id, message id);
- receipt artifact conforming to the external apply receipt schema;
- rollback/correction evidence;
- taskpool marker using accepted evidence prefixes.

Use proof-check accepted evidence prefixes such as:

```text
command:send_message target=telegram success=true message_id=<id> chat_id=<id>
artifact:telegram_dispatch_receipt:<sha256>
proof:telegram_system_test_message_sent
classification:workflow_kernel_external_dispatch_smoke_test_complete
```

Avoid ad-hoc prefixes such as `tool:...`; proof-check treats them as unstructured evidence.

## Governed notification policy before automation

After one real smoke test, do not enable unattended sends. First land a policy layer with:

- target allowlist;
- allowed purposes;
- idempotency key fields;
- duplicate policy;
- rate limit per target chat;
- dry-run preview requirement;
- receipt ledger;
- compensating-message correction path.

Expected safe default:

```text
unattended_send_enabled=false
default_mode=dry_run_preview
```

The policy compiler should emit a `send_instruction` for a future explicit tool action; it should not call `send_message` itself. A separate guarded manual-send runner may later consume a dry-run packet plus explicit authorization and then record the real receipt.

## Architecture self-check after dispatch work

After external-dispatch phases, run a system architecture self-check before claiming the control plane is healthy. Collect evidence from:

```text
hermes doctor
~/.hermes/diagnostics/runner.py --json
brain_task_orchestrator.py selfcheck --json
brain_task_orchestrator.py proof-check --json
brain_task_orchestrator.py eligibility-check --json
hermes mission board/doctor/signals
cron job health
source leak check for nested .hermes in the source repo
git status
```

Report as a classification, not a victory lap. Example outcomes:

```text
HEALTHY
DEGRADED_NOT_BLOCKED
BLOCKED_NEEDS_HUMAN
```

Score conservatively. Scheduled automation degradation can coexist with a usable interactive/control-plane core; separate those layers.

When cron/provider degradation is found, classify it before repairing or mutating scheduler state:

```bash
python3 scripts/cron_provider_degradation_triage.py --write-report --json
./scripts/run_tests.sh tests/scripts/test_cron_provider_degradation_triage.py
```

The Phase 22 triage boundary is read-only except local evidence under `docs/private/workflow-kernel-cron-provider-triage/`. Do not pause/resume/remove jobs, rerun failed jobs, retry external notifications, migrate config, or run npm audit fixes in the same slice. Use primary classes (`provider_generation`, `script_network_failure`, `telegram_delivery`, `script_failure`, `network_or_proxy`, `unknown`) to choose one repair class for the next phase.

For the first provider-generation repair slice, add a bounded provider/network probe ledger instead of retrying model calls:

```bash
python3 scripts/provider_network_probe_ledger.py --write-report --json
./scripts/run_tests.sh tests/scripts/test_provider_network_probe_ledger.py
```

The Phase 23 probe must be unauthenticated and side-effect free: no LLM prompt, no credential read/write, no cron mutation, no Telegram send. Treat HTTP `401/403/404` as reachability evidence because they still prove DNS/proxy/TLS/edge routing; record provider-specific TLS/proxy/timeout classes for downstream cron gates.

## Common P1/P2 classification

- P1: cron/provider-generation errors affecting scheduled automation.
- P1: upstream ratchet review blind due to network/fetch failure.
- P2: config schema drift that requires reviewed migration.
- P2: dependency audit issues not on the active execution path.
- P2: edge-node heartbeat/lease policy warnings.
- P2: autorun kill switch active by safe default.

## Anti-conditions

Do not use this reference to justify:

- global autorun enablement;
- config migration without backup/diff;
- npm audit fix without scoped tests;
- repeated or unattended Telegram sends;
- Lark/GitHub mutations without exact target and rollback;
- treating a plan or policy document as proof that dispatch executed.
