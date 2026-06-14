# Control Console Human Inbox UX Regression Pattern

Use this reference when a dashboard/control-console UI change appears technically verified but the user reports that the rendered UI is cramped, unreadable, or conceptually wrong.

## Failure shape observed

A broad browser harness returned `issueCount=0`, but the actual Human Inbox screenshot showed:

- a visible permission-scope matrix inserted into the primary workflow;
- grid/card text rendered vertically because columns were squeezed to a few pixels;
- tiny horizontal scrollbars and clipped list/detail content;
- copy that framed the console as `read-only` / `only observe`, conflicting with the intended control-console experience.

Root causes:

- The harness tested a broad page/topology smoke, not the changed Human Inbox surface.
- A CSS media rule changed `grid-template-columns` without updating `grid-template-areas`, causing invalid/squeezed grid layout between breakpoints.
- The UI exposed implementation capability boundaries as a permission matrix instead of keeping safety at the action point.

## Correct verification pattern

Add a surface-specific Playwright/DOM harness that:

1. Starts the app from the real project build/preview command.
2. Captures screenshots and machine-readable DOM geometry for the exact changed surface.
3. Tests representative viewports, including:
   - the user's normal desktop viewport;
   - a short desktop viewport;
   - a breakpoint-band viewport just above tablet/mobile collapse.
4. Asserts positive contracts:
   - lead/list/detail panes exist;
   - list and detail widths remain readable;
   - request cards keep readable height;
   - scroll panes use bounded internal scrolling;
   - page horizontal overflow stays near zero.
5. Asserts negative contracts:
   - unwanted permission matrices or diagnostic panels are absent from the main workflow;
   - copy does not frame the console as `read-only-only` when the product goal is an operable control entry.
6. After the harness passes, inspect the generated screenshot manually. If text is vertical, cramped, or visually unusable, keep the regression open.

## Design lesson

For operator consoles, show the next action and local receipt/readback. Capability/session/safety details should be enforced by endpoint gates and displayed at the action point or secondary diagnostics panel, not as a primary workflow matrix unless the user asks for that diagnostic view.

## Example checks to encode

- `document.documentElement.scrollWidth - clientWidth <= 4`
- `.operation-permission-scope` is absent from the Human Inbox
- `.approval-request-list` and `.approval-request-detail` exist
- list/detail rectangles are above readable width thresholds
- first cards have sufficient height and `scrollHeight - clientHeight` within tolerance
- top copy says control/operation session rather than `current read-only snapshot`
