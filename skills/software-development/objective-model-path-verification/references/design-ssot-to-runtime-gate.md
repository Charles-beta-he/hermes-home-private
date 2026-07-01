# Design SSOT to Runtime Gate

Use when a full-landing task involves an external/design tool screen (Stitch, Figma-like artifacts, generated mockups) and the user's intent is not just to create a design, but to make it govern the implemented product.

## Pattern

1. Land the design artifact as a named SSOT
   - Record project/screen/design-system IDs or URLs in a scoped config/doc, not global memory.
   - Save a local evidence artifact if it is safe and non-secret (for example a screenshot cache).
   - Label generated design output as visual/design SSOT, not runtime proof.

2. Add a PRD/workflow baseline before design/function fill
   - Capture product intent, scope/non-scope, user flows, and a design-block → runtime-function mapping table.
   - Define required selectors, data fields, API states, acceptance gates, and known future-only features.
   - Add a workflow gate that validates PRD sections, design target configuration, runtime contract preservation, visual/interaction gate coverage, and semantic-boundary documentation.

3. Add a read-only design gate
   - Gate must never mutate the external design tool.
   - Verify the named target exists/configured.
   - Verify local artifact presence; if ignored from git, the gate may re-fetch from a configured URL.
   - Verify local UI contract selectors, data fields, tokens, and required copy.

4. Add runtime/UI gates separately
   - Interaction smoke: click/select/check/toggle real controls in browser automation.
   - Visual-structure gate: assert layout order and key bounding boxes against the design intent.
   - Keep screenshot outputs transient unless explicitly requested.

5. Preserve semantic boundaries
   - Do not turn design copy into runtime capability claims.
   - If the design shows future navigation or features not implemented, mark them optional/future and do not silently make them current requirements.
   - Runtime evidence (API/controller/model status) remains authoritative for claims like recognition quality, safety boundaries, or model readiness.

6. Verify and commit only scoped work
   - Run the full verification chain after wiring the gates.
   - Clean transient test-results/screenshots before commit.
   - Commit only when the working tree is scoped to this task and the user’s project policy allows local commits.

## Anti-conditions

- Do not store project IDs or one-off URLs in global memory.
- Do not make a gate write to Stitch/Figma/etc. unless the user explicitly asks for a design-generation/edit action.
- Do not replace runtime tests with a visual screenshot comparison.
- Do not push/deploy/publish without the user's explicit authority.
