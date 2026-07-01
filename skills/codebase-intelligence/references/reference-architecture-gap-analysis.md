# Reference-architecture gap analysis

Use when analyzing an external codebase to improve another system without integrating or modifying the external system.

## Method

1. Set boundary first: external repo is a reference, not a runtime dependency.
2. Inspect repo guidance files (`AGENTS.md`, docs, architecture docs) before drawing conclusions.
3. Extract class-level architecture signals rather than copying implementation:
   - manifest or metadata catalogs
   - activation/planning layers
   - scoped policy files
   - protocol/schema directories
   - SDK/contract boundaries
   - test harness and validation patterns
4. Produce a gap matrix:
   - external pattern
   - target-system gap
   - proposed local artifact/change
   - acceptance criterion
   - explicit non-claims
5. Land the smallest target-system artifact that proves the pattern locally: report, generated index, schema inventory, validator, dashboard, or planner.
6. Verify with deterministic commands: compile, analyze, parse generated JSON, run planner, inspect dashboard.

## Portfolio / multi-project absorption levels

When a user asks to apply a reference project across existing projects, first classify the requested landing level:

- A / light absorption: write a scoped reference note or project-profile pointer only; no implementation claim.
- B /方案吸收: create a per-project gap matrix with proposed local artifacts and acceptance criteria; no runtime/code completion claim.
- C /实施吸收: for each included project, read its SSOT/profile/ledger, land a bounded local implementation slice or implementation-ready contract, run project-specific proof, and append evidence to that project's ledger before calling it absorbed.

For C-mode portfolio rollout:

1. Preserve explicit exclusions as project/profile policy, especially work/client projects the user excludes.
2. Create a machine-readable rollout artifact and a human-readable summary under the portfolio or target governance SSOT.
3. Update the portfolio registry/policy so future sessions rediscover the default absorption level.
4. Add an intake entry to every included project's progress ledger, but label it as implementation intent/queue until that project has its own proof.
5. Keep reference boundaries visible: no code/brand/IP copying, no provider/legal cargo-culting, no external dispatch/deploy/destructive/credential authority expansion.
6. Verify parse/readback of the rollout artifact, registry, and affected ledger markers; run the portfolio/project doctor if one exists.

## Pitfalls

- Do not turn this into live integration unless the user asks for integration.
- Do not claim feature parity with the reference system.
- Do not treat a portfolio-wide C-mode rollout/intake as proof that each project has been implemented; each included project still needs its own SSOT readback, bounded slice/contract, proof, and ledger evidence.
- Do not let one repo's vendor-specific policy become a permanent global rule; keep it as a scoped reference until promoted deliberately.
