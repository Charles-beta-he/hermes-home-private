# Design-SDK → mobile production delivery gate

Use when a mobile/RN project syncs design-tool SDK artifacts into runtime UI and the user asks for enterprise/production-grade delivery, not only visual fill.

## Applicability

- React Native/PWA/mobile companion work where design-tool screens are design SSOT inputs.
- SDK artifacts are pulled locally by a design SDK or equivalent tool client.
- The product needs repeatable quality gates: design artifact presence, runtime surface mapping, UX receipts, accessibility, tests/build, rollback proof, dependency audit, and secret redaction.

## Anti-conditions

- Do not treat this as authorization to push, deploy, write back to the design cloud, rotate credentials, or claim store/MDM readiness.
- Do not persist API keys in repo docs/manifests/skills/memory; redacted manifests only.
- Do not claim “latest screen” from an unstable SDK list order unless the API exposes a reliable update timestamp or the user supplied a screen id.

## Procedure

1. Confirm SDK version and config source without printing secrets.
   - Use package-manager metadata if available.
   - Prefer reading a local config file or env var at runtime; write only `[REDACTED]` / `***` to artifacts.
2. Add a safe sync script instead of ad-hoc SDK calls.
   - Support `--dry-run`, `--project-id`, `--screen-id`, `--out-dir`, `--config`.
   - Download image/html or equivalent artifacts under a design evidence directory.
   - Emit a redacted manifest with project/screen ids, SDK version, artifact paths, and fetch time.
3. Handle screen ordering explicitly.
   - If the list API lacks stable `updateTime`, treat default order as advisory only.
   - For production claims, sync explicit screen ids or a curated set of related surfaces.
4. Map design blocks to runtime surfaces.
   - Each visible design block becomes either a reachable runtime control/state or an explicit future/local/draft boundary.
   - Bottom/top navigation controls must route to distinct functional surfaces, not one generic details page.
   - Local/draft/gated actions need truthful receipts near the action or via short toast.
5. Add a production gate script.
   - Check root workflow scripts exist (`test`, `build`, rollback proof, SDK sync, production gate/verify).
   - Check SDK dependency/version is declared.
   - Check runtime surface `testID` anchors exist for all implemented design surfaces.
   - Check UX action receipt strings exist for draft/local/gated actions.
   - Check every RN `Pressable` has `accessibilityLabel` and `accessibilityRole`.
   - Check test files assert the surface contract.
   - Check the redacted design manifest and required artifacts exist.
   - Scan repo files, excluding dependency/vendor/.git dirs, for known key prefixes or provider-specific secret patterns.
6. Add a one-command verification target.
   - Native lint/Jest.
   - Production gate.
   - Workspace test/build.
   - Rollback proof.
   - Runtime dependency audit.
7. Record boundaries in the project profile/ledger.
   - No push/deploy/cloud write performed unless explicitly authorized.
   - Hardware/microphone/store/MDM readiness remain separate gates unless actually verified.

## UI/UX standard to enforce

- Main UX presents one coherent assistant/avatar/control-room experience; SDK/Gateway/local/projection diagnostics stay secondary.
- Each secondary surface has a visible accessible return path.
- Dense score/metric UI uses readable text, not only color/progress bars.
- Draft-only or local-only controls must not imply external/cloud side effects.
- Design artifact is not runtime proof: require artifact + mapped runtime surface + tests + production gate.

## Pitfalls

- SDK screen list order may vary between calls; do not build “latest” logic from the default first item without timestamp proof.
- RN test renderers can choke on dynamic percentage width styles in some cases; for tested progress bars, prefer stable flex/proportional fills.
- A generated design screen is not evidence of implemented capability. Keep design SSOT, runtime behavior, and verification gates distinct.
