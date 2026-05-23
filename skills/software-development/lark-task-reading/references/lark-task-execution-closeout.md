# Lark task execution closeout pattern

Use this when a Lark Task Center item is not only read but implemented and reported back.

## Why this exists

A common failure mode is to finish the code and deterministic verification, then spend the remaining tool/context budget on increasingly detailed documentation updates. That can leave the actual task unfinished because there is no scoped commit and no requested user/TG notification.

For Lark-assigned work, the user-visible delivery unit is:

`task selected -> implemented -> verified -> evidence summarized -> scoped commit -> notification/report`

Docs and ledgers support the delivery; they do not replace commit/report.

## Branch preflight before local implementation

Local acceptance and online UI acceptance are separate phases, so local fixes must not be made directly on the deployment/base branch.

Before editing a UVISA/Lark task repo:

```bash
git fetch origin --prune
git branch --show-current
```

- If the current branch is `main`/`master`/the configured deployment base, stop before editing.
- After an online PR is merged, GitHub may delete the remote task branch and the local checkout often returns to `main`; treat that as expected and create/check out the next shared task-loop branch from the freshly fetched base.
- Preferred pattern:
  ```bash
  git checkout main
  git pull --ff-only origin main
  git checkout -B lark-task-loop/<scope-or-date>
  ```
  Use the project’s configured deployment branch if it is not `main`.
- If an existing task-loop branch is still active, fetch/rebase it onto the latest `origin/main` before the next local fix instead of stacking on a stale pre-merge commit.
- Machine-check the branch gate when preparing implementation evidence:
  ```bash
  python3 ~/.hermes/scripts/lark_task_closeout_guard.py \
    --phase implementation \
    --repo-path <project-root> \
    --base-branch main \
    --json
  ```
  `implementation_branch_gate.allowed` must be true before local code edits. This does not allow Lark `completed_at`; it only proves the local-fix branch is safe.

## Closeout sequence

After implementation and tests pass:

1. Create or update a concise evidence artifact.
   - Include task id/title, approach, changed files, commands, pass/fail result, residual risk.
   - Prefer a compact `/tmp/<project>-<task>-<date>.md` note when the task does not need a permanent ADR.
   - Do not store OTP values, tokens, screenshots with secrets, or disposable credentials in repo docs.

2. Minimal project ledger update.
   - Update the primary task/test ledger row that future maintainers will search.
   - Avoid broad rewrites or reordering historical evidence rows.
   - If a patch accidentally replaces historical evidence, restore it immediately before continuing.

3. Pre-commit sanity.
   ```bash
   git status --short
   git diff --check
   ```
   Add a targeted lint/test rerun only if docs/code changed after the last verification.

4. Scoped commit.
   ```bash
   git add <exact task files>
   git status --short -- <exact task files>
   git commit -m "fix(scope): concise task summary"
   git log -1 --oneline
   git status --short
   ```
   Never rely on `git add .` in a dirty worktree.

5. Local-close first; remote acceptance only when requested.
   - Default UVISA/Lark flow: complete local acceptance and scoped commit first.
   - Do not run remote deployment/package monitoring or remote acceptance proactively unless the user explicitly initiates it.
   - When remote acceptance is deferred by user preference, report `local_closed_remote_deferred_by_user`, not `fully_remote_closed`.
   - Do not post the final evidence comment to the Lark task while remote acceptance is still deferred.
   - If the user later asks for remote acceptance, inspect the relevant service deployment/package/build then, record terminal `success`/`healthy` status, and use `references/remote-package-monitor-closeout.md` for status vocabulary and redaction rules.

6. Evidence comment / user report.
   - Post complete evidence to the Lark task comment area only after remote acceptance has completed, when comment write permission is available.
   - Include task id/title, commit hash, changed files, local verification commands/results, remote acceptance result, screenshot/evidence path, and residual risk.
   - If remote acceptance is not yet requested/completed, report locally to the user only and keep the Lark comment pending.
   - If Lark comment writeback fails after remote acceptance, report the exact blocker and provide the comment text for manual paste.
   - Do not include OTP values, tokens, passwords, screenshots with secrets, or disposable credentials.

7. Continue loop.
   Move to the next visible/assigned Lark task after local acceptance and scoped commit. If remote acceptance is deferred by user preference, Lark evidence-comment closure remains pending until the user initiates remote acceptance.

## Budget rule

When context/tool-call budget is low, skip optional extra docs and close the delivery first:

`tests passed -> evidence note -> git diff --check -> commit -> remote package/deploy monitor -> notify`

If interrupted before commit or notify, the final answer must state:

- commit not done, or notification not sent;
- exact files currently modified;
- exact verification already passed;
- exact next commands to resume.

Do not say the Lark task is completed merely because tests/build passed.

### Long-runner / browser-auth budget pitfall

A recurring failure mode is to start a saved multi-model discussion in the background, then continue implementation, full tests, build, dev-server startup, and browser exploration until the session reaches its tool-call ceiling before commit/TG closeout. Avoid this by checking closeout budget before every expensive side lane:

- If `consult_models.py --discussion` is started, reserve tool calls to poll/read the tick artifact. Until `discussion_result.json` is read and passes, the status is `started/no_ratification_artifact` or advisory only.
- Do not start a fresh long T2/T3 discussion after deterministic gates pass if there is not enough budget left for commit and notification.
- If browser verification lands on login because `/notifications` or another task route is auth-protected, immediately choose one of two bounded paths: use the documented project test-login/OTP workflow to establish state, or mark browser UI acceptance as unfinished. Do not spend repeated clicks/probes on the login page unless those clicks are the documented login flow.
- For tasks with requested TG reporting, notification is a closeout gate. Reserve it before optional Workpad/ledger/UI polish.
- For deployed tasks, remote package/deploy monitoring is also a closeout gate. A public app smoke can be useful evidence, but dashboard/package status blocked by login must be labeled `access_blocked_needs_login`, not silently treated as success.
- If live Lark read/writeback fails with `TOKEN_EXPIRED` during closeout, treat OAuth recovery as its own budgeted gate: start `lark-mcp login --domain https://open.larksuite.com --port 3010 ...`, immediately open/authorize `http://localhost:3010/authorize`, then rerun the reader before writing back. Do not start OAuth recovery at the very end of a tool budget and then imply Lark closeout succeeded; report `lark_writeback_blocked_token_expired` if authorization cannot be completed and verified in-session.

Example: a notification-detail task had TDD, full tests, and build green, but got interrupted before reading the background multi-model verdict, completing auth-gated browser verification, committing, and TG notification. The correct final state is “implementation verified but closeout incomplete,” not “task done.”

## Auth/i18n bug-fix example pattern

For an auth verification-code localization task, a robust boundary is:

- Preserve backend machine-readable `code` at the API envelope adapter.
- Normalize only auth-domain OTP/code/rate-limit failures to i18n keys in the auth store/domain layer.
- Do not globally translate every API error.
- Do not translate only in screen toast components.
- Keep unknown backend business messages raw so customer-service/account-opening guidance is not lost.
- Test both response-body business failures and rejected axios error payloads.
