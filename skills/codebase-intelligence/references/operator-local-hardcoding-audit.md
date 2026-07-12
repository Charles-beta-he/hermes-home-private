# Operator-local hardcoding audit and projection cleanup

Scope: class-level repository hygiene workflow for auditing portable application repositories and collaboration docs. Applicability: use when a repo may contain operator-local paths, private evidence roots, personal fixture names, deployment service identifiers, or project-specific authority facts. Anti-conditions: do not use this to preserve task progress, secrets, one-off incident narratives, or to rewrite historical evidence ledgers unless they are active bootstrap/runtime dependencies.

## Goal

Separate portable repository facts from scoped project runtime facts without destroying useful private context.

## Classify each match

1. Runtime code or production config
   - Highest risk. Remove personal paths, private hosts, hardcoded credentials, local-only service IDs, and personal fixture names unless explicitly required by a public contract.
   - Prefer environment variables, typed config, or project-profile lookup.

2. Active collaboration/agent workflow docs
   - Replace private absolute paths and environment-specific service names with indirection such as "resolve from active project profile / local checkout".
   - Keep the behavior rule portable; move the concrete local value to the scoped project profile.

3. Tests and fixtures
   - Replace personal-looking identifiers with neutral fixtures such as generic demo/test users unless the test intentionally verifies exact imported backend text.
   - Re-run the touched tests because fixture renames often require updating expectations in the same file.

4. Historical evidence ledgers, incident reports, old command transcripts
   - Do not bulk rewrite by default. These may be audit artifacts.
   - Only edit if the private value is an active secret, active workflow dependency, or current bootstrap rule. Otherwise report as historical/non-active residue.

5. Project profile / scoped private profile
   - Correct landing zone for concrete operator-local facts: checkout paths, workpad paths, private evidence roots, deployment service names, dashboard access notes, project-specific write authority.
   - Add scope/applicability/anti-conditions so future agents do not promote these facts to global memory or portable repo docs.

## Procedure

1. Search for local-machine and environment-specific patterns in source and docs:
   - absolute home paths, private profile paths, workpad/evidence roots;
   - local service identifiers and deployment project names;
   - personal usernames/emails in fixtures;
   - local backend/frontend URLs, localhost defaults in production config, private IP ranges.
2. Split findings by class above before editing.
3. For active docs, replace concrete local values with a project-profile resolution rule.
4. For concrete values that remain operationally useful, write them into the project profile or another explicitly scoped private profile.
5. For fixture-only personal names, rename to neutral fixtures and update assertions.
6. Verify:
   - JSON/YAML profile parses;
   - touched tests pass;
   - diff whitespace check passes;
   - repeat search shows no active bootstrap/runtime hits, while any remaining historical hits are explicitly classified.

## Pitfalls

- Do not move local facts into global memory; they become stale ghosts and leak across projects.
- Do not delete historical evidence just to make a grep clean.
- Do not replace all localhost mentions blindly: dev proxy defaults and browser-test base URLs may be intentional.
- Do not treat hosted prototype URLs as runtime backend evidence unless the scoped project profile says they are authoritative.
- Do not make a repo workflow depend on a private project profile unless it also has a collaboration fallback for agents without that profile.
