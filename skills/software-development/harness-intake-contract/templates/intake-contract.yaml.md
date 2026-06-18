# Harness Intake Contract Template

Use this template when a task needs to become executable by an AI worker and verifiable by a separate validator.

```yaml
source:
  origin: "user | social_video | lark_task | github_issue | taskpool | mission | other"
  source_url_or_id: ""
  captured_evidence: []

map:
  project_purpose: ""
  state_source: "project profile | AGENTS.md | repo docs | taskpool record | mission ledger | user context"
  repo_or_surface: ""
  key_files_or_objects: []
  existing_conventions: []
  forbidden_changes: []

goal:
  user_intent: ""
  desired_state: ""
  non_goals: []
  constraints: []
  assumptions: []

acceptance:
  observable_results: []
  required_commands: []
  required_artifacts: []
  screenshots_or_logs: []
  precision_rules: []
  regression_boundaries: []

division:
  executor_role: "implementer | researcher | operator | reviewer-only"
  validator_role: ""
  subagents: []
  conflict_groups: []
  ownership_boundary: ""

evidence:
  proof_schema: "freeform | PROOF_JSON | command/log/screenshot/file/readback"
  evidence_refs: []
  minimum_done_proof: []
  readback_required: true

gates:
  risk_level: "low | medium | high"
  human_gate_required: false
  human_gate_reason: ""
  side_effects_allowed: []
  dry_run_first: true
  rollback_or_escape: ""
```

## Confirmer JSON shape

```json
{
  "understood": true,
  "missing_map_fields": [],
  "missing_acceptance_fields": [],
  "contract": {},
  "executor_prompt": "",
  "validator_prompt": "",
  "risk_level": "low",
  "human_gate_required": false,
  "human_gate_reason": ""
}
```

## Minimum done rule

Do not advance to executor if any of these are empty for non-trivial work:

- `goal.desired_state`
- `acceptance.observable_results`
- `evidence.minimum_done_proof`
- `gates.risk_level`

Do not advance to done if proof evidence is only an executor summary and no command/file/log/screenshot/readback evidence exists.
