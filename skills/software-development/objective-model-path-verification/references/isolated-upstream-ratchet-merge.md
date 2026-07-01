# Isolated upstream ratchet merge for customized forks

Applicability: use when upgrading a locally customized Hermes/forked codebase from an upstream branch while private overlays, local governance, or provider/runtime changes must be preserved. This is a procedure pattern, not a record of a specific branch.

Anti-conditions:
- Do not use this as authority to push, deploy, publish, enter credentials, or replace the live checkout.
- Do not store one-off branch names, commit hashes, or session progress here; keep those in the project SSOT or final report.
- Do not treat a provider config smoke as verified when the remaining blocker is a missing/invalid secret.

## Safe ratchet shape

1. Establish the objective model before merge:
   - success criteria: conflict-free merge, preserved private overlays, upstream features adopted, tests/smokes pass, rollback path exists;
   - red lines: do not mutate the dirty live checkout; do not push; do not type secrets; do not silently drop private behavior.
2. Create evidence and rollback first:
   - record current branch/HEAD/status/remotes;
   - save tracked diff and untracked archive;
   - create an isolated `git worktree` branch for the merge.
3. Merge upstream in the isolated worktree only.
4. Resolve conflicts by policy:
   - adopt upstream when it replaces a known-broken legacy path;
   - preserve private overlays by seam (hooks, governed taskpool, AgentOS/advisory surfaces, profile boundaries);
   - avoid cargo-culting both sides into duplicate logic.
5. Verify incrementally before commit:
   - `git diff --name-only --diff-filter=U` must be empty;
   - conflict-marker scan must distinguish true markers from test fixture literals;
   - `git diff --check`;
   - targeted `py_compile` for edited Python files;
   - focused tests for changed domains;
   - runtime/import smoke from the isolated worktree using `PYTHONPATH=.` if the worktree venv is incomplete.
6. Run post-update/self-check logic against the ratchet worktree, but beware scripts that hardcode the live checkout root. Prefer a temporary copied script or explicit root override; label any check that still assumes live-checkout branch/layout.
7. Commit only after the isolated worktree is clean and focused tests pass.
8. Get independent verification before claiming certification or proposing merge-back.
9. Stop at a human gate before changing the live checkout or pushing.

## Verification bundle

A minimally credible bundle includes:
- clean isolated branch status;
- merge commit with both upstream and private parents reachable;
- focused tests for provider/runtime/tool/gateway areas touched;
- private overlay smoke tests;
- post-update/self-check readback or scoped explanation for inapplicable checks;
- CLI import/version smoke from the isolated tree;
- independent verifier PASS/FAIL with caveats;
- explicit credential, push, deploy, and live-checkout boundaries.

## Pitfalls

- Worktree `.git` is a file, not a directory. Scripts that check `isdir(root/.git)` may misclassify a valid worktree as not a git checkout.
- Post-update scripts often hardcode the live Hermes root and the script directory. If copied to `/tmp`, sibling-script checks may fail even though the worktree code is valid.
- A stale worktree `.venv` without test dependencies is an environment caveat. Use a known-good interpreter with `PYTHONPATH` pointed at the isolated tree, and label the caveat instead of calling the code broken.
- When upstream intentionally removes a broken legacy provider path, do not resurrect deleted files unless a verified compatibility requirement exists. Preserve config/fallback behavior separately and mark live runtime as credential-bound if no valid key is available.
- Large conflict resolution can accidentally concatenate both sides. Look for duplicate calls, nested non-reentrant locks, repeated test definitions, and stale import paths.
