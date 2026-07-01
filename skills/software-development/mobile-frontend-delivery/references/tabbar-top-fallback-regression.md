# TabBar top-fallback regression pattern

Use when a mobile/PWA bottom TabBar disappears after recent safe-area, viewport, or Android reload-recovery commits.

## Symptom

- iOS/Android simulator or real device shows main content and floating widgets, but the bottom TabBar is absent.
- Source still renders the TabBar route condition and component.
- The regression appears after changes that introduce `--tabbar-top`, `--tabbar-bottom`, `data-tabbar-top-fallback`, or visualViewport recovery logic.

## Root-cause pattern

A dangerous patch changes the TabBar from normal bottom-owned CSS placement into always-JS-owned `top`/`bottom` inline placement, for example:

```tsx
style={{
  top: 'var(--tabbar-top, auto)',
  bottom: 'var(--tabbar-bottom, var(--tabbar-bottom-gap))',
}}
```

Then Android/iOS viewport settlement code writes top-anchor variables too broadly. If a later commit forces top fallback for all Android standalone sessions, or stale visualViewport metrics produce an invalid top value, the TabBar can be positioned outside the app canvas or clipped by the shell. Because the DOM still exists, tests that only assert `getByRole('navigation')` pass while the simulator shows no bottom bar.

## Correct model

1. Default TabBar placement must be CSS bottom-owned:

```css
.tabbar-glass {
  bottom: var(--tabbar-bottom-gap);
}
```

2. Top fallback must be opt-in through a root recovery marker, not inline JSX on every render:

```css
[data-tabbar-top-fallback="android"] .tabbar-glass[data-tabbar-root="true"] {
  top: var(--tabbar-top);
  bottom: auto;
}
```

3. `reconcileTabbarTopFallback()` should apply top fallback only after measuring that the existing TabBar rect is actually outside the visual viewport:

```ts
const rect = nav.getBoundingClientRect();
const visualHeight = Math.round(window.visualViewport?.height ?? window.innerHeight);
const visualBottom = Math.round((window.visualViewport?.offsetTop ?? 0) + visualHeight);
const outsideVisualViewport = rect.bottom > visualBottom || rect.top >= visualBottom || rect.height <= 0;

if (outsideVisualViewport) return applyTabbarTopFallback(root, visualHeight);
clearTabbarTopFallback(root);
return false;
```

Do not force top fallback merely because `data-platform="android"` and `data-display-mode="standalone"` are present.

## Debugging checklist

- Inspect recent commits touching `TabBar.tsx`, `index.css`, `viewportStability.ts`, and safe-area tests.
- Prove whether the TabBar DOM exists: `[data-tabbar-root]` / navigation role.
- Read `getBoundingClientRect()` and computed `top`, `bottom`, `display`, `opacity`, `visibility`, `z-index`.
- Compare browser vs standalone and iOS vs Android; do not apply Android fallback to iOS.
- Check served asset hashes if production differs from source.
- If the current worktree is dirty or behind, create a clean worktree from the target branch and land the fix there.

## Regression tests to add

- Component/layout test: TabBar has `data-tabbar-root` but no inline `style` in normal mode.
- CSS test: `.tabbar-glass` owns `bottom: var(--tabbar-bottom-gap)` by default.
- CSS test: top fallback selector exists only under `[data-tabbar-top-fallback="android"]`.
- Runtime test: bottom-positioned visible TabBar clears top fallback.
- Runtime test: offscreen TabBar applies top fallback.
- Mobile browser harness: iPhone and Pixel, browser and standalone display-mode emulation, assert TabBar exists and rect is inside viewport.

## Anti-conditions

- Do not use this pattern for a truly missing route condition or removed TabBar component.
- Do not hide install banners, support FABs, or main content to make the TabBar visible.
- Do not tune safe-area constants before proving whether the TabBar is DOM-missing, offscreen, or clipped.
