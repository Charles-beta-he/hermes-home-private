# PWA TabBar scroll-owner debugging

Use when a mobile/PWA bottom TabBar appears to create a gray/blank band, abnormal scrollbar, or a scrollable white area near the bottom.

## Core lesson

Do not start by changing the TabBar positioning (`absolute` -> `fixed`) or by tuning safe-area constants. First find the scroll owner and the element whose `scrollHeight` is abnormal.

A bottom blank/gray band can be caused by the intended internal scroll container carrying a real `padding-bottom` reserve equal to the TabBar height + bottom gap. When the user scrolls to the end, that pure padding becomes visible behind a translucent/glass TabBar.

## Debug procedure

1. Enumerate root and shell geometry:
   - `html`
   - `body`
   - `#root`
   - app/phone portal shell
   - app shell wrapper
   - intended scroll owner such as `main[data-screen-scroll]`
   - current page root such as `.screen-enter`
   - bottom chrome such as `nav` / TabBar
2. For each, read:
   - `clientHeight`, `scrollHeight`, `scrollTop`
   - `getBoundingClientRect()` top/bottom/height
   - computed `overflow`, `overflowY`, `position`
   - computed `height`, `bottom`, `padding-bottom`, `margin-bottom`
3. Identify the only element with `scrollHeight > clientHeight` or unexpected bottom beyond the viewport.
4. Scroll that element to its maximum `scrollTop`, then compare:
   - scroll owner bottom
   - content/page-root bottom
   - TabBar top/bottom
   - viewport bottom
5. If the gap between content bottom and scroll owner bottom equals the TabBar reserve token, the bug is a scroll-padding-tail bug, not a chrome-positioning bug.

## Known pattern

Bad pattern:

```tsx
main[data-screen-scroll] {
  bottom: 0;
  padding-bottom: var(--tabbar-content-reserve); // e.g. 52px + 8px = 60px
}
```

This makes the full reserve part of real scrollable content height. With a translucent TabBar, the user can scroll into a pure padding area.

Better pattern when TabBar remains absolute inside the app shell:

```tsx
main[data-screen-scroll] {
  bottom: var(--tabbar-content-reserve); // end viewport above TabBar
  padding-bottom: var(--tabbar-visual-bottom-gap); // small breathing room only
}
```

This keeps the scroll viewport above the TabBar and avoids a full reserve tail while retaining a small final-item visual gap.

## Anti-conditions

- Do not apply this blindly to pages where scroll content intentionally extends behind a blur/glass nav for a design reason.
- If `html/body/#root` also have `scrollHeight > clientHeight`, fix document/root scroll ownership first.
- If only TabBar is clipped while main content is not affected, the issue may be chrome layer clipping rather than scroll reserve.
- If Android system navigation underlaps the TabBar, handle platform baseline/system-nav separately; do not remove Android safety baseline just to fix iOS padding tails.

## Verification checklist

- Before and after DOM probe shows root/shell elements are not the abnormal scroll owner unless the fix explicitly targets them.
- The intended scroll owner still scrolls content normally.
- At max scroll, page content bottom is close to scroll owner bottom (usually only the visual gap), not `tabbar height + bottom gap` away.
- TabBar top aligns with the scroll owner bottom when using the inset-scroll-viewport model.
- Browser H5, iOS standalone PWA, and Android standalone PWA platform baselines remain separately verified.
