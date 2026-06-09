# Multi-repo sync and decomposed self-checks

Use this pattern after syncing a frontend/backend/admin style project with multiple repositories.

## Safe sync verification sequence

1. Inspect each repo before pulling:
   - `git status --short --branch`
   - `git remote -v`
   - `git rev-parse --abbrev-ref --symbolic-full-name @{u}`
2. `git fetch --all --prune` before deciding how to sync.
3. If the tracked upstream is gone, do not keep pulling blindly. First compare local branch against the likely surviving remote target with:
   - `git branch -vv`
   - `git rev-list --left-right --count HEAD...origin/<candidate>`
4. Rebind the upstream only after confirming the surviving target is the correct continuation branch, then fast-forward with `git pull --ff-only`.
5. Re-check `git status --short --branch` after syncing all repos.

## Decomposed self-check strategy

When a project has an umbrella verification script, do not stop at the top-level pass/fail result. Break the check into its stage commands and verify them independently.

Recommended order:

- dependency install (`pnpm install --frozen-lockfile`, `npm ci`)
- unit/integration tests
- production build
- backend compile / module test
- backend boot health check
- full-stack wrapper script last, as an orchestrator check

This separates code regressions from environment/runtime blockers.

## Common false-negative pattern from full-stack wrappers

A full-stack wrapper can fail even when compile and tests pass, because the boot stage depends on runtime services such as MySQL/Redis.

Interpretation rule:
- If backend compile and targeted backend tests pass, but boot health fails, classify the failure as a runtime boot blocker until logs prove otherwise.
- Read the wrapper log immediately instead of assuming the whole repository is broken.

Example blockers to distinguish:
- application packaging/repackage failure during install
- main-class ambiguity in Spring Boot repackage
- database handshake / connection loss during `spring-boot:run`

## Spring Boot packaging pitfall

`mvn -pl app/uvisa-app -am -DskipTests install` can fail in the `spring-boot-maven-plugin:repackage` phase even when `clean compile` succeeds.

Diagnostic split:
- `mvn -pl app/uvisa-app -am clean -DskipTests compile` -> proves source compiles
- `mvn -pl api/api-public -am test -q` -> proves targeted backend tests still pass
- `mvn -pl app/uvisa-app -am -DskipTests install` -> surfaces packaging/repackage-only failures
- `mvn -pl app/uvisa-app spring-boot:run -DskipTests -q` -> surfaces runtime dependency failures

Treat these as distinct layers; do not collapse them into a single generic "build failed" statement.

## Reporting guidance

For each repo, report separately:
- dependency update result
- test result
- build result
- boot/runtime result if applicable
- whether the working tree stayed clean

This gives the user a deployability picture instead of a single red/green answer.
