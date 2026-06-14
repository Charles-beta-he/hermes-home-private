# PWA Standalone Tab Safe-Area Normalization

## Trigger

Use when the mobile H5/browser version looks correct, but installed PWA standalone on iOS and Android has inconsistent bottom safe-area behavior: TabBar floats too high, leaves too much blank space, or content padding is double-counted.

## Durable pattern

Do not let the TabBar and scroll container consume raw `env(safe-area-inset-bottom)` independently. Installed PWA environments report safe-area values differently across iOS and Android, and Android often should not receive an iPhone-style bottom inset.

Instead, install runtime mode/platform markers and derive normalized app-level tokens:

```ts
// Run before React render, ideally from main.tsx.
document.documentElement.dataset.platform = 'ios' | 'android' | 'other';
document.documentElement.dataset.displayMode = 'standalone' | 'browser';
```

```css
:root {
  --safe-top: env(safe-area-inset-top, 0px);
  --system-safe-bottom: env(safe-area-inset-bottom, 0px);
  --app-safe-bottom: var(--system-safe-bottom);
  --safe-bottom: var(--app-safe-bottom); /* compatibility alias */
  --tabbar-height: 56px;
  --tabbar-bottom-gap: var(--app-safe-bottom);
  --tabbar-content-reserve: calc(var(--tabbar-height) + var(--tabbar-bottom-gap) + 8px);
}

[data-display-mode="standalone"][data-platform="ios"] {
  --app-safe-bottom: clamp(8px, var(--system-safe-bottom), 18px);
}

[data-display-mode="standalone"][data-platform="android"] {
  --app-safe-bottom: clamp(0px, var(--system-safe-bottom), 8px);
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

- H5/browser: TabBar height 56, viewport bottom gap 0, main padding 64px.
- Android standalone: TabBar height 56, viewport bottom gap 0, main padding 64px.
- iOS standalone: TabBar height 56, viewport bottom gap around 8px, main padding around 72px.

## Pitfalls

- Do not solve by hard-coding `bottom: 0/10/18px` on TabBar; it will regress one platform while fixing another.
- Do not synthesize Android bottom inset from `screen.height - innerHeight`; that can include browser/system chrome and create over-offset.
- Do not update only TabBar. If the scroll container still uses a different padding formula, the visual gap can remain even when TabBar is positioned correctly.
- If local preview logs API proxy `ECONNREFUSED`, classify whether the layout proof actually depends on API data. For layout-only TabBar measurement, seed auth/local state or use a route where chrome renders; do not treat missing backend as a layout failure.