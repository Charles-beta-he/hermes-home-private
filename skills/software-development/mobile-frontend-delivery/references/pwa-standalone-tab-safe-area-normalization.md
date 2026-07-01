# PWA Standalone Tab Safe-Area Normalization

## Trigger

Use when the mobile H5/browser version looks correct, but installed PWA standalone on iOS and Android has inconsistent bottom safe-area behavior: TabBar floats too high, leaves too much blank space, or content padding is double-counted.

## Durable pattern

Do not let the TabBar and scroll container consume raw `env(safe-area-inset-bottom)` independently. Installed PWA environments report safe-area values differently across iOS and Android, and the same physical-looking "safe height" can mean opposite things by platform.

When screenshots show **iOS has an extra blank strip under the TabBar but Android is correct only when a bottom safety height is present**, use a static platform-baseline model rather than dynamic viewport measurement:

- iOS installed PWA: baseline should be `0px`; the PWA/Home Indicator area is already owned by the shell, and adding the safe height double-counts it into bottom blank space.
- Android installed PWA: baseline should be the Android system-navigation safety height; otherwise clear-cache/cold launches can hide the TabBar behind the system navigation area.
- Select the baseline via stable `data-platform` + `data-display-mode` markers set before React render. Do not feed theme-switch or `visualViewport` deltas into TabBar placement.
- TabBar `bottom` and scroll `padding-bottom`/reserve must consume the same baseline token so the visible position and content reserve do not diverge.

Instead, install runtime mode/platform markers and derive normalized app-level tokens:

```ts
// Run before React render, ideally from main.tsx.
document.documentElement.dataset.platform = 'ios' | 'android' | 'other';
document.documentElement.dataset.displayMode = 'standalone' | 'browser';
```

```css
:root {
  --safe-top: env(safe-area-inset-top, 0px);
  --safe-bottom: env(safe-area-inset-bottom, 0px);
  --tabbar-height: 52px;
  --android-standalone-tabbar-safe-baseline: 32px;
  --ios-standalone-tabbar-safe-baseline: 0px;
  --tabbar-safe-baseline: 0px;
  --tabbar-scroll-extra-gap: 8px;
  --tabbar-bottom-gap: var(--tabbar-safe-baseline);
  --tabbar-content-reserve: calc(var(--tabbar-height) + var(--tabbar-safe-baseline) + var(--tabbar-scroll-extra-gap));
}

[data-display-mode="standalone"][data-platform="ios"] {
  --tabbar-safe-baseline: var(--ios-standalone-tabbar-safe-baseline);
  --tabbar-scroll-extra-gap: 0px;
}

[data-display-mode="standalone"][data-platform="android"] {
  --tabbar-safe-baseline: var(--android-standalone-tabbar-safe-baseline);
  --tabbar-scroll-extra-gap: 8px;
}
```

Then make both shell chrome and scroll reserves use the same normalized tokens:

```tsx
<TabBar style={{ bottom: 'var(--tabbar-bottom-gap)' }} />
<main className="pb-[var(--tabbar-content-reserve)]" />
<Screen withTabBar className="pb-[var(--tabbar-content-reserve)]" />
```

## Verification recipe

1. Unit-test platform/display-mode detection:
   - `navigator.standalone === true` => standalone on iOS.
   - `matchMedia('(display-mode: standalone)').matches` => standalone on Android/PWA.
   - browser mode remains `data-display-mode="browser"`.
2. Unit-test layout contracts:
   - TabBar `bottom` uses `--tabbar-bottom-gap`, not raw `--safe-bottom`.
   - tab-page scroll region uses `--tabbar-content-reserve`.
   - shared `Screen withTabBar` uses the same reserve token.
3. Build and run a preview measurement with an authenticated/seeded state if TabBar is auth-gated. Measure:
   - `data-platform`, `data-display-mode`
   - computed `--app-safe-bottom`, `--tabbar-bottom-gap`, `--tabbar-content-reserve`
   - TabBar height and gap to viewport bottom
   - main scroll padding-bottom

Expected baseline when the browser reports raw bottom safe-area as `0px`:

- H5/browser: TabBar height from the app token, viewport bottom gap 0, main padding = TabBar height + small scroll affordance.
- Android standalone: TabBar height from the app token, bottom gap = Android system-nav safety baseline (for example 32px), main padding = TabBar height + Android baseline + scroll affordance.
- iOS standalone: TabBar height from the app token, bottom gap 0, main padding = TabBar height only (or TabBar height + explicit product affordance if visually required). Do not add Home Indicator safe-area again.

## iOS PWA theme-mode safe-area drift

If an installed iOS PWA's bottom TabBar height/gap changes when switching app day/night mode, suspect raw `env(safe-area-inset-bottom)` being re-resolved through `color-scheme` or system chrome changes. This can happen even when browser H5 and Android are already fixed.

Fix pattern:

```css
:root {
  --safe-bottom: env(safe-area-inset-bottom, 0px);
  --tabbar-height: 52px;
  --ios-standalone-tabbar-safe-baseline: 0px;
  --android-standalone-tabbar-safe-baseline: 32px;
  --tabbar-safe-baseline: 0px;
  --tabbar-bottom-gap: var(--tabbar-safe-baseline);
  --tabbar-content-reserve: calc(var(--tabbar-height) + var(--tabbar-safe-baseline));
}

[data-display-mode="standalone"][data-platform="ios"] {
  /* iOS PWA already owns the Home Indicator area; do not double-count it. */
  --tabbar-safe-baseline: var(--ios-standalone-tabbar-safe-baseline);
}

[data-display-mode="standalone"][data-platform="android"] {
  /* Android needs the system-nav safety baseline to keep TabBar visible. */
  --tabbar-safe-baseline: var(--android-standalone-tabbar-safe-baseline);
}
```

Keep browser/H5 and Android/iOS standalone paths separate. Scope iOS to a 0 baseline when screenshots show bottom blank space, and keep Android on its system-nav baseline when screenshots show clear-cache/cold launches can hide the TabBar. Avoid dynamic `visualViewport` writes for TabBar placement; they can reintroduce theme-switch drift.

Regression tests should assert:

- the TabBar uses `bottom: var(--tabbar-bottom-gap)`, not raw `--safe-bottom`;
- installed iOS PWA CSS sets the TabBar safe baseline from an iOS-specific 0 token;
- installed Android PWA CSS sets the TabBar safe baseline from an Android-specific safety token;
- installed iOS PWA CSS does not set `--tabbar-bottom-gap: var(--safe-bottom)` and does not consume Android visual-inset tokens;
- scroll reserve uses the same `--tabbar-content-reserve` / baseline token chain as the TabBar bottom;
- the production build CSS still contains both iOS and Android standalone selectors after minification.

## Platform-baseline + visual-gap model

When iOS and Android need different treatment for the same bottom "safe height", split the model into two tokens instead of one overloaded `safe-bottom` value:

```css
:root {
  --tabbar-height: 52px;
  --ios-standalone-tabbar-safe-baseline: 0px;
  --android-standalone-tabbar-safe-baseline: 32px;
  --tabbar-safe-baseline: 0px;
  --tabbar-visual-bottom-gap: 8px;
  --tabbar-bottom-gap: calc(var(--tabbar-safe-baseline) + var(--tabbar-visual-bottom-gap));
  --tabbar-content-reserve: calc(var(--tabbar-height) + var(--tabbar-bottom-gap));
}

[data-display-mode="standalone"][data-platform="ios"] {
  --tabbar-safe-baseline: var(--ios-standalone-tabbar-safe-baseline);
}

[data-display-mode="standalone"][data-platform="android"] {
  --tabbar-safe-baseline: var(--android-standalone-tabbar-safe-baseline);
}
```

Use stable `data-platform` + `data-display-mode` markers set before React render as the discriminator. iOS installed PWA already owns the Home Indicator area, so its baseline should usually be `0`; Android installed PWA may need a system-navigation baseline to prevent the TabBar being hidden after cold launch / cache clear. Keep any desired visual breathing room (for example `8px`) as a separate app-owned visual gap applied to both platforms.

## Browser vs standalone viewport ownership

Applicability: mobile web/PWA app shells where Safari browser mode looks correct, but iOS installed standalone PWA shows bottom blank space, bottom clipping, or a gray/crop strip near the Home Indicator area. Anti-condition: do not apply this pattern to native apps, non-PWA browser-only pages, or cases where only the TabBar is mispositioned while main scroll content remains correctly painted.

When Safari browser mode is correct but iOS installed PWA shows bottom blank space, bottom clipping, or a gray/crop strip, do not assume the TabBar baseline is wrong. Separate three layers before fixing:

1. **TabBar baseline/gap**: `bottom: var(--tabbar-bottom-gap)` and scroll reserve should share the normalized platform baseline.
2. **Phone/app canvas height**: the app canvas may need a standalone/iOS override, but avoid raw `100lvh` on iOS PWA because it can exceed the visible clipped screen.
3. **Root/body render boundary**: a fixed `html/body` workaround that is correct for Safari browser drag-scroll can itself become the iOS standalone crop source and cover both TabBar and main content.

Use display-mode/platform scoping:

- `display-mode="browser"`: keep the app canvas on the component's `dvh`/browser-aware path, because Safari toolbars are real chrome and must reduce the visible web viewport. A fixed `html/body` lock can be acceptable here to prevent dragging the app shell into body whitespace.
- `display-mode="standalone"` + `platform="android"`: preserve the Android-safe baseline and, if already validated, keep the conservative root lock rather than changing Android while fixing iOS.
- `display-mode="standalone"` + `platform="ios"`: do **not** blindly inherit the browser fixed-body path. iOS WebKit can resolve a fixed body/containing block above the fullscreen drawable bottom, exposing a bottom compositor/root strip over both app chrome and scroll content.

Safer pattern when iOS PWA crop affects both TabBar and content:

```css
html, body, #root {
  height: 100%;
  min-height: 100%;
  overflow: hidden;
  background-color: var(--surface-base);
}
html, body {
  margin: 0;
  width: 100%;
}
[data-display-mode="browser"],
[data-display-mode="browser"] body,
[data-display-mode="standalone"][data-platform="android"],
[data-display-mode="standalone"][data-platform="android"] body {
  position: fixed;
  inset: 0;
}
[data-display-mode="standalone"][data-platform="ios"] #app-canvas {
  height: 100%;
  min-height: 100%;
}
[data-theme="dark"] html,
[data-theme="dark"] body,
[data-theme="dark"] #root {
  background-color: var(--surface-dark);
}
```

Do not switch TabBar from absolute to fixed just because the TabBar appears clipped. If the main scroll content is also covered by the same gray/crop strip, the root/body/app-canvas boundary is the failing layer; fixing TabBar positioning only masks one symptom and leaves content clipped. Scope standalone viewport overrides to the platform that demonstrates the failure. If Android PWA is already correct, prefer `[data-display-mode="standalone"][data-platform="ios"]` over a broad `[data-display-mode="standalone"]` override.

## Pitfalls

- Do not solve by hard-coding `bottom: 0/10/18px` on TabBar globally; it will regress one platform while fixing another.
- Do not use one "safe height" as both platform system avoidance and visual spacing. Split platform baseline from visual gap; otherwise iOS double-counts the Home Indicator while Android still needs system-nav avoidance.
- Do not use `100lvh` as an iOS PWA quick fix for bottom blank space without device proof; it can make the app shell taller than the visible clipped screen and leave the TabBar visually hidden under the bottom edge.
- Do not apply iOS standalone viewport fixes broadly to Android if Android is already validated. Scope by `data-display-mode` and `data-platform`.
- Do not synthesize Android bottom inset from `screen.height - innerHeight`; that can include browser/system chrome and create over-offset.
- Do not feed `visualViewport` deltas into TabBar placement if stable platform markers and fixed baselines suffice; theme switches can re-trigger viewport measurements and move the TabBar after first render.
- Do not let iOS installed PWA TabBar geometry depend directly on raw `env(safe-area-inset-bottom)` when app theme changes can update `color-scheme`; normalize the app-level token instead.
- Do not update only TabBar. If the scroll container still uses a different padding formula, the visual gap can remain even when TabBar is positioned correctly.
- If local preview logs API proxy `ECONNREFUSED`, classify whether the layout proof actually depends on API data. For layout-only TabBar measurement, seed auth/local state or use a route where chrome renders; do not treat missing backend as a layout failure.
- Do not update only TabBar. If the scroll container still uses a different padding formula, the visual gap can remain even when TabBar is positioned correctly.
- If local preview logs API proxy `ECONNREFUSED`, classify whether the layout proof actually depends on API data. For layout-only TabBar measurement, seed auth/local state or use a route where chrome renders; do not treat missing backend as a layout failure.
