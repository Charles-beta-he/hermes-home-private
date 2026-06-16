# UVISA C-end bottom TabBar Liquid Glass verification

Use for UVISA C-end tasks where Lark/prototype evidence says the bottom navigation should use iOS-style Liquid Glass and should not have a separate solid bottom strip.

## Class-level acceptance atoms

- Target routes: `/home` (资产首页), `/card` (U-VISA 首页), `/me` (我的首页). Include `/wealth` if the task names the wealth tab.
- TabBar is a floating rounded pill, not an edge-to-edge bottom plate.
- Match the prototype's visible geometry before declaring done.
- When screenshots mention phone dark/night mode, explicitly reproduce Android system dark + app light before concluding. For the detailed matrix and theme-color pitfall, see `references/android-pwa-app-theme-vs-system-dark.md`.
- Background is translucent glass: content underneath can visually bleed through.
- CSS/computed style matches the current accepted translucent-glass contract, not merely the old prototype blur contract:
  - Light mode `.glass`: `background: rgba(255, 255, 255, 0.58)` and `border: .5px solid rgba(255, 255, 255, 0.7)`.
  - Dark mode `[data-theme="dark"] .glass`: `background: rgba(27, 30, 37, 0.58)` and `border: .5px solid rgba(255, 255, 255, 0.12)`.
  - Do not add `backdrop-filter` / `-webkit-backdrop-filter` on the TabBar glass surface, either in CSS or inline React style; in this product context those blur filters made the bar look too opaque/muddy and user explicitly requested removing them.
- No extra solid bottom background/strip is created behind the TabBar. Distinguish a legitimate prototype 18px floating gap from a separate solid backing plate/strip.
- Main scroll viewport extends to the bottom (`bottom: 0`) and uses bottom padding/reserve for readability instead of clipping the content above the TabBar; otherwise the glass can only show the page canvas color and look like a solid strip.
- Active tab highlight remains inside the pill and does not become a separate bottom background.

## Reference implementation pattern

Prototype repo path observed for UVISA C-end:

- `uvdemo2.0/uvisa-app/src/components/TabBar.tsx`
- `uvdemo2.0/uvisa-app/src/index.css`

Prototype pattern:

```tsx
<nav className="absolute ... rounded-32 glass shadow-tab flex">
```

```css
.glass {
  background: rgba(255, 255, 255, 0.58);
  border: .5px solid rgba(255, 255, 255, 0.7);
}
[data-theme="dark"] .glass {
  background: rgba(27, 30, 37, 0.58);
  border: .5px solid rgba(255, 255, 255, 0.12);
}
```

- Do not copy blindly: preserve current geometry tokens such as `--tabbar-height`, `--tabbar-bottom-gap`, and `--tabbar-content-reserve` if they were introduced to prevent iOS/Android gesture-bar regressions. For UVISA C-end, do **not** make the TabBar bottom gap additive with synthesized iOS standalone bottom safe-area height (`--system-safe-bottom` / `--app-safe-bottom`). First login or cold PWA relaunch can synthesize/report a large bottom inset and lift the pill too high, leaving a large blank band under it. Keep the base TabBar gap as the fixed product geometry token (for example 18px), let only non-tab full-screen flows use `--safe-bottom` when needed, and handle Android system navigation overlap with a separate bounded `visualViewport`-derived token (for example `--android-visual-bottom-inset` from `innerHeight - visualViewport.height - offsetTop`) scoped to `[data-display-mode="standalone"][data-platform="android"]`. Never reintroduce `screen.height - innerHeight` as a generic bottom inset. For this product's accepted visual, also remove stale inline `backdropFilter` / `WebkitBackdropFilter` from `TabBar.tsx`; an inline filter overrides CSS tuning and makes the translucent surface look wrong.

## Workflow

1. Read the specific Lark task by GUID if provided; extract exact surfaces and screenshots.
2. Inspect the current target repo and recent branches/worktrees before editing. If the main working tree is dirty, prefer a clean worktree or current `origin/main` evidence rather than mixing unrelated changes.
3. Compare target TabBar against the prototype implementation:
   - component class names (`glass` vs custom `tabbar-glass`);
   - CSS opacity/border for light and dark themes;
   - absence of `backdrop-filter` / `-webkit-backdrop-filter` in both CSS and inline styles;
   - scroll viewport bottom/padding behavior.
4. Add or update a focused layout test covering:
   - TabBar class/style glass contract;
   - prototype geometry (`h-16`/64px, 18px browser bottom gap, 32px radius, `shadow-tab`);
   - tab-page scroll reserve extends behind TabBar;
   - no stale inline `backdropFilter` / `WebkitBackdropFilter` and no CSS `backdrop-filter` / `-webkit-backdrop-filter` if the accepted design is the current semi-transparent surface.
5. Run targeted test and build.
6. For UI proof, run a real browser/mobile viewport check on the built preview and record computed styles for `/home`, `/card`, and `/me`:
   - `navBackground` is the accepted translucent rgba for the active theme;
   - `navBackdrop` is `none` when the current accepted design is the semi-transparent surface rather than blurred glass;
   - `navBorderRadius` is pill-like;
   - `navBorderRadius` is pill-like (`32px`);
   - `mainBottom` is `0px`;
   - `mainPaddingBottom` reserves content height + 18px gap;
   - screenshots show a floating glass pill with no extra solid backing strip.

## Pitfalls

- A TabBar can have blur CSS but still look wrong if the scroll container is clipped above it; ensure content can exist behind the glass.
- `tabbar-glass` variants with lower alpha may be correct in some branches, but if Lark explicitly references the prototype Liquid Glass, first check whether the prototype’s shared `.glass` class is now the canonical target.
- Do not close Lark final completion from local preview alone. UVISA Lark final closeout still needs online UI evidence and native screenshot attachment when that closeout gate applies.
