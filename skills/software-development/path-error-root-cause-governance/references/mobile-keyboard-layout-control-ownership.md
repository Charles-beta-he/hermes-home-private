# Mobile keyboard layout control ownership

Scope: class-level debugging pattern for mobile Web/PWA/WebView input-flow regressions where soft keyboard, safe-area, fixed headers/footers, app shell scroll, and page-local scroll all interact.

Applicability:
- The same keyboard/viewport symptom is being patched in multiple layers: global CSS/body lock, app route shell overflow, component shell, visualViewport listener, page-specific pointer/focus handlers.
- Fixes trade symptoms: header preserved but input hidden; CTA stable but page cannot scroll; typing jitters; manual scroll snaps back; BottomSheet/select/composer breaks.
- Existing tests mostly assert class names, marker attributes, or CSS strings instead of the real focus/keyboard path.

Anti-conditions:
- A single deterministic component bug with no OS/browser viewport involvement.
- Pure desktop layout issues without soft keyboard or visualViewport behavior.
- Cases where real device/browser evidence already proves one owner layer is solely responsible.

## Core failure mechanism

Do not represent this as “page X header/CTA/input is misplaced.” Represent it as a state-owner problem:

> During a mobile input path, OS/browser `visualViewport`, document/body, app-level screen scroller, page-local content scroller, fixed header, and bottom CTA all participate in layout, but the codebase lacks a single ownership contract. Multiple layers compete to control scroll and viewport state, so each local patch creates a new symptom in a neighboring layer.

Bad loop:

```text
visible symptom -> patch page/component -> add route/platform escape hatch -> add pointer/focus workaround -> typing/scroll regression -> rollback
```

Governed loop:

```text
user path -> time slice -> owner boundary -> competing hypotheses -> falsifier -> single owner contract -> behavior verification
```

## Required problem representation

Before another patch, write the failing path by time slice:

- T0 initial page: who owns height, safe-area, app scroll, and CTA position?
- T1 input focus / keyboard opening: who is allowed to react to visualViewport change?
- T2 typing: can value changes trigger scroll restore/snap/reset?
- T3 scroll while focused: which container may scroll, and should focus blur?
- T4 keyboard dismiss / route return / resume: who cleans temporary state?

Then name the control boundary:

- OS/browser: visualViewport, native focus scroll, IME behavior.
- Document/body: only one policy; avoid casual global `position: fixed` / `overflow: hidden` as a local fix.
- App shell: safe-area and tab-page reserve; should not own page-specific keyboard behavior.
- Keyboard/input flow shell: fixed header/footer and inner content scroll, if that is the chosen contract.
- Page/component: field validation and ordinary rendering; should not own global viewport listeners or pointer capture unless explicitly justified.

## Evidence matrix for mobile keyboard issues

Collect both broken and working/contrast paths:

- DOM existence of header, content scroller, CTA/footer, overlays/sheets.
- Computed `overflow`, `position`, `height`, `bottom`, `padding-bottom`, `z-index` for body, root, app main, page shell, footer.
- Bounding boxes before focus, after focus, during typing, after dismiss.
- `window.innerHeight`, `visualViewport.height`, `visualViewport.offsetTop`, scrollTop for document/body/app scroller/content scroller.
- Active element and any route/platform/data markers.
- Whether `preventDefault`, `focus({preventScroll:true})`, `scrollIntoView`, or manual `scrollTop` resets fire on the path.

## Entry gate before a fix

Reject a candidate patch if it:

1. Adds another owner for the same state instead of removing/merging owners.
2. Uses page/platform/route escape hatches before proving the owner boundary.
3. Captures `pointerdown`/`touchmove` globally without testing cursor placement, text selection, native select/picker, IME, and scroll gestures.
4. Treats CSS-string/class/attribute assertions as sufficient proof of keyboard behavior.
5. Mixes unrelated concerns such as TabBar theme/safe-area visual tuning with soft-keyboard input-flow control.
6. Leaves dead tokens/listeners (`--keyboard-inset` calculated but unused, stale route switches, unused marker attributes).

## Preferred convergence shape

Create or recover one explicit contract:

- App shell owns safe-area and tab-page content reserve only.
- A dedicated keyboard/input flow shell owns header/content/footer geometry for input flows.
- The dedicated shell owns focused-input visibility by scrolling only its inner content scroller.
- Ordinary amount/remark/address fields keep CTA in its original bottom area; content scrolls instead of lifting CTA above the keyboard.
- Global visualViewport listeners are minimal and delegated to marked shells; they do not become a second layout system.
- Preview/confirm/non-input pages are not migrated into keyboard shells merely because they share a route group.

## Competitive / standard interaction classifier

Before judging whether a keyboard fix is correct, classify the surface by product interaction model. Do not apply one keyboard behavior to every route.

### Ordinary financial form / amount / address / remark flows

Standard effect for banking, payment, remittance, and finance-like forms:

- Header remains stable and visible.
- The focused field is visible.
- The middle content/form region scrolls.
- The primary process CTA remains in its original bottom/safe-area region; it is not lifted to sit above the keyboard unless product explicitly defines that as the task interaction.
- Document/body/window scroll should not fight the form scroller.
- Typing must not cause jitter, snap-back, first-tap loss, or caret/IME breakage.

Rationale: the primary CTA is a flow/submission action, not a keyboard accessory. Lifting it above the keyboard on money/address/remark flows increases accidental-submit risk, competes with IME/candidate bars, and reduces the visible business context. The correct behavior is content reveal via the owned scroller, not CTA promotion.

### Chat / support / AI composer flows

Standard effect for chat-like composer surfaces:

- Header remains stable.
- The composer/input bar may track the keyboard/visual viewport.
- The message/activity list shrinks and is the only scroll owner.
- The document/body/window do not scroll to reveal the composer.

Rationale: the composer is an input accessory, so docking it near the keyboard is expected. This model must be explicit (for example `composer` mode) and must not leak into ordinary financial forms.

### Short auth/login flows

Standard effect for short auth screens:

- Default state can keep the full-height brand/login composition with a bottom CTA.
- Focused state may reveal an inline CTA near the input and hide the bottom CTA via CSS `:focus-within` / group focus.
- Suggestions/dropdowns stay anchored to the input and first tap works.
- Avoid React blur timers, global keyboard reserve, visual-viewport composer shrink, or page-wide `scrollBy` as the default auth solution.

Long auth/KYC forms should instead follow the ordinary form model: content scrolls, focused input is visible, and the primary CTA stays in the flow bottom area.

### Sheets / modals / scanners / selectors

Standard effect:

- The sheet/overlay owns its own panel height and internal scroll.
- Background route scrollers and body locks do not become part of the sheet keyboard behavior.
- If the sheet contains an input, keyboard handling remains inside the sheet surface.

### Preview / confirm / finish / detail routes

Standard effect:

- Do not use keyboard shells for non-input routes.
- Preserve ordinary page flow and process CTA behavior.
- These routes are contrast paths proving keyboard tokens/shells have not leaked into unrelated pages.

## Verification checklist

At minimum, verify one representative path in each class:

- Auth/login email focus plus suggestions: default bottom CTA, focused inline CTA if used, suggestions first tap works, no blur race or page-wide jump.
- Amount-entry flow: Header stable, focused field visible, content scroller moves if needed, process CTA remains in original bottom/safe-area region rather than being lifted above the keyboard.
- Address/remark text-entry flow: field visibility and form scrolling work without document/body scroll competition, caret/IME behavior is intact.
- Chat/composer full-height flow: composer tracks visual viewport/keyboard, message list shrinks and owns scroll, Header remains visible.
- BottomSheet/select/scan overlay opened from a keyboard flow: overlay owns its panel/internal scroll; background route does not become a second scroll owner.
- A contrast non-input preview/confirm/detail page: no keyboard shell/tokens leak in; ordinary process CTA behavior is preserved.

Assertions should cover behavior, not implementation traces:

- Header remains visible and not overlapped.
- CTA stays in the intended bottom area and is not lifted above the keyboard unless product explicitly wants that.
- Focused input is reachable/visible.
- The intended content container scrolls; body/app scroller does not fight it.
- Typing does not snap scroll or jitter.
- Overlay/sheet can open, scroll, and close.
- Route return/dismiss clears temporary viewport state.

Use unit tests for helper contracts, but do not claim closure without browser/device or harness evidence for the real focus path.