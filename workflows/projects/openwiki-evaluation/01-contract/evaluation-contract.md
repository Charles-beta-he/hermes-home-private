# OpenWiki Evaluation Contract

## Objective

Determine whether OpenWiki should be adopted as an optional Hermes workflow for repo-local agent documentation.

## Non-goals

- Do not replace Hermes project profiles, progress ledgers, taskpool evidence, or skills.
- Do not enable scheduled CI writes before a pilot pass.
- Do not auto-merge generated docs.
- Do not let generated docs override source/readback evidence.

## Candidate path

1. Select one low-risk, non-protected pilot repository.
2. Run OpenWiki locally with explicit provider/key boundary.
3. Review only the resulting git diff.
4. Score generated docs against the decision task gates.
5. If accepted, document a reversible workflow/skill; if rejected, keep the intake as evidence only.

## Hard gates

Accept only if all are true:

- `openwiki/quickstart.md` is accurate enough to reduce initial repo discovery time.
- It names real source files, entrypoints, commands, and tests.
- It does not expose secrets or read `.env` values.
- It does not corrupt or overtake existing `AGENTS.md` / `CLAUDE.md` instructions.
- It avoids thin page sprawl and hallucinated business rules.
- `--update` either makes surgical changes or no-ops when current.
- Future CI mode is PR-only and review-gated.

Reject or keep experimental if any are true:

- It invents architecture/business facts not found in source/docs/git evidence.
- It generates noisy generic docs that increase review burden.
- It mishandles monorepo boundaries, binary/text classification, or protected paths.
- It requires unsafe credential/storage practices.

## Required evidence for decision

- Target repo path and git status before run.
- OpenWiki command and provider/model used, with secrets redacted.
- Git diff after run.
- `verify_openwiki_pilot.py` report.
- Manual spot-check notes mapping at least five material claims to source files.
