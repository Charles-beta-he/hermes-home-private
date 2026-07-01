# Portfolio Ratchet Operating System

Scope: product/workflow sessions that touch more than one durable project, or where a user says project work should generalize across projects. Applicability: use after project profiles/SSOTs are discovered and before merge, abstraction, shared-module promotion, or portfolio-wide progress claims. Anti-condition: do not use this to mutate project code, copy secrets/auth/session state, or mark implementation progress without project-specific proof.

## Why this exists

A project is not a chat topic, repo, task list, or folder. Treat it as a governed capability system with:

1. objective/value model;
2. project profile;
3. progress ledger;
4. evidence/proof ledger;
5. task/backlog state;
6. typed relations to sibling/platform/integration projects;
7. evidence-gated promotion/demotion.

This prevents the “one-off chat” failure mode: useful decisions and progress vanish unless captured in durable project state.

## Objective model before landing

Success means every relevant durable project has:

- a project profile;
- `ssot_root`;
- `progress_ledger`;
- `project_type`;
- `relations` with `merge_policy`;
- `current_components`;
- `promotion_policy` using evidence-gated ratchet language;
- a read-only doctor/checker or equivalent validation path.

Cost function: minimize false production claims, secret/auth leakage, project fact pollution, and unnecessary user steering.

## Project relation types

Use typed relations instead of vague “merge”:

- `same_product_as`: candidates for full merge.
- `platform_for`: platform owns shared mechanism, vertical owns domain facts.
- `edge_runtime_of`: mobile/local runtime of a cloud/platform project.
- `integration_boundary_for`: auth/tool/API integration boundary; never merge secrets.
- `shares_module`: extract reusable procedure/code contract, keep facts scoped.
- `supersedes`: successor replaces prior project, old proof remains searchable.
- `sibling`: related domain family, distinct users/authority.
- `evidence_for`: proof informs another project without state merge.
- `governed_by`: portfolio governance controls metadata/ledger only.

## Merge gate

Full merge is allowed only if all are true:

1. profiles for both projects are readable;
2. objectives/non-goals match;
3. fact authority does not conflict;
4. secret/auth/runtime state will not be copied;
5. progress/proof ledgers are preserved with provenance;
6. a rollback path exists;
7. the merged capability has a new SSOT and acceptance matrix.

If any item fails, do not merge. Add a typed relation or extract a shared module instead.

## Casual-chat project uplift policy

Casual conversation can and should improve projects, but it must land at the right status level.

- If it is only an idea or weak signal: keep in conversation or ask later.
- If it improves direction but has no proof: write as `proposal`, `candidate`, or `needs-evidence` in a ledger/decision log/experience atom.
- If it creates a verified artifact or governance state change: update ledger/profile and read back/doctor it.

Never auto-mark implementation `done`, `validated`, `promoted`, or `production-ready` from discussion alone.

## Metadata-only code guard

When the user authorizes portfolio governance but forbids code changes for a named project, encode the boundary in that project profile and keep writes to metadata/ledger paths only. A doctor should verify the guard exists. Do not touch the project repo/code unless explicit project-code authorization is later given.

## Doctor checklist

A portfolio doctor should be read-only and check:

- all project profile JSON parses;
- required profile fields exist;
- `ssot_root` exists;
- `progress_ledger` exists;
- relation targets resolve to known profiles;
- relation entries include merge policies;
- promotion policy includes evidence-gated ratchet semantics;
- project-specific code guards are present where requested.

## Experience-ratchet handoff

When a portfolio rule appears reusable across projects, create an experience atom or proposal with:

- claim;
- applicability;
- anti-condition;
- falsifier;
- evidence refs;
- landing zone.

Do not immediately promote a single-project correction into a global skill unless abstraction-governance passes.

## Common pitfalls

1. **Metadata as implementation trap**: portfolio ledgers prove governance exists, not that product implementation is done.
2. **False merge trap**: sharing infrastructure or UI patterns does not justify merging business facts, auth state, or release lifecycles.
3. **Chat insight loss**: valuable casual discussion should become a proposal/signal, not disappear.
4. **Over-promotion trap**: a proposal with no proof must not become `validated` or `promoted`.
5. **Code-boundary violation**: portfolio governance may update profiles/ledgers while explicitly not touching project code.

## Verification evidence pattern

Report completion with concrete evidence:

```text
- doctor: ok true, N profiles, 0 errors, 0 warnings
- JSON validation: ok
- ledgers found: N/N
- guarded project: metadata/profile/ledger only; no project code touched
- experience atoms/proposals: ids + validation result
```
