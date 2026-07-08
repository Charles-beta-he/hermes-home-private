# Development Trigger Packet Template

```yaml
development_trigger_packet:
  version: "1.2.0"
  task: ""
  surface:
    frontend: false
    backend: false
    fullstack: false
    ui_ux: false
    release: false
  signals:
    deterministic_low_risk: false
    repeated_fix: false
    multi_controller_shared_state: false
    failing_test: false
    screenshot_acceptance: false
    api_contract_change: false
    db_migration_change: false
    permission_security_change: false
    async_retry_or_side_effect: false
    performance_sensitive: false
    issue_or_pr_closeout: false
  recommended_route: direct_fix|specialist_review|ownership_audit|lightweight_council|full_council|release_certification
  specialist_roles: []
  required_evidence: []
  forbidden_actions:
    - "Do not push/merge/deploy from this packet alone."
  escalation_condition: []
```
