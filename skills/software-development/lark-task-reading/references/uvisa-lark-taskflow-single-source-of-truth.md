# UVISA Lark Task Flow — Single Source of Truth

This reference is the current canonical rule for 贺程's UVISA Lark/work task flow. When this conflicts with older notes about mandatory online UI retest before final Lark completion, this reference wins unless the user explicitly re-enables the old fail-closed UI-retetest gate for a specific batch/task.

## Current policy

1. Lark Task Center is the external source of truth for live task existence, owner, GUID, title, comments, and completion state.
2. Hermes local taskpool / envelope bus is the execution source of truth after intake:
   - taskpool brain note = lifecycle / dependency / owner / evidence policy
   - envelope bus = worker execution status and proof SHA
   - evidence directory = immutable closeout artifacts
3. For the current UVISA admin/work closeout mode, online UI retest is not a blocking phase for Lark final completion.
4. A Lark task can be closed when all of these are true:
   - the task is mapped to the correct Lark GUID and project surface;
   - implementation is merged or the current code is proven to already satisfy the task;
   - deterministic verification passes, at minimum `npm run build` for `uvisa-admin` tasks unless a stronger task-specific gate is required;
   - an evidence directory exists under `~/.hermes/evidence/envelopes/<envelope-id>/` with `closeout-summary.json`, build/test logs, PR URL or code-location proof, and `proof_sha`;
   - Lark receives a concise public-safe comment and `PATCH /task/v2/tasks/{guid}` sets `completed_at` successfully;
   - taskpool brain note and envelope state are synchronized to done.
5. Do not close Lark when the implementation is partial, wrong-scope, or only superficially changes the requested surface. Mark the envelope/task as `BLOCKED` with the concrete contract gap, and leave Lark open.

## Canonical execution order

1. Read live Lark tasks through the task v2 API / configured reader.
2. Filter to tasks owned by 贺程; do not treat follower/member-only presence as ownership.
3. Deduplicate by Lark GUID, URL, and normalized title.
4. Create/enrich one taskpool note per live task and one envelope per executable unit.
5. Before executing, classify:
   - point fix;
   - cross-cutting / infrastructure;
   - existing implementation + regression proof;
   - partial/blocked contract.
6. For `uvisa-admin` execution, use isolated worktrees under `.agent-team-worktrees/`, not the user's main working copy.
7. Implement on a shared task-loop branch, open/merge PR, then sync the worktree to the deployment/base branch before the next task.
8. Run deterministic verification. For admin tasks, the default gate is `npm run build` plus task-specific tests/static checks when relevant.
9. Write evidence under `~/.hermes/evidence/envelopes/<envelope-id>/`:
   - `closeout-summary.json`
   - `build.log` / test logs
   - `pr_url.txt` or code-location evidence
   - `diff.patch` when applicable
   - `proof_sha.txt`
10. Comment on Lark with a concise public-safe summary: what changed, PR/commit, verification result. Do not include `/Users/...`, `/tmp/...`, secrets, raw logs, or internal-only evidence paths.
11. Patch Lark task `completed_at` using task v2 shape: `{"task":{"completed_at":"<ms>"},"update_fields":["completed_at"]}`.
12. Mark envelope DONE with `proof_sha`; mark brain task done with structured evidence.
13. Notify TG after each batch or user-requested completion. If `telegram` has no home channel, retry `telegram:he cheng`; if that fails, report the notification blocker explicitly.

## Reopened / partial task rule

If post-closeout audit finds the task was not really satisfied:
- do not defend the old done state;
- create a corrective PR when the original PR was merged but wrong;
- if the contract is large or ambiguous, mark the envelope/task `BLOCKED` and keep Lark open;
- never close Lark from a partial PR just because build passed.

Known example:
- `ed84743a` / `24189dc0e210`: PR #156 only changed a title suffix for Debit 入金 and did not satisfy the full Debit inflow page contract. Correct handling is BLOCKED + Lark left open.

## Evidence hierarchy

For this UVISA admin/work mode:
1. Lark live API: external task truth.
2. Latest local prototype source: before using `/Users/charles/Desktop/folder/work/uvdemo2.0/uvisa-app` or `/Users/charles/Desktop/folder/work/uvdemo2.0/uvisa-admin` as a fallback for stripped Lark `[Image]` evidence, run `git -C /Users/charles/Desktop/folder/work/uvdemo2.0 fetch origin --prune` and, if the tree is clean, `git -C /Users/charles/Desktop/folder/work/uvdemo2.0 pull --ff-only origin main`; record the resulting commit SHA in task evidence. If the prototype tree is dirty or cannot fast-forward, treat prototype freshness as blocked and do not claim prototype parity from stale local files.
3. Merged PR / current code inspection: implementation truth.
4. `npm run build` and task-specific deterministic checks: verification truth.
5. `~/.hermes/evidence/envelopes/<id>/closeout-summary.json` + proof SHA: local closeout truth.
6. Brain task/envelope status: derived execution lifecycle; must be synchronized, but must not override missing implementation evidence.

## Scope of this override

This override applies to current UVISA admin/work Lark batches where the user has explicitly canceled separate online UI acceptance before Lark close.

It does not apply to:
- user explicitly requested online UI 回测;
- mobile H5 tasks requiring real mobile screenshots;
- backend/API/data-correctness tasks requiring real API/database equality proof;
- security/PII/payment tasks where task-specific verification must be stronger than build;
- any task where the user says final completion depends on production UI evidence.
