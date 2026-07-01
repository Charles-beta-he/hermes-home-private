# PWA route-return safe-area resettling

## Applicability

Use when an installed PWA looks correct on first load, but after navigating to a non-tab route (for example About / update / legal / settings, receiving-info/payment flow pages) and returning to a main tab, the floating bottom TabBar is lifted and a large blank/frosted block appears below it.

Also use when the lift appears after opening/closing searchable pickers, country/region dropdowns, bottom sheets, or input-heavy flow screens before returning to a Tab route. These controls can leave document scroll or `visualViewport` state settling after React route changes even if the TabBar CSS token itself is stable.

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

Keep TabBar geometry tokens stable. Add a route-return settle pass that runs more than once. If the app has a global viewport-stability runtime, expose a shared primitive (for example `settleViewportLayout`) and call it from both native viewport listeners and route-change effects instead of duplicating partial scroll resets.

```ts
export function scheduleViewportSettles(root = document.documentElement): () => void {
  const timers: ReturnType<typeof setTimeout>[] = [];
  const settle = () => settleViewportLayout(root); // reset scroll + reconcile safe-area + visual bottom inset

  settle();
  window.requestAnimationFrame?.(settle);
  [150, 300, 600].forEach((delay) => timers.push(setTimeout(settle, delay)));
  return () => timers.forEach(clearTimeout);
}
```

Route effects should return the cleanup from this helper after resetting the app's internal screen scroller. Keep the helper generic and call it from route changes, native viewport listeners, and any explicit picker/dropdown settle event if the app needs one.

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
- Layout regression checks outer scroll ownership: `html`, `body`, framework root, and app shell stay non-scroll owners (`overflow:hidden`, `scrollHeight === clientHeight` where applicable), while the intended internal screen scroller remains scrollable.
- Browser/mobile harness verifies at least one affected non-tab flow route and one picker/dropdown route returning to a Tab page; compare `window.innerHeight - nav.getBoundingClientRect().bottom` before and after and require the gap to remain stable.
- Existing safe-area tests still pass; TabBar fixed gap/content reserve tokens are unchanged.
- Build artifact still preserves app-owned `theme-color` behavior and platform visual inset tokens.
- Final visual acceptance should use installed PWA/native package content, not `ChromeTabbedActivity` browser-tab content.
