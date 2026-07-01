# Controlled Upgrade Workflow

Extracted from `/Users/charles/.hermes/skills/software-development/post-update-patch-healing/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Controlled Upgrade Workflow

When upgrading with local vendor patches, follow this exact sequence. Skipping steps causes conflicts that are harder to resolve than the upgrade itself.

### Fast recovery from failed `自更新` attempts

If an automatic self-update attempt returns only `hermes update` timeout plus `post-update-check.py` exit `126`, do not stop there:

- Treat the update timeout as inconclusive. Inspect the repo and update process state, then verify whether the pull/install actually finished.
- Exit `126` from `~/.hermes/scripts/post-update-check.py` means the script was found but not executable. Rerun as `python3 ~/.hermes/scripts/post-update-check.py` or fix permissions with `chmod +x ~/.hermes/scripts/post-update-check.py`, then rerun dry-run and `--fix` if needed.
- After any checker fix, run the normal verification: `git diff --check`, checker dry-run, relevant `py_compile`/pytest, `hermes --version`, and `hermes doctor`.
- Final report should distinguish command timeout, permission issue, actual patch status, and verification status.



### Phase 0: Pre-Upgrade Analysis (before touching anything)

Use this both for deciding whether an update is worth doing and for preparing the actual update.

```bash
cd ~/.hermes/hermes-agent

# 1. Check how far behind/ahead
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
git describe --tags --always HEAD 2>/dev/null || true
git describe --tags --always origin/main 2>/dev/null || true

# 2. Summarize upstream value, not just count commits
git rev-list --count HEAD..origin/main
git diff --name-only HEAD..origin/main | wc -l
git diff --numstat HEAD..origin/main | awk '{a+=$1; d+=$2} END{printf("+%s -%s\n", a+0, d+0)}'
git log --first-parent --date=short --pretty=format:'%h%x09%ad%x09%s' HEAD..origin/main | sed -n '1,120p'
git show origin/main:RELEASE_v0.12.0.md 2>/dev/null | sed -n '1,220p' || true

# 3. Identify local modifications
git diff --stat                            # unstaged tracked changes
git diff --cached --stat                   # staged tracked changes
git ls-files --others --exclude-standard   # untracked custom files

# 4. Identify overlap: files changed both locally AND upstream
{ git diff --name-only HEAD; git diff --cached --name-only; git ls-files --others --exclude-standard; } | sort -u > /tmp/hermes-local-files.txt
git diff --name-only HEAD..origin/main | sort -u > /tmp/hermes-upstream-files.txt
comm -12 /tmp/hermes-local-files.txt /tmp/hermes-upstream-files.txt

# 5. Check whether untracked local files already exist upstream
while read -r f; do
  if git cat-file -e "origin/main:$f" 2>/dev/null; then echo "$f"; fi
done < <(git ls-files --others --exclude-standard)

# 6. Predict stash-pop/patch conflicts by simulating on a detached worktree
TMP=/tmp/hermes-upgrade-check-$$
PATCH=/tmp/hermes-local-tracked-$$.patch
git diff --binary HEAD > "$PATCH"
git worktree add --detach "$TMP" origin/main
(cd "$TMP" && git apply --3way --check "$PATCH")
git worktree remove --force "$TMP"
rm -f "$PATCH"
```

Interpretation:
- `git apply --3way --check` passing means the tracked patch will probably re-apply cleanly, but it does **not** prove behavior is correct. Still run `post-update-check.py`, py_compile, focused pytest, and `hermes doctor` after the update.
- Untracked files that do not exist in `origin/main` are not a path-collision risk, but they can still be forgotten if you stash or reset carelessly.
- If `HEAD...origin/main` reports `ahead > 0`, this is a private-fork state. Do **not** blindly follow the fast-forward-only path; choose merge/rebase strategy explicitly (see Phase 2).

### Phase 1: Pre-Upgrade Fixes

Before upgrading, ensure:

1. **Post-merge hook is correct** — Git post-merge `$1` is `0` (normal merge/fast-forward) or `1` (squash), NOT the strings `"merge"`/`"squash"`. Verify:
   ```bash
   cat .git/hooks/post-merge
   ```

2. **Checker covers all local patches** — Run `post-update-check.py` dry-run. If any local vendor patch is NOT in the checker, add it BEFORE upgrading. Otherwise the patch will be lost after upgrade with no auto-recovery.

3. **Clean working tree** — `git diff --check` should produce no output (no trailing whitespace, no conflict markers).

4. **Backup everything**:
   ```bash
   mkdir -p ~/.hermes/backups
   git diff --binary > ~/.hermes/backups/pre-upgrade-$(date +%Y%m%d-%H%M%S).patch
   cp .git/hooks/post-merge ~/.hermes/backups/
   cp ~/.hermes/scripts/post-update-check.py ~/.hermes/backups/
   ```

### Phase 2: Upgrade Execution

Choose the path based on ahead/behind state from Phase 0.

#### Path A — No private commits ahead (`ahead = 0`): fast-forward

```bash
cd ~/.hermes/hermes-agent

# 1. Stash ALL changes (tracked + untracked)
git stash push -u -m "pre-hermes-upgrade-$(date +%Y%m%d-%H%M%S)"

# 2. Pull (fast-forward preferred)
git pull --ff-only origin main
# ↑ This triggers post-merge hook → post-update-check.py --fix automatically
# The checker re-applies all vendor patches to the new upstream code

# 3. Verify checker results — look for FIXED/OK/NEEDS_FIX in output
```

#### Path B — Private fork has local commits ahead (`ahead > 0`): controlled merge

When the repo is `ahead N, behind M`, `git pull --ff-only` will fail by design. Treat upstream as an upgrade source and preserve private commits with an explicit merge (preferred for large upstream jumps) unless the user explicitly wants a rebase.

```bash
cd ~/.hermes/hermes-agent

# 0. Create restore points before changing history or working tree
git branch private-backup-before-upstream-$(date +%Y%m%d-%H%M%S)
git tag pre-upstream-update-$(date +%Y%m%d-%H%M%S)
mkdir -p ~/.hermes/backups
git diff --binary HEAD > ~/.hermes/backups/hermes-agent-local-tracked-before-update-$(date +%Y%m%d-%H%M%S).patch
cp .git/hooks/post-merge ~/.hermes/backups/post-merge-before-update 2>/dev/null || true
cp ~/.hermes/scripts/post-update-check.py ~/.hermes/backups/post-update-check-before-update.py 2>/dev/null || true

# 1. Stash all dirty work, including untracked private files
git stash push -u -m "pre-upstream-update-private-patches-$(date +%Y%m%d-%H%M%S)"

# 2. Merge upstream explicitly (not ff-only, not implicit pull)
git fetch origin main --prune
git merge --no-ff origin/main -m "merge: sync from origin/main"
# post-merge hook may run post-update-check.py --fix here.

# 3. Reapply local dirty work
git stash pop
```

Alternative when untracked private modules are long-lived repo-level artifacts: commit them first in a clear private commit, then stash only tracked dirty patches before the merge. This reduces risk of losing untracked files but creates another local commit to carry forward.

```bash
git add <private-untracked-files>
git commit -m "feat(private): add private agent modules"
git stash push -m "pre-upstream-update-tracked-private-patches" -- <tracked-patch-files>
git merge --no-ff origin/main -m "merge: sync from origin/main"
git stash pop
```

### Phase 3: Stash Pop + Conflict Resolution

**Critical trap**: If post-update-check already applied patches to files that are also in the stash, `git stash pop` will fail with "Your local changes to the following files would be overwritten by merge". This happens because both the checker AND the stash modified the same files.

**Solution**: Restore checker-modified files to clean HEAD, then pop:

```bash
# For files where checker already applied the same patch as stash:
git checkout HEAD -- agent/context_compressor.py agent/memory_manager.py ...

# Then pop — only truly different changes will conflict
git stash pop
```

After pop, exactly ONE file may still conflict: files where upstream AND local patch changed the same region differently (e.g., `tools/mcp_tool.py` where upstream added `server._rpc_lock` and local patch added `asyncio.wait_for`).

**For mechanical conflicts** (both sides add independent features to the same function), delegate to Claude Code:

```bash
# From Hermes, delegate the conflict resolution
# Claude Code can read the conflict markers and produce the correct merge
```

**Resolution principle**: Keep BOTH sides' changes. In the mcp_tool example:
```python
async def _call():
    async with server._rpc_lock:       # ← upstream's addition
        try:
            result = await asyncio.wait_for(  # ← local patch
                server.session.call_tool(...),
                timeout=tool_timeout,
            )
        except asyncio.TimeoutError:   # ← local patch
            ...
```

### Phase 4: Verification

Run the verify script at `~/.hermes/scripts/hermes-pre-update-verify.sh`:

```bash
~/.hermes/scripts/hermes-pre-update-verify.sh
```

This checks:
- `git diff --check` (no trailing whitespace)
- `post-update-check.py` dry-run (all patches applied)
- `py_compile` on all patched runtime files
- `pytest` with isolated `HERMES_HOME` (temp directory, avoids polluting real state)

Then verify the CLI itself:
```bash
hermes --version
hermes doctor
```

### Phase 5: Cleanup

```bash
git stash drop   # only after verification passes
```

### Verify Script Template

Create at `~/.hermes/scripts/hermes-pre-update-verify.sh`:

```bash
#!/bin/sh
set -eu
REPO="${HERMES_REPO:-$HOME/.hermes/hermes-agent}"
CHECKER="$HOME/.hermes/scripts/post-update-check.py"
if [ -x "$REPO/venv/bin/python" ]; then PY="$REPO/venv/bin/python"
elif [ -x "$REPO/.venv/bin/python" ]; then PY="$REPO/.venv/bin/python"
else PY="$(command -v python3)"; fi

cd "$REPO"
echo "== git diff --check =="; git diff --check
echo "== post-update-check dry run =="; python3 "$CHECKER"
echo "== py_compile patched files =="
"$PY" -m py_compile agent/context_compressor.py agent/memory_manager.py \
  agent/prompt_builder.py agent/transports/chat_completions.py cli.py \
  hermes_cli/commands.py run_agent.py tools/mcp_tool.py tools/skill_manager_tool.py
echo "== isolated pytest =="
TMP_HOME="$(mktemp -d)"; trap 'rm -rf "$TMP_HOME"' EXIT
HERMES_HOME="$TMP_HOME" "$PY" -m pytest tests/test_model_health.py \
  tests/test_task_classifier.py -q -o 'addopts='
echo "== OK =="
```

### Pitfalls

1. **Stash pop fails with "would be overwritten"**: Checker already modified those files. Restore them to HEAD first, then pop. See Phase 3.

2. **Post-merge hook doesn't run**: Hook compares `$1` to wrong values. Fix: compare to `0`/`1`, or just always run checker unconditionally.

3. **Checker misses a patch**: After upgrade, a local patch silently vanishes. Always verify checker coverage BEFORE upgrading. If a patch isn't covered, add it to the checker first.

4. **Tests fail with stale state**: `model_health` and other stateful tests read `~/.hermes/rate_limits/` and other real paths. Always use temp `HERMES_HOME` for isolated testing.

6. **`hermes --version` shows "behind" after upgrade**: The version string in `pyproject.toml` may not be bumped yet even though code is at origin/main HEAD. Check `git rev-list HEAD..origin/main | wc -l` (should be 0) to confirm you're current. If git says `HEAD..origin/main=0` but `hermes --version` still reports old behind count, clear the cached update result (`rm -f ~/.hermes/.update_check`) and rerun `hermes --version`; the update checker caches results for ~6h. Note: running `hermes --version` can itself fetch/update `origin/main`; re-check `git rev-list --left-right --count HEAD...origin/main` afterward before declaring the upgrade current.

7. **TUI tests need generated hermes-ink dist first**: In `ui-tui`, a direct `npm test` can fail with `Cannot find module './dist/entry-exports.js'` from `packages/hermes-ink/index.js`. Build the package first, then rerun tests:
   ```bash
   cd ~/.hermes/hermes-agent/ui-tui
   npm run build --prefix packages/hermes-ink
   npm test
   ```
   A Python traceback during the slash-parity helper on systems whose default `python` is too old may be reported while Vitest exits 0 and skips those parity checks; treat non-zero Vitest exit as blocking, and record skipped parity separately if present.

8. **Config version outdated after large upstream jump**: Run `hermes doctor --fix` after code validation, with a backup of `~/.hermes/config.yaml` first. This migrates `config_version` and seeds new defaults (for example curator/auxiliary config) without touching secrets. Re-run `hermes doctor` afterward and distinguish real blockers from optional missing provider keys.

8. **Upstream timeout is silent**: In MCP tools, upstream's `_run_on_mcp_loop` timeout returns `None` on expiry, which gets misreported as success. The local `asyncio.wait_for` patch provides correct error reporting + circuit breaker bump. Keep it even though upstream has "timeout handling".

7. **MCP conflict resolution is always mechanical**: When upstream adds `server._rpc_lock` and local adds `asyncio.wait_for`, combine them (lock outside, wait_for inside). Never choose one or the other.
