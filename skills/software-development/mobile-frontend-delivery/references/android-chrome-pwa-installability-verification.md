# Android Chrome PWA Installability Verification

Use this when verifying whether a deployed web app is eligible for Android Chrome PWA installation, especially when users see both “Install” and “Create shortcut”.

## Evidence hierarchy

1. **Static delivery sanity**
   - HTTPS origin.
   - `/manifest.webmanifest` returns `200` with `Content-Type: application/manifest+json`.
   - Manifest has `name`/`short_name`, `start_url`, `scope`, `display: standalone`, and 192/512/maskable icons.
   - `/sw.js` returns JavaScript with no long immutable cache. Prefer `no-cache, no-store, must-revalidate` for SW and registration scripts.
   - Icons referenced with query strings still resolve to `200 image/png`.

2. **Browser installability proof**
   - Use Chrome DevTools Protocol on the target browser:
     - `Page.getAppManifest` should return no `errors` and a parsed scope under the tested origin.
     - `Page.getInstallabilityErrors` should return `installabilityErrors: []`.
   - Also instrument `beforeinstallprompt`; on Android Chrome it should fire with `platforms: ['web']` and a callable `prompt()` when the site is installable and not suppressed by cooldown/native-app state.

3. **Service-worker runtime proof**
   - Page JS should read back `navigator.serviceWorker.ready === true` and an active registration with the expected scope.
   - `navigator.serviceWorker.controller` can be false on the first load; reload or wait for activation before treating it as a failure.

4. **Android Chrome UI proof**
   - In Chrome menu, `Add to Home screen` may be the entry point even for installable PWAs.
   - After tapping it, modern Chrome can show two explicit choices:
     - `Install` — PWA install path.
     - `Create shortcut` with subtitle like `Shortcuts open in Chrome` — ordinary browser shortcut path.
   - If both are visible, the site is installable as a PWA; user guidance must tell them to choose `Install`, not `Create shortcut`.

## CDP probe pattern

```js
const client = await context.newCDPSession(page);
await client.send('Page.enable');
await client.send('Runtime.enable');
await client.send('Page.addScriptToEvaluateOnNewDocument', { source: `
  window.__pwaProbe = { beforeinstallprompt: false, events: [], appinstalled: false };
  window.addEventListener('beforeinstallprompt', e => {
    window.__pwaProbe.beforeinstallprompt = true;
    window.__pwaProbe.platforms = e.platforms || null;
    window.__pwaProbe.hasPrompt = typeof e.prompt === 'function';
    window.__pwaProbe.events.push({ type: 'beforeinstallprompt', platforms: e.platforms || null, t: Date.now() });
  });
  window.addEventListener('appinstalled', () => {
    window.__pwaProbe.appinstalled = true;
    window.__pwaProbe.events.push({ type: 'appinstalled', t: Date.now() });
  });
`});
await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(12000);
const manifest = await client.send('Page.getAppManifest');
const installErr = await client.send('Page.getInstallabilityErrors');
```

Expected positive signals:

```json
{
  "manifest": { "errors": [], "parsed": { "scope": "https://example.com/" } },
  "installErr": { "installabilityErrors": [] },
  "probe": { "beforeinstallprompt": true, "platforms": ["web"], "hasPrompt": true }
}
```

## Lighthouse version pitfall

Lighthouse v13 no longer exposes the old `pwa` category in the same way; `--only-categories=pwa` can fail with `unrecognized category in 'onlyCategories': pwa`. Do not stop there. Run full Lighthouse for general HTTPS/console evidence, then use CDP `Page.getInstallabilityErrors` and Android Chrome UI evidence for installability.

## Reporting rubric

Say “Chrome installability satisfied” only when all of these are evidenced:

- Static delivery is valid.
- `Page.getInstallabilityErrors` is empty.
- `beforeinstallprompt` fired or Chrome UI shows `Install`.
- SW is active/ready on the target origin.

Say “PWA installed/standalone verified” only after a launch from the installed entry reports `matchMedia('(display-mode: standalone)').matches === true`. Installability proof is not the same as standalone launch proof.
