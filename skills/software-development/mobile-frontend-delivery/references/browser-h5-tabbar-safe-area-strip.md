# Browser H5 TabBar safe-area strip vs Liquid Glass

Scope: browser-based mobile H5/PWA frontends with a floating bottom TabBar / bottom navigation that should render as iOS-style Liquid Glass.
Applicability: use when screenshots show a solid background strip under or behind the TabBar even though the TabBar component appears to use glass/blur styling.
Anti-condition: do not apply this as a universal installed-PWA rule; standalone apps may intentionally need a bounded gesture/home-indicator inset.

## Symptom

- The TabBar itself has the right glass styling (`background: rgba(...)`, `backdrop-filter`, rounded corners, shadow), but the screenshot still looks wrong.
- A solid page/canvas-colored strip is visible below the TabBar or behind its bottom area.
- The issue appears on online/browser H5 even though local preview or component tests say the `.glass` class exists.

## Root cause pattern

Separate **glass styling** from **viewport positioning**.

A TabBar can match the prototype internally while still failing visually if it is lifted by a safe-area variable in browser mode:

```css
--tabbar-bottom-gap: var(--app-safe-bottom); /* risky for browser H5 */
```

If `--app-safe-bottom` resolves from `env(safe-area-inset-bottom)` while the app is running in a browser tab, the nav is raised and the real bottom of the viewport exposes the app surface color. The user perceives this as an extra bottom background and “not Liquid Glass”.

## Fix pattern

Use different defaults for browser H5 and installed standalone mode:

```css
:root {
  --system-safe-bottom: env(safe-area-inset-bottom, 0px);
  --app-safe-bottom: var(--system-safe-bottom);
  --safe-bottom: var(--app-safe-bottom);
  --tabbar-height: 56px;

  /* Browser H5: keep glass flush with viewport bottom; no extra strip. */
  --tabbar-bottom-gap: 0px;
  --tabbar-content-reserve: calc(var(--tabbar-height) + var(--tabbar-bottom-gap) + 8px);
}

[data-display-mode="standalone"][data-platform="ios"] {
  --app-safe-bottom: clamp(8px, var(--system-safe-bottom), 18px);
  --tabbar-bottom-gap: var(--app-safe-bottom);
}

[data-display-mode="standalone"][data-platform="android"] {
  --app-safe-bottom: clamp(0px, var(--system-safe-bottom), 8px);
  --tabbar-bottom-gap: var(--app-safe-bottom);
}
```

Then position the nav with the TabBar-specific variable, not directly with the global safe-area variable:

```tsx
<nav
  className="absolute left-4 right-4 z-[100] h-[var(--tabbar-height)] rounded-32 glass shadow-tab flex"
  style={{
    bottom: 'var(--tabbar-bottom-gap)',
    backdropFilter: 'blur(40px) saturate(200%)',
    WebkitBackdropFilter: 'blur(40px) saturate(200%)',
  }}
/>
```

Keep the scroll container extended to the viewport bottom and reserve readable content space with padding, not by clipping the scroll viewport above the TabBar:

```tsx
mainClassForTabPage = 'top-[calc(<topbar-height>+var(--safe-top))] bottom-0 pb-[var(--tabbar-content-reserve)]'
```

## Verification checklist

1. Compare against the prototype at two levels:
   - Glass body: class, background rgba, blur/saturate, border, radius, shadow, active pill.
   - Placement: height, bottom offset, viewport bottom gap, scroll-container bottom/padding.
2. In browser H5 computed style, require:
   - `--tabbar-bottom-gap == 0px`
   - nav `bottom == 0px`
   - nav `getBoundingClientRect().bottom == window.innerHeight`
   - `backdrop-filter` / `-webkit-backdrop-filter` includes `blur(...)` and `saturate(...)`
3. Test all primary tab pages named by the task, not just the default tab.
4. Add a regression test that proves browser H5 keeps `--tabbar-bottom-gap: 0px` while standalone iOS/Android set `--tabbar-bottom-gap: var(--app-safe-bottom)`.
5. For hosted/prod verification, do not stop at PR merged or checks green. Fetch the live HTML, extract CSS/JS asset hashes, fetch the CSS, and search for a deterministic marker such as `--tabbar-bottom-gap:0px`.

## Local backend note for visual checks

For purely visual TabBar checks, avoid letting auth/backend setup hide the UI. If the user wants local UI connected to an online backend, set the API base explicitly (for Vite apps, commonly `VITE_API_BASE=https://<online-host>/api`) rather than assuming the dev proxy points online. In Vite dev, `/api` often proxies to a local default unless `VITE_DEV_API_PROXY_TARGET` is configured.

Use real online auth/session when final acceptance requires data correctness or production UI evidence; use a temporary visual-only token only to inspect unauthenticated layout mechanics, and label it as visual-only evidence.
