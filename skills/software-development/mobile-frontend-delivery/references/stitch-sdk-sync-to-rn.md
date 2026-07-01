# Stitch SDK sync to React Native mobile surfaces

Use this when a mobile RN/PWA implementation must follow the latest Stitch design and prior sessions may already have a working SDK setup.

## Trigger

- User asks to use an updated Stitch design, latest SDK, or “other session installed SDK”.
- MCP Stitch is unavailable or incomplete, but a local SDK/config exists.
- Design sync must fill real mobile app functions, not just visuals.

## Procedure

1. Reuse prior/local SDK setup before guessing:
   - Search prior session context when available for SDK name/version/path.
   - Check installed/reference projects for SDK wrapper code and config paths.
   - Confirm npm latest with `npm view @google/stitch-sdk version` before installing.
2. Install the SDK in the target repo only as needed, usually dev dependency:
   - `npm install --save-dev @google/stitch-sdk@<confirmed-version>`
3. Add a safe sync bridge rather than embedding credentials:
   - Read API key from a local config such as `~/.rowboat/config/stitch.json` or `STITCH_API_KEY`.
   - Never print/write the key; manifests must contain `***` or `[REDACTED]`.
   - Save downloaded image/html artifacts under a project evidence/reference directory such as `apps/rn-shell/references/stitch/sdk-sync/`.
4. Do not trust default `list_screens` ordering as “latest” unless the SDK exposes reliable screen `updateTime`.
   - Prefer explicit `--screen-id` once a candidate is known.
   - If ordering varies, sync related observed screens and implement them as distinct reachable surfaces.
5. Implement functions from design anchors:
   - Map each visual control to a reachable RN surface/action.
   - Preserve existing app boundaries: mobile projection/draft/handoff only unless the product contract allows writes.
   - Keep prior surfaces reachable when adding a newer screen.
6. Verify:
   - Native: `npm run lint && npm test -- --runInBand` in the RN native app.
   - Workspace: `npm test && npm run build` at repo root.
   - SDK: `npm run stitch:sync:dry-run` or equivalent redacted dry-run.
   - Secret check: exact key prefix search excluding `node_modules`, `vendor`, `.git` should return zero matches.

## Pitfalls

- Stitch MCP connection failure is not a product blocker if a local SDK config exists; use the SDK path, but report cloud-write boundaries.
- `list_screens` may return unstable order and no reliable timestamp; avoid claiming “latest” from the first result without evidence.
- RN `react-test-renderer` can fail on dynamic percent width styles; use flex-ratio progress fills for test-stable progress bars.
- Do not turn design sync into raw screenshot copying. Fill semantic product surfaces: asset list, detail drilldown, settings, readiness score, export/optimize actions, etc.

## Evidence shape

Record, preferably in project profile/ledger rather than global memory:

- SDK version and redacted config source.
- Project/screen IDs and artifact paths.
- Implemented surfaces and changed files.
- Verification commands and pass counts.
- Secret redaction/absence check result.

## Anti-conditions

- Do not save API keys or raw manifests with secrets into skills, memory, or repo artifacts.
- Do not write back to Stitch cloud unless explicitly requested and authorized.
- Do not promote project-specific screen IDs into global memory; keep them in the project profile/ledger or a scoped reference note.
