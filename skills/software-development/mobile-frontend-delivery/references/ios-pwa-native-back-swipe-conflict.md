# iOS installed PWA native back-swipe vs custom SPA swipe

Use this when iOS “Add to Home Screen” PWA shows a blank/white screen while returning from deep flow pages to a main tab, especially after repeated left-edge swipes across assets/topup/exchange/payout/card/wealth/me subpages.

## Symptom pattern

- Only occurs in iOS standalone PWA / Add to Home Screen, not ordinary Android/native shells.
- Trigger paths vary widely, but share the same shape:

```text
main tab -> multiple flow/detail pages -> left-edge swipe back repeatedly -> main tab white/blank snapshot
```

- A video may show a transient or persistent near-empty app background frame between a deep page and the main tab.
- The breadth of affected business pages is a signal that the root is global navigation/gesture handling, not each screen.

## Root cause to check first

Look for a custom left-edge touch handler in the SPA shell, commonly named `useSwipeBack`, `useBackSwipe`, `edgeSwipe`, or similar. If it calls `navigate(-1)` on `touchend`, it can conflict with iOS Safari’s native interactive back-swipe in standalone PWA.

On iOS PWA, a single physical left-edge swipe can produce two backs:

1. Safari/PWA native history back.
2. React Router / SPA custom `navigate(-1)` from the touch handler.

That double-pop can outrun route rendering/history state and leave the standalone PWA showing a blank snapshot while React catches up.

## Fix pattern

Do not add per-page back hacks. Gate the global custom swipe handler by runtime:

```ts
function isIosWebRuntime() {
  if (typeof navigator === 'undefined') return false;
  const ua = navigator.userAgent || '';
  const maxTouchPoints = navigator.maxTouchPoints || 0;
  return /iPad|iPhone|iPod/.test(ua) || (/Macintosh/.test(ua) && maxTouchPoints > 1);
}

const shouldUseCustomSwipe = Capacitor.isNativePlatform() || !isIosWebRuntime();
```

Then no-op `onTouchStart` / `onTouchEnd` when `shouldUseCustomSwipe` is false, so ordinary iOS Safari browser delegates left-edge back to Safari. Keep Capacitor native and non-iOS web behavior unchanged.

For iOS profile-installed/fullscreen PWA Web Clips, do **not** blindly delegate to Safari. A profile Web Clip can expose native history swipe while hiding browser chrome; repeated swipes can fall through to the empty Web Clip launch snapshot. Detect `navigator.standalone === true` or `matchMedia('(display-mode: standalone|fullscreen)')`, suppress the native edge gesture with `preventDefault()` on edge `touchstart`/`touchmove`/`touchend`, and issue exactly one SPA `navigate(-1)` on sub-routes. On main-tab routes, swallow the gesture after suppression. Also keep a same-URL history guard entry armed on main tabs for iOS standalone/profile PWA so native back cannot escape to a blank snapshot if suppression is bypassed.

## Regression tests

Add/keep hook-level tests for all branches:

- Android/non-iOS web: qualifying edge swipe still calls `navigate(-1)` on subpages.
- iPhone/iOS standalone PWA UA: qualifying edge swipe does **not** call `navigate(-1)` and does not call `exitApp()`.
- Capacitor native main tabs: qualifying edge swipe still calls `exitApp()`.
- Main-tab route list stays synced with TabBar.

## Verification

- Run the swipe hook tests and main-tab history guard tests.
- Run build/typecheck.
- For manual QA on a real iPhone installed PWA: repeat at least one long chain from each main area (Assets, U-VISA/Card, Me) and verify repeated left-swipes return to the tab page without blank frames.

## Pitfalls

- Do not diagnose this as a business-page bug just because many flows list different screens; the common denominator is the global shell gesture.
- Do not rely only on browser desktop/mobile emulation: the bug depends on iOS standalone PWA native gesture ownership.
- Do not disable native Android/Capacitor back handling while fixing iOS PWA; they are different surfaces.
