# Vercel Monorepo Reference Review for Hermes Self-Optimization

Source: https://github.com/vercel/vercel
Reviewed commit: `13186826be714430f3e237e76d8127d811826f0a`
Local clone: `/Users/charles/.hermes/runs/vercel-reference-review-20260526-011817/repo`
Scope: static architecture review only; no credentials, deployments, or remote Vercel mutations were executed.

## Why this repository matters

Vercel is a mature agent-facing, CLI-heavy monorepo that combines:

- many public runtime/builder packages under `packages/*`;
- internal shared packages under `internals/*`;
- framework examples and fixtures used as integration tests;
- root-level agent instructions in `AGENTS.md`;
- deterministic build/test command surfaces in `package.json` and `turbo.json`;
- changeset-based release accounting;
- an error-documentation catalog under `errors/`;
- a bundled `skills/vercel-cli` skill with a decision tree and anti-patterns.

This maps well to Hermes because Hermes also has a large CLI, runtime adapters, gateway/platform adapters, skills, plugins, local scripts, test fixtures, profiles, and private overlays.

## Evidence highlights

1. Agent instructions are first-class.
   - `AGENTS.md` documents repo structure, essential commands, changeset rules, runtime package API shape, CLI local-development workflow, and pitfalls.
   - Hermes root `AGENTS.md` was only seven lines before this review, so future agents lacked a local equivalent of Vercel's repository contract.

2. Test surfaces are named by intent.
   - Root scripts split `build`, `type-check`, `lint`, `test-unit`, `test-cli`, `test-e2e`, and package-scoped test flows.
   - `turbo.json` models task dependencies and cache outputs explicitly.
   - Hermes should preserve a similar habit: every self-change must name the targeted verification surface rather than saying merely "tested".

3. Affected testing is automated but fail-safe.
   - `utils/get-affected-packages.js` queries Turbo's graph, selects changed package dependents, but falls back to testing all packages if base SHA or graph data is missing.
   - Infrastructure/config/shared test-lib changes force broad e2e coverage.
   - Hermes should keep its existing fail-closed behavior, but make the "impact class -> verification command" mapping explicit in local docs/skills.

4. Fixtures/examples are protected artifacts.
   - `biome.jsonc` and `vitest.config.mts` deliberately exclude fixture trees that contain intentionally broken or special files.
   - `AGENTS.md` warns not to modify examples for testing because they are integration fixtures.
   - Hermes skills, brain fixtures, browser-harness evidence, and taskpool examples should be treated the same way: test against fixtures, do not mutate them casually.

5. Release accounting is mandatory.
   - Vercel requires a changeset for every PR, even with empty frontmatter for non-package changes.
   - Hermes private workflow already relies on scoped git commits; the transferable rule is not Changesets itself, but "every self-change has an auditable release/evidence note".

6. Errors are documented as user-facing playbooks.
   - `errors/*.md` explains specific failure modes and how to fix them.
   - Hermes already has scattered references; a stronger pattern is to promote recurring incidents into small named error/playbook docs and link them from the relevant skill.

7. Local CLI can be tested against external projects.
   - Vercel supports `pnpm vercel --cwd /path/to/external/repo`.
   - Hermes already supports project workdir/profile context in cron and tool calls. The transferable rule is to keep local Hermes CLI/dev commands runnable against external repos without installing or mutating the target.

## Hermes changes made from this review

1. Expanded `/Users/charles/.hermes/AGENTS.md` from a terse constitution into a Vercel-style local contract:
   - structure map;
   - essential validation commands;
   - scoped commit discipline;
   - reference-repo review protocol;
   - impact-to-verification mapping;
   - fixture/evidence protection;
   - common pitfalls.

2. Added this review file as durable evidence under `docs/private/`.

3. Patched `hermes-agent` skill to point at this reference and to encode the reusable reference-architecture review workflow.

## Transferable optimization backlog

P1 — keep immediately:
- Maintain root `AGENTS.md` as the canonical fast path for future agents.
- For Hermes self-changes, always report changed files + exact verification commands + scoped commit hash.
- Classify changes as docs/skill, scripts, core agent loop, gateway/platform, taskpool/brain, or config/profile before choosing tests.

P2 — next implementation candidate:
- Add a small `~/.hermes/scripts/hermes_affected_checks.py` that maps changed paths to commands, inspired by Vercel's affected-package selector but suited to Hermes:
  - `skills/**` -> skill index/lint smoke;
  - `scripts/**` -> `py_compile` + matching `test_*.py` when present;
  - `brains/**` -> `brainctl --json brains validate` + targeted route;
  - `hermes-agent/**` -> repo-local pytest by path class;
  - infra/shared config -> broader `p10-health` / doctor.
- The script must fail open to broader tests, not narrower tests, when unsure.

P3 — optional governance improvement:
- Add a local `docs/private/changes/` convention for non-code self-changes, analogous to empty changesets: one small markdown note for notable skill/brain/governance changes that do not touch Hermes core code.

## Anti-patterns to avoid

- Do not import Vercel's Node/Turbo/Changesets stack into Hermes just because Vercel uses it; only the governance pattern transfers.
- Do not treat examples/fixtures/evidence files as scratchpads.
- Do not run integration/deployment commands from the reference repository; static analysis is enough unless the user explicitly asks for Vercel operations.
- Do not store Vercel private access material in notes; any access examples must remain placeholders.
