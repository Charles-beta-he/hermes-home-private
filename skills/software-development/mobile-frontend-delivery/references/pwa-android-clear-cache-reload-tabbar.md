# Android PWA clear-cache reload TabBar underlap

## Applicability

Use when an installed Android PWA/WebAPK looks mostly correct during normal navigation, but after an in-app action such as “clear cache and restart” (`CacheStorage` delete + service-worker unregister + `window.location.reload()`), the bottom TabBar moves closer to the physical bottom edge or is partly hidden by the system gesture/navigation area.

Anti-conditions:

- If the bug happens on ordinary route returns after pickers/inputs, use route-return viewport settling first.
- If the issue is only stale code delivery, use the PWA code freshness/cache checklist.
- If content is hidden behind a correctly positioned TabBar but the TabBar itself is stable, inspect scroll reserve/padding instead.

## First split: geometry bug vs restart-route bug

Before changing safe-area tokens again, identify whether the post-clear-cache symptom is actually a route/history problem:

- If reload resumes on a nested route such as an About/legal/settings page that intentionally has a `FlowNav`/subpage header and no main TabBar, first ask whether preserving that nested restart location is a product requirement. A missing TabBar on the nested page may be expected chrome, while the later TabBar disappearance after returning to a main tab can still be a viewport reflow problem.
- Inspect the clear-cache handler for `caches.delete(...)`, service-worker `unregister()`, and a bare `window.location.reload()` while the current path is a nested tab sub-route.
- Inspect the subpage back handler. A generic `history.length > 1 ? navigate(-1) : navigate('/')` can send the user through a stale pre-reset history stack after reload instead of landing deterministically on the owning tab.
- If product wants a deterministic main-tab restart, replace the URL/history entry with the owning terminal tab route before reload, then optionally dispatch the app's existing viewport-settle event so Android PWA geometry recalculates after the reset:

```ts
try {
  window.history.replaceState(window.history.state, '', '/owning-tab');
  window.dispatchEvent(new Event('app:viewport-settle'));
  window.location.reload();
} catch {
  window.location.replace('/owning-tab');
}
```

- If product wants to preserve the current nested route, do **not** force `replaceState('/owning-tab')`. Instead mark the reload as needing post-reload viewport validation (for example `sessionStorage.setItem('app:post-reload-viewport-check', 'clear-cache')`), dispatch the settle event, reload the current path, and have app startup consume that marker to run a stronger viewport-height check.

Keep the cache/SW reset itself intact; do not weaken the cache clear just to avoid the route bug. Add regression tests for the selected route policy: either assert `history.replaceState(..., '/owning-tab')`, or assert the nested route is preserved and the post-reload viewport-check marker + settle event + reload call order occur.

## Root-cause pattern

The cache/SW action is usually the trigger, not necessarily the geometric cause. Deleting caches and unregistering the service worker does not uninstall the PWA or intentionally change `display-mode`, but it creates a cold reload path where Android WebAPK/Chrome may re-resolve route state, `display-mode`, `100dvh`, and `visualViewport` differently from a warm app session.

Common fragile layout contract:

```css
[data-display-mode="standalone"][data-platform="android"] {
  --android-standalone-canvas-bottom-trim: 40px;
  --tabbar-bottom-gap: 0px;
}

[data-display-mode="standalone"][data-platform="android"] #phone-portal {
  height: calc(100dvh - var(--android-standalone-canvas-bottom-trim));
}
```

with the TabBar pinned to the app canvas:

```tsx
<nav style={{ bottom: 'var(--tabbar-bottom-gap)' }} />
```

This makes effective Android bottom clearance:

```text
effectiveClearance = canvasTrim + tabbarBottomGap
```

If `tabbarBottomGap = 0` and `canvasTrim = 40`, then any real Android bottom obstruction greater than 40px, or any cold-start `100dvh` that includes more of the system gesture area, can push the TabBar into the native bottom area. If the cold reload is temporarily classified as browser mode, the Android standalone selector is missed entirely and clearance may fall back to only the browser visual gap (for example 16px).

## Diagnosis before fixing

Capture values at these moments: normal warm launch, immediately after clear-cache reload, after `pageshow`, after first `visualViewport.resize`, and after ~600ms.

```js
(() => {
  const root = document.documentElement;
  const phone = document.querySelector('#phone-portal');
  const nav = document.querySelector('nav');
  const rs = getComputedStyle(root);
  const pr = phone?.getBoundingClientRect();
  const nr = nav?.getBoundingClientRect();
  const visualBottom = window.visualViewport
    ? window.visualViewport.offsetTop + window.visualViewport.height
    : window.innerHeight;

  return {
    dataset: { ...root.dataset },
    displayModeMedia: window.matchMedia?.('(display-mode: standalone)').matches,
    swController: !!navigator.serviceWorker?.controller,
    viewport: {
      innerHeight: window.innerHeight,
      clientHeight: document.documentElement.clientHeight,
      visualViewport: window.visualViewport && {
        height: window.visualViewport.height,
        offsetTop: window.visualViewport.offsetTop,
      },
      visualBottom,
      scrollY: window.scrollY,
    },
    css: {
      canvasTrim: rs.getPropertyValue('--android-standalone-canvas-bottom-trim').trim(),
      tabbarBottomGap: rs.getPropertyValue('--tabbar-bottom-gap').trim(),
      tabbarContentReserve: rs.getPropertyValue('--tabbar-content-reserve').trim(),
      safeBottom: rs.getPropertyValue('--safe-bottom').trim(),
    },
    rects: {
      phone: pr && { top: pr.top, bottom: pr.bottom, height: pr.height },
      nav: nr && { top: nr.top, bottom: nr.bottom, height: nr.height },
    },
    gaps: pr && nr && {
      phoneBottomFromInner: window.innerHeight - pr.bottom,
      navBottomFromInner: window.innerHeight - nr.bottom,
      navBottomFromVisual: visualBottom - nr.bottom,
      navBottomFromPhone: pr.bottom - nr.bottom,
    },
  };
})();
```

Interpretation:

- `dataset.displayMode !== 'standalone'` or `dataset.platform !== 'android'`: Android standalone CSS did not apply; fix first-paint/runtime display-mode classification or add a robust Android installed fallback.
- `phoneBottomFromInner ≈ 0`: canvas trim did not apply.
- `navBottomFromInner ≈ browser visual gap` (for example 16px): likely browser-mode branch is active in an installed PWA.
- `navBottomFromInner ≈ canvasTrim` but the screenshot still shows native obstruction: static trim is insufficient for that device/cold-start viewport.
- `navBottomFromVisual < 0`: TabBar is below the visual viewport.

## Fix direction

Do not solve this by adding more route-return timers alone; route settling handles stale scroll/viewport after navigation, while clear-cache reload underlap is a cold-start Android bottom-clearance problem. However, cold-start viewport values can arrive late, so the Android bottom-clearance measurement itself should run in multiple settle passes.

Prefer one of these, verified on installed Android PWA:

1. Preserve an independent Android TabBar bottom baseline/gap in addition to any canvas trim, so the chrome itself is not pinned at `bottom: 0` inside a potentially under-trimmed canvas.
2. Prefer platform-reported `env(safe-area-inset-bottom, 0px)` for Android standalone canvas trim when the existing trim is only a local hard-coded guess. Keep it scoped to `[data-display-mode="standalone"][data-platform="android"]`; do not move the value into generic `--safe-bottom` or iOS rules. If `env()` reports `0px`, retain a narrow Android-only TabBar chrome gap (for example 8px) so the pill is not flush to the canvas.
3. Measure Android-only bottom obstruction from `visualViewport`/element geometry with bounded min/max values, and feed it into an Android-specific token rather than generic `--safe-bottom`, when `env()` is proven insufficient on real devices.
4. If first-paint display-mode is unstable after reload, make the installed-Android classification robust before React render and re-apply it on `pageshow`, `resize`, and display-mode media changes.

### Target branch already has an Android canvas/gap model

If the target branch already contains a newer Android standalone model such as:

```css
[data-display-mode="standalone"][data-platform="android"] {
  --android-standalone-canvas-bottom-trim: env(safe-area-inset-bottom, 0px);
  --tabbar-safe-baseline: 0px;
  --tabbar-bottom-gap: var(--android-standalone-tabbar-bottom-gap);
  --tabbar-content-reserve: calc(var(--tabbar-height) + var(--tabbar-bottom-gap) + 8px);
}
```

do not replay an older broad patch that replaces its canvas strategy or iOS/browser baselines. Preserve the target branch's canvas trim and narrow Android gap, then add only the missing cold-start obstruction token:

```css
:root {
  --android-visual-bottom-inset: 0px;
}

[data-display-mode="standalone"][data-platform="android"] {
  --android-standalone-canvas-bottom-trim: env(safe-area-inset-bottom, 0px);
  --tabbar-safe-baseline: 0px;
  --tabbar-bottom-gap: calc(var(--android-standalone-tabbar-bottom-gap) + var(--android-visual-bottom-inset, 0px));
  --tabbar-content-reserve: calc(var(--tabbar-height) + var(--tabbar-bottom-gap) + 8px);
}
```

Runtime helper pattern:

```ts
const hiddenBottom = Math.round(window.innerHeight - visualViewport.height - visualViewport.offsetTop);
const inset = hiddenBottom <= 12 ? 0 : Math.min(hiddenBottom, 40);
root.style.setProperty('--android-visual-bottom-inset', `${inset}px`);
```

Run this measurement only when `data-platform="android"` and `data-display-mode="standalone"`, skip while an editable element is focused, and clear the token when the measurement returns 0. On app start, `pageshow`, and explicit viewport-settle events, schedule several passes (for example 0/150/300/600ms) so clear-cache reload and first WebAPK launch can catch late `visualViewport` settlement. Existing keyboard/resize settle listeners can stay single delayed passes.

Verification must include installed-PWA evidence, not only desktop/Playwright browser mode. Browser mode can show a stable `navBottomGap` while installed Android standalone still underlaps the system gesture area. Add regression assertions that iOS standalone does not consume Android-only canvas-trim or TabBar-gap tokens.

When the app already trims Android standalone canvas (for example `#phone-portal { height: calc(100dvh - 40px) }`) and earlier fixes intentionally set Android TabBar `bottom: 0` to avoid over-lifting, do **not** revert to a large historical Android baseline or the shared browser/iOS visual gap. That can double-count the system area and reintroduce the opposite bug: TabBar floating too high.

Use a small Android-only chrome gap token instead:

```css
:root {
  --android-standalone-tabbar-bottom-gap: 8px;
}

[data-display-mode="standalone"][data-platform="android"] {
  --android-standalone-canvas-bottom-trim: 40px;
  --tabbar-safe-baseline: 0px;
  --tabbar-bottom-gap: var(--android-standalone-tabbar-bottom-gap);
  --tabbar-content-reserve: calc(var(--tabbar-height) + var(--tabbar-bottom-gap) + 8px);
}
```

Expected geometry in an Android standalone web-runtime probe:

```text
phoneBottomFromInner = canvasTrim
navBottomFromPhone = androidTabGap
navBottomFromInner = canvasTrim + androidTabGap
```

For the example above: `40 + 8 = 48px` total clearance, while iOS/browser should still show their prior `16px` visual gap and no Android canvas trim.

Keep the change scoped:

- Do not switch TabBar to `position: fixed`; keep it absolute inside the app-owned canvas.
- Do not write the Android gap to generic `--safe-bottom`.
- Do not change iOS standalone selectors or `100vh`/`100lvh` restoration.
- Update the scroll/content reserve together with TabBar placement so the last content is not hidden behind the raised chrome.
- Add regression assertions that Android standalone no longer has `--tabbar-bottom-gap: 0px`, iOS does not mention the Android token, and the Android rule does not consume the shared `--tabbar-visual-bottom-gap`.
- If runtime code measures an Android visual bottom token, verify the CSS actually consumes it. A correctly measured `--android-visual-bottom-inset` that is not referenced by `--tabbar-bottom-gap` / content reserve is functionally the same as no fix.
- Install/startup viewport stabilization should run multiple settle passes, not only one immediate debounce. Cold WebAPK launches and cache/SW reloads can expose the true `visualViewport.height` after the first pass; schedule probes at roughly `0/150/300/600ms` on install, `pageshow`, and explicit viewport-settle events.

Verification must include installed-PWA evidence, not only desktop/Playwright browser mode. Browser mode can show a stable `navBottomGap` while installed Android standalone still underlaps the system gesture area. If only web-runtime simulation is available, force Android + standalone markers, seed or simulate a plausible visual bottom inset, and assert the built CSS resolves to `productAndroidGap + visualInset` while the TabBar remains present and measurable.

If the TabBar stays missing after clear-cache/restart but becomes correct only after going through the login account-input flow, do not jump to a top-anchor workaround for the TabBar. Treat the login field's visible "jitter" as a browser/WebAPK viewport reflow signal, not proof that arbitrary keyboard open/close repairs the layout. Capture and compare the three runtime states: post-clear-cache before login, during/after account-input reflow, and after login success. Inspect `#phone-portal` rect, `visualViewport.height/offsetTop`, `window.innerHeight`, TabBar rect, scroll owner `clientHeight/scrollHeight/scrollTop/padding-bottom`, route/auth-shell to tab-shell transition, and which settle event fires. Keep TabBar on the established bottom-token model until that differential evidence identifies the actual auth-flow reflow or shell-transition trigger.

### Manual viewport recheck vs visual-height fallback

If user evidence shows first install and warm relaunch are correct, but clear-cache reload still hides the TabBar until the login account-field keyboard jitter, classify the keyboard as a `visualViewport`/WebAPK layout invalidation signal. Use a two-level response; do not start with TabBar `top` anchoring.

Level 1 — low-risk manual recheck:

- Before reload, preserve the current route/history if that is the product expectation; do not force a nested route such as `/me/about` back to the owning tab unless the user explicitly wants deterministic tab landing.
- Mark the next boot in `sessionStorage` (for example `post-reload-viewport-check`) and dispatch the app's viewport-settle event before `location.reload()`.
- On next boot, consume the marker and run multi-pass checks (`requestAnimationFrame`, ~80/150/300/600/1000ms): read `window.innerHeight`, `visualViewport.height`, `visualViewport.offsetTop`, flush `documentElement` and `#phone-portal` rects, then rerun the existing safe-area/Android visual-bottom reconciliation.
- This is only a revalidation/flush path. If WebAPK does not actually recompute the shell height, Level 1 may leave the TabBar missing.

Level 2 — scoped Android `visualViewport.height` shell fallback:

- If Level 1 fails on installed Android PWA, write a scoped Android-only app shell token from `visualViewport.height`, for example `--app-visual-height: ${Math.min(window.innerHeight, visualViewport.height)}px`, only when `data-platform="android"`, `data-display-mode="standalone"`, and no editable element has focus.
- Let only the Android standalone `#phone-portal` consume it, with `100dvh` fallback:

```css
:root { --app-visual-height: 100dvh; }

[data-display-mode="standalone"][data-platform="android"] #phone-portal {
  height: calc(var(--app-visual-height, 100dvh) - var(--android-standalone-canvas-bottom-trim));
  min-height: calc(var(--app-visual-height, 100dvh) - var(--android-standalone-canvas-bottom-trim));
}
```

- Keep TabBar absolute with `bottom: var(--tabbar-bottom-gap)` at first; do not move it to a computed top anchor until Level 1/2 have failed on installed Android PWA evidence.
- Keep iOS standalone on its existing `100vh`/`100lvh` restoration path, and do not write the Android visual height into generic safe-area variables.
- Regression tests should assert route preservation when required, marker consumption after reload, manual recheck timing, Android-only `--app-visual-height` writes, `#phone-portal` CSS consuming the token, and no iOS consumption of Android-only tokens.

Level 3 — Android-only forced TabBar top anchor fallback:

Use only after installed Android evidence shows `location.reload()` itself leaves the app canvas/bottom tokens unreliable even after Level 1/2, while first install or killing the PWA process and reopening from the launcher is correct. In that case the product may choose to bypass Android bottom placement entirely:

```tsx
<nav
  data-tabbar-root="true"
  style={{
    top: 'var(--tabbar-top, auto)',
    bottom: 'var(--tabbar-bottom, var(--tabbar-bottom-gap))',
  }}
/>
```

Runtime pattern:

```ts
const TABBAR_HEIGHT_PX = 52;
const TABBAR_TOP_GAP_PX = 8;

function clearTabbarTopAnchor(root = document.documentElement) {
  root.style.removeProperty('--tabbar-top');
  root.style.removeProperty('--tabbar-bottom');
  root.removeAttribute('data-tabbar-top-fallback');
}

function applyAndroidTabbarTopAnchor(root = document.documentElement) {
  const isAndroidStandalone = root.dataset.platform === 'android' && root.dataset.displayMode === 'standalone';
  if (!isAndroidStandalone || isEditableElement(document.activeElement)) {
    clearTabbarTopAnchor(root);
    return false;
  }
  if (!document.querySelector('[data-tabbar-root]')) return false;
  const height = Math.round(window.visualViewport?.height ?? window.innerHeight);
  if (height <= TABBAR_HEIGHT_PX) return false;
  root.style.setProperty('--tabbar-top', `${Math.max(0, height - TABBAR_HEIGHT_PX - TABBAR_TOP_GAP_PX)}px`);
  root.style.setProperty('--tabbar-bottom', 'auto');
  root.setAttribute('data-tabbar-top-fallback', 'android');
  return true;
}
```

Run this from the existing viewport settle path (`startup`, `pageshow`, `visualViewport.resize/scroll`, explicit `app:viewport-settle`) so Android standalone is consistently top-anchored after reload. Clear it for iOS, browser mode, and focused editable/keyboard states to avoid keyboard shrink pushing the TabBar upward. Verification should include: unit tests that Android standalone forces `--tabbar-top = visualViewport.height - tabbarHeight - gap`, tests that keyboard/non-Android clear it, a built-bundle marker scan for `data-tabbar-root`/`--tabbar-top`, and a runtime probe showing an 8px visual-bottom gap.

If the differential evidence shows a keyboard-triggered `visualViewport.resize` causes WebView to recompute the correct layout, add a manual viewport-height validation path before moving TabBar to top anchoring. JS cannot directly resize `visualViewport`, but it can approximate the app-owned validation path:

```ts
const POST_RELOAD_VIEWPORT_CHECK_KEY = 'app:post-reload-viewport-check';
const MANUAL_VIEWPORT_CHECK_DELAYS = [0, 80, 150, 300, 600, 1000];

export function markPostReloadViewportCheck(reason = 'clear-cache') {
  sessionStorage.setItem(POST_RELOAD_VIEWPORT_CHECK_KEY, reason);
}

export function forceViewportHeightCheck(root = document.documentElement) {
  const viewport = window.visualViewport;
  const height = Math.round(viewport?.height ?? window.innerHeight);
  const offsetTop = Math.round(viewport?.offsetTop ?? 0);
  root.style.setProperty('--viewport-recheck-tick', `${Date.now()}:${window.innerHeight}:${height}:${offsetTop}`);
  void root.getBoundingClientRect();
  void document.getElementById('phone-portal')?.getBoundingClientRect();
  return settleViewportLayout(root);
}
```

On reload before calling `location.reload()`, mark the session flag and dispatch the normal viewport-settle event. At runtime startup, consume the flag and schedule manual height checks at immediate/RAF plus the delayed passes above. Tests should prove: the route policy is preserved, the marker is written/consumed, manual checks write a benign recheck tick, and delayed visualViewport height changes still update the Android-only bottom token.

Level 3 — conditional TabBar top fallback after bottom positioning is proven broken:

- Use this only after Level 1/2 still leave the TabBar missing and evidence shows the automatic reload path corrupts bottom/canvas calculation while first install and process-kill relaunch are normal.
- Do **not** globally switch TabBar to top anchoring. Keep bottom-token positioning as the default and add a guarded fallback that activates only when the rendered TabBar is measured outside the visual viewport.
- Add a stable marker to the TabBar, for example `data-tabbar-root="true"`, and allow CSS variables to override the normal bottom placement:

```tsx
<nav
  data-tabbar-root="true"
  style={{
    top: 'var(--tabbar-top, auto)',
    bottom: 'var(--tabbar-bottom, var(--tabbar-bottom-gap))',
  }}
/>
```

- During Android standalone post-reload recovery checks, after flushing `#phone-portal`, measure the TabBar rect against `visualViewport.offsetTop + visualViewport.height`. If `rect.bottom > visualBottom`, `rect.top >= visualBottom`, or `rect.height <= 0`, switch to a computed top:

```ts
const TABBAR_HEIGHT_PX = 52;
const TABBAR_TOP_FALLBACK_GAP_PX = 8;

function applyTabbarTopFallback(root = document.documentElement) {
  const visualHeight = Math.round(window.visualViewport?.height ?? window.innerHeight);
  const top = Math.max(0, visualHeight - TABBAR_HEIGHT_PX - TABBAR_TOP_FALLBACK_GAP_PX);
  root.style.setProperty('--tabbar-top', `${top}px`);
  root.style.setProperty('--tabbar-bottom', 'auto');
  root.setAttribute('data-tabbar-top-fallback', 'clear-cache');
}
```

- Clear the fallback when the TabBar is visible, when not Android standalone, or when an editable element is focused. This prevents keyboard-open states from pulling the TabBar upward and preserves normal first-install/warm-relaunch behavior.
- Verification should include unit tests for: outside-visual-viewport detection, fallback top calculation (for example `768 - 52 - 8 = 708px`), clearing on visible/focused states, and component style defaults. Add a browser-runtime probe that starts with an oversized app canvas and confirms fallback moves the TabBar back to an 8px visual-bottom gap.
