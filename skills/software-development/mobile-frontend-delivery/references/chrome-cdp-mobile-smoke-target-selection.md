# Chrome/CDP mobile smoke target selection

Use when a mobile H5/PWA verification script launches Chrome headless (or connects to an existing Chrome) through the DevTools Protocol and evaluates DOM/runtime assertions.

## Problem pattern

A CDP script may connect successfully but evaluate against the wrong target, especially when Chrome exposes extension/background targets. Symptoms can look like app failures:

- `Runtime.evaluate` returns empty `document.body.innerText` even though the page is visible in a browser.
- Current evaluated URL is `chrome-extension://.../background.html` or another non-app page.
- DOM assertions fail for all expected text despite the target URL being opened elsewhere.
- Repeated retries of the same script hit tool-loop guards without improving evidence.

Root cause: the script selected the first `/json` page target instead of selecting the app page by URL/origin.

## Diagnostic steps

1. List CDP targets after navigation:
   - `GET http://127.0.0.1:<debug-port>/json`
2. Record the URL of the target actually connected by WebSocket.
3. Before app assertions, run tiny readbacks:
   - `1+1`
   - `document.readyState`
   - `location.href`
   - `document.body && document.body.innerText.slice(0, 200)`
4. If `location.href` is not the app URL, stop debugging the product and fix target selection.

## Robust target selection

Prefer explicit app-origin target selection:

```js
let pages = await fetchJson(`http://127.0.0.1:${port}/json`);
let page = pages.find(p => p.type === 'page' && String(p.url || '').includes('127.0.0.1:4173'))
  || pages.find(p => p.type === 'page' && !String(p.url || '').startsWith('chrome-extension://'))
  || pages.find(p => p.type === 'page')
  || pages[0];
```

If the script calls `Page.navigate`, refresh the `/json` target list after navigation and re-check that the selected target URL is the expected app origin before `Runtime.evaluate` assertions.

## Verification checklist

- [ ] CDP `location.href` readback matches the expected app origin/path.
- [ ] Tiny Runtime.evaluate probes pass before complex DOM assertions.
- [ ] The smoke output records current URL, viewport, key visible text, and screenshot path.
- [ ] If a repeated command is blocked by a loop guard, change the script path/arguments only after changing the diagnostic strategy; do not keep retrying unchanged.
- [ ] Treat the fixed CDP script as verification infrastructure, not product evidence by itself; still capture screenshot/readback from the app page.

## Anti-conditions

Do not store a blanket claim that Chrome/CDP/browser tools are broken. This is a target-selection pitfall, not a durable tool limitation.
