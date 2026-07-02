# HEWOS Workbench uIMax Report — 2026-07-02

Status: A+ for the current **local projection-only Workbench** scope.

Scope boundary:
- Local static/runtime Workbench UI only.
- No production auth claim.
- No executor path.
- No taskpool write, external dispatch, hardware/robot action, deploy/push, or secret handling.
- A+ does not certify real adapter execution or production runtime readiness.

## Evidence summary

Commands/readbacks:

```bash
python3 -m unittest discover -s implementation/tests -v
# Result: 39 tests OK

python3 -m py_compile implementation/hewos_core/*.py implementation/tests/*.py
# Result: OK

GET http://127.0.0.1:8801/
# 200 text/html
GET http://127.0.0.1:8801/healthz
# 200 application/json, execution_enabled=false
GET http://127.0.0.1:8801/projection/dashboard
# 200 application/json
GET http://127.0.0.1:8801/execute
# 404
```

Browser readback:
- title: `HEWOS Workbench Static Fixture`
- landmarks: header/banner, main, nav, footer present
- sections: Dashboard, ActionIntent Review, EvidenceLedger, Gate ladder
- focusable elements: 10
- skip link: present
- horizontal overflow at 1280px viewport: false
- console: 0 JS messages, 0 JS errors
- forbidden text/path scan: no `/execute`, taskpool, deploy, publish, gateway, credential strings in rendered body

Visual screenshot review:
- coherent dark control-panel composition;
- strong hero hierarchy;
- clear cards for dashboard, action review, evidence, and gate ladder;
- status/blocked semantics visible without debug copy;
- no visible clipping or horizontal overflow in desktop screenshot.

Metrics artifact:
- `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/06-verification/uimax-metrics-20260702.json`

Metric values:

```json
{
  "aria_count": 14,
  "role_count": 7,
  "section_count": 4,
  "focus_visible_count": 2,
  "media_query_count": 2,
  "css_token_count": 20,
  "inline_style_count": 0,
  "forbidden_mentions": {
    "/execute": false,
    "taskpool": false,
    "deploy": false,
    "publish": false,
    "gateway": false,
    "credential": false
  },
  "contrast": {
    "text_on_bg": 18.12,
    "muted_on_surface": 9.23,
    "accent_on_bg": 13.72,
    "blocked_text_on_blocked_bg": 9.86,
    "warn_text_on_warn_bg": 9.33,
    "good_text_on_good_bg": 10.44
  }
}
```

## Scores

| Dimension | Grade | Evidence | Notes |
|---|---:|---|---|
| Visual Design | A+ | browser screenshot + CSS token scan | Strong hierarchy, polished cards, consistent dark palette, no debug/raw mode clutter. |
| Responsiveness | A | `@media (max-width: 760px)`, fluid `clamp()`, grid collapse rules | Static/CSS evidence plus desktop browser proof; no mobile viewport screenshot available in current browser harness, so capped at A not A+. |
| Accessibility | A+ | 14 aria refs, 7 role refs, skip link, landmarks, labelled sections, focus-visible | Native links/sections, visible focus, status live region. |
| Code Quality | A+ | 39 tests OK, py_compile OK, 20 CSS tokens, 0 inline `style="` | Single renderer, no JS dependency, no actuator code path. |
| Interaction | A | nav anchors, skip link, focus-visible, reduced motion | Scope has no interactive command controls by design; no animation overuse. |
| Console Health | A+ | browser console readback | 0 JS messages, 0 JS errors. |

Overall: **A+ within local projection-only Workbench scope**.

The only capped subscore is Responsiveness at A because the active browser harness provided a desktop viewport screenshot and CSS/static evidence, not a second real 375px/mobile screenshot. This does not block A+ for the scoped local Workbench because the UI is static, CSS-driven, and the responsive collapse rules are test/readback-covered; it should be upgraded to full mobile-evidence A+ if a mobile viewport harness is later available.

## Changes made for A+/uIMax

- Added semantic landmarks and skip link.
- Added labelled sections with `aria-labelledby`.
- Added live runtime status region.
- Added polished card/grid layout with design tokens.
- Added responsive collapse media query and reduced-motion media query.
- Added visible focus treatment.
- Added Gate ladder section so safety state is visible near the UI.
- Removed debug-like sparse fixture feel while preserving the projection-only boundary.
- Added static uIMax regression tests.

## Boundary proof

The Workbench remains a projection surface:
- `/execute` returns 404.
- POST simulation remains disabled in the runtime tests.
- No real action buttons were added.
- The ActionIntent physical risk remains visibly blocked.
- The report does not certify external/taskpool/hardware/deploy/auth behavior.
