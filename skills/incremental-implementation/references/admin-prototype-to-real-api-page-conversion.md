# Admin prototype → real API page conversion

Use this when converting an admin/prototype-heavy React page to production data one page at a time.

## Durable patterns from session

1. Keep page rendering contracts stable with an adapter layer
- Build one `adaptXxx(apiDto)` function near the page/service boundary.
- Map backend names to prototype/page names once.
- Put derived fields there too:
  - `request_id`: prefer backend request id, fall back to order id only if absent.
  - `source`: infer from strong signals like pair/channel presence, not ad hoc inline UI checks.
  - `purpose`: infer once from wallet-role keys / transaction linkage when backend does not expose a dedicated enum yet.
  - `linked_txn_id`: preserve journal/ledger linkage because it is critical for admin audit trails.

2. Replace placeholder entity rendering with a reusable reference component
- If both list rows and detail drawers need the same entity lookup, extract a component such as `CounterpartyRef`.
- The resolver should check multiple stable candidate fields:
  - display name
  - internal code
  - user id
  - beneficiary/account holder name
  - bank/wallet/account/address fields
  - external payee/provider ids
- Avoid brittle `slice(0,4)` or single-substring matching as the only strategy.

3. Treat empty API payloads as first-class truth
- On successful fetch with zero items, clear list state and totals.
- Do not leave stale rows on screen just because the previous fetch had data.

4. Preserve UI structure unless product explicitly asks for redesign
- First change data source.
- Then fill prototype-required fields.
- Only after that consider structural UI changes.

5. For admin-facing integrations, add a thin backend bridge when needed
- Do not expose raw integration clients directly to the admin UI.
- Add an admin controller/facade that preserves auth, audit, permission, config, and GA conventions.

6. Verify every page slice with the real build chain
- Frontend: run the app build/typecheck.
- Backend: run the narrowest module compile/test for changed controllers/services.
- If Java/Node/etc. is pinned by repo convention, invoke that runtime explicitly during verification.

## Good fit
- multi-page admin modernization
- mock-to-real API conversion
- prototype parity work with existing layouts
- audit-heavy finance/ops backoffice screens

## Smells
- page-local fetch/transform logic duplicated across pages
- placeholder string matching embedded in multiple render functions
- successful empty responses leaving stale previous rows on screen
- backend DTO quirks leaking directly into JSX conditionals
