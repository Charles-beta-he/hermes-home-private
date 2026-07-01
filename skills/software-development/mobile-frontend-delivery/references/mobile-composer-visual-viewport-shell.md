# Mobile composer visual-viewport shell

Applicability: mobile web / PWA routes with a fixed or persistent header, a bottom text composer, and an inner message/activity region (support chat, AI assistant, comments) where the on-screen keyboard should shrink only the middle activity area.

Anti-conditions:
- Do not use this as a generic TabBar/system-navigation fix.
- Do not start by forcing `window.scrollTo(0, 0)` while the input remains focused; that can fight WebKit's caret-visibility logic and hides the real height-ownership bug.
- Do not treat a desktop/headless browser run with no keyboard shrink as enough evidence for iOS acceptance.

## Correct model

When the keyboard opens:

```text
visualViewport.height shrinks
→ route shell height shrinks to visual viewport
→ header remains at the top/safe area
→ composer remains at the visual bottom
→ message/activity region becomes shorter and is the only scroll owner
```

## Diagnostic signs of the wrong model

- The route shell is layout-viewport-owned (`100dvh`, `100vh`, `100lvh`, `h-full`, or `bottom: safe-bottom`) instead of visual-viewport-owned.
- Existing `--app-visual-height`/visualViewport tokens are only used for TabBar/chrome and are skipped while `document.activeElement` is editable.
- The bottom composer stays at the large/layout viewport bottom, so iOS scrolls the layout/window to reveal the textarea and the header disappears above the visible viewport.
- Prior patches keep adding `position: fixed`, z-index, scroll resets, or prompt suppression without making the shell shorter.

## Preferred fix path

1. Identify the scroll owners:
   - outer app/document: locked, not the active scroll surface;
   - route shell: height-owned by the visual viewport;
   - message/activity list: `min-h-0 flex-1 overflow-y-auto`;
   - composer/header: `shrink-0` or fixed/sticky chrome, outside content scrolling.
2. Make the composer route shell consume visual height, for example:
   ```text
   top: var(--safe-top)
   bottom: auto
   height: calc(var(--app-visual-height, 100dvh) - var(--safe-top) - var(--safe-bottom))
   overflow: hidden
   ```
3. Update the viewport runtime so focused editables inside a keyboard-preserving composer shell still write `--app-visual-height = visualViewport.height`.
4. Keep ordinary focused inputs from updating TabBar/top-anchor visual height if that was an existing guard; scope the exception to `[data-keyboard-preserve-header="true"]` or equivalent.
5. Applicability: mobile web/PWA composer shells that already have a keyboard-preserving route marker and a visual-viewport-owned shell. Anti-condition: ordinary form/login/OTP/payment inputs that rely on browser caret visibility. Do not use focused-window force-scroll as the *primary* fix. First prove the shell consumes `visualViewport.height`. After that model is in place, a scoped outer-scroll lock may still be required for WebKit/iOS: only for focused elements inside the keyboard-preserving shell marker, reset `window.scrollY`, `document.documentElement.scrollTop`, `document.body.scrollTop`, and any app-level screen-scroller drift to 0. Ordinary focused inputs must remain untouched so the browser can keep the caret visible.
6. If real iOS screenshots still show a brief header-up motion, right-side scrollbar flash, or content jumping during the keyboard-open transition even though the settled state is correct, treat it as a **focus-frame race**: `focusin -> setTimeout(0)/visualViewport resize -> settle` can be one paint too late. Run the preserve-header settle synchronously in the `focusin` handler, then schedule the delayed settle tail. Set a scoped root marker such as `data-keyboard-shell-active="true"` while a focused element is inside the keyboard-preserving shell, and use it to disable route-enter/child transform animations for that shell during keyboard focus. Clear the marker on focusout/settle recovery. Do not disable global page animations or apply this to ordinary form inputs.

## Next-button / CTA shell extension

If the user asks for an ordinary flow page with a bottom “Next/下一步” button to behave like the AI/customer-service composer, do not assume `data-keyboard-preserve-header` on the input is enough. First classify whether the page is already a three-part shell:

```text
fixed or shrink-0 header
→ min-h-0 flex-1 overflow-y-auto middle region
→ shrink-0 bottom composer / CTA
```

Only that shell can safely consume `--app-visual-height`. Pages built as `FlowNav + content + CtaBlock mt-auto` or `min-h-full` need to be refactored into this shell shape before claiming the header and next button are fixed while only the middle area shrinks. Otherwise the patch may pin the outer scroll but leave content clipped, CTA unreachable, or iOS caret visibility broken.

A marker-only implementation is a red flag: the viewport runtime should write a visual-height token such as `--app-visual-height = visualViewport.height` during focused keyboard-shell editables, and the preserve route should use `height: calc(var(--app-visual-height, 100dvh) - safe-top - safe-bottom)` rather than only `top + bottom` layout-viewport anchoring.

## Verification checklist

- RED test before fix:
  - composer route class expects visual-height-owned shell, not a layout-viewport bottom anchor;
  - focused textarea inside the keyboard-preserving shell writes `--app-visual-height` from `visualViewport.height`;
  - after a simulated iOS keyboard scroll, keyboard-preserving shells reset window/document/body/app-scroller scroll to 0;
  - for the applicable preserve-header composer shell only, `focusin` performs the lock synchronously before timers/resize events run, marks the shell-active state, and leaves window/document/body/app-scroller scroll at 0;
  - for the same applicable shell, CSS disables route-enter/child transform animations during keyboard focus; anti-condition: ordinary form/login/OTP/payment inputs and unrelated page-enter animations remain unchanged;
  - ordinary focused inputs keep the app visual-height token untouched and do **not** call `window.scrollTo`, preserving the browser caret-visibility path.
- Component tests assert:
  - route root is `h-full min-h-0 overflow-hidden`;
  - message list is `min-h-0 flex-1 overflow-y-auto`;
  - composer is `shrink-0` and one-row compact by default.
- Browser/Playwright bbox smoke with simulated visual height:
  - screen/root bottom equals simulated visual height;
  - header top remains 0/safe-top and visible;
  - composer bottom equals visual height;
  - message list height shrinks and `overflow-y` is `auto`;
  - app/window scroll remains at rest in the harness.
- Real iOS Safari/Home Screen PWA evidence is still required for final UI acceptance because headless Chromium cannot open the native keyboard.
