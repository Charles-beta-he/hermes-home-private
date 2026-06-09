# General Query Full-Coverage Protocol

Use this reference for project/code/product/document queries, not only PRD status/source audits. A query answer should cover the associated system around the object being queried unless the user explicitly asks for a narrow lookup.

## Default stance

Treat the queried object as an entry point, not the boundary.

- A page implies routes, sidebars, dashboards, services, backend contracts, permissions, tests, and related workflows.
- A field implies producers, consumers, normalization, validation, storage, analytics, and downstream effects.
- A status implies a state machine, queues, KPIs, badges, permissions, actions, and transitions.
- A button/action implies API, GA/MFA/audit, optimistic UI, error paths, permissions, and state synchronization.
- A document/PRD claim implies prototype/current implementation/backend/runtime evidence and conflict resolution.

## Coverage loop

1. **Clarify the object class internally**: page, field, status, action, API, route, workflow, metric, permission, document claim, bug symptom.
2. **Build the关联面 map** before final answer:
   - Canonical source / newest doc / profile / prototype
   - Producers / writers / inputs
   - Transformers / adapters / fallbacks / defaults
   - Consumers / displays / downstream actions
   - Entry points / routes / menus / dashboard cards / deep links
   - Permissions / guards / MFA/GA / audit logs
   - Metrics / badges / counts / reports / exports
   - Tests / fixtures / browser/runtime evidence
3. **Search by both names and semantics**:
   - filenames and route names
   - enum values / labels / i18n text
   - business verbs: submit, approve, reject, review, pending, expire, freeze, export, notify
   - infrastructure verbs: controller, service, repository, migration, summary, count, badge, permission
4. **Classify every nontrivial hit** as producer, transformer, display consumer, action consumer, entry, permission, metric, test, doc/prototype, irrelevant.
5. **Stop only when the map is closed enough** for the question, or explicitly report uncovered surfaces.

## Minimal output contract

For simple query answers, include at least:

- Direct answer.
- Scope actually checked.
- Associated modules/surfaces discovered.
- Any unverified or suspicious surfaces.

For high-risk project queries, include:

- Evidence paths/lines.
- Source-to-sink or page-to-workflow matrix.
- Divergences by doc/prototype/current FE/current BE/runtime.
- Falsifier/test to prove the claim wrong.

## Fail-closed rules

- Do not answer from the named file/page only if related modules can affect the truth of the answer.
- Do not treat UI similarity as business closure.
- Do not treat a KPI/count/badge as aligned until its detail queue/list predicate is compared.
- Do not treat route absence in Sidebar as route absence; inspect route table/direct URL/permissions.
- Do not treat a fallback/default as source-of-truth without verifying producer and backend contract.
- If query budget prevents full expansion, say exactly which associated surfaces were not checked.
