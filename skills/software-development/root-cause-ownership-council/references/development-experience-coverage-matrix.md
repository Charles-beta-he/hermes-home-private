# Development Experience Coverage Matrix

Version: 1.2.0

Scope: class-level trigger matrix for deciding when normal frontend/backend/fullstack development experience should invoke a specialist reviewer, an ownership audit, the Root-Cause Ownership Council, or release certification.

Applicability: reusable development workflow routing across frontend, backend, fullstack, UI/UX, release, and evidence-gated tasks.

Anti-condition: do not encode one repository, product, customer, route, API, database table, issue number, or incident as global truth. Project-specific facts belong in scoped session packets.

## Coverage model

The council module now has three coverage layers:

1. Normal development route: direct implementation or test-first fix with lightweight checks.
2. Specialist reviewer route: frontend/backend/fullstack/UI/UX domain experience applies, but no full council is needed.
3. Ownership/council route: repeated failures, shared state conflicts, cross-domain ambiguity, or release certification require owner tables, falsifiers, evidence ledgers, and final certification.

## Escalation levels

| Level | Name | Trigger | Roles |
|---|---|---|---|
| L0 | Direct Fix | Deterministic low-risk bug, direct evidence, no shared state | Minimal Implementer, optional Regression Designer |
| L1 | Specialist Review | Domain-specific frontend/backend/UI/UX experience applies | One or more specialist reviewers |
| L2 | Ownership Review | Multiple writers/controllers/readers for the same state or lifecycle | Ownership Auditor, Evidence Accountant, Domain Specialist |
| L3 | Root-Cause Council | Repeated fix, cross-domain breakage, user asks root cause/final convergence | Lightweight 3-role or full 9-role council |
| L4 | Release Certification | Merge, publish, deploy, A+/release readiness, issue closure | Final Certifier, Release Readiness Reviewer, relevant specialists |

## Frontend experience matrix

| Trigger signal | Typical risk | Specialist role | Evidence expected |
|---|---|---|---|
| Form, dialog, sheet, dropdown, tab, toast, focus, keyboard navigation | inaccessible or broken interaction | Accessibility & Localization Reviewer | source inspection, keyboard path, ARIA/focus evidence |
| Mobile layout, viewport, keyboard, safe area, tabbar | multiple scroll/height owners | Product Standard Reviewer + Ownership Auditor | screenshots/bounding boxes or route metrics |
| API-rendered data, nullable fields, enum labels, pagination | contract drift and blank/error UI | API Contract Reviewer | API/readback fixture, schema or typed contract |
| Store/cache/URL/component state all write same value | stale or conflicting UI state | Ownership Auditor | writer/reader table and regression path |
| Amount/date/currency/locale rendering | precision, formatting, timezone drift | Product Standard Reviewer + API Contract Reviewer | fixed string/locale examples and tests |
| Large list, dashboard, charts, images | render/performance regression | Performance Reviewer | profiling, bundle/list metrics, runtime observation |
| New visual surface, high-polish UI, A+/uIMax request | taste/quality regression | Xianggua UI/UX Reviewer + UIMax Auditor | screenshot matrix, visual rubric, console health |
| Error boundary, toast, loading/empty states | user feedback mismatch | Product Standard Reviewer + Evidence Accountant | state matrix and user-path evidence |

## Backend experience matrix

| Trigger signal | Typical risk | Specialist role | Evidence expected |
|---|---|---|---|
| Entity/DTO/native SQL/table/column/enum change | schema drift, prod migration failure | Migration & Data Integrity Reviewer | migration file, schema diff, rollback/compat note |
| New endpoint or role-sensitive behavior | authz bypass or object-level leak | Security & Permission Reviewer | permission matrix, backend guard evidence |
| Payment/order/status/webhook/retry/job | duplicate side effects or state race | Concurrency & Idempotency Reviewer | idempotency key/state transition tests |
| Cache, queue, scheduled job, async worker | stale data or replay behavior | Concurrency & Idempotency Reviewer + Observability Reviewer | event order/retry/readback evidence |
| Error code/message mapping | frontend/backend error contract drift | API Contract Reviewer + Evidence Accountant | error contract and failing/negative tests |
| Large query/report/export/search | slow SQL/N+1/missing index | Performance Reviewer | query plan/index/pagination evidence |
| Sensitive data/logging/audit | privacy or compliance issue | Security & Permission Reviewer + Observability Reviewer | redaction/audit log proof |

## Fullstack experience matrix

| Trigger signal | Typical risk | Specialist role | Evidence expected |
|---|---|---|---|
| Frontend and backend both touch the same feature | contract/deploy-order drift | Fullstack Coordination Reviewer | branch/ref map, API contract, deploy order |
| Mock server differs from real backend | false frontend pass | API Contract Reviewer | real API readback or contract fixture |
| Generated client/shared schema changes | type/runtime mismatch | Fullstack Coordination Reviewer | generated artifact/readback and compatibility |
| Feature flag or staged rollout | split-brain behavior | Release Readiness Reviewer | flag matrix and fallback plan |
| Issue closure or release readiness | premature completion claim | Final Certifier | merged PR, issue state, target branch file readback |

## Specialist role additions

These roles are optional specialists. They do not replace the default council roles; they are invoked by L1/L2/L4 routes.

- API Contract Reviewer
- Migration & Data Integrity Reviewer
- Security & Permission Reviewer
- Concurrency & Idempotency Reviewer
- Observability Reviewer
- Performance Reviewer
- Accessibility & Localization Reviewer
- Release Readiness Reviewer
- Fullstack Coordination Reviewer
- Xianggua UI/UX Reviewer
- UIMax Auditor

## Normal-development non-council rule

Do not invoke a full council when:

- direct evidence proves a small deterministic bug;
- no shared state or repeated churn exists;
- a single specialist reviewer can close the risk;
- user explicitly asks for a quick reversible prototype and accepts limited verification.

Instead, use L0 or L1 and keep the output small.

## Escalation rule

Escalate from L1 to L2/L3 when any of these appears:

- more than one writer/controller for the same state;
- specialist reviewers disagree on owner or evidence;
- a fix in one path breaks a contrast path;
- existing issue history shows repeated patching;
- user asks for root cause, final convergence, or release certification.
