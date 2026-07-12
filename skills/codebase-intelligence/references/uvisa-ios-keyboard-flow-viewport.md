# UVISA iOS keyboard flow-page viewport debugging

Applicability: UVISA C-end/PWA tasks where iOS soft keyboard opens on a non-tab FlowNav page (remit/payout/transfer/payment/security) and the whole page shifts upward, top content leaves the visible viewport, bottom CTA/input is covered, or layout differs between Safari and installed PWA.

Anti-conditions:
- Do not apply to TabBar-only safe-area issues without an active input/textarea.
- Do not treat this as a backend/API defect unless the visible symptom includes failed requests or contract errors.
- Do not store one task ID as truth; re-check current code and git history every time.

## Intake from Lark screenshot

If Lark OAuth/API access is blocked but the user provides a task screenshot, proceed from the screenshot instead of stalling:
1. Extract platform, route/path words, reproduction steps, and expected vs actual behavior from the image.
2. Map visible product terms to route families: `资产 → 转出 → 国际汇款` usually maps to `src/screens/remit/*`; `链上提现` to `src/screens/payout/PayoutCryptoScreen.tsx`; `快捷转账` may exist only in history/branch if recently reverted.
3. Mark missing Lark comments/attachments as an evidence gap, not a blocker, when the screenshot contains enough acceptance atoms.

## Code surfaces to inspect

1. App shell/scroll geometry:
   - `src/components/PhoneCanvas.tsx` for `h-dvh` / app canvas and `overflow-hidden`.
   - `src/index.css` for `html, body, #root` fixed/hidden rules, safe-area vars, `--app-visual-height`, and keyboard-related vars.
   - `src/App.tsx` for `main[data-screen-scroll]`, `screenScrollInsetsClass(isTabPage)`, route registration, and `ScrollReset`/viewport settle calls.
2. Shared bottom CTA:
   - `src/components/CtaBlock.tsx`; `mt-auto` bottom CTAs inside `flex flex-col min-h-full` can force iOS to document-scroll when a field near the bottom focuses.
3. Target screens:
   - Remit amount: `src/screens/remit/RemitAmountScreen.tsx` amount inputs.
   - Remit preview: `src/screens/remit/RemitPreviewScreen.tsx` note/message input.
   - Crypto payout: `src/screens/payout/PayoutCryptoScreen.tsx` amount input and address textarea.
   - Internal/quick transfer: search git history for `src/screens/transfer/*`; it may have been promoted and reverted.
4. Existing viewport runtime:
   - `src/lib/viewportStability.ts` often handles route settle, safe-area reconciliation, Android visual bottom insets, and keyboard-dismiss stray scroll. Check whether it intentionally no-ops while an editable element is focused; if so, it does not solve keyboard-open layout.

## Root-cause pattern

The common chain is:

`PhoneCanvas h-dvh overflow-hidden` + `html/body fixed overflow:hidden` + app-owned `main[data-screen-scroll]` + non-tab flow pages with only `safe-bottom` reservation + `flex flex-col min-h-full` + bottom CTA `mt-auto` + iOS soft-keyboard document-scroll behavior.

When an input/textarea focuses, iOS reduces `visualViewport.height` and may shift/scroll the document to reveal the caret. If the app does not translate that into an internal scroll-container keyboard inset, the whole canvas appears to move upward and top content can leave the visible viewport.

Existing `resetStrayWindowScroll()`-style fixes usually run only when no editable element is focused; they unwind after keyboard dismissal but do not preserve layout while the keyboard is open.

## Git history checklist

Run history over both route screens and shell/runtime files:
- `git log --all --grep='t104xxx\|keyboard\|viewport\|safe-area\|iOS\|payout\|remit' --oneline`
- `git log --all -- src/App.tsx src/index.css src/lib/viewportStability.ts src/components/PhoneCanvas.tsx src/components/CtaBlock.tsx src/screens/remit src/screens/payout src/screens/transfer`
- If a feature is absent on current `origin/main`, check commits that added/reverted it (`git show --stat <commit> -- src/screens/transfer src/App.tsx`).

Classify:
- No task-specific commit found → likely missing keyboard-open adaptation.
- Viewport commits only mention tabbar/safe-area/cache/keyboard-dismiss → adjacent mitigation, not closure.
- Feature promoted then reverted → include it in impact if re-enabled, but do not claim current production exposure.

## Recommended fix shape

Prefer a reusable keyboard-aware flow layer over per-input `scrollIntoView` hacks when the same symptom spans multiple flow pages:
1. Add a small runtime/hook that listens to `focusin`, `focusout`, `visualViewport.resize`, and `visualViewport.scroll`.
2. While iOS/mobile + editable focus is active, compute:
   `keyboardInset = max(0, window.innerHeight - visualViewport.height - visualViewport.offsetTop)`.
3. Write a scoped CSS var such as `--keyboard-bottom-inset`; clear it on blur/settle.
4. Apply it only to non-tab flow scroll content, e.g. internal `main[data-screen-scroll]` padding/scroll-padding, not global body/window scrolling and not TabBar geometry.
5. If auto-scrolling the focused field, scroll the app-owned `[data-screen-scroll]` container, not `window`.
6. Keep existing keyboard-dismiss/route-settle logic for cleanup after blur.

### Page-local containment path

When the user or Lark acceptance explicitly scopes the bug to one page/one input (e.g. “单个页面，单独修复”), do **not** broaden into global viewport/runtime changes first. Use a page-local containment patch and regression:
1. Patch only the target screen’s editable control.
2. For touch/pen `pointerdown`, `preventDefault()` and call `focus({ preventScroll: true })` on the input/textarea so WebKit does not perform native document auto-scroll before the app-owned scroller reacts. Leave mouse behavior alone for desktop tests/accessibility.
3. Avoid `transition-all` on the focused input if the defect is visible jumping/flicker during typing/deleting; narrow it to `transition-shadow`, `transition-colors`, or the specific property needed.
4. Add a screen-level test asserting the target editable prevents native scroll on touch and focuses with `preventScroll: true`.
5. Scope/applicability for the remaining bullets: U-VISA React/PWA pages using `KeyboardPinnedFlow` or equivalent fixed-header + inner-scroller shells on iOS/WKWebView. Anti-condition: do not apply these opt-outs globally; only use them on a page that has fresh video/evidence of keyboard focus scroll, header instability, or manual-scroll snap-back and whose inputs already use `focus({ preventScroll: true })`.
6. If a follow-up video shows the page still scrolling to the editable and then snapping back (header disappears, then content flashes to top), the page-local `preventScroll` was not enough because the shared flow wrapper's focus handler may still be auto-scrolling the content scroller. Add a narrow opt-out prop on the wrapper and use it only on the affected page; also apply `preventScroll` to every editable on that page that can receive touch focus (e.g. amount and memo), not just the originally reported input.
7. If the page still jumps after disabling wrapper focus-scroll, inspect the global viewport/runtime path for attribute-based classification. In U-VISA this specifically means `data-keyboard-preserve-header="true"` makes the focused editable a keyboard-pinned surface, so `viewportStability` can reset `[data-screen-scroll]` and outer scroll during keyboard settle. For a page that owns its own focus containment, add a narrow opt-out for the preserve marker (default-on for other `KeyboardPinnedFlow` pages) instead of broadening global viewport behavior.
8. If the remaining bug is “user manually drags the scroll area while an input is focused, then release snaps back to the input”, treat it as the UA/caret reveal loop rather than another auto-scroll reset. On that page, capture pointer down/move on the content scroller; when a non-editable-origin touch drag exceeds a small threshold, blur the active editable so iOS/WKWebView no longer re-reveals the caret on release. Do not blur drags that begin on the editable itself.
9. Verification checklist: target screen test for all keyboard-triggering editables; test manual-scroll blur vs editable-origin drag; safe-area/keyboard layout regression test proving default P0 shells still preserve the marker while the affected page opts out; full build; if auto-merging to a deployed test branch, fetch the live HTML/JS bundle and check for the new code marker before asking for retest. Manual iOS/PWA evidence is still needed before claiming UI acceptance, and warn about PWA/Service Worker cache when applicable.

## Verification checklist

Automated:
- Unit test the keyboard inset runtime by mocking `visualViewport.height/offsetTop`, focusing an input, and asserting `--keyboard-bottom-inset` is set/cleared.
- Layout test that non-tab routes gain keyboard-aware reserve while tab routes/TabBar do not.
- Screen tests for remit preview note input and crypto payout textarea/amount input.

Manual/iOS acceptance:
- iPhone Safari and installed PWA.
- `资产 → 转出 → 国际汇款 → 选择收款人 → 金额 input`.
- `国际汇款 → 预览页 → 留言 input`.
- `资产 → 转出 → 链上提现 → 金额 input / 地址 textarea`.
- Quick transfer if restored.

Pass criteria:
- FlowNav/top content remains visible or at least is not pushed off by whole-canvas translation.
- Focused input/textarea remains visible above keyboard.
- Content scrolls inside the app container.
- Closing keyboard restores normal layout.
- Main tab TabBar/safe-area does not regress.
