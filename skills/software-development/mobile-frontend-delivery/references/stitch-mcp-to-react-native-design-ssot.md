# Stitch MCP as React Native design SSOT

Use when a mobile/RN implementation should be driven from a Google Stitch project rather than browser screenshots or Figma export.

## Applicability

- User has a Stitch project ID or Stitch MCP is configured.
- Goal is RN/PWA/mobile visual parity from a Stitch-generated mobile screen.
- Figma export/token flow is unavailable, unnecessary, or lower priority than direct Stitch evidence.

Anti-conditions:

- Do not treat Stitch HTML/PNG as permission to copy third-party proprietary assets or unique logos.
- Do not let Stitch visual direction override product logic, safety boundaries, or existing feature reachability.
- Do not store exposed API keys in public docs or logs.

## MCP connection pattern

Hermes native MCP config is YAML. A Codex-style TOML snippet such as:

```toml
[mcp_servers.stitch]
url = "https://stitch.googleapis.com/mcp"

[mcp_servers.stitch.http_headers]
"X-Goog-Api-Key" = "..."
```

maps to Hermes as:

```yaml
mcp_servers:
  stitch:
    url: "https://stitch.googleapis.com/mcp"
    headers:
      X-Goog-Api-Key: "..."
    timeout: 180
    connect_timeout: 60
    sampling:
      enabled: false
```

Use `headers`, not `http_headers`. After config reload/restart, verify:

```bash
hermes mcp list
hermes mcp test stitch
hermes mcp doctor stitch
```

Successful smoke evidence should show the server enabled, connected, and Stitch tools such as `get_project`, `list_screens`, `get_screen`, `generate_screen_from_text`, `edit_screens`, and design-system tools.

If the CLI test sees tools but the current chat does not expose `mcp_stitch_*`, the session likely needs a Hermes reload/restart; report that as a tool-injection boundary rather than continuing browser-only.

## Design evidence workflow

1. Read project metadata via `get_project`.
2. List screens via `list_screens`.
3. Pick one primary mobile screen before coding; record screen ID, title, dimensions, screenshot URL, and HTML URL.
4. Pull local immutable evidence: Stitch PNG screenshot and HTML source under the project references directory.
5. Extract implementation anchors from HTML/PNG:
   - page structure and safe-area model
   - color tokens
   - typography tokens
   - exact user-visible copy
   - component order and interactive affordances
   - animation notes such as Three.js/particle parameters
6. Implement RN parity without dropping existing product actions: every visible control should still route to an equivalent reachable product surface.
7. Verify with Jest/lint, iOS simulator build, and a screenshot; compare against Stitch and record remaining deltas.

## RN particle/orb implementation notes

For Stitch ionic/particle cores, a reversible first slice can use Reanimated native Views before moving to Skia/WebGL:

- Use many small deterministic particles rather than a few large dots.
- Drive pulse/rotation/drift via `useSharedValue`, `useAnimatedStyle`, `withTiming`, `withSequence`, `withRepeat`, and `withDelay`.
- Keep voice/listening state as an amplitude/brightness modifier, not a separate product mode.
- Preserve unified UX copy; do not expose local/offline/online/internal routing terms on the main screen.

Skia/WebGL remains the higher-fidelity path when the reference requires thousands of points, additive blending, or true 3D rotation.

## Verification checklist

- [ ] `mcp_stitch_get_project`/`list_screens`/`get_screen` or CLI `hermes mcp test stitch` proves Stitch access.
- [ ] Local HTML + PNG evidence is saved under `references/`.
- [ ] RN main screen preserves product navigation and safety gates.
- [ ] User-facing copy avoids internal implementation lanes unless explicitly requested.
- [ ] Tests/lint/build pass.
- [ ] Simulator screenshot path is recorded.
- [ ] Remaining visual deltas are specific: font asset, icon asset, particle renderer, safe-area/device-frame difference, etc.
