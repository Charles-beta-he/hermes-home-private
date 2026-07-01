# PRD → Stitch → PWA self-circulating workflow gate

Applicability: mobile/PWA work where Stitch or another design tool is the visual SSOT and the product must keep PRD, generated design, implemented UI, and interaction/runtime truth synchronized. Use especially when the user asks to “完善 workflow”, “自动完善缺失 PRD/UI”, “全盘推进”, or wants a design-to-implementation chain that can be run repeatedly.

Anti-conditions: do not auto-write external design tools, push/deploy, enable future navigation/routes, or change runtime side effects without explicit authority. Do not treat generated design copy as proof of backend/model capability.

## Pattern

1. Establish canonical sources:
   - PRD/spec doc for product intent, scope, selector/data-field contract, acceptance gates, and backlog.
   - Design config with stable project/design-system/screen IDs and local artifact path.
   - Landing/design note that records known deltas and semantic boundaries.
   - Implemented UI source, runtime source, visual-structure test, interaction smoke test.
2. Add a read-only `workflow-gate` that validates all layers:
   - PRD exists and has required sections.
   - Stitch/design target IDs and screenshot/artifact evidence exist.
   - PRD mentions all current selectors/data fields that the UI/runtime requires.
   - UI implements the selector/data-field contract.
   - Runtime references required diagnostic fields.
   - Makefile exposes `workflow-gate`, `workflow-propose`, `workflow-apply-safe`, `design-gate`, `visual-gate`, `ui-smoke`, and `verify`.
   - Visual and interaction gates cover key screen atoms.
   - Semantic boundaries are documented.
3. Add `workflow-propose` for local-only intervention packets when the gate fails:
   - Write ignored JSON/Markdown under `state/workflow/proposals/`.
   - For each missing item, classify target owner: `prd_backlog`, `pwa_runtime`, `stitch_design`, `makefile`, or `manual_review`.
   - Mark whether an item is safe to auto-apply.
4. Add `workflow-apply-safe` with a very narrow write policy:
   - It may append PRD backlog/checklist notes only.
   - It must not mutate Stitch/design tools, runtime behavior, routes, upload policy, external services, push, deploy, or publish.
5. Wire `verify` to include the read-only workflow/design/visual gates, then keep deeper UI interaction smoke as an explicit command when it needs browser runtime.
6. Add a broken-project fixture test:
   - Copy a minimal project to a temp directory.
   - Deliberately remove a PRD selector/field mention.
   - Run `workflow-gate --root tmp --propose --apply-safe`.
   - Assert proposal files are created and safe-apply only appends a PRD backlog note.

## Runtime evidence-surface fill

When a design screen has placeholders like “等待首帧”, `CONF --`, or `EVIDENCE --`, do not leave them as static copy after workflow closure. Make them runtime-addressable fields and prove they fill from a deterministic controller response.

Recommended fields:

- `data-field="preview-frame-state"` for waiting/uploading/analyzing/evidence-written state.
- `data-field="advice-message"` for mutable advice text only; do not write `textContent` to the whole card container or it will destroy title/metric child nodes.
- `data-field="advice-title"`, `data-field="advice-summary"`.
- `data-field="confidence-chip"`, `data-field="evidence-chip"`, `data-field="mode-chip"`.

Test pattern:

- Use Playwright mobile device emulation.
- Inject fake `navigator.mediaDevices.getUserMedia` using a canvas `captureStream()`.
- Mock session and interaction HTTP endpoints with `page.route`.
- Stub WebSocket if the smoke target is HTTP frame readback.
- Click the real start button and assert the UI displays response-derived confidence/evidence/mode, guidance copy, safety boundary, and camera setup.
- Capture a final screenshot from the same deterministic runtime state when showing the result to the user.

## Pitfalls

- A passing static visual gate is not proof that runtime evidence flows into the UI. Add a mock-controller interaction smoke for filled state.
- If runtime sets `textContent` on a section/card container, it can delete nested metric chips and labels. Update only the intended child data-field.
- If a helper updates default camera/safety copy during diagnostics, persist the last remote camera instruction and safety boundary so later diagnostic refreshes do not overwrite controller-provided guidance.
- Proposal generation is useful even when there are no gaps: it should produce a no-op packet and make `workflow-apply-safe` return `no_safe_items`, not modify source files.
