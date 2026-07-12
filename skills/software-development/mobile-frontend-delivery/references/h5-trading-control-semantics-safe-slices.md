# H5 trading/control semantics safe slices

Use this reference when advancing mobile H5/native-parity work on transaction-like screens (spot trading, contract trading, order books, balances, transfer/deposit entry points, drawers, selectors, sliders) without authenticated credentials or real side effects.

## Applicability

Apply when:
- The user asks to keep pushing local H5/native-app parity in safe reversible slices.
- The screen contains trading/order/balance controls where native parity, touch targets, and accessibility matter.
- You can verify anonymous/read-only behavior through local preview, CDP, screenshots, scoped lint/build, and SSOT evidence.

Anti-conditions:
- Do not use this to claim authenticated trading, transfer/deposit, order cancel, production, push/deploy, real-device, PWA install, or Android/iOS native parity.
- Do not create real orders, cancel orders, mutate funds, read/session-copy tokens/cookies, or infer authenticated state from anonymous smoke tests.
- If the next control needs account data or a real mutation, stop at a human/fixture/auth lane decision instead of silently downgrading.

## Slice selection pattern

1. Prefer controls whose product behavior is already present but implemented as non-semantic click targets:
   - pair/drawer trigger and drawer list rows
   - buy/sell tabs
   - orderbook price rows and latest price
   - depth, order-type, margin-mode, and advanced-order selectors
   - percentage sliders/range inputs
   - history/transfer/deposit entry points
   - bottom tabs and orderbook view-mode toggles
2. Convert only the narrow target:
   - `div onClick` -> `button type="button"` when it is an action.
   - Add `aria-label`, `aria-pressed`, `aria-expanded`, or `aria-haspopup` that describes the product action/state.
   - Add `border-0 bg-transparent p-0 text-left` or equivalent to avoid browser button chrome changing the mobile screenshot.
   - For nested star/favorite buttons inside clickable rows, stop propagation and give the star its own label so row selection and favorite mutation do not conflict.
   - For MUI Select, label both the hidden input and visible combobox when needed (`inputProps` plus `SelectDisplayProps`). Verify the visible `[role="combobox"]` carries the label; some renders will not expose the same label on an input.
   - For MUI Select smoke behavior, keyboard focus + ArrowDown/Enter is often more deterministic than mouse-clicking a portaled option in headless Chrome; record the exposed options, selected text change, and product-state result (market hint, margin mode, drawer close, etc.).
   - For native invisible depth/precision `<select>` controls, add an `aria-label` directly on the `<select>`, verify tag/label/visibility/option count, and choose the next option by value rather than assuming a fixed option index differs from the current value.
   - Contract trading pages often have a dense safe-slice ladder that can be drained without credentials: pair drawer trigger/rows, margin mode select, order type select, advanced-limit select, depth select, orderbook view-mode toggle, and transfer drawer entry. Keep each patch one-control wide.
   - For orderbook view-mode toggles, convert icon-only clickable containers to `button type="button"`, expose `aria-label` with the current mode (e.g. buy+sell/buy/sell), and use `aria-pressed` for non-default states; verify label and pressed state change after click.
   - For transfer/deposit entry points that only open a drawer, verify the entry is a semantic button and that opening the drawer does not submit transfer/order mutations. Evidence should assert drawer title/expected fields and negative API patterns for transfer/order/password/funds endpoints.
   - For MUI Slider, verify the generated range input has the intended aria label and min/max; do not assume a `role="slider"` selector will be present in every render.
3. Preserve native-route/business identity fields already flowing through the page; do not strip symbol/tradeName/tradeId-style query contract fields. Redact such quasi-identifiers in evidence.

## Verification checklist

For every slice, collect fresh evidence before committing:

- Scoped static check: targeted eslint for touched files.
- Build: full app build, accepting only known non-blocking chunk/Browserslist/PWA warnings.
- Mobile smoke: 390x844 (or project-standard) local preview through Chrome/CDP.
- CDP target discipline: select the page target by the expected app origin/path and assert `location.href`; do not inspect an extension/background target.
- DOM semantics: tag/type/aria/state readback for the exact changed control.
- Behavior: click/change the control and assert the original product behavior still happens (drawer closes, tab changes, query syncs, price fills, selector value changes, login boundary opens, etc.).
- Negative evidence: no credential/session read, no real order, no password/order/funds mutation API, no forbidden authenticated request for anonymous-only slices.
- Visual evidence: screenshot/vision check that mobile layout did not pick up default button/select styling and did not break form/orderbook/footer layout.
- SSOT: write evidence under the project workflow/profile area, not the business repo, unless the project explicitly stores test artifacts in-repo.
- Local commit: commit the product code only after evidence is written/read back.
- Independent verifier: dispatch verifier for L3 promotion; until it returns APPROVE, state the slice as L2/local-loop-verified only.

## Boundary decision point

After draining anonymous/read-only semantic slices, stop and ask for an explicit lane rather than faking progress:

- Auth-free UI-only lane: continue anonymous/read-only semantic polish.
- Fixture lane: create local-only mocked data for order rows/cancel buttons without real API mutation.
- Authenticated lane: human logs in; the agent must not read/save/repeat credentials or session tokens.
- Verifier lane: pause new slices and process APPROVE/AMEND results.

Use a DecisionPacket + ContinuationPacket when the next meaningful work crosses auth, fixture, real mutation, push/deploy, production, device, or PWA-install boundaries.
