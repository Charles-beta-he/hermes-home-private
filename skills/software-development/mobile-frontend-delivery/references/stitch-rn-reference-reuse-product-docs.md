# Stitch/RN Reference Reuse + Product/UX Documentation

Use when a React Native/mobile product already has Stitch or design-tool artifacts in the repo and the user asks for enterprise/product-grade UI progress, especially after correcting that product docs or UX records are missing.

## Trigger

- User says the UI was not redesigned through Stitch, but existing reference systems/artifacts should be used.
- User explicitly authorizes local product/UI progress but does not authorize a new external Stitch generation/redesign.
- Product docs, UX records, or reference-source traceability are missing from closeout.
- RN/PWA surface already has functional tests but still feels under-documented or disconnected from design references.

## Procedure

1. **Classify authorization before acting**
   - Treat this as local code/docs/tests unless the user names an external target.
   - Do not create a new Stitch project, sync new remote screens, push, deploy, or publish unless separately authorized.
   - Use Agent OS / policy preflight if the task touches Hermes control-plane or high side effects.

2. **Inventory existing references first**
   - Search the repo for `references/stitch/`, `sdk-sync/`, manifests, exported HTML/PNG, and prior UX/UIMax reports.
   - Build a small contact sheet or otherwise inspect the existing images.
   - Select one master direction and list the exact reference files used.

3. **Translate references into runtime anchors**
   - Carry over durable design tokens and IA, not random decoration:
     - home/control-room hierarchy;
     - ion/orb or hero status object;
     - bottom dock/global tabs;
     - knowledge/document cards;
     - release/readiness score;
     - settings with diagnostics hidden behind disclosure.
   - Make each important product surface reachable and give it a stable `testID` / accessibility label.
   - Keep external actions as drafts/readback/confirmation; do not make product copy imply real release or side effects.

4. **Supplement product and UX documentation in the same slice**
   - Add or update a product delivery doc with product boundary, run commands, verification evidence, and blockers not claimed done.
   - Add a product experience spec with:
     - reference files used;
     - product thesis;
     - UX principles;
     - information architecture;
     - runtime anchors/test IDs;
     - acceptance criteria;
     - anti-claims such as no App Store/TestFlight/public SaaS release unless actually done.
   - Append a short project ledger/profile note only if the project already has an SSOT ledger; keep session progress out of memory.

5. **Update gates and tests**
   - Patch RN/Jest tests to assert the new anchors and user-facing copy.
   - Patch production/readiness gate so the new product/UX anchors are required.
   - Run at minimum RN lint/tests and the project production verification command.

## Pitfalls

- Do not interpret “授权” as authorization for external Stitch generation, push, deploy, TestFlight, App Store, or broad dispatch.
- Do not claim UI completion from docs or tests alone if the user asked for strict uIMax/pixel acceptance; run the uIMax/screenshot workflow or state that it remains unaccepted.
- Avoid leaving design artifacts as passive screenshots. Product surfaces must be reachable through real navigation and covered by tests.
- Do not let diagnostics, monorepo details, debug state, mock/sample wording, or provider internals dominate the default mobile surface.

## Verification checklist

- Existing reference artifacts named and paths recorded.
- Product docs and UX docs created/updated.
- Runtime anchors added to RN/PWA surfaces.
- Tests/gates updated to require those anchors.
- Production verification passes with fresh output.
- Closeout states what was local-production only and what still requires exact external authorization.
