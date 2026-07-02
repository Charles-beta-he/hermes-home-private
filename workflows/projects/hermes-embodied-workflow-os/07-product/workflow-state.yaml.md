---
project: hermes-embodied-workflow-os
updated_at: 2026-07-02T20:52:00+08:00
current_stage: p1_p2_validated_p3_runtime_smoke_and_best_practice_gates_codified
completion_boundary: local_contract_process_docs_tests_no_external_or_hardware_side_effects
states:
  p1_contract_core:
    status: accepted
    artifact: implementation/hewos_core
  p2_replay_harness:
    status: accepted
    artifact: implementation/hewos_core/ledger.py
  p3_local_web_runtime:
    status: accepted_smoke_verified
    artifact: implementation/hewos_core/workbench_runtime.py
  best_practice_gate_ladder:
    status: accepted_local_contract
    artifacts:
      - implementation/hewos_core/best_practice_gates.py
      - implementation/tests/test_best_practice_gates.py
      - 01-architecture/best-practice-gates-and-process.md
    contract:
      - GatePacket requires evidence/readback/rollback/idempotency/explicit forbidden high-risk actions
      - ProcessPhase requires sequential previous receipt
      - AuthorityLadder blocks phase skips and high-risk side-effect requests
next_safe_phase:
  phase: ui_quality_audit
  allowed: local UI improvements, browser smoke, console readback, screenshot readback, audit report
  forbidden: taskpool_write, external_dispatch, hardware_or_robot_execution, deploy_or_push, auth_or_credentials, execute_endpoint
---
