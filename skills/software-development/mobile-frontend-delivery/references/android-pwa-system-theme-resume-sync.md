# Android PWA/WebView system theme resume sync

## Trigger

Use when an Android PWA/WebView app has a visible status-bar/top-safe-area color mismatch after the phone switches light/dark mode, especially when:

- The app is in dark mode or Follow System, but the top status bar briefly or persistently stays white.
- Navigating back to a main page such as `/me` or toggling theme again fixes the color.
- Source already has a single app-owned `meta[name="theme-color"]`, but runtime state can still drift.

## Root cause pattern

Android Chrome/WebAPK/WebView may not dispatch `prefers-color-scheme` change exactly when the OS theme toggles, and React/Zustand persistence rehydration can briefly apply the default theme before the persisted choice is loaded. The result is a stale `data-theme` or `theme-color` until some page-level effect or user action triggers a re-render.

## Fix pattern

Keep the product theme model intact:

- `light` and `dark` are fixed app-owned choices; they must not read OS color-scheme.
- `system` is the only choice that reads `matchMedia('(prefers-color-scheme: dark)')`.
- Maintain exactly one authoritative `meta[name="theme-color"]` and remove legacy `media` attributes.

Then add two guards:

1. **Pre-react hydration guard**
   - During store/module initialization, synchronously read the persisted theme choice from localStorage when available.
   - Resolve `system` immediately against current `matchMedia`.
   - Apply `document.documentElement.dataset.theme` and `meta[name="theme-color"]` before normal persistence rehydration can repaint the app with a default light theme.

2. **Lifecycle resync guard**
   - Re-resolve and apply theme on lifecycle return events such as `pageshow`, `focus`, and `visibilitychange` when visible.
   - This catches Android cases where OS theme changed while the app was backgrounded or the media-query change event was missed.
   - Keep the resync idempotent and update the store only when `theme` or `resolved` actually changed.

## Minimal regression tests

Add tests that prove:

- Fixed `light` ignores later system-dark changes.
- Fixed `dark` ignores later system-light changes.
- `system` follows media-query changes.
- `system` re-syncs on `pageshow`/resume even when no media-query change event fired.
- Persisted `system` hydrates directly to the correct `resolved` value and `theme-color` before React-level rehydration.
- Only one `theme-color` tag remains and none has a `media` attribute.

## Runtime verification

DOM-level smoke is useful before device testing:

```js
({
  dataTheme: document.documentElement.getAttribute('data-theme'),
  themeColor: document.querySelector('meta[name="theme-color"]')?.content,
  metaCount: document.querySelectorAll('meta[name="theme-color"]').length,
  mediaCount: document.querySelectorAll('meta[name="theme-color"][media]').length,
})
```

Device acceptance still needs a real Android installed-PWA/WebView screenshot matrix when available:

- Android system light + app system/light.
- Android system dark + app system/dark.
- Switch system light → dark → light while the app is open or backgrounded, then verify the status bar changes without navigating back to a special page.

## Anti-conditions

- Do not remove a Follow System option unless product explicitly removes it.
- Do not fix this by hardcoding a black spacer/header on one route; the symptom is global system-bar theme drift.
- Do not confuse this with bottom navigation-bar underlap; bottom viewport compensation is a separate atom.
- Do not claim final Lark closeout from DOM tests alone when the task is specifically an Android system-bar screenshot bug; record Android device/emulator evidence or a clear blocker.
