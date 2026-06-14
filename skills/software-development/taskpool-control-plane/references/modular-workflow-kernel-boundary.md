# Modular Workflow Kernel boundary pattern

Use when a user asks to continue a self-advancing / Agent Builder / workflow-kernel implementation "until the scheme boundary".

## Durable pattern

Do not jump from a conceptual workflow-kernel design directly into runtime/taskpool execution. Land the control-plane layers in this order:

```text
contract seed
  → model registry / route aliases
  → route trace schema
  → run lockfile schema
  → read-only projection
  → frozen dry-run acceptance bundle
  → STOP before executor/runtime/taskpool write-through
```

The first five layers are safe local contract/projection work. The next layer after a frozen acceptance bundle is an executor boundary, even if the executor is local-only. That requires an explicit human gate.

## Minimal artifact set

- `schemas/workflow_contract.schema.json`
- `config/workflow_registry.json`
- `config/model_registry.json`
- `schemas/route_trace.schema.json`
- `schemas/run_lockfile.schema.json`
- `schemas/acceptance_bundle.schema.json`
- read-only validator script
- read-only projection compiler
- dry-run acceptance compiler
- focused tests for fail-closed flags, model route aliases, route trace/run lockfile schema presence, projection-only output, and frozen acceptance bundles
- ADRs documenting each boundary

## Required fail-closed flags

For contract/projection/dry-run phases these must remain false:

```text
runtime_enabled=false
write_through_enabled=false
external_side_effects_enabled=false
dynamic_routing_enabled=false
auto_promote_enabled=false
```

Model routing can be represented as route aliases and traces, but must be pinned by default. New model/provider aliases can be registered, shadowed, and evaluated; they must not auto-promote into production runs.

## Human gate packet for next phase

When the dry-run acceptance bundle exists, stop and offer choices:

```text
continue_dry_run_only
authorize_local_reversible_executor_stub
stop_and_review_architecture
```

Recommended default is `continue_dry_run_only` unless the user explicitly authorizes a local reversible executor stub.

## Pitfalls

- Do not treat a projection or acceptance bundle as task completion or runtime authority.
- Do not claim/handoff taskpool work from a workflow pack until executor integration is explicitly authorized.
- Do not call models from the route projection step; route traces can explain alias selection without invoking a provider.
- Do not let model/module output become canonical lifecycle state. Taskpool/Mission/Evidence/Profile remain the facts.
- Do not silently proceed from "全盘推进" into executor/write-through boundaries; full-landing authorization still stops at permission, side-effect, value-judgment, and runtime-boundary gates.

## Verification commands pattern

Use project-local equivalents of:

```bash
python3 scripts/workflow_contract_validator.py --json
python3 scripts/workflow_projection.py --json
python3 scripts/acceptance_compiler.py --json
./scripts/run_tests.sh tests/scripts/test_workflow_contract_validator.py tests/scripts/test_workflow_projection.py tests/scripts/test_acceptance_compiler.py
```

Completion evidence should include the validator PASS, projection boundary string, frozen acceptance bundle fields, test pass count, scoped commits, and mission/stage report if operating under a Mission ledger.
