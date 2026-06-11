# Unified Execution Flow Framework

Scope: Hermes self-architecture, workflow orchestration, taskpool lifecycle, and harness engineering.
Applicability: use when merging agent execution, workflow stages, task lifecycle, and verification harnesses into one governed execution flow.
Anti-condition: do not use this pattern to create a second task store, bypass human authority gates, or treat proof tooling as done authority.

## Decision

The unified framework is a layered execution flow over the existing taskpool ledger:

```text
Taskpool owns truth.
Workflow owns order.
Hermes owns action.
Harness owns proof.
Verifier owns closeout authority.
Human gate owns permission.
```

Any new runner, workflow graph, harness, mission controller, or adapter must project into this chain instead of becoming a competing source of truth.

## Objective

A task should move through a durable, auditable chain:

```text
Intent -> Task Contract -> Taskpool Ledger -> Workflow Stage -> Gate -> Hermes Runner -> Harness Proof -> Verifier -> Review/Done or Human Gate
```

Hard constraints:

- No competing taskpool or workflow-owned lifecycle state.
- No direct `done` from an executor, harness, model review, or scheduled tick.
- No destructive, publishing, credential, payment, production, or external write-back side effect without an authority gate.
- No mock evidence as acceptance unless explicitly allowed.
- No plan-only closeout for implementation-class work.
- Preserve existing taskpool status, claim, lease, retry, proof, and lifecycle gates.

## Layer contracts

### Task Contract

Canonical fields a task should expose or derive:

```yaml
objective: string
acceptance_criteria: [string]
red_lines: [string]
source_of_truth: [doc|prototype|repo|api|runtime|user]
priority_layer: P0|P1|P2|P3
lane: work|evolution|advisory
project: string|null
requires_multimodel: bool
external_side_effects: [string]
workflow_stage: intake|evidence|plan|execute|verify|review|writeback|human_gate|done
harness_spec: object|null
human_gate_packet: object|null
rollback_plan: object|null
```

The taskpool record remains durable. Workflow and harness outputs are projections or evidence attached to it.

### Workflow Stage

Workflow is a stage machine, not a task store:

- `intake`: normalize source, de-duplicate, classify priority/lane/project.
- `evidence`: collect facts and source-of-truth observations.
- `plan`: choose path, dependency order, rollback, and harness requirements.
- `execute`: bounded implementation or runner action after claim.
- `verify`: run harness and collect artifacts.
- `review`: compare proof to acceptance and red lines.
- `writeback`: prepare/execute authorized external side effects with read-back.
- `human_gate`: wait for smallest required permission/choice while continuing safe work.
- `done`: only after closeout gate passes.

### Gate Evaluator

Every stage transition should answer:

```yaml
allowed_to_continue: bool
boundary_class: none|permission|evidence|external_side_effect|destructive|credential|value_judgement|safety_legal
safe_actions: [string]
blocked_actions: [string]
required_confirmation: string|null
verification_required: [string]
rollback_required: bool
```

Boundary rule: a boundary is not stop-work. Realign to the initial objective, continue safe read-only/local/reversible/harness-preparation work, and emit a compact intervention packet for the smallest gated action.

### Hermes Runner

Hermes is the action layer:

- file/code edits;
- terminal/build/test/API probes;
- browser or desktop walkthrough;
- delegated workers or agent teams;
- scheduled or mission-triggered dispatch;
- adapter intent generation.

Runner output must be structured proof or a classified blocker, not a lifecycle decision.

### Harness Engineering

Harness is the proof layer. It derives `HarnessSpec`, executes `HarnessRun`, and normalizes an `EvidenceBundle`.

Example `HarnessSpec`:

```yaml
harness_spec:
  required: true
  surfaces: [ui, api]
  environment:
    frontend: local|deployed|none
    backend: real|local|none
  browser:
    route: string|null
    viewport: desktop|mobile|mobile_short|null
    target_anchor: string|null
  disallow:
    - mock_api_acceptance
    - synthetic_fixture_acceptance
  required_artifacts:
    - command_output
    - screenshot
    - console_log
    - network_observation
    - api_readback
  pass_condition:
    - build_pass
    - no_blocking_console_error
    - target_surface_visible
    - acceptance_fields_verified
    - backend_contract_readback_pass
```

Harness evidence levels must be explicit:

- unit/store/service tests: logic only;
- build/lint: compile/regression guard;
- browser/Playwright: selected user surface proof;
- real backend/API read-back: contract or business proof;
- visual screenshot: visual state proof, not full semantic proof;
- multimodel review: advisory/certification, not runtime proof.

### Evidence Bundle

Taskpool evidence should use structured, durable prefixes:

```yaml
evidence:
  - command:build PASS
  - command:test PASS
  - artifact:/absolute/path/to/report.md
  - artifact:/absolute/path/to/screenshot.png
  - proof:browser route=<route> viewport=<viewport> backend=<backend> console_errors=0
  - proof:api_readback endpoint=<endpoint> status=200 fields=<fields>
  - classification:boundary_class=permission
```

Do not invent evidence. If proof is blocked, record `blocked` with exact reason and safe work completed.

### Verifier / Closeout Gate

The verifier decides whether evidence satisfies the task contract. It is separate from the harness and runner.

Done requires:

- acceptance criteria checked;
- red lines preserved;
- feature-specific implementation artifact exists;
- feature-specific verification artifact exists;
- unresolved human gates absent;
- external write-back read-back passed when writeback is in scope;
- multimodel certification passed when required.

Advisory pass, model consensus, generic compile checks, proof hashes, or generic selfcheck are insufficient for product/work done by themselves.

## Event flow

```text
task.created/task.updated
  -> normalize_contract
  -> derive_workflow_stage
  -> derive_harness_spec
  -> gate_evaluate
  -> claim_or_human_gate
  -> runner_execute
  -> harness_run
  -> evidence_normalize
  -> verifier_closeout
  -> taskpool_transition
  -> authorized_writeback_readback
```

Events should wake the flow. Scheduled jobs are watchdog/maintenance fallback, not the primary executor.

## Production dry-run surface

The current production-safe entrypoint is:

```bash
python3 ~/.hermes/scripts/execution_flow_evaluator.py --limit 5 --json
python3 ~/.hermes/scripts/execution_flow_evaluator.py --task-file <task.md> --json --fail-on-blocked
python3 ~/.hermes/scripts/execution_flow_evaluator.py --task-file <task.md> --report /tmp/unified-flow-report.md
```

Contract:

- read-only: no task transition, external writeback, publish, delete, credential, or production mutation;
- stable schema: `schema_version=execution-flow/v1`;
- enterprise gate: `PASS` only when no evaluated task has a boundary or missing evidence;
- exit code: `--fail-on-blocked` returns `2` when the enterprise gate is blocked;
- report: durable Markdown report includes contract, evaluations, and human-gate/intervention packets.

## MVP landing order

1. Define `ExecutionFlowState` / `HarnessSpec` as derived fields; no lifecycle mutation. **Landed as read-only evaluator.**
2. Build a read-only evaluator that prints next stage, safe actions, blocked actions, and missing evidence for existing tasks. **Landed: `~/.hermes/scripts/execution_flow_evaluator.py`.**
3. Normalize existing build/test/browser/API outputs into `EvidenceBundle` records. **Partially landed through structured evidence detection.**
4. Wire review closeout to require feature-specific harness evidence for work/UI/API tasks. **Dry-run gate landed; lifecycle mutation remains intentionally unopened.**
5. Add event-driven claim/handoff integration after dry-run proves no competing source of truth.
6. Add write-back executors one adapter at a time with digest-bound authorization and read-back.

## Anti-patterns

- Workflow owns status separate from taskpool.
- Harness marks tasks done.
- Runner directly mutates external systems after model approval only.
- Scheduled jobs synchronously run long workers and block the scheduler.
- Mock evidence is reported as product acceptance.
- Browser screenshot from wrong route/tab/filter is treated as valid proof.
- Historical proof debt blocks a safe current priority claim without checking if it is a live blocker.

## Verification checklist for implementations

- [ ] Existing taskpool remains the only state owner.
- [ ] The evaluator can run read-only against existing tasks.
- [ ] Stage decisions include safe actions and blocked actions.
- [ ] Harness artifacts are written to durable paths and referenced as structured evidence.
- [ ] Closeout gate rejects implementation-class tasks without feature-specific proof.
- [ ] Human gates include blast radius, rollback/escape hatch, and post-execution verification.
- [ ] Tests cover disabled/dry-run, boundary-blocked, harness-pass, harness-fail, and evidence-missing paths.
