# Audit Coverage Registry Pattern

Use when the user asks for system-level self-audit, multi-model/Fable review, or to push audit coverage to “100%”.

## Key rule

Never let “100% audit coverage” mean “the system is 100% healthy” or “there are no blind spots.” Define it as coverage-model completeness only:

A dimension is covered when it has all four fields:

1. current readback evidence;
2. verdict;
3. known gaps / blind spots;
4. next action.

100% coverage means every declared dimension has those four fields. It is not a claim of omniscience, production readiness, or risk elimination.

## Minimal registry shape

```json
{
  "schema": "audit_coverage_registry_v1",
  "definition": "100% coverage means every declared audit dimension has current local readback, verdict, known gaps, and next action. It does not mean omniscience or no risks.",
  "coverage_percent": 100,
  "dimension_count": 15,
  "covered_dimension_count": 15,
  "dimensions": [
    {
      "id": "system_runtime",
      "coverage_status": "covered_by_current_readback",
      "verdict": "healthy_with_attention",
      "evidence": ["post-update check", "brain validate", "edge selfcheck"],
      "known_gaps": ["single-time snapshot"],
      "next_action": "add freshness window"
    }
  ]
}
```

## Recommended dimensions for Hermes self-audit

- system runtime
- tool discipline / hook gates
- authority boundaries
- memory and skills
- project portfolio
- taskpool / cron / automation
- provider routes
- multi-model governance
- git / release / rollback
- user-profile alignment
- external side effects / outbox
- security
- cost / token / storage
- UI / browser / desktop capability
- continuous learning / steward / skill tracking

## Workflow

1. Gather only read-only evidence unless the user explicitly authorizes repairs.
2. Ask the external model (for example Fable 5) to audit the evidence and propose dimensions.
3. Build the registry with one row per dimension.
4. Validate deterministically: dimension count matches, every dimension has evidence, verdict, gaps, and next action.
5. Ask the external model to audit the registry itself for pseudo-coverage.
6. Report with the definition first, then health/risks. Explicitly say what cannot be claimed.

## Reporting language

Use:
- “Coverage reached 100% under the declared 15-dimension model.”
- “Known gaps are registered with next actions.”
- “This does not mean the system is 100% healthy.”

Avoid:
- “Everything is normal.”
- “Fully passed.”
- “Production ready.”
- “No blind spots.”

## Commit/gate pitfall

If a local pre-commit / BrainConstraintGate requires architecture evidence labels, name the registry as an architecture artifact or add a companion readback note with explicit labels such as `design_doc:` and `gate_readback:`. Do not bypass the hook; make the evidence discoverable and retry the normal commit.
