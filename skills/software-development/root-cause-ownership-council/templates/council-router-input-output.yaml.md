# Council Router Input/Output Template

```yaml
council_router_input:
  task: ""
  user_intent: debug|review|implement|certify|plan|absorb|unknown
  risk_signals:
    repeated_fix: false
    multi_controller_shared_state: false
    high_risk_domain: []
    failing_test: false
    evidence_gap: false
    model_disagreement: false
    final_certification_needed: false
  artifacts:
    files: []
    tests: []
    diffs: []
    logs: []
    screenshots: []
    api_readbacks: []
  constraints:
    non_goals: []
    red_lines: []
    authority: read_only|local_write_allowed|external_write_requires_gate

council_router_output:
  invoke: false
  reason: ""
  mode: none|micro|lightweight_3_role|full_9_role|domain_specialist_only|final_certifier_only
  roles: []
  gates: []
  linked_files_to_load: []
  forbidden_actions:
    - "No push/deploy/external dispatch from router decision alone."
  next_step: ""
```
