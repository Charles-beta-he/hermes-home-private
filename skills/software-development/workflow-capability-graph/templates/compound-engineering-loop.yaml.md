# Compound Engineering Loop Template

Use this as a local, copyable task/plan footer when applying the Compound Engineering absorption pattern.

```yaml
compound_engineering_loop:
  source_scope:
    source_refs:
      - url_or_doc: ""
        evidence_level: user_provided|opened_directly|not_available
    target_landing_zone: project_doc|skill_reference|test|taskpool|advisory_only
    side_effect_boundary: read_only|local_write|external_write_requires_gate

  prior_context_intake:
    read:
      - ref: ""
        relevance: ""
    not_read_reason: ""

  objective_plan:
    goal: ""
    success_criteria: []
    constraints: []
    non_goals: []
    red_lines: []
    chosen_path: ""
    verification_plan: []

  work_slice:
    vertical_outcome: ""
    artifacts_to_change_or_create: []
    rollback_or_escape: ""

  verification_evidence:
    commands_or_observables:
      - command_or_check: ""
        expected_signal: ""
        actual_result: ""
    evidence_refs: []
    claims_not_proven: []

  review_matrix:
    regression: pass|warn|fail|not_applicable
    architecture: pass|warn|fail|not_applicable
    simplicity: pass|warn|fail|not_applicable
    domain_red_lines: pass|warn|fail|not_applicable
    evidence: pass|warn|fail
    security: pass|warn|fail|not_applicable
    ui: pass|warn|fail|not_applicable
    verdict: pass|pass_with_warnings|fix_required|blocked

  compound_writeback:
    candidates:
      - lesson: ""
        landing: project_doc|skill|test|taskpool_followup|experience_atom|reject
        evidence_ref: ""
        reason: ""
    next_loop_hook: ""

  closure:
    status: done|advisory_only|blocked|partial
    residual_risks: []
    next_safe_action: ""
```
