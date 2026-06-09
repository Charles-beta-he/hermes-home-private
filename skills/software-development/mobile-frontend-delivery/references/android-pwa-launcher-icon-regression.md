# Android PWA Launcher Icon Regression

Use when an installed Android PWA shows the wrong home-screen / launcher icon even though the manifest appears to reference the expected filenames.

## Durable lessons

For Android PWA launcher bugs, verify the bytes of the manifest icon files, not only the manifest paths. A regression can preserve `manifest.icons[].src` while replacing the PNG contents with the wrong visual variant.

If Android shows a generic colored circle with initials/letters from the app name (for example `UV`) instead of the brand artwork, treat it as a Chrome/WebAPK fallback launcher icon. Common causes are stale OS/WebAPK icon cache, previously failed icon fetch/selection, or manifest icon URLs that stayed byte-path-stable while the underlying PNG changed.

## Investigation checklist

1. Locate the generated/runtime manifest source, usually `vite.config.ts` with `vite-plugin-pwa` or a static `manifest.webmanifest`.
2. Identify the actual Android launcher files from `manifest.icons[]`, especially:
   - `/icon-192.png`
   - `/icon-512.png`
   - `/icon-maskable.png`
3. Inspect dimensions and visual content of those PNGs. Do not treat correct filenames as proof.
4. Fetch the deployed manifest and icon URLs, including response headers. Record `cache-control`, `etag`, `last-modified`, status, content type, and image dimensions.
5. If deployed icons are correct but installed Android still shows a letter/initial fallback, change the manifest icon `src` values to new versioned URLs (for example `/icon-512.png?v=<date>-<variant>`) so WebAPK/Chrome must refetch the icons instead of reusing stale immutable cache.
6. For clearer icon selection, use explicit purposes:
   - ordinary square icons: `purpose: 'any'`
   - maskable icon: `purpose: 'any maskable'`
7. Cross-check project brand docs, preview pages, or git history for the intended launcher variant. In UVISA-like brand workflows, preview docs may explicitly separate browser favicon / iOS apple-touch-icon / Android launcher variants.
8. Keep the fix scoped to Android launcher assets and manifest icon entries unless evidence says otherwise. Do not unnecessarily change `apple-touch-icon`, favicon SVG/PNG, or unrelated metadata.
9. If the main working tree has unrelated dirty/untracked files that break build, verify the scoped icon patch in a clean temporary worktree rather than editing or deleting unrelated files.

## Verification

- Confirm image dimensions match manifest declarations.
- Visually inspect the launcher PNGs at 192 and 512 sizes.
- Run the frontend build from a clean tree or clean worktree and inspect `dist/manifest.webmanifest` to ensure the manifest references the intended files and versioned URLs.
- Fetch deployed manifest/icons with `curl -I` / `curl -fsSL` after deployment; if icon responses are `immutable` or long-lived, a manifest `src` version bump is the proof that the browser has a new cache key.
- For an already installed Android PWA, remove/reinstall the PWA/home-screen icon when validating. URL versioning should force a refetch for fresh installs, but OS/WebAPK icon state can still persist for existing installs.

## Pitfalls

- Fixing only `index.html` favicon links: Android launcher uses the web app manifest, not browser tab favicon links.
- Assuming `purpose: maskable` changes artwork: maskable affects cropping/background behavior, but the PNG contents still must be the intended design.
- Broadly reverting all icon assets: Android launcher, iOS `apple-touch-icon`, and browser favicon can intentionally use different variants.
- Mistaking a letter/initial icon for a bad PNG design. A colored circle with app initials is usually generated fallback; check deployed icon bytes and cache headers before changing artwork.
- Reusing unversioned icon paths with long-lived `immutable` caching. If the server serves `/icon-512.png` with a week-long immutable cache, changing bytes alone may not affect Chrome/WebAPK installs promptly; version the manifest icon `src`.
