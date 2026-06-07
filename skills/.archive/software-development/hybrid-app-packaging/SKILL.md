---
name: hybrid-app-packaging
description: "Use when packaging an existing Web SPA (React/Vue/Angular) as a native mobile app via Capacitor, Cordova, or similar WebView-based frameworks. Covers decision framework (Capacitor vs React Native vs PWA), code reuse analysis, known pitfalls (side-swipe exit, iOS WKWebView quirks), and security layer bridging."
triggers:
  - "package web app as mobile"
  - "Capacitor setup"
  - "wrap SPA in native shell"
  - "web to mobile migration"
  - "React Native vs Capacitor"
  - "PWA to APK"
  - "side swipe exits app"
  - "WebView back button"
---

# Hybrid App Packaging — WebView-based Native Wrapping

## Overview

Use when packaging an existing Web SPA (React/Vue/Angular) as a native mobile app via Capacitor, Cordova, or similar WebView-based frameworks. Covers decision framework (Capacitor vs React Native vs PWA), code reuse analysis, known pitfalls (side-swipe exit, iOS WKWebView quirks), and security layer bridging. This skill is maintained as a `wrapper`-shaped contract: it should guide external tools, APIs, CLIs, platforms, or other side-effecting capability surfaces without stealing adjacent workflows or relying on unstated assumptions.

## When to Use

Use this skill when the user's request matches `hybrid-app-packaging` and requires external tools, APIs, CLIs, platforms, or other side-effecting capability surfaces.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

When you have an existing Web SPA and need native mobile apps (APK/AAB/IPA), WebView-based wrappers like Capacitor are the fastest path. This skill covers the decision framework, known pitfalls, and implementation patterns.

## Decision Framework: Capacitor vs React Native vs PWA

### When to choose Capacitor (WebView wrapper)
- Existing SPA is clean, well-structured (service/store/screen separation)
- Need to ship fast (days, not months)
- Team is Web-focused, no RN experience
- App doesn't need heavy native animations or game-like performance
- Financial/utility apps where content > motion

### When to choose React Native
- Need truly native UI feel (fluid gestures, native scroll physics)
- Heavy use of native modules (Bluetooth, NFC, camera streaming)
- Long-term investment, dedicated mobile team
- App is animation/performance critical

### When PWA alone suffices
- No App Store distribution needed
- No push notifications or biometrics required
- Budget/time extremely constrained

### Quantitative comparison (from UVISA 58K-line React SPA analysis)

| Metric              | Capacitor  | React Native |
|---------------------|------------|--------------|
| Dev cycle           | 2-4 weeks  | 3-5 months   |
| Code changes        | ~2K lines  | ~40K lines   |
| Team size           | 1 person   | 2-3 people   |
| Difficulty (1-10)   | 2.9        | 7.1          |
| Feature coverage    | 85-95%     | 100%         |
| Regression risk     | Very low   | High         |

## Code Reuse Rate Analysis Methodology

When estimating migration effort, decompose the codebase into layers:

### Layer classification

| Layer        | Typical reuse | Notes |
|-------------|---------------|-------|
| types/      | 100%          | Pure TS interfaces |
| stores/     | 95%           | Zustand/Pinia pure state; replace localStorage→AsyncStorage |
| services/   | 90%           | API calls + business orchestration; minor adapter needed |
| data/       | 85%           | Pure data dicts, configs; some use localStorage |
| hooks/      | 75%           | Business logic hooks; some use Web APIs |
| lib/        | 65%           | Utilities, crypto, validators; some browser-dependent |
| components/ | 0%            | DOM components → must rewrite for RN |
| screens/    | 0-15%         | UI + embedded logic; need extraction |

### Tier system for migration planning

1. **Direct reuse** (copy as-is): types, pure stores, pure services, data dicts
2. **Small adaptation** (change 3-10 lines/file): localStorage→AsyncStorage, browser API→RN equivalent
3. **Extractable** (refactor then reuse): Business logic embedded in screens → extract to hooks/utils
4. **Must rewrite**: All UI components (components/, screen JSX, routing, styling)

For a typical 58K-line React SPA:
- Direct reuse: ~11%
- Small adaptation: ~4%
- Extractable: ~14%
- Must rewrite: ~53%
- Tests (not migrated): ~18%

## Capacitor Pitfalls

### PITFALL: Side-swipe / back button causes app exit

**Symptom**: On secondary pages, swiping back (iOS) or pressing system back (Android) exits the app instead of navigating to the previous screen.

**Root cause**: WebView's `history.back()` and the system's "back" have different semantics. The system back triggers at the Activity/ViewController level. When WebView's history stack is empty, the system thinks the app wants to exit.

```
Native navigation stack:
  Home ← Card ← Topup    (system back = pop ViewController)

WebView (SPA) navigation:
  Single WebView, URL history: /home → /card → /topup
  System back → history.back() → if stack empty → app exits
```

**Fix**: Intercept the back button at the Capacitor level and route it through your SPA router:

```typescript
// main.tsx or App.tsx
import { App as CapApp } from '@capacitor/app';
import { Capacitor } from '@capacitor/core';
import { useNavigate, useLocation } from 'react-router-dom';

// In your root component or a hook:
useEffect(() => {
  if (!Capacitor.isNativePlatform()) return;

  const listener = CapApp.addListener('backButton', ({ canGoBack }) => {
    // Check if current route is a root/tab route
    if (isRootRoute(location.pathname)) {
      // On root route: optionally show exit confirmation
      CapApp.exitApp();
    } else {
      // On sub-route: use react-router to go back
      navigate(-1);
    }
  });

  return () => { listener.then(l => l.remove()); };
}, [location.pathname]);
```

**Pre-existing hooks**: Check if the Web project already has a `useSwipeBack` hook — it can be extended for Capacitor rather than writing from scratch.

### PITFALL: iOS swipe-back gesture conflicts with WKWebView

**Symptom**: iOS system swipe-back gesture fights with WKWebView's own back-forward navigation gesture, causing glitchy behavior.

**Fix**: Disable WKWebView's navigation gesture in `capacitor.config.ts` or `AppDelegate.swift`:

```typescript
// capacitor.config.ts
const config: CapacitorConfig = {
  ios: {
    preferredContentMode: 'mobile',
  }
};
```

```swift
// AppDelegate.swift
webView.allowsBackForwardNavigationGestures = false
```

### PITFALL: iOS App Store review 4.2 rejection

Apple's 4.2 guideline: "App should include features, content, and UI that go beyond a simple repackaged website."

**Pass criteria**: App must use at least 2-3 native capabilities (push notifications, biometrics, camera, file system, etc.). Financial apps with security requirements easily pass.

### PITFALL: Security capabilities gap

WebView cannot access: system secure keyboard, Jailbreak/Root detection, SSL Pinning, hardware Keystore/TEE.

**Solutions**:
1. Write custom Capacitor native plugins (1-2K lines Java/Swift)
2. Integrate third-party security SDKs (梆梆/几维/娜迦)
3. Both approaches are similar effort for Capacitor and RN

### PITFALL: iOS WKWebView performance

WKWebView on iOS is generally faster than Android WebView. iOS experience is often *better* than Android, not worse. Don't assume iOS is the harder platform.

## iOS Compatibility Matrix

| iOS Version | Capacitor 5+ Support |
|-------------|---------------------|
| iOS 17      | ✅ Full (latest)     |
| iOS 16      | ✅ Full              |
| iOS 15      | ✅ Full              |
| iOS 14      | ✅ (some new APIs unavailable) |
| iOS 13      | ⚠️ Minimum recommended |
| iOS 12      | ❌ Not supported     |

Build requirements: Xcode 15+, CocoaPods, Apple Developer account ($99/yr), minimum deployment target iOS 13.0.

## Feature Coverage for Financial Apps

### Fully covered (Capacitor native plugins)
Push notifications, biometrics, camera, local storage, filesystem, clipboard, device info, network status, keyboard control, status bar, screen orientation, app lifecycle, deep links, local notifications, haptics, geolocation, in-app browser.

### Partially covered (needs extra work)
NFC reading (Android yes, iOS limited), background tasks, custom secure keyboard, system share sheet.

### Cannot cover (needs native plugins or SDKs)
System-level secure keyboard, Jailbreak/Root detection, SSL Pinning, hardware Keystore/TEE, Widgets, App Clips.

**Overall financial app coverage: 85-95%** (remaining 5-15% is security layer, solvable with native plugins or third-party SDKs).

## Common Pitfalls

1. Reporting a tool/API mutation as complete without reading back target state.
2. Skipping prerequisite checks and assuming the environment already matches the workflow.
3. Reporting success before reading back the actual outputs, files, or external side effects.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] For mutations or external-system actions, command success was paired with target-state read-back.
