---
name: pwa-install-prompt
description: "Control browser PWA install prompts — beforeinstallprompt, iOS fallback, custom install UI. Use when adding PWA install flow, diagnosing why install prompt doesn't appear, or building cross-platform install UX."
triggers:
  - PWA install prompt
  - beforeinstallprompt
  - 添加到主屏幕
  - install PWA
  - iOS Safari install guide
  - PWA 不弹安装
  - usePwaInstall
---

# PWA Install Prompt

Control when and how the "Add to Home Screen" prompt appears. Chrome auto-fires
`beforeinstallprompt`; Safari iOS never does — both need explicit handling.

## Chrome Install Criteria (ALL required)

| # | Condition | How to verify |
|---|-----------|--------------|
| 1 | HTTPS or localhost | Check deploy URL |
| 2 | Valid manifest (name, icons 192+512, start_url, display) | Lighthouse PWA audit |
| 3 | Service Worker registered + activated | `navigator.serviceWorker.ready` |
| 4 | User not previously dismissed (90-day cooldown) | Can't verify programmatically |
| 5 | User has engagement (30s + 1 click minimum) | DevTools → Application → Manifest |
| 6 | Not in incognito | Check |
| 7 | No native app installed for same domain on Android | Capacitor/Cordova builds block PWA prompt |

**UVISA note**: `@capacitor/android` is in dependencies. If native Android app
is installed, Chrome suppresses the PWA install prompt entirely.

## Platform Behavior

| Platform | Auto prompt | Manual trigger |
|----------|------------|---------------|
| Chrome Android | Mini-infobar after criteria met | `beforeinstallprompt` event |
| Chrome Desktop | Install icon in address bar | `beforeinstallprompt` event |
| Edge | Similar to Chrome | `beforeinstallprompt` event |
| Safari iOS | **Never** | User: Share → Add to Home Screen |

## usePwaInstall Hook

```typescript
// src/hooks/usePwaInstall.ts
import { useEffect, useRef, useState } from 'react';

export function usePwaInstall() {
  const deferred = useRef<BeforeInstallPromptEvent | null>(null);
  const [canInstall, setCanInstall] = useState(false);

  useEffect(() => {
    const handler = (e: BeforeInstallPromptEvent) => {
      e.preventDefault();        // Block default mini-infobar
      deferred.current = e;      // Store for later
      setCanInstall(true);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const prompt = async () => {
    if (!deferred.current) return false;
    deferred.current.prompt();
    const { outcome } = await deferred.current.userChoice;
    deferred.current = null;
    setCanInstall(false);
    return outcome === 'accepted';
  };

  return { canInstall, prompt };
}
```

## Android OEM / HarmonyOS Install Edge Cases

### Do not treat `accepted` as installed

On Android Chrome, `BeforeInstallPromptEvent.userChoice` resolves when the browser prompt is accepted. It can happen before the launcher or OEM permission layer finishes creating the desktop icon/WebAPK. OnePlus/ColorOS may then show a system dialog like “Allow Chrome to create desktop shortcut?”. If the user denies it, or if the browser only supports shortcut creation, the site may not be installed as a standalone PWA.

Correct state model:

1. `beforeinstallprompt` captured → app can show a browser install affordance.
2. `prompt()` called and `userChoice === 'accepted'` → browser flow started/accepted only.
3. `appinstalled` fired, or later `display-mode: standalone` / `navigator.standalone` readback is true → installed.

Do not call `setIsInstalled(true)` only from `userChoice === 'accepted'`.

### HarmonyOS / Huawei Browser fallback

HarmonyOS, Huawei Browser, ArkWeb, and OEM browsers may not emit `beforeinstallprompt` even with a valid manifest and service worker. Detect likely platform from UA markers such as `HarmonyOS`, `OpenHarmony`, `ArkWeb`, `HuaweiBrowser`, or `Huawei`, then after a short bounded wait (for example 1–2s) show manual browser-menu guidance if no native prompt arrived.

Manual guidance should be Android/Harmony-specific, not iOS profile copy:

- Open browser menu.
- Prefer “安装应用 / Install app”.
- If only “添加到主屏幕 / 创建快捷方式” appears, explain it may open inside the browser rather than standalone.
- On OnePlus/ColorOS launcher permission dialogs, allow Chrome/browser to create the home-screen item, then return to confirm.

### Native prompt latency: show feedback before `prompt()`

On Android Chrome 138+ / Android 15 and some OEM builds, tapping the app's custom "Install now" button can pause for a moment before Chrome renders the PWA install sheet or before the launcher permission dialog appears. Avoid a dead tap feeling:

1. Immediately show an in-app loading/info toast such as "正在调起系统安装窗口".
2. Wait for the toast to paint before calling `BeforeInstallPromptEvent.prompt()` — use one or two `requestAnimationFrame` ticks.
3. Then call `prompt()` and await `userChoice`.
4. Dismiss the loading toast after `userChoice` resolves, and still do not mark installed until `appinstalled`/standalone readback.

Pattern:

```ts
const dismissPreparing = toast(t('pwa.install.preparing'), {
  tone: 'loading',
  body: t('pwa.install.preparingBody'),
});
await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
const outcome = await promptInstall();
dismissPreparing();
```

### Test coverage pattern

Add hook/component tests for:

- `userChoice: accepted` clears the one-shot prompt but does not mark installed until `appinstalled`.
- Harmony/Huawei UA with no `beforeinstallprompt` becomes a manual install guide after the timer.
- Android Chrome / OnePlus UA still prefers real `beforeinstallprompt` over the delayed manual guide.
- Manual guide CTA shows browser-menu steps and does not call `promptInstall()`.
- Browser install CTA shows the loading/preparing feedback before invoking `promptInstall()`.

## Display Mode Detection

```typescript
// Check if running as installed PWA
const isStandalone =
  window.matchMedia('(display-mode: standalone)').matches ||
  (window.navigator as any).standalone === true; // iOS Safari
```

## Recommended Install Prompt Timing

Don't prompt on first visit. Show install UI at:

1. **After login** — user has value commitment
2. **After first transaction** — high engagement signal
3. **3+ visits** — track via localStorage
4. **During idle** — `requestIdleCallback` to check canInstall

## Pitfalls

1. **Calling `e.preventDefault()` is required** — without it, Chrome shows its
   own mini-infobar and the event can't be reused for custom UI.

2. **`userChoice` is one-shot** — after calling `prompt()`, the event is consumed.
   Store the outcome but don't expect to reuse the same event.

3. **90-day cooldown after dismiss** — if user clicks "Not now" on Chrome's
   prompt, `beforeinstallprompt` won't fire again for 90 days on that origin.

4. **Capacitor/Cordova blocks Chrome prompt** — native app + same origin =
   no PWA prompt. Separate domains needed.

5. **`appinstalled` event** — listen for this to detect successful install:
   ```typescript
   window.addEventListener('appinstalled', () => {
     // Track analytics, hide install UI
   });
   ```

6. **Standalone mode detection on iOS** — `(window.navigator as any).standalone`
   is the only reliable check; `display-mode: standalone` media query may not
   work on older iOS versions.
