# PWA/mobile tab uIMax A+ closeout

Use when a mobile/PWA user reports missing bottom tabs, excessive blank space, inconsistent tab page coverage, safe-area issues, or explicitly demands uIMax A/A+ for tabbed product surfaces.

## Procedure

1. Reproduce the visual complaint on a real mobile viewport before fixing.
   - Capture every tab/panel, not only the default route.
   - Check whether the tab component is actually absent, hidden/offscreen, overlapped, stale-cached, or only missing from the current scroll position.
2. Make the tab acceptance measurable.
   - `navFixedVisible === true` or equivalent computed rect check.
   - active tab target visible and large enough for touch.
   - `contentOverlapNav === 0` for fixed bottom navigation.
   - `contentGapToNav` bounded so short pages cannot leave a large blank tail.
   - no horizontal overflow (`bodyScrollWidth` and `documentScrollWidth` <= viewport width).
   - min touch target height >= 40px, preferably 44px for primary controls.
   - console/pageerror lists empty.
3. Audit more than one mobile viewport.
   - Include a normal modern phone (e.g. Pixel 7 / ~412px width).
   - Include a narrow phone (e.g. iPhone SE / ~320px width).
   - A single screenshot size is not enough to claim mobile A+ for tab layout.
4. If using a local audit server, keep it loopback-only by default.
   - Bind ad-hoc screenshot/audit servers to `127.0.0.1` unless the user explicitly asked for LAN review.
   - If the audit needs a port, pass `MOBILE_WEB_PORT` or equivalent into both the server and the browser script; do not hardcode a shared port like 5173.
5. Avoid stale mobile shell false negatives.
   - If changing app-shell CSS/HTML/JS under a service worker, bump the SW/cache version or otherwise prove mobile clients will refresh.
6. Re-run the full product verification bundle after the UI-specific gate, then request an independent review before committing.

## Documentation and evidence rules

- Do not overclaim `100% coverage` unless the code actually enforces exactly 1.000 and the report shows it. Prefer threshold language such as `coverageRatio >= 0.94` when that is the gate.
- Docs must copy machine-report metrics exactly or avoid exact numbers. A+ means the gate passed its thresholds; it does not automatically mean perfect pixel or full-page coverage.
- Store machine-readable evidence (JSON) and screenshots for each tab/device pair. The human-facing report should point to those artifacts and identify known thresholds.

## Common failure modes

- Sticky bottom nav participates in flow and appears absent on real phones after content pushes/scrolls; fixed viewport chrome plus content reserve often matches user expectation better.
- Screenshot scripts that click tabs without resetting scroll can measure a scrolled state and hide top/bottom defects. Reset or intentionally account for scroll before each capture.
- Fixed bottom nav can create a false pass if screenshots show the nav but content is hidden behind it; always compute overlap.
- Short tabs can pass overflow checks while still looking empty; require bounded content gap to nav or fill-card behavior.
- Local preview or audit servers can accidentally expose the app directory on LAN. Use production allowlist servers for LAN preview, loopback-only simple servers for automated audits.
