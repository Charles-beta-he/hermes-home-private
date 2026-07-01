# Mobile keyboard scroll-owner debugging

Applicability: mobile web / PWA / WebView flow pages where a focused input opens the soft keyboard and the CTA/footer appears roughly correct, but the visible viewport has extra blank/gray space, clipped content, or the page still looks wrong after safe-area constant tweaks.

Anti-conditions:
- Do not apply this to full-height composer/chat shells that intentionally own an internal message scroller and bottom composer; use the composer visual-viewport references for those.
- Do not assume a fix to `data-keyboard-preserve-header` / preserve-shell height affects login or other normal forms unless the route predicate actually returns true for that route.
- Do not tune `--safe-bottom`, `--ios-keyboard-bottom-inset`, or footer padding before proving which element owns scrolling.

Debugging path:
1. Classify the route first:
   - Preserve shell (`shouldPreserveHeaderWhileKeyboardOpenRoute(path) === true`): app shell height should be tied to `visualViewport.height`; only the inner content/activity area scrolls.
   - Normal form (`false`, e.g. login/search/ordinary forms): the app-level `main[data-screen-scroll]` should own the iOS keyboard reserve and reveal behavior.
2. Trace where the keyboard reserve is applied. In many SPA shells it is on `main[data-screen-scroll]` via `pb-[var(--flow-keyboard-content-reserve)]` / `scroll-pb[...]`.
3. Trace the actual scroll owner after focus. Inspect root, app shell, `main[data-screen-scroll]`, page root, and any nested `.overflow-y-auto` for `clientHeight`, `scrollHeight`, `scrollTop`, computed `overflow-y`, and bottom padding.
4. If the route is a normal form but the page root is `h-full/min-h-0 overflow-hidden` and an inner child is `overflow-y-auto`, the keyboard reserve and real scroll owner are split. This can keep the CTA visible while still leaving an apparent extra viewport gap or preventing normal reveal.
5. For normal forms, prefer a single app-level scroll owner: remove the nested locked scroller, use `min-h-full` page content, and let `main[data-screen-scroll]` consume the keyboard reserve. Keep `data-keyboard-preserve-header` absent.
6. For preserve shells, ensure the visual-height formula does not subtract bottom safe-area twice: `visualViewport.height` already excludes the keyboard; the shell height usually subtracts top safe area only, while footer padding owns its own bottom comfort.

Regression checklist:
- A normal form route asserts `shouldPreserveHeaderWhileKeyboardOpenRoute(route) === false`.
- The form input has no ancestor with `data-keyboard-preserve-header="true"`.
- The normal form source/component does not reintroduce nested `overflow-y-auto` or a root `h-full overflow-hidden` lock unless the app-level scroll reserve is intentionally moved to that same scroll owner.
- Preserve-shell routes still assert the route predicate is true and continue using a bounded shell with `min-h-0`, internal scroll area, and shrink/fixed footer.
- Run targeted layout tests plus TypeScript/build, then still require real iOS browser/Home Screen screenshot evidence for final UI acceptance.

Pitfall learned:
A fix that changes preserve-shell height can be correct for P0 amount/remit/payout shells but irrelevant to `/login` when `/login` is deliberately a normal keyboard-reveal route. If the user reports the login screenshot still wrong, re-enter scroll-owner tracing instead of explaining the preserve-shell fix as if it applied globally.
