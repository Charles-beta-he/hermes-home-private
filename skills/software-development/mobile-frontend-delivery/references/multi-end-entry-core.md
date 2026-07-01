# Multi-End Entry Core for PWA/RN/Desktop/Web-UI

## Scope / Applicability / Anti-conditions

Scope: mobile/PWA/RN products that need multiple user/operator entry points while sharing one authority model and one monorepo contract.

Use when:
- a product has PWA and React Native shells plus desktop/web control surfaces;
- mobile is a companion/runtime projection, not the canonical fact authority;
- the team needs one shared package to describe entries, capability boundaries, and production-readiness gates;
- the UI must expose multi-end status without creating another source of truth.

Anti-conditions:
- Do not use for pure visual-only mobile fixes.
- Do not use when the target is a single native-only app with no web/PWA/control-surface reuse.
- Do not store project-specific paths, task IDs, branches, or release status in the class contract. Put those in the project profile/ledger; this pattern only defines the reusable shape.

## Core Pattern

Create a small shared TypeScript package, commonly named like `entry-core`, that exports:

```ts
type RuntimeSurface = 'desktop' | 'web-ui' | 'pwa' | 'rn-ios' | 'rn-android';
type EntryRole = 'operator' | 'mobile-companion';
type EnterpriseGateState = 'missing' | 'planned' | 'human_gate' | 'verified';

interface EntryDescriptor {
  id: string;
  surface: RuntimeSurface;
  role: EntryRole;
  title: string;
  purpose: string;
  authorityChain: string[];
  canMutateCanonicalFacts: boolean;
  mobileWritesCanonicalFacts: boolean;
  nativeCapabilities: string[];
  localFallbacks: string[];
  nextGate: string;
}
```

Recommended authority model for hybrid assistant/mobile companion systems:

```text
canonical server/agent state
→ exported/cacheable context projection
→ gateway/sync boundary
→ mobile local projection
→ read-only evidence + draft/handoff queue
```

The shared package should be metadata/control-plane contract only. It must not fetch live facts, seed demo data, write memory/tasks, or become another fact source.

## Entry Roles

- `desktop` and `web-ui`: operator/control-room entries. They may mutate canonical state only through governed server/agent authority gates, audit logs, and rollback/readback flows.
- `pwa` and `rn-*`: mobile companion entries. They can store local projections, encrypted persistence, selected device evidence, drafts, and handoff queues, but must not write canonical facts offline.

## Enterprise Readiness Gate

Model production/beta readiness as a pure function over named gates, for example:

- context projection verified;
- gateway dry-run/readback verified;
- encrypted local persistence verified;
- release/rollback proof verified;
- RN device install verified or explicitly human-gated;
- audit ledger verified;
- dependency/security audit resolved or formally accepted.

Return a structured result such as:

```ts
interface EnterpriseReadiness {
  grade: 'internal_alpha' | 'production_beta_candidate';
  decision: 'blocked' | 'beta_candidate';
  blockers: string[];
  verified: string[];
  humanGates: string[];
  summary: string;
}
```

Do not promote to beta just because tests/build pass; production readiness also needs device install, rollback, persistence/security, and audit evidence.

## UI Integration

PWA status/landing surface should show:
- all entries from the registry;
- the authority chain;
- current readiness grade/decision;
- current blockers;
- concise copy that mobile is a projection/handoff companion, not the canonical authority.

RN guide/details surface should show the same contract:
- current RN entry based on platform;
- authority chain;
- mobile write boundary;
- available operator entries;
- readiness state.

Keep this panel descriptive/diagnostic. The main interaction layer should remain a unified avatar/product experience, not a wall of architecture text.

## TDD / Verification Ladder

1. RED: add tests in each consuming app proving the package does not yet resolve and/or the expected entries are absent.
2. GREEN: add the shared package and workspace dependencies.
3. Add package-level tests:
   - all expected surfaces are present;
   - mobile entries cannot mutate canonical facts;
   - authority chain starts at the canonical server/agent source;
   - returned descriptors are defensive copies;
   - readiness gate blocks when any required gate is not verified.
4. Add PWA tests for rendering/consuming the entry contract.
5. Add RN shell tests for consuming the same contract.
6. Run the full workspace test and build, not only targeted tests.
7. Run native-shell lint/Jest separately if the native app is not a workspace package or has its own dependency tree.
8. Run production dependency audit for native package separately. If audit fixes imply semver-major/downgrade/native-framework churn, record it as an enterprise hardening gate rather than auto-applying a risky fix.
9. Update the project profile/ledger with only project-specific paths, timestamps, and current gate states.

## Pitfalls

1. Treating the entry registry as a new source of truth. It is a navigation/readiness contract only.
2. Letting mobile entries write canonical facts because the desktop/web operator entries can do so through governed gates.
3. Marking a local test/build landing as production beta. Device install, rollback, encrypted persistence, audit/readback, and dependency security are separate gates.
4. Forgetting that RN native packages can have a separate dependency tree and audit surface outside the root workspace.
5. Auto-running `npm audit fix --force` on RN packages. It may downgrade or semver-major-change React Native/CLI and break the app; record the hardening gate unless the task explicitly authorizes dependency migration.
6. Filling the primary avatar screen with architecture diagnostics. Put multi-entry/readiness details on secondary guide/status surfaces.
