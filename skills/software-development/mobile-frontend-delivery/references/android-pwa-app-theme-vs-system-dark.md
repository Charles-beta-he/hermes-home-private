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

Separate three surfaces:

- App content area: controlled by app CSS/runtime theme. It can and should follow the app's own theme SSOT.
- Top status bar: Chrome WebappActivity usually follows `theme-color`, but behavior can depend on manifest cache and runtime meta tags.
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

## Verification checklist

For a real Android AVD or device:

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

Acceptance evidence should say which combination was tested, e.g. "Android system dark + app light". Do not report a light-mode pass as proof for a dark-mode bug.

## Anti-conditions

- If the app is running inside a native shell, the durable fix may belong in native status/navigation-bar APIs, not PWA meta tags.
- If the only issue is TabBar/content underlap, keep the visualViewport/safe-area fix separate from system bar color policy.
- Do not promise pure PWA can force Android bottom gesture bar color on every OEM; frame that as best-effort unless a native/TWA layer is available.
