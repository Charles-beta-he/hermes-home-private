# Fact-source merge for split implementation lines

Scope: class-level project-evidence pattern for durable projects whose profile/ledger, SSOT docs, older proof-slice implementation, and newer product repo disagree. This reference is not a project status record; concrete paths from a session belong in the affected project profile/ledger.

Applicability:
- User suspects multiple truth sources, duplicate app versions, or conflicting project progress.
- A project profile says one path/status, while another repo/doc has newer tested implementation.
- Runtime code has demo/sample/fixture data that could be treated as production evidence.
- A mobile/PWA/native projection cache is involved and the client must not become authority.

Anti-conditions:
- Do not use this to merge secrets, OAuth state, raw session DBs, raw screenshots, or unreviewed user data.
- Do not call a repo primary unless current tests/build/readback prove it.
- Do not mark production/release status merely because a repo has tests; keep device install, signing, auth, and certification gates explicit.
- Do not erase older validated slices; demote them to historical/bootstrap evidence unless the user explicitly asks to delete/archive.

## Procedure

1. Build the source map:
   - canonical project profile;
   - progress ledger / SSOT docs;
   - current implementation repos/apps/packages;
   - runtime data sources, fixture/demo seeds, projection caches, and gateway/exporter boundaries;
   - taskpool/lifecycle/certification state if closure is involved.
2. Decide authority, implementation, and projection separately:
   - authority: canonical system of record;
   - implementation source: repo/path that currently owns product code and passes verification;
   - projection/cache: synced read-only copy, never authority;
   - local client state: drafts, queue, local UI/thread state, selected OCR/screenshots, or equivalent.
3. Patch runtime first if demo data can masquerade as facts:
   - production paths must not implicitly import/use sample/demo/canned fact data;
   - require explicit projection/sync payload or explicit demo flag;
   - fail closed to refusal/handoff/empty evidence when projection is absent;
   - add a regression test named in production terms, e.g. “does not use demo data without explicit projection”.
4. Patch durable truth surfaces:
   - profile: add implementation repo/source, canonical implementation statement, fact-source merge policy, component status, and remaining gates;
   - ledger: append authority chain, current implementation source, demoted legacy slices, code boundary, verification commands, and remaining gates;
   - repo docs/ADR: record the same boundary locally so future code work does not reintroduce split truth.
5. Verify:
   - profile JSON parses;
   - focused tests covering the runtime guard pass;
   - repo/workspace tests and builds pass where scripts exist;
   - changed profile/ledger/doc snippets read back;
   - portfolio doctor runs if portfolio metadata changed, with unrelated project failures classified separately.

## Reporting pattern

Report three layers separately:
- Authority source — where facts are allowed to originate.
- Primary implementation source — where code now lives.
- Historical/bootstrap evidence — older slices retained for proof but no longer primary.

Then list verification commands and boundary stops. If the repository is not a git repo or has unrelated dirty state, say no scoped commit was possible rather than inventing a commit boundary.

## Pitfalls

- Treating demo/sample cards as harmless because tests use them; if production imports them by default, they are a second fact source.
- Updating only the project profile but not the runtime guard; the next app run can still answer from stale fixtures.
- Updating only repo docs but not the profile/ledger; future portfolio/status reads will resurrect the old path.
- Calling Gateway/cache a source of truth. It is a projection/sync boundary unless explicitly promoted by a governed authority decision.
- Letting “native build exists” imply “device-ready”; signing/team/install and real device proof remain separate gates.
