# PWA splash marker can permanently hide restored TabBar after kill/reopen

Scope/applicability: installed mobile PWA / WebAPK / iOS standalone SPAs that render a splash/loading surface over a restored tab route, and hide restored app chrome with a root marker such as `data-splash-visible` while the splash is visible.

Anti-conditions: do not apply when the TabBar route predicate is false, the TabBar DOM is absent, auth redirects to login, or measured root/splash heights are actually shorter than the visual viewport. In those cases debug routing/auth/layout ownership first.

## Symptom

After installing the PWA, killing it from the background, and reopening:

- Main route is restored under the splash/loading screen.
- `[data-tabbar-root]` exists and its bounding rect is inside the visual viewport.
- Computed `display` is normal, but `opacity: 0` and `pointer-events: none` persist after the splash should be gone.
- `document.documentElement` still has `data-splash-visible="true"`.

This can look like a TabBar positioning/safe-area bug, but the chrome is often being hidden by the splash marker.

## Root-cause pattern

A splash component reads `sessionStorage('splash-shown')` directly during render, then writes the same key in an effect whose dependency includes the derived render value:

```tsx
const alreadyShown = sessionStorage.getItem('splash-shown') === '1';

useEffect(() => {
  if (alreadyShown) return;
  sessionStorage.setItem('splash-shown', '1');
  const exitTimer = setTimeout(() => setExiting(true), 4500);
  const removeTimer = setTimeout(() => setVisible(false), 5200);
  return () => {
    clearTimeout(exitTimer);
    clearTimeout(removeTimer);
  };
}, [alreadyShown]);
```

When `setExiting(true)` triggers a rerender, `alreadyShown` is re-read as `true`. React runs the cleanup for the previous effect, cancelling `removeTimer`, then the new effect returns early. The splash remains mounted or the root marker remains set, so CSS like this keeps the TabBar invisible:

```css
[data-splash-visible="true"] [data-tabbar-root="true"] {
  opacity: 0 !important;
  pointer-events: none !important;
}
```

## Debugging path

1. First separate “loading page is short” from “target page after loading is broken”. If the user says the target state can wait for animation end, wait for `.splash-root` to detach and for `data-splash-visible` to be absent before focusing inputs or measuring target-page header/chrome. A screenshot with only the logo/orb is splash evidence, not target-page evidence.
2. Then separate “loading page is short” from “TabBar is hidden by marker”. Measure all ownership layers during the splash:
   - `html`, `body`, `#root`, app canvas/phone portal, `.splash-root`, `[data-tabbar-root]`
   - `getBoundingClientRect()`, `clientHeight`, `scrollHeight`, `scrollTop`, `overflow`, `position`, `height`, `top/bottom`, `opacity`, `z-index`
   - `window.innerHeight`, `visualViewport.height`, `visualViewport.offsetTop`
3. If splash/root heights are full but TabBar opacity is 0, inspect `data-splash-visible` and the splash teardown lifecycle.
4. If waiting for splash end times out and `.splash-root.is-out` remains mounted, debug the splash teardown before continuing target-page focus/layout acceptance; do not keep testing the hidden page through the overlay.
5. If splash/root heights are short, do not patch TabBar visibility; debug first-paint layout markers and app-canvas height ownership.
6. Do not remove the temporary splash marker blindly: it may intentionally prevent restored tab chrome from leaking through startup. Fix marker teardown instead.

## Fix pattern

Freeze the “should play splash” decision for the current mount, and do not depend on a render-time sessionStorage read after the effect mutates storage:

For extra resilience, chain the removal timer from the exit timer or otherwise test the exact dev/StrictMode/browser path, not only a unit mount. The important invariant is: once `is-out` is visible, the DOM removal must still happen even if the original effect cleanup runs after the exit state was applied.

```tsx
useEffect(() => {
  if (!shouldPlayRef.current) return;
  try { sessionStorage.setItem('splash-shown', '1'); } catch {}
  const exitTimer = setTimeout(() => {
    setExiting(true);
    window.setTimeout(() => setVisible(false), 700);
  }, 4500);
  return () => clearTimeout(exitTimer);
}, []);
```

Keep any `data-splash-visible` marker tied to actual `visible` state and verify it is absent after removal.

## Regression tests

- Mount splash with a sibling `[data-tabbar-root]` inside the app canvas.
- Assert `data-splash-visible="true"` while splash is mounted.
- Use fake timers: advance to the exit phase and assert the splash has the exiting class while the marker still exists.
- Advance through fade-out and assert the splash DOM is removed and `data-splash-visible` is absent.
- Add a mobile standalone harness for kill/reopen: early snapshot should have TabBar DOM with `opacity: 0`; late snapshot should have no splash marker and TabBar `opacity: 1`, pointer events restored, and rect inside viewport.

## Pitfalls

- Do not frame this as “do not load TabBar on loading page” unless the product intentionally wants that. The safer model is: restored chrome may be temporarily hidden under a splash marker, but the marker must be cleared deterministically.
- User-visible “loading page is short” reports should trigger root/splash height evidence before applying marker or TabBar fixes.
- Tests that only unmount the component miss this bug; they must exercise the timer/rerender path after storage is marked.
