# PWA login keyboard + CTA layout

Applicability: mobile/PWA auth entry screens where the default design wants a full-height welcome/login surface with a bottom CTA, but focusing the primary input should not make the page visibly slide upward or trigger global keyboard reserve behavior.

Anti-conditions:
- Do not apply this to long ordinary forms that need natural browser reveal scrolling.
- Do not apply this to chat/assistant composer shells that need an internal message-list scroll owner and a keyboard-preserve header shell.
- Do not blindly implement a user-suggested mechanics change (for example “move the button below the input on focus”) before checking whether the interaction model is stable; first pick the best model for the class of screen.

Best model:
1. Keep the auth page as a full-height flex surface so the default CTA remains bottom-aligned.
2. Wrap the input, hint, inline CTA, and bottom CTA in a single `group flex flex-1 flex-col` region.
3. Render two CTAs with CSS-only visibility:
   - inline CTA under the input: `mt-6 hidden group-focus-within:block`
   - bottom CTA: `mt-auto pt-8 group-focus-within:hidden`
4. Keep focus movement inside the same group so tapping/clicking the inline CTA does not blur the input and immediately move the button away.
5. Avoid React focus state + blur `setTimeout` for layout switching; it creates mobile click races and makes the button jump on blur.
6. Do not add `data-keyboard-preserve-header` to the login form unless it is actually a full-height composer shell with an internal scroll owner.
7. Do not solve the login case with global keyboard reserve (`--flow-keyboard-content-reserve`), scroll-padding, or JS `scrollBy`/`scrollIntoView`; these make the app-level page slide and often double with the browser’s own input reveal.
8. If the route-level shell must be pinned to prevent app-level movement, classify `/login` explicitly in the shared route/layout predicate while keeping composer internals separate.
9. Route-level pinning alone may not protect the focused input: if the viewport runtime only recognizes `[data-keyboard-preserve-header="true"]`, the login input still behaves like an ordinary focused field during blur/refocus. Add a distinct auth marker such as `data-keyboard-pinned-surface="true"` on the login root and teach the viewport-reset path to treat both composer shells and auth pinned surfaces as keyboard-pinned for stale-scroll cleanup. Keep tests asserting login does not use the composer marker.
10. On iOS second-focus bugs, reset stale offsets synchronously on focus/refocus for the pinned surface: `window.scrollY`, `documentElement.scrollTop`, `body.scrollTop`, and `[data-screen-scroll].scrollTop`. Do not reintroduce global reserve or `scrollBy`; the goal is to clear leftover WebKit reveal state, not to animate/avoid the keyboard manually.

Verification checklist:
- Default state: one visible bottom CTA is bottom-aligned by `mt-auto` in the full-height layout.
- Focus-within state: inline CTA under the input becomes visible and bottom CTA is hidden by CSS, not React blur timers.
- The login screen source does not contain `data-keyboard-preserve-header` or internal `overflow-y-auto` unless the design truly changed to a composer shell.
- Search/build output confirms global flow keyboard reserve is not emitted when the fix removes it.
- Focused tests cover the login structure and route/layout predicate.
- Build passes; real iOS Safari/Home Screen PWA screenshot remains the final visual acceptance boundary.

PR/branch hygiene note:
When landing this from a dirty PWA branch into a shared test branch, create a clean worktree from `origin/<target>`, apply only the auth-keyboard semantic hunk, run focused tests/build there, then open/merge the PR. Do not forward-port broad unrelated safe-area/theme/runtime diffs from the dirty source branch.
