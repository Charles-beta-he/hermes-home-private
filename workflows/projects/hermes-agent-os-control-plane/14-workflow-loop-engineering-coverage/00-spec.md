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
