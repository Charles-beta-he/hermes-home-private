# Android PWA app-canvas bottom trim

## Applicability

Use for web/PWA/mobile frontends that render the app inside a bounded root canvas or portal (for example an app shell element such as `#app`, `#root`, `#phone-portal`, or a mobile preview canvas). This is a class-level pattern for Android standalone PWA/WebAPK/WebView viewport underlap.

## Anti-conditions

- Do not use when only one component has an isolated spacing bug; tune that component instead.
- Do not use to change iOS standalone PWA fullscreen workarounds when iOS is already correct.
- Do not store project names, PR numbers, or branch names here; resolve the concrete selector and branch from the current repo.

## Trigger

Use when an Android installed PWA/WebAPK or WebView screenshot shows bottom sheets, full-screen portals, or absolute bottom chrome extending into the Android gesture/navigation area, while iOS standalone PWA is already visually correct.

This is often a canvas-height problem, not a TabBar spacing problem.

## Diagnostic path

1. Identify the affected layer before tuning component gaps:
   - If only the TabBar floats too high/low, inspect TabBar tokens.
   - If bottom sheets, portals, scroll containers, and bottom chrome all appear to run under the system gesture area, inspect the app canvas/root shell and viewport units.
2. Search history for viewport-unit changes around the app shell:
   - `100vh`, `100dvh`, `100svh`, `100lvh`, `h-dvh`, `min-height`, `position: fixed`, `inset: 0`.
   - Look for iOS-specific fixes that intentionally changed standalone PWA canvas height from `dvh` to `vh/lvh` to restore fullscreen behavior.
3. Preserve iOS fullscreen restorations if iOS is reported correct. Do not globally revert `100vh/100lvh` or shared bottom-gap tokens just because Android is clipped.
4. For Android-only underlap caused by `100dvh` being slightly taller than the visually safe area, prefer an Android standalone canvas trim on the app canvas selector:

```css
:root {
  --android-app-canvas-bottom-trim: 8px;
}

[data-display-mode="standalone"][data-platform="android"] <app-canvas-selector> {
  height: calc(100dvh - var(--android-app-canvas-bottom-trim));
  min-height: calc(100dvh - var(--android-app-canvas-bottom-trim));
}
```

5. Keep the selector narrow: `display-mode=standalone` + `platform=android` + app canvas. Browser H5 and iOS standalone should not consume the trim.

## Verification checklist

- [ ] The fix is applied at the canvas/shell layer only after proving the symptom is not isolated to one component.
- [ ] iOS standalone `100vh` / `100lvh` or equivalent fullscreen workaround remains unchanged when iOS is already correct.
- [ ] Android browser mode is unaffected.
- [ ] Regression test asserts the Android canvas trim value and selector, and asserts the iOS canvas rule does not consume the trim or `100dvh` calc.
- [ ] Build output is checked for the CSS marker, not only source tests.

## Pitfall

Do not jump from a bottom screenshot directly to TabBar gap changes. A bottom sheet rendered through the app canvas/portal inherits the canvas height; if that canvas is too tall on Android, changing TabBar spacing will miss the actual root cause and may regress iOS or other bottom chrome.
