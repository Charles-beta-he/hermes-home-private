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

Prefer a reusable keyboard-aware flow layer over per-input `scrollIntoView` hacks:
1. Add a small runtime/hook that listens to `focusin`, `focusout`, `visualViewport.resize`, and `visualViewport.scroll`.
2. While iOS/mobile + editable focus is active, compute:
   `keyboardInset = max(0, window.innerHeight - visualViewport.height - visualViewport.offsetTop)`.
3. Write a scoped CSS var such as `--keyboard-bottom-inset`; clear it on blur/settle.
4. Apply it only to non-tab flow scroll content, e.g. internal `main[data-screen-scroll]` padding/scroll-padding, not global body/window scrolling and not TabBar geometry.
5. If auto-scrolling the focused field, scroll the app-owned `[data-screen-scroll]` container, not `window`.
6. Keep existing keyboard-dismiss/route-settle logic for cleanup after blur.

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
