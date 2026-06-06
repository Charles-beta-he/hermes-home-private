# Hermes Self-Extension Control Plane SSOT

Status: accepted P0 SSOT
Updated: 2026-06-06
Scope: Hermes-local self-extension, taskpool, PUA case-to-capability, multi-model governance, evidence/promotion gates, and runtime/brain/evidence asset boundaries.

## Why this exists

Hermes self-extension must not be a pile of cron jobs, notes, model opinions, and ad-hoc script patches. The durable target is a production-grade control plane:

```text
observe event → scope work → execute safely → attach evidence → review/ratify → promote/reject → benchmark regression
```

This document is the canonical reference for future self-extension changes. Chat, cron jobs, taskpool prompts, skills, model packets, docs, and code diffs should reference this SSOT instead of copying parallel truths.

## Product-thinking method adopted from user reference

User supplied a Douyin reference by ShaneCodeStudio: "第一性原理 + 苏格拉底式提问 + 奥卡姆剃刀" for product/AI deep thinking.

Hermes adopts it as a self-extension design gate:

1. Socratic question chain: ask until the real failure mode is identified. Do not stop at symptoms like "cron failed"; ask what state failed to advance, what evidence was missing, and which boundary allowed ambiguity.
2. First-principles reduction: reduce each proposal to underlying invariants: evidence before promotion, event before execution, explicit permission before side effects, and no multi-model consensus without tool evidence.
3. Occam minimum executable plan: prefer the smallest verifiable work package that removes the bottleneck. Do not build a large framework when one SSOT + one verifier + one state transition test proves the next step.

This method is a design/review heuristic, not a truth source. It cannot override evidence gates or permission boundaries.

## Six abstraction layers

### L0 — Events

Events are state-change facts that trigger work. They do not contain business logic and do not claim success.

Required fields:

```text
event_id
event_type
subject_type
subject_id
source
causality_id
dedupe_key
lease_id
idempotency_window
expected_transition
evidence_refs
created_at
```

Canonical event types:

```text
proposal.created
proposal.scoped
proposal.accepted_for_taskpool
task.created
task.dispatchable
task.claimed
task.completed
evidence.attached
review.requested
review.passed
review.failed
promotion.requested
promotion.approved
promotion.rejected
dashboard.degraded
cron.error_detected
upstream.drift_detected
quota.low_confidence
human_ack.received
```

### L1 — Facts

Facts describe current world/project/runtime state. Examples: taskpool rows, envelope states, provider quota state, project profiles, dashboard active data, `confidence-db`, `results.tsv`.

Rules:

- Facts need source and freshness.
- Canonical runtime evolution facts live under `~/.hermes/state/evolution/`.
- Archived skill data is historical fallback and must be marked degraded if used as the only source.
- Project facts do not become global rules.

### L2 — Scenario rules

Scenario rules describe how to act for a class of tasks. Examples: skills, project profiles, workflow contracts, routing matrix, subbrain registry.

Rules:

- Rules are scoped to trigger classes.
- Task-local workflow contracts can override scenario rules.
- Cross-context promotion requires evidence and review.

### L3 — Mandatory gates

Mandatory gates block unsafe or unverifiable advancement.

Required gates:

```text
evidence_contract
truth_gate
permission_gate
quota_gate
duplicate_execution_gate
human_escape_gate
promotion_gate
rollback_gate
```

Non-negotiables:

- Multi-model agreement is not evidence.
- Promotion without evidence is forbidden.
- Failed `min_quorum` means degraded/not_certified, not success.
- High-risk side effects require explicit human approval.
- Watchdogs emit events and recovery signals; they do not bypass gates.

### L4 — ADRs

ADRs record durable architecture decisions such as event-driven migration, evidence-first promotion, multi-model role separation, and asset boundary policy.

### L5 — Meta rules

Meta rules define how L0-L4 may be changed. They must be abstract, stable, cross-context, and sparse. They do not encode project-specific facts.

## Event-driven migration target

Cron/tick is a fallback watchdog, not the main execution mechanism.

Target chain:

```text
proposal.created
  → proposal.scoped
  → task.created
  → task.dispatchable
  → task.claimed
  → worker.started
  → evidence.attached
  → review.requested
  → review.passed / review.failed
  → promotion.approved / promotion.rejected / parked
```

Allowed watchdog responsibilities:

- missed event detection
- stale lease recovery
- health check
- storage cleanup
- degraded source detection
- human escape reminder

Disallowed watchdog responsibilities:

- direct task completion
- promotion
- closing user work
- global rule mutation
- bypassing evidence or permission gates

## Proposal lifecycle

```text
proposed → scoped → accepted_for_taskpool → task_created → implementation_started → implementation_done → evidence_attached → review_requested → reviewed → promoted/rejected/parked
```

Promotion requires:

- evidence bundle with external/tool evidence
- deterministic verification where applicable
- independent review for control-plane changes
- rollback signal
- scope check excluding unrelated changes

## Permission matrix

### Auto-execute

Read-only scans, status summaries, local benchmark/test runs, dashboard refresh, stale claim release, proposal drafts, taskpool candidates, local evidence bundle creation.

### Auto-execute with evidence gate

Local script/skill/verifier patches and local commits. Requirements: scoped diff, tests, static scan, independent review for control-plane changes, no push by default.

### Human approval required

`git push`, external write APIs, global profile/meta-rule changes, permission/human_escape gate changes, provider/model primary config changes, destructive cleanup, automatic closure of user tasks, bulk taskpool state rewrites.

### Suggest only

Architecture-scale rewrites, deleting capabilities, lowering safety gates, treating degraded as success, treating multi-model consensus as truth, writing project facts into global memory.

## Multi-model governance

Roles:

- Claude: architecture, boundary, arbitration
- DeepSeek: engineering implementation and concrete failure risk
- GPT-5.5: codegen, implementation completeness, test design
- MiMo: AI/user-profile/self-extension perspective
- Gemini: wide-context cross-check

Semantics:

- T0: low-risk; single model plus deterministic checks may be enough.
- T1: medium-low; `min_quorum >= 2`.
- T2: self-extension/control-plane; `min_quorum >= 3`.
- T3: permission/global gate/meta-rule; `min_quorum >= 3` plus human approval.

If quorum fails: emit valid failure artifacts and mark degraded/not_certified. Do not promote.

If models agree but evidence is missing: mark unsupported_consensus/not_certified and generate evidence requests.

## Asset boundaries

### Live runtime

Paths: `~/.hermes/run/`, `~/.hermes/state/`.

Examples: leases, locks, worker jobs, scheduler state, quota cache, active evolution runtime state.

Policy: not git-managed; schema-versioned; GC/backup separately.

### Brain assets

Paths: `~/.hermes/brains/`, `~/.hermes/skills/`, `~/.hermes/docs/private/`, `~/.hermes/project-profiles/`.

Policy: git-managed with scoped commits and ratchet/post-update verification.

### Evidence artifacts

Paths: `~/.hermes/evidence/`, `~/.hermes/runs/`, taskpool proof/evidence paths.

Policy: retention/TTL with pinning for promotion evidence; cited by evidence refs.

### Ephemeral

Paths: `/tmp/hermes/`, `~/.hermes/tmp/`, `~/.hermes/cache/`.

Policy: GC; never a truth source; never git-managed.

## P0 acceptance criteria

- Dashboard active sources are canonical or active; archived fallback is explicitly degraded.
- Nightly evolution wrapper exits success for healthy no-change audits and records `no_state_change`, not cron error.
- Upstream ratchet wrapper skips non-reviewable work branches without cron error and writes a classified event.
- Critical cron errors for self-extension are classified, not silent.
- This SSOT exists and is referenced by future self-extension changes.

## Long-term stability metrics

```text
Agent Health V >= 0.90
V_dot >= 0 over 7 days
PUA readiness >= 85
critical_cron_error_count = 0
dashboard_degraded_source_count = 0
proposal_stuck_count decreases weekly
duplicate_execution_count = 0
promotion_without_evidence_count = 0
unsupported_consensus_promotions = 0
dirty_runtime_asset_leak_count = 0
ratchet review completes or emits classified skip/blocked artifact
```
