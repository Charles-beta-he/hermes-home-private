# Project profile from target repo + reference repo

Scope: class-level workflow for adding a new work project to Hermes when the user names a primary target repo and a sibling/reference implementation repo. Use when the requested output is a durable project profile / project image, not a one-off chat audit.

Applicability:
- Primary repo is the future edit target.
- Reference repo is used for capability ceiling, endpoint/flow parity, or product-domain mapping.
- The result should survive future sessions in `~/.hermes/project-profiles/` and, when Portfolio OS is present, the portfolio registry.

Anti-conditions:
- Do not modify the reference repo unless the user explicitly changes the edit target.
- Do not write secrets or concrete third-party keys observed in source files into the profile, ledger, skill, or final report.
- Do not claim runtime/build/browser/device readiness from static profiling only.
- Do not store task/session progress in memory; keep project-specific paths in the project profile and ledger.

## Procedure

1. Confirm scope and repo state.
   - Verify both paths exist.
   - Capture branch, short commit, remote, and working-tree state for both repos.
   - Mark the reference repo boundary explicitly: reference-only unless instructed otherwise.

2. Scan target repo structure.
   - Count files by major extension excluding dependency/build/git directories.
   - Read package/build manifests, README, app entrypoint, router/routes, request/API layer, state store, config, and mobile/PWA setup if present.
   - Extract route count, API wrapper count, unique endpoint strings, top source directories, and business modules.

3. Scan reference repo structure.
   - Read settings/build manifests and app manifest/entrypoint equivalents.
   - Count modules, activities/fragments/screens/controllers where relevant.
   - Extract endpoint constants or API interfaces and realtime/socket constants.
   - Map native/mobile-only capabilities separately from target-web capabilities.

4. Compare target and reference.
   - Normalize endpoint paths and compute overlap.
   - Build a domain map: target paths/routes/API examples/reference anchors.
   - Produce an alignment matrix by dimensions such as domain breadth, endpoint contracts, realtime market data, mobile capability, auth/KYC/security, packaging/update.

5. Write durable artifacts.
   - Profile path: `~/.hermes/project-profiles/<project-id>.json`.
   - Ledger path: `~/.hermes/workflows/projects/<project-id>/progress-ledger.md`.
   - If Portfolio OS exists, add/update the registry entry and relations.
   - Required profile fields for Portfolio doctor commonly include: `ssot_root`, `progress_ledger`, `portfolio_profile`, `promotion_policy`, and `relations`.

6. Verify.
   - Re-read/parse JSON profile and registry.
   - Check referenced repo paths exist.
   - Run portfolio doctor if registry/profile governance exists; fix profile-schema warnings/errors rather than leaving a "created but unhealthy" project.
   - Final report should cite artifact paths, scan metrics, doctor result, and static-vs-runtime boundary.

## Recommended profile sections

- `project_identity`: primary target, reference repo, non-integration boundary, evidence level.
- `repositories`: path, remote, branch, commit, working-tree state, evidence anchors.
- `source_weighting_policy`: target current code first; reference repo second; README/docs as setup hints unless verified.
- `tech_stack` and build commands.
- `codebase_metrics` for target/reference and cross-repo endpoint overlap.
- `architecture` for target app entry, routing, state, request layer, i18n, mobile/PWA.
- `business_domain_map` with routes, files, API examples, and reference anchors.
- `reference_alignment_matrix`.
- `risk_register` with mitigations.
- `developer_workflow` with preflight, verification ladder, and red lines.
- `evidence_index` with file/line anchors.
- `current_components` and `profile_update_history`.

## Pitfalls

- Static scan is not runtime proof. Say "static-code-profile" unless build/browser/device verification was actually run.
- Reference repo breadth can be much larger than target repo; classify native-only capability as reference-only instead of a target gap by default.
- README Node/package-manager claims can drift from `package.json`/Volta/lockfile; record the drift and require preflight verification before builds.
- Large legacy apps often have duplicate request clients; API changes must search endpoint + route + user-facing text + reference implementation.
