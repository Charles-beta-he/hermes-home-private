# Dirty Workspace Gain Extraction vs Target Branch

Use when a long-lived or dirty worktree contains uncommitted changes and the user asks to compare against a shared target branch (for example `test`) and keep only the beneficial increments.

## Applicability

- The current branch is stale, gone on remote, or diverged heavily from the target.
- The worktree has mixed tracked/untracked changes, copied duplicate files, or old local experiments.
- The user wants reusable/good changes preserved without regressing the target branch.

Anti-conditions:
- Do not use this to hide unrelated local work in a broad commit.
- Do not overwrite newer target-branch behavior just because the dirty worktree has an older implementation.
- Do not classify task/session progress as a durable gain.

## Procedure

1. Fetch and identify the real target tip:
   - `git fetch origin --prune`
   - `git rev-parse --short origin/<target>`
   - `git rev-list --left-right --count HEAD...origin/<target>`
2. Back up the dirty workspace before touching it:
   - Save `git diff` to a timestamped `/tmp/.../tracked-uncommitted.patch`.
   - Save `git status --porcelain=v1`.
   - Copy untracked files into `/tmp/.../untracked/` preserving paths.
3. Classify each change against `origin/<target>`:
   - **already in target**: same file/content or equivalent behavior exists at target tip.
   - **superseded by target**: target has newer semantics; applying dirty change would downgrade behavior.
   - **stale duplicate/junk**: Finder-style ` 2` files, copied old snapshots, obsolete generated outputs.
   - **beneficial increment**: not in target, compatible with target tip, testable in isolation.
   - **needs human/product confirmation**: changes product semantics, removes UI/fields/routes, or crosses authority boundaries.
4. Extract only beneficial increments into a clean worktree from the target:
   - `git worktree add -b <gain-branch> /tmp/<repo>-gain origin/<target>`
   - Apply selected hunks/files only, not a broad dirty-worktree diff.
   - If a file already changed on target, merge semantically and preserve target behavior first.
5. Resolve conflicts by meaning, not side:
   - Prefer target branch current behavior when it represents a newer deployed/product/UI fix.
   - Layer only the narrow beneficial addition back in.
   - Re-check for conflict markers and `git diff --check`.
6. Verify the extracted increment in the clean worktree:
   - Run targeted tests for touched helpers/components.
   - Run build/typecheck when the change affects app startup, build scripts, routing, API plumbing, or release artifacts.
   - If the increment adds a generator (for example `version.json`), run it and read back the generated artifact.
7. Commit only the clean extracted gain:
   - Stage exact files.
   - Inspect `git diff --cached --stat` and `git diff --cached --name-status`.
   - Commit locally; push/PR only when requested.
8. Leave the original dirty workspace intact unless the user explicitly asks to clean it. Report the backup path, extracted branch/commit, what was not extracted, and verification evidence.

## Classification heuristics

- If `git diff --no-index <(git show origin/<target>:path) dirty/path` is empty, it is already in target.
- If the dirty file is older and lacks named fixes now present in target, it is superseded.
- Files with names like `Something 2.tsx`, copied snapshots, or old generated artifacts are usually stale duplicates; do not stage them without explicit evidence.
- A selected patch that applies with many conflicts is a warning: re-create it as semantic edits on top of target rather than forcing the old file through.

## Report format

- Base target and commit.
- Original worktree branch/status summary.
- Backup directory.
- Extracted clean worktree path, branch, commit.
- Included gains.
- Excluded changes with reason: already in target / superseded / duplicate / needs human.
- Verification commands and real outputs.
