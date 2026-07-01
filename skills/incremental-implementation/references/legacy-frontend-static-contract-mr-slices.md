# Legacy frontend static-contract MR slices

Applicability: old Vue/React/mobile-web codebases where global lint/build baselines are noisy, UI regressions are small and localized, and the user wants a reviewable MR rather than broad auto-merge. Anti-conditions: do not use static contracts as a substitute for browser/device screenshots when the task explicitly requires visual acceptance, animation, safe-area, or A+/uIMax proof.

Pattern:

1. Start from a fresh remote base in an isolated worktree.
   - `git fetch origin --prune`
   - `git worktree add -b <topic> /tmp/<repo>-<topic> origin/<base>`
   - Keep the user's existing dirty or behind worktree untouched.

2. Slice by task class and commit after each green slice.
   - Behavior fixes: add a small real-code JS contract test under `tests/*.test.js`.
   - Static UI/CSS fixes: add a static contract test that reads the touched `.vue`/`.scss` files and asserts the required visible contract (font token exists, numeric cells use tabular figures, price column is right-aligned, button width is fixed, etc.).
   - Keep each commit scoped to one semantic concern.

3. Treat full-lint failures in legacy repos as baseline evidence, not an excuse to skip verification.
   - Run full lint once if useful to classify historical/off-scope failures.
   - Then run targeted eslint on the touched files plus new tests.
   - Run `git diff --check origin/<base>..HEAD`.
   - Run the project build if available, and classify warnings separately from exit status.

4. Create the MR without opening merge automation unless explicitly authorized.
   - Push the topic branch.
   - Create the MR with a description that lists task IDs, touched behavior, verification commands, and known baseline warnings.
   - Read back MR state via the hosting API/CLI and report: opened state, source/target branches, conflict/mergeability, pipeline/auto-merge flags, and head SHA.

5. Stop at the human gate.
   - Do not merge, enable auto-merge, or mark external task lifecycle complete unless the user explicitly authorizes that boundary and the required verification evidence exists.
