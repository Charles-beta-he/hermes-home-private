# Specialist Code Review CLI Reference Pattern

Scope: reusable code-review workflow design for Hermes verification gates. Applicability: use when an external specialist reviewer tool demonstrates a deterministic pipeline around model-based review. Anti-conditions: this reference does not authorize installing any package, sending private code to external LLM providers, entering API keys, or replacing project-specific tests and reviewer gates.

## Transferable Pattern

Do not treat code review as a free-form prompt over a raw diff. Make brittle steps deterministic and reserve the model for contextual reasoning.

### Deterministic review control plane

Before model review:

1. Build a coverage manifest:
   - changed files;
   - changed line ranges;
   - ignored/generated/vendor files with reasons;
   - required review units.
2. Bundle related files intentionally, not by accidental context-window order.
3. Attach rule packs by file kind/risk domain:
   - security;
   - money/funds movement;
   - auth/session;
   - UI/i18n/user-facing copy;
   - concurrency/state machine;
   - database/schema/migration.
4. Decide the review mode:
   - diff review;
   - full-file scan;
   - targeted high-risk gate;
   - CI-comment projection.

### Agent review layer

The reviewer should receive:

- exact review unit;
- changed-line manifest;
- relevant full-file context or search capability;
- risk-specific rubric;
- required output schema;
- explicit precision/recall stance.

Default Hermes stance: precision-biased for blocking findings; recall-biased only for advisory follow-ups or explicitly requested exhaustive audits.

### Position verifier

After model output:

- verify every file path exists in the reviewed tree;
- verify line numbers fall inside changed ranges or explicitly justified context lines;
- reject comments whose quoted code no longer matches the file;
- separate exact changed-line blockers from broad architecture observations.

### Reflection/filter pass

Before presenting or posting findings:

- remove duplicate findings;
- demote style/preferences unless the task requested them;
- fail closed on security/funds/auth/data-loss issues;
- require evidence citations for every blocker;
- include false-positive risk and confidence.

### CI integration gate

For automated posting/commenting, require a separate gate:

- dry-run output first;
- stable machine-readable JSON;
- idempotency key per finding;
- no duplicate comments on rerun;
- scoped token/permission boundary;
- post-action readback.

## Hermes Application

Use this reference to strengthen `requesting-code-review`:

- Add a deterministic coverage manifest for large/high-risk diffs.
- Add line-position verification before treating reviewer JSON as a blocker.
- Treat model comments without exact evidence as advisory.
- Keep any external reviewer CLI evaluation as a bounded spike, not a default dependency.

## Falsifier

If deterministic manifests and position verification add significant friction without reducing false positives, line-drift findings, or coverage gaps, narrow this pattern to high-risk or large diffs only.
