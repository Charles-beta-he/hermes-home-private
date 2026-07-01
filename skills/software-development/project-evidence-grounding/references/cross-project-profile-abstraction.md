# Cross-project profile abstraction without fact leakage

Use when one mature project profile appears richer than another and the user asks whether it can improve the target profile.

## Pattern

Migrate governance shape, not project facts.

A mature profile may contain reusable structures such as:

- source/evidence weighting policy
- profile import preflight and redaction rules
- task execution classification
- domain dispatch/router policy
- acceptance-level taxonomy
- forbidden patterns / red lines
- branch and release role gates

But its project-specific content must not be copied into the target profile unless independently verified in the target project:

- business domains and PRD claims
- repo paths, branch names, remotes, deployment providers
- commands, package managers, language/runtime versions
- backend/fullstack assumptions
- credentials, URLs, screenshots, task IDs, branch/commit IDs

## Procedure

1. Read both profiles and compare top-level keys plus sizes.
2. Classify each richer source section:
   - reusable governance shape
   - source-project fact
   - source-project procedure that might be adapted
   - sensitive/private material
   - stale/session-local progress
3. For each reusable shape, rewrite it in the target project’s vocabulary:
   - target source order
   - target repo roles
   - target reference implementation boundary
   - target verification ladder
   - target anti-conditions
4. Explicitly record what was not migrated.
5. Re-parse the target profile and run the project/portfolio doctor if available.

## Example transformation

Source profile has a fullstack default policy. Target project is a web frontend with a read-only native reference repo.

Do not copy “default fullstack-integrated”. Rewrite as:

- primary target: web frontend
- reference repo: read-only capability/parity source
- backend/API contract checks only when endpoint semantics are touched
- native/runtime parity proof must be labeled separately from static reference reading

## Landing zones

- Target project-specific rewritten policy -> target project profile.
- Reusable class-level procedure -> this skill or a reference file.
- Stable user preference -> memory/user profile.
- Concrete follow-up work -> taskpool/project ledger, not skill.

## Pitfalls

- Copying source-project business maps into the target profile because the structure looked useful.
- Treating another project’s release branch names or test commands as default branch policy for the target.
- Importing fullstack assumptions into a project whose authoritative target is only one repo plus a reference implementation.
- Failing to state evidence tier and anti-conditions, causing advisory maps to be reused as authoritative facts later.
