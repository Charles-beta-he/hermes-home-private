# Hermes Local Constitution

Policy: proof gates, scoped self-changes, no arbitrary command execution, fail-closed default.

## Core paths

- Active Hermes home: `/Users/charles/.hermes`
- Hermes source checkout: `/Users/charles/.hermes/hermes-agent`
- User/private skills: `/Users/charles/.hermes/skills`
- Local scripts: `/Users/charles/.hermes/scripts`
- Project profiles: `/Users/charles/.hermes/project-profiles`
- Brain/control-plane notes: `/Users/charles/Documents/brain`
- Private governance docs: `/Users/charles/.hermes/docs/private`

## Essential commands

Use targeted commands first, then broaden when impact is unclear.

```bash
hermes --version
git -C ~/.hermes status --short
git -C ~/.hermes/hermes-agent status --short --branch
python3 ~/.hermes/scripts/post-update-check.py --fix
python3 ~/.hermes/scripts/brainctl.py --json brains validate
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
~/.hermes/scripts/p10-health.sh
```

For Hermes source-code changes inside `~/.hermes/hermes-agent`, prefer repo-local commands from that checkout and its venv:

```bash
cd ~/.hermes/hermes-agent
./venv/bin/python -m pytest <focused tests>
./scripts/run_tests.sh <focused tests or suite selector>
```

## Scoped commit rule

Hermes self-modifications must be auditable.

1. Inspect status before editing.
2. Avoid staging unrelated runtime/config/log changes already present in `~/.hermes`.
3. Stage only files touched for the current request.
4. Commit with a scoped message after validation.
5. Report changed files, verification commands, and commit hash.
6. Do not push unless the user explicitly asks or the current Hermes maintenance task clearly requires publishing the private branch.

## Reference-repo analysis protocol

When the user asks to analyze an external repo to improve Hermes itself:

1. Clone/read the reference repo in `~/.hermes/runs/<repo>-reference-review-*`.
2. Read its agent/developer instructions first (`AGENTS.md`, `CLAUDE.md`, README, package manifests, CI/build config).
3. Extract transferable patterns, not stack-specific cargo culting.
4. Map each pattern to Hermes impact classes:
   - docs/skills/governance;
   - local scripts;
   - core agent loop;
   - tool/gateway/platform adapters;
   - taskpool/brain/control-plane;
   - tests/evidence fixtures.
5. Implement only low-risk, scoped improvements immediately unless deeper code changes are clearly required.
6. Write a durable review note under `docs/private/` when the reference repo yields reusable self-optimization guidance.

## Impact-to-verification mapping

- `skills/**`: reload/read the skill and patch only the targeted skill file; verify formatting and references.
- `brains/**`: run `brainctl --json brains validate`; add a targeted `brainctl --json brains route '<example>'` smoke when routing changes.
- `scripts/**`: run `python3 -m py_compile` on changed scripts and matching `scripts/test_*.py` when available.
- `hermes-agent/**`: use focused pytest in the source checkout; include `post-update-check.py --fix` if vendor/local overlay behavior is involved.
- `project-profiles/**`: read the affected profile and any referenced Workpad/boot context; verify JSON syntax.
- `cron/jobs.json` or hooks: list/inspect job/hook state before and after; avoid recursive cron scheduling.
- config/profile changes: run the exact CLI command that consumes the changed config path.

If impact is ambiguous, broaden verification rather than narrowing it.

## Fixture and evidence protection

- Treat examples, fixtures, evidence bundles, screenshots, and historical taskpool logs as test artifacts, not scratchpads.
- Do not mutate fixture/evidence files just to make a test easier unless the user asked to update that artifact and verification covers the consumer.
- Prefer creating new evidence under a request-specific directory or `docs/private/` review note.

## Common pitfalls

- `hermes update` can overwrite local overlays; always run `post-update-check.py --fix` before declaring the update healthy.
- A clean exit code is not enough if a post-update summary contains `FIX_FAILED`; read the summary.
- Brain markdown and kanban DB can diverge; verify both when task lifecycle state matters.
- Do not treat model consensus as evidence without claim-linked artifacts.
- Keep private access material out of docs, memories, skills, and task notes; use placeholders only.
