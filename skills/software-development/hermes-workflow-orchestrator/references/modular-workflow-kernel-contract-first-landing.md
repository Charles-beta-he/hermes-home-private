# Modular Workflow Kernel Contract-First Landing

## Scope / Applicability / Anti-condition

Scope: Hermes workflow-orchestrator and taskpool/control-plane evolution work that introduces a reusable self-advancing workflow kernel, module registry, model-routing registry, acceptance compiler, or Agent/Workflow Pack system.

Applicability: use when the goal is to turn a high-level modular Agent Builder / Workflow Kernel architecture into the first safe implementation slice.

Anti-condition: do not use this pattern for ordinary product feature delivery, one-off agent prompts, external adapter write-through, production deploys, sender enablement, secret handling, or destructive cleanup. Those require their own project/profile authority and gates.

## Product boundary

Do not frame the base as only “deliverable agent products.” The same kernel can produce:

- Workflow Packs: reusable business process packages.
- Agent Packs: role/persona wrappers over workflow packs.
- Evidence Ledger / compliance layers.
- Model Router / model-governance layers.
- Acceptance Compiler / verifier packages.
- Execution Console / Control Tower projections.
- Enterprise delivery packages.
- Internal personal-assistant workflows.

Agent products are a packaging layer, not the only output.

## Contract-first rule

Start with a reversible contract seed pack, not live runtime mutation. Do **not** begin by changing the main runtime loop, gateway, taskpool transitions, external adapters, senders, or deployers.

The first safe slice should define:

1. Workflow contract schema.
2. Workflow registry with at least one disabled-by-default pack.
3. Model registry with abstract route aliases and pinned defaults.
4. Read-only validator.
5. Focused tests for fail-closed constraints.
6. ADR documenting fact-source boundaries and why runtime remains closed.
7. Taskpool seed doc for future governed implementation.

Default flags for the contract layer:

```yaml
runtime_enabled: false
write_through_enabled: false
external_side_effects_enabled: false
production_run_mode: pinned
dynamic_routing_enabled: false
shadow_routing_enabled: true
auto_promote_enabled: false
default_model_change_requires_human_approval: true
```

## Minimal first pack

Use a `decision_brief_pack` style workflow as the first pack because it validates the common kernel without dangerous external side effects:

- goal calibration
- evidence/source collection
- decision synthesis
- acceptance compilation
- evidence verification

Each module should declare capability, input/output schema, risk level, side-effect level, model policy, evidence requirements, and blocked actions.

## Model-routing boundary

First-stage “intelligent routing” is not autonomous production switching. It is a controlled registry + alias + trace contract:

- Modules reference route aliases such as `best.synthesis.decision_brief`, not concrete providers.
- Model registry entries declare status, capabilities, risk profile, eval result, and production controls.
- Route aliases require stable primary models and fallback models.
- Production runs default to pinned route plans.
- Dynamic routing starts as shadow/recommendation only.
- Auto-promotion and default model changes require human/release approval.

## Validator checks

A read-only validator should fail closed on:

- `runtime_enabled=true`
- `write_through_enabled=true`
- `external_side_effects_enabled=true`
- module side effects of `external_write` or `destructive`
- missing model policy fallback
- module route alias not registered in model registry
- acceptance not compile-before-execution or not freeze-before-execution
- incomplete human gate packet fields
- invalid evidence prefixes
- dynamic routing or auto-promote enabled in production controls
- route alias primary/fallback model not registered

## Verification commands

Use deterministic checks before opening later execution layers:

```bash
python3 scripts/workflow_contract_validator.py --json
./scripts/run_tests.sh tests/scripts/test_workflow_contract_validator.py
python3 -m py_compile scripts/workflow_contract_validator.py
```

Acceptable proof shape:

- validator `status=PASS`
- nonzero workflow/module/model/route-alias counts
- all runtime/write-through/external-side-effect flags false
- focused tests pass
- scoped diff is limited to contract/registry/validator/docs/tests

## Fact-source boundaries

- Mission ledger owns long-term objective, budget, stage report, and human decisions.
- Taskpool owns lifecycle state and dispatchability.
- Evidence ledger owns completion proof.
- Project/Profile/Agent/Workflow config owns scoped business rules and acceptance expectations.
- Dashboard/Control Tower are projections only.
- Models/workers can propose or produce evidence, but do not own `done` authority.

## Later phase gate

Only after the contract layer passes should later work add:

1. route-trace schema
2. run-lockfile schema
3. read-only dashboard projection
4. acceptance-compiler dry-run
5. local-only reversible executor
6. adapter-specific write-through with readback and rollback
7. external delivery authorization
