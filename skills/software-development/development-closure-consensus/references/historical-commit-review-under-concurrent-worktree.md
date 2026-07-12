# Historical Commit Review Under a Concurrent Worktree

Use this pattern when the requested review target is an exact commit/range but the active branch, worktree, or external test artifact may change during review.

## Applicability

- The user names exact commit hashes or a historical range.
- Other agents/processes may be committing or editing concurrently.
- Verification fixtures live outside the repository and may also change.

## Anti-conditions

- Do not silently review current `HEAD` when the requested target is historical.
- Do not reset, checkout, stash, or overwrite a shared worktree merely to make review easier.
- Do not call current-tree build proof exact-target proof when later commits touch the reviewed module.

## Procedure

1. **Freeze target identity**
   - Read every requested commit with `git show <hash>` and record its changed-file list.
   - Read the final historical artifact with `git show <final-hash>:<path>` and cite historical line numbers.
   - Record its blob hash using `git rev-parse <hash>:<path>`.

2. **Detect drift before and after verification**
   - Re-read `git log -1`, `git status --short`, and the current file hash.
   - If HEAD/worktree/fixture changed, classify each command as exact-target evidence, target-plus-later-compatible evidence, or unusable for target approval.

3. **Handle changing external fixtures without editing them**
   - Re-read the fixture immediately before execution.
   - Inspect fixture imports before treating the run as exact-target evidence. A historical-review fixture that imports an absolute/current-worktree source path executes mutable current code, not automatically the named commit.
   - Hash every imported target source both from the immutable commit (`git show <commit>:<path> | shasum -a 256`) and from the current path. If all relevant hashes match, the fixture run may be attributed to the immutable slice; record the equality. If any hash differs, materialize the historical source in an isolated temporary directory or adapt the fixture in-memory/stdin to import that copy. Do not rewrite the shared fixture.
   - If the fixture gained unrelated imports/tests, run the current full fixture and separately execute the originally requested subset through an in-memory/stdin transformation.
   - State both counts explicitly, e.g. `original 14/14` and `current 16/16`.
   - Never rewrite the shared fixture merely to recover the old subset.

4. **Separate baseline failures from target failures**
   - Run the requested repository-wide command and report its real result.
   - If it fails only in untouched files, run a focused compiler/linter check on the historical target file or an unchanged equivalent.
   - Treat the full failure as non-blocking only when no target path appears, the reviewed commits changed none of the implicated files, and focused verification passes. Never report the full gate itself as passing.

5. **Bind verdict to scope**
   - Distinguish pure-library/formula approval from UI wiring, API integration, runtime, deploy, or production acceptance.
   - List caller-owned invariants that remain unverified, such as mode-specific data isolation.

6. **Preserve the shared workspace**
   - Do not modify source or shared fixtures.
   - Note build-generated ignored artifacts separately from tracked changes.
   - Report concurrent unrelated modifications without attributing them to the reviewer.

## Verification Checklist

- [ ] Exact commit diff and historical artifact were read.
- [ ] Target blob hash was distinguished from current file hash.
- [ ] Fixture was re-read immediately before running, and every current-worktree import was hash-bound to the immutable target or replaced by an isolated historical copy.
- [ ] Requested original test subset passed independently if the fixture drifted.
- [ ] Full compiler/lint failures were classified by touched-path ownership.
- [ ] Focused target checks passed.
- [ ] Verdict scope excludes unreviewed integration/UI/runtime behavior.
- [ ] No shared source or fixture was rewritten.
