# Agent OS Projectization + Read-only Projection Pattern

Use when a user approves an architecture/product signal (for example an AI OS diagram, social video, conference screenshot, or multi-model architecture analysis) as a durable Hermes-managed project.

## Applicability

- The signal is broader than a one-off answer and should become a portfolio-governed project.
- The next safe slice is metadata/profile/SSOT/projection work, not runtime mutation.
- The idea spans Hermes self-architecture, control surfaces, CapabilityGraph, context/evidence layers, edge/multimodal ingress, or governance.

## Anti-conditions

- Do not treat source-observed/social/conference claims as runtime evidence.
- Do not edit Hermes runtime, cron, taskpool, mission lifecycle, gateway delivery, or worker execution as part of the metadata slice.
- Do not enable always-on sensing, automatic memory writes, external sends, or worker lifecycle authority without a separate AuthorityGrant.
- Do not mark the project promoted/production-ready from a projection report.

## Procedure

1. **Create project identity**
   - Add a project profile under `~/.hermes/project-profiles/<project>.json`.
   - Create SSOT root under `~/.hermes/workflows/projects/<project>/`.
   - Add progress ledger, source/evidence index, roadmap, governance notes, and backlog/task-candidates.

2. **Register in Portfolio OS**
   - Add the project to `portfolio-registry.json` with `profile`, `type`, `status`, `role`, and `progress_ledger`.
   - Add relations as pattern-only unless facts/auth/secrets are explicitly allowed to merge.
   - Typical relations for Hermes self-architecture projects:
     - `governed_by -> project-portfolio-os`
     - `managed_by_agent_workflow -> hermes`
     - `shares_module -> hermes-control-console` / `hermes-self-extension-os` / model-router projects as applicable.

3. **Land the first safe slice as read-only projection**
   - Define schemas/taxonomies before runtime wiring:
     - `CapabilityNode`
     - `CapabilityIntent`
     - `AgentWrapper`
     - `EvidenceNode`
     - `ClosureRecord`
     - `AuthorityGrant`
     - side-effect taxonomy.
   - Generate projection artifacts under the project workspace, such as:
     - `capability_graph_projection.json`
     - `doctor_report.json`
     - `control-surface-projection.md`
     - `context-snapshot.json`
     - sample `closure-record.json`.
   - Projection scripts may read skills/tools/cron/project profiles/missions, but must not mutate runtime state.

4. **Use shadow mode for routing/intelligence**
   - Shadow routers should output `would_execute=false`.
   - Policy-block high side-effect requests by default.
   - Record sample/historical replay reports before any runtime integration.

5. **Update ledger and profile after each verified slice**
   - Component states should distinguish:
     - `contract-ready`
     - `validated-local-read-only-slice`
     - `shadow-schema-ready`
     - `sample-shadow-replay-validated`
     - `runtime_implementation: not_started/explicit-authorization-required`.
   - Evidence must cite commands, projection files, doctor reports, and readbacks.

6. **Verify**
   - Run portfolio doctor.
   - Run strict portfolio verify.
   - Validate generated JSON.
   - Compile projection scripts when applicable.
   - Run projection/shadow commands and read back their reports.

## Commit/guard pitfall

Hermes local git guards may flag governance words such as authorization/credential in newly staged architecture docs or projections. Do not bypass the guard casually. Reset the staged files, report the guard as a commit boundary, and leave the verified artifacts on disk unless the user explicitly authorizes a safe redaction/commit pass.

## Completion language

Allowed after this slice:

- `profiled+ledgered+contract-ready`
- `validated-local-read-only-slice`
- `sample-shadow-replay-validated`

Not allowed unless runtime code and gates are actually implemented and verified:

- `runtime-complete`
- `production-ready`
- `promoted`
- `default-enabled`
