# Android PWA TabBar safe-area and scroll ownership

Use when investigating Android installed PWA bottom TabBar drift, clipping, or system gesture/navigation overlap.

## Key rules

1. Do not anchor mobile PWA bottom chrome directly to the browser viewport with `position: fixed; bottom: 0` unless the app has explicitly proven the viewport bottom equals the safe visual bottom on the target Android device.
2. Prefer an app-owned shell:
   - lock `html`, `body`, and `#root` so they are not scroll owners;
   - size an app canvas such as `#phone-portal` to the intended safe app viewport;
   - place bottom chrome as `position: absolute` inside a `relative` shell/canvas;
   - keep `main[data-screen-scroll]` as the only normal page scroll owner.
3. Treat canvas bottom trim and TabBar visual bottom gap as separate concerns:
   - canvas trim handles native/system obstruction;
   - TabBar bottom gap handles product visual spacing and safety buffer.
   Avoid contracts like `canvasTrim=40px` plus `tabbarBottomGap=0px` unless verified on real Android installed PWA cold starts.
4. Manifest `display: fullscreen` can destabilize Android layout calculations, but first verify the actual built/served manifest. A project using `display: standalone` is not suffering from a fullscreen-manifest root cause.
5. `display_override` entries should be treated as variables to reduce when debugging, but `window-controls-overlay` is not equivalent to Android fullscreen and usually falls back to `standalone` on mobile.

## Measurements to collect

On the failing Android installed PWA state, record:

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
    displayModeStandalone: window.matchMedia?.('(display-mode: standalone)').matches,
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

- If `dataset.displayMode !== 'standalone'`, Android standalone CSS selectors are not active; bottom trim/gap may be wrong.
- If `phoneBottomFromInner ≈ 0`, the app canvas is not being trimmed away from the bottom viewport.
- If `navBottomFromVisual < 0`, the TabBar extends below the visual viewport.
- If `navBottomFromInner` equals a static trim but visual clipping remains, the static trim is smaller than the real Android bottom obstruction.

## Scroll-owner check

For PWA pages, expected scroll ownership is:

```text
html/body/#root        overflow hidden, no scroll
#phone-portal          overflow hidden, no scroll
shell                  relative, no scroll owner
main[data-screen-scroll]  the only page scroll owner
page content root      natural height, overflow visible
TabBar                 absolute inside shell/canvas, not fixed to browser viewport
```

If a secondary page overflows, `main[data-screen-scroll]` should have `scrollHeight > clientHeight` and changing its `scrollTop` should consume the scroll. `window.scrollY`, `documentElement.scrollTop`, and `body.scrollTop` should stay zero.

## Common false leads

- Page content overflow is not the same as TabBar clipping. Content reserve affects page content; TabBar clipping is chrome/canvas geometry.
- Service-worker cache clearing is often the trigger for cold-start viewport instability, not the direct geometric root cause.
- A manifest must be inspected from the served `manifest.webmanifest`; source config alone is not enough.
