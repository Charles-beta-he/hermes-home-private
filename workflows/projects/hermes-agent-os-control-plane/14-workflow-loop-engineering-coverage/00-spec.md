# Workflow / Loop Engineering Coverage — Canonical Spec

Date: 2026-07-10
Project: hermes-agent-os-control-plane
Risk: local reversible implementation; no external dispatch, deploy, push, destructive operation, credential entry, or production write.

## Objective

Raise the engineering-contract coverage of Hermes workflow governance and Loop Engineering to 100% while keeping runtime-health truth separate. “100%” means every required stage, system, authority boundary, and evidence claim is explicitly covered or explicitly classified N/A with a machine-verifiable reason; it never means external providers or optional dependencies are fabricated healthy.

## Non-goals

- Do not weaken gates, thresholds, or evidence requirements to increase a score.
- Do not classify empty checks as covered.
- Do not treat docs, node counts, unit-test counts, static auth/config readiness, or model consensus as runtime success.
- Do not enable external/cron/taskpool/AgentOS mutation from this slice.
- Do not edit memory or delete/clean existing user artifacts.

## Source facts

- Legacy dynamic registry reported 27 systems and 2 missing checks while only 5 systems had non-empty current_checks.
- Exact user intent routed to domain=unknown before this slice.
- Static provider selfcheck passed, while a real T1 fan-out failed 0/3 and DeepSeek was health-gated.
- Existing Workflow Kernel Loop persisted decision/module-plan/scaffold/ledger but did not emit machine-verifiable Simulate, Verify, Ratchet, Monitor, or Cleanup stages.

## Required Loop contract

Nine kernel stages, each with status and evidence refs:
1. Observe
2. Orient
3. Compile
4. Simulate
5. Execute
6. Verify
7. Ratchet
8. Monitor
9. Cleanup

Five control moves must be mapped: discovery, handoff, verification, persistence, scheduling.
Six system parts must be declared: automations, worktrees, skills, connectors, subagents, memory. Disabled/N/A parts need explicit reason and boundary evidence.

The evaluator must be a separate module from the generator, have veto authority, require evidence refs, enforce positive budgets, and reject any undeclared/missing stage or enabled external side effect.

## Acceptance criteria

AC1. The exact Chinese request about self workflow engineering coverage and loop engineering routes to `hermes_self_architecture` without ambiguity.
AC2. A local loop run emits all nine stages, 5/5 control-move coverage, 6/6 declared-part coverage, positive budgets, kill switch, local evidence, and all external side-effect flags false.
AC3. Independent evaluator returns PASS only for complete/evidenced receipts and vetoes missing stage, missing evidence, invalid budget, or enabled external side effects.
AC4. Strict engineering coverage registry has zero unclassified systems and 100% classification coverage. It separately reports operational health and does not turn a missing/unhealthy check into covered.
AC5. Provider projection separates static readiness from actual runtime evidence; absent/failed runtime evidence is `not_verified` or `degraded`, never healthy/certified.
AC6. Focused tests, py_compile, live local run, artifact readback, and git diff checks pass.
AC7. No external send, deploy, push, destructive operation, credential entry, production write, or implicit cron/taskpool/AgentOS mutation occurs.

## Negative cases

- Keyword-only “workflow” does not create a durable asset.
- Empty current_checks cannot produce healthy/covered status.
- Static provider status cannot certify actual runtime invocation.
- Missing evaluator independence/veto/evidence fails closed.
- Any side-effect flag true fails the local loop gate.
- A 100% engineering-contract score may coexist with degraded operational health; the report must show both.

## Score semantics

- Engineering-contract coverage: covered-or-explicitly-classified requirements / total requirements.
- Loop stage coverage: evidenced stages / 9.
- Loop control coverage: evidenced control moves / 5.
- Loop system-part declaration coverage: declared parts with boundary / 6.
- Operational health: currently passing live checks / applicable live checks.
- Full-score claim is allowed only for engineering-contract coverage after AC1–AC7 evidence. Operational health is independently scored and may remain below 100.

## Rollback

- Revert only the scoped core commit and scoped home-repo files from this slice.
- Remove generated local run receipts only under separate cleanup authorization.
- No global config change is required.

## Converge evidence — 2026-07-10

- AC1: Agent OS control-plane suite passed `28 passed`; the exact Chinese workflow/Loop Engineering route remains shadow-only with `would_execute=false`.
- AC2–AC3: Workflow/Lark/evaluator/asset suite passed 18 tests. The live loop receipt records 9/9 stages, 5/5 control moves, 6/6 declared system parts, positive budgets, evaluator PASS, and all external side-effect flags false.
- AC4–AC5: Dynamic coverage suite passed 16 tests. Latest runtime readback reports 27 systems, zero missing checks, 100% classification/check attachment, Provider runtime verified from recent real planner artifacts, and engineering gaps separated from two operational findings.
- AC6: `consult_models` integration/fanout suites passed 119 tests; dynamic/workflow/Lark suites passed 34 tests; Agent OS suite passed 28 tests; scoped `py_compile` and `git diff --check` passed.
- Evidence-link repair: `claim_id + status=supports|contradicts` is normalized into explicit claim links. RED reproduced three failures; GREEN passed those tests and the 119-test consult_models suite. Readback now yields C-001 `verified_by_evidence`, C-002 `contradicted_by_evidence`, and no false `needs_link_review`.
- Independent review: the engineering-only packet reached `truth_status=grounded`, `evidence_coverage=1.0`, and `no_action_certification`, but final multi-model certification remains `degraded_not_certified` because planner success was 2/3 against min quorum 3.
- Operational boundary: Provider runtime is currently not degraded. Lark remains degraded (`no_tokens` / existing login in progress), and the root repository is dirty until scoped commits are written. These are operational findings, not missing engineering checks.

Closure state: `waiting_acceptance`. Engineering-contract coverage is converged; global operational-health/full-certification claims remain blocked by Lark human OAuth and independent certification quorum.

## V2 Spec Brief — Procedure-Level E2E Truth and Ratchet

### Goal

Make every enabled runtime procedure explicitly distinguishable as fully landed and freshly end-to-end verified, landed but unverified/stale, partially landed, pending, authority-blocked, degraded, or N/A. A system may be operationally ready while its procedures remain uncertified; aggregate health must fail closed for any required procedure lacking fresh E2E evidence.

### Non-goals

- Do not execute browser/OAuth, external reads/writes, delivery, deploy, destructive, credential, payment, or production flows from ordinary selfcheck.
- Do not convert unit/contract tests, check attachment, token readiness, model votes, or historical chat into a fresh E2E receipt.
- Do not classify authority-blocked procedures as runtime failures; expose them as distinct pending boundaries.
- Do not delete or rewrite the existing engineering and operational axes.

### Source facts and boundaries

- The current Coverage Registry has engineering coverage and operational findings but no generic procedure/E2E axis.
- Lark `--health-check` proves current auth readiness only and intentionally cannot open a browser, auto-authorize, read tasks, or write Lark.
- A real OAuth recovery was previously exercised under exact user authority, but no durable, standardized, fresh receipt exists that this control plane can independently verify now.
- Provider runtime evidence already demonstrates a useful pattern: discover a recent real artifact, enforce quorum and freshness, and explicitly deny global certification.
- The Workflow Loop evaluator already demonstrates independent fail-closed receipt evaluation.

### Candidate paths and decision

1. Extend each system row with ad-hoc E2E fields. Rejected: conflates systems, checks, and procedures and cannot model multiple procedures per system.
2. Execute every E2E flow on every selfcheck. Rejected: unsafe, noisy, expensive, and impossible for authority-gated side effects.
3. Add a separate Procedure Validation Registry and project it into existing control-plane surfaces. Selected: preserves current behavior, supports multiple procedures per system, keeps selfcheck read-only, and permits receipt freshness/expiry and authority boundaries.

### Required procedure contract

Each procedure declaration must include a stable ID, owning system, requirement class, side-effect class, authority policy, implementation state, validation policy, freshness TTL, required evidence kinds, failure/recovery expectations, and propagation targets. Each receipt must include procedure ID, schema/version, started/completed timestamps, result, evidence refs, execution mode, side-effect declaration, authority reference when required, negative assertions, and cleanup/readback results.

For `exact_grant_required`, the declaration also names an independently controlled authority root and issuer. The receipt must bind the grant artifact SHA-256; the verifier rejects paths outside that root, symlinked path components, non-regular files, issuer or identity mismatch, and grants whose validity interval does not enclose the receipt execution interval. A receipt producer cannot satisfy this boundary by creating a matching grant in its own temporary directory.

### Canonical states

- `implementation_state`: `missing | scaffolded | landed | enabled`
- `validation_state`: `untested | contract_passed | integration_passed | e2e_passed | e2e_failed | stale | blocked_by_authority`
- `delivery_state`: `pending | in_progress | partially_landed | landed_unverified | fully_connected | blocked | not_applicable`
- `operational_state`: `unknown | ready | healthy | degraded | failed | not_running`

`fully_connected` requires enabled implementation, a fresh successful E2E receipt with existing evidence refs, all mandatory acceptance atoms satisfied, cleanup/readback success, no unresolved mandatory finding, and no forbidden side effect. `certified_healthy` additionally requires every required enabled procedure to be `fully_connected` and an independent evaluator to pass.

### Acceptance criteria

- AC8. A standalone procedure registry/evaluator loads declarations and receipts without executing procedures.
- AC9. Missing, malformed, contradictory, failed, or expired receipts fail closed and cannot produce `fully_connected`.
- AC10. Authority-blocked procedures remain distinct from operational failures and generate actionable local-only pending items.
- AC11. Every enabled discovered system is mapped to at least one procedure or has an explicit N/A reason; inventory gaps are visible.
- AC12. Procedure findings propagate to Coverage Registry, lifecycle, repair packets, quiet-success, Loop/evaluator input, and certification/readback summaries without collapsing existing axes.
- AC13. Real safe local/read-only procedures may produce receipts; external/authority-gated procedures are only represented and never silently executed.
- AC14. Independent multi-model review is advisory until deterministic tests, fresh artifact readback, and evidence-linked certification gates pass.

### Negative cases

- 100% check attachment with no procedure inventory cannot claim complete health.
- Current token validity cannot certify OAuth recovery or Task API read procedures.
- A mock/contract pass cannot be relabeled as E2E.
- An expired receipt becomes `stale`, reopens lifecycle state, and blocks certified health without auto-running the procedure.
- A missing authority grant becomes `blocked_by_authority`, not `healthy`, `failed`, or silently skipped.
- A receipt whose evidence path does not exist, whose procedure ID is unknown, or whose side-effect declaration contradicts policy is rejected.
- An inventory attestation whose `reviewed_at` is materially in the future is rejected; clock skew cannot be clamped into permanent freshness.
- A Workflow Loop receipt with a non-canonical schema, generator, or top-level status is vetoed even when its stage fields look complete.
- Ratchet demotion or failure reopen must clear the active promotion state while preserving the previous state as audit metadata; top-level lifecycle and promotion state cannot contradict each other.
- Agent OS procedure projections must validate nested axis and procedure-entry contracts at the Python trust boundary; malformed nested values are omitted and mark the projection untrusted before Dashboard consumption.

### Evidence required

RED/GREEN tests; schema/readback artifacts; failure injection for missing, expired, failed, authority-blocked, unknown-procedure, and forbidden-side-effect cases; live local/read-only receipt generation; dynamic selfcheck readback; Loop evaluator veto/readback; scoped diff and commit. External E2E remains at exact authority gates.
