# Council Router Contract

Version: 1.1.0

Scope: class-level routing contract for reusable council invocation across debugging, review, implementation planning, certification, and workflow absorption tasks.

Applicability: use when risk signals suggest that a root-cause ownership council may be needed.

Anti-condition: this router must not encode one project, repository, product, customer, or historical incident as global truth. Project-specific paths and examples belong in scoped session packets, not this global contract.

## Purpose

The Council Router decides whether to invoke Root-Cause Ownership Council roles and which subset to run. It is a routing contract, not a runtime authority grant.

## Input schema

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
```

## Output schema

```yaml
council_router_output:
  invoke: true|false
  reason: ""
  mode: none|micro|direct_fix|specialist_review|ownership_audit|lightweight_3_role|full_9_role|domain_specialist_only|final_certifier_only|release_certification
  roles:
    - id: framing-lead
      required: true
      parallel_group: 1
  gates:
    - owner_table_required
    - falsifier_required
    - evidence_ledger_required
    - regression_matrix_required
    - final_diff_review_required
  linked_files_to_load:
    - references/agent-role-registry.md
  forbidden_actions:
    - "No push/deploy/external dispatch from router decision alone."
  next_step: ""
```

## Routing rules

### No invocation

Return `invoke: false` when:

- the fix is deterministic and low-risk;
- no shared state or repeated churn exists;
- user asked for simple explanation only;
- council overhead would exceed risk.

### Micro mode

Use when the model only needs a reminder:

- ask for owner before patching;
- require falsifier;
- separate evidence from model opinion.

### Specialist review mode

Use when a normal development task has one or more clear specialist risks but does not yet need a full council:

- API contract/schema/DTO/mock-live drift;
- database migration or persisted data integrity;
- security/permission/upload/sensitive data;
- concurrency/idempotency/webhook/job/retry;
- observability/incident evidence;
- performance/scalability;
- accessibility/localization;
- UI/UX polish, screenshot acceptance, Xianggua review, or uIMax grade;
- release readiness or fullstack coordination.

### Ownership audit mode

Use when the first real question is who owns a state variable, lifecycle transition, user-facing decision, or side effect.

### Lightweight 3-role mode

Use for medium risk:

1. Framing Lead + Ownership Auditor
2. Skeptic + Evidence Accountant
3. Minimal Implementer + Regression Designer

### Full 9-role mode

Use for high risk:

- multiple domains;
- repeated regressions;
- broad diff;
- user explicitly asks for multi-agent/multi-model/root cause;
- final certification or release readiness is requested.

### Domain specialist only

Use when the problem is clearly in one calibrated domain and needs only an owner contract:

- mobile keyboard/layout;
- error surface/auth/API;
- notification/SSE/WebPush;
- client release/PWA;
- payment/remit/card;
- customer service/chat/composer.

### Final certifier only

Use when implementation is complete and the user asks whether it is done/ready/certified.

## Required decision discipline

- The router can recommend roles, not decide truth.
- A single deterministic failing test outranks model consensus.
- A role can be skipped only with a reason.
- If the router selects implementation before owner/falsifier/evidence gates, the route is invalid.

## Generic example

```yaml
council_router_input:
  task: "A global error surface changed and a regression test now fails."
  user_intent: debug
  risk_signals:
    repeated_fix: true
    multi_controller_shared_state: true
    high_risk_domain: [api_interceptor, auth, global_toast]
    failing_test: true
    evidence_gap: false
  artifacts:
    tests: ["focused failing regression test"]
    files: ["interceptor implementation", "global error consumer"]

council_router_output:
  invoke: true
  reason: "Shared error surface with failing regression test."
  mode: lightweight_3_role
  roles:
    - id: framing-lead
      required: true
      parallel_group: 1
    - id: ownership-auditor
      required: true
      parallel_group: 1
    - id: evidence-accountant
      required: true
      parallel_group: 1
    - id: minimal-implementer
      required: true
      parallel_group: 2
  gates:
    - owner_table_required
    - failing_test_red_green_required
    - final_diff_review_required
```
