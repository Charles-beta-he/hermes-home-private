# Applied case: mobile PWA kill/reopen bottom chrome path error

Scope: scoped example for mobile/PWA debugging. This file preserves the transferable mechanism from a concrete project incident without making the project-specific branch, PR, or commit history a global rule.

Applicability: use when an installed mobile PWA/WebAPK/iOS standalone app is killed from background and reopened, and bottom navigation or restored app chrome appears missing after a splash/loading surface.

Anti-conditions: do not assume this exact cause if the navigation DOM is absent, auth redirects, service-worker stale assets, or measured root/splash heights are short. In those cases follow the generic RPEPR procedure first.

## Path-error pattern

Wrong initial frame:

```text
Bottom navigation is missing -> change navigation top/bottom/fallback positioning.
```

Better frame:

```text
Kill/reopen startup path enters a restored-route/loading/splash state where chrome visibility, root height, and splash lifecycle may disagree.
```

## Evidence to collect before editing

Measure these during early startup and after expected splash teardown:

- `document.documentElement`, `document.body`, app root, app canvas, splash/loading root, and bottom navigation `getBoundingClientRect()`.
- `clientHeight`, `scrollHeight`, `scrollTop`, `overflow`, `position`, `height`, `top`, `bottom`, `opacity`, `z-index`.
- `window.innerHeight`, `visualViewport.height`, `visualViewport.offsetTop`.
- Root markers such as `data-platform`, `data-display-mode`, `data-splash-visible`.
- Storage/lifecycle flags such as `sessionStorage('splash-shown')` when used by the splash.
- Current route and auth state.

## Classification gate

- DOM absent -> route/render/auth condition.
- DOM present + rect inside viewport + opacity 0 -> marker/state/lifecycle.
- DOM present + rect outside viewport -> geometry/viewport/layout.
- DOM present + covered -> stacking/overlay.
- Root/splash/app canvas short -> height ownership/loading layout contract.
- Only installed mode -> standalone/shortcut/service-worker/cache/device path.

Do not change bottom navigation placement until the class is known.

## Known mechanism: splash marker teardown failure

A common mechanism is a splash component that:

1. reads a persisted “already shown” flag during render;
2. writes that flag in an effect;
3. includes the derived render value in the effect dependency;
4. starts exit/remove timers;
5. triggers a rerender when the exit phase starts;
6. re-reads the persisted flag as “already shown”; and
7. cleans up the remove timer before it can clear the splash marker.

Observable result:

- Navigation DOM exists.
- Navigation rect is inside viewport.
- Navigation computed `opacity` is 0 and `pointer-events` is none.
- Root still has the splash/loading marker after the splash should be gone.

Fix shape:

- Freeze the per-mount “should play splash” decision in a ref.
- Do not depend on a render-time storage read after mutating that storage in the effect.
- Ensure marker removal is tied to actual splash unmount/visible state.
- Regression-test the timer/rerender path, not only manual unmount.

## Counterfactuals

If this mechanism is true:

- Clearing the marker should immediately reveal the existing navigation.
- A late snapshot after splash teardown should show no marker, no splash DOM, navigation opacity 1, pointer events restored, and rect inside viewport.

If the loading page is truly short:

- Root/splash/app canvas rects should be shorter than `visualViewport.height`.
- Clearing the marker will not fix the underlying height mismatch.
- The fix belongs in app shell/loading height ownership, not bottom navigation visibility.

## Regression expectation

A useful harness should assert:

- early startup: splash exists, marker exists, restored bottom chrome may be opacity 0;
- late startup: splash absent, marker absent, bottom chrome exists, opacity 1, pointer events restored, rect inside viewport;
- contrast path: normal refresh or already-shown splash path remains visible.
