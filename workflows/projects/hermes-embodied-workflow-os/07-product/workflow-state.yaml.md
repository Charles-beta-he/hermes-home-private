---
project: hermes-embodied-workflow-os
updated_at: 2026-07-02T19:42:00+08:00
current_stage: p1_p2_validated_and_p3_projection_fixtures_validated
completion_boundary: local_contract_replay_and_projection_fixtures_no_runtime_side_effects
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
    evidence: implementation/tests + unittest 20 tests OK
  p2_replay_harness:
    status: accepted
    artifact: implementation/hewos_core/ledger.py
    evidence: implementation/tests/test_evidence_replay.py + unittest 20 tests OK
  p3_web_workbench_spec:
    status: accepted
    artifact: 07-product/prd-p3-web-workbench.md + 01-architecture/web-workbench-boundary.md
    evidence: committed in 735fe130
  p3_projection_fixtures:
    status: accepted
    artifact: implementation/hewos_core/projections.py
    evidence: implementation/tests/test_workbench_projections.py + unittest 20 tests OK
human_intervention_gate:
  reason: next material boundary is actual Web runtime/UI implementation or any real adapter/hardware/taskpool/deploy/auth path
  safe_next_options:
    - implement local non-server Workbench fixture CLI/HTML artifact only
    - start actual Web UI runtime after separate implementation gate
    - stop here with P3 projection fixtures
---
