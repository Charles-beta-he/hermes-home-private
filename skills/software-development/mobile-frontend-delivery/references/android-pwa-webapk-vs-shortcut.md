# Android PWA WebAPK vs Launcher Shortcut

Use this when Android / OnePlus / ColorOS / HarmonyOS users report that PWA "installation succeeded" but the result behaves like a browser shortcut rather than an installed standalone app.

## Key distinction

Do not equate Chromium install events with confirmed standalone PWA installation:

1. `beforeinstallprompt` fired: the browser considers the page installable enough to show an install prompt.
2. `BeforeInstallPromptEvent.userChoice.outcome === 'accepted'`: the user accepted the browser prompt only.
3. `appinstalled` fired: Chromium reports that installation / home-screen entry creation completed. On some Android OEM environments this can still result in a launcher shortcut rather than a true WebAPK / standalone PWA.
4. `matchMedia('(display-mode: standalone)').matches === true` after launching from the desktop icon: confirmed standalone PWA.

Treat step 4 as the success gate for "installed as app". Treat step 3 as "desktop entry created / install flow accepted" unless standalone is also observed.

## Diagnostic pattern

Collect these fields before and after install, then again after the user opens the desktop icon:

- `location.href`
- `navigator.userAgent`
- `navigator.serviceWorker.controller`
- manifest fetch status/content type/body fields: `id`, `name`, `short_name`, `start_url`, `scope`, `display`, `display_override`, `icons`
- `beforeinstallprompt` fired and `platforms`
- `prompt()` returned
- `userChoice` outcome/platform
- `appinstalled` fired
- `matchMedia('(display-mode: standalone)').matches`
- `navigator.standalone` for iOS only
- whether browser address bar is visible in a follow-up screen recording

Run Lighthouse PWA installability as a separate server-side sanity check. A passing manifest/SW audit proves the site is installable, but does not prove the target device created a WebAPK.

## Common finding

If logs show all of the following:

- manifest and service worker are valid
- `beforeinstallprompt` fired
- `userChoice.outcome === 'accepted'`
- `appinstalled` fired
- but `displayModeStandalone === false`
- and the page still displays Chrome/browser address bar

then the most accurate conclusion is: the browser/OEM reported successful entry creation, but standalone mode is not confirmed. On OnePlus/ColorOS/HarmonyOS-like environments this often means the created item behaves as a launcher shortcut.

## Android Chrome menu distinction

Modern Android Chrome may route both installable PWAs and ordinary shortcuts through the menu item named `Add to Home screen`. The decisive screen is the next bottom sheet:

- `Install` means Chrome recognizes the origin as installable and is offering the PWA/WebAPK path.
- `Create shortcut` with wording such as `Shortcuts open in Chrome` means a plain launcher shortcut that opens in Chrome.

If both choices appear, tell users to choose `Install` and explicitly avoid `Create shortcut`. This is stronger field evidence than the menu label alone, because the menu label can still say “Add to Home screen” for a valid PWA.

For a full deployed-origin verification recipe, including CDP `Page.getInstallabilityErrors`, see `references/android-chrome-pwa-installability-verification.md`.

## Product-state model

Use explicit states instead of a boolean `isInstalled`:

- `promptAvailable`
- `promptAccepted`
- `desktopEntryCreated` / `appinstalledReceived`
- `standaloneVerified`
- `shortcutOnlySuspected`

Recommended copy:

- After `accepted` + `appinstalled` but no standalone readback: "桌面入口已创建。请从桌面图标打开以完成独立应用验证。"
- On next launch with `display-mode: standalone`: "已进入独立应用模式。"
- On next launch still showing browser chrome / `display-mode` false: "当前为浏览器快捷方式，不是独立应用模式；该设备/浏览器可能不支持 WebAPK standalone。"

## Implementation pitfall

Avoid code like:

```ts
window.addEventListener('appinstalled', () => setIsInstalled(true));
```

and avoid resolving install confirmation as `appinstalled || standalone` if the UI wording says "installed app". Instead:

- record `appinstalled` as an intermediate signal;
- only set `isStandaloneInstalled` from standalone readback;
- persist a post-install pending check so the next desktop-icon launch can verify final mode.
