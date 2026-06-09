When the user explicitly asks for Hermes self-check/update (for example, "Hermes自检更新"), treat the object as the local Hermes installation/repo rather than the current project.

Recommended sequence:
1. Confirm current install and update availability with `hermes --version`.
2. Inspect the Hermes repo state before update:
   - `git -C ~/.hermes/hermes-agent status --short --branch`
   - `git -C ~/.hermes/hermes-agent remote -v`
3. Run `hermes update --backup --yes`.
4. Immediately run `python3 ~/.hermes/scripts/post-update-check.py --fix`.
5. Re-verify:
   - `hermes --version`
   - `git -C ~/.hermes/hermes-agent status --short --branch`
   - `git -C ~/.hermes/hermes-agent stash list --max-count=5`
6. Report both update success and leftovers that still need attention.

What to explicitly report after update:
- version change / whether Hermes is up to date
- whether the repo is clean or still has local modifications / untracked files
- whether update created an autostash that remains in `git stash list`
- whether `post-update-check.py --fix` still shows any FIX_FAILED item (for example `mcp_rpc_timeout_guard`)

Pitfall from this session:
- `hermes update` can succeed while leaving local patches, untracked files, and an autostash behind. Treat update success and worktree cleanliness as separate checks.
- `post-update-check.py --fix` can exit 0 while still reporting a specific guard as `FIX_FAILED`; read the summary instead of trusting exit code alone.
