---
schema: product_workflow_state_v1
slug: mini-program-game-factory
title: 小程序游戏批量研发工厂
chain: full-lifecycle
current_stage: shipping
status: blocked
created_at: 2026-07-26T12:44:35Z
updated_at: 2026-07-26T12:50:01Z
authority_boundary: local-artifacts-only
highest_evidenced_state: local_contract_verified
---

# Workflow State: 小程序游戏批量研发工厂

## Stage Ledger

- stage: intake
  status: accepted
  artifact: 00-intake/intent-card.md
  evidence: spec-packet.md

- stage: discovery
  status: accepted
  artifact: 01-discovery/opportunity-analysis.md
  evidence: evidence/evidence-bundle.json

- stage: strategy
  status: accepted
  artifact: 02-strategy/strategy-canvas.md
  evidence: spec-packet.md

- stage: metrics
  status: accepted
  artifact: 03-metrics/metrics-contract.md
  evidence: evidence/converge-matrix.md

- stage: prd
  status: accepted
  artifact: 04-prd/game-product-contract.md
  evidence: capability-graph.json

- stage: risk
  status: accepted
  artifact: 05-risk/risk-register.md
  evidence: model-routing.json

- stage: planning
  status: accepted
  artifact: 06-planning/research-development-flow.md
  evidence: tasks/task-candidates.json

- stage: build
  status: accepted
  artifact: 07-build/work_package_compiler.py
  evidence: 07-build/implementation-evidence.md
  closure: local_contract_verified

- stage: shipping
  status: blocked
  artifact: 08-shipping/shipping-packet.md
  blocker: no playable runtime, no current official platform contract, no human playtest
  authority: no platform submission or publish

- stage: launch
  status: not_started
  blocker: external side effect requires exact target, account, rollback and readback

- stage: measure
  status: not_started
  blocker: no launched product or real telemetry

## Next Safe Dependency Order

1. R0 pure gameplay rule simulator and golden cases.
2. R1 one-level playable runtime slice.
3. Human playtest acceptance.
4. Read-only official platform contract research.
5. Only then request exact authority for platform sandbox/submission.
