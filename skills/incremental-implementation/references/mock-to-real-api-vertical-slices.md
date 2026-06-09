# Mock-to-Real-API Vertical Slices

Condensed pattern from a fullstack admin integration session where mock/prototype pages were converted to real APIs across separate frontend and backend repos.

## When this pattern fits
- Admin/prototype pages already exist visually
- Data is still mocked or partially stubbed
- Backend truth sources exist, but frontend contracts are incomplete
- Work spans service layer, pages, and possibly a thin backend bridge

## Recommended order
1. Find the page with the clearest existing backend truth source.
2. Extend the existing frontend service module first.
3. Replace mock data on that single page.
4. Reuse existing backend permission/config/audit/GA flows where possible.
5. Add a thin backend admin-facing bridge only if the raw integration/domain API is not directly UI-safe.
6. After the page works, wire secondary consumers such as dashboard summary tiles.
7. Continue to adjacent detail pages.

## Practical heuristics
- Prefer shared service adaptation over page-local response mapping.
- Prefer adding one reusable endpoint over sprinkling multiple page-specific fetches.
- Keep UI structure stable during the first data-source swap; reduce layout churn while contracts are still settling.
- When multiple repos are involved, verify the touched frontend and backend in the same slice before moving on.

## Verification pattern
- Frontend: build/typecheck the touched app immediately after the slice.
- Backend: compile or test the narrowest affected module graph.
- If build failures smell like toolchain/runtime mismatch rather than code errors, retry with the repo-declared runtime before diagnosing the code itself.

## Good slice examples
- Add reserve-summary service method → wire ChannelReserve page → build frontend → compile admin backend module
- Reuse reserve-summary service in Dashboard warning tile → build frontend again

## Anti-patterns
- Starting with the broadest page just because it is most visible
- Embedding fetch/shape adaptation directly inside page components
- Adding new schema/config storage before checking whether an existing admin config mechanism already fits
- Declaring backend code broken before ruling out repo runtime mismatch
