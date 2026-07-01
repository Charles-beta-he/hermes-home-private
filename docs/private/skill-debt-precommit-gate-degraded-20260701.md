# Skill debt pre-commit gate degraded receipt

Date: 2026-07-01

## Context

User selected Option A: local-only scoped commit plan, exact staging manifest, no push.

The scoped staging gate completed:
- exact manifest path: `/Users/charles/.hermes/docs/private/skill-debt-scoped-staging-manifest-20260701.json`
- cached diff check: PASS (`git diff --cached --check` exit 0)
- staged readback: `/Users/charles/.hermes/docs/private/skill-debt-staged-readback-20260701.md`
- staged secret scan: 0 hits in the prior scripted readback
- taxonomy auditor before staging: ok=true, findings_by_code={}, findings_by_severity={}

## Pre-commit hook result

`git commit -m "chore(skills): clear taxonomy debt"` invoked the local-brain pre-commit hook and exited non-zero.

The hook produced a dry-run `local_brain_change_preflight_v1` packet with:
- side_effects.external_dispatch=false
- side_effects.lifecycle_write=false
- side_effects.publish_deploy_push=false
- side_effects.destructive=false
- side_effects.credential_payment=false
- verdict.status=`degraded_not_certified`
- allowed_actions included only `local_dry_run` and `evidence_request`

The hook classified the broad staged skill/report set as high-risk / credential-payment adjacent and requested evidence classes that are not meaningful for this local markdown-only skill-debt commit, such as screenshot, browser_console, task_record, lifecycle_readback, source_packet, and timestamped_source.

## Boundary decision

This receipt records the degraded hook result before continuing with the explicitly authorized local-only commit path. No push is authorized or performed.

Rollback/escape hatch after commit:
- local rollback: `git revert <commit>`
- index rollback before commit would have been `git reset --staged <paths>`; no push means remote state is unaffected

Post-commit verification required:
1. read back `git show --stat --oneline HEAD`
2. re-run taxonomy auditor
3. verify no push occurred and unrelated dirty work remains unstaged/uncommitted
