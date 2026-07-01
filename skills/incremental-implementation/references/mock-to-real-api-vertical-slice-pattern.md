# Mock-to-Real-API Vertical Slice Pattern

Extracted from `/Users/charles/.hermes/skills/incremental-implementation/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Mock-to-Real-API Vertical Slice Pattern

Use this when a prototype or mock-heavy page must be converted to production data without destabilizing the surrounding app.

1. Start with the narrowest end-to-end slice that already has a clear backend truth source.
   - Prefer pages where the backend controller / DTO / domain fields already exist.
   - Avoid starting with the visually biggest page if its data contract is still ambiguous.

2. Land the service-layer contract first.
   - Extend the existing frontend service module instead of inventing page-local fetch code.
   - Normalize backend shapes once in the service layer so multiple pages can reuse them.

3. Wire one page at a time.
   - Replace mock data on a single page.
   - Keep the page layout mostly stable; change the data source before redesigning UI structure.

4. Add backend bridging only when needed.
   - If the raw integration client is not suitable for admin/UI use, add a thin admin-facing controller/facade that preserves permission checks and existing response conventions.
   - Prefer reusing existing config storage / audit / GA flows over introducing new schema or ad hoc endpoints.

5. Adapt real backend shapes at the edge, not deep in the UI.
   - If the page already renders against a prototype/mock type, add one adapter function from API DTO → page contract.
   - Preserve existing table/detail rendering first; migrate field truth sources before redesigning component structure.
   - When a placeholder field is derivable but not explicitly returned (for example purpose/source derived from wallet keys, pair presence, or linked journal IDs), centralize that derivation in the adapter instead of scattering heuristics across the page.
   - Treat empty API responses as real state: explicitly clear lists/totals instead of only updating state on non-empty responses.

6. Extract reusable reference components when replacing placeholders across multiple surfaces.
   - If the same placeholder logic appears in both table rows and detail drawers (for example counterparty resolution), factor it into a reusable reference component/helper instead of duplicating click/match heuristics.
   - Prefer a single matching function that checks multiple durable identifiers (name/code/userId/account/address/external payee id) over fragile substring-only matching.

7. Verify both sides immediately after each vertical slice.
   - Run the frontend build/typecheck for the touched app.
   - Run the narrowest backend compile/test command that exercises the changed module graph.
   - If the repo requires a pinned runtime, invoke the build with the repo-declared runtime rather than assuming the shell default is correct.

8. Only then move to the next page.
   - Typical order: service contract → page A → dashboard/summary consumers → neighboring detail pages.

See also: `references/mock-to-real-api-vertical-slices.md` and `references/admin-prototype-to-real-api-page-conversion.md`.
