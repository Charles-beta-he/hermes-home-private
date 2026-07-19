---
name: spec-stateful-sdd-workflow
description: "Use when a complex task needs spec-stateful SDD: canonical specs, subagent execution, interaction gates, evidence gates, acceptance closure, and governed learning writeback."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [specs, sdd, workflow, evidence, gates, subagent, governance]
    related_skills: [writing-plans, subagent-driven-development, qian-meta-synthesis, abstraction-governance, hermes-experience-ratchet]
---

# Spec-Stateful SDD Workflow

## Overview

Use this workflow to turn complex work into a recoverable, auditable, evidence-backed control-plane run. It combines spec-driven correctness, subagent-driven execution, interactive risk gates, evidence-gated closure, and governed learning writeback.

Core formula:

```text
Spec + Event + Gate + Evidence + Ratchet = Stable Evolution
```

Applicability: complex software, product, research-to-engineering, workflow, or Hermes-control-plane tasks where correctness depends on preserving requirements, state, risk decisions, and proof across multiple steps.

Anti-condition: do not force the full protocol onto trivial Q&A, simple read-only lookups, or explicitly mock-only prototypes.

Falsifier: narrow this workflow if it increases simple-task latency without reducing failures, or if evidence gates become disconnected from acceptance criteria.

## When to Use

Use when:

- The task spans multiple files, repos, systems, or sessions.
- Requirements are ambiguous, evolving, or high-impact.
- The task may need subagents, multi-model review, browser/API verification, or acceptance gates.
- The user asks for full autonomous advancement until human intervention is needed.
- A task must survive context compression, interruption, or later recovery.
- A completion claim would be unsafe without real tool evidence.

Don't use the full protocol for:

- trivial Q&A, small read-only lookups, or simple one-command checks;
- mock-only prototypes explicitly scoped as non-production;
- tasks where a direct tool call plus short answer is enough.

Use a lighter variant for medium tasks: mini-spec + risk gate + evidence note.

## Operating Modes

| Mode | Trigger | Required artifacts |
|---|---|---|
| Lite | Small reversible task | goal, action, evidence |
| Standard | Multi-step local task | spec, task list, verification |
| Full | Cross-system/high-risk/long-running task | spec packet, gates, evidence bundle, acceptance state |
| Certification | Multi-model or high-risk closure | evidence ledger, dissent ledger, truth gate, final arbitration |

## Stage 0 — Resolve Context

Before acting, resolve:

- active project/repo/profile;
- relevant skills and project rules;
- current git/worktree state when editing code;
- previous session/taskpool state if the user refers to prior work;
- whether the request has external side effects.

If context is missing but retrievable, use tools. Ask only when ambiguity changes the action or risk class.

## Stage 1 — Compile the Spec Packet

For Standard/Full mode, make the spec explicit before implementation.

Minimum packet:

```yaml
spec_packet:
  goal: "..."
  non_goals: []
  invariants: []
  constraints: []
  acceptance_criteria: []
  mock_policy: "real-verification-required|mock-allowed-for-unit-only|mock-only-prototype"
  risk_class: "read_only|local_reversible|local_destructive|external_side_effect|production_sensitive|irreversible"
  evidence_requirements: []
  open_questions: []
  decision_log: []
```

Rules:

1. Implementation cannot silently rewrite the spec.
2. If reality invalidates the spec, create a spec patch or decision record.
3. Specs belong in a recoverable file for long-running work; chat alone is not SSOT.
4. Do not encode project-specific facts as global rules unless stripped to a transferable pattern.

## Stage 2 — Risk-Classify and Apply Interaction Gates

Human interaction is risk-gated, not step-by-step permission polling.

| Gate | Trigger | Default action |
|---|---|---|
| G0 Intake | project/goal/acceptance cannot be resolved | ask focused question |
| G1 Spec | large or ambiguous task | compile spec, proceed if authorized |
| G2 Architecture Fork | major route tradeoff | present options + recommendation |
| G3 Destructive | delete/overwrite/schema/permission/data loss | require human confirmation |
| G4 External Side Effect | push/deploy/send/close external task/prod write | require confirmation unless explicitly authorized |
| G5 Acceptance | real UI/API/human acceptance needed | stop at `waiting_acceptance` |

Policy:

- Read-only and analysis tasks proceed automatically.
- Local reversible work proceeds with audit trail.
- Recoverable medium-risk work may proceed under full-advance authorization.
- Destructive, irreversible, credential/permission/production-sensitive actions stop for human confirmation.
- Do not block recoverable work with over-hard UX; make the escape/confirmation path explicit.

## Stage 3 — Plan Tasks

Break work into bite-sized verifiable tasks.

Each task packet should include:

```yaml
task_packet:
  id: "T1"
  objective: "..."
  files: []
  dependencies: []
  exact_steps: []
  verification_commands: []
  expected_evidence: []
  risk_class: "..."
  rollback_note: "..."
```

Use `writing-plans` for detailed implementation plans. Use `planning-with-files` when the task may span context compression.

## Stage 4 — Dispatch SDD Execution

SDD here means Spec-Anchored Subagent-Driven Development.

Rules:

1. Main agent owns the spec, gates, and final arbitration.
2. Subagents receive complete task packets, not vague references to a plan file.
3. Independent tasks may run in parallel; tasks touching the same files or dependent state run serially.
4. Each significant task gets two-stage review: spec compliance first, code/quality/security review second.
5. A subagent's self-report is not proof. Verify changed files, commands, or external handles in the main session.

## Stage 5 — Evidence Gate

When implementation depends on an uncertain mechanism rather than a settled requirement, use `scientific-inquiry-evidence-update` before intervention. Store competing hypotheses, discriminating predictions, probe validity threats, evidence updates, and remaining alternatives in or beside the spec packet; do not let an implementation plan silently become proof of the mechanism.

Every completion claim needs evidence bound to claims.

Evidence classes:

- CommandEvidence: command + exit code + relevant output.
- DiffEvidence: changed files/diff/stat.
- TestEvidence: focused/full test output.
- BrowserEvidence: screenshot, browser harness, real UI path.
- APIEvidence: real request/response or integration result.
- LogEvidence: runtime log proving behavior.
- HumanAcceptance: user or external approval.
- KnownLimitation: what remains unproven.

Never treat these as sufficient alone:

- "subagent says done";
- "multi-model agrees";
- "mock passed" for production acceptance;
- "no error appeared";
- screenshots that do not prove data correctness.

Evidence must say which claim it supports and what it does not prove.

## Stage 6 — Closure State

Choose an explicit closure state:

| State | Meaning |
|---|---|
| done | acceptance criteria met with evidence |
| waiting_acceptance | build/proof exists but human/online acceptance remains |
| blocked | prerequisite or human decision required |
| rolled_back | action reverted with evidence |
| superseded | replaced by newer spec/decision |

For work requiring real online UI/API/human acceptance, code/build/proof is not enough to close; stop at `waiting_acceptance`.

## Stage 7 — Learning Writeback

After completion, choose the correct landing zone.

| Learning shape | Landing zone |
|---|---|
| temporary progress | session/task file only |
| stable user preference | memory/user profile |
| project-specific fact | project profile or repo docs |
| reusable procedure | skill |
| candidate lesson needing challenge | experience-ratchet atom/proposal |
| mandatory safety rule | runtime gate/hook/taskpool policy |
| architectural decision | ADR/docs/private |
| executable future work | taskpool |

Rules:

- Do not write WIP/session progress to memory.
- Prefer patching existing skills before creating new narrow skills.
- Multi-model consensus is expert signal until grounded by evidence and falsifiers.
- Add anti-conditions and falsifiers to generalized lessons.

## Multi-Model Variant

When multi-model analysis is used, keep three ledgers separate:

```yaml
multi_model_ledgers:
  source_evidence:
    verified: []
    uncertain: []
    missing: []
  model_dissent:
    - participant: "..."
      claim: "..."
      objection: "..."
      confidence: 0.0
  engineering_verification:
    - artifact: "path_or_command"
      result: "PASS|FAIL|WARN"
  arbitration:
    decision: "accept|amend|split|escalate_to_human"
```

Do not collapse dissent into fake consensus. If truth is needed, every material factual claim needs evidence coverage.

## Event-Driven Runtime Direction

For long-running operationalization, taskpool should be the SSOT. Chat, gateway, cron, and hooks are entrypoints/triggers.

Preferred events:

- `task.created`
- `spec.updated`
- `dependency_met`
- `evidence_uploaded`
- `review_failed`
- `user_approved`
- `acceptance_required`
- `task_closed`

Cron is for watchdogs, reconciliation, and low-frequency summaries. If a cron job behaves like a poller for available work, consider an event-driven trigger or taskpool hook instead.

## Quick Checklist

Before execution:

- [ ] Context/project/profile resolved.
- [ ] Spec packet exists or task is intentionally Lite mode.
- [ ] Risk class assigned.
- [ ] Human gates checked.
- [ ] Task packets include verification/evidence.

During execution:

- [ ] Shared-file tasks are serialized.
- [ ] Subagents receive complete context.
- [ ] Spec compliance review happens before quality review.
- [ ] Main session verifies subagent claims.

Before closure:

- [ ] Evidence supports each acceptance claim.
- [ ] Mock-only proof is not treated as production acceptance.
- [ ] Closure state is explicit.
- [ ] Learning writeback uses the right landing zone.

## Common Pitfalls

1. Treating the plan as the spec. Plans describe execution; specs define correctness.
2. Letting subagents infer missing requirements from context they do not have.
3. Asking the user at every step instead of only at meaningful gates.
4. Skipping human confirmation for destructive or external side-effect actions under broad full-advance authorization.
5. Treating multi-model agreement as evidence.
6. Closing a task with code/build proof when real UI/API/human acceptance remains.
7. Saving active progress or stale task state to memory.
8. Creating new skills for every incident instead of patching existing reusable workflows.
9. Making evidence formal but not claim-linked.
10. Using cron polling as the default runtime when event-driven triggers are available.

## Verification Checklist

- [ ] The chosen operating mode matches task complexity and risk.
- [ ] Spec, gates, evidence, and closure state are visible in the final report.
- [ ] Any durable writeback was scoped, evidence-backed, and landed in the right surface.
- [ ] Any generated files or skills were read back or validated.
- [ ] Any high-risk action stopped at the appropriate human-intervention gate.
- [ ] For Hermes self-governance work, distinguish governed durable artifacts from runtime/recovery artifacts before committing.

## References

- `references/hermes-self-governance-scoped-commit.md` — session-derived pattern for scoped commits after Hermes self-governance runs: commit SSOT/skill/memory artifacts, leave logs/backups/runtime state uncommitted unless explicitly requested.
