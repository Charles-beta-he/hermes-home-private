# Stitch/PWA full-resolution visual parity pass

Use when a Stitch-derived PWA/mobile surface has already reached product-level UX closure and the user approves continuing toward `1:1`, `极限像素级`, or `全盘推进` visual parity.

## Applicability

- Stitch MCP can read the project/screen and expose screenshot/html download URLs.
- The PWA already has productized runtime surfaces, tests, and screenshot gates.
- The goal is to reduce visual drift without deleting runtime behavior, safety gates, readiness/status surfaces, or product panels.

## Anti-conditions

- Do not claim pixel-perfect parity from a wide drift/readiness threshold.
- Do not replace a runtime product surface with a static screenshot unless the user explicitly chooses a separate static parity route.
- Do not commit secret-bearing SDK/API config or raw credentials. Persist only IDs, local cache paths, and non-secret metadata.
- Do not collapse multi-panel product UX into a single long Stitch mock if that removes reachable product surfaces.

## Procedure

1. Freeze the target source.
   - Read the Stitch screen via MCP (`get_screen`).
   - Persist a tracked manifest such as `configs/stitch.screen.json` with project ID, screen ID, dimensions, asset names, and local cache paths.
   - Download the high-resolution screenshot deliberately; for Google image URLs append `=s0` when needed.
   - Cache the Stitch HTML locally when available, but treat it as design evidence, not product logic.

2. Keep semantic boundaries explicit.
   - Stitch target is the visual SSOT.
   - PWA runtime remains the authority for real adapter/readiness, safety, voice, diagnostics, and product-panel navigation.
   - Record known semantic deltas in docs/PRD instead of silently removing product behavior for visual similarity.

3. Productize the comparison.
   - Add a script such as `scripts/visual_parity_report.py` that loads the full-resolution Stitch target and current PWA screenshot.
   - Scale the PWA screenshot to the Stitch width.
   - Compute `changedPixelRatio`, `meanRgbDelta`, compared size, and write a side-by-side proof image.
   - Return JSON and label the claim honestly: quantified side-by-side evidence, not pixel-perfect acceptance.

4. Add a Makefile target and workflow hooks.
   - `make visual-parity` should run the report script.
   - Add the target to workflow config, workflow gate missing-target checks, tests, README, and PRD/workflow docs.

5. Iterate layout only in reversible slices.
   - First reduce major anchor drift: title/header, mode card, camera region, action buttons, advice, safety/voice/diagnostics order.
   - Preserve runtime `data-field` bindings and tests.
   - After each slice, regenerate product screenshots and rerun visual parity metrics.

6. Verify before closeout.

```bash
make product-screenshots
make visual-parity
make pixel-diff
make verify
make ui-smoke
```

If real adapter availability is part of the UI claim, include:

```bash
make vision-inventory
make vision-smoke
```

## Evidence to report

- Tracked manifest path, e.g. `configs/stitch.screen.json`.
- Cached full-resolution screenshot path and dimensions.
- Side-by-side proof path.
- Quantified metrics: target size, candidate size, scaled size, changed pixel ratio, mean RGB delta.
- Explicit remaining boundary: pixel-perfect parity not claimed unless thresholds are tight and element-level anchors pass.

## Pitfalls

- Low-resolution thumbnails hide real layout drift. Always verify the full-resolution target dimensions.
- A single full-frame diff number can worsen after a product-preserving change. Pair it with anchor/order review and screenshots.
- Productized PWA panels often intentionally differ from a single long Stitch screen. Keep those as documented semantic deltas rather than regressions.
- Do not let `state/artifacts` become the only source of truth for target identity; keep tracked non-secret manifest/config in repo.
