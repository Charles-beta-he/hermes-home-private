# Android PWA TabBar bottom-gap regression

Use when an Android installed PWA/WebAPK shows the bottom TabBar too far above the visible bottom, while browser/iOS surfaces should remain unchanged.

## Symptom

- User reports Android-only TabBar is too far from viewport bottom.
- TabBar height itself is normal (`getBoundingClientRect().height` around the expected token, e.g. 52px), but `visualViewport.height - nav.getBoundingClientRect().bottom` is too large.
- Screenshots may look like the whole Home page is visually shifted upward after returning from scroll-heavy flow pages.

## Root-cause pattern

A common regression is double-counting Android bottom safety:

```css
:root {
  --android-standalone-tabbar-safe-baseline: 32px;
  --tabbar-visual-bottom-gap: 16px;
  --tabbar-bottom-gap: calc(var(--tabbar-safe-baseline) + var(--tabbar-visual-bottom-gap));
}
[data-display-mode="standalone"][data-platform="android"] {
  --tabbar-safe-baseline: var(--android-standalone-tabbar-safe-baseline);
  --tabbar-bottom-gap: calc(var(--tabbar-safe-baseline) + var(--tabbar-visual-bottom-gap));
}
```

This lifts Android standalone TabBar by 48px before any app-canvas trim or system gesture area effect. If the app already trims the Android canvas (for example `#phone-portal { height: calc(100dvh - 16px); }`), the perceived gap can become even larger.

## Debug recipe

1. Compare source branch vs deployed/test bundle. Do not assume local source equals the PWA running on the phone; service-worker and environment branches can be stale.
2. Inspect the built CSS, not only source:
   - find the emitted `dist/assets/index-*.css`
   - grep/slice around `[data-display-mode=standalone][data-platform=android]`
   - verify Android selector values after minification.
3. Measure in Android Chrome/DevTools:

```js
(() => {
  const root = document.documentElement;
  const nav = document.querySelector('nav[aria-label], nav');
  const r = nav?.getBoundingClientRect();
  const vv = window.visualViewport;
  const cs = nav && getComputedStyle(nav);
  const rootCs = getComputedStyle(root);
  return {
    dataset: {...root.dataset},
    innerHeight,
    visualHeight: vv?.height,
    navRect: r && {top: r.top, bottom: r.bottom, height: r.height},
    distanceToVisualBottom: r && vv ? vv.offsetTop + vv.height - r.bottom : null,
    cssBottom: cs?.bottom,
    tokens: {
      tabbarHeight: rootCs.getPropertyValue('--tabbar-height').trim(),
      tabbarBottomGap: rootCs.getPropertyValue('--tabbar-bottom-gap').trim(),
      tabbarContentReserve: rootCs.getPropertyValue('--tabbar-content-reserve').trim(),
      tabbarSafeBaseline: rootCs.getPropertyValue('--tabbar-safe-baseline').trim(),
      tabbarVisualGap: rootCs.getPropertyValue('--tabbar-visual-bottom-gap').trim(),
      androidBaseline: rootCs.getPropertyValue('--android-standalone-tabbar-safe-baseline').trim(),
    }
  };
})()
```

Interpretation:

- `height` too large → TabBar sizing/children issue.
- `height` correct but `cssBottom`/token gap large → bottom-gap token issue.
- `cssBottom: 0px` but `distanceToVisualBottom` still positive → parent canvas trim / visualViewport / system gesture area issue.

## Safe fix shape

When the requirement is explicitly Android PWA only and iOS/browser must not change, patch only the Android standalone selector:

```css
[data-display-mode="standalone"][data-platform="android"] {
  --tabbar-safe-baseline: 0px;
  --tabbar-bottom-gap: 0px;
  --tabbar-content-reserve: calc(var(--tabbar-height) + 8px);
}
```

Leave iOS standalone and browser default rules unchanged unless evidence shows they are affected.

If the remaining Android gap equals a known app-canvas trim (for example 16px), stop and report that as a separate Android canvas/system-bar boundary. Do not remove the canvas trim in the same change unless the user explicitly wants physical 0px-to-visual-viewport and accepts underlap risk.

## Verification checklist

- Targeted layout test asserts Android standalone uses `--tabbar-bottom-gap: 0px` and iOS/browser rules remain unchanged.
- Build passes.
- Built CSS readback confirms the minified Android selector has `--tabbar-bottom-gap:0px`.
- Android runtime measurement confirms:
  - TabBar height equals expected token.
  - Android standalone CSS bottom is 0px.
  - Remaining distance, if any, is attributable to app-canvas trim / viewport boundary, not TabBar bottom gap.
