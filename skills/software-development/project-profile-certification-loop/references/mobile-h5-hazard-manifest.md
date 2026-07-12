# Mobile H5 Hazard Manifest

Scope: reusable project-profile/SSOT manifest for mobile web, PWA, and WebView projects. Use it to make autonomous triggers capability-based instead of hardcoded to one project or phrase.

## Purpose

A project should expose reusable hazard tags in its profile/SSOT. The agent/router can then load the right workflows when a task touches a capability surface such as keyboard focus, scroll ownership, safe areas, tab bars, API-backed blank sections, or WebView return/resume — without relying on hardcoded project names or exact user wording.

## Recommended profile shape

```json
{
  "workflow_capability_tags": [
    "mobile-h5",
    "pwa-or-webview",
    "api-backed-ui",
    "bottom-tab-shell",
    "keyboard-focus-risk",
    "scroll-owner-risk",
    "safe-area-risk",
    "route-guard-risk"
  ],
  "hazard_inventory": {
    "keyboard_focus": {
      "applies_to": ["forms", "amount inputs", "auth screens", "composer/chat screens"],
      "default_gate": "classify page model before editing",
      "evidence": ["focused screenshots", "visualViewport/geometry readback", "CTA visibility"],
      "anti_patterns": ["global scrollBy", "global keyboard reserve", "moving fixed CTA unexpectedly"]
    },
    "scroll_owner": {
      "applies_to": ["nested mobile pages", "fixed header/bottom tab layouts", "long forms"],
      "default_gate": "identify the owning scroll container and preserve route-level shell behavior",
      "evidence": ["375/390/414 viewport geometry", "top/bottom reachability", "no hidden CTA/tabbar"]
    },
    "safe_area": {
      "applies_to": ["bottom navigation", "fixed CTA", "headers", "PWA/WebView"],
      "default_gate": "verify env(safe-area-inset-*) behavior and fallback geometry",
      "evidence": ["bottom strip screenshot", "nav rect within viewport", "home-indicator gap behavior"]
    },
    "api_backed_blank": {
      "applies_to": ["home sections", "lists", "cards", "ranking/market data"],
      "default_gate": "prove exact opened URL uses the expected API base/proxy and renders loading/error/empty/data states",
      "evidence": ["network/API readback", "DOM text markers", "mobile screenshot"]
    }
  }
}
```

## Autonomous routing rule

Do not route by hardcoded strings such as one project name or one exact command phrase. Route by the intersection of:

1. project profile capability tags;
2. current task intent and touched files/routes/components;
3. source/evidence class: PRD, native reference, current implementation, browser/runtime proof;
4. side-effect authority boundary.

Example:

- If profile has `mobile-h5` + `keyboard-focus-risk`, and the task touches inputs/forms/CTA/focus/viewport, load `mobile-frontend-delivery` and the keyboard/scroll-owner references.
- If profile has `api-backed-ui`, and a page appears blank or data-backed, load API fallback/proxy evidence workflows.
- If profile has `bottom-tab-shell` or `safe-area-risk`, run bottom-tab/safe-area geometry evidence before UI closure.

## Project-specific landing

The manifest in a skill is only the class-level template. Each project should store its actual hazard inventory in its project profile/SSOT, with local route names and evidence paths there — not in this reusable skill.

## Verification checklist

- [ ] Profile has capability tags, not only prose status.
- [ ] Hazards name triggers, gates, evidence, and anti-patterns.
- [ ] Project-specific routes and evidence paths stay in the project profile/SSOT.
- [ ] Router decisions can be explained from tags + touched surface + authority boundary.
- [ ] UI completion claims cite runtime/screenshot/geometry evidence for each active hazard.
