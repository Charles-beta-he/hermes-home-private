# Upstream ratchet merge: isolated worktree → self-contained verification → mainline adoption

Use when a Hermes/private fork must absorb a large upstream update while preserving local overlays and the user authorizes a later merge back to the main checkout.

## Applicability

- Large upstream merge into a private fork or long-lived local overlay branch.
- Existing main checkout may be dirty or running active user state.
- The user wants a reversible ratchet upgrade, not a blind `git pull`.
- The resulting isolated worktree must be usable by itself, not only via another checkout's venv.

## Anti-conditions

- Do not use this to push/publish/deploy without a separate exact authorization.
- Do not type or create provider/API credentials; stop at a credential boundary.
- Do not mix pre-existing dirty main-checkout changes into the ratchet commit.
- Do not treat a test pass using another checkout's venv as proof the worktree is self-contained.

## Procedure

1. Establish the objective model and rollback boundary.
   - Record current main checkout path, branch, HEAD, dirty status, remotes, upstream target, and protected local overlays.
   - Create/confirm a backup before mutating the main checkout.

2. Use an isolated worktree for the risky merge.
   - Create a ratchet branch/worktree from the private baseline.
   - Merge upstream there; resolve conflicts in the worktree only.
   - Keep a task-local SSOT doc for decisions such as keep/absorb/retire overlay and provider migration choices.

3. Verify in the isolated worktree before mainline adoption.
   - `git diff --check`
   - targeted `py_compile`
   - focused tests for touched surfaces and protected overlays
   - CLI smoke with `PYTHONPATH=.` if the package is not installed into the worktree venv yet
   - post-update/self-check adapted to the ratchet root if the canonical script defaults to the main checkout
   - independent verifier readback when the change is large

4. Make the worktree self-contained if requested or if canonical wrappers depend on local `.venv`.
   - Inspect `.venv/bin/python -m pytest --version` rather than assuming `.venv` is ready.
   - Use the repo lockfile/manager, e.g. `uv sync --frozen` plus the extras needed by the focused test surfaces (`dev`, `messaging`, `cron`, `pty`, `voice`, etc. as applicable).
   - Re-run a representative focused test slice using `.venv/bin/python`, not another checkout's venv.
   - Smoke the CLI from the worktree with `PYTHONPATH=. .venv/bin/python -m hermes_cli.main --version`.

5. Commit the ratchet worktree only after the focused gates pass and status is clean.

6. When the user authorizes mainline adoption, protect main checkout dirty work first.
   - If `git status --short` is non-empty, create a named stash such as `pre-ratchet-main-dirty-<timestamp>` before merging.
   - Prefer fast-forwarding main to the verified ratchet commit when possible.
   - Do not auto-apply the stash afterward; it contains pre-ratchet work that must be reviewed separately.

7. Post-adoption verification in the main checkout.
   - Run the canonical post-update check from a compatible Python. If a local script uses modern annotations, ensure `from __future__ import annotations` or run it with the Hermes venv Python.
   - Run focused tests again in the main checkout.
   - Smoke version/CLI and relevant read-only control-plane commands.
   - Report ahead/clean status, stash name, commit hash, and remaining boundaries.

8. If the user later asks to align the protected stash with other session work, treat it as a separate evidence-alignment slice, not as part of the ratchet merge.
   - Inspect `git stash show --stat --include-untracked` and the untracked parent (`stash@{n}^3`) before applying.
   - Apply only after mainline adoption is clean and remote/local are aligned.
   - If Git reports a stale sequencer state such as “Cherry-pick currently in progress” without `CHERRY_PICK_HEAD`, inspect `.git/sequencer` and use `git cherry-pick --quit` only to clear metadata; do not abort unless an actual in-progress operation must be reverted.
   - Validate restored evidence artifacts by type before committing: parse JSON/JSONL, check markdown non-empty/headings, and run `git diff --check`.
   - Commit the restored session artifacts separately from the ratchet merge, push only with exact authorization, read back `origin/<branch>...<branch>` is `0 0`, then drop the now-consumed stash to prevent ghost re-application.

## Common pitfalls

- `post-update-check.py` may exit 0 while still listing `FIX_FAILED`/BROKEN summaries; read the summary, not only the exit code.
- A git worktree has `.git` as a file, not a directory; governance scripts that check `isdir(.git)` may produce false negatives when adapted to a ratchet worktree.
- Running tests with the main checkout's venv can verify source semantics but not self-contained worktree readiness.
- Post-merge hooks can call system `python3`; local maintenance scripts using Python 3.10+ annotation syntax should either run under the Hermes venv or include future annotations for older system Python compatibility.
- Provider migrations often leave a credential boundary: tests can verify the provider adapter, while live smoke still requires the user's valid API key.
- Applying a stash after a large ratchet can surface unrelated stale Git operation metadata (for example an old `.git/sequencer/todo`) even when no `CHERRY_PICK_HEAD` exists. Clear only the stale metadata after inspection; the applied files are still ordinary working-tree changes that need separate validation and commit.
- Stash `show --stat` may hide untracked files unless `--include-untracked` is used or the third stash parent is inspected. Always account for untracked docs/evidence before declaring the stash aligned.

## Evidence bundle to report

- Main pre-merge HEAD and final HEAD.
- Ratchet branch/worktree path and commit hash.
- Dirty work stash name if one was created.
- Self-contained worktree proof: `.venv/bin/python -m pytest --version`, focused tests via `.venv`, and CLI version smoke.
- Main checkout proof: clean status, post-update summary, focused tests, CLI/control-plane smoke.
- Remaining authority/credential/push boundaries.
