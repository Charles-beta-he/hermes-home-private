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
  → Runtime Executor Integration
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
./scripts/run_tests.sh tests/scripts/test_workflow_contract_validator.py \
  tests/scripts/test_workflow_projection.py \
  tests/scripts/test_acceptance_compiler.py \
  tests/scripts/test_workflow_executor_stub.py \
  tests/scripts/test_workflow_taskpool_import_dry_run.py \
  tests/scripts/test_workflow_taskpool_import_write.py
```

Expected invariants:

```text
runtime_enabled=false
write_through_enabled=false
external_side_effects_enabled=false
taskpool_claim_enabled=false until taskpool import/integration is explicitly authorized
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