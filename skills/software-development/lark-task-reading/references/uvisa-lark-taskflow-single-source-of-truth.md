# UVISA Lark Task Flow — Single Source of Truth

This reference is the current canonical rule for 贺程's UVISA Lark/work task flow. For `uvisa-app-2.0`, because the project has an online address and a complete publishing flow, Lark final completion must wait for online-address UI 回收/验收 evidence. Code merge/current-code proof plus deterministic verification is only an implementation-sendback gate and must not close Lark by itself.

## Current policy

1. Lark Task Center is the external source of truth for live task existence, owner, GUID, title, comments, and completion state.
2. Hermes local taskpool / envelope bus is the execution source of truth after intake:
   - taskpool brain note = lifecycle / dependency / owner / evidence policy
   - envelope bus = worker execution status and proof SHA
   - evidence directory = immutable closeout artifacts
3. For `uvisa-app-2.0`, online-address UI 回收/验收 is a blocking phase before Lark final completion. This prevents the logic funnel where locally implemented or merged code is marked complete before the published online UI proves the task surface.
4. Implementation merge/current-code proof plus deterministic verification can move a task to implementation-sendback / online UI 回收 pending, but it must not set Lark `completed_at`.
5. A Lark task can be closed only when all of these are true:
   - the task is mapped to the correct Lark GUID and project surface;
   - implementation is merged or the current code is proven to already satisfy the task;
   - deterministic verification passes, at minimum `npm run build` for `uvisa-admin` tasks unless a stronger task-specific gate is required;
   - for `uvisa-app-2.0`, the relevant release/publishing flow has completed and the online address has been checked;
   - online-address UI 回收/验收 evidence proves the exact task surface and acceptance atoms using the real online environment;
   - an evidence directory exists under `~/.hermes/evidence/envelopes/<envelope-id>/` with `closeout-summary.json`, build/test logs, PR URL or code-location proof, online UI evidence, and `proof_sha`;
   - Lark receives a concise public-safe final comment and `PATCH /task/v2/tasks/{guid}` sets `completed_at` successfully;
   - taskpool brain note and envelope state are synchronized to done.
6. Do not close Lark when the implementation is partial, wrong-scope, only superficially changes the requested surface, lacks published online UI evidence, or has not completed the required online-address UI 回收. Mark the envelope/task as `BLOCKED` or `online_ui_retest_pending` with the concrete gap, and leave Lark open.

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
8. Run deterministic verification. For admin tasks, the default gate is `npm run build` plus task-specific tests/static checks when relevant. This is not final Lark closeout for `uvisa-app-2.0`; it is the implementation-sendback gate before online UI 回收.
9. Write evidence under `~/.hermes/evidence/envelopes/<envelope-id>/`:
   - `closeout-summary.json`
   - `build.log` / test logs
   - `pr_url.txt` or code-location evidence
   - `diff.patch` when applicable
   - `proof_sha.txt`
10. If implementation is ready but online UI 回收 has not passed, comment only an interim public-safe implementation-sendback summary and keep Lark open. Do not imply final completion.
11. Complete the release/publishing flow and verify the online address with real online UI evidence for the exact task surface and acceptance atoms.
12. Only after online UI 回收/验收 passes, comment on Lark with a concise public-safe final summary: what changed, PR/commit, deployed/online URL checked, verification result. Do not include `/Users/...`, `/tmp/...`, secrets, raw logs, or internal-only evidence paths.
13. Patch Lark task `completed_at` using task v2 shape: `{"task":{"completed_at":"<ms>"},"update_fields":["completed_at"]}`.
14. Mark envelope DONE with `proof_sha`; mark brain task done with structured evidence.
15. Notify TG after each batch or user-requested completion. If `telegram` has no home channel, retry `telegram:he cheng`; if that fails, report the notification blocker explicitly.

## Reopened / partial task rule

If post-closeout audit finds the task was not really satisfied:
- do not defend the old done state;
- create a corrective PR when the original PR was merged but wrong;
- if the contract is large or ambiguous, mark the envelope/task `BLOCKED` and keep Lark open;
- never close Lark from a partial PR just because build passed;
- never close Lark for `uvisa-app-2.0` from local/build/merged-code evidence alone when online UI 回收 is missing.

Known example:
- `ed84743a` / `24189dc0e210`: PR #156 only changed a title suffix for Debit 入金 and did not satisfy the full Debit inflow page contract. Correct handling is BLOCKED + Lark left open.

## Evidence hierarchy

For this UVISA admin/work mode:
1. Lark live API: external task truth.
2. Latest local prototype source: before using `/Users/charles/Desktop/folder/work/uvdemo2.0/uvisa-app` or `/Users/charles/Desktop/folder/work/uvdemo2.0/uvisa-admin` as a fallback for stripped Lark `[Image]` evidence, run `git -C /Users/charles/Desktop/folder/work/uvdemo2.0 fetch origin --prune` and, if the tree is clean, `git -C /Users/charles/Desktop/folder/work/uvdemo2.0 pull --ff-only origin main`; record the resulting commit SHA in task evidence. If the prototype tree is dirty or cannot fast-forward, treat prototype freshness as blocked and do not claim prototype parity from stale local files.
3. Merged PR / current code inspection: implementation truth.
4. `npm run build` and task-specific deterministic checks: implementation verification truth.
5. Published online address + real online UI 回收/验收 evidence: final completion truth for `uvisa-app-2.0` tasks.
6. `~/.hermes/evidence/envelopes/<id>/closeout-summary.json` + proof SHA: local closeout truth.
7. Brain task/envelope status: derived execution lifecycle; must be synchronized, but must not override missing implementation or online UI evidence.

## uvisa-app-2.0 online closeout boundary

This rule applies to `uvisa-app-2.0` Lark/work tasks because the project has an online address and a complete publishing flow.

Do not cancel or bypass this gate for `uvisa-app-2.0` by batch-level wording. Code merge/current-code proof, build logs, local screenshots, browser-harness local evidence, and proof SHA are necessary implementation evidence, but final Lark closeout requires online-address UI 回收/验收 first.

If online UI evidence is missing, keep Lark open and use one of these statuses in the local task/envelope:
- `implementation_sendback_done`
- `online_ui_retest_pending`
- `blocked_online_publish_or_ui_evidence`

Stronger proof is still required for:
- mobile H5 tasks requiring real mobile screenshots;
- backend/API/data-correctness tasks requiring real API/database equality proof;
- security/PII/payment tasks where task-specific verification must be stronger than build;
- any task where the user says final completion depends on a stricter production/online evidence shape.
