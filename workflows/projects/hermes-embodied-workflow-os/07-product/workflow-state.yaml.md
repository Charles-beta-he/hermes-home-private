---
project: hermes-embodied-workflow-os
updated_at: 2026-07-02T19:50:00+08:00
current_stage: p1_p2_validated_and_p3_static_workbench_artifact_validated
completion_boundary: static_html_fixture_only_no_runtime_side_effects
states:
  p1_contract_core:
    status: accepted
    artifact: implementation/hewos_core
    evidence: unittest 22 tests OK
  p2_replay_harness:
    status: accepted
    artifact: implementation/hewos_core/ledger.py
    evidence: unittest 22 tests OK
  p3_web_workbench_spec:
    status: accepted
    artifact: 07-product/prd-p3-web-workbench.md + 01-architecture/web-workbench-boundary.md
    evidence: committed in 735fe130
  p3_projection_fixtures:
    status: accepted
    artifact: implementation/hewos_core/projections.py
    evidence: unittest 22 tests OK
  p3_static_workbench_artifact:
    status: accepted
    artifact: artifacts/workbench-static-fixture.html
    evidence: implementation/tests/test_workbench_static.py + unittest 22 tests OK
human_intervention_gate:
  reason: next boundary is real Web runtime/UI acceptance or any external/hardware/taskpool/deploy/auth integration
  safe_next_options:
    - stop here with static artifact
    - separately authorize real local Web runtime implementation
    - separately authorize taskpool ingestion
---
