# Backend-existing / frontend-unwired analysis

Use this when the user asks which backend logic already exists but is not wired into an admin/frontend module, especially when they add a constraint like "directly connect it without changing UI/functionality".

## Goal

Produce an integration classification, not a generic gap list:

1. Already wired: backend endpoint/service exists and current frontend module calls it.
2. Directly wireable without UI change: frontend already has a matching interaction/state, but it still calls a mock/local helper/legacy endpoint. Replace the backing service call only.
3. Backend-orchestration needed: backend capability exists, but frontend lacks required sensitive fields, permission semantics differ, or direct browser calls would leak/overexpose data. Keep UI unchanged and wrap it behind the existing domain endpoint.
4. UI/feature change required: backend has useful data, but the current page has no control, table column, tab, or affordance for it. Do not classify as direct wiring under a no-UI-change constraint.
5. Out of module scope: already wired elsewhere (e.g. detail page), or belongs to another admin module.

## Evidence collection pattern

- Read the current page/component to find actual user interactions and current service calls.
- Read the frontend service module to enumerate available client wrappers and endpoint paths.
- Read the backend controller(s) and permission annotations for corresponding paths.
- Search frontend usages of each service wrapper to distinguish "service exists" from "module actually uses it".
- Search local mock/fallback helpers in the target page: in-memory audit, empty mock functions, prototype stores, hard-coded dates, local toast-only actions.

## Classification heuristics

- Directly wireable when the UI affordance already exists and the backend endpoint accepts the same identifiers the UI already has.
- Backend-orchestration needed when the backend endpoint requires full PII/card numbers/tokens that the page should not expose, or when permissions differ from the current UI action permission.
- UI change required when wiring would require adding a new filter, KPI, tab, drawer, table column, or action button.
- Prefer preserving existing route/button/modal labels and swapping only the service implementation when the user explicitly says not to change admin UI/functionality.

## Reporting format

For each candidate, report:

- Current frontend behavior and file/function.
- Backend existing logic and endpoint/controller.
- Whether it is direct, backend-orchestrated, UI-change, already wired, or out-of-scope.
- Why, including permission/identifier/data-sensitivity constraints.
- Recommended priority and a safe migration path with fallback if applicable.

## Pitfalls

- Do not equate "frontend service wrapper exists" with "the page is wired"; verify component usage.
- Do not call sensitive backend endpoints directly from the browser if they require data not already safe to display in the UI; wrap in the domain backend endpoint.
- Do not add UI affordances when the constraint is "without changing UI/functionality"; mark those as not directly wireable.
- For PII audit, distinguish local in-memory/toast audit from backend `audit_event` or security-event persistence.
