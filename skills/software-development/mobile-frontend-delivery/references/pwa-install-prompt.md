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
| 2 | Valid manifest (name, icons 192+512, start_url, display) | Fetch manifest + CDP `Page.getAppManifest`; Lighthouse may no longer expose a PWA category in v13+ |
| 3 | Service Worker registered + activated | `navigator.serviceWorker.ready`, `getRegistrations()`, and expected scope |
| 4 | User not previously dismissed (90-day cooldown) | Can't verify programmatically |
| 5 | User has engagement (30s + 1 click minimum) | DevTools/CDP + real Chrome UI |
| 6 | Not in incognito | Check |
| 7 | No native app installed for same domain on Android | Capacitor/Cordova builds block PWA prompt |

**UVISA note**: `@capacitor/android` is in dependencies. If native Android app
is installed, Chrome can suppress the PWA install prompt for the same origin.

For deployed-origin verification, prefer the evidence ladder in
`references/android-chrome-pwa-installability-verification.md`: static headers,
CDP `Page.getInstallabilityErrors`, `beforeinstallprompt`, SW readiness, and
Android Chrome menu proof. Lighthouse v13 may reject `--only-categories=pwa`, so
CDP installability is the more durable check.

For Google Pixel emulator-specific verification (creating/switching Pixel 8 AVDs,
dismissing Chrome first-run dialogs, and proving the `Install` vs `Create shortcut`
split), use `references/android-chrome-pixel-emulator-pwa-verification.md`.

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

### Do not treat `accepted` or `appinstalled` alone as standalone installed

On Android Chrome, `BeforeInstallPromptEvent.userChoice` resolves when the browser prompt is accepted. It can happen before the launcher or OEM permission layer finishes creating the desktop icon/WebAPK. OnePlus/ColorOS may then show a system dialog like “Allow Chrome to create desktop shortcut?”. If the user denies it, or if the browser only supports shortcut creation, the site may not be installed as a standalone PWA.

Also do **not** treat `appinstalled` alone as proof of standalone/WebAPK success on Android OEM browsers. In OnePlus/ColorOS/HarmonyOS-like environments, Chromium can fire `appinstalled` after creating a launcher entry that still opens with browser chrome. Confirm final success only after a desktop-icon launch reports `matchMedia('(display-mode: standalone)').matches === true` (or iOS `navigator.standalone === true`). See `references/android-pwa-webapk-vs-shortcut.md` for the shortcut-vs-WebAPK diagnostic pattern.

Correct state model:

1. `beforeinstallprompt` captured → app can show a browser install affordance.
2. `prompt()` called and `userChoice === 'accepted'` → browser flow started/accepted only.
3. `appinstalled` fired → desktop entry / browser-reported install completed, but standalone is still unconfirmed on Android OEMs.
4. Later `display-mode: standalone` / `navigator.standalone` readback is true after opening from the icon → confirmed installed as standalone PWA.

Do not call `setIsInstalled(true)` only from `userChoice === 'accepted'` or only from `appinstalled` if the UI copy means “standalone app installed”. Track an intermediate state such as `desktopEntryCreated` and a final `standaloneVerified` state.
Do not call `setIsInstalled(true)` only from `userChoice === 'accepted'`. For OEM Android/Harmony cases, avoid treating `appinstalled` alone as proof of standalone mode; use copy like “桌面入口已创建，请从桌面图标打开完成验证” until a standalone-mode readback confirms it.

### Android Chrome readiness gate vs HarmonyOS / Huawei Browser fallback

For mainstream Android Chrome/Edge, do **not** show a proactive fallback such as “查看步骤” merely because a short timer elapsed. `beforeinstallprompt` is the browser readiness signal: keep the install UI silent until Chrome emits it, then show the custom install toast/banner with “立即安装”. This avoids teaching ordinary Chrome users a manual path while the browser may still be evaluating installability, engagement, cooldown, native-app suppression, or service-worker readiness.

HarmonyOS, Huawei Browser, ArkWeb, and OEM browsers may not emit `beforeinstallprompt` even with a valid manifest and service worker. Detect likely platform from UA markers such as `HarmonyOS`, `OpenHarmony`, `ArkWeb`, `HuaweiBrowser`, or `Huawei`, then after a short bounded wait (for example 1–2s) show manual browser-menu guidance if no native prompt arrived.

Manual guidance should be Harmony/OEM-specific, not iOS profile copy and not the default Android Chrome path:

- Open the Chrome/browser menu.
- Prefer the menu item explicitly labeled “安装 / Install” or “安装应用 / Install app”.
- Do **not** tell users to choose the separate menu item “创建快捷方式 / Create shortcut” when a real PWA install option is present; that creates a browser shortcut and may not produce standalone PWA behavior.
- On OnePlus/ColorOS, after the user chooses Chrome menu → “安装”, Android may still show a system permission dialog worded as “允许 Chrome 创建桌面快捷方式吗?” / “Allow Chrome to create a home-screen shortcut?”. Treat this as the launcher permission required to place the installed PWA icon, not as evidence that the user chose the wrong “Create shortcut” flow. The UX copy should say: choose “安装”, not “创建快捷方式”; if the subsequent system permission mentions creating a shortcut, allow it to complete installation.
- If only “添加到主屏幕 / 创建快捷方式” appears and no install option exists, explain it may open inside the browser rather than standalone.

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

### OnePlus / ColorOS accepted-but-not-standalone fallback

### OnePlus / ColorOS accepted-but-not-installed fallback

A recurring OnePlus/ColorOS failure mode is: Chrome's install sheet appears, the user taps "Install", the page shows "installing" for ~3 seconds, then no system permission dialog appears and no home-screen icon is created. Do not let the UI silently disappear after `userChoice === 'accepted'`.

A second recurring failure mode is: Chrome reports success and fires `appinstalled`, but the resulting home-screen entry opens with Chrome/browser UI instead of standalone. This is a shortcut/WebAPK distinction, not a manifest failure if Lighthouse and manifest/SW checks pass.

Recommended confirmation gate after `accepted`:

1. Await `appinstalled` and standalone readback separately for a short bounded window (about 3–4s).
2. Show full "安装完成" success only if `display-mode: standalone` / `navigator.standalone` is true.
3. If `appinstalled` fires but standalone is false, show neutral copy such as "桌面入口已创建，请从桌面图标打开以完成独立应用验证" and persist a pending verification flag for the next launch.
4. If no confirmation signal arrives, show a warning such as "未确认安装完成" with actionable copy: use browser menu → "安装应用 / 添加到主屏幕", then allow Chrome/browser to create the home-screen shortcut in the OnePlus/ColorOS permission dialog.
5. Include a "查看步骤" action that opens the Android manual-install guidance. This converts a silent failure into a recoverable path while preserving truthful install state.
5. Include a "查看步骤" action that opens the Android manual-install guidance. This converts a silent failure into a recoverable path while preserving truthful install state.

Minimal pattern:

```ts
function waitForInstallConfirmation(timeoutMs = 3500) {
  return new Promise<boolean>((resolve) => {
    if (isStandaloneMode()) return resolve(true);
    let settled = false;
    let timer: number | undefined;
    const finish = (installed: boolean) => {
      if (settled) return;
      settled = true;
      if (timer !== undefined) window.clearTimeout(timer);
      window.removeEventListener('appinstalled', onInstalled);
      resolve(installed || isStandaloneMode());
    };
    const onInstalled = () => finish(true);
    window.addEventListener('appinstalled', onInstalled, { once: true });
    timer = window.setTimeout(() => finish(false), timeoutMs);
  });
}

const outcome = await promptInstall();
if (outcome === 'accepted') {
  const installed = await waitForInstallConfirmation();
  if (installed) toast(t('pwa.install.accepted'), 'success');
  else toast(t('pwa.install.needsPermission'), {
    tone: 'warning',
    body: t('pwa.install.needsPermissionBody'),
    actionLabel: t('pwa.install.manualAction'),
    onAction: showAndroidManualSteps,
  });
}
```

### Test coverage pattern

Add hook/component tests for:

- `userChoice: accepted` clears the one-shot prompt but does not mark installed until `appinstalled`.
- Android Chrome should stay silent before `beforeinstallprompt`; after the event arrives, show the install CTA and call the stored event only from the user's click.
- Harmony/Huawei UA with no `beforeinstallprompt` becomes a manual install guide after the timer.
- Android Chrome / OnePlus UA stays silent after the timer when no `beforeinstallprompt` arrived.
- Android Chrome / OnePlus UA still prefers real `beforeinstallprompt` over any delayed manual guide, even if the event arrives after the timer.
- Manual guide CTA shows browser-menu steps and does not call `promptInstall()`.
- Browser install CTA shows the loading/preparing feedback before invoking `promptInstall()`.
- `userChoice: accepted` with no `appinstalled` / standalone confirmation within the bounded wait shows a OnePlus/ColorOS permission/manual-install fallback instead of a success toast or silent disappearance.
- `appinstalled` fires while `display-mode: standalone` remains false: UI should report “desktop entry created / launch from icon to verify,” not final standalone success; a later launch in Chrome with address bar should be classified as shortcut/browser entry.

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
