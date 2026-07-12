# Progress Ledger — openwiki-evaluation

Created: 2026-07-07T16:18:23+08:00
Status: contract-ready / pilot-not-started

## Current truth

- OpenWiki upstream was researched and locally smoke-verified as a candidate repo-local agent documentation generator.
- This project is an evaluation track only. It does not authorize CI, auto-merge, protected work repo rollout, or generated-doc-as-truth promotion.
- Canonical intake: `00-intake/openwiki-upstream-intake.md`.
- Evaluation contract: `01-contract/evaluation-contract.md`.
- Reserved decision task: `02-tasks/openwiki-pilot-adoption-decision.json`.
- Pilot verifier: `04-scripts/verify_openwiki_pilot.py`.

## Component states

- upstream_research: validated-local-smoke, evidence `03-evidence/openwiki-upstream-research-20260707T161823+0800.json`
- adoption_contract: contract-ready
- pilot_selection: blocked-awaiting-target-repo
- ci_adoption: closed-until-pilot-pass
- taskpool_projection: reserved-local-task-file-only

## Next safe step

Choose one low-risk, non-protected pilot repository, run OpenWiki locally, review diff, run `04-scripts/verify_openwiki_pilot.py <repo> --json`, and write a decision note under `05-decisions/`.

## Gates

- No UVISA/UAEC/protected work repo without explicit context switch.
- No credentials committed or displayed.
- No scheduled CI write until pilot decision passes.
- No completion claim without diff + verifier + manual source-claim spot checks.
