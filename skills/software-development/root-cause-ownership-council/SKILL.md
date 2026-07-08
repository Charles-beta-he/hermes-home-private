---
name: root-cause-ownership-council
description: Use when repeated fixes, multi-controller state conflicts, high-risk shared runtime changes, or multi-model/multi-agent review are needed to reframe symptoms into owner contracts, evidence ledgers, falsifiers, minimal implementation boundaries, and final verification gates.
version: 1.2.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [root-cause, multi-agent, ownership, evidence, review, governance]
    related_skills: [path-error-root-cause-governance, multi-agent-code-review, qian-meta-synthesis, abstraction-governance, agent-skill-design-patterns]
---

# Root-Cause Ownership Council

## Overview

Use this skill to run a multi-agent / multi-role council when ordinary debugging or implementation is at risk of becoming a patch pile. The council reframes visible symptoms into shared state variables, identifies the single owner for each variable, preserves dissent, separates evidence from model opinion, and hands implementation only a minimal scoped contract.

This is a Pipeline + Reviewer skill. It does not replace normal coding. It is a high-risk / repeated-regression role set for cases where the problem is likely the problem representation, not just the code line.

Core principle:

```text
Do not ask five agents for five fixes. Ask orthogonal roles for framing, ownership, falsifiers, evidence, implementation boundaries, and verification.
```

## v1.2.1 Autonomous Merge Correction

For Hermes self-evolution/private-home PRs in a user-approved autonomous lane, the release loop should not stop at PR creation waiting for a second merge prompt. The correct path is evidence-first multi-model review, then automated merge when objective evidence is grounded, review is non-blocking, PR is mergeable, scope is clean, and post-merge readback/rollback are available. This does not apply to project repos, external dispatch, runtime deploy, destructive changes, credentials, broad fanout, or unclear target authority.

## v1.2 Development Experience Coverage

Scope: class-level routing expansion for reusable frontend, backend, fullstack, UI/UX, and release-development experience. Applicability: use only when normal development risk signals require a specialist reviewer or escalation gate. Anti-condition: do not encode one project, customer, repository, route, issue, or product incident as global truth.

This release expands the council module beyond repeated root-cause cases into a routed development-experience coverage layer. Normal development tasks should first choose the smallest route that covers the risk: direct fix, specialist reviewer, ownership audit, lightweight council, full council, or release certification.

New specialist coverage includes API Contract, Migration & Data Integrity, Security & Permission, Concurrency & Idempotency, Observability, Performance, Accessibility & Localization, Release Readiness, Fullstack Coordination, UIMax Auditor, and Xianggua UI/UX Reviewer.

See `references/development-experience-coverage-matrix.md`, `references/frontend-backend-trigger-map.md`, `references/normal-dev-vs-council-escalation.md`, and `references/xianggua-ui-ux-role.md`.

## v1.1 Always-callable Agent Module

This skill can be used as an always-callable module contract, but it should not be always fully loaded.

```text
Always callable, not always loaded.
```

Use a progressive loading model:

1. Micro-router: a tiny trigger contract visible to broad model/workflow routing surfaces.
2. Role registry: load `references/agent-role-registry.md` only when council roles may be needed.
3. Full council: load this SKILL.md plus session/templates/references only for high-risk or repeated tasks that need owner contracts, falsifiers, evidence ledgers, and final certification.

The module may recommend roles and gates, but it does not grant push, deploy, external dispatch, destructive, credential, memory-write, taskpool-lifecycle, or scheduler authority. See `references/always-callable-agent-module.md` and `references/council-router-contract.md`.

When publishing a new version of this module as a repo-reviewed release, use `references/agent-module-release-issue-pr-loop.md` for the scoped branch, validation, issue, PR, and readback loop.

## When to Use

Use when:

- The same symptom has already been fixed or reverted more than once.
- A diff adds another global listener, force reload, timeout, scroll restore, preventDefault, feature flag, route exception, or page-specific workaround.
- Multiple modules write the same state variable or lifecycle decision.
- A user asks for root cause, final convergence, multi-model analysis, multi-agent roles, existing-issue regression, or "do not keep patching".
- The change touches high-risk shared domains: auth/session, payment/remit/card flows, notification/realtime delivery, PWA release/update/cache, mobile keyboard/viewport/layout, API interceptor, state machine, async worker, scheduler, or evidence gate.
- A model/team consensus exists but no falsifier, runtime evidence, or owner table exists.

Do not use for:

- Simple deterministic bugs with direct root-cause evidence and no shared state.
- Pure copy/style tweaks, static pages, or low-risk CRUD changes.
- Requests where the user explicitly wants a quick reversible prototype and accepts limited verification.
- Replacing product/design/security decision makers. The council supplies evidence and boundaries; it does not invent business policy.

## Council Roles

Default 9-role council:

| Role | Responsibility | Output |
|---|---|---|
| Framing Lead | Reframe symptom into state/path/time/goal/non-goals | Problem brief, constraints, path matrix |
| Domain Specialist | Inspect the specific domain such as mobile layout, auth, notification, release, payment, or customer support | Domain owner contract and domain risks |
| Skeptic / Falsifier | Attack assumptions and produce counterexamples | Falsifier table and stop conditions |
| Ownership Auditor | Map state variables, current writers, correct owner, forbidden writers | Ownership table |
| Product Standard Reviewer | Check scenario semantics and user-facing standard behavior | Interaction/business standard classification |
| Evidence Accountant | Separate facts, model opinions, source quality, missing proof | Evidence ledger |
| Minimal Implementer | Propose the smallest code boundary after the contract is accepted | Patch boundary and rollback scope |
| Regression Designer | Convert existing problems into tests and contrast paths | Regression matrix |
| Final Certifier | Re-check final diff, commands, readbacks, and residual risks | PASS/BLOCK verdict with evidence |

For small tasks, use a 3-role cut:

1. Framing Lead + Ownership Auditor
2. Skeptic + Evidence Accountant
3. Minimal Implementer + Regression Designer

### v1.2 Specialist reviewers

Scope: class-level specialist roles for reusable development review. Applicability: invoke these roles only when their trigger signals appear in the current task. Anti-condition: do not encode one project, product, customer, repository, endpoint, schema, issue, or incident as global truth.

These roles are invoked by the development experience coverage matrix before escalating to a full council:

- API Contract Reviewer — request/response schema, DTO, enum, pagination, sorting, filtering, error contract.
- Migration & Data Integrity Reviewer — entity/table/column/index/constraint/native SQL/persisted-data changes.
- Security & Permission Reviewer — endpoint/role/object permission, sensitive data, upload, token/session, XSS/CSRF/CORS.
- Concurrency & Idempotency Reviewer — payment/order/status, webhook/callback, retry, queue/job, double-submit, external side effect.
- Observability Reviewer — trace/log/metric/audit/redaction gaps.
- Performance Reviewer — large lists, dashboards, charts, exports, slow query, N+1, missing index, bundle/render bottleneck.
- Accessibility & Localization Reviewer — forms, dialogs, keyboard, ARIA, contrast, screen reader, currency/date/timezone, long text, multi-language labels.
- Release Readiness Reviewer — merge/release/publish/deploy/readiness, branch merge, issue closure, deploy order.
- Fullstack Coordination Reviewer — frontend/backend/mobile/admin/shared schema compatibility and deploy ordering.
- UIMax Auditor — A/A+, uIMax grade, screenshot matrix, console health, systematic UI release gate.
- Xianggua UI/UX Reviewer — visual taste, product scenario fit, premium/professional polish, screenshot acceptance, design consistency.

See `references/development-experience-coverage-matrix.md` and `references/xianggua-ui-ux-role.md`.

## Stage Gate Workflow

### Gate 0 — Intake and trigger check

Confirm the task actually warrants a council. If not, use a narrower debugging, code review, or implementation skill.

Minimum intake:

- Current visible symptom.
- Known repeated fixes or churn signals.
- Scope and non-goals.
- High-risk shared state variables.
- Existing failing tests, user paths, logs, screenshots, or API readbacks.

### Gate 1 — Independent framing

Before seeing each other's conclusions, roles produce independent statements:

- What is the problem representation?
- What state variable or lifecycle is involved?
- What visible symptom might be misleading?
- What evidence would disprove this framing?

Block implementation if all agents answer at the component/symptom layer only.

### Gate 2 — Ownership map

Create one ownership table per domain:

```text
Variable | Current controllers/writers | Correct owner | Readers | Forbidden writers | Cleanup/migration path | Verification
```

Examples of variables:

- viewport height, document scroll, route scroll, focused input visibility, CTA placement;
- auth expired, refresh retry, SSO kick, 4xx/5xx display message;
- notification cursor, unread count, push account preference, current-device subscription;
- backend release policy, service-worker asset freshness, reload timing, bad-release marking;
- amount decimal string, fee quote, limit warning, order status, CTA enablement.

### Gate 3 — Falsifier and evidence ledger

For every nontrivial claim, record:

```yaml
claim: ...
if_true_observe: ...
if_false_observe: ...
minimal_probe: ...
evidence:
  source: file|test|log|screenshot|api|git_history|model_opinion
  quality: A|B|C|D
missing: ...
decision: accept|reject|defer|needs_probe
```

Evidence quality:

- A: fresh command/test/runtime readback/API response/screenshot/bounding boxes.
- B: source code, current diff, git log, docs, deterministic static analysis.
- C: model interpretation or expert judgment.
- D: analogy, memory, or generic best practice.

Only A/B evidence can authorize implementation. C/D evidence can propose hypotheses only.

### Gate 4 — Standard / scenario classification

Classify the user-facing scenario before deciding the fix. Do not transfer behavior from one scenario class to another.

Common examples:

- Ordinary financial form / amount / address / remark: stable header, focused field visible, middle content scrolls, CTA remains in original bottom/safe-area region; CTA is not a keyboard accessory unless product explicitly defines it.
- Chat/support/AI composer: composer can follow keyboard, message list shrinks, header remains visible.
- Short auth/login: default bottom CTA may switch to inline focus CTA; suggestions must not lose first tap or race blur.
- Sheet/modal/scanner/selector: overlay owns its panel/internal scroll; background route/body does not manage sheet keyboard behavior.
- Preview/confirm/detail: must not inherit input-flow keyboard shells or tokens.

### Gate 5 — Minimal implementation boundary

Implementation may start only after:

- Owner table names the correct owner.
- Competing controllers to remove or narrow are known.
- Falsifiers exist for the selected hypothesis.
- Regression matrix names existing broken paths and contrast paths.

Default patch bias:

1. Delete or narrow conflicting controller.
2. Preserve public API / product behavior.
3. Add or update behavior tests before broad refactors when practical.
4. Avoid new global listeners, timeouts, feature flags, or route exceptions unless the owner contract explicitly requires them.

### Gate 6 — Final certification

Final Certifier checks the actual final diff, not the pre-fix plan.

Do not claim done/certified unless fresh evidence covers:

- Commands/tests run and results.
- User paths and contrast paths.
- No new controller for the same variable.
- Dead token/flag/file cleanup status.
- Residual risks and unverified devices/environments.

## Multi-Model / Multi-Agent Execution Pattern

Use models/agents for orthogonal review, not voting.

Recommended rounds:

1. Independent domain reviews.
2. Cross-cutting ownership aggregation.
3. Dissent review and falsifier selection.
4. Minimal patch planning.
5. Implementation.
6. Final diff re-review.

If using subagents, provide each subagent a role-specific prompt and scoped evidence. Do not ask all subagents the same broad question.

Promote any deterministic finding even if only one agent reports it when it includes a failing test, exact source path, reproducible command, security issue, data-loss risk, or money-precision risk.

## Open-Source Agent Ecosystem Intake

GitHub agent repos are useful as references, but do not treat a repo as authority without live evidence and fit analysis.

Known reference classes:

- Role / software-company patterns: MetaGPT, ChatDev, CrewAI examples, CAMEL.
- Runtime / orchestration patterns: LangGraph, Microsoft Agent Framework, OpenAI Agents SDK, Google ADK, Agno, CrewAI.
- Executor agents: Claude Code, Gemini CLI, Codex/OpenCode-style tools, browser-use.
- Discovery indices: awesome-ai-agents, awesome-agents.

Use them to extract reusable role cards, workflow states, handoff protocols, evidence gates, and control-plane ideas. Do not copy product code, visual identity, credentials, or unverified runtime claims.

See `references/github-agent-repos-evidence.md` for the initial researched repository packet and `references/agent-role-registry.md` for the v1 role cards.

## Output Template

```yaml
root_cause_ownership_council:
  version: "1.2.0"
  problem: "..."
  scope: []
  non_goals: []
  stop_triggers: []
  roles_run: []
  ownership_table:
    - variable: "..."
      current_controllers: []
      correct_owner: "..."
      forbidden_writers: []
      verification: []
  evidence_ledger:
    - claim: "..."
      evidence_quality: A|B|C|D
      evidence: []
      falsifier: "..."
      decision: accept|reject|defer|needs_probe
  dissent:
    - role: "..."
      objection: "..."
      resolution: accepted|rejected|split|deferred
  minimal_solution_boundary: []
  regression_matrix: []
  final_verdict: PASS|BLOCK|DEGRADED_PASS|DEFER
  residual_risk: []
```

## Release v1.2.0 Contract

This v1.2.0 release adds development-experience coverage and UI/UX specialist routing on top of the v1.1 always-callable module contract:

- frontend, backend, fullstack, UI/UX, and release triggers can route to lightweight specialist reviewers;
- normal deterministic work can stay on direct-fix or specialist-review routes instead of full council ceremony;
- Xianggua UI/UX Reviewer is available for taste/scenario-fit/polish/screenshot acceptance, while UIMax Auditor remains the evidence-backed grading gate;
- full council escalation remains reserved for repeated fixes, shared-state ownership conflicts, cross-domain ambiguity, or release certification;
- all execution authority remains outside the module and must follow Hermes tool/user/evidence gates.

It remains stable for use as a development role template when:

- the task is high-risk or repeated;
- user-path evidence matters;
- at least one role produces a falsifier;
- ownership and evidence ledgers are emitted;
- implementation remains separately verified.

It is not a production runtime, scheduler, external-dispatch authority, or autonomous side-effect executor. It is a reusable Hermes role/council skill and module contract for structuring specialist review, multi-agent analysis, code review, implementation planning, UI/UX acceptance, and certification.

## Common Pitfalls

1. Treating multi-model agreement as proof. Agreement is advisory unless grounded by evidence.
2. Asking all agents the same question and calling the result coverage.
3. Letting the implementer role start before owner and falsifier gates exist.
4. Flattening dissent into consensus instead of preserving minority blockers.
5. Writing tests that assert implementation traces instead of user-path behavior.
6. Importing an open-source agent framework directly before extracting the smaller role/control-flow pattern needed.
7. Overusing the council for trivial tasks and slowing down normal development.
8. Claiming UI/product acceptance without runtime, screenshot, API, or command readback evidence.

## Verification Checklist

- [ ] The trigger class matched; this was not a trivial one-off.
- [ ] At least one state variable owner table was created.
- [ ] Claims were split into evidence vs model opinion.
- [ ] Falsifiers or probes exist for major hypotheses.
- [ ] Existing broken paths and contrast paths are in the regression matrix.
- [ ] Minimal implementation boundary prefers removing/narrowing conflicting controllers before adding flags.
- [ ] Final verdict is bound to fresh final diff/test/readback evidence.
- [ ] Any open-source repo inspiration is cited as reference evidence, not treated as authority.
