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

Then compile a read-only provider health gate before wiring cron execution:

```bash
python3 scripts/cron_provider_health_gate.py --write-report --json
./scripts/run_tests.sh tests/scripts/test_cron_provider_health_gate.py
```

The Phase 24 gate consumes `~/.hermes/cron/jobs.json` and the latest provider probe, then emits decisions like `skip_provider_health_degraded`, `retry_allowed_by_provider_health`, and `run_with_degraded_provider_exclusions`. It must not mutate cron jobs or rerun anything; actual cron wrapper rollout is a later opt-in phase.

Before migrating this growing script/ADR ladder into a new runtime architecture, compile a migration evaluation instead of switching behavior directly:

```bash
python3 scripts/workflow_architecture_migration_evaluation.py --write-report --json
./scripts/run_tests.sh tests/scripts/test_workflow_architecture_migration_evaluation.py
```

The safe Phase 25 recommendation is incremental strangler migration: create a `kernel.*` package scaffold, keep existing scripts as compatibility CLIs, require parity tests for Phase17-24 behavior, and stop short of cron mutation, autorun changes, external dispatch expansion, or evidence-directory deletion. Big-bang rewrite is not acceptable because taskpool/mission/cron/external-dispatch semantics are evidence-sensitive.

For Phase 26, create only the package scaffold and shared helper extraction:

```bash
python3 -m py_compile workflow_kernel/__init__.py workflow_kernel/io.py
./scripts/run_tests.sh tests/workflow_kernel/test_kernel_scaffold.py \
  tests/scripts/test_workflow_architecture_migration_evaluation.py \
  tests/scripts/test_cron_provider_health_gate.py
```

Keep `workflow_kernel.RUNTIME_SWITCH_ENABLED = False`. Existing scripts remain compatibility CLIs; importing shared IO helpers is allowed, but cron wrappers, external dispatch, autorun, config migration, and evidence-directory consolidation remain closed.

For Phase 27 runtime-switch readiness, make the kernel switchable in compatibility-shim mode without enabling it by default:

```bash
python3 scripts/workflow_kernel_runtime_readiness.py --write-report --json
./scripts/run_tests.sh tests/workflow_kernel/test_runtime_switch_readiness.py \
  tests/workflow_kernel/test_kernel_scaffold.py \
  tests/scripts/test_workflow_architecture_migration_evaluation.py \
  tests/scripts/test_cron_provider_health_gate.py
```

Required status is `RUNTIME_SWITCH_READY_PENDING_EXPLICIT_ENABLE`; `runtime_switch_enabled_by_default` must remain false. This permits a later explicit single-wrapper rollout, but still forbids global cron mutation, autorun enablement, config migration, and external-dispatch expansion.

For Phase 28, perform only one opt-in wrapper rollout against the most specific degraded provider job:

```bash
python3 -m py_compile ~/.hermes/scripts/multi-model-smoke-daily-full-wrapper.py
./scripts/run_tests.sh tests/scripts/test_multi_model_smoke_daily_wrapper_gate.py \
  tests/scripts/test_cron_provider_health_gate.py \
  tests/workflow_kernel/test_runtime_switch_readiness.py
python3 ~/.hermes/scripts/multi-model-smoke-daily-full-wrapper.py
```

Expected readback is `provider_health_degraded_skip`, `model_generation_attempted=false`, `cron_state_mutated=false`, and an append-only local skip ledger under `~/.hermes/state/cron-provider-health-gate/`. Do not edit `cron/jobs.json`, enable the global runtime switch, or patch multiple wrappers in the same slice.

For Phase 29, wire the every-4h multi-provider wrapper to consume `run_with_degraded_provider_exclusions` as explicit model selection args:

```bash
python3 -m py_compile ~/.hermes/scripts/multi-model-smoke-every4h-wrapper.py
./scripts/run_tests.sh tests/scripts/test_multi_model_smoke_every4h_wrapper_gate.py \
  tests/scripts/test_multi_model_smoke_daily_wrapper_gate.py \
  tests/scripts/test_cron_provider_health_gate.py
HERMES_MULTI_MODEL_SMOKE_EVERY4H_PLAN_ONLY=1 python3 ~/.hermes/scripts/multi-model-smoke-every4h-wrapper.py
```

Expected plan-only readback is `provider_health_exclusion_plan`, `selected_models` excluding `mimo-v2.5-pro`, `degraded_endpoints_excluded=[xiaomi]`, `model_generation_attempted=false`, and `cron_state_mutated=false`. This phase may patch only the every-4h wrapper; it must not execute model generation during verification or mutate cron job definitions.

If later evidence suggests a provider is degraded only because the probe request shape diverges from runtime, calibrate the probe before keeping cron quarantine decisions. For Xiaomi/MiMo, the probe must not use retired/stale hosts like `api.mimogpt.com`; it should resolve the runtime OpenAI-compatible base URL (`XIAOMI_BASE_URL` if set, otherwise `https://api.xiaomimimo.com/v1`) and probe `<base_url>/models`. `401` is reachable evidence. Also ensure wrappers read `docs/private/workflow-kernel-cron-provider-health-gate/cron_provider_health_gate_*.json`; stale report paths can keep old quarantine decisions alive after probe repair.

```bash
python3 scripts/provider_network_probe_ledger.py --write-report --json --timeout 8
python3 scripts/cron_provider_health_gate.py --write-report --json
HERMES_MULTI_MODEL_SMOKE_EVERY4H_PLAN_ONLY=1 python3 ~/.hermes/scripts/multi-model-smoke-every4h-wrapper.py
./scripts/run_tests.sh tests/scripts/test_provider_network_probe_ledger.py \
  tests/scripts/test_cron_provider_health_gate.py \
  tests/scripts/test_multi_model_smoke_every4h_wrapper_gate.py \
  tests/scripts/test_multi_model_smoke_daily_wrapper_gate.py
```

Expected calibrated readback: Xiaomi `classification=reachable`, `status_code=401` on `*/v1/models`, health gate `degraded_endpoints=[]`, and every-4h plan returns base args only. This proves edge reachability, not credential validity, quota, or successful generation.

For Phase 31 architecture switching, do not jump to global scheduler rewrite. Move the already-proven opt-in wrapper gate logic into a kernel compatibility shim while preserving cron entrypoints:

```bash
python3 -m py_compile workflow_kernel/cron_wrappers.py \
  ~/.hermes/scripts/multi-model-smoke-daily-full-wrapper.py \
  ~/.hermes/scripts/multi-model-smoke-every4h-wrapper.py
./scripts/run_tests.sh tests/workflow_kernel/test_cron_wrapper_kernel_shim.py \
  tests/scripts/test_multi_model_smoke_every4h_wrapper_gate.py \
  tests/scripts/test_multi_model_smoke_daily_wrapper_gate.py \
  tests/workflow_kernel/test_runtime_switch_readiness.py
HERMES_MULTI_MODEL_SMOKE_EVERY4H_PLAN_ONLY=1 python3 ~/.hermes/scripts/multi-model-smoke-every4h-wrapper.py
```

Expected readback: wrapper payload includes `kernel_shim=true`, `model_generation_attempted=false`, and `cron_state_mutated=false`. Keep `workflow_kernel.RUNTIME_SWITCH_ENABLED=false`, do not edit `cron/jobs.json`, and do not broaden to all wrappers in this slice.

For Phase 32, add only a read-only scheduler-level projection that correlates cron job definitions, wrapper kernel-shim adoption, latest health gate, and latest provider probe freshness:

```bash
python3 -m py_compile scripts/workflow_cron_runtime_projection.py
./scripts/run_tests.sh tests/scripts/test_workflow_cron_runtime_projection.py \
  tests/workflow_kernel/test_cron_wrapper_kernel_shim.py \
  tests/scripts/test_cron_provider_health_gate.py \
  tests/scripts/test_provider_network_probe_ledger.py
python3 scripts/provider_network_probe_ledger.py --write-report --json --timeout 8
python3 scripts/cron_provider_health_gate.py --write-report --json
python3 scripts/workflow_cron_runtime_projection.py --write-report --json
```

Expected readback: `SCHEDULER_READBACK_PROJECTION_READY`, fresh gate/probe artifacts, and wrapper projections classified as either `KERNEL_SHIM_SCHEDULER_READBACK_READY` or `KERNEL_SHIM_NO_GATE_DECISION_NEEDED`. Missing gate decisions are acceptable only for non-error jobs because the Phase 24 gate emits decisions for failed jobs. Do not execute cron jobs or change scheduler state in this phase.

For Phase 33, correlate real scheduled-run outcomes with the Phase 32 projection without triggering cron:

```bash
python3 -m py_compile scripts/workflow_cron_run_outcome_correlation.py scripts/workflow_cron_runtime_projection.py
./scripts/run_tests.sh tests/scripts/test_workflow_cron_run_outcome_correlation.py \
  tests/scripts/test_workflow_cron_runtime_projection.py \
  tests/workflow_kernel/test_cron_wrapper_kernel_shim.py
python3 scripts/workflow_cron_run_outcome_correlation.py --write-report --json
```

Expected partial readback may be `REAL_RUN_CORRELATION_PARTIAL_READY` when at least one wrapper has run after the projection and another has not reached its next schedule yet. Do not claim full two-wrapper runtime correlation until both wrappers have post-projection logs, or until a future wrapper-run ledger records explicit per-run kernel/gate metadata.

For Phase 34, add append-only wrapper-run receipts for future scheduled runs instead of triggering cron. Patch only the opted-in wrappers and the kernel helper:

```bash
python3 -m py_compile workflow_kernel/cron_wrappers.py \
  ~/.hermes/scripts/multi-model-smoke-daily-full-wrapper.py \
  ~/.hermes/scripts/multi-model-smoke-every4h-wrapper.py
./scripts/run_tests.sh tests/workflow_kernel/test_cron_wrapper_kernel_shim.py \
  tests/scripts/test_multi_model_smoke_every4h_wrapper_gate.py \
  tests/scripts/test_multi_model_smoke_daily_wrapper_gate.py
HERMES_CRON_WRAPPER_RECEIPT_LEDGER=/tmp/phase34_receipts.jsonl \
  HERMES_MULTI_MODEL_SMOKE_EVERY4H_PLAN_ONLY=1 \
  python3 ~/.hermes/scripts/multi-model-smoke-every4h-wrapper.py
```

Expected readback: receipt has `kernel_shim=true`, `runtime_mode`, `gate_report_id` when available, `cron_state_mutated=false`, and `external_side_effects=false`. The production ledger path is `~/.hermes/state/cron-provider-health-gate/wrapper_run_receipts.jsonl`; verification should use an override ledger to avoid polluting production receipts.

For Phase 35, make run correlation receipt-aware without requiring a live cron run:

```bash
python3 -m py_compile scripts/workflow_cron_run_outcome_correlation.py
./scripts/run_tests.sh tests/scripts/test_workflow_cron_run_outcome_correlation.py
python3 scripts/workflow_cron_run_outcome_correlation.py --write-report --json
```

Expected behavior: if production `wrapper_run_receipts.jsonl` has post-projection rows, classify `RECEIPT_AFTER_PROJECTION_CORRELATED`; otherwise fall back to wrapper JSONL log correlation such as `REAL_RUN_CORRELATION_PARTIAL_READY`. Do not trigger cron just to create receipts.

For Phase 36, compile one read-only runtime readiness summary across runtime switch, scheduler projection, run correlation, receipt readiness, provider gate, and provider probe freshness:

```bash
python3 -m py_compile scripts/workflow_runtime_readiness_summary.py \
  scripts/workflow_cron_run_outcome_correlation.py \
  scripts/workflow_cron_runtime_projection.py \
  workflow_kernel/cron_wrappers.py
./scripts/run_tests.sh tests/scripts/test_workflow_runtime_readiness_summary.py \
  tests/scripts/test_workflow_cron_run_outcome_correlation.py \
  tests/scripts/test_workflow_cron_runtime_projection.py \
  tests/workflow_kernel/test_cron_wrapper_kernel_shim.py
python3 scripts/workflow_runtime_readiness_summary.py --write-report --json
```

Expected readback: `RUNTIME_READINESS_SUMMARY_READY_PENDING_EXPLICIT_ENABLE`, `blocking_checks=[]`, fresh gate/probe artifacts, `runtime_switch_enabled_by_default=false`. This is an operator summary only; it is not authorization to enable the runtime switch.

For Phase 37, compile the human authorization packet instead of crossing runtime/scheduler boundaries:

```bash
python3 -m py_compile scripts/workflow_runtime_enablement_packet.py \
  scripts/workflow_runtime_readiness_summary.py
./scripts/run_tests.sh tests/scripts/test_workflow_runtime_enablement_packet.py \
  tests/scripts/test_workflow_runtime_readiness_summary.py
python3 scripts/workflow_runtime_enablement_packet.py --write-report --json
```

Expected readback: `RUNTIME_ENABLEMENT_HUMAN_AUTH_PACKET_READY` with options `A_READ_ONLY_CONTINUE`, `B_SINGLE_WRAPPER_RUNTIME_ENABLE_DRY_RUN`, `C_SINGLE_WRAPPER_SCHEDULER_NATIVE_ROLLOUT`, `D_WAIT_FOR_NATURAL_RECEIPTS`. Do not enable runtime switch, mutate cron, trigger jobs, call credentialed model generation, or send external messages without the specific option being authorized.

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
