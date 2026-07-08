# Frontend / Backend Trigger Map

Version: 1.2.0

Scope: practical trigger map for routing normal frontend, backend, and fullstack development experience into specialist roles or council escalation.

Applicability: use during debugging, code review, implementation planning, issue triage, and release closeout.

Anti-condition: this file is not a universal checklist that must run on every task; use the smallest route that covers the real risk.

## Frontend trigger map

### UI interaction / state

Trigger signals:
- focus, keyboard, scroll, sheet, modal, drawer, dropdown, tab, toast, loading, empty state;
- user path works in one scenario but fails in a contrast scenario;
- component state, store, URL, cache, and DOM effects all touch the same value.

Default route:
- Product Standard Reviewer
- Ownership Auditor if multiple writers exist
- Regression Designer for user paths and contrast paths

Proof:
- screenshot or DOM/readback evidence;
- keyboard/focus path evidence for interactive controls;
- no console/runtime errors for UI acceptance claims.

### API-rendered UI

Trigger signals:
- field rename, null/undefined, optional value, enum unknown, list pagination, sorting, filtering;
- mock and live API drift;
- frontend invents fallback business state.

Default route:
- API Contract Reviewer
- Evidence Accountant
- Regression Designer

Proof:
- API contract or fixture;
- live/stubbed response readback;
- tests for null/empty/unknown enum and happy path.

### Visual polish and UI/UX taste

Trigger signals:
- user asks for A+, uIMax, high-polish, not ugly, premium, professional, benchmark, design-system consistency;
- new dashboard/control panel/mobile shell/landing page;
- screenshot acceptance matters.

Default route:
- Xianggua UI/UX Reviewer for taste and scenario-fit review;
- UIMax Auditor for evidence-backed scoring;
- Accessibility & Localization Reviewer for controls/forms/navigation.

Proof:
- screenshot matrix;
- visual hierarchy / spacing / typography / density notes;
- accessibility/keyboard/contrast evidence;
- console health.

## Backend trigger map

### API and DTO

Trigger signals:
- endpoint added/changed;
- DTO/request/response/schema changes;
- error code/message changes;
- pagination or filtering changes.

Default route:
- API Contract Reviewer
- Security & Permission Reviewer when endpoint is user/role-sensitive
- Fullstack Coordination Reviewer when frontend also changes

Proof:
- request/response contract;
- tests/readbacks for success, business error, auth error, server error;
- backward compatibility note.

### Database and migration

Trigger signals:
- entity/table/column/index/constraint/native query changes;
- enum/status/data migration;
- validation rule changes with existing data impact.

Default route:
- Migration & Data Integrity Reviewer
- Release Readiness Reviewer if deploy order matters

Proof:
- migration exists;
- schema/query compatibility;
- duplicate migration/version check where applicable;
- rollback or forward-only note.

### Side effects, concurrency, and jobs

Trigger signals:
- payment/order/remit/card status;
- webhook/callback/retry/queue/job;
- user can submit twice;
- external provider involved.

Default route:
- Concurrency & Idempotency Reviewer
- Ownership Auditor for state machine owner
- Observability Reviewer for trace/audit proof

Proof:
- idempotency/retry/ordering tests or reasoning;
- state transition table;
- logs/metrics/audit events where appropriate.

## Fullstack trigger map

Trigger signals:
- frontend and backend change same feature;
- deploy order matters;
- feature flag or API version compatibility matters;
- generated client/shared schema changes;
- issue can only be closed by both UI and API evidence.

Default route:
- Fullstack Coordination Reviewer
- API Contract Reviewer
- Release Readiness Reviewer
- Final Certifier for closeout

Proof:
- remote refs/branch tips when shared branches are involved;
- frontend build/test evidence;
- backend test/API evidence;
- contract fixture or live readback;
- issue/PR/target branch readback when closing.

## Council escalation

Escalate to root-cause council if:

- frontend and backend disagree on owner;
- a frontend patch hides a backend contract bug;
- backend changes force frontend special cases;
- multiple controllers can mutate the same status/error/release/notification value;
- repeated fixes exist.
