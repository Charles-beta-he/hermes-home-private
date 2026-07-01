# Stitch/PWA Product Tabs and Vision Readiness

Use when a Stitch-derived mobile/PWA screen has an accepted visual design but the user asks to fill the whole product surface, or when bottom navigation and vision/model status must be enterprise-deliverable rather than demo-like.

## Landing-zone classifier

- Reusable procedure: promote safe local UI surfaces from placeholder navigation to real product panels.
- Pitfall: do not stop at href anchors or generic diagnostics when the user has authorized project-level product completion.
- Verification checklist: product-tab behavior, readiness readback, adapter inventory, and no mock/stub leakage in customer-facing copy.
- Anti-condition: do not install heavy model/runtime dependencies, write external design systems, deploy, or claim real recognition unless explicitly authorized and verified by runtime readback.

## Procedure

1. Convert bottom navigation placeholders into first-class local product panels when full routing is not yet in scope.
   - Use panel IDs such as `#tab-overview`, `#tab-voice`, `#tab-diagnostics`, `#tab-safety`.
   - Use `data-tab-target="..."`, `hidden`, and `aria-current` rather than dead `href="#"` links.
   - Keep separate pages/routes out of scope until a route PRD exists, but make the current shell usable.
2. Give every panel product-owned content:
   - overview: mode, camera/preview, sampling controls, live advice, evidence/confidence.
   - voice: speech controls, command affordances, privacy boundary.
   - diagnostics: Controller origin, readiness, vision adapter, model list, session/mode/frame/boundary.
   - safety: setup guidance, stop conditions, acknowledgment, delivery boundary.
3. Add runtime tab switching:
   - initialize from `location.hash` with a safe default.
   - prevent default navigation, toggle `hidden`, update `aria-current`, and `replaceState`.
4. Add fail-visible vision readiness instead of product claims:
   - create/read a local adapter inventory command if one does not exist.
   - expose `/health/ready` or equivalent Controller readiness in diagnostics.
   - show adapter/model status to the operator; use copy like `模型待接入` or `降级`, not raw `stub`/`mock` copy.
5. Keep fixtures isolated:
   - Playwright may mock Controller, camera, WebSocket, or model responses.
   - Product advice and primary UI must not show `mock`, `demo`, `sample`, raw `mode=...`, or `evidence=...` debug strings.
6. Update PRD/workflow/design gate sources together so the automation chain knows the new panel and readiness contracts.

## Vision adapter inventory pattern

Prefer a read-only inventory script/target that reports:

- implemented real adapters
- available real adapters
- stub/test-only adapters
- classification per adapter: `test_only_stub`, `real_local_available`, `implemented_but_runtime_unavailable`
- production rule: real adapter requests must fail visibly; no silent fallback to stub

The inventory command is evidence, not proof of recognition. Real recognition may only be claimed after a non-stub adapter is both available and verified through runtime health/readiness plus an analysis smoke.

## Verification checklist

- `make workflow-gate` or equivalent coherence gate passes.
- adapter inventory command runs and distinguishes implemented vs available adapters.
- build/typecheck passes.
- visual gate verifies bottom nav targets and panel visibility after clicking tabs.
- interaction smoke covers each product panel and the live evidence surface.
- screenshots are captured for each product panel when claiming UI delivery.
- docs/PRD state the remaining true boundary: install/verify real adapter runtime before claiming real recognition.

## Common pitfalls

- Treating bottom tabs as done after replacing `href="#"` with anchors. If the user asks for full product-surface fill, local product panels are the minimum safe slice.
- Claiming a vision node is real because an adapter class exists. Inventory must distinguish implemented adapter code from importable runtime dependencies and installed model weights.
- Hiding degraded/model-unavailable status to make the UI look polished. Enterprise UX should be operator-facing and fail-visible.
- Capturing missing dependencies as a durable negative rule. Record the readiness/verification pattern, not the transient machine state.
