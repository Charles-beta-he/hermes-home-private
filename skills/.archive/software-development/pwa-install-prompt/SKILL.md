---
name: pwa-install-prompt
description: "Use when control browser PWA install prompts — beforeinstallprompt, iOS fallback, custom install UI. Use when adding PWA install flow, diagnosing why install prompt doesn't appear, or building cross-platform install UX."
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

## Overview

Control browser PWA install prompts — beforeinstallprompt, iOS fallback, custom install UI. Use when adding PWA install flow, diagnosing why install prompt doesn't appear, or building cross-platform install UX. This skill is maintained as a `reviewer`-shaped contract: it should guide evidence-grounded review, audit, critique, certification, or quality-gate work without stealing adjacent workflows or relying on unstated assumptions.

## When to Use

Use this skill when the user's request matches `pwa-install-prompt` and requires evidence-grounded review, audit, critique, certification, or quality-gate work.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Control when and how the "Add to Home Screen" prompt appears. Chrome auto-fires
`beforeinstallprompt`; Safari iOS never does — both need explicit handling.


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
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

## iOS Safari Fallback

```typescript
const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
const showIOSHint = isIOS && !isStandalone;
```

Show a banner: "点击 Safari 底部分享按钮 → 添加到主屏幕"

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


## Common Pitfalls

1. Applying this skill mechanically after the user's goal has shifted. Re-check the current request before acting.
2. Treating a plan, stale memory, or prior report as proof of completion. Verify with fresh readback.
3. Ignoring neighboring skills or narrower workflows that better match the task. Prefer the most specific applicable skill.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Findings include evidence, severity/rubric calibration, and false-positive controls.
