# Stitch design automation gate

Use when a mobile/PWA UI has a Stitch design source or the user asks to land Stitch/design into the automation chain, not just generate a design.

## Applicability

- A PWA/RN/mobile screen is governed by Stitch or a similar external design artifact.
- The user cares about interface interaction, design parity, or regression prevention.
- The implementation already has tests/build but design/UI interaction is not part of the gate.

## Anti-conditions

- Do not treat a generated Stitch screen as runtime proof of backend, vision, ASR, safety, or recognition quality.
- Do not mutate external Stitch projects from ordinary CI/gate scripts. Generation/editing is an explicit design action; verification should be read-only.
- Do not force optional design-only navigation/chrome into current product behavior without a product decision.

## Landing pattern

1. Create or identify the canonical Stitch project, design system, and screen.
2. Record stable IDs in repo config, not only in chat:
   - project ID/resource name
   - design system asset ID
   - screen ID/resource name
   - screenshot/html artifact names and download URLs
   - local screenshot evidence path
3. Add a read-only `design-gate` that verifies:
   - local UI contract selectors and diagnostic fields still exist;
   - required safe-area/design tokens and critical copy are present;
   - named Stitch target is configured;
   - screenshot artifact exists locally, or can be fetched from the recorded URL;
   - external writes are disabled by policy.
4. Add or extend UI interaction smoke tests, preferably Playwright mobile viewport, covering design-critical interaction surfaces:
   - mode/select controls;
   - primary/secondary buttons;
   - safety acknowledgement;
   - voice/hands-free controls;
   - diagnostics/status fields.
5. Wire gates into the normal verification path:
   - `make verify` includes local contract + build + design-gate;
   - deeper `make ui-smoke` or equivalent runs browser interaction proof.
6. Write a short landing note under project docs with:
   - Stitch IDs;
   - local artifacts;
   - visual acceptance readback;
   - known deltas between design and implementation;
   - semantic boundaries.

## Verification evidence to report

- Stitch project/design-system/screen IDs.
- Design gate output: `ok`, `externalWritesAllowed=false`, missing selector/data-token arrays empty, target status ready.
- UI smoke output with passed interaction tests.
- Build/test output.
- Explicit boundaries: pixel parity not yet done, optional design elements not implemented, runtime claims still need runtime evidence.

## Common pitfall

Saying “Stitch is connected” after creating a design or SDK tool is not enough. The design layer is only truly landed when a future verification run can fail if the product loses design-critical UI controls, diagnostics, safe-area tokens, or the named Stitch target/artifact.
