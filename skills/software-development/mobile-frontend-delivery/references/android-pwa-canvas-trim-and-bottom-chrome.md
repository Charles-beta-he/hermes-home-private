# Android PWA canvas trim vs bottom chrome gaps

Use when Android installed PWA/WebAPK shows bottom content, TabBar, BottomSheet, or full-screen portals extending into or being clipped by the gesture/navigation area, while iOS standalone has separate first-screen/fullscreen viewport behavior.

## Core diagnosis

Do not treat all bottom-space symptoms as one `safe-bottom` problem. Separate three concepts:

1. App canvas correction
   - The size of `#phone-portal` / app shell.
   - Android WebAPK/Chrome can expose `100dvh` as extending under the system gesture/navigation affordance.
   - If product/device evidence shows `height: calc(100dvh - 40px)` is the correct Android result, keep that correction Android-standalone-only.
   - If the number is merely a developer hard-code rather than device evidence, prefer `env(safe-area-inset-bottom, 0px)` for the Android standalone canvas trim and verify the computed value on the affected device.

2. Bottom chrome placement
   - TabBar `bottom` / visual floating gap.
   - If the app canvas is already trimmed by a proven system-area value, do not also add a large Android baseline or full visual bottom gap to the TabBar. That double-counts the system area and lifts the TabBar too far from the visible bottom.
   - If the canvas trim comes from `env(safe-area-inset-bottom, 0px)` and can be `0px` on Android, keep a narrow Android-only TabBar chrome gap (for example 8px) so the pill is not flush to the canvas. This is not the old 32px baseline + 16px visual gap.

3. Scroll/content reserve
   - The padding that keeps the last content readable behind bottom chrome.
   - It should account for TabBar height plus the actual TabBar bottom gap and a small readability allowance, not blindly include canvas trim or Android system-baseline again.

## Recommended CSS model

```css
:root {
  --tabbar-height: 52px;
  --tabbar-visual-bottom-gap: 16px;
  --tabbar-safe-baseline: 0px;
  --tabbar-bottom-gap: calc(var(--tabbar-safe-baseline) + var(--tabbar-visual-bottom-gap));
  --tabbar-content-reserve: calc(var(--tabbar-height) + var(--tabbar-bottom-gap));
  --android-standalone-canvas-bottom-trim: 0px;
  --android-standalone-tabbar-bottom-gap: 8px;
}

/* Browser/iOS can keep the floating visual gap. */
[data-display-mode="standalone"][data-platform="ios"] {
  --tabbar-safe-baseline: 0px;
  --tabbar-bottom-gap: calc(var(--tabbar-safe-baseline) + var(--tabbar-visual-bottom-gap));
  --tabbar-content-reserve: calc(var(--tabbar-height) + var(--tabbar-bottom-gap));
}

/* Android standalone: canvas uses platform env; TabBar keeps only a narrow chrome gap. */
[data-display-mode="standalone"][data-platform="android"] {
  --android-standalone-canvas-bottom-trim: env(safe-area-inset-bottom, 0px);
  --tabbar-safe-baseline: 0px;
  --tabbar-bottom-gap: var(--android-standalone-tabbar-bottom-gap);
  --tabbar-content-reserve: calc(var(--tabbar-height) + var(--tabbar-bottom-gap) + 8px);
}

[data-display-mode="standalone"][data-platform="android"] #phone-portal {
  height: calc(100dvh - var(--android-standalone-canvas-bottom-trim));
  min-height: calc(100dvh - var(--android-standalone-canvas-bottom-trim));
}
```

If real-device evidence proves `env(safe-area-inset-bottom)` is too small for a specific Android shell, introduce a separate bounded Android visual-inset token instead of restoring a broad hard-coded canvas trim or moving the value to iOS/generic safe-area rules.


## BottomSheet / portal rule

If BottomSheet, toast, modal, or full-screen portal is portaled into `#phone-portal` and positioned with `absolute inset-0`, the Android canvas trim becomes the shared safe containing block. Prefer fixing `#phone-portal` once over adding Android-specific bottom padding to every sheet.

Avoid this double-count:

```css
[data-display-mode="standalone"][data-platform="android"] {
  --android-standalone-canvas-bottom-trim: 40px;
  --tabbar-bottom-gap: 48px; /* wrong: canvas trim + bottom gap */
}
```

## Verification checklist

- Android standalone computed CSS:
  - `--android-standalone-canvas-bottom-trim` equals the intended trim, e.g. `40px`.
  - `#phone-portal` height is `calc(100dvh - var(--android-standalone-canvas-bottom-trim))`.
  - TabBar `bottom` is `0px` when canvas trim is active.
  - TabBar height remains its fixed token, e.g. `52px`.
- iOS standalone computed CSS:
  - `#phone-portal` uses `100vh` / `100lvh`, not `calc(100dvh - Npx)`.
  - iOS is excluded from fixed-body/crop paths intended for Android/browser.
- Browser/H5:
  - Android trim token stays `0px` unless both `data-display-mode="standalone"` and `data-platform="android"` are present.
- Regression tests should assert platform selectors, not just a screenshot.
