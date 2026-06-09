# Local Brain HTML App UIMax / Browser-QA Report - 2026-05-18

## Scope

Target app: `/Users/charles/personal-hermes-brain/hermes/local-brain-html-app`
Built output: `/Users/charles/Documents/brain/07-仪表盘/local-brain-app/index.html`
Canonical data snapshot: `/Users/charles/.hermes/memory/local-brain-model.json`

This is now a complete first-generation React/Tailwind/D3/Three-ready replacement for the ugly static local-brain HTML surface. Markdown / JSON / kanban.db remain canonical truth; the app is a derived, rebuildable UI.

## Implemented surfaces

1. Cockpit
   - KPI overview for HTML entries, task nodes, relationship edges, blocked tasks, running tasks.
   - Search across labels, paths, priority, lane, status, and group labels.
   - Filter chips: all / HTML / task / blocked / running.
   - Inspector with canonical markdown, HTML sidecar, status, visual state, evidence count.

2. Taskpool Mission Control
   - P0/P1/P2/P3/unprioritized lanes.
   - Mission telemetry bound to exported fields only: visual state, multimodel gate, evidence count.
   - No fake telemetry: missing values render as unavailable.
   - Reduced-motion safe radar/pulse styling.

3. D3 Atlas
   - Real SVG graph rendered from exported nodes / edges / groups.
   - Cluster backgrounds, labels, node colors, blocked danger ring, running glow.
   - Browser visual audit confirmed graph is present: 282 real nodes, 87 live edges, 5 clusters in current build.

4. Memory Palace
   - Three.js-ready spatial model using real group rooms.
   - Uses `THREE.Vector3` preparation while keeping the actual rendered fallback DOM/file:// safe.
   - Room dominant status is derived from real node statuses; no invented task states.

5. Ops Console
   - Canonical truth boundary check.
   - HTML freshness check.
   - Mission telemetry export check.
   - Graph contract check.
   - Shows the browser-QA command used for repeatable verification.

## Verification commands and results

- `python3 /Users/charles/.hermes/scripts/test_brainctl_export_app_data.py`
  - PASS
- `python3 -m py_compile /Users/charles/.hermes/scripts/brainctl.py /Users/charles/.hermes/scripts/test_brainctl_export_app_data.py`
  - PASS
- `pnpm test -- --runInBand`
  - PASS: 2 files, 11 tests
- `pnpm build`
  - PASS: single-file `dist/index.html`, gzip about 117 KB
- `pnpm browser:qa file:///Users/charles/Documents/brain/07-%E4%BB%AA%E8%A1%A8%E7%9B%98/local-brain-app/index.html`
  - PASS
  - desktop 1280x900: console errors 0, page errors 0, horizontal overflow 0
  - mobile 375x812: console errors 0, page errors 0, horizontal overflow 0
- `python3 ~/.hermes/scripts/brainctl.py --json html status`
  - PASS: total 98, stale_count 0

Screenshots:

- `/tmp/local-brain-html-app-desktop.png`
- `/tmp/local-brain-html-app-mobile.png`

## Code quality metrics

- ARIA / role / aria-pressed occurrences in `App.tsx`: 11
- Global `:focus-visible`: present
- `prefers-reduced-motion`: present via no-preference animation guard
- Static inline styles in TSX: 1, only for CSS custom property `--room-color`
- Console errors: 0
- Horizontal overflow: 0 on 1280 and 375

## UIMax score

| Dimension | Grade | Evidence |
| --- | --- | --- |
| Visual design | A | Cockpit/Mission/Atlas/Palace/Ops all have coherent dark command-center styling and hierarchy. |
| Responsiveness | A | Browser-QA verified desktop 1280 and mobile 375 with zero horizontal overflow. |
| Accessibility | A- | Semantic main/header/nav/sections, tablist, aria-pressed filters, focus-visible, labels. Further improvement: graph keyboard node selection. |
| Code quality | A- | Typed model adapters, TDD coverage, file:// single-file build, minimal inline style. Further improvement: split App.tsx into component files. |
| Interaction | A- | Search, filters, tabs, inspector, Mission Control, Atlas, Palace, Ops verified. Further improvement: D3 zoom/drag. |
| Console health | A | Browser-QA reports zero JS console errors and page errors. |

Overall: A- / production-usable first-generation local-brain app.

## Remaining P2/P3 improvements

P2:
- Add keyboard-selectable graph nodes and graph zoom/fit controls.
- Split `App.tsx` into component modules.
- Add a refresh wrapper that runs export-app-data + pnpm build + deploy in one command.

P3:
- Replace deterministic SVG layout with force/collision tuning if graph density grows.
- Upgrade Memory Palace from DOM-safe spatial rooms to optional WebGL mode after D3 Atlas stabilizes.
