# Mobile composer flex-height diagnostics

Scope: class-level mobile frontend layout procedure. This reference applies to generic mobile H5/PWA chat, support, assistant, comment, and messaging composers. It intentionally contains no project-specific paths, brands, URLs, branches, or task outcomes.

Applicability: use when a mobile H5/PWA screen shows an abnormal tall white bottom composer area with a one-line text field or textarea next to a send/action button.

Anti-conditions: do not use as the primary path when the keyboard is open, when native system bars clip the composer, or when the product intentionally uses a large rich editor by default.

## Debugging path

1. Locate the exact route/component from visible copy. Do not patch only the parent hub if the defect is on a nested chat/support screen.
2. Inspect the vertical flex ownership chain:
   - outer screen root: `h-full`, usually `min-h-0 overflow-hidden`;
   - message/list scroll owner: `flex-1 min-h-0 overflow-y-auto`;
   - composer container: `shrink-0`;
   - textarea/input: explicit one-row height matching the action button, commonly 40-48px.
3. If the textarea should grow for multiline input, implement controlled auto-resize:
   - reset inline height to the base height before measuring;
   - set height to `clamp(scrollHeight, baseHeight, maxHeight)`;
   - enable vertical scrolling only at the max height;
   - after send/clear, reset value and height to the base height.
4. Avoid arbitrary bottom padding or generic safe-area constant changes. Those hide a flex ownership problem and can regress installed PWA or tabbar layout.
5. If the screenshot is specifically an installed iOS PWA with a large blank band *below* an otherwise compact input row, check safe-area ownership before more textarea fixes:
   - inspect the parent app/screen shell for `bottom-[var(--safe-bottom)]`, `padding-bottom: var(--safe-bottom)`, or equivalent safe-area reservation;
   - if the parent already owns the bottom safe area, nested chat/assistant composers must not also use raw `env(safe-area-inset-bottom)` or `pb-[calc(env(safe-area-inset-bottom,...)+...)]`;
   - prefer a fixed visual composer padding such as `pb-3` while leaving the parent shell as the single safe-bottom owner;
   - keep this scoped to nested flow composers. Do not remove raw safe-area handling from global bottom sheets, TabBars, or overlays unless their parent ownership is separately proven.

## Regression test shape

Component/unit:
- Assert the composer has `shrink-0`.
- Assert the textarea has base height, min/max height, `rows=1`, and hidden overflow.
- Mock `scrollHeight`, fire multiline input, and assert it grows only to the measured/clamped height.
- Click/send and assert textarea value and height reset to the base height.
- For installed-PWA safe-area regressions, assert the nested composer does **not** carry raw safe-area bottom padding when the parent shell already owns `--safe-bottom` (for example `not.toHaveClass('pb-[calc(env(safe-area-inset-bottom,0px)+10px)]')` and positive fixed padding such as `pb-3`).
- Scope: mobile chat/support/assistant composer fixes in existing applications. Applicability: when adding layout regression coverage to a component that already has tests for adjacent behavior such as config loading, polling, media upload, or error handling. Anti-condition: do not replace those existing behavior tests with narrow layout-only tests; preserve them and add composer assertions/imports incrementally.
- If multiple user journeys enter different composer components, audit and test each concrete route/component. A fix on one nested composer does not prove another composer route.

Browser/visual proof:
- Use a mobile viewport.
- Bypass splash/loading if it overlays the page during screenshot verification.
- Stub only unrelated API calls needed to render the screen; do not treat mocks as product/backend proof.
- Read `getBoundingClientRect()` for composer, textarea, and send button. Healthy relationship: empty textarea height approximately equals action button height; composer height approximately equals button height plus padding/safe-area; no large blank white region remains under the field.
- After a PR/deploy landing, verify the served bundle or online artifact contains robust fix markers such as stable test IDs/classes used by the composer contract. Treat this as deploy-freshness evidence only; final UI closeout still needs real mobile/PWA visual evidence when the task requires it.
