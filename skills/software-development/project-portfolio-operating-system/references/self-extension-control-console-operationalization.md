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
- Do not promote external-write or rollback capabilities from UI labels alone.
- Do not stage/commit generated console files or unrelated untracked files unless the user asked for that project’s implementation change.

## Portfolio writeback after validation

After validation, update only the scoped project profile, project progress ledger, and portfolio registry:

- set project status to the highest evidenced maturity;
- update `current_components` with component-level evidence states;
- append project-ledger evidence with command names and artifact paths;
- run `hermes portfolio doctor` and `hermes portfolio verify --json`;
- validate JSON files.

Do not put project-specific IDs or artifact paths into global memory; keep them in the project ledger/profile.
