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

Scope: implementation-class task closeout inside the unified Hermes/workflow/taskpool/harness execution flow.
Applicability: use when a task is moving from `review` to `done` and the task contract implies work/UI/API/backend/command execution proof.
Anti-condition: do not apply this as a pre-execution dispatch blocker; missing proof should guide execution until the closeout boundary.

The verifier decides whether evidence satisfies the task contract. It is separate from the harness and runner.

Done requires:

- acceptance criteria checked;
- red lines preserved;
- feature-specific implementation artifact exists;
- feature-specific verification artifact exists;
- unresolved human gates absent;
- external write-back read-back passed when writeback is in scope;
- multimodel certification passed when required.

Unified execution-flow closeout rule:

- Missing harness evidence may allow `dispatch-dry-run` and execution, but must block `review -> done`.
- Work/surface/API tasks must provide structured command evidence plus surface-specific proof: browser/screenshot/Playwright proof for UI surfaces, and API/curl/read-back proof for API/backend surfaces.
- A blocked closeout must fail before mutating the task note; it should return a machine-readable failure such as `execution_flow_closeout_blocked:<missing_evidence>`.
- Closeout proof matching must trust only structured lifecycle evidence sources such as proposed `--evidence` and frontmatter `evidence`; arbitrary task body placeholders or acceptance examples that look like `proof:*` must not satisfy closeout.

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

The current production-safe entrypoints are:

```bash
# Dispatch planning now consumes the unified gate without mutating state.
python3 ~/.hermes/scripts/brain_task_orchestrator.py dispatch-dry-run --json

# Canonical taskpool-owned entrypoint (preferred)
python3 ~/.hermes/scripts/brain_task_orchestrator.py execution-flow-dry-run --limit 5 --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py execution-flow-dry-run --task <task-id> --json --fail-on-blocked
python3 ~/.hermes/scripts/brain_task_orchestrator.py execution-flow-dry-run --task <task-id> --report /tmp/unified-flow-report.md

# Lower-level evaluator entrypoint
python3 ~/.hermes/scripts/execution_flow_evaluator.py --limit 5 --json
python3 ~/.hermes/scripts/execution_flow_evaluator.py --task-file <task.md> --json --fail-on-blocked
python3 ~/.hermes/scripts/execution_flow_evaluator.py --task-file <task.md> --report /tmp/unified-flow-report.md
```

Contract:

- read-only: no task transition, external writeback, publish, delete, credential, or production mutation;
- stable schema: `schema_version=execution-flow/v1`;
- enterprise gate: `PASS` only when no evaluated task has a boundary or missing evidence;
- exit code: `--fail-on-blocked` returns `2` when the enterprise gate is blocked;
- report: durable Markdown report includes contract, evaluations, and human-gate/intervention packets;
- report path safety: report generation may write the explicitly requested report file, but must not create parent directories or mutate taskpool/external state as a side effect;
- summary consistency: any aggregate such as `blocked_or_missing_evidence` must count both explicit boundaries and missing evidence so it cannot disagree with `enterprise_gate.status`.

Dispatch consumption rule:

- `dispatch-dry-run` must include the task's `execution_flow` payload and an `execution_flow_dispatch_decision`.
- Missing harness evidence on `pending` / pre-closeout tasks is not a stop-work signal; it becomes execution/harness requirements and remains safe to dispatch.
- Hard boundaries (`permission`, `external_side_effect`, `destructive`, `credential`, `value_judgement`, `safety_legal`) and review/writeback/done/human-gate boundaries must block dispatch in dry-run rather than creating an execution prompt that could cross authority.
- When a dispatch is blocked by the execution-flow decision, the dry-run payload must suppress actionable `claim_command`, `execution_prompt`, and nested intervention plans; return only safe inspection/remediation actions plus the `execution_flow` evidence packet.
- Dispatch consumption is still read-only: it must not claim, transition, mark done, write adapters, or execute external side effects.

Pitfall: a "read-only" evaluator can accidentally stop being read-only through convenience filesystem behavior. `mkdir(parents=True)` for a report path is still a filesystem mutation beyond the requested artifact and should be rejected unless a separate write contract authorizes it.

## MVP landing order

1. Define `ExecutionFlowState` / `HarnessSpec` as derived fields; no lifecycle mutation. **Landed as read-only evaluator.**
2. Build a read-only evaluator that prints next stage, safe actions, blocked actions, and missing evidence for existing tasks. **Landed: `~/.hermes/scripts/execution_flow_evaluator.py`.**
3. Connect the evaluator to the taskpool-owned CLI surface. **Landed: `brain_task_orchestrator.py execution-flow-dry-run`; still read-only and uses canonical task ids/notes.**
4. Make `dispatch-dry-run` consume the execution-flow gate. **Landed: dispatch plans now include `execution_flow` and `execution_flow_dispatch_decision`; pre-closeout evidence gaps are safe-to-execute, while hard authority/writeback/destructive/human-gate boundaries block dispatch in dry-run.**
5. Normalize existing build/test/browser/API outputs into `EvidenceBundle` records. **Partially landed through structured evidence detection.**
6. Wire review closeout to require feature-specific harness evidence for work/UI/API tasks. **Landed: `review -> done` lifecycle gate now consumes execution-flow proof requirements and blocks work/UI/API closeout when browser/API/command proof is missing; safe dispatch remains allowed before closeout.**
7. Add event-driven claim/handoff integration after dry-run proves no competing source of truth. **Landed for `auto-claim-and-handoff`: actual claim/handoff now checks `execution_flow_dispatch_decision` before write guard and suppresses claim/handoff/proof writes on hard execution-flow boundaries.**
8. Route human confirmation through a scoped control-console approval projection. **Scope: local Hermes control console only. Applicability: execution-flow human/writeback/done/hard-boundary requests that need a human choice. Anti-condition: this is not an external adapter executor and does not grant publish/send/delete/deploy authority. Landed: snapshot projects those requests into `snapshot.approvalRequests`, and the Human Inbox routes choices through existing capability-gated decision/apply/dispatch/worker surfaces.**
9. Add write-back executors one adapter at a time with digest-bound authorization and read-back.

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
