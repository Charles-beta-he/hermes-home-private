# Android PWA Safe-Area Over-Offset

## Trigger

Use this reference when an installed Android PWA shows a floating bottom navigation / TabBar too high above the gesture bar, especially on tall devices (for example 1080×2400 screenshots) while iOS safe-area behavior still needs to be preserved.

## Durable lesson

Do not infer a generic bottom safe-area from `screen.height - window.innerHeight` across all standalone PWAs. On Android, that delta can include status/nav/system chrome and may be ~100px on tall devices. If code treats `delta > 20` as an iPhone-style 34px Home Indicator inset, the app will lift all bottom chrome unnecessarily.

Typical compounding path:

```css
:root { --safe-bottom: env(safe-area-inset-bottom, 0px); }
```

```tsx
<TabBar style={{ bottom: 'var(--safe-bottom)' }} />
<main className="pb-[calc(64px+var(--safe-bottom))]" />
```

A mistaken `--safe-bottom: 34px` moves the TabBar up and adds extra scroll padding, producing a visible gap between the TabBar and Android gesture bar.

## Recommended fix pattern

When adding a standalone fallback for browsers that report `env(safe-area-inset-bottom) = 0`:

```html
<script>
(function () {
  var root = document.documentElement;
  var s = getComputedStyle(root);
  var envBottom = s.getPropertyValue('env(safe-area-inset-bottom)').trim();
  var isStandalone =
    window.navigator.standalone === true ||
    window.matchMedia('(display-mode: standalone)').matches;

  if (!isStandalone) return;

  if (!envBottom || envBottom === '0px' || envBottom === '0') {
    var isIPhone = /iPhone/.test(navigator.userAgent);
    var bottomInset = screen.height - window.innerHeight;
    var safeBot = isIPhone && bottomInset > 20 ? '34px' : '0px';
    root.style.setProperty('--safe-bottom', safeBot);
  }
})();
</script>
```

Key point: synthesize the well-known `34px` fallback only for iPhone. Let Android stay `0px` unless the browser provides a real `env(safe-area-inset-bottom)` value.

## Regression test recipe

Add a test around the actual inline/polyfill script or helper, not just component classes:

- Stub standalone mode: `matchMedia('(display-mode: standalone)').matches = true`.
- Stub `getComputedStyle(...).getPropertyValue(...)` to return `0px` for env safe area.
- Android case: UA contains `Android`, `screen.height = 2400`, `innerHeight = 2292`; assert `--safe-bottom === '0px'`.
- iPhone case: UA contains `iPhone`, `screen.height = 852`, `innerHeight = 812`; assert `--safe-bottom === '34px'`.

Run the test before the fix and confirm RED: Android incorrectly gets `34px`.

## Visual verification recipe

After build/preview, use a mobile viewport with DPR 3 (for example 360×800 representing 1080×2400) and authenticated or seeded app state. Measure the TabBar rect:

```js
const nav = document.querySelector('nav[aria-label]');
const rect = nav.getBoundingClientRect();
console.log({
  safeBottom: document.documentElement.style.getPropertyValue('--safe-bottom') || getComputedStyle(document.documentElement).getPropertyValue('--safe-bottom'),
  gapToViewportBottom: Math.round(window.innerHeight - rect.bottom),
  tabbarHeight: Math.round(rect.height),
});
```

Expected for Android fallback-zero case:

- `safeBottom: "0px"`
- `gapToViewportBottom: 0` when TabBar is intended to sit on the viewport bottom/safe-area edge
- TabBar height remains unchanged (e.g. 64px)

## Pitfalls

- Do not “fix” by globally removing `--safe-bottom`; that can break iPhone Home Indicator avoidance.
- Do not add another hardcoded bottom offset to TabBar; it compounds the same class of bug.
- Do not conclude content height is wrong until measuring the TabBar rect and custom property value. A visible bottom gap often comes from chrome offset, not the scroll content itself.
