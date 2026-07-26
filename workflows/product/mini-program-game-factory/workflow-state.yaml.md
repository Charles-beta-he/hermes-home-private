---
schema: product_workflow_state_v1
slug: mini-program-game-factory
title: 小程序游戏批量研发工厂
chain: full-lifecycle
current_stage: discovery
status: blocked
created_at: 2026-07-26T12:44:35Z
updated_at: 2026-07-26T16:16:49Z
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
  status: local_gate_verified_waiting_direct_evidence
  artifact: 01-discovery/hot-game-observatory.md
  evidence: evidence/hot-game-receipt-2026-07-26.json, evidence/market-loop-receipt-2026-07-26.json
  closure: recent_market_lead
  loop_gate: accepted 0 / rejected 2; may_freeze_kernel false; may_compile_work_package false
  verification: 54/54 tests; stale exact-commit review reconciled; source freshness, discovery-only quorum, receipt binding, state inventory and mechanic-field parity verified
  blocker: no 7-day locally digest-verified direct rank and gameplay captures; no two current subject-bound independent lineages

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
  artifact: 07-build/work_package_compiler.py, 07-build/direct_capture_intake.py, 07-build/hot_game_observatory.py, 07-build/market_loop_gate.py
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

1. Capture a fresh Douyin mini-game hot/grossing chart and direct gameplay samples; re-run M0 receipt.
2. Re-run `market_loop_gate.py`; only `verified_current_hot` observations may admit an abstract `kernel_hypothesis` candidate.
3. For an admitted candidate, complete differentiation review, kernel specification, offline rule simulation and golden/negative cases before any freeze request.
4. R1 one-level playable runtime slice and human playtest acceptance.
5. Read-only official platform contract research.
6. Only then request exact authority for platform sandbox/submission.
