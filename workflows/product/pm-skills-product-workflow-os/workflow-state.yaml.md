---
schema: product_workflow_state_v1
slug: pm-skills-product-workflow-os
title: PM Skills inspired Hermes Product Workflow OS
chain: full-lifecycle
current_stage: intake
status: in_progress
created_at: 2026-06-11T05:45:01Z
updated_at: 2026-06-11T05:45:01Z
authority_boundary: local-artifacts-only
---

# Workflow State: PM Skills inspired Hermes Product Workflow OS

## Stage Ledger

- stage: intake
  status: in_progress
  artifact: intent-card.md
  evidence: evidence/evidence-bundle.json
  gate: objective/non-goals/success/authority boundary explicit
  next: discovery

- stage: discovery
  status: not_started
  artifact: 01-discovery/opportunity-analysis.md
  evidence: evidence/evidence-bundle.json
  gate: user/problem hypothesis and risky assumptions exist
  next: evidence

- stage: evidence
  status: not_started
  artifact: evidence/evidence-bundle.json
  gate: facts vs assumptions vs interpretation separated
  next: strategy

- stage: strategy
  status: not_started
  artifact: 02-strategy/strategy-canvas.md
  gate: segment/alternatives/differentiation/stop condition explicit
  next: metrics

- stage: metrics
  status: not_started
  artifact: 03-metrics/metrics-contract.md
  gate: metric readback path or instrumentation gap labeled
  next: prd

- stage: prd
  status: not_started
  artifact: 04-prd/prd.md
  gate: observable acceptance criteria
  next: risk

- stage: risk
  status: not_started
  artifact: 05-risk/risk-register.md
  gate: high-risk items have detection and mitigation
  next: planning

- stage: planning
  status: not_started
  artifact: 06-planning/stories-and-tests.md
  gate: task candidates include evidence and anti-drift checks
  next: build

- stage: build
  status: not_started
  artifact: 07-build/implementation-evidence.md
  gate: real tests/build/API/browser evidence or explicit blocker
  next: shipping

- stage: shipping
  status: not_started
  artifact: 08-shipping/shipping-packet.md
  gate: security/performance/test gaps fixed, blocked, or accepted
  next: launch

- stage: launch
  status: not_started
  artifact: 09-launch/launch-plan.md
  gate: launch state and smoke/readback path explicit
  next: measure

- stage: measure
  status: not_started
  artifact: 10-measure/measure-retro.md
  gate: decision and learning writeback boundary explicit
  next: ratchet

## Decision Log

Append decisions in `decisions.md` with: date, decision, evidence, rejected alternatives, next state.
