# Mobile PWA keyboard focus layout: no global reserve, focus-within CTA swap

Applicability:
- Mobile web / installed PWA / WebView pages where focusing an input makes the page visibly slide upward.
- Auth/login or short form pages that should keep a full-height visual composition but expose a nearby CTA while the field is focused.
- Full-screen composer pages that should shrink an internal activity area when the keyboard opens.

Anti-conditions:
- Do not apply the login/auth CTA swap to long forms where browser-native reveal/scroll is expected.
- Do not use this as a reason to remove safe-area / TabBar / Android visual-bottom handling.
- Do not blindly implement a proposed tweak such as “move button below input” before checking the best interaction model for the page class.

## Preferred model

1. Do not simulate keyboard animation.
2. Lock the document/root canvas so `body` is not the scroll owner.
3. Keep ordinary flow pages as simple safe-area-bounded scrollers: `top: safe-top`, `bottom: safe-bottom`.
4. Do not add global `keyboardHeight` padding, `scroll-padding-bottom`, `scrollIntoView`, or `scrollBy` for all inputs.
5. For full-screen composer shells, use `visualViewport.height` to shrink the shell and delegate scrolling to the internal message/content owner.
6. For short auth/login pages, keep the full-height layout and use CSS `group-focus-within` to swap CTA placement, rather than React focus state with blur timers.

## Login/auth CTA pattern

Goal: default state keeps the “full-height + bottom CTA” composition; focused state exposes a CTA directly under the input without scrolling the page.

Recommended structure:

```tsx
<div className="flex flex-col min-h-full pb-6">
  <div className="px-6 pt-[60px] pb-6 flex flex-col flex-1">
    <BrandLockup />
    <Title />
    <Subtitle />

    <div className="group flex flex-1 flex-col">
      <label htmlFor="login-email">Email</label>
      <div className="relative">
        <input id="login-email" />
        {/* suggestions/dropdown stays inside this relative anchor */}
      </div>
      <div id="login-email-hint">Hint</div>

      <div className="mt-6 hidden group-focus-within:block">
        <CtaBtn>Next</CtaBtn>
      </div>

      <div className="mt-auto pt-8 group-focus-within:hidden">
        <CtaBtn>Next</CtaBtn>
      </div>
    </div>

    <SupportLink />
  </div>
</div>
```

Why this is better than JS focus state:
- Focus can move from the input to the inline CTA without a blur timer race.
- The bottom CTA remains the default layout; the inline CTA is only a focused-state affordance.
- No duplicate keyboard handling or forced page scroll is required.
- The pattern is declarative and survives fast taps better than `setTimeout(..., 120)` blur workarounds.

## Runtime/root rules

Keep root/canvas safety separate from keyboard UX. Distinguish three different concepts instead of collapsing them into one "keyboard pinned" flag:

1. **Outer-scroll lock / stale-scroll reset**: short auth surfaces may need to clear `window.scrollY`, `documentElement/body.scrollTop`, and the app `[data-screen-scroll].scrollTop` on blur/refocus so iOS WebKit's previous reveal offset is not inherited.
2. **Visual-viewport shell shrink**: full-screen composer shells may size their outer route from `visualViewport.height` / `--app-visual-height` and delegate scrolling to an internal message/content area.
3. **Generic flow reveal**: ordinary forms should not receive global keyboard reserve, `scroll-padding-bottom`, `scrollBy`, or visual-height shrink.

Do not put a short login/auth screen into the visual-viewport composer path just to fix stale scroll. That can make the final position correct while producing a visible intermediate upward/height-shrink animation as the keyboard opens. Use separate route predicates/markers, for example:

```ts
shouldPreserveHeaderWhileKeyboardOpenRoute('/login') === false; // no visualViewport height shrink
shouldLockOuterScrollWhileKeyboardOpenRoute('/login') === true; // reset stale outer scroll only
```

Runtime marker pattern:

```tsx
<div data-keyboard-pinned-surface="true" className="flex min-h-full flex-col pb-6">
  {/* auth screen */}
</div>
```

`data-keyboard-pinned-surface="true"` should participate in stale-scroll reset, but must not set the global keyboard-shell-active state or write keyboard-shrunk `--app-visual-height`. Reserve `data-keyboard-preserve-header="true"` for real composer shells that intentionally shrink to the visual viewport.

```css
html, body, #root {
  height: 100%;
  min-height: 100%;
  overflow: hidden;
}

html, body {
  position: fixed;
  inset: 0;
  width: 100%;
  overscroll-behavior-y: none;
}

[data-screen-scroll] {
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
}
```

Ordinary flow pages should not include global keyboard reserve classes/tokens such as:
- `--flow-keyboard-content-reserve`
- `pb-[var(--flow-keyboard-content-reserve)]`
- `scroll-pb-[calc(var(--ios-keyboard-bottom-inset,...))]`
- focused-input `scrollBy(...)` / `scrollIntoView(...)` in shared runtime code

## Verification checklist

Unit/component tests:
- Default login CTA wrapper has `mt-auto pt-8 group-focus-within:hidden`.
- Inline login CTA wrapper has `mt-6 hidden group-focus-within:block`.
- Login input is not inside `data-keyboard-preserve-header="true"` unless it is genuinely a full-height composer shell.
- Short auth/login surfaces that need iOS refocus protection have an explicit auth marker such as `data-keyboard-pinned-surface="true"`.
- Route predicates keep auth scroll-lock separate from composer shrink: login-style auth routes should be `shouldLockOuterScrollWhileKeyboardOpenRoute(...) === true` but `shouldPreserveHeaderWhileKeyboardOpenRoute(...) === false`.
- Viewport runtime tests cover both behaviors: auth pinned surfaces reset stale outer scroll without setting `data-keyboard-shell-active` or keyboard-shrunk `--app-visual-height`; composer shells still set those tokens and reset their outer scroller.
- Ordinary flow `screenScrollInsetsClass(false)` contains only top/bottom safe-area bounds and no keyboard reserve/scroll-padding tokens.
- Built CSS contains `group-focus-within\:block` and `group-focus-within\:hidden` but does not contain the removed global flow keyboard reserve token.

Real UI evidence before final acceptance:
- iOS Safari and/or iOS Home Screen PWA: login default shows bottom CTA.
- Focus email: page does not visibly slide upward, inline CTA appears under the input, bottom CTA hides.
- Tap inline CTA: no blur race causes the button to jump back to the bottom before click handling.
- Blur/route-return: layout returns cleanly and no stale scroll/keyboard token remains.
- Android Chrome / Android installed PWA: no iOS keyboard token changes TabBar/system-nav geometry.

## Pitfalls

- Treating a user-proposed UI move as the final solution. First classify the page: ordinary flow, short auth screen, full-screen composer, sheet/modal, or tab page. Choose the interaction model for that class.
- Global keyboard reserve is a bad default. It often combines with browser-native input reveal and produces double movement.
- React focus state plus delayed blur can work in tests but creates mobile tap races. Prefer CSS `:focus-within` when the intent is just conditional layout.
- Hiding DOM with CSS means testing-library still sees both buttons by role. Tests should find wrappers/classes, and browser/UI evidence should confirm visible behavior.
