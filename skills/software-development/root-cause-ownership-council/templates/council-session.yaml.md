# Council Session Template

```yaml
root_cause_ownership_council:
  version: "1.0.0"
  session_id: ""
  problem: ""
  requested_by: ""
  trigger_reason:
    - repeated_fix
    - multi_controller
    - high_risk_shared_runtime
    - user_requested_root_cause
  scope:
    in_scope: []
    out_of_scope: []
  non_goals: []
  red_lines: []
  roles_run:
    - name: Framing Lead
      status: pending|done|skipped
  source_packet:
    verified: []
    uncertain: []
    missing: []
  ownership_table:
    - variable: ""
      current_controllers: []
      correct_owner: ""
      readers: []
      forbidden_writers: []
      cleanup_path: []
      verification: []
  evidence_ledger:
    - claim: ""
      evidence_quality: A|B|C|D
      evidence: []
      falsifier: ""
      decision: accept|reject|defer|needs_probe
  dissent:
    - participant: ""
      objection: ""
      resolution: accepted|rejected|split|deferred
  minimal_solution_boundary:
    files_to_change: []
    files_not_to_change: []
    controllers_to_remove_or_narrow: []
    tests_to_add_or_update: []
  regression_matrix:
    broken_paths: []
    contrast_paths: []
    negative_cases: []
    commands_or_harness: []
  final_verdict:
    status: PASS|BLOCK|DEGRADED_PASS|DEFER
    fresh_evidence: []
    residual_risk: []
    not_verified: []
```
