# Modular workflow kernel landing pattern

Use when advancing Hermes/Agent Builder self-evolution from architecture discussion into governed implementation, especially for modular workflow kernels, Agent/Workflow Pack runtime, model routing, acceptance compilation, or executor integration.

## Core landing ladder

Advance in this order and stop at each authority boundary:

```text
Contract Seed
  → Model Registry / Route Alias Seed
  → Route Trace Schema
  → Run Lockfile Schema
  → Read-only Projection
  → Frozen Acceptance Bundle
  → Local Reversible Executor Stub
  → Taskpool Import Dry-run
  → Taskpool Import Write
  → Candidate Consolidation Write
  → Runtime Integration Record-only
  → Runtime Claim Executor
  → Runtime Execution Worker
  → Runtime Module Executor
  → Review / Done Gate
  → Model Call Gate
  → Adapter Write-through
```

Do not jump from registry/spec directly into runtime execution. Each layer should produce a concrete artifact and focused tests before opening the next boundary.

## Artifact contract by layer

- **Contract seed**: workflow schema, workflow registry, model registry, validator, ADR, taskpool seed. Runtime/write-through/external side effects must remain false.
- **Route trace**: per-module model route alias, selected model id, fallback chain, routing policy version, checked constraints, eval gate, and `projection_only_no_model_call` marker.
- **Run lockfile**: frozen workflow version, registry versions, module versions, route trace ids, acceptance criteria, evidence policy, context digest, and fail-closed side-effect flags.
- **Read-only projection**: local artifact only; no task claim, no model call, no adapter write, no runtime mutation.
- **Frozen acceptance bundle**: criteria derived from lockfile/module contracts/model route traces/safety flags; `frozen=true`, `dry_run_only=true`; include a human-gate packet template for moving beyond dry-run.
- **Local reversible executor stub**: converts criteria into local preview steps only; set `taskpool_claim_enabled=false`, `model_call_enabled=false`, `adapter_write_enabled=false`, `external_side_effects_enabled=false`.
- **Taskpool import dry-run**: converts executor-preview steps into candidate task previews only; set `taskpool_write_enabled=false`, `taskpool_claim_enabled=false`, and keep all runtime/model/adapter/external side-effect flags false.
- **Taskpool import write**: writes selected candidates as canonical `status: proposed` task notes only, read-back verifies marker fields, refreshes derived taskpool views, and still keeps `taskpool_claim_enabled=false`, `runtime_enabled=false`, `model_call_enabled=false`, `adapter_write_enabled=false`, and `external_side_effects_enabled=false`.
- **Candidate consolidation write**: groups over-fragmented imported `proposed` candidates into fewer canonical `proposed` review tasks, preserves source candidate notes, read-back verifies group/source fields, and still keeps claim/runtime/model/adapter/external side-effect flags false.
- **Runtime integration record-only**: annotates selected consolidated `proposed` tasks with runtime packet metadata and prepared claim packets while keeping task status `proposed`, `taskpool_claim_enabled=false`, `model_call_enabled=false`, `adapter_write_enabled=false`, and `external_side_effects_enabled=false`.
- **Runtime claim executor**: consumes exactly one prepared claim packet for one non-human-gated consolidated task, moves that task from `proposed` to `claimed`, records `claimed_by=workflow_runtime_claim_executor`, and stops before `running`, `review`, `done`, model calls, adapter writes, or external side effects. Make the claim id deterministic so a max-iteration relay can replay/read back without double-claiming.
- **Runtime execution worker**: starts exactly one claimed, non-human-gated task with a local no-op runtime marker, moves it from `claimed` to `running`, records `workflow_runtime_execution_status=running_noop_started_not_reviewed`, and stops before `review`, `done`, model calls, adapter writes, or external side effects. Make the runtime execution id deterministic and treat an already-`running` task with the same id as idempotent readback, not failure.
- **Runtime module executor**: consumes exactly one running, non-human-gated task with `workflow_runtime_execution_status=running_noop_started_not_reviewed`, runs one bounded local deterministic module, writes a module execution packet, moves the task from `running` to `review`, records `workflow_module_execution_status=module_execution_review_ready`, and stops before `done`, model calls, adapter writes, or external side effects. The first safe module is `contract_acceptance_governance.local_validator.v1`, backed by `workflow_contract_validator` evidence.
- **Review / done gate**: consumes review-ready module execution evidence and may close only the exact local task after structured project-verification evidence, without opening model/adapter/external authority.
- **Model call gate**: separate authority boundary for invoking pinned/read-only model routes for one module. Keep adapter/external flags false and persist route trace, prompt digest, response artifact, and verification before lifecycle closeout.
- **Adapter write-through**: separate digest-bound boundary for mutating taskpool/Kanban/external adapters; never inherit authority merely because a module reached review.

## Authority boundaries

Treat these as separate human gates even under broad “全盘推进” authorization:

1. **Executor stub boundary** — moving from acceptance/projection to runnable local behavior.
2. **Taskpool import write boundary** — writing canonical taskpool/SSOT tasks.
3. **Runtime lifecycle boundary** — connecting executor output to taskpool claim/running/review/done transitions.
4. **Adapter write-through boundary** — mutating external systems or sending notifications.

The safe default after executor stub is `authorize_taskpool_import_dry_run`, not direct runtime integration.

## Validation pattern

For each layer, add focused tests and deterministic commands:

```bash
python3 scripts/workflow_contract_validator.py --json
python3 scripts/workflow_projection.py --json
python3 scripts/acceptance_compiler.py --json
python3 scripts/workflow_executor_stub.py --json
python3 scripts/workflow_taskpool_import_dry_run.py --json
python3 scripts/workflow_taskpool_import_write.py --json
python3 scripts/workflow_candidate_consolidation.py --json
python3 scripts/workflow_runtime_integration.py --json
python3 scripts/workflow_runtime_claim_executor.py --json
python3 scripts/workflow_runtime_execution_worker.py --json
python3 scripts/workflow_runtime_module_executor.py --json
python3 scripts/workflow_runtime_review_done_gate.py --json
python3 scripts/workflow_runtime_model_call_gate.py --json
python3 scripts/workflow_runtime_adapter_write_gate.py --json
./scripts/run_tests.sh tests/scripts/test_workflow_contract_validator.py \
  tests/scripts/test_workflow_projection.py \
  tests/scripts/test_acceptance_compiler.py \
  tests/scripts/test_workflow_executor_stub.py \
  tests/scripts/test_workflow_taskpool_import_dry_run.py \
  tests/scripts/test_workflow_taskpool_import_write.py \
  tests/scripts/test_workflow_candidate_consolidation.py \
  tests/scripts/test_workflow_runtime_integration.py \
  tests/scripts/test_workflow_runtime_claim_executor.py \
  tests/scripts/test_workflow_runtime_execution_worker.py \
  tests/scripts/test_workflow_runtime_module_executor.py \
  tests/scripts/test_workflow_runtime_review_done_gate.py \
  tests/scripts/test_workflow_runtime_model_call_gate.py \
  tests/scripts/test_workflow_runtime_adapter_write_gate.py
```

Expected invariants:

```text
runtime_enabled=false
write_through_enabled=false
external_side_effects_enabled=false
taskpool_claim_enabled=false until taskpool import/integration is explicitly authorized; true only for the one selected runtime claim executor task
model_call_enabled=false until real model routing/eval integration is explicitly authorized
adapter_write_enabled=false until adapter write-through is explicitly authorized
```

## Compatibility pitfall

If scripts may run under macOS/Xcode Python 3.9, avoid `datetime.UTC` and use:

```python
from datetime import datetime, timezone
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
```

This is a durable compatibility fix for small standalone scripts in Hermes repo workflows, not a claim about all Python environments.

## Reporting pattern

Each boundary should write a Mission stage report with:

- commits/artifact paths;
- validator/test command outputs;
- explicit false side-effect flags;
- next boundary and required human choice.

Avoid saying “done” for the whole architecture when the current layer is only contract/projection/acceptance/executor-preview.