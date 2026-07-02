---
project: hermes-embodied-workflow-os
updated_at: 2026-07-02T19:34:00+08:00
current_stage: p1_p2_validated_and_p3_workbench_specified
completion_boundary: local_contract_replay_and_p3_spec_no_runtime_side_effects
states:
  p0_project_memory:
    status: accepted
    artifact: 00-model/embodied-workflow-os-ssot.md
    evidence: progress-ledger.md
  competitor_best_practices:
    status: accepted
    artifact: 02-research/competitor-and-best-practice-evaluation.md
    evidence: 02-research/competitor-source-samples-20260702.json
  p1_contract_core:
    status: accepted
    artifact: implementation/hewos_core
    evidence: implementation/tests + unittest 17 tests OK
  p2_replay_harness:
    status: accepted
    artifact: implementation/hewos_core/ledger.py
    evidence: implementation/tests/test_evidence_replay.py + unittest 17 tests OK
  p3_web_workbench_spec:
    status: accepted
    artifact: 07-product/prd-p3-web-workbench.md + 01-architecture/web-workbench-boundary.md
    evidence: spec readback required before commit
  latest_commit:
    status: accepted
    commit: c5538566 feat: add embodied workflow contract core
human_intervention_gate:
  reason: next material boundary is P3 implementation or any real adapter/hardware/taskpool/deploy path
  safe_next_options:
    - implement P3 projection fixtures and tests only
    - repair old unrelated portfolio warnings separately
    - stop here with P3 spec-only slice
---
