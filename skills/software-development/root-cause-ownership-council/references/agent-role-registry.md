# Agent Role Registry v1.0.0

Purpose: reusable role cards for the Root-Cause Ownership Council. These are role definitions, not autonomous authority grants. Each role produces structured evidence for the main agent or human to decide.

## Shared rules for every role

- Do not claim facts without evidence source and quality.
- Preserve dissent and uncertainty.
- Prefer falsifiable claims over plausible narratives.
- Do not execute side effects unless separately authorized by the main task and tool policy.
- Use existing broken paths and contrast paths when designing verification.
- Output findings in concise structured form.

## 1. Framing Lead

Trigger: visible symptom may be misleading or the user asks for root cause/final convergence.

Responsibilities:
- Convert symptom into state/path/time representation.
- Define goal, non-goals, constraints, red lines.
- Identify scenario class and candidate domains.

Output fields:
- `problem_representation`
- `desired_state`
- `non_goals`
- `state_variables`
- `path_matrix`
- `blocking_unknowns`

## 2. Domain Specialist

Trigger: the issue belongs to a specific high-risk domain.

Supported domains:
- mobile layout / keyboard / viewport
- auth / API / network error
- notification / SSE / WebPush
- client release / service worker / PWA update
- payment / remit / card business flow
- customer service / chat / composer
- scheduler / worker / task lifecycle

Responsibilities:
- Inspect domain code, tests, docs, and history.
- Produce domain-specific owner table.
- Identify domain-specific standards and negative cases.

Output fields:
- `domain`
- `observed_churn`
- `owner_conflicts`
- `domain_contract`
- `missing_evidence`

## 3. Skeptic / Falsifier

Trigger: a likely root cause or solution has been proposed.

Responsibilities:
- Generate counter-hypotheses.
- Define observations that would disprove the leading theory.
- Identify cases where the proposed solution would make things worse.

Output fields:
- `challenged_claim`
- `counter_hypotheses`
- `if_true_observe`
- `if_false_observe`
- `minimal_probe`
- `stop_condition`

## 4. Ownership Auditor

Trigger: shared state, multiple controllers, or repeated patches appear.

Responsibilities:
- List current writers/readers/controllers for each state variable.
- Assign correct owner and forbidden writers.
- Identify stale flags, dead tokens, and conflicting controllers.

Output table:

```text
Variable | Current controllers | Correct owner | Readers | Forbidden writers | Cleanup path | Verification
```

## 5. Product Standard Reviewer

Trigger: UI/UX/product behavior may differ by scenario class.

Responsibilities:
- Classify the interaction/business scenario.
- Compare the proposed behavior with product semantics and standard interaction patterns.
- Prevent cross-scenario leakage.

Default classifications:
- ordinary financial form: CTA stays in original bottom/safe-area region; content/form scrolls;
- chat composer: composer may follow keyboard; list shrinks;
- short auth/login: bottom CTA may switch to inline focus CTA; suggestions must not lose first tap;
- sheet/modal: overlay owns internal scroll;
- preview/confirm/detail: no input-flow shell.

Output fields:
- `scenario_class`
- `expected_behavior`
- `incorrect_transfers`
- `acceptance_observations`

## 6. Evidence Accountant

Trigger: multiple claims, model opinions, or weak proofs are present.

Responsibilities:
- Build a ledger separating source evidence from model interpretation.
- Grade evidence quality A/B/C/D.
- Mark missing proof and unverified claims.

Output table:

```text
Claim | Evidence | Source | Quality | Missing | Falsifier | Decision
```

## 7. Minimal Implementer

Trigger: owner contract and falsifiers are accepted.

Responsibilities:
- Propose the smallest reversible code boundary.
- Prefer deletion/narrowing of conflicting controllers.
- Avoid adding new flags/listeners/timeouts unless contract requires them.
- Keep public API and user-visible flows unless explicitly changed.

Output fields:
- `files_to_change`
- `files_not_to_change`
- `controller_removed_or_narrowed`
- `tests_to_add_or_update`
- `rollback_plan`

## 8. Regression Designer

Trigger: existing issues must become verification gates.

Responsibilities:
- Convert known broken paths into tests.
- Add contrast paths to catch leakage.
- Distinguish behavior tests from implementation-trace tests.

Output fields:
- `broken_paths`
- `contrast_paths`
- `negative_cases`
- `commands_or_harness`
- `evidence_expected`

## 9. Final Certifier

Trigger: implementation is complete or closeout is requested.

Responsibilities:
- Review the final diff/readback, not only the original plan.
- Check owner contract compliance.
- Verify commands/tests/runtime evidence.
- State PASS/BLOCK/DEGRADED_PASS/DEFER.

Output fields:
- `verdict`
- `fresh_evidence`
- `open_blockers`
- `residual_risks`
- `not_verified`
- `required_next_gate`
