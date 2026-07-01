# PRD → Design SSOT → Runtime Workflow Gate

Applicability: use when a project has a design-tool SSOT (Stitch/Figma-like screen, generated mockup, or screenshot artifact) and the user wants the implemented product and workflow automation to stay synchronized with it. This is a class-level workflow pattern; do not copy project IDs, screen URLs, or local paths across projects.

Anti-conditions:
- Do not use this to justify mutating an external design tool from CI; verification gates stay read-only unless the user explicitly asks for a design-generation/edit action.
- Do not treat visual design as runtime proof for model quality, safety, recognition, payments, permissions, or external side effects.
- Do not activate navigation/features shown in a mockup without a PRD row and route/behavior contract.

## Pattern

1. Establish a PRD baseline before filling design behavior.
   - Product intent and P0 scope.
   - In-scope and out-of-scope boundaries.
   - User flows.
   - A design-block → runtime-function mapping table.
   - Required selectors/data fields/API states.
   - Acceptance gates and known backlog.

2. Record the design SSOT in scoped config/docs.
   - Project/screen/design-system IDs or URLs.
   - Local non-secret screenshot/artifact cache if safe.
   - A policy flag that verification is read-only.
   - Known deltas: future navigation, placeholder copy, design-only affordances.

3. Add a workflow config and gate.
   - Config lists canonical sources: PRD, design config, landing notes, runtime files, visual tests, interaction tests.
   - Gate validates source existence, PRD sections, design target presence, screenshot/artifact presence, selector/data-field implementation, runtime field references, Makefile targets, visual/interaction test coverage terms, and semantic-boundary docs.
   - Gate outputs structured JSON and fails closed when any layer drifts.

4. Wire automation targets.
   - `workflow-gate`: PRD/design/runtime/automation coherence.
   - `design-gate`: read-only design target + local UI contract.
   - `visual-gate`: Playwright screenshot/bounding-box/layout assertions.
   - `ui-smoke`: real interaction smoke for controls/state.
   - `verify`: includes workflow/design/visual gates plus normal tests/build.

5. Use the project itself as the fixture.
   - Add deterministic tests that run the workflow gate against the current repo.
   - Verify expected project-independent invariants: no missing sections, no missing selectors/data fields, target configured, gate targets present, semantic boundaries documented.
   - Clean transient Playwright screenshots/test-results before commit.

6. Close with scoped evidence.
   - Run `make workflow-gate && make verify && make ui-smoke` or the project equivalents.
   - Commit only scoped workflow/config/test/docs changes.
   - Stop before push/deploy/publish unless explicitly authorized.

## Fill workflow for future UI/product changes

For every new design/function fill slice:

1. Update the PRD row or backlog item first.
2. Update/read back the design SSOT if visual behavior changes.
3. Update runtime implementation without deleting existing contracts.
4. Add or update visual and interaction gates.
5. Run the full workflow gate chain.
6. Commit scoped changes after cleaning transient artifacts.

## Pitfalls

- Design-first drift: changing UI from a mockup without a PRD makes later runtime behavior ambiguous.
- Runtime-only drift: passing API/tests does not prove the design layer is governed.
- Mockup-as-capability: visual copy like “识别中” must not imply real recognition if the backend is stub/degraded.
- Bottom-nav trap: navigation shown in a design should remain future-only until routes, state, and acceptance are defined.
