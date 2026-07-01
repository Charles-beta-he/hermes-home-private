# iOS global keyboard viewport inset for mobile/PWA flow pages

Applicability: mobile web / installed PWA / WebView flow pages where focusing any editable control on iOS shifts the whole fixed app canvas upward or leaves content outside the visual viewport. Use when the requirement says the fix is global, not limited to one transfer/payment page.

Anti-conditions:
- Do not use this for Android system-navigation underlap/over-lift bugs; keep Android visual bottom inset separate.
- Do not change global `--safe-top` / `--safe-bottom` constants before proving the symptom is tied to a focused editable state.
- Do not claim UI acceptance from unit tests only; real iOS browser/standalone evidence is still required for final visual acceptance.

Pattern:
1. Ensure platform/display-mode markers are established before or at app boot (`data-platform="ios|android|other"`, `data-display-mode="standalone|browser"`).
2. Centralize the keyboard measurement in the existing viewport-stability/runtime-layout layer, not in individual screens.
3. Treat editable focus broadly: native `input`, `textarea`, `select`, `contenteditable`, and custom controls with `role="textbox"`.
4. On iOS + focused editable + `visualViewport` shrink, compute `hiddenBottom = innerHeight - visualViewport.height - visualViewport.offsetTop` and write a dedicated token such as `--ios-keyboard-bottom-inset` only when positive.
5. Clear that token on blur, keyboard recovery, route-return settling, page show, and non-iOS paths.
6. Do **not** make a generic `--flow-keyboard-content-reserve` / `scroll-padding-bottom` / auto-`scrollBy` branch the default for all ordinary flow pages. If focusing an input makes the whole page visibly slide upward, treat the reserve/reveal abstraction itself as suspect, not only the affected route. Ordinary flow pages should usually remain pinned between `--safe-top` and `--safe-bottom`; add keyboard handling only after a page-specific ownership problem is proven.
7. For app-owned full-height keyboard shells (chat/support composer pages, login/auth entry pages, or any page where header/brand/FlowNav must stay visible while a bottom or prominent input is focused), do **not** scroll the app-level `[data-screen-scroll]` to reveal the focused field. Put those routes in an explicit pinned-shell allowlist, keep the shell `h-full min-h-0 flex-col overflow-hidden`, make its content/message body the internal `overflow-y-auto min-h-0 flex-1` owner, and on keyboard settle reset the app-level screen scroller to `scrollTop = 0` for focused editables inside that shell. Because iOS can apply the automatic scroll before `visualViewport` reports a measurable keyboard inset, run immediate + delayed reset passes while the pinned shell remains focused; do not gate the scroller reset only on `keyboardInset > 0`. If the user still reports the FlowNav/header missing, treat scroll reset as insufficient: for that route class, pin the outer app `[data-screen-scroll]` between safe areas with `overflow-y-hidden` and no keyboard reserve/scroll-padding, then delegate all scrolling to the inner message/content owner. If the header is still not visibly present in a screenshot, promote the FlowNav/header to its own fixed top layer and reserve its height with top padding on the shell. Before generalizing, inventory all editable routes and classify by layout ownership: only explicit full-height/pinned shells get this treatment; ordinary form/search/amount/address/password pages should not inherit a global keyboard reserve.
8. Preserve Android behavior: if the runtime already has Android visual bottom inset or TabBar top-fallback logic, add the iOS keyboard token beside it, not through generic `--safe-bottom`.
8. Preserve Android behavior: if the runtime already has Android visual bottom inset or TabBar top-fallback logic, add the iOS keyboard token beside it, not through generic `--safe-bottom`.

Regression checklist:
- iOS focused native input sets the keyboard token.
Regression checklist:
- iOS focused native input sets the keyboard token.
- iOS focused custom `role="textbox"` sets the keyboard token.
- Blur/focusout clears the token.
- Android/browser/blurred states leave the iOS token absent/zero.
- Existing Android visual-bottom and TabBar tests still pass.
- Ordinary flow shells/classes do **not** consume a global keyboard reserve token, do not add keyboard-driven `scroll-padding-bottom`, and do not run app-level auto-`scrollBy` reveal logic by default.
- A representative full-height/pinned keyboard shell opts into header preservation and proves: the route is in an explicit pinned-shell allowlist (or focused input lives under `data-keyboard-preserve-header="true"`), the shell is `h-full min-h-0 overflow-hidden`, the internal content area owns scrolling, the composer/input is `shrink-0`/bounded when applicable, and the app-level `[data-screen-scroll]` is either reset to `scrollTop = 0` or, for route classes where the header still disappears, explicitly `overflow-y: hidden` with no keyboard reserve/scroll-padding. If route-level locking still leaves the screenshot ambiguous, make the FlowNav/header a fixed top layer (`fixed inset-x-0 top-[var(--safe-top)] z-40 ...`) and add top padding equal to the header height on the shell. Acceptance evidence must include a real screenshot where the header/title/back/action controls are visibly present and unobscured after focus; DOM rects alone are insufficient, and top install/update/network toasts must be suppressed or dismissed on keyboard-sensitive routes before accepting the result.
- When auditing “other input pages,” classify pages by layout ownership, not just by presence of an `<input>`: ordinary form flows may scroll normally; only full-height app-owned shells need header-preservation opt-in.

- **Do not preserve a broken global flow keyboard reserve just to minimize the diff.** If the observed effect of a generic keyboard reserve / auto-reveal abstraction is page-wide upward sliding, remove or narrow that abstraction first. Route-level exceptions such as `/login` are acceptable as a fast containment step, but final closure should make ordinary flow pages free of the global reserve and keep only explicit pinned-shell behavior.
- Say the code path is global if it is installed in the shared viewport runtime and shared flow shell.
- Label remaining acceptance boundary: real iOS Safari/Home Screen or target WebView screenshots are needed before final UI acceptance.
