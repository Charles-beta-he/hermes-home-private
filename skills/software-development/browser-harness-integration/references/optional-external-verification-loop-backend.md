# Optional External Verification-Loop Backend Pattern

Scope: class-level browser/API verification governance for Hermes-style agents. Applicability: use when a browser/API verification workflow needs an agent-consumable failure bundle, a resumable run contract, or an optional external verification backend. Anti-conditions: do not use this pattern to default-enable any third-party service, upload private app pages, bypass local project tests, replace TDD, or treat dry-run/sample data as acceptance evidence.

## Core transferable pattern

Some external verification CLIs demonstrate a useful loop that can be implemented locally first:

1. Create or select a behavior test.
2. Run it against a real target surface to a terminal verdict.
3. On failure, fetch one self-consistent failure bundle.
4. Feed that bundle back to the coding agent.
5. Fix, redeploy/restart as needed, then rerun the same behavior.
6. Bank the passing test/evidence into a durable suite or ledger.

For Hermes, the default backend should remain local Playwright/browser-harness/real backend evidence. External cloud verification is an optional backend only after explicit project authorization.

## Failure bundle shape to emulate locally

A good browser-harness failure bundle should include:

- `schema_version`
- `run_id` and/or `snapshot_id`
- `task_id` / `test_id` / `project_id`
- `code_ref` / `commit` / `build_id` / `code_version` when available
- `target_url`
- `target_surface`: route, active tab/filter/modal, viewport, device, theme, locale
- `auth_mode` and `backend_mode` (`real`, `mocked-auth developer check`, `mock-server non-acceptance`, etc.)
- `command` and exact environment used
- `status` and `exit_reason` (`passed`, `product_failed`, `blocked`, `auth_error`, `not_found`, `validation_error`, `conflict`, `timeout_resumable`, `rate_limited`, `insufficient_credits`, `infra`)
- `failed_step_index` / step list with neighboring steps
- artifact refs: screenshot, DOM/AX snapshot, console/pageerror/requestfailed log, network summary, storage assertions, video if present
- `root_cause_hypothesis` explicitly labeled as a hypothesis
- `recommended_fix_target` with file/route/component/service if grounded
- `redaction_summary`
- `bundle_hash`
- `.partial` or equivalent incomplete marker on failed capture

Integrity gate:
- Refuse to consume a bundle if `run_id` / `snapshot_id` / `code_ref` / `target_url` disagree across artifacts.
- Write artifacts atomically: temporary directory first, final metadata last.
- If capture fails mid-write, leave an explicit partial marker and mark the result unusable for closeout.

## External cloud backend boundaries

Do not run a third-party cloud verification backend by default.

Hard gates before using one on a real project:
- User/project explicitly authorizes the external service.
- Dedicated API key exists; do not type or store secrets yourself.
- Target URL is safe to expose to the service and publicly reachable, or the user has approved a local tunnel/MCP path.
- Test account/data are low sensitivity and disposable.
- Cost/credit/rate-limit expectations are known.
- The task accepts writing/updating external tests.
- The closeout clearly labels evidence as external-cloud verification, not local browser proof.

Never claim acceptance from:
- canned dry-run data;
- README/video benchmark claims;
- a run pointed at an old preview/staging deployment;
- external cloud evidence for pages that the project says must be verified locally or on device.

## How this maps to Hermes closeout

For Kanban/taskpool UI work, a closeout should reference the bundle path/hash, not just prose such as “browser verified.” Example metadata:

```json
{
  "verification_backend": "local_playwright",
  "evidence_bundle": "/tmp/project-scope/run-123/bundle.json",
  "bundle_hash": "sha256:...",
  "status": "failed",
  "exit_reason": "product_failed",
  "target_surface": "/card tab=transactions viewport=390x844",
  "auth_mode": "real_test_account",
  "backend_mode": "real_backend",
  "rerun_command": "node scripts/verify-card.js --run-id run-123"
}
```

If the run times out but remains resumable, store the run/job id and the resume command instead of collapsing it to a generic failure.

## Candidate landing order

1. Add/emit local failure bundle schema in browser-harness scripts.
2. Add fixture tests that intentionally create a screenshot/DOM/console failure and assert bundle integrity.
3. Teach taskpool/kanban closeout to preserve bundle path/hash and exit reason.
4. Only then consider an explicit external backend in a project profile, default off.
