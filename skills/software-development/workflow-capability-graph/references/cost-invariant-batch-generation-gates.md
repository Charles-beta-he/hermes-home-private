# Cost-Invariant Batch Generation Gates

Scope: workflows that use cheap/low-cost models to generate many candidates while preserving correctness, compliance, or product invariants.

Applicability:
- a stable kernel/spec is reused across many themes, content packs, fixtures, localizations, or parameter sets;
- generation throughput should increase without granting the cheap model authority over protected semantics;
- objective validators, simulations, golden cases, or human acceptance can decide promotion.

Anti-conditions:
- the task changes core state transitions, win/lose/scoring/economy/privacy/platform contracts or release authority;
- correctness is purely subjective and has no objective or human gate;
- platform policy is unknown or stale;
- the batch is so small that the governance cost exceeds reuse.

## Core invariant

Do not promise that a cheap model is as accurate as a larger model. Preserve outcome quality by making model output a candidate and keeping promotion gates cost-invariant:

```text
frozen spec/kernel
→ capability allowlist
→ cheap candidate generation
→ deterministic schema + protected-surface gate
→ bounds/rights/dedupe/golden/simulation gates
→ accepted | rejected | escalated | blocked
```

The same gates apply regardless of producer model. Model self-report is never evidence. Unknowns fail closed.

## Protected surfaces

Declare machine-readable protected fields before routing. Common examples:

- state schema and legal actions;
- win/lose/scoring/probability/difficulty formulas;
- economy and monetization rules;
- platform SDK/API and privacy contracts;
- release/publish decisions;
- any shared kernel whose change invalidates downstream evidence.

A candidate touching a protected surface must route to a higher-reasoning lane and independent evidence. It must not be silently stripped, merged, or treated as ordinary content.

## Allowed cheap-model tasks

Good candidates have narrow schemas and cheap deterministic verification:

- classification and normalization;
- theme/copy/localization drafts;
- asset briefs with rights metadata;
- parameter generation inside frozen bounds;
- test-fixture expansion;
- failure-summary formatting.

Bad candidates for cheap-only handling:

- novel core mechanics;
- rule/economy/advertising changes;
- platform compatibility claims;
- privacy/security decisions;
- release arbitration.

## Escalation rules

Escalate or block when any applies:

- protected field touched;
- confidence below a declared threshold;
- required platform contract unknown;
- deterministic gate fails;
- the same failure repeats beyond a bounded retry count;
- evidence conflicts;
- human playability/taste/fairness acceptance is required.

Retries remain inside the total model-call budget. A cheap retry does not erase the earlier failure or restore confidence automatically.

## Batch isolation

Compile each candidate independently. One invalid item must not poison valid siblings, and a valid sibling must not launder an invalid item. Emit deterministic per-item states and a batch receipt:

```json
{
  "accepted": [],
  "rejected": [{"candidate_id": "...", "error": "..."}],
  "summary": {"accepted": 0, "rejected": 0, "total": 0},
  "authority": {"may_publish": false}
}
```

Bind frozen-kernel digest separately from content digest. A content swap must preserve the kernel digest; a shared-kernel edit invalidates old downstream evidence.

## Accuracy and cost metrics

Correctness guardrails:
- protected_surface_escape_count = 0;
- gate_escape_count = 0;
- deterministic_replay_pass_rate = 100%;
- unknown_platform_contract promoted to build/release = 0.

Cost/throughput metrics are secondary:
- low_cost_candidate_share;
- escalation_rate;
- high_cost_call_share;
- accepted candidates per validation unit.

Never optimize high-cost-call share before correctness guardrails are stable.

## Verification matrix

Required negative tests:
1. cheap allowlisted task routes low-cost;
2. protected change escalates;
3. low confidence escalates;
4. unknown external/platform contract blocks;
5. content cannot override kernel fields;
6. parameter bounds reject invalid values;
7. same input produces same digest;
8. content swap preserves kernel digest;
9. mixed batch isolates invalid candidates;
10. every output keeps publish/payment/credential authority closed by default.

## Claim boundary

This pattern can prove local contract isolation, deterministic compilation, routing, and failure containment. It cannot prove product fun, retention, revenue, platform approval, production performance, legal clearance, or real-provider quality without the corresponding runtime, official-source, human, or production evidence.
