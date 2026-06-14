# Self-Advancing Workflow Kernel

Use when multiple autonomous/self-advancing directions need to share one control-plane skeleton instead of each creating its own cron/state/task runner.

## Core decision

Treat self-advancement as a workflow control-plane pattern, not as a one-off agent loop.

Shared kernel:

```text
Signal -> Intake -> Classify -> Plan -> Dispatch -> Execute -> Prove -> Verify -> Close/Retry/Block/AskHuman -> Ratchet -> NextSignal
```

Hermes mapping:

- Signal: webhook, cron, taskpool event, mission flow signal, user seed.
- Intake: taskpool add, mission event, adapter fetch.
- Classify: lane, priority, project/profile, architecture target, boundary, depth.
- Plan: mission tick, workflow planner, multimodel triage.
- Dispatch: eligibility, claim, handoff, lease, parallel boundary.
- Execute: worker, delegate, script, external coding agent.
- Prove: command output, diff, test, screenshot, artifact, evidence note.
- Verify: proof-check, lifecycle gate, multimodel gate, project profile gate.
- Close: review, done, retry, blocked, archived.
- AskHuman: mission handoff / intervention packet.
- Ratchet: skill, project profile, ADR, memory landing-zone decision.

## Fact-source boundaries

Keep these separate:

- Mission owns objective truth: direction, budget, stage reports, open decisions.
- Taskpool owns task truth: concrete work, dependency, priority, lifecycle, dispatchability.
- Evidence ledger owns proof truth: artifacts and read-back verification.
- Workflow kernel owns progression rules, not facts.
- Dashboard/Control Tower owns projection only, never canonical state.

## Workflow pack pattern

Each self-advancing direction should register as a workflow pack/profile rather than implementing a private runner:

```yaml
workflow_id: memory-governance
objective: classify and repair memory/skill/project-profile landing zones
mission_id: optional
sources:
  - cron
  - taskpool_event
  - webhook
priority_policy: ...
allowed_actions:
  - local_read
  - local_patch
blocked_actions:
  - push
  - deploy
  - secrets_write
  - destructive_delete
  - external_send_without_gate
evidence_required:
  - before_after_diff
  - command_output
closeout_gates:
  - proof_check
  - lifecycle_gate
human_gate_triggers:
  - value_judgement
  - permission_escalation
  - irreversible_action
  - evidence_insufficient
projection:
  dashboard_panel: read_only
ratchet_policy:
  skill_patch: true
  memory_only_for_durable_user_or_env_fact: true
```

## What to solidify vs configure

Solidify in the kernel:

- state machine;
- event schema;
- task schema;
- evidence schema;
- human gate schema;
- runner contract;
- closeout contract;
- projection contract.

Configure per workflow pack:

- objective;
- source adapters;
- project/profile;
- priority policy;
- tool/model policy;
- allowed/blocked actions;
- evidence requirements;
- cadence/budget;
- dashboard projection.

Never hardcode a specific project, branch, URL, Lark task, provider incident, or temporary path into the kernel.

## Maturity model

1. Exploration: dynamic tasks, spikes, audits, frequent human decisions.
2. Convergence: recurring task types, known failures, fixed evidence shape.
3. Productized workflow: routine runs are automatic; only risk/value/permission gaps interrupt.

Stabilize the protocol and gates, not a one-off prompt or local incident.

## Pitfalls

- Do not create one cron/state file/runner per direction without registering it in a shared workflow registry.
- Do not let a dashboard write canonical state directly.
- Do not confuse Mission with taskpool: Mission says why; taskpool says what.
- Do not let self-evolution/advisory tasks starve P0/P1 project delivery; priority policy belongs in the pack and dispatcher.
- Do not treat `PASS_ADVISORY_ONLY`, `py_compile`, or mock-only checks as product delivery closeout authority.

## Verification checklist

- A new self-advancing direction has a workflow_id and policy, not only a cron.
- Its tasks land in the canonical taskpool or a declared adapter that projects into it.
- It has explicit evidence and closeout gates.
- It has human-gate triggers for side effects and value decisions.
- Its dashboard view is traceable back to Mission/taskpool/evidence, not a second fact source.
