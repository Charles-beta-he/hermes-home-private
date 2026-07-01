# PWA TabBar top-anchor from visual height

Use when a bottom TabBar exists in DOM but disappears or is clipped specifically in installed PWA / WebView / simulator modes, and prior bottom-owned or conditional top-fallback repairs still fail on real devices.

## Applicability

- Mobile SPA/PWA has a floating bottom TabBar rendered as app chrome, usually `position:absolute` inside a fixed/overflow-hidden app canvas.
- Browser/mobile harness may show the TabBar, but installed PWA / WebView / simulator hides it or clips it near the bottom edge.
- The component is not route-missing: `[data-tabbar-root]` or the navigation role exists.
- The app already has platform/display-mode tokens such as `data-platform`, `data-display-mode`, `--tabbar-height`, `--tabbar-bottom-gap`, and an app shell height token.

## Anti-conditions

- Do not use this if the TabBar route predicate is false or the component is not rendered.
- Do not use this to mask a login/auth redirect or splash overlay that removes the route.
- Do not remove platform-specific bottom-gap baselines; move only the final chrome positioning model from `bottom` to `top`.
- Do not write device-specific constants before measuring `visualViewport.height`, `innerHeight`, and the TabBar rect.

## Pattern

1. Keep all platform-specific spacing in `--tabbar-bottom-gap`:
   - browser/iOS can keep the shared visual gap,
   - Android standalone can add its bounded visual bottom inset or system-nav baseline.
2. Define a single top anchor from the measured app visual height:

```css
:root {
  --app-visual-height: 100dvh;
  --tabbar-height: 52px;
  --tabbar-bottom-gap: calc(var(--tabbar-safe-baseline) + var(--tabbar-visual-bottom-gap));
  --tabbar-top: calc(var(--app-visual-height, 100dvh) - var(--tabbar-height) - var(--tabbar-bottom-gap));
}

.tabbar-glass {
  top: var(--tabbar-top);
  bottom: auto;
}
```

3. Reconcile `--app-visual-height` from runtime viewport metrics for every platform, not only Android recovery paths:

```ts
export function reconcileAppVisualHeight(root: HTMLElement = document.documentElement) {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;
  if (isEditableElement(document.activeElement)) return;
  const height = Math.round(window.visualViewport?.height ?? window.innerHeight);
  if (height > 0) root.style.setProperty('--app-visual-height', `${height}px`);
}
```

Call this from the normal viewport settle path and stronger manual viewport check path, before TabBar reconciliation.

## Verification checklist

- Component/layout test: normal TabBar still has `data-tabbar-root` and no JSX inline style.
- CSS test: `--tabbar-top` is calculated from `--app-visual-height - --tabbar-height - --tabbar-bottom-gap`.
- CSS test: `.tabbar-glass` uses `top: var(--tabbar-top); bottom: auto;`.
- Runtime test: `reconcileAppVisualHeight()` writes `--app-visual-height` from `visualViewport.height`.
- Mobile harness: verify iPhone browser, Android browser, iPhone standalone, Android standalone; assert `[data-tabbar-root]` exists, `display:flex`, opacity visible, and `rect.top >= 0 && rect.bottom <= visualViewport.height + offsetTop`.
- Build after tests; minified CSS should still include `--tabbar-top` and `top:var(--tabbar-top)` markers.

## Pitfall

A conditional top fallback can be too conservative when the shell itself clips bottom-owned chrome before the measured rect looks obviously offscreen. If PWA mode still misses the TabBar after a bottom-owned fix, top-anchor all normal TabBar placement from app visual height instead of repeatedly tuning bottom gaps.
