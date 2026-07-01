# Stitch/PWA Enterprise UX Closure Pattern

Use when a Stitch-generated mobile design has been wired into a PWA/RN surface and the user wants production-grade or enterprise-deliverable UX rather than a demo.

## Applicability

- Stitch/Figma/design-tool screen is already the visual SSOT.
- A PWA/mobile implementation exists with workflow/design/visual/UI gates.
- The UI still contains placeholder/mock/debug language, dead navigation, or unclosed “next-fill” backlog items that are locally safe to implement.

Anti-conditions:

- Do not auto-write external Stitch/Figma screens without explicit authority.
- Do not claim real model recognition from mocked or stubbed controller responses.
- Do not turn in-page anchors into full product routes unless a route PRD exists.

## Procedure

1. Reclassify every backlog item:
   - Safe local UX contract: implement now.
   - Test-only fixture: keep isolated in e2e/support code.
   - External/design write, prod deploy, credentials, real model runtime: stop at boundary packet.
2. Remove demo/mock leakage from product UI:
   - Avoid `mock`, `demo`, `sample`, `fixture`, `mode=...`, `evidence=...`, raw `stub` in user-facing copy.
   - Keep diagnostics truthful but operator-facing: “模型待接入”, “证据 3”, “置信 87%”.
3. Make generated navigation usable:
   - Replace `href="#"` with real product surfaces. If full routing is not in scope, prefer a one-shell tab/panel model (`data-tab-target`, `hidden`, `aria-current`) over loose anchors so the bottom bar feels like a real mobile product surface.
   - Give each surface a bounded job (overview, voice, diagnostics, safety, etc.) and document that separate routes/pages still need a route PRD.
4. Turn model/runtime uncertainty into a visible readiness surface:
   - Add adapter inventory/readiness readback instead of letting UI copy imply recognition that is not proven.
   - For real local adapters, add a deterministic smoke that proves `/health` and `/analyze-frame` execute through the non-stub adapter; label synthetic-frame smoke as API/runtime proof, not quality or object-recognition proof.
   - Keep `stub` as test/development only and fail visibly when a requested real adapter is unavailable; never silently fall back to stub in production paths.
5. Add regression tests:
   - Positive: fixture response fills runtime-backed chips/advice.
   - Negative: advice/user-facing copy does not contain raw debug strings.
   - Visual/bbox: preview pill centered in camera, nav links/panels switch correctly, content order is stable.
   - Runtime readiness: diagnostics expose controller readiness, adapter name/status, and model list.
6. Add a visual drift gate before claiming design parity:
   - A thresholded pixel-diff or screenshot drift script is useful as a readiness signal, but it is not pixel-perfect parity unless thresholds and target resolution are deliberately tightened in a separate 1:1 pass.
7. Update the workflow config/backlog after landing so completed items are not presented again as future work.
8. Verify with the full chain: workflow gate, unit/contract tests, build, design gate, adapter inventory/smoke, pixel-diff/readiness gate, visual gate, UI smoke, and screenshot/readback evidence.

## Pitfalls

- A passing mock-controller smoke proves the UI can consume the contract; it does not make the app production-real. The product surface should still be deliverable: no fake-looking copy, no dead buttons, truthful degraded-state labels, and no hidden capability claims.
- “Real adapter installed” is not the same as “domain recognition solved.” A MediaPipe pose smoke proves local pose-runtime execution; it does not prove assembly-object recognition, OCR, VLM scene reasoning, or product safety quality.
- If a design-generated bottom bar exists, leaving it as anchors may still feel unfinished. Use tab/panel switching for current P0 surfaces, then defer only true multi-route/product-page scope.
