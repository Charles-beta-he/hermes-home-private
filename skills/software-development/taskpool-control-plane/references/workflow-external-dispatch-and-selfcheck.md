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

For Phase 38, when asked to “梳理顺序” before continuing, compile the ordered phase/dependency map instead of crossing the enablement boundary:

```bash
python3 -m py_compile scripts/workflow_sequence_map.py \
  scripts/workflow_runtime_enablement_packet.py \
  scripts/workflow_runtime_readiness_summary.py
./scripts/run_tests.sh tests/scripts/test_workflow_sequence_map.py \
  tests/scripts/test_workflow_runtime_enablement_packet.py \
  tests/scripts/test_workflow_runtime_readiness_summary.py
python3 scripts/workflow_sequence_map.py --write-report --json
```

Expected readback: `WORKFLOW_SEQUENCE_MAP_READY`, `validation_errors=[]`, ordered Phase17-37 dependencies, and next ladder Phase39(A read-only runbook), Phase40(A drift watcher), Phase41(B dry-run), Phase42(C scheduler-native rollout). Continue by default into Phase39 unless the user explicitly selects B/C.

For Phase 39, compile an enablement runbook and rollback drill under `A_READ_ONLY_CONTINUE`; do not execute the runbook:

```bash
python3 -m py_compile scripts/workflow_enablement_runbook.py \
  scripts/workflow_sequence_map.py \
  scripts/workflow_runtime_enablement_packet.py
./scripts/run_tests.sh tests/scripts/test_workflow_enablement_runbook.py \
  tests/scripts/test_workflow_sequence_map.py \
  tests/scripts/test_workflow_runtime_enablement_packet.py
python3 scripts/workflow_enablement_runbook.py --write-report --json
```

Expected readback: `ENABLEMENT_RUNBOOK_READY`, preflight commands, dry-run commands using temp receipt ledger only, rollback drill, and go/no-go gates. The runbook is executable documentation, not permission to run runtime/scheduler changes.

For Phase 40, add a read-only drift watcher over projection/correlation/readiness-summary artifacts and production wrapper-run receipts:

```bash
python3 -m py_compile scripts/workflow_drift_watch.py \
  scripts/workflow_enablement_runbook.py
./scripts/run_tests.sh tests/scripts/test_workflow_drift_watch.py \
  tests/scripts/test_workflow_enablement_runbook.py
python3 scripts/workflow_drift_watch.py --write-report --json
```

Expected readback may be `DRIFT_WATCH_DEGRADED_NOT_BLOCKED` with `production_receipts_not_complete` until natural scheduled wrapper runs append receipts. Do not trigger cron solely to satisfy the watcher.

For Phase 41, after explicit `B_SINGLE_WRAPPER_RUNTIME_ENABLE_DRY_RUN` authorization, execute only a single-wrapper shadow dry-run against every-4h using a temporary receipt ledger:

```bash
python3 -m py_compile scripts/workflow_runtime_shadow_dry_run.py
./scripts/run_tests.sh tests/scripts/test_workflow_runtime_shadow_dry_run.py
python3 scripts/workflow_runtime_shadow_dry_run.py --write-report --json
```

Expected readback: `RUNTIME_SHADOW_DRY_RUN_READY`, `cron_state_mutated=false`, `credentialed_generation_attempted=false`, and `receipt_runtime_mode=plan_only`. This is not scheduler mutation.

For Phase 42, after explicit `C_SINGLE_WRAPPER_SCHEDULER_NATIVE_ROLLOUT` authorization, mutate exactly one job (`2c14ca2a9bd2`, every-4h) from the legacy wrapper path to the scheduler-native workflow-kernel runner, with a backup and rollback command:

```bash
python3 -m py_compile scripts/workflow_scheduler_native_rollout.py \
  ~/.hermes/scripts/workflow-kernel-multi-model-smoke-every4h-runner.py
./scripts/run_tests.sh tests/scripts/test_workflow_scheduler_native_rollout.py \
  tests/scripts/test_workflow_cron_runtime_projection.py \
  tests/scripts/test_workflow_cron_run_outcome_correlation.py
python3 scripts/workflow_scheduler_native_rollout.py --dry-run --json
python3 scripts/workflow_scheduler_native_rollout.py --write-report --json
HERMES_MULTI_MODEL_SMOKE_EVERY4H_PLAN_ONLY=1 \
  python3 ~/.hermes/scripts/workflow-kernel-multi-model-smoke-every4h-runner.py
python3 scripts/workflow_cron_runtime_projection.py --write-report --json
python3 scripts/workflow_cron_run_outcome_correlation.py --write-report --json
python3 scripts/workflow_runtime_readiness_summary.py --write-report --json
python3 scripts/workflow_drift_watch.py --write-report --json
```

Expected readback: `SCHEDULER_NATIVE_ROLLOUT_APPLIED`, job script set to `workflow-kernel-multi-model-smoke-every4h-runner.py`, rollback backup exists, native plan-only receipt has `runtime_mode=scheduler_native_plan_only`, projection remains ready, readiness summary remains ready. Do not broaden to the daily-full job or global runtime switch without a fresh explicit gate.

For Phase 43-45, after explicit full authorization through auto-enable, proceed in order: daily receipt closure, daily scheduler-native rollout, runtime switch enable. Keep each slice independently reversible and verified:

```bash
HERMES_MULTI_MODEL_SMOKE_DAILY_PLAN_ONLY=1 \
  python3 ~/.hermes/scripts/workflow-kernel-multi-model-smoke-daily-full-runner.py
python3 scripts/workflow_scheduler_native_rollout.py --target daily-full --dry-run --json
python3 scripts/workflow_scheduler_native_rollout.py --target daily-full --write-report --json
python3 scripts/workflow_cron_runtime_projection.py --write-report --json
python3 scripts/workflow_cron_run_outcome_correlation.py --write-report --json
python3 scripts/workflow_drift_watch.py --write-report --json
python3 scripts/workflow_kernel_runtime_readiness.py --write-report --json
python3 scripts/workflow_runtime_readiness_summary.py --write-report --json
```

Expected readback: daily plan-only receipt `runtime_mode=scheduler_native_plan_only`, daily job script `workflow-kernel-multi-model-smoke-daily-full-runner.py`, every4h still `workflow-kernel-multi-model-smoke-every4h-runner.py`, projection ready, receipt correlation partial/ready, drift clear, `RUNTIME_SWITCH_AUTO_ENABLED`, `RUNTIME_READINESS_SUMMARY_AUTO_ENABLED`, and `explicit_enable_required=false`. Auto-enable still does not authorize unrelated external dispatch expansion, credential policy broadening, or broad scheduler rewrites without scoped rollback gates.

For Phase 46 after auto-enable, do not immediately broaden behavior. Observe natural scheduled runs and refresh the read-only evidence chain:

```bash
python3 scripts/workflow_cron_runtime_projection.py --write-report --json
python3 scripts/workflow_cron_run_outcome_correlation.py --write-report --json
python3 scripts/workflow_runtime_readiness_summary.py --write-report --json
python3 scripts/workflow_drift_watch.py --write-report --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
```

Expected readback: both opted-in jobs remain scheduler-native, runtime summary remains `RUNTIME_READINESS_SUMMARY_AUTO_ENABLED` or `RUNTIME_READINESS_SUMMARY_DEGRADED_NOT_BLOCKED` when waiting for post-projection scheduled runs, drift remains `DRIFT_WATCH_CLEAR_READ_ONLY`, and scheduled-run receipts/logs are correlated without manually triggering cron. If no new scheduled run has occurred yet, classify it as `POST_AUTO_ENABLE_OBSERVATION_PENDING_SCHEDULED_RUN` rather than a failure.

For Phase 47 after auto-enable observation, compile an external-dispatch expansion candidate packet before any external side effect:

```bash
python3 -m py_compile scripts/workflow_external_dispatch_expansion_packet.py
./scripts/run_tests.sh tests/scripts/test_workflow_external_dispatch_expansion_packet.py
python3 scripts/workflow_external_dispatch_expansion_packet.py --write-report --json
```

Expected readback: `EXTERNAL_DISPATCH_EXPANSION_CANDIDATE_READY`, `unattended_external_dispatch_enabled=false`, `external_side_effects_executed=false`, default adapter `local_outbox_simulator`, and candidate tracks for local outbox, dry-run policy, guarded single send, and unattended policy gate. Do not call `send_message`, mutate Lark/GitHub, read credentials, or enable unattended dispatch until exact adapter/target/payload/mode/idempotency/rollback are selected.

For Phase 48 after broad authorization but without a concrete external target/payload, select the safe default local outbox track:

```bash
python3 -m py_compile scripts/workflow_external_dispatch_policy_gate.py
./scripts/run_tests.sh tests/scripts/test_workflow_external_dispatch_policy_gate.py
python3 scripts/workflow_external_dispatch_policy_gate.py --write-report --json
```

Expected readback: `EXTERNAL_DISPATCH_POLICY_GATE_LOCAL_OUTBOX_RECORDED`, `selected_track=P47A_LOCAL_OUTBOX_ONLY`, `selected_adapter=local_outbox_simulator`, `external_side_effects_executed=false`, `unattended_external_dispatch_enabled=false`, with local outbox and receipt artifacts under `docs/private/workflow-kernel-external-dispatch-policy-gate/`. This is the correct full-landing next step when the user authorizes continuation but does not supply a user-visible external target or payload.

For Phase 49 productization, compile schema/projection-only Workflow Pack and Agent Pack manifests from the proven kernel/external-dispatch governance chain:

```bash
python3 -m py_compile scripts/workflow_pack_manifest_compiler.py
./scripts/run_tests.sh tests/scripts/test_workflow_pack_manifest_compiler.py
python3 scripts/workflow_pack_manifest_compiler.py --write-report --json
```

Expected readback: `WORKFLOW_AGENT_PACK_MANIFESTS_READY`, `validation_errors=[]`, workflow pack `workflow_kernel_external_dispatch_governance`, agent pack `agent.workflow_kernel_operator`, fail-closed side-effect policy, and artifacts under `docs/private/workflow-kernel-pack-manifests/`. This phase is projection-only: no cron mutation, model generation, credential access, external send, or unattended dispatch. If exact external adapter/target/payload is still absent after Phase49, continue to pack registry/control-tower projection rather than inventing a guarded send.

For Phase 51, project the Phase49 manifests into a read-only pack registry/control-tower view:

```bash
python3 -m py_compile scripts/workflow_pack_registry_projection.py
./scripts/run_tests.sh tests/scripts/test_workflow_pack_registry_projection.py
python3 scripts/workflow_pack_registry_projection.py --write-report --json
```

Expected readback: `PACK_REGISTRY_PROJECTION_READY`, blockers `[]`, module rows with risk/gate/side-effect flags, and artifacts under `docs/private/workflow-kernel-pack-registry/`. This remains read-only: no cron mutation, task lifecycle mutation, model generation, credential access, external send, or unattended dispatch. After Phase51, stop at the larger divergence unless the user chooses: Phase50 guarded single external send (requires exact adapter/target/payload/mode/idempotency/rollback) vs Phase52 Control Tower UI/API productization.

For Phase 50, execute at most one exact guarded external send only after the user selects concrete adapter/target/payload. Prefer `hermes send --to telegram --json '<message>'` for Telegram home because it reuses Hermes gateway config and emits structured receipt. If the in-process `send_message` tool fails due to missing isolated dependencies, do not loop; use the CLI path or stop honestly. Then record the receipt:

```bash
python3 -m py_compile scripts/workflow_guarded_external_send_receipt.py
./scripts/run_tests.sh tests/scripts/test_workflow_guarded_external_send_receipt.py
python3 scripts/workflow_guarded_external_send_receipt.py --send-result /tmp/phase50_send_result.json --write-report --json
```

Expected readback: `GUARDED_EXTERNAL_SEND_VERIFIED`, exact platform/target/message_id, `external_side_effect_executed=true`, `unattended_external_dispatch_enabled=false`, and a compensating-message correction path. This authorizes one send only; no repeated or unattended sends.

For Phase 52, after Phase50 and Phase51, emit a read-only Control Tower UI/API projection:

```bash
python3 -m py_compile scripts/workflow_control_tower_projection.py
./scripts/run_tests.sh tests/scripts/test_workflow_control_tower_projection.py
python3 scripts/workflow_control_tower_projection.py --write-report --json
```

Expected readback: `CONTROL_TOWER_UI_API_PROJECTION_READY`, JSON API payload, static HTML dashboard artifact, browser/readback evidence, and no live server/runtime mutation/additional external send. If the user says both Phase53 and Phase54 are required, continue in order rather than treating them as a divergence.

For Phase 53, integrate the Workflow Kernel projection into the existing live Control Tower dashboard/API snapshot instead of creating a parallel server:

```bash
python3 -m py_compile hermes_cli/control_tower.py
./scripts/run_tests.sh tests/hermes_cli/test_control_tower_snapshot.py tests/plugins/test_control_tower_dashboard_plugin.py
```

Expected readback: `control_tower.build_snapshot()["workflow_kernel_control_tower"].status == "ready"`, latest guarded send message id present, dashboard plugin renders the Workflow Kernel panel, and authenticated dashboard API `/api/plugins/control-tower/snapshot` exposes the same read-only projection. If a running dashboard process was started before the code change, restart only the dashboard process to load the new backend module; do not restart gateway/message delivery casually.

For Phase 54, compile the unattended dispatch policy gate fail-closed:

```bash
python3 -m py_compile scripts/workflow_unattended_dispatch_policy_gate.py
./scripts/run_tests.sh tests/scripts/test_workflow_unattended_dispatch_policy_gate.py
python3 scripts/workflow_unattended_dispatch_policy_gate.py --write-report --json
```

Expected readback: `UNATTENDED_DISPATCH_POLICY_GATE_READY`, `default_mode=dry_run_preview`, `unattended_dispatch_enabled=false`, `external_side_effects_executed=false`, plus policy/dry-run instruction artifacts under `docs/private/workflow-kernel-unattended-dispatch-policy/`. If the user says Phase55 and Phase56 are both required, continue in order rather than treating them as a divergence.

For Phase 55, land the unattended dry-run scheduler runner and append-only receipt ledger without installing cron or sending messages:

```bash
python3 -m py_compile scripts/workflow_unattended_dry_run_scheduler.py
./scripts/run_tests.sh tests/scripts/test_workflow_unattended_dry_run_scheduler.py
python3 scripts/workflow_unattended_dry_run_scheduler.py --append-ledger --write-report --json
```

Expected readback: `UNATTENDED_DRY_RUN_SCHEDULER_READY`, `would_send=false`, `external_side_effects_executed=false`, `unattended_dispatch_enabled=false`, `cron_state_mutated=false`, and artifacts under `docs/private/workflow-kernel-unattended-dry-run-scheduler/`. This creates a cron-safe runner but does not create or edit any cron job.

For Phase 56, expose Control Tower policy editor / approval UI as an approval-ledger-only surface:

```bash
python3 -m py_compile hermes_cli/control_tower.py plugins/control-tower/dashboard/plugin_api.py
./scripts/run_tests.sh tests/hermes_cli/test_control_tower_snapshot.py \
  tests/plugins/test_control_tower_dashboard_plugin.py \
  tests/plugins/test_control_tower_workflow_kernel_policy_api.py
```

Expected readback: `POLICY_EDITOR_APPROVAL_UI_READY`, allowed decisions `draft|approve_dry_run_only|reject|request_changes`, local approval ledger under `docs/private/workflow-kernel-policy-editor/`, and live dashboard API exposes `workflow_kernel_control_tower.policy_editor`. The endpoint `POST /api/plugins/control-tower/workflow-kernel/policy-editor/decision` must only record intent; it must not mutate policy, enable unattended dispatch, install cron, or send messages. If the user says Phase57 and Phase58 are both required, continue in order rather than treating them as a divergence.

For Phase 57, roll out exactly one no-agent/local dry-run cron job with backup/rollback evidence:

```bash
python3 -m py_compile scripts/workflow_dry_run_cron_rollout.py ~/.hermes/scripts/workflow-kernel-unattended-dry-run-runner.py
./scripts/run_tests.sh tests/scripts/test_workflow_dry_run_cron_rollout.py tests/scripts/test_workflow_unattended_dry_run_scheduler.py
python3 scripts/workflow_dry_run_cron_rollout.py --dry-run --write-report --json
python3 scripts/workflow_dry_run_cron_rollout.py --write-report --json
python3 ~/.hermes/scripts/workflow-kernel-unattended-dry-run-runner.py
```

Expected readback: `DRY_RUN_CRON_ROLLOUT_APPLIED`, job id `wk57dryrun01`, `script=workflow-kernel-unattended-dry-run-runner.py`, `no_agent=true`, `deliver=local`, `would_send=false`, `external_side_effects_executed=false`, and a rollback backup under `~/.hermes/cron/jobs.json.bak-phase57-*`. This is a scheduler mutation but still no external dispatch.

For Phase 58, compile the guarded send runner activation packet/contract without implementing or activating the runner:

```bash
python3 -m py_compile scripts/workflow_guarded_send_runner_activation_packet.py
./scripts/run_tests.sh tests/scripts/test_workflow_guarded_send_runner_activation_packet.py
python3 scripts/workflow_guarded_send_runner_activation_packet.py --write-report --json
```

Expected readback: `GUARDED_SEND_RUNNER_ACTIVATION_PACKET_READY`, `manual_send_runner_is_active_now=false`, `unattended_dispatch_enabled=false`, `external_side_effects_executed=false`, `send_message_called=false`, and contract artifacts under `docs/private/workflow-kernel-guarded-send-runner-activation/`. If the user says Phase59 and Phase60 are both required, continue in order rather than treating them as a divergence.

For Phase 59, implement the guarded manual-send runner with preview-by-default behavior:

```bash
python3 -m py_compile scripts/workflow_guarded_manual_send_runner.py
./scripts/run_tests.sh tests/scripts/test_workflow_guarded_manual_send_runner.py
python3 scripts/workflow_guarded_manual_send_runner.py --write-report --json
```

Expected readback: `GUARDED_MANUAL_SEND_RUNNER_READY`, target `telegram`, deterministic idempotency key, `external_side_effects_executed=false`, and artifacts under `docs/private/workflow-kernel-guarded-manual-send-runner/`. The runner must require `--execute` plus packet/policy/idempotency validation before it can call `hermes send`.

For Phase 60, execute exactly one packet-approved Telegram home send through the Phase59 runner:

```bash
python3 scripts/workflow_guarded_manual_send_runner.py --execute --write-report --json
```

Expected readback: `ONE_SHOT_GUARDED_SEND_VERIFIED`, exact `message_id`, `chat_id`, payload hash, idempotency key, `external_side_effects_executed=true`, `unattended_dispatch_enabled=false`, and append-only receipt ledger. This authorizes one send only; do not enable repeated, cron, unattended, or cross-adapter sends. If the same governed Workflow Kernel sequence continues and the user says Phase61 and Phase62 are both required, continue in order rather than treating them as a divergence.

Applicability: only for this Hermes-owned Workflow Kernel external-dispatch governance ladder after Phase60 one-shot guarded send evidence exists. Anti-condition: do not apply to unrelated projects, generic notification systems, or any workflow that lacks exact target/payload/receipt/compensation evidence.

For Phase 61, run the post-send correlation and compensation watch without any new send:

```bash
python3 -m py_compile scripts/workflow_post_send_correlation_watch.py
./scripts/run_tests.sh tests/scripts/test_workflow_post_send_correlation_watch.py
python3 scripts/workflow_post_send_correlation_watch.py --write-report --json
```

Expected readback: `POST_SEND_CORRELATION_COMPENSATION_WATCH_READY`, Phase60 `message_id` correlated with the ledger, idempotency/payload hash match, compensation path present, `new_message_sent=false`, and `unattended_dispatch_enabled=false`.

For Phase 62, generate the unattended dispatch enablement packet fail-closed:

```bash
python3 -m py_compile scripts/workflow_unattended_dispatch_enablement_packet.py
./scripts/run_tests.sh tests/scripts/test_workflow_unattended_dispatch_enablement_packet.py
python3 scripts/workflow_unattended_dispatch_enablement_packet.py --write-report --json
```

Expected readback: `UNATTENDED_DISPATCH_ENABLEMENT_PACKET_READY`, options `A_KEEP_MANUAL_ONLY|B_APPROVE_DRY_RUN_ONLY_AUTOMATION|C_APPROVE_ONE_TARGET_LIMITED_UNATTENDED_SENDS`, default `A_KEEP_MANUAL_ONLY`, `unattended_dispatch_enabled=false`, `external_side_effects_executed=false`, and `cron_state_mutated=false`. This is a packet/decision schema only; do not enable repeated sends without a future explicit decision/apply phase. If the same governed Workflow Kernel sequence continues and the user says Phase63 and Phase64 are both required, continue in order rather than treating them as a divergence.

Applicability: only for the Hermes-owned Workflow Kernel external-dispatch governance ladder after Phase62 enablement packet evidence exists. Anti-condition: do not apply to generic product notification automation or any system where `keep_manual_only` is not an explicitly authorized safe default.

For Phase 63, record an explicit unattended enablement decision without applying it:

```bash
python3 -m py_compile scripts/workflow_unattended_decision_record.py
./scripts/run_tests.sh tests/scripts/test_workflow_unattended_decision_record.py
python3 scripts/workflow_unattended_decision_record.py --decision keep_manual_only --write-report --json
```

Expected readback: `UNATTENDED_DECISION_RECORD_READY`, `decision=keep_manual_only`, `selected_option=A_KEEP_MANUAL_ONLY`, `record_only=true`, `unattended_dispatch_enabled=false`, and `external_side_effects_executed=false`.

For Phase 64, close the ladder on safe-default manual-only mode:

```bash
python3 -m py_compile scripts/workflow_manual_only_closure.py
./scripts/run_tests.sh tests/scripts/test_workflow_manual_only_closure.py
python3 scripts/workflow_manual_only_closure.py --write-report --json
```

Expected readback: `MANUAL_ONLY_CLOSURE_READY`, `final_mode=manual_only_with_no_send_dry_run_cron`, `unattended_dispatch_enabled=false`, `external_side_effects_executed=false`, and closed paths include repeated/unattended/cron-triggered/cross-adapter dispatch without new authorization. If the same governed Workflow Kernel sequence continues, adjacent phases are sequential work, not a divergence; stop only for competing schemes at the same implementation point.

For Phase 65, add read-only monitoring of the manual-only closure invariants:

```bash
python3 -m py_compile scripts/workflow_manual_only_closure_monitoring.py
./scripts/run_tests.sh tests/scripts/test_workflow_manual_only_closure_monitoring.py
python3 scripts/workflow_manual_only_closure_monitoring.py --write-report --json
```

Expected readback: `MANUAL_ONLY_MONITORING_CLEAR`, `drift=[]`, dry-run job `wk57dryrun01` still `no_agent=true` and `deliver=local`, `read_only=true`, `unattended_dispatch_enabled=false`, `external_side_effects_executed=false`, and `cron_state_mutated=false`.

For Phase 66, compile a future unattended apply reopen packet without applying it:

```bash
python3 -m py_compile scripts/workflow_future_unattended_reopen_packet.py
./scripts/run_tests.sh tests/scripts/test_workflow_future_unattended_reopen_packet.py
python3 scripts/workflow_future_unattended_reopen_packet.py --write-report --json
```

Expected readback: `FUTURE_UNATTENDED_REOPEN_PACKET_READY`, default `A_NO_REOPEN_KEEP_MANUAL_ONLY`, `selected_option=null`, `packet_only=true`, `reopen_apply_enabled=false`, `unattended_dispatch_enabled=false`, and `external_side_effects_executed=false`.

For Phase 67, record the single implementation-point reopen choice using the safe default unless the user explicitly opens a competing scheme:

```bash
python3 -m py_compile scripts/workflow_single_point_reopen_choice.py
./scripts/run_tests.sh tests/scripts/test_workflow_single_point_reopen_choice.py
python3 scripts/workflow_single_point_reopen_choice.py --choice A_NO_REOPEN_KEEP_MANUAL_ONLY --write-report --json
```

Expected readback: `SINGLE_POINT_REOPEN_CHOICE_RECORDED`, `choice=A_NO_REOPEN_KEEP_MANUAL_ONLY`, `record_only=true`, `reopen_apply_enabled=false`, `unattended_dispatch_enabled=false`, and `message_sent=false`.

For Phase 68, build the read-only governance archive/index:

```bash
python3 -m py_compile scripts/workflow_manual_only_governance_archive.py
./scripts/run_tests.sh tests/scripts/test_workflow_manual_only_governance_archive.py
python3 scripts/workflow_manual_only_governance_archive.py --write-report --json
```

Expected readback: `MANUAL_ONLY_GOVERNANCE_ARCHIVE_READY`, `archive_policy=read_only_index_closed_ladder`, indexed key phase artifacts present, `read_only=true`, `reopen_apply_enabled=false`, `unattended_dispatch_enabled=false`, and `external_side_effects_executed=false`.

For Phase 69, generate a read-only periodic closure health report:

```bash
python3 -m py_compile scripts/workflow_periodic_closure_health_report.py
./scripts/run_tests.sh tests/scripts/test_workflow_periodic_closure_health_report.py
python3 scripts/workflow_periodic_closure_health_report.py --write-report --json
```

Expected readback: `PERIODIC_CLOSURE_HEALTH_REPORT_CLEAR`, `health=clear`, `stage_report_only=true`, `read_only=true`, `unattended_dispatch_enabled=false`, and `external_side_effects_executed=false`.

For Phase 70, create a packet-only archive publication gate:

```bash
python3 -m py_compile scripts/workflow_archive_publication_packet.py
./scripts/run_tests.sh tests/scripts/test_workflow_archive_publication_packet.py
python3 scripts/workflow_archive_publication_packet.py --write-report --json
```

Expected readback: `ARCHIVE_PUBLICATION_PACKET_READY`, default `A_KEEP_PRIVATE_NO_PUBLICATION`, `packet_only=true`, `publication_apply_enabled=false`, `external_publication_enabled=false`, and `external_side_effects_executed=false`.

For Phase 71, run a private archive retention/drift watch:

```bash
python3 -m py_compile scripts/workflow_private_archive_retention_watch.py
./scripts/run_tests.sh tests/scripts/test_workflow_private_archive_retention_watch.py
python3 scripts/workflow_private_archive_retention_watch.py --write-report --json
```

Expected readback: `PRIVATE_ARCHIVE_RETENTION_WATCH_CLEAR`, `retention_policy=private_archive_retained_no_publication`, `drift=[]`, `read_only=true`, `publication_apply_enabled=false`, and `external_side_effects_executed=false`.

For Phase 72, define the exact-target publication apply gate without applying it:

```bash
python3 -m py_compile scripts/workflow_publication_exact_target_gate.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_exact_target_gate.py
python3 scripts/workflow_publication_exact_target_gate.py --write-report --json
```

Expected readback: `PUBLICATION_EXACT_TARGET_GATE_READY`, `gate_only=true`, `selected_target=null`, `publication_apply_enabled=false`, `external_publication_enabled=false`, and `external_side_effects_executed=false`.

For Phase 73, compile an exact-target apply dry-run preview without selecting a target or publishing:

```bash
python3 -m py_compile scripts/workflow_exact_target_apply_dry_run_compiler.py
./scripts/run_tests.sh tests/scripts/test_workflow_exact_target_apply_dry_run_compiler.py
python3 scripts/workflow_exact_target_apply_dry_run_compiler.py --write-report --json
```

Expected readback: `EXACT_TARGET_APPLY_DRY_RUN_COMPILER_READY`, `dry_run_only=true`, `would_publish=false`, `publication_apply_enabled=false`, and `external_side_effects_executed=false`.

For Phase 74, create the publication apply authorization packet fail-closed:

```bash
python3 -m py_compile scripts/workflow_publication_apply_authorization_packet.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_apply_authorization_packet.py
python3 scripts/workflow_publication_apply_authorization_packet.py --write-report --json
```

Expected readback: `PUBLICATION_APPLY_AUTHORIZATION_PACKET_READY`, default `A_KEEP_PRIVATE_NO_PUBLICATION`, `selected_option=null`, `packet_only=true`, `publication_apply_enabled=false`, and `external_publication_enabled=false`.

For Phase 75, compile a private/local export artifact manifest without publishing:

```bash
python3 -m py_compile scripts/workflow_private_export_artifact_compiler.py
./scripts/run_tests.sh tests/scripts/test_workflow_private_export_artifact_compiler.py
python3 scripts/workflow_private_export_artifact_compiler.py --write-report --json
```

Expected readback: `PRIVATE_EXPORT_ARTIFACT_COMPILER_READY`, `visibility=private_local_only`, `private_export_ready=true`, `publication_apply_enabled=false`, and `external_publication_enabled=false`.

For Phase 76, record the safe-default implementation choice without applying it:

```bash
python3 -m py_compile scripts/workflow_publication_apply_implementation_choice.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_apply_implementation_choice.py
python3 scripts/workflow_publication_apply_implementation_choice.py --choice A_KEEP_PRIVATE_NO_APPLY --write-report --json
```

Expected readback: `PUBLICATION_APPLY_IMPLEMENTATION_CHOICE_RECORDED`, `choice=A_KEEP_PRIVATE_NO_APPLY`, `record_only=true`, `exact_target_present=false`, `publication_apply_enabled=false`, and `external_publication_enabled=false`.

For Phase 77, run a read-only private export retention/drift watch:

```bash
python3 -m py_compile scripts/workflow_private_export_retention_watch.py
./scripts/run_tests.sh tests/scripts/test_workflow_private_export_retention_watch.py
python3 scripts/workflow_private_export_retention_watch.py --write-report --json
```

Expected readback: `PRIVATE_EXPORT_RETENTION_WATCH_CLEAR`, `drift=[]`, `read_only=true`, `publication_apply_enabled=false`, and `external_publication_enabled=false`.

For Phase 78, compile a packet-only publication apply reopen design:

```bash
python3 -m py_compile scripts/workflow_publication_apply_reopen_packet.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_apply_reopen_packet.py
python3 scripts/workflow_publication_apply_reopen_packet.py --write-report --json
```

Expected readback: `PUBLICATION_APPLY_REOPEN_PACKET_READY`, default `A_NO_REOPEN_KEEP_PRIVATE`, `selected_option=null`, `packet_only=true`, `reopen_apply_enabled=false`, and `publication_apply_enabled=false`.

For Phase 79, generate a read-only publication closure health report:

```bash
python3 -m py_compile scripts/workflow_publication_closure_health_report.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_closure_health_report.py
python3 scripts/workflow_publication_closure_health_report.py --write-report --json
```

Expected readback: `PUBLICATION_CLOSURE_HEALTH_REPORT_CLEAR`, `health=clear`, `unhealthy_checks=[]`, `read_only=true`, `publication_apply_enabled=false`, and `external_publication_enabled=false`.

For Phase 80, update the read-only publication governance archive/index:

```bash
python3 -m py_compile scripts/workflow_publication_governance_archive_update.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_governance_archive_update.py
python3 scripts/workflow_publication_governance_archive_update.py --write-report --json
```

Expected readback: `PUBLICATION_GOVERNANCE_ARCHIVE_READY`, `archive_policy=read_only_publication_governance_index`, `item_count=6`, `read_only=true`, and `publication_apply_enabled=false`.

For Phase 81, run a read-only publication archive retention/drift watch:

```bash
python3 -m py_compile scripts/workflow_publication_archive_retention_watch.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_archive_retention_watch.py
python3 scripts/workflow_publication_archive_retention_watch.py --write-report --json
```

Expected readback: `PUBLICATION_ARCHIVE_RETENTION_WATCH_CLEAR`, `drift=[]`, `read_only=true`, `retention_policy=publication_archive_retained_read_only_no_apply`, and `publication_apply_enabled=false`.

For Phase 82, compile a packet-only publication export review packet:

```bash
python3 -m py_compile scripts/workflow_publication_export_review_packet.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_export_review_packet.py
python3 scripts/workflow_publication_export_review_packet.py --write-report --json
```

Expected readback: `PUBLICATION_EXPORT_REVIEW_PACKET_READY`, default `A_REVIEW_PRIVATE_ARCHIVE_ONLY`, `selected_option=null`, `packet_only=true`, `export_apply_enabled=false`, and `publication_apply_enabled=false`.

For Phase 83, run a read-only retention/drift watch over the export review packet:

```bash
python3 -m py_compile scripts/workflow_publication_export_review_retention_watch.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_export_review_retention_watch.py
python3 scripts/workflow_publication_export_review_retention_watch.py --write-report --json
```

Expected readback: `PUBLICATION_EXPORT_REVIEW_RETENTION_WATCH_CLEAR`, `drift=[]`, `packet_only=true`, `export_apply_enabled=false`, and `publication_apply_enabled=false`.

For Phase 84, compile the final fail-closed publication apply boundary packet:

```bash
python3 -m py_compile scripts/workflow_publication_apply_final_boundary_packet.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_apply_final_boundary_packet.py
python3 scripts/workflow_publication_apply_final_boundary_packet.py --write-report --json
```

Expected readback: `PUBLICATION_APPLY_FINAL_BOUNDARY_PACKET_READY`, default `A_STOP_AT_PRIVATE_REVIEW`, `selected_option=null`, `packet_only=true`, `final_boundary=true`, and `publication_apply_enabled=false`.

For Phase 85, run a read-only retention/drift watch over the final boundary packet:

```bash
python3 -m py_compile scripts/workflow_publication_final_boundary_retention_watch.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_final_boundary_retention_watch.py
python3 scripts/workflow_publication_final_boundary_retention_watch.py --write-report --json
```

Expected readback: `PUBLICATION_FINAL_BOUNDARY_RETENTION_WATCH_CLEAR`, `drift=[]`, `read_only=true`, `packet_only=true`, and `publication_apply_enabled=false`.

For Phase 86, compile a read-only governance closure summary:

```bash
python3 -m py_compile scripts/workflow_publication_governance_closure_summary.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_governance_closure_summary.py
python3 scripts/workflow_publication_governance_closure_summary.py --write-report --json
```

Expected readback: `PUBLICATION_GOVERNANCE_CLOSURE_SUMMARY_READY`, `summary_policy=read_only_publication_governance_closed_no_apply`, `item_count=6`, `read_only=true`, and `publication_apply_enabled=false`.

For Phase 87, run a read-only retention/drift watch over the governance closure summary:

```bash
python3 -m py_compile scripts/workflow_publication_closure_retention_watch.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_closure_retention_watch.py
python3 scripts/workflow_publication_closure_retention_watch.py --write-report --json
```

Expected readback: `PUBLICATION_CLOSURE_RETENTION_WATCH_CLEAR`, `drift=[]`, `read_only=true`, and `publication_apply_enabled=false`.

For Phase 88, compile a packet-only publication apply reopen human gate:

```bash
python3 -m py_compile scripts/workflow_publication_apply_reopen_human_gate_packet.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_apply_reopen_human_gate_packet.py
python3 scripts/workflow_publication_apply_reopen_human_gate_packet.py --write-report --json
```

Expected readback: `PUBLICATION_APPLY_REOPEN_HUMAN_GATE_PACKET_READY`, default `A_KEEP_CLOSED_NO_REOPEN`, `selected_option=null`, `packet_only=true`, `human_gate_required_for_apply=true`, and `publication_apply_enabled=false`.

For Phase 89, run a read-only retention/drift watch over the reopen human gate packet:

```bash
python3 -m py_compile scripts/workflow_publication_human_gate_retention_watch.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_human_gate_retention_watch.py
python3 scripts/workflow_publication_human_gate_retention_watch.py --write-report --json
```

Expected readback: `PUBLICATION_HUMAN_GATE_RETENTION_WATCH_CLEAR`, `drift=[]`, `packet_only=true`, and `publication_apply_enabled=false`.

For Phase 90, compile the read-only publication governance final index:

```bash
python3 -m py_compile scripts/workflow_publication_governance_final_index.py
./scripts/run_tests.sh tests/scripts/test_workflow_publication_governance_final_index.py
python3 scripts/workflow_publication_governance_final_index.py --write-report --json
```

Expected readback: `PUBLICATION_GOVERNANCE_FINAL_INDEX_READY`, `index_policy=read_only_final_index_closed_no_apply`, `item_count=8`, `read_only=true`, and `publication_apply_enabled=false`.

Closeout pitfall: if a long turn stops after verification but before commit, resume with scoped status checks, rerun the focused validation slice, commit the child repo first, then commit the parent repo pointer/runner/skill. Keep ignored runtime rollback backups on disk unless the intended durable policy explicitly says to commit them; commit `cron/jobs.json` only when the phase intentionally mutates scheduler state.

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
