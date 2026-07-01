# Stitch SDK → mobile/RN design sync

Use this when Stitch SDK is the authorized path for reading design artifacts and synchronizing mobile/RN/PWA screens. Treat Stitch MCP as deprecated for this workflow unless the user explicitly re-authorizes it for a legacy task.

## Applicability

- Mobile/RN/PWA project already uses Stitch designs as upstream visual/product SSOT.
- A local `@google/stitch-sdk` integration or API key exists in a separate trusted config location.
- The task is to pull/read Stitch artifacts and implement reachable mobile functions, not to mutate Stitch cloud designs.
- For one-off design asset generation (for example PWA startup images), the Stitch SDK should run from the Hermes/module-library side when available; do not install Stitch SDK or secret-handling scripts into the target app repo unless that repo intentionally owns the integration.

Anti-conditions:

- Do not save Stitch/API keys in the app repo or skill. Read from a local secret file or environment only; manifests must redact secrets.
- Do not claim “latest” solely from one `list_screens` result if the SDK response lacks reliable `updateTime` per screen or returns unstable ordering.
- Do not treat downloaded HTML/CSS as production RN code. Extract product surfaces, controls, copy, tokens, and interaction intent; reimplement in native/RN components with existing app boundaries.

## Procedure

1. Confirm SDK version from npm and installed repo/module library; install the current/latest compatible version into the target project only if the target project itself must own the integration.
2. Before touching the app repo, check for an existing Hermes/module-library Stitch SDK bridge and local secret config (for example `~/.rowboat/config/stitch.json` or `STITCH_API_KEY`). Prefer that bridge for design generation/export so the product repo receives only static assets and code changes.
3. Add a small sync script rather than ad-hoc shell snippets:
   - reads API key from local secret config or `STITCH_API_KEY`;
   - instantiates `StitchToolClient`;
   - lists projects/screens;
   - downloads selected screen HTML/image via `Screen.getHtml()` / `Screen.getImage()` or raw artifact URLs;
   - writes a redacted manifest and never prints the key.
3. Prefer explicit `projectId` / `screenId` when the user says a specific design changed. If scanning automatically, record that ordering may be unstable and sync multiple related candidate screens rather than hard-coding a false latest.
4. Analyze the image and HTML together:
   - image gives layout/visual hierarchy;
   - HTML gives exact copy, theme tokens, button IDs, and micro-interaction intent.
5. Fill every visible control with a reachable app function:
   - top/header controls route to status/share/profile surfaces;
   - bottom nav routes to current product surfaces;
   - cards/drilldowns open detail views;
   - export/add/restore controls perform safe local actions or show explicit queued/toast state.
6. Preserve product authority boundaries. For mobile companions, keep canonical facts server/Gateway-owned; mobile can show projections, local drafts, handoff queues, settings, and readbacks.
7. Add regression tests for the visible route/function contract, not just rendering:
   - nav button opens expected surface title;
   - list item drills into detail;
   - export/add/restore buttons exist and produce safe local state.
8. Verify:
   - SDK dry-run can list/read screens with redacted output;
   - no exact secret prefix appears in source/artifacts outside dependency folders;
   - native lint/Jest pass;
   - workspace tests/build pass.
9. Record the synced screens and caveats in project profile/ledger rather than global memory.

## Pitfalls

- SDK/MCP screen ordering may fluctuate when screen-level timestamps are absent. Treat this as a selection ambiguity, not a tool failure. Use explicit screen IDs or sync a small set of related candidate screens.
- A screen that looks like a settings/list/detail surface should not replace the avatar home screen unless the user explicitly asks for redesign. Integrate it as a reachable surface behind the relevant nav/control.
- Generated “export to Figma” or “restore defaults” buttons should be safe local stubs or gated actions unless cloud writes are explicitly authorized.
- Searching for a short API-key prefix can false-positive in minified dependencies. Exclude dependency/vendor directories and search an exact enough prefix; report only that no secret is present, never print the key.
