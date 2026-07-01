# PWA first-paint layout markers and splash scroll ownership

Scope/applicability: mobile web / installed PWA SPAs whose CSS selects browser vs standalone and platform-specific viewport/root-lock rules using `data-platform` and `data-display-mode` on `document.documentElement`. Especially relevant when a splash/loading screen is shown before the main app is interactive.

Anti-conditions: do not apply to apps where server-rendered markup already includes stable platform/display-mode classes, native-only shells, desktop document-flow pages, or layouts that intentionally allow document/body scrolling.

## Symptom

Before or during the splash/loading screen, the outer root or app canvas briefly shows a scrollbar or reports `scrollHeight > clientHeight`, even though later in the app the intended internal scroll container behaves correctly.

A related PWA kill/reopen symptom is restored app chrome leaking onto a loading/splash surface: the last tab route is restored under the splash and the floating bottom TabBar remains visible at the bottom, even though first install/cold launch looked correct.

This is usually a **first-paint or restored-route chrome ownership race**, not a TabBar gap problem:

1. CSS has rules such as `[data-display-mode="browser"] body { position: fixed; inset: 0; }` or standalone/platform-specific app-shell height rules.
2. `data-platform` / `data-display-mode` are installed only after the React/Vue bundle runs.
3. The splash overlay appears, but the underlying root/app shell has already had one or more unclassified layout frames.
4. Browser/PWA viewport units may briefly assign scroll ownership to `html`, `body`, `#root`, or the full-screen app shell.

## Fix pattern

Set the stable layout markers in a small head inline script **before** the module script that loads the app:

```html
<script>
  (function () {
    var ua = navigator.userAgent.toLowerCase();
    var maxTouchPoints = navigator.maxTouchPoints || 0;
    var isIpadDesktopUa = ua.indexOf('macintosh') >= 0 && maxTouchPoints > 1;
    var platform = /iphone|ipad|ipod/.test(ua) || isIpadDesktopUa
      ? 'ios'
      : /android/.test(ua)
        ? 'android'
        : 'other';
    var standalone =
      navigator.standalone === true ||
      (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches);
    document.documentElement.dataset.platform = platform;
    document.documentElement.dataset.displayMode = standalone ? 'standalone' : 'browser';
  })();
</script>
<script type="module" src="/src/main.tsx"></script>
```

The runtime installer should still run after app startup to keep the markers fresh across resize, orientation, or display-mode media changes. The head script is only the first-paint seed.

For kill/reopen cases where restored tab chrome leaks onto the loading page, isolate startup chrome separately from safe-area geometry:

1. Render the splash/loading component inside the same app canvas/phone portal that owns the TabBar; avoid a `document.body` portal fallback before the app canvas exists.
2. While the splash is visible, set a root marker such as `data-splash-visible="true"` and remove it on unmount/hide.
3. Hide restored bottom chrome under that marker, e.g. `[data-splash-visible="true"] [data-tabbar-root="true"] { opacity: 0; pointer-events: none; }`.
4. Give the splash a higher z-index than app chrome (for example `1000` vs TabBar `100`) but keep it inside the app canvas so max-width/overflow clipping remains identical to the real app.
5. Do not fix this class by tuning TabBar safe-area gaps; the bug is restored-route chrome leaking through a startup/loading surface.

## Test pattern

Add a regression test that reads the app HTML and asserts the marker script appears before the app module script:

```ts
const html = readFileSync(resolve(process.cwd(), 'index.html'), 'utf8');
const firstModuleScript = html.indexOf('<script type="module" src="/src/main.tsx"></script>');
expect(html.indexOf('document.documentElement.dataset.platform')).toBeLessThan(firstModuleScript);
expect(html.indexOf('document.documentElement.dataset.displayMode')).toBeLessThan(firstModuleScript);
```

For restored-chrome splash leaks, add a component/CSS regression that mounts the splash with a `data-tabbar-root` sibling inside the app canvas and asserts:

- `document.documentElement` has `data-splash-visible="true"` while splash is mounted.
- `.splash-root.closest('#phone-portal')` or equivalent app canvas is present.
- The root marker is removed on unmount/hide.
- The built CSS contains a `[data-splash-visible="true"] [data-tabbar-root="true"]` hiding rule and splash z-index remains above TabBar.

## Browser probe

During splash, assert all outer ownership layers are non-scrollable:

- `document.documentElement`, `document.body`, framework root, and full-screen app shell all have `scrollHeight === clientHeight`, `scrollTop === 0`, and `overflowY: hidden`.
- `window.scrollY === 0`.
- `document.documentElement.dataset.platform` and `.dataset.displayMode` are present before the splash disappears.

Keep separate route-return TabBar checks for non-tab flows; first-paint marker seeding and post-route viewport settling are different failure classes.
