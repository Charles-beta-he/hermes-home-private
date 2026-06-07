# Hermes Spec-Stateful SDD Control Plane SSOT

Date: 2026-06-07
Scope: Hermes Agent long-term evolution protocol for complex software/product/workflow tasks.
Status: accepted by user for full autonomous advancement until a human-intervention gate is reached.

## Problem

Hermes currently has strong tools, skills, memory, taskpool, diagnostics, subagents, and multi-model workflows, but the execution surface can still degrade into chat-local planning, implicit specs, model self-reporting, and scattered durable writes. Long-running or high-risk tasks need a stable control-plane protocol that preserves intent, state, gates, evidence, and learning boundaries.

## Desired State

Hermes evolves from a chat-first agent into a spec-stateful, event-driven, evidence-gated human/AI engineering control plane.

The stable formula is:

Spec + Event + Gate + Evidence + Ratchet = Stable Evolution

## Core Architecture

### 1. Spec Layer

Canonical task facts live in specs, not chat prose alone.

Objects:
- RequirementSpec
- DesignSpec
- TaskSpec
- VerificationSpec
- AcceptanceSpec
- DecisionRecord

Minimum fields:
- goal
- non_goals
- invariants
- acceptance_criteria
- constraints
- mock_policy
- risk_class
- evidence_requirements
- open_questions
- decision_log
- version/diff when changed

Rule: implementation cannot silently rewrite the spec. If reality invalidates the spec, produce a spec patch or decision record.

### 2. SDD Execution Layer

SDD means Spec-Anchored Subagent-Driven Development.

Rules:
- Main agent compiles the spec and task graph.
- Subagents receive complete task packets, not vague plan references.
- Independent tasks may run in parallel; shared-file or dependency tasks run serially.
- Every nontrivial task needs spec-compliance review before quality review.
- Subagent self-report is not proof; main agent must verify key artifacts.

### 3. Interactive Gate Layer

Human interaction is risk-gated, not step-by-step permission polling.

Gate classes:
- G0 Intake Gate: missing project, goal, constraints, or acceptance criteria.
- G1 Spec Gate: large/ambiguous/high-impact task needs canonical spec.
- G2 Architecture Fork Gate: material tradeoff changes long-term design.
- G3 Destructive Gate: deleting fields, features, data, schemas, permissions, or irreversible state.
- G4 External Side-Effect Gate: push, deploy, send message, close external task, production API/config writes.
- G5 Acceptance Gate: real UI/API/user acceptance is required before closure.

Default policy:
- low-risk read/analyze/verify: auto proceed;
- local reversible work: proceed with audit trail;
- recoverable medium risk: proceed if user gave full-advance authorization, otherwise summarize route;
- destructive/irreversible/external high risk: ask human;
- acceptance-required work: stop at waiting_acceptance until real acceptance exists.

### 4. Evidence Layer

Completion requires evidence bound to claims.

Evidence classes:
- CommandEvidence
- DiffEvidence
- TestEvidence
- BrowserEvidence
- APIEvidence
- LogEvidence
- HumanAcceptance
- KnownLimitation

Rules:
- "Subagent says done" is not evidence.
- "Multi-model agrees" is not truth.
- "Mock passed" is not final acceptance unless explicitly scoped to a mock-only prototype.
- Evidence must state which claim it supports and what it does not prove.

### 5. Knowledge/Ratchet Layer

Durable learning must land in the right surface.

Landing zones:
- memory: compact durable user/environment facts only;
- project profile: project-specific stable facts and red lines;
- skill: reusable procedure with triggers, steps, pitfalls, verification;
- taskpool: executable future work/state;
- experience atom: candidate lesson with applicability, anti-conditions, evidence, falsifier;
- docs/private or ADR: long-form rationale/review packets;
- session_search: historical progress recall, not current-state memory.

Rules:
- No WIP/session progress in memory.
- No project-specific fact in global skill unless stripped to a transferable pattern.
- No multi-model result promoted without source/evidence and falsifier.

## State Machine

request_received -> context_resolved -> spec_compiled -> risk_classified -> gate_decision -> plan_generated -> dispatch_ready -> executing -> spec_review -> quality_review -> evidence_verification -> waiting_acceptance|done|blocked -> learn_or_discard

Closure states:
- done: all acceptance criteria met and evidence is attached;
- waiting_acceptance: build/proof exists but real human/online acceptance is still required;
- blocked: prerequisite or human decision is required;
- rolled_back: action reverted with evidence;
- superseded: spec/task replaced by newer decision.

## Multi-Model Governance

Use multi-model only as expert signal, not proof.

Separate ledgers:
- source/evidence ledger;
- model opinion/dissent ledger;
- engineering verification ledger;
- final arbitration.

Approval requires evidence coverage and unresolved dissent handling, not majority vote alone.

## Event-Driven Runtime Direction

Taskpool should be the long-running SSOT. Chat, gateway, cron, and hooks are entrypoints/triggers.

Preferred events:
- task.created
- spec.updated
- dependency_met
- evidence_uploaded
- review_failed
- user_approved
- acceptance_required
- task_closed

Cron is allowed for watchdog, reconciliation, and low-frequency summaries, but should not be the primary task execution strategy when an event can trigger the work.

## Initial Implementation Decisions

1. Land a reusable `spec-stateful-sdd-workflow` skill.
2. Use this SSOT as the canonical rationale for the skill and future taskpool/profile/runtime changes.
3. Treat runtime/core changes beyond skill/docs/diagnostic cleanup as separate high-risk implementation tasks requiring focused specs and tests.
4. Fix safe health issues that are already diagnosed and reversible, especially log bloat.
5. Do not delete existing skills/memories broadly in this pass; do only low-risk compression or proposal generation unless a human approves aggressive pruning.

## Anti-Conditions

Do not apply the full protocol to trivial single-answer requests, simple calculations, or short read-only lookups. Use lighter variants.

Do not force every task through subagents; use subagents when isolation, parallelism, or independent review materially improves quality.

Do not block recoverable local work just because the protocol exists; gate strength follows risk.

## Falsifiers

This protocol should be narrowed if:
- it increases simple-task latency without reducing failures;
- evidence gates become formal checklists disconnected from acceptance criteria;
- users repeatedly reject gate interruptions as unnecessary;
- task recovery is not improved versus normal chat-local planning;
- skill/memory entropy increases instead of decreasing.

## Metrics

Short-term:
- complex-task spec coverage >80%;
- completion evidence coverage 100%;
- mock-only acceptance 0 for production tasks;
- Hermes health warnings reduced;
- memory usage below 85% when safely compressible.

Mid-term:
- event-triggered task execution >60%;
- stale memory <10%;
- continuation/task recovery >90%;
- multi-model claims have evidence/falsifier links.

Long-term:
- event-triggered execution >80%;
- high-risk changes evidence coverage 100%;
- task recovery >95%;
- repeated user feedback of "not really done" trends toward 0.
