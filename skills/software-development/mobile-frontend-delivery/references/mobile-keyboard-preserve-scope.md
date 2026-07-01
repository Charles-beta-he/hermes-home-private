# Mobile keyboard preserve-header scope

Applicability: mobile/PWA flow pages where focusing an input opens the soft keyboard and there is pressure to keep a header/FlowNav visible. Use this when debugging CTA/input obstruction, iOS keyboard scroll, or customer-support composer regressions.

Anti-conditions:
- Do not apply `data-keyboard-preserve-header="true"` to ordinary forms, login pages, amount inputs, search inputs, or normal flow pages just because they contain an input.
- Do not route-opt-in `/login` or amount-entry routes to composer-shell preservation unless the screen is actually a full-height shell with its own internal scroll/composer ownership.

Pattern:
1. Before editing, run a light iceberg scan for the keyboard symptom: classify the reported route, route predicate, app-level scroll owner, nested scroll owners, keyboard/safe-area tokens, shared shell/components, and adjacent recent commits. Do not fix the first visible layer until the scroll ownership chain is closed.
2. Classify the page before editing:
   - Full-height composer shell: fixed FlowNav/header + internal message/activity scroller + bottom composer. These may opt into `data-keyboard-preserve-header="true"` and route-level `shouldPreserveHeaderWhileKeyboardOpenRoute(...)`.
   - Normal form/amount/search flow: app-level screen scroller should remain scrollable, but must not globally add focus-driven keyboard `pb`/`scroll-pb` reserves. Let the browser native caret reveal handle ordinary inputs; app-driven keyboard reserve on normal pages can create first/second focus drift.
2. For normal flow pages, preserve native scroll reveal. Do not use the preserve-header marker or global keyboard padding to force outer scrolling; both can introduce keyboard/input accessory bar drift or inconsistent refocus geometry.
3. For composer pages, verify the marker is on the shell that owns the internal scroller, not on reusable input primitives.
4. For bottom-CTA / “Next” flow pages, do not equate a bottom button with a composer shell. If the page is still `FlowNav + content + CtaBlock mt-auto` / `min-h-full`, first convert it to a height-bounded shell with an internal scroll owner and `shrink-0` footer before enabling preserve-header behavior for the route. A broad input-level marker can freeze the outer scroller while the CTA or middle content still belongs to the wrong scroll owner.
5. After any change, grep for the marker and route predicate to confirm blast radius. The marker should remain on composer shells only unless a new full-height shell is intentionally added.
6. Add regression tests for both sides:
   - Normal form route/input: `closest('[data-keyboard-preserve-header="true"]')` is null and CTA still renders.
   - Composer route: marker still exists and chat/AI tests still pass.

Verification checklist:
- Targeted form/page test for the reported input route.
- Composer regression tests for customer chat/AI if those pages are in scope.
- Safe-area/layout predicate test that `/login` and other normal flow routes are false, while true composer routes remain true.
- For “first focus OK, blur then second focus drifts upward” regressions, test stale scroll cleanup after blur across `window.scrollY`, `document.documentElement.scrollTop`, `document.body.scrollTop`, `visualViewport.offsetTop`, and the app-owned `[data-screen-scroll].scrollTop`; ordinary focused inputs may skip reset while focused, but blur settlement must clear all outer scroll containers before the next focus. Include a quick-refocus timing regression: if blur cleanup waits only for a late single timer (for example 250ms), the input can refocus first and make cleanup no-op; blur should schedule an immediate pass plus delayed tails, and app-scroller reset should be scoped to keyboard dismiss rather than generic route/resize settles.
- TypeScript check.

Why this matters: `data-keyboard-preserve-header` is a powerful opt-in that tells viewport stability code to treat the focused input as a header-preserving shell and reset/lock the outer scroller. Broadly applying it to shared inputs (for example amount inputs) or ordinary login forms turns off the normal keyboard reveal behavior and can hide the primary CTA behind the iOS keyboard.
