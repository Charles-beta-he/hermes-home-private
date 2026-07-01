---
name: pwa-safe-area-handling
description: "Use when env(safe-area-inset) returns 0 in PWA standalone mode, TabBar clipped by Home Indicator, mobile web safe area layout issues, iPhone notch/Dynamic Island inset not applying, or iOS shows stale PWA icon in Add to Home Screen dialog."
trigger: PWA standalone safe area issues, env(safe-area-inset) returning 0, mobile web bottom/top inset problems, TabBar or nav bar clipped by gesture bar, Home Indicator overlap, iPhone notch/dynamic island safe area
---

# PWA Safe Area Handling

When a web app is installed as a PWA (standalone mode), `env(safe-area-inset-bottom)` and `env(safe-area-inset-top)` may return **0** even when the Home Indicator or notch is physically present. This is a known WebKit/iOS behavior in certain versions.

## Root Cause

- Safari browser mode: `env(safe-area-inset-bottom)` = ~34px (Home Indicator) ✅
- PWA standalone mode (iOS 15.x and some 16.x): returns 0px ❌
- `viewport-fit=cover` is required but not sufficient — some iOS versions still report 0 in standalone

## Detection Pattern

```js
// In index.html <head>, before any CSS renders
(function () {
  var root = document.documentElement;

  function readEnvInset(edge) {
    var probe = document.createElement('div');
    probe.style.cssText = 'position:absolute;visibility:hidden;pointer-events:none;contain:strict;padding-' + edge + ':env(safe-area-inset-' + edge + ',0px)';
    root.appendChild(probe);
    var value = parseFloat(getComputedStyle(probe).getPropertyValue('padding-' + edge)) || 0;
    root.removeChild(probe);
    return value;
  }

  var envBottom = readEnvInset('bottom');
  var envTop = readEnvInset('top');

  var isStandalone =
    window.navigator.standalone === true ||                       // iOS Safari
    window.matchMedia('(display-mode: standalone)').matches;      // Android / desktop

  if (!isStandalone) return;

  // --- bottom (Home Indicator / gesture bar) ---
  if (envBottom > 0) {
    root.style.setProperty('--safe-bottom', envBottom + 'px');
  } else {
    // Only synthesize the well-known 34px fallback for iPhone.
    // On Android standalone PWAs, screen.height - innerHeight can include
    // system chrome and over-lift floating bottom navigation.
    var isIPhone = /iPhone/.test(navigator.userAgent);
    var bottomInset = screen.height - window.innerHeight;
    var safeBot = isIPhone && bottomInset > 20 ? '34px' : '0px';
    root.style.setProperty('--safe-bottom', safeBot);
  }

  // --- top (notch / Dynamic Island) ---
  if (envTop > 0) {
    root.style.setProperty('--safe-top', envTop + 'px');
  } else {
    var isIPhone = /iPhone/.test(navigator.userAgent);
    if (isIPhone && screen.height >= 800) {
      root.style.setProperty('--safe-top', '47px');
    }
  }
})();
```

## Key Requirements

1. **Must run in `<head>` inline `<script>`** — before CSS renders to prevent layout shift (flash of wrong position)
2. **Only patch in standalone mode** — browser mode uses native `env()` values which are correct
3. **Use CSS custom properties** as the injection target (`--safe-bottom`, `--safe-top`) — measure `env(...)` through a hidden probe element, then reference custom properties in Tailwind/CSS.
4. **Heuristic: `screen.height - window.innerHeight > 20` only for iPhone fallback**. Do not synthesize iPhone-style 34px on Android; Android's delta can include system chrome and lift bottom bars too high.

## CSS Usage Pattern

```css
:root {
  --safe-top: env(safe-area-inset-top, 0px);
  --safe-bottom: env(safe-area-inset-bottom, 0px);
}
/* Components use var(--safe-bottom) which the JS may override in standalone */
```

## Pitfalls

- **Don't hardcode 34px universally** — only apply when heuristic detects gesture navigation. Old iPhones with home buttons should get 0px.
- **Don't skip the `isStandalone` guard** — running in browser mode would double-count the inset.
- **Android PWA** may also have this issue with gesture navigation — `navigator.standalone` is iOS-only, but `display-mode: standalone` catches both.
- **Orientation changes** can change `screen.height` vs `window.innerHeight` — consider adding a `resize` listener if the app supports rotation. For fixed-portrait apps (like this one), the initial check suffices.
- **This is a polyfill, not a fix** — the real fix is Apple fixing WebKit. This approach degrades gracefully: if Apple fixes it, `env()` returns real values, the JS detects non-zero and skips.

## iOS PWA Icon Caching (apple-touch-icon / manifest icons)

iOS Safari caches `apple-touch-icon` and manifest icons at the **OS level**, not just browser cache level. Updating the file on the server + using cache-bust query params (`?v=20260529-v10`) is NOT sufficient — the "Add to Main Screen" dialog and installed PWA may still render the old icon for days/weeks.

### Why This Happens
- iOS downloads and caches the apple-touch-icon when the user first visits the site
- The cached icon persists even after the URL param changes
- Installed PWAs keep their icon until the SW activates a new version AND the user accepts the update prompt
- The service worker itself may not activate if `skipWaiting` is not configured

### Verification
```bash
# Confirm server serves the new icon (MD5 should match your local file)
curl -so /tmp/deployed-apple-touch.png 'https://<site>/apple-touch-icon.png?v=<version>'
md5 /tmp/deployed-apple-touch.png
md5 public/apple-touch-icon.png
# If MD5s match, the server is correct — the issue is iOS client caching
```

### What DOES NOT Fix It
- Changing `?v=` cache-bust parameter in `<link rel="apple-touch-icon">`
- Updating `icon-192.png` / `icon-512.png` in manifest
- Railway redeployment
- Clearing Safari tab cache (just the page cache, not icon cache)

### What DOES Fix It (User-Side)
1. **Settings → Safari → Clear History and Website Data** (full cache clear)
2. **Remove old PWA from Home Screen → re-add** (if already installed)
3. **Wait** (iOS garbage collects stale icon cache, can take days)

### Prevention for Future Icon Updates
- Set a very short `Cache-Control: max-age=300` on `/apple-touch-icon.png` during rollout, then extend after users have picked up the new icon
- For installed PWAs: ensure `skipWaiting` + `clientsClaim` in service worker so new SW activates immediately, and the manifest icons get refreshed on next PWA open
- **Full PWA version-iteration strategy** (cache-bust params, versioned SW cache names, build-number injection): see `pwa-cache-invalidation` skill

## Safe Area Layout Simplification (Anti-Pattern)

When multiple components independently compute their own safe-area padding,
the values **compound** and users see excessive spacing:

```
❌ App.tsx:   pb-[calc(96px+var(--safe-bottom))]   // 96px = TabBar height + extra
❌ Screen.tsx: pb-[calc(72px+env(safe-area-inset-bottom,0px))]
❌ TabBar.tsx: bottom: calc(10px + var(--safe-bottom))
```

Each adds its own constant on top of the safe area → total bottom gap = 96px + 34px = 130px.

**Fix**: Make `--safe-bottom` the single source of truth. Every component uses
`var(--safe-bottom)` directly, no extra constants:

```
✅ App.tsx:   pb-[var(--safe-bottom)]
✅ Screen.tsx: pb-[var(--safe-bottom)]
✅ TabBar.tsx: bottom: var(--safe-bottom)
```

TabBar sits flush against the safe-area edge. The scroll content's `pb-[var(--safe-bottom)]`
ensures the last item scrolls above TabBar. No extra `10px`, `18px`, `72px`, or `96px`.

**When changing safe-area CSS values, always grep for test assertions that
hardcode the old values** (e.g. `expect(nav).toHaveStyle({ bottom: 'calc(10px + var(--safe-bottom))' })`).
Tests that assert exact CSS strings break silently when values change.

## Cross-End Capability SDK Pointer

For device/system features whose behavior differs across H5, installed PWA/WebView, and native/hybrid shells (camera scan, geolocation, push, biometrics, file picker, share sheet), use `references/cross-end-capability-sdk.md`. The key rule is to split permission, device/session, and processing layers; do not let an optional processor API decide whether the base permission/device path is attempted.

## iOS PWA Splash Fullscreen Status Bar Contract

When an installed iOS PWA must show a fullscreen splash/loading surface, treat
`apple-mobile-web-app-status-bar-style` as a **viewport ownership contract**, not
as a theme color. In iOS Home Screen standalone mode:

- `content="default"` makes the WebView content area avoid the status bar / Dynamic Island; even `position: fixed; inset: 0` only fills the cropped content area, so the splash can look one status-bar slice short.
- `content="black-translucent"` lets web content draw underneath the status bar, so the startup splash can own the full drawable viewport.

Rules:
1. Keep the first-paint HTML meta as `black-translucent` when splash/loading is expected to cover the whole screen.
2. The meta must ship before the React module script; CSS/React cannot recover the area if the initial WebView was created with `default`.
3. Runtime theme sync may update `theme-color` for light/dark/system, but must not map light theme back to iOS status-bar `default` unless the product explicitly accepts a non-fullscreen splash.
4. Do not diagnose this as only `100vh` / `100dvh` / `.splash-root` height. If the WebView drawable area is cropped by status-bar mode, CSS height cannot fill the missing slice.
5. Keep normal page safe-area layout separate: splash fullscreen bugs are not the same as completed-page TopBar/main-content double safe-top bugs.

Regression gates:
- Unit/static test reads `index.html` and asserts `apple-mobile-web-app-status-bar-style` is `black-translucent` before the React module script.
- Test/scan that first-paint boot code has no `iosStatusBarStyle = 'default'` path.
- Theme-store tests assert light, dark, and system-resolved-light all keep iOS status bar `black-translucent` while `theme-color` can still change.
- Build artifact readback checks `dist/index.html`, not only source HTML.
- Visual proof should use installed iOS PWA early frames (T0/T1 splash/loading), not only Safari tab mode or completed-page screenshots.

Anti-patterns:
- Coupling `theme-color` and `apple-mobile-web-app-status-bar-style` as if both are harmless theme metadata.
- Fixing splash top/bottom gaps by changing TabBar, main page padding, or completed-page `--safe-top` math without verifying the startup status-bar mode.
- Letting recent commit diffs redefine the user's visual target; first separate T0 splash/loading, T1 skeleton, and T2 completed-page layout.

## Splash Anti-Repeat for Android PWA Rebuilds

In Android PWA standalone mode, the system back gesture can trigger a full
process rebuild — equivalent to re-opening `start_url`. The entire React tree
mounts from scratch and the splash animation replays, which feels broken.

**Fix**: Use `sessionStorage` to mark splash as shown. `sessionStorage` persists
across process rebuilds within the same browser session but clears on new sessions:

```tsx
const SPLASH_KEY = 'splash-shown';

export default function SplashScreen() {
  const alreadyShown =
    typeof sessionStorage !== 'undefined' && sessionStorage.getItem(SPLASH_KEY) === '1';
  const [visible, setVisible] = useState(!alreadyShown);

  useEffect(() => {
    if (alreadyShown) return;
    sessionStorage.setItem(SPLASH_KEY, '1');
    // ... animation timers
  }, [alreadyShown]);

  if (!visible) return null;
  // ...
}
```

**Why sessionStorage and not localStorage**: `localStorage` persists across
browser sessions → splash never plays on return visits. `sessionStorage` clears
when the user closes the browser or opens a new tab — correct boundary.

## Verification

After deploying, verify on a real iOS device in standalone mode:
1. TabBar should have visible gap above Home Indicator (~34px)
2. Main content bottom should not be clipped
3. Status bar area should not overlap top content (notch/Dynamic Island)
4. In Safari browser mode, layout should be identical (JS doesn't run)
5. On Android PWA: back gesture → forward → splash should NOT replay
