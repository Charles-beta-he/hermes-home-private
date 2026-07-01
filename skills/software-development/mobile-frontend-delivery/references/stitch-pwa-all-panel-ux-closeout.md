# Stitch/PWA all-panel UX closeout

Use when a Stitch-derived PWA already has product tabs/panels (for example overview, voice, diagnostics, safety) and the user asks for `项目级别`, `全盘推进`, `极限`, or says other pages also need the same treatment.

## Applicability

- Mobile/PWA product surface generated from Stitch or a similar design SSOT.
- Bottom navigation has multiple product panels inside one shell.
- One panel has been optimized but sibling panels still feel placeholder-like, diagnostic-heavy, or copy-only.

## Anti-conditions

- Do not use this as authority to push/deploy/publish.
- Do not claim pixel-perfect parity unless a dedicated per-screen pixel/bbox pass exists.
- Do not expose internal/debug terms as default user copy; keep them in diagnostics or tests.

## Pattern

1. Inventory every nav target, not only the active/overview panel.
2. For each panel, define the user job in one sentence:
   - Overview: start and see next action.
   - Voice: hands-free control and privacy boundary.
   - Diagnostics: conclusion first, technical details second.
   - Safety: stop conditions and explicit acknowledgement.
3. Replace thin placeholder surfaces with panel-specific product hierarchy:
   - A compact hero/status summary.
   - One or two primary actions.
   - Short cards/checklists instead of long paragraphs.
   - A truthful boundary statement.
4. If the same runtime state appears in more than one panel, update all matching `data-field` nodes. Avoid a `Map(data-field -> single node)` implementation; duplicate data-fields otherwise desynchronize.
5. Add/extend tests for each panel, not only overview:
   - navigation reaches the panel;
   - panel identity heading is visible;
   - key status/checklist/command copy is present;
   - runtime state updates in duplicated summary fields;
   - product UI remains free of mock/demo/debug leakage.
6. Update PRD/workflow/design-gate required data-fields and design tokens to match the new copy.
7. Generate screenshots for every panel and run the full gate bundle before reporting completion.
8. If the user says `项目级别`, `全盘推进`, or `推进至极限`, productize the screenshot step as a reusable project gate instead of leaving it as a one-off script:
   - add a committed script (for example `apps/mobile-web/scripts/capture-product-panels.mjs`) that launches/captures every panel with deterministic local fixtures;
   - add a Makefile target such as `make product-screenshots`;
   - assert screenshot generation plus layout health (`bodyScrollWidth <= innerWidth`, `documentElement.scrollWidth <= innerWidth`, bottom navigation visible/bounded) for every panel;
   - add the target to workflow config/gates/tests/README/PRD so future changes cannot skip the panel evidence loop.
9. If the user then approves continuing beyond product-panel closure toward `1:1` or full visual parity, switch to the full-resolution parity loop in `references/stitch-pwa-fullres-visual-parity.md`: freeze Stitch source/HTML, add a tracked non-secret manifest, produce side-by-side quantified metrics, and preserve runtime/product semantics rather than flattening the PWA into a static mock.

## Verification bundle

At minimum:

```bash
make product-screenshots
make vision-inventory
make vision-smoke
make pixel-diff
make verify
make ui-smoke
```

When `make product-screenshots` is not yet present, create it before claiming project-level UI/UX closure. If pixel-diff remains a wide drift/readiness gate, label it honestly and keep a separate 1:1 layout pass as the next boundary.
