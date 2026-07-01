# Android PWA: app theme vs system dark mode

Use this when a user reports Android installed PWA / WebappActivity screenshots where the phone is in system dark mode but the app is set to light/day mode, especially when black blocks appear in the status bar or bottom gesture/navigation area.

## Key lesson

Do not validate this class of issue only in desktop mobile emulation or Android light mode. Reproduce the matrix explicitly:

1. Android system light + app light
2. Android system dark + app light
3. Android system light + app dark
4. Android system dark + app dark

The critical regression is usually case 2: system dark mode leaks into PWA chrome while the app UI is intended to stay light.

## Diagnosis split

Separate four surfaces before changing code:

- App content area: controlled by app CSS/runtime theme. It can and should follow the app's own theme SSOT.
- Android/Chrome top status bar: Chrome WebappActivity usually follows `theme-color`, but behavior can depend on manifest cache and runtime meta tags.
- iOS Home Screen top status bar: controlled by `meta[name="apple-mobile-web-app-status-bar-style"]`; if this is statically `black-translucent`, phone dark + app light can show a black top bar even when Android `theme-color` is correct. See `references/ios-pwa-status-bar-app-theme.md`.
- Bottom gesture/navigation bar: Android/Chrome may keep this system-controlled in dark mode. Pure PWA can avoid content underlap but may not be able to force the bar color on every device/OEM.

## Common root cause

HTML like this makes PWA chrome follow the phone's system mode, not the app's internal theme:

```html
<meta name="theme-color" content="#F2F3F5" media="(prefers-color-scheme: light)" />
<meta name="theme-color" content="#0E0F12" media="(prefers-color-scheme: dark)" />
```

If the product requirement is "PWA interface follows the app theme regardless of phone system mode", remove the media-bound theme colors and manage a single `meta[name="theme-color"]` from the app theme runtime.

## Recommended implementation pattern

- Make app theme the SSOT, e.g. `data-theme="light|dark"` on `document.documentElement`.
- Avoid using `@media (prefers-color-scheme: dark)` for product UI when app theme must be independent of system mode.
- Use CSS variables under `[data-theme="light"]` and `[data-theme="dark"]`.
- Runtime-sync `meta[name="theme-color"]` from the app theme:

```ts
function syncThemeColor(theme: 'light' | 'dark') {
  const color = theme === 'dark' ? '#0E0F12' : '#F2F3F5';
  let meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', 'theme-color');
    document.head.appendChild(meta);
  }
  meta.setAttribute('content', color);
}
```

### Resume / rehydration hardening

If the top status bar stays stale until the user navigates back to `/me` or toggles theme again, the app may already have the right theme model but miss a lifecycle sync. Add two guards before tuning route CSS:

- Synchronously read the persisted theme choice during theme-store initialization so a persisted `system` choice resolves to current OS dark/light before React/persistence rehydration can briefly apply default light.
- Re-resolve `system` and reapply `data-theme` + `theme-color` on `pageshow`, foreground `visibilitychange`, and `focus`, because Android Chrome/WebAPK/WebView can miss or delay the media-query change event when the OS theme changes in the background.

See `references/android-pwa-system-theme-resume-sync.md` for the regression-test checklist.

## Runtime hardening pattern

For apps that support `light | dark | system` themes, avoid a rehydration flash that temporarily repaints Android PWA chrome white:

- Read the persisted theme choice synchronously at store/bootstrap time before React rehydration applies the default state.
- If the persisted choice is `system`, resolve it immediately from `matchMedia('(prefers-color-scheme: dark)')` and apply both `document.documentElement[data-theme]` and the single app-owned `meta[name="theme-color"]`.
- Keep fixed `light` and `dark` choices app-owned; they must not follow the phone unless the explicit `system` option is selected.
- Add a lifecycle resync for Android/WebAPK/WebView cases where the media-query `change` event is missed or delayed: re-resolve the theme on `pageshow`, `focus`, and `visibilitychange` when visible. This prevents the status bar from staying white until route navigation (for example returning to `/me`) happens to reapply the theme.

## Verification checklist

When no Android device is attached, still run a **PWA-layer proof** before reporting a device blocker:

1. Build and inspect the generated artifacts: `dist/index.html` should have exactly one `meta[name="theme-color"]`, zero media-bound theme-color tags, exactly one `meta[name="apple-mobile-web-app-status-bar-style"]`, and `dist/manifest.webmanifest` should have `display: standalone` plus the expected light `theme_color` / `background_color`. For iOS Home Screen PWA, app light should map `apple-mobile-web-app-status-bar-style` to `default`; app dark should map it to `black-translucent`.
2. Serve the built `dist` with `vite preview` or an equivalent static preview.
3. Use Playwright mobile context (for example Pixel 7) with `colorScheme: 'dark'`, set persisted `{ theme: 'system' }`, reload, and assert `data-theme='dark'` + `theme-color='#0E0F12'`.
4. Switch `page.emulateMedia({ colorScheme: 'light' })`, dispatch `pageshow`, and assert `data-theme='light'` + `theme-color='#F2F3F5'`.
5. Label this as "PWA/H5 runtime proof" only. It proves the web inputs to Android system chrome are correct; it does **not** prove installed WebAPK/native system-bar rendering.

For final installed-PWA proof, use a real Android AVD or device:

```bash
adb shell cmd uimode night yes   # system dark
adb shell cmd uimode night no    # system light
```

Then launch the installed PWA from the launcher, not just a normal Chrome tab. Confirm the top activity is Chrome WebappActivity:

```bash
adb shell dumpsys activity activities | grep -E 'topResumedActivity|WebappActivity|ChromeTabbedActivity' | head
```

Capture screenshots with:

```bash
adb exec-out screencap -p > /tmp/pwa-dark-mode-check.png
```

Acceptance evidence should say which combination was tested, e.g. "Android system dark + app light". Do not report a PWA-layer Playwright pass or a light-mode pass as proof for an installed Android PWA dark-mode system-bar bug.

## Anti-conditions

- If the app is running inside a native shell, the durable fix may belong in native status/navigation-bar APIs, not PWA meta tags.
- If the only issue is TabBar/content underlap, keep the visualViewport/safe-area fix separate from system bar color policy.
- Do not promise pure PWA can force Android bottom gesture bar color on every OEM; frame that as best-effort unless a native/TWA layer is available.
