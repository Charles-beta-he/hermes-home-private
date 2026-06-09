# Status / Source Full-Coverage Audit

Use this reference when a user asks whether a status column, source field, badge, queue, KPI, or PRD state is aligned. Treat the field/status as a workflow contract, not as one page's UI text.

## Iceberg framing

1. Event/UI layer: visible tag, column text, badge, table row.
2. Pattern layer: where the same state is filtered, counted, sorted, exported, or reused.
3. System layer: producers, state machine, queues, route entries, permissions, KPIs, downstream unlock/lock actions.
4. Mental-model layer: why the product wants this state and who must act on it.

Do not conclude at layer 1. A status/source audit is incomplete until layers 2-4 have been checked or explicitly ruled out.

## Mandatory source-to-sink matrix

For each PRD status/field, fill these rows:

| Dimension | Required evidence |
|---|---|
| Canonical requirement | Latest PRD/profile line, status enum, business meaning |
| Producers | User/PAD/admin/backend job/webhook/API/migration paths that write or derive the state |
| Backend contract | Controller/service/domain/repository/DTO/schema/enum and default/fallback behavior |
| Frontend normalization | service/store/adapter/type/i18n/render mapping and unknown-state fallback |
| Display consumers | list/detail/dashboard/widget/drawer/tab/table/mobile/empty states |
| Action consumers | filters, sort priority, review buttons, GA/MFA actions, export/report/notification |
| Route/entry points | App routes, Sidebar, WorkspaceTabs, Dashboard cards, direct URLs, breadcrumbs |
| Permissions | view/action perms for visibility, clickability, mutation, direct route access |
| KPI/badge口径 | dashboard summary, sidebar badge, tab counts, list total, backend count source |
| State transitions | legal transitions, illegal transition rejection, after-action synchronization |
| Downstream effects | account locks/unlocks, funds outflow, card activation, CS visibility, audit logs |
| Falsifiers/tests | static check, API count comparison, fixture/browser/permission tests |

## Default search expansion

When the starting point is a page column, do not only search that page. Search by:

- enum values and labels: e.g. `AUTO_PASSED`, `SUBMITTED`, `待复核`, `已提交`
- field names and aliases: e.g. `kycStatus`, `kycLevel`, `status`, `source`
- workflow words: `review`, `pending`, `queue`, `case`, `decide`, `approve`, `reject`
- entry/KPI words: `Dashboard`, `MetricTile`, `badge`, `count`, `summary`, `Sidebar`, `WorkspaceTabs`, route paths
- backend words: controller, DTO, service, repository, migration, enum

Every match must be classified as producer, normalizer, display consumer, action consumer, KPI, route/entry, permission, test, or irrelevant. Unclassified matches mean the audit is not finished.

## Falsifier gates

Fail the audit if any of these hold:

1. A PRD status appears in one source but not in backend enum, frontend type, renderer, and test/fixture coverage.
2. A Dashboard/sidebar/tab/list count uses a different predicate from the queue/list it claims to summarize.
3. A page displays a state but no route/queue/action exists for the operator who must handle it.
4. Hiding a Sidebar item still leaves a direct URL reachable without the expected route/action permission.
5. Unknown or legacy states fall back to a misleading success label (for example treating unknown KYC as normal).
6. A backend field alias or frontend fallback masks source-of-truth drift instead of surfacing it.
7. A status-triggered downstream lock/unlock/audit effect is claimed but no backend action/log path is found.

## Output contract

A complete answer should include:

- Canonical source and newest-source decision.
- Source-to-sink matrix or concise equivalent.
- Divergences separated by PRD/prototype/current frontend/current backend.
- At least one falsifier/test path for the highest-risk state.
- Explicit uncovered risk list if runtime/browser/backend validation was not performed.

## UVISA KYC example anchors

- Prototype PRD says DashboardPage includes KYC pending widget and data source is `DASHBOARD_METRICS` derived from `KYC_CASES` / related lists.
- Prototype `DashboardPage` has `待复核 KYC` tile and lower quick-list; both link to `/kyc`.
- Prototype `/kyc` pending tab includes `AUTO_PASSED` and `SUBMITTED`.
- Prototype Sidebar intentionally does not expose KYC review directly; entry is Dashboard card or direct URL with permission.
- Current uvisa-admin kept the Dashboard tile and `/kyc` route, but its lower quick-list may be an empty placeholder unless wired to real KYC cases. Verify before closing.
