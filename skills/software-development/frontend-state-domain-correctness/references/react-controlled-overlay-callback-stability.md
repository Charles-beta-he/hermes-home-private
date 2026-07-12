# React Controlled Overlay Callback Stability

## Scope

Use for controlled dialogs, drawers, popovers, sheets, focus traps, and similar overlays whose lifecycle effect installs listeners, locks scroll, marks the app root inert/hidden, records focus, or schedules focus restoration.

Anti-conditions:
- Purely presentational overlays with no lifecycle side effects.
- A callback identity change is intentionally the lifecycle boundary and that behavior is tested.

## Core invariant

An open overlay's lifecycle effect must not tear down and reinstall merely because local content state changes. Search text, list filtering, loading completion, validation, or child rendering must not cause listener churn, transiently restore background interaction, reset focus ownership, or schedule duplicate focus restoration.

Stabilizing only the shared overlay component is insufficient. Callback identity is an end-to-end property:

1. The overlay's internal close dispatcher must be stable.
2. The controlled `onOpenChange` supplied by its caller must be stable.
3. Any parent callback captured by that wrapper must also be stable, or be read through an intentional latest-callback ref/event primitive.

A typical safe call site:

```tsx
const closeOverlay = useCallback(() => {
  setOpen(false);
  queueMicrotask(() => triggerRef.current?.focus());
}, []);

const handleOpenChange = useCallback(
  (nextOpen: boolean) => {
    if (!nextOpen) closeOverlay();
  },
  [closeOverlay]
);

<Drawer open={open} onOpenChange={handleOpenChange} />
```

If the callback must always observe changing values but should not restart the modal effect, store the latest callback in a ref (or use the framework's stable event primitive) and keep the effect dependent on overlay state rather than callback identity. Document that ownership choice explicitly.

## Debugging path

1. Identify lifecycle side effects: `addEventListener`, scroll lock, `inert`, `aria-hidden`, focus capture/restore, timers, history state.
2. Trace every effect dependency through the component boundary. A memoized internal `setOpen` can still churn when its caller passes an inline function.
3. Reproduce with an unrelated local rerender while the overlay remains open—typing in search is ideal.
4. Instrument the actual event target (`window` vs `document`). Counting the wrong target can produce a false zero.
5. Capture listener add/remove counts immediately after open and after the unrelated rerender. They must be unchanged between those checkpoints.
6. Verify functional behavior in the same run: initial focus, Tab containment, Escape, background inertness, close, focus restoration, and original attribute restoration.
7. Run against a fresh served artifact. A long-lived preview page or service worker may keep an old bundle; use an isolated browser profile or restart the preview/browser before accepting GREEN.

## RED/GREEN evidence shape

```json
{
  "opened": {"adds": 2, "removes": 1},
  "afterUnrelatedRerender": {"adds": 3, "removes": 2}
}
```

After the callback chain is stable:

```json
{
  "opened": {"adds": 1, "removes": 0},
  "afterUnrelatedRerender": {"adds": 1, "removes": 0}
}
```

Absolute counts may vary under StrictMode or other page listeners; the key assertion is no delta while the same overlay remains open. Isolate or tag the relevant listener where shared global listeners make totals ambiguous.

## Pitfalls

- Fixing exhaustive-deps warnings in the overlay but ignoring inline callbacks at call sites.
- Treating passing focus/Escape tests as proof that no lifecycle churn occurred.
- Instrumenting `document.addEventListener` when the implementation listens on `window`.
- Accepting a cached preview's result after rebuilding a different output directory.
- Promoting the original commit after an AMEND; certify the explicit remediation chain.
- Claiming multi-overlay nesting, direct-unmount behavior, mobile keyboard/WebView behavior, or production accessibility from a single desktop-browser probe.

## Verification checklist

- [ ] Internal dispatcher identity is stable.
- [ ] Controlled call-site callback identity is stable across content-state rerenders.
- [ ] Parent callbacks captured by the wrapper are stable or intentionally ref-backed.
- [ ] Listener counts do not change from open to unrelated rerender.
- [ ] Scroll lock, inert, and `aria-hidden` do not transiently restore.
- [ ] Escape and Tab behavior remain correct.
- [ ] Close restores the original focus and original root attributes.
- [ ] Test runs against the current artifact in a fresh enough browser context.
- [ ] Independent review names the full original+remediation commit chain and evidence boundary.
