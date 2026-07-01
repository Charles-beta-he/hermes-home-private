# Spec Gate + Converge Template

Use this template when a task is complex enough that a direct patch could satisfy the visible symptom while violating the real requirement.

## 1. Spec Brief

```yaml
spec_brief:
  goal: ""
  non_goals:
    - ""
  source_facts:
    - source: "user/video/screenshot/doc/API/code"
      fact: ""
      boundary: "what this does not prove"
  business_rules:
    - ""
  invariants:
    - ""
  acceptance_criteria:
    - id: AC1
      claim: ""
      evidence_required: ["diff", "test", "runtime"]
  negative_cases:
    - id: N1
      forbidden_behavior: ""
      proof_required: ""
  risk_class: "read_only|local_reversible|local_destructive|external_side_effect|production_sensitive|irreversible"
  open_questions:
    - "ask only if this changes path/risk/acceptance"
```

## 2. Constitution Readback

- Project/profile rules loaded:
- User red lines that apply:
- Repo/worktree/branch status if editing code:
- External/destructive/credential gates:

## 3. Plan

```yaml
plan:
  chosen_path: ""
  rejected_paths:
    - path: ""
      reason: ""
  impacted_modules:
    - ""
  data_flow:
    - "source -> transform -> UI/API/runtime"
  rollback:
    - ""
  verification_strategy:
    commands:
      - ""
    ui_or_api:
      - ""
```

## 4. Tasks

| ID | Objective | Dependencies | Files/modules | Verification | Risk |
|---|---|---|---|---|---|
| T1 | Evidence scan | none | | | |
| T2 | Rule extraction | T1 | | | |
| T3 | Implementation | T2 | | | |
| T4 | Regression tests | T3 | | | |
| T5 | Runtime/UI/API proof | T3/T4 | | | |
| T6 | Converge closure | all | | | |

## 5. Converge Matrix

| Spec / acceptance claim | Code/doc evidence | Test evidence | Runtime/UI/API evidence | Status | Gap |
|---|---|---|---|---|---|
| AC1 | | | | pending | |
| N1 | | | | pending | |

## 6. Closure

Closure state: `done | waiting_acceptance | blocked | rolled_back | superseded`

- Done only if every required spec claim has sufficient evidence.
- Waiting acceptance if implementation proof exists but user/UI/API acceptance remains.
- Blocked if authority, credentials, destructive action, external side effect, or unavailable evidence is required.

## Example pattern: config-driven CTA/UI

Use this shape for backend-config-driven UI behavior without project-specific hardcoding:

- Goal: UI displays a business CTA only when the authoritative backend configuration provides both action target and display text.
- Non-goal: frontend must not infer a business CTA from category, route, product type, or legacy fallback unless the spec explicitly says so.
- Positive case: `target|ctaTarget` exists and `ctaText` exists -> show configured CTA.
- Negative cases:
  - category implies product but backend CTA missing -> no business CTA.
  - target exists but text missing -> no business CTA.
  - text exists but target missing -> no business CTA.
- Evidence: selector/unit tests for all cases, UI screenshot/runtime readback for configured and unconfigured states, diff showing removal or isolation of hardcoded fallback.
