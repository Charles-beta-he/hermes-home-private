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
  var s = getComputedStyle(root);
  var envBottom = s.getPropertyValue('env(safe-area-inset-bottom)').trim();
  var envTop    = s.getPropertyValue('env(safe-area-inset-top)').trim();

  var isStandalone =
    window.navigator.standalone === true ||                       // iOS Safari
    window.matchMedia('(display-mode: standalone)').matches;      // Android / desktop

  if (!isStandalone) return;

  // --- bottom (Home Indicator / gesture bar) ---
  if (!envBottom || envBottom === '0px' || envBottom === '0') {
    // screen.height - window.innerHeight delta is the most reliable heuristic
    var bottomInset = screen.height - window.innerHeight;
    var safeBot = bottomInset > 20 ? '34px' : '0px';
    root.style.setProperty('--safe-bottom', safeBot);
  }

  // --- top (notch / Dynamic Island) ---
  if (!envTop || envTop === '0px' || envTop === '0') {
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
3. **Use CSS custom properties** as the injection target (`--safe-bottom`, `--safe-top`) — then reference these in your Tailwind/CSS alongside the `env()` fallback
4. **Heuristic: `screen.height - window.innerHeight > 20`** reliably distinguishes gesture-nav devices (34px inset) from old home-button devices (0px inset)

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
