# Android Chrome Pixel emulator PWA verification

Use this when the user asks to validate a PWA on a Google Pixel emulator (for example Pixel 8) rather than only from desktop/Lighthouse.

## Durable lessons

1. Prefer a real Android Chrome evidence ladder over Lighthouse-only checks.
   - Static headers: `/`, `/manifest.webmanifest`, `/sw.js`, `/registerSW.js`, icons.
   - Chrome CDP: `Page.getAppManifest` and `Page.getInstallabilityErrors`.
   - Page runtime: `beforeinstallprompt`, `navigator.serviceWorker.ready`, registrations, controller, display-mode.
   - Manual Chrome menu proof: menu -> `Add to Home screen` -> verify whether the sheet shows `Install` versus `Create shortcut`.

2. Pixel emulator creation may need explicit Java.
   - `avdmanager` can fail on macOS with “Unable to locate a Java Runtime” even when the emulator itself runs.
   - Use a known JDK for AVD creation, for example:
     `JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home` and prepend `$JAVA_HOME/bin`.
   - This is setup state, not a PWA bug.

3. AVD profile names and system properties differ.
   - `adb emu avd name` is the reliable way to confirm the running AVD (for example `Pixel_8_API_36`).
   - `ro.product.model` may still show generic emulator names such as `sdk_gphone64_arm64`; do not treat that as failure if the AVD name, screen size, density, SDK, and Chrome version match the target.

4. Chrome first-run dialogs can block CDP/menu verification.
   - After `pm clear com.android.chrome`, Chrome may show first-run screens such as `Use without an account`, notifications education, search-engine prompt, or translation bubble.
   - Dismiss these deliberately before judging PWA install UI.
   - Do not classify them as app/PWA failures.

5. Distinguish install from shortcut in the final report.
   - A valid PWA may show both `Install` and `Create shortcut` in the Android Chrome sheet.
   - `Create shortcut` often includes copy like `Shortcuts open in Chrome`; it is not standalone PWA proof.
   - Report that users should choose `Install`, and treat final standalone proof as a separate desktop-icon launch check if the user asks to complete installation.

## Minimal Pixel AVD creation pattern

```bash
export HOME=/Users/charles
export ANDROID_HOME=/opt/homebrew/share/android-commandlinetools
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"

PKG='system-images;android-36;google_apis_playstore;arm64-v8a'
AVD='Pixel_8_API_36'
printf 'no\n' | avdmanager create avd -n "$AVD" -k "$PKG" --device 'pixel_8' --force
```

If the device profile is present but the generated config needs alignment, check or patch:

```text
hw.device.name=pixel_8
hw.lcd.width=1080
hw.lcd.height=2400
hw.lcd.density=428
hw.ramSize=4096
```

Confirm the active emulator:

```bash
adb devices
adb emu avd name
adb shell wm size
adb shell wm density
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.sdk
adb shell dumpsys package com.android.chrome | grep -m1 versionName
```

## CDP probe shape

Use Chrome remote debugging through adb forwarding:

```bash
adb forward --remove-all
adb forward tcp:9333 localabstract:chrome_devtools_remote
curl http://127.0.0.1:9333/json/version
curl http://127.0.0.1:9333/json/list
```

Then connect Playwright over CDP and collect:

- `Page.getAppManifest` -> manifest URL and errors.
- `Page.getInstallabilityErrors` -> expect `installabilityErrors: []`.
- Inject listeners before navigation for `beforeinstallprompt` and `appinstalled`.
- Evaluate `navigator.serviceWorker.ready`, `getRegistrations()`, `navigator.serviceWorker.controller`, `matchMedia('(display-mode: standalone)')`, and `matchMedia('(display-mode: browser)')`.

## Reporting template

```text
Device: Pixel_8_API_36 / Android <version> / Chrome <version>
URL: <origin>
PWA installable: yes/no
CDP installabilityErrors: [] / <errors>
Manifest: URL + errors
Service Worker: ready/controller/registration scope
beforeinstallprompt: fired/not fired
Chrome menu: Add to Home screen -> Install present? Create shortcut present?
User instruction: choose Install, not Create shortcut, when both appear.
```
