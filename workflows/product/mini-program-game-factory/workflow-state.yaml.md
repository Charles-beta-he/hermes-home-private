---
schema: product_workflow_state_v1
slug: mini-program-game-factory
title: 小程序游戏批量研发工厂
chain: full-lifecycle
current_stage: discovery
status: blocked
created_at: 2026-07-26T12:44:35Z
updated_at: 2026-07-27T04:30:15Z
authority_boundary: local-artifacts-only
highest_evidenced_state: creator_project_candidate_materialized
---

# Workflow State: 小程序游戏批量研发工厂

## Stage Ledger

- stage: intake
  status: accepted
  artifact: 00-intake/intent-card.md
  evidence: spec-packet.md

- stage: discovery
  status: local_contract_certified_waiting_direct_evidence
  artifact: 01-discovery/hot-game-observatory.md
  evidence: evidence/hot-game-receipt-2026-07-26.json, evidence/market-loop-receipt-2026-07-26.json
  closure: recent_market_lead
  loop_gate: accepted 0 / rejected 2; may_freeze_kernel false; may_compile_work_package false
  verification: reviewed commit 0747403e84e6bf98b4683f2b8901c166ee804357 / tree 7dd6e9a6ea82b538f084d7d6a56fb51ac23b6f02; immutable-archive 68/68 tests; two independent APPROVE reviews with no material findings; certificate evidence/h4-local-verification-certificate.json
  blocker: no 7-day locally digest-verified and human-classified direct rank/gameplay captures; no two current subject-bound independent lineages

- stage: reference-ad-experiment
  status: candidate_lane_local_only
  artifact: 07-build/reference_ad_experiment.py, experiments/stack-path-runner/
  evidence: evidence/ad-tests/2026-07-30-douyin-7665976730670091561/
  closure: reference_ad_experiment_candidate
  boundary: user-supplied reference ad with immutable local digest; verified_current_hot=false and rank_claimed=false enforced; outputs cannot satisfy the verified-current-hot market-to-kernel gate and open no kernel freeze, Cocos build, platform, submission or publish authority
  verification: RED→GREEN unittest + Node kernel tests recorded in evidence/ad-tests/2026-07-30-douyin-7665976730670091561/red-green-evidence.md; browser slice is a local original candidate only, not Cocos/Douyin runtime evidence

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

- stage: gameplay-architecture-profile
  status: local_contract_candidate
  artifact: gameplay-architecture-profiles.json, 07-build/gameplay_architecture_profiles.py
  closure: architecture_profile_bound
  boundary: one canonical primary simulation profile selected by time/space/state/resolution/authority topology; shared shell and presentation fields cannot own or override gameplay semantics; registry does not implement seven runtimes or prove fun/production readiness
  verification: RED missing-module failure followed by 52/52 focused profile/compiler/batch/adapter tests; full local regression 169 Python + 17 runtime-core + 15 stack-path-runner PASS; producer exact/approved field inventories, nested scalar/object/list and finite-number semantics, WorkPackage and integration-packet canonical replay, symlink-ancestor rejection, and hostile-input negatives PASS; deterministic generated artifact byte parity PASS; exact commit/tree independent review remains the certification gate for this local candidate slice

- stage: risk
  status: accepted
  artifact: 05-risk/risk-register.md
  evidence: model-routing.json

- stage: planning
  status: accepted
  artifact: 06-planning/research-development-flow.md
  evidence: tasks/task-candidates.json

- stage: build
  status: local_runtime_project_and_platform_adapter_candidates_verified_build_preflight_blocked
  artifact: 07-build/gameplay_architecture_profiles.py, 07-build/work_package_compiler.py, 07-build/cocos_work_package_adapter.py, 07-build/cocos_project_generator.py, 07-build/cocos_delivery_gate.py, runtime/cocos/runtime-core/
  evidence: evidence/cocos-sample-candidate/candidate-manifest.json, evidence/cocos-node-runtime-smoke.json, evidence/cocos-creator-project-candidate/project-manifest.json, evidence/cocos-build-preflight-blocked.json, evidence/cocos-creator-cli-source.json
  closure: creator_project_candidate_materialized + official_platform_adapter_contract_tested
  certification: local candidate slice; prior local-contract certificate does not cover these files and cannot be inherited by the architecture-profile changes
  node runtime: fixed-seed GameplayKernel smoke passed; LocalPlatformStub reports official_sdk=false and grants no reward
  platform adapters: wx/tt adapters are local contract-tested with fake SDKs, strict runtime SDK shape checks, one-time login-code semantics and reward completion checks; official SDK E2E not executed
  Creator project: deterministic 19-file import candidate verified, including the official adapter candidate source; Creator import/build not executed
  build preflight: blocked with no command because Creator CLI/version, AppID, editor-exported config and build authority are absent
  authority: local candidate materialization and verification only; official SDK runtime, build, DevTools, credentials, device preview, submission and publish remain false

- stage: shipping
  status: blocked_at_creator_devtools_device_and_external_authority
  artifact: 08-shipping/shipping-packet.md, 08-shipping/devtools-handoff-template.json
  blocker: no Creator import/build receipt, no official platform SDK E2E/runtime receipt, no DevTools/device receipt, no human playtest
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
4. Install or identify an exact Cocos Creator 3.8 version and read back its callable CLI without entering platform credentials.
5. Import the digest-bound project candidate, export the real platform build config and provide the platform AppID through the human/third-party boundary.
6. Re-run build preflight; only an exact grant may invoke the emitted Creator command, followed by Creator artifact digest readback.
7. Only after build, DevTools and device receipts converge request exact authority for platform sandbox/submission.
