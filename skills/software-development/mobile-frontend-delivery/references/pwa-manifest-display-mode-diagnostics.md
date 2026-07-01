# PWA manifest display-mode diagnostics for mobile viewport bugs

Scope/applicability: mobile web / installed PWA layout bugs where bottom chrome, safe areas, or viewport units behave differently after install, cache clear, service-worker update, or cold reload. Use this to separate manifest display-mode causes from CSS/runtime viewport causes.

Anti-conditions: do not treat this as proof for native wrappers or app-store shells; do not infer the live manifest from source only when a deployed URL is involved.

## Diagnostic order

1. **Read source manifest config**
   - For Vite PWA, inspect the `VitePWA({ manifest: ... })` block.
   - Look specifically for:
     - `display`
     - `display_override`
     - `start_url`
     - `scope`
     - `theme_color` / `background_color`

2. **Read the live manifest** when there is a deployed/acceptance URL
   - Fetch `/manifest.webmanifest` from the actual URL users installed.
   - Compare live `display` / `display_override` against source; SW/cache or deployment lag can make source-only conclusions wrong.

3. **Search the repo for fullscreen separately**
   - `fullscreen` in helper code (for iOS Web Clips or history/swipe guards) is not the same as `manifest.display = "fullscreen"`.
   - Classify occurrences by surface:
     - manifest config / generated manifest: can affect PWA display mode;
     - runtime installed-mode detection: usually only affects app behavior after load;
     - comments/tests: evidence only, not behavior.

4. **Do not over-blame `fullscreen` without evidence**
   - If source and live manifest say `display: "standalone"` and `display_override` does not include `fullscreen`, then fullscreen is not the root cause.
   - Continue with viewport/canvas/TabBar geometry: `data-display-mode`, `100dvh`, `visualViewport`, app-shell trim, and bottom chrome `bottom` token.

## Android clear-cache reload pitfall

For Android installed PWA bugs after a button deletes CacheStorage, unregisters service workers, then calls `location.reload()`:

- Cache/SW actions are often the **trigger**, not the geometric root cause.
- Manifest remains installed-state metadata unless site data/install state is actually cleared.
- A reload can still expose early `matchMedia('(display-mode: standalone)')` or `100dvh` instability.
- Verify the live manifest first, then measure runtime layout.

## Interpretation examples

### Not fullscreen-rooted

```json
{
  "display": "standalone",
  "display_override": ["window-controls-overlay", "standalone", "minimal-ui"]
}
```

Conclusion:
- Not a manifest `fullscreen` issue.
- `window-controls-overlay` is mainly a desktop PWA mode; on Android it usually falls back to `standalone` if unsupported.
- You may still reduce variables by removing unnecessary overrides, but that is a hardening step, not a proven root cause.

### Fullscreen-rooted candidate

```json
{
  "display": "fullscreen"
}
```

or:

```json
{
  "display_override": ["fullscreen", "standalone"]
}
```

Conclusion:
- Treat as a plausible Android viewport instability cause.
- Test by moving to `display: "standalone"` without `fullscreen` in overrides and reinstalling/refreshing the PWA install metadata; a simple page reload may not update installed WebAPK metadata immediately.

## Runtime probe

Run in the installed PWA at the broken moment:

```js
(() => ({
  manifestLink: document.querySelector('link[rel="manifest"]')?.href || '/manifest.webmanifest',
  displayMode: document.documentElement.dataset.displayMode,
  platform: document.documentElement.dataset.platform,
  standaloneMedia: window.matchMedia?.('(display-mode: standalone)').matches,
  fullscreenMedia: window.matchMedia?.('(display-mode: fullscreen)').matches,
  viewport: {
    innerHeight,
    clientHeight: document.documentElement.clientHeight,
    visualViewport: window.visualViewport && {
      height: window.visualViewport.height,
      offsetTop: window.visualViewport.offsetTop,
    },
  },
}))();
```

If fullscreen media is false and live manifest is standalone, continue with app-shell geometry rather than manifest diagnosis.
