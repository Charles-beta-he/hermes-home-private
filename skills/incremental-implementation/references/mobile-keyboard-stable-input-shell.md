# Mobile keyboard-stable input shell slice

## Applicability

Use for mobile H5/PWA/RN-web routes where focusing an input/textarea causes the page header/FlowNav, logo, or composer area to be pushed away by the soft keyboard, especially on iOS Safari/Home Screen.

Typical targets:
- Chat/AI composer pages with bottom textarea input.
- Search/input pages under a FlowNav header.
- Auth/login/setup forms with prominent header/branding that must remain stable during keyboard focus.

## Anti-conditions

- Do not apply blindly to ordinary long form pages where app-level scrolling is desired to reveal many fields.
- Do not replace visual/device acceptance with DOM-only assertions when the user asks for A+/uIMax/pixel acceptance.
- Do not mutate global safe-area tokens for platform-specific keyboard behavior; keep keyboard/safe-area deltas behind scoped route/layout flags.

## Pattern

1. Identify the routes/components with native `<input>`, `<textarea>`, `contenteditable`, or `role="textbox"` that share the same keyboard symptom.
2. Add or reuse a route-level classifier such as `shouldPreserveHeaderWhileKeyboardOpenRoute(pathname)`.
   - Include every route that opts into the stable shell.
   - Keep the classifier explicit and tested so future input pages do not silently drift.
3. For each stable-shell route:
   - Wrap the page root in `data-keyboard-preserve-header="true"`.
   - Use a full-height pinned shell: `h-full min-h-0 flex-col overflow-hidden`.
   - If the page has a FlowNav/header, render it in a fixed header container at `top-[var(--safe-top)]` with app max width.
   - Add top padding equal to the header height, usually `pt-[52px]`.
   - Move page content into an inner `min-h-0 flex-1 overflow-y-auto` scroller.
   - For bottom composers, make the composer `shrink-0`; keep multiline textareas at one-row default height and only grow on actual multiline input.
4. Keep global viewport/runtime logic generic:
   - Detect focused editable elements broadly (`input`, `textarea`, `select`, `contenteditable`, `role="textbox"`).
   - If focused inside `[data-keyboard-preserve-header="true"]`, reset the app-level screen scroller instead of scrolling the whole page.
   - Let the inner page/message scroller own movement.

## Verification checklist

- Unit/static tests assert the route classifier includes every newly synced input page and excludes unrelated pages.
- Component tests assert the focused input is inside `[data-keyboard-preserve-header="true"]`.
- Component tests assert fixed header container classes, full-height shell classes, and inner scroll container exist.
- Regression tests for existing composer pages still pass.
- Run TypeScript/build or the project’s relevant frontend gate.
- If claiming visual quality, add real browser/device screenshot evidence in addition to DOM tests.

## Pitfalls

- Fixing one input page (for example chat) but leaving sibling input/search pages with the old app-level scroll behavior creates inconsistent UX; scan for all input/textarea routes before finalizing.
- A `--runInBand` flag is Jest-specific and may fail on Vitest v4; run Vitest without it unless the repo defines an equivalent option.
- Waiting for async service calls in added tests avoids React `act(...)` warnings when the component fetches config after mount.
