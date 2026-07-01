# iOS PWA status-bar style and safe-top double counting

Applicability: iOS Home Screen PWA / standalone web app where the app owns a fixed/fullscreen shell, uses `viewport-fit=cover`, injects or consumes `--safe-top`, and a recent change touched first-paint loading/splash, `apple-mobile-web-app-status-bar-style`, or status-bar theme syncing.

Anti-conditions: do not apply to normal Safari browser tabs, native React Native views, or apps that do not add app-owned top padding/header offsets. Do not assume this is the cause without checking the served HTML/CSS and a real iOS/standalone screenshot or recording.

## Symptom

The app appears as if the whole visible iOS viewport was pulled downward:

- Large blank space between the Dynamic Island/status bar and the first app content (logo/title/header).
- Top content starts lower than expected across multiple pages, not only during one route transition.
- Bottom chrome may still look mostly normal; the main visual defect is top spacing.
- A loading/splash change may be blamed, but the actual issue can persist after loading because the shell/header is double-avoiding the status bar.

## Root cause pattern

A common regression is combining these two models:

1. iOS PWA status bar mode is changed to `default`, so WebKit owns/avoids the status bar area.
2. The app still injects or consumes an app-owned `--safe-top` fallback, for example:
   - `index.html` writes `--safe-top: 47px` when `env(safe-area-inset-top)` reports 0 in standalone.
   - `TopBar` uses `paddingTop: var(--safe-top)`.
   - main scroll geometry uses `top: calc(52px + var(--safe-top))`.

Result: the status-bar/notch area is avoided twice, making the whole app shell look lowered.

## Investigation checklist

1. Inspect the user evidence first: video/screenshot frames around launch and after route transitions. Classify whether the shift is only during splash/loading or persists on stable pages.
2. Fetch/read the served `index.html`, not only local source, and check:
   - `<meta name="apple-mobile-web-app-status-bar-style" ...>` value.
   - viewport tag includes `viewport-fit=cover`.
   - first-paint scripts that set `data-platform`, `data-display-mode`, or CSS vars such as `--safe-top`.
3. Fetch/read served CSS and search for:
   - `--safe-top`, `env(safe-area-inset-top)`, `--tabbar-top`, `--app-visual-height`.
   - header/topbar rules that add `padding-top: var(--safe-top)`.
   - scroll viewport rules such as `top: calc(52px + var(--safe-top))`.
4. Use git history/blame on `index.html`, root CSS, `TopBar`, `App` shell, splash, and viewport-stability helpers. Recent status-bar/theme-sync commits can be the trigger even if their title says “loading” or “theme”.
5. Confirm deployment freshness: online HTML/CSS asset hashes or `/version.json` should match the suspected commit/time before attributing the recording to local HEAD.

## Fix decision

Choose one top safe-area ownership model:

### Fast rollback / low-risk stopgap

If the current shell already expects to own the top inset, restore iOS PWA status-bar mode to `black-translucent` and keep app-owned `--safe-top` behavior. Verify light/dark status-bar legibility after the change.

### Cleaner long-term model

If product wants `apple-mobile-web-app-status-bar-style=default`, then gate or remove the standalone iOS `--safe-top` fallback for that mode, and ensure `TopBar`/main geometry does not add a second notch/status offset. Verify on real iOS standalone because simulator/browser mode may not match WebKit PWA behavior.

## Verification

- Real iOS standalone/Home Screen screenshot or recording after cold launch and after splash exits.
- Stable tab page: logo/title starts at intended top position, not double-spaced below Dynamic Island.
- Non-tab flow page: back/title area avoids the notch without extra blank band.
- Bottom TabBar remains inside viewport; do not regress bottom safe-area fixes while correcting top ownership.
- Served HTML/CSS are read back from the target URL so stale PWA/service-worker bundles are ruled out.
