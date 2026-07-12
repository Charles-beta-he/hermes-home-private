# Self-extension + Control Console operationalization pattern

Use this reference when a portfolio-governed Hermes extension direction needs to move from `proposal/source-observed` into an evidence-backed local slice, especially for:

- long-running Hermes self-extension / mission-control projects;
- local operator/control-console prototypes;
- dashboard-listed capability ladders that must not be treated as production just because they appear in UI data.

## Landing-zone classification

Before writing durable state, split conclusions:

- Reusable control-loop procedure -> skill/reference.
- Project-specific profile paths, mission ids, artifact paths -> project profile or scoped project ledger only.
- Concrete next engineering work -> taskpool/proposal, not a fake skill.
- Session progress -> no global memory.

## Self-extension project maturity path

For `hermes-self-extension-os`-class projects, advance maturity in small evidence gates:

1. `proposal/needs-evidence`: direction exists but has no contract or current readback.
2. `contract-ready-metadata-slice`: project has objective model, mission contract, decision protocol, resume protocol, side-effect boundaries, stage-report schema, and a stage report artifact.
3. `validated-active-control-loop-slice`: a real mission/control loop is active, has no open decisions, has a healthy doctor/readback, and stale local-ledger backlog is either absent or recovered with an audit reason.
4. `runtime-integrated`: Hermes runtime/CLI/dashboard enforces the loop, not just documents it.

Do not skip directly from proposal to production-ready.

## Mission gate unblocking pattern

When a mission is blocked on a human decision and the user gives broad authorization such as “认可，全盘推进”, only apply it to the narrow local gate that matches the pending decision. Preserve the existing mission blocked actions.

Recommended sequence:

```bash
hermes mission inbox --json
hermes mission status <mission_id> --json
hermes mission doctor <mission_id> --json
hermes mission decide <decision_id> "<scoped answer with boundaries>"
hermes mission doctor <mission_id> --json
```

If doctor then recommends stale signal recovery, do a dry-run first unless the current user instruction clearly authorizes local-ledger recovery:

```bash
hermes mission recover-signals <mission_id> --json
hermes mission recover-signals <mission_id> --apply --reason "<audit reason; local-ledger only; no external side effects>" --json
hermes mission doctor <mission_id> --json
hermes mission report <mission_id> > <project>/05-status/mission-report-YYYYMMDD.txt
```

Verification targets:

- mission status `active`;
- open decisions `0`;
- stale flow signals `0`;
- tick script exists;
- cron job exists;
- report artifact is written to the project status directory.

Pitfalls:

- Do not mutate mission budget/cadence under broad “推进” authorization; that remains a separate blocked action unless explicitly requested.
- Do not treat signal recovery as task completion. It is local-ledger housekeeping that restores the control loop.
- If command output is huge, parse/summarize with a bounded script rather than dumping full pending-signal payloads into the chat.

## Control console validation pattern

For `hermes-control-console`-class projects, source files and dashboard JSON prove only that a capability is represented. Current runtime validation requires running the console's own gates and capturing artifacts.

Typical local verification chain:

```bash
pnpm test:graph
pnpm test:ui
pnpm test:api
pnpm test:launchd
pnpm snapshot
pnpm lint
pnpm build
pnpm test:browser
pnpm test:human-inbox
```

Record:

- exact Node/pnpm versions if relevant to evidence;
- pass/fail for each gate;
- artifact paths for browser and human-inbox harness summaries;
- repo dirty-state note if snapshot regeneration changed generated data.

Maturity mapping:

- `source-observed`: docs/source/dashboard mention capability.
- `validated-local-slice`: graph/ui/api/build/browser/human-inbox gates pass with artifacts.
- `operator-integrated`: console read-only surface is connected to Hermes CLI/dashboard readback.
- `external-write-capable`: only after capability ladder gates, preflight, rollback path, and explicit user authorization.

Anti-conditions:

- Do not edit the console implementation merely because portfolio metadata is being updated.
- If local safe-boundary UI hardening is authorized, keep fixes narrow, rerun the console's own full `pnpm verify`, and preserve generated evidence paths in the portfolio ledger.
- When mission/task backlog cleanup makes dashboard data sparse (for example zero current task routes), adapt harness assertions to the actual DOM/data state instead of requiring route highlights for routes that do not exist. Keep the negative assertion explicit with a route-count readback.
- Do not promote external-write or rollback capabilities from UI labels alone.
- Do not stage/commit generated console files or unrelated untracked files unless the user asked for that project’s implementation change.

## Portfolio writeback after validation

After validation, update only the scoped project profile, project progress ledger, and portfolio registry:

- set project status to the highest evidenced maturity;
- update `current_components` with component-level evidence states;
- append project-ledger evidence with command names and artifact paths;
- run the portfolio doctor and portfolio verify command for the active portfolio;
- validate JSON files.

Do not put project-specific IDs or artifact paths into global memory; keep them in the project ledger/profile.

## Safe-boundary closeout review pattern

Applicability: portfolio-governed local projects where the user has authorized continued safe progress but has not authorized external effects, production promotion, credentials, payment, destructive actions, or broad lifecycle execution. Anti-condition: do not use this pattern to justify crossing those boundaries; it is only for local evidence/proof/harness/metadata hardening.

Before finalizing, classify remaining work:

- `final_safe_boundary`: local, reversible, evidence-only, or harness/metadata/proof hardening that can be completed under the current authority;
- `real_authority_boundary`: external dispatch, deploy/push/publish, credentials, payment, destructive action, production runtime promotion, default voice/external-send enablement, scheduler/worker/lifecycle write, or A+/production acceptance without an explicit standard;
- `not_a_boundary`: duplicate verification, already green gates, or attempts to relabel local evidence as production certification.

For final safe-boundary closeout:

1. Write a manifest that includes artifact paths, existence, sizes, and hashes.
2. Add denominator/scope notes for strong claims such as `100% coverage`, `0 issues`, `PASS`, or `A-/B+`; say exactly what population/tool/audit those claims cover.
3. If an independent reviewer returns WARN for grounding gaps, amend the manifest with the missing artifacts or scope notes rather than arguing from summary text.
4. Re-run the independent review after amendment and write the PASS/WARN result back into `review_history`.
5. Re-run portfolio verify, semantic audit, and strict verify after manifest/profile/registry/ledger updates.
6. In the final answer, distinguish completed safe boundaries from preserved high-authority boundaries; do not present preserved boundaries as unfinished local work.

Pitfalls:

- A verifier PASS is evidence for the scoped manifest, not global runtime certification or production readiness.
- A copied/mirrored report may be counted as an artifact for traceability, but note duplicates if artifact count matters.
- Compact review prompts can obscure two files with the same basename (for example multiple `summary.json` files); include enough directory context or hashes to avoid ambiguity.
- Do not keep re-running the same green gates unless a new write changed the evidence set.
