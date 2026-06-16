# PWA route-return safe-area resettling

## Applicability

Use when an installed PWA looks correct on first load, but after navigating to a non-tab route (for example About / update / legal / settings) and returning to a main tab, the floating bottom TabBar is lifted and a large blank/frosted block appears below it.

This is most common in iOS installed PWA/WebKit, but the same debugging shape can apply to Android/WebView when visual viewport state settles after React route changes.

## Symptom shape

- Main tab bottom TabBar appears higher than intended.
- A large blank, translucent, or frosted area remains underneath the TabBar.
- The issue appears only after routing or after an update-check/about screen interaction, not on a clean first render.
- Browser-tab screenshots may not reproduce it; installed PWA evidence is required for final visual proof.

## Root cause pattern

Do not assume the CSS token is wrong just because the TabBar is lifted. In installed PWAs, route changes can be followed by late `visualViewport` / safe-area / window-scroll settlement:

1. React swaps from a non-tab page back to a tab page.
2. The app immediately applies tab-page bottom classes and positions the absolute TabBar.
3. iOS/WebKit updates `window.scrollY`, `documentElement.scrollTop`, `visualViewport.offsetTop`, or `env(safe-area-inset-*)` slightly later.
4. A one-shot route reset misses the late update, leaving the whole `h-dvh` canvas or TabBar visually displaced.

## Fix pattern

Keep TabBar geometry tokens stable. Add a route-return settle pass that runs more than once:

```ts
const settle = () => {
  settleViewportLayout(); // reset scroll + reconcile safe-area + visual bottom inset
  resetStrayWindowScroll();
};

settle();
requestAnimationFrame(settle);
[150, 300, 600].forEach((delay) => setTimeout(settle, delay));
```

`settleViewportLayout()` should be a small shared primitive that:

- resets stray `window.scrollY` and `document.documentElement.scrollTop` when no editable element is active;
- reconciles any first-paint safe-area guesses against real `env()` values;
- reconciles platform-specific visual bottom inset tokens, without writing them to generic `--safe-bottom`.

## Anti-conditions

- If the TabBar is wrong on first render in every route, inspect the CSS tokens and safe-area model first.
- If the bottom black area is the native system navigation bar clipping content, use Android/WebView underlap handling instead of route resettling.
- If the installed wrapper never reaches app content and only shows Android default splash, record wrapper/runtime blocker; do not treat the splash screenshot as PWA theme/layout proof.

## Verification checklist

- Unit test the settle primitive: stale scroll + stale safe-area guess are reconciled together.
- Route reset test or code review confirms multiple settle passes on pathname change.
- Existing safe-area tests still pass; TabBar fixed gap/content reserve tokens are unchanged.
- Build artifact still preserves app-owned `theme-color` behavior and platform visual inset tokens.
- Final visual acceptance should use installed PWA/native package content, not `ChromeTabbedActivity` browser-tab content.
