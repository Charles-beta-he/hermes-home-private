# Open-source capability absorption governance

Use when a user wants to take a feature from an open-source project and implement or strengthen it inside their own architecture.

## Core invariant

Do not promote an external capability into the mainline just because it is attractive, popular, or model-approved. Mainline promotion requires all three gates to be evidenced:

1. **Evidence verification** — live source inspected, claim grounded, and at least one reproducible local demo / CLI / API / official test / real sample output exists, or a blocker is recorded.
2. **Rollback / fallback** — old path is preserved behind a feature flag, adapter boundary, kill switch, or documented fallback; rollback must be executable or explicitly rehearsed/described.
3. **Maintenance readiness** — license/version/upstream drift/upgrade owner or review cadence is clear enough that the capability can survive future changes.

If any gate is missing, valid outcomes are `watch`, `skill-only`, `wrapper`, or a bounded follow-up task. Do not mark it `integrated`, `taskpool-automated`, or `done`.

## Default landing sequence

1. Source review: repo identity, commit/version, license, README/manifest/API surface.
2. Capability decomposition: problem, capability, interface, implementation coupling, verification shape.
3. Architecture mapping: map to local primitives, adapter point, registry entry, event/state boundary, permission surface.
4. Minimal prototype: bounded reversible slice; no mainline replacement.
5. Harness: fixed input, fixed assertions, readable failure, offline rerun where possible.
6. Shadow/wrapper phase: compare with current path; record success rate, cost, quality, latency, and failure mode.
7. Promotion readiness: evidence + rollback/fallback + maintenance plan all present.
8. Mainline adoption: only after readiness; preserve feature flag or fallback until stability is proven.

## Hermes/taskpool operational rule

For Hermes self-evolution or taskpool work, prefer a first-class `repo_capability_absorption` task/SSOT before implementation. The task should carry source/claim metadata, target surface, integration level, reproduction/risk/harness gates, rollback/fallback, maintenance plan, and promotion readiness evidence.

Creation of an intake task does **not** authorize vendoring, external side effects, runtime integration, taskpool automation, or main-chain replacement.

## Pitfalls

- Treating README claims or multi-model consensus as proof.
- Copying external code directly into core instead of using an adapter/wrapper first.
- Letting the external project's state model, worker lifecycle, or permission assumptions override local architecture.
- Calling a proof-only or intake-certified task "done" before source review/prototype/harness exists.
- Forgetting license and upgrade drift until after integration.
