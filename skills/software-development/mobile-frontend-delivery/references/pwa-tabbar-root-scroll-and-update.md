# PWA TabBar root scroll, platform baselines, and update freshness

Scope/applicability: generic mobile web / installed PWA frontends with a fixed or absolute bottom TabBar, internal app scroll container, Service Worker precache, and browser/PWA delivery. This is not tied to any specific repository, branch, deploy URL, PR, or product. Use project-specific numbers (heights, colors, URLs, release IDs) only after confirming them in the target project.

Anti-scope: do not use for native-only apps, desktop-only layouts, or PWAs whose release lifecycle is fully controlled by a native store wrapper with no browser Service Worker.

## Trigger

Use when a mobile H5 / installed PWA bottom TabBar shows any combination of:

- iOS installed PWA has a blank strip below the floating TabBar.
- Android installed PWA loses or clips the TabBar after cache clear / cold launch.
- Safari browser mode shows a document-level scrollbar, and dragging the TabBar can scroll the page into white/body background.
- Users must refresh the browser page, clear site data, or reinstall the PWA before new code appears.

## Layout model

Separate three concepts; do not collapse them into one `safe-bottom` value:

1. **Platform safety baseline**
   - iOS installed PWA: often `0px`. The Home Indicator/PWA container may already own this area; adding a bottom safe-area baseline can double-count and create blank background below the TabBar.
   - Android installed PWA: a bounded/fixed system-navigation baseline when real-device evidence shows the system nav area can cover the page after clear-cache/cold launch.
2. **Visual gap**
   - A product-owned constant, e.g. `8px`, added on both platforms after the baseline.
3. **Scroll reserve**
   - Must match the TabBar placement formula so the last content is readable but does not create extra iOS blank space.

Example contract:

```css
:root {
  --tabbar-height: 52px;
  --android-standalone-tabbar-safe-baseline: 32px;
  --ios-standalone-tabbar-safe-baseline: 0px;
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

Platform selection should use stable markers set before React render, e.g. `data-platform="ios|android"` and `data-display-mode="standalone|browser"`, not theme-change or `visualViewport` driven TabBar relayout.

## Root scroll lock and display-mode viewport split

Applicability: mobile browser/PWA frontends where the outer document can scroll independently from an internal app scroll container, and where installed standalone mode may compute viewport units differently from browser mode. Anti-conditions: do not use this pattern for native-only apps, desktop-only layouts, or pages without a full-screen app shell.

If browser mode can drag the absolute TabBar and reveal white/body background, the outer document is scrolling. Lock the document and leave only the app's internal scroll container scrollable:

```css
html, body, #root {
  height: 100%;
  min-height: 100%;
  overflow: hidden;
}

html, body {
  margin: 0;
  position: fixed;
  inset: 0;
  width: 100%;
  overscroll-behavior-y: none;
}

#root { position: relative; }

[data-screen-scroll] {
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
}
```

Evidence: a right-edge page scrollbar plus the TabBar/app shell moving above a blank area means `document/body` moved, not the business list.

After root scroll is locked, compare browser and installed-PWA screenshots before changing gap constants again. If browser mode is correct but standalone still shows a blank band below the TabBar, the failure is usually viewport-height ownership, not TabBar safe-area math.

Applicability: React/Vue/SPAs whose document root is already fixed to the visible viewport and whose app-shell/canvas sits inside that fixed root. Anti-conditions: do not use this pattern for native-only shells, pages that intentionally allow document scrolling, or layouts where the app-shell is not a full-screen canvas.

- Browser mode: address/tool bars are real chrome; keep the app canvas on `100dvh` / framework `h-dvh` so it ends at the visible web viewport.
- Standalone PWA: there is no browser bottom toolbar. If `100dvh` resolves shorter than the fullscreen viewport, the TabBar pins to a short app shell and the area below is body/app background. But do **not** jump to `100lvh`: on iOS standalone, `lvh` can resolve taller than the actually visible clipped screen, making the TabBar logically correct inside an over-tall shell while visually hidden under the bottom/cut area.
- Preferred standalone fix after the root is fixed/inset/overflow-hidden: bind the app shell to the fixed root viewport with `height: 100%`, not `100vh/100lvh`.

Generic pattern; replace `[data-root]` and `[data-app-shell]` with the target project’s root and full-screen app-shell/canvas selectors:

```css
html, body, [data-root] {
  height: 100%;
  min-height: 100%;
  overflow: hidden;
}

html, body {
  position: fixed;
  inset: 0;
  width: 100%;
}

[data-display-mode="standalone"] [data-app-shell] {
  height: 100%;
  min-height: 100%;
}
```

Do not add a browser-mode override for this class of failure; browser mode must keep accounting for browser chrome. Do not expose a screen-bottom gray/cut area as an app-visible region; if it appears, the shell is probably over-tall or pinned to the wrong viewport box.

## Render-ownership trace when gray/cut area persists

If several safe-area/viewport-unit fixes have not removed an iOS PWA bottom gray band or TabBar clipping, stop changing constants and trace the render tree. This is a workflow correction: the next step is evidence, not another `bottom` or `height` guess.

Trace these layers in order:

1. **Outer root**: `html`, `body`, framework root. Are they fixed/inset/overflow-hidden? What is their computed height?
2. **App shell / phone canvas**: the full-screen canvas that owns app background. Does it use `h-dvh`, `100%`, `100vh`, `100lvh`, or `-webkit-fill-available`? Does it have `overflow: hidden`?
3. **Scroll owner**: identify the only internal scroll container, usually `[data-screen-scroll]`. Confirm content padding/reserve is on this layer, not on the outer document.
4. **Bottom chrome**: is the TabBar `absolute` inside a clipped app shell, or `fixed` to the viewport? An `absolute` TabBar inside a shorter `overflow:hidden` shell can be logically positioned correctly but visually clipped at the shell bottom.
5. **Floating siblings**: compare other fixed/absolute elements such as a support FAB. If a FAB higher in the tree remains visible while only the TabBar is cut at a horizontal boundary, suspect parent overflow clipping rather than a system overlay.

Symptoms that point to **parent clipping** rather than safe-area math:

- TabBar position is otherwise correct but a horizontal boundary cuts through its bottom half.
- A uniform gray/background strip appears below the app shell.
- Moving `--tabbar-bottom-gap` trades between “too high blank space” and “clipped,” without eliminating the boundary.
- Browser mode is correct and standalone-only viewport unit changes (`dvh`/`vh`/`lvh`) produce different failures.

Preferred diagnosis and fixes, in order:

Applicability: mobile H5/PWA apps with a full-screen app shell, one intended internal scroll owner, and bottom chrome overlapping that scroll owner. Anti-conditions: do not apply to native-only screens, desktop document-flow pages, or layouts where the browser document is intentionally the page scroller.

1. **Find the abnormal scroll owner before changing positioning.** Enumerate `html`, `body`, framework root, app shell, intended scroll owner, page-content root, and bottom chrome. Record `clientHeight`, `scrollHeight`, `scrollTop`, computed `overflow`, `padding-bottom`, and `getBoundingClientRect()`.
2. If outer roots/app shell have `scrollHeight === clientHeight` but the intended internal scroll owner has `scrollHeight > clientHeight`, do **not** move the TabBar out of the app shell as the first fix. The abnormal element is the internal scroll container; inspect whether a real bottom padding reserve is being scrolled into view.
3. If the visible gray/blank band height equals `tabbar height + bottom gap`, or content bottom stops at the TabBar top while the scroll container bottom remains below it, the culprit is usually scroll reserve (`padding-bottom` on the scroll owner), not TabBar positioning. Fix the reserve model: constrain the scroll viewport above the TabBar, reduce real padding to the visual gap, or convert some reserve to non-scroll-affecting scroll intent. Do not mask the bug by making the TabBar `fixed` unless evidence shows only the TabBar layer is clipped.
4. Move bottom chrome to a viewport-owned layer (`position: fixed`) only when evidence shows the bottom chrome alone is clipped by a parent `overflow:hidden` boundary while the main scroll content is otherwise correct. Preserve phone-width alignment with `left: 50%`, `translateX(-50%)`, full-width minus side gutters, and a max width matching the canvas.
5. If bottom chrome must remain inside the app shell, remove or narrow the parent `overflow:hidden` only after proving it will not reintroduce document-scroll white screens.
6. Only then consider viewport-unit alternatives. Do not keep cycling through `100dvh`/`100vh`/`100lvh` without measuring computed rects.

Minimal browser-console audit snippet for this class of bug:

```js
(() => {
  const pick = (el) => {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return {
      tag: el.tagName.toLowerCase(), id: el.id || '', cls: String(el.className || '').slice(0, 160),
      position: cs.position, overflow: cs.overflow, overflowY: cs.overflowY,
      height: cs.height, paddingBottom: cs.paddingBottom, bottom: cs.bottom,
      rect: { top: Math.round(r.top), bottom: Math.round(r.bottom), height: Math.round(r.height) },
      clientHeight: el.clientHeight, scrollHeight: el.scrollHeight,
      scrollTop: el.scrollTop, overBy: el.scrollHeight - el.clientHeight,
    };
  };
  const candidates = [document.documentElement, document.body, document.querySelector('[data-root]'),
    document.querySelector('[data-app-shell]'), document.querySelector('[data-screen-scroll]'),
    document.querySelector('[data-page-root]'), document.querySelector('nav')].filter(Boolean).map(pick);
  const abnormal = [...document.querySelectorAll('*')].map(pick)
    .filter(x => x.overBy > 0 || /(auto|scroll)/.test(x.overflow + x.overflowY))
    .sort((a, b) => b.overBy - a.overBy).slice(0, 20);
  return { viewport: { innerHeight, scrollY, vv: window.visualViewport && { height: visualViewport.height, offsetTop: visualViewport.offsetTop } }, candidates, abnormal };
})();
```

Regression assertions should cover the scroll owner, not only numbers:

- Outer roots/app shell do not become scroll containers unless that is intentional.
- Exactly the intended internal container owns vertical scrolling.
- Any bottom reserve strategy cannot expose a pure padding tail as a blank/gray band when scrolled to the end.
- If TabBar positioning is changed, the test states why content scrolling was not the root cause.
- Parent canvas overflow behavior is intentionally documented.

## Android clear-cache reload TabBar underlap

When an installed Android PWA action deletes CacheStorage, unregisters service workers, then calls `window.location.reload()`, treat the cache/SW action as a cold-reload trigger, not automatically as the geometric root cause. If the bottom TabBar moves closer to the physical bottom edge or is covered by the system gesture/navigation area after that reload, inspect the Android standalone contract: `data-display-mode`, `data-platform`, `100dvh`, app-canvas bottom trim, and the TabBar's own `bottom` token. A fragile pattern is `#phone-portal { height: calc(100dvh - 40px) }` combined with `TabBar bottom: 0`; if cold-start `100dvh` includes more native bottom obstruction than the static trim, or if the Android standalone selector is missed and browser mode applies, the TabBar will underlap. See `references/pwa-android-clear-cache-reload-tabbar.md` for the exact probe and interpretation checklist.

## PWA code freshness / cache pitfall

Do not runtime-cache hashed JS/CSS with `StaleWhileRevalidate` in addition to Workbox precache. Installed PWAs can keep serving old bundles from a runtime `static-cache` until users clear site data or reinstall.

Preferred pattern:

- Let Workbox precache own hashed JS/CSS; keep `cleanupOutdatedCaches` enabled.
- Keep `/`, `index.html`, `/sw.js`, `registerSW.js`, manifest/version endpoints no-store or no-cache at the server layer.
- Runtime-cache images only if needed, with versioned cache names.
- Update action must not be `registration.waiting?.postMessage(SKIP_WAITING)` only. If `waiting` is empty, call `registration.update()`, wait for `installing -> installed/waiting` with a bounded timeout, then send `SKIP_WAITING` and reload only the user-initiated tab.
- Re-check `registration.update()` on app foreground/focus so installed PWAs discover a new `sw.js` without requiring a browser-tab refresh.

## Verification checklist

- CSS source and built CSS contain the platform baselines, visual gap, and content reserve formula.
- Built CSS does not contain obsolete dynamic inset tokens if the accepted model is static platform baselines.
- Source and built CSS lock `html/body/#root` outer scroll while keeping `[data-screen-scroll]` scrollable.
- If using a standalone app-shell override, built CSS binds the standalone shell to the fixed root with `height: 100%` and does not contain `height: 100lvh` / `height: 100vh` for the shell unless the target device was explicitly verified not to clip it.
- Build-generated `sw.js` does not contain runtime `static-cache` or `StaleWhileRevalidate` for JS/CSS.
- `sw.js` still handles `SKIP_WAITING`.
- Targeted tests assert the layout contract and root-scroll lock; build gate passes.

## Anti-conditions

- Do not apply an iOS `0px` baseline to Android installed PWA if real devices show the system navigation area clips the TabBar.
- Do not fix an outer-document scrollbar by increasing content padding; lock the root scroll instead.
- Do not solve stale PWA code by telling users to clear cache/reinstall as the primary update path; that is a fallback, not the release mechanism.
