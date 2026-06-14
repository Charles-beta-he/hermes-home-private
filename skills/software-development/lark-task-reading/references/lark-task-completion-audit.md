# Lark task completion audit pattern

Use this when the user pastes a single Lark Task URL and asks to analyze whether it is complete, especially for UVISA tasks already marked `done`.

## Goal

Separate three different claims that are often conflated:

1. **Lark state** — what Task Center says (`status`, `completed_at`, comments, native attachments).
2. **Implementation state** — whether a scoped code change exists on the relevant branch and deterministic checks pass.
3. **Acceptance/closeout state** — whether the expected environment, UI evidence, and notification/hand-off are actually present.

A `done` status plus a code comment is not enough for UI/product tasks if native UI evidence, deployment evidence, or tester acknowledgement is missing.

## Read path

1. Parse the URL for `guid` and `suite_entity_num`.
2. Direct-fetch the task by GUID with `GET /task/v2/tasks/{guid}` rather than relying only on the incomplete-task list.
3. Enrich tasklist names when possible so scope claims are tasklist-backed, not title-backed.
4. Read comments and attachments:
   - comments may contain the real closeout note, commit hash, test commands, or tester pushback;
   - native attachments prove screenshot/evidence backfill for UI tasks;
   - a late comment such as “没发测试？” is a closeout signal, not noise.
5. Inspect the target repo/branches referenced by the comment or title:
   - `git fetch origin --prune` first;
   - check whether the named commit is contained in `origin/test`, `origin/main`, or the deployment branch;
   - inspect the changed files and regression tests for requirement coverage.
6. Re-run the smallest deterministic verification that proves the task claim, preferably in a clean worktree if the canonical worktree is dirty.
7. If an online/test URL is in scope, verify the deployed bundle or runtime route contains the change. Bundle-marker checks can support deployment evidence, but they do not replace real UI interaction for UI-closeout tasks.

## Classification language

Use explicit buckets:

- `implementation_done`: scoped code exists and deterministic tests/build for the task pass.
- `deployed_to_test`: the relevant test/online bundle or branch contains the change.
- `main_not_covered`: test branch has the fix but main/release does not.
- `evidence_incomplete`: Lark has no native screenshot/attachment or no online UI proof for a UI task.
- `tester_followup_pending`: a later Lark comment asks for testing, says not sent, reports recurrence, or otherwise challenges closeout.
- `not_done`: no scoped implementation or failing deterministic proof.

## Reporting shape

Keep the answer decision-oriented:

- task id/title/status/completion time;
- implementation commit and files;
- branch/deployment containment;
- verification commands actually run and results;
- closeout gaps and exact next action.

Avoid saying simply “done” when the better answer is “implementation done, but closeout evidence incomplete.”

## Pitfalls

- Do not infer completion from the Lark `done` state alone.
- Do not ignore late comments after the closeout note; they can invalidate the closeout path.
- Do not count local paths, `/tmp` notes, or text-only comments as UI proof when the workflow requires native screenshots/attachments.
- Do not treat `pnpm test -- <file>` as a targeted Vitest file run unless the package script really forwards arguments that way; if it runs the whole suite or unexpected files, rerun with `pnpm exec vitest run <file>` and report the actual result.
- Do not assume test-branch completion implies main/release completion. Always state branch containment.