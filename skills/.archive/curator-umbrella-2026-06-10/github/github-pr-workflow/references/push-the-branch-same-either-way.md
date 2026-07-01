# Push the Branch (same either way)

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/github/github-pr-workflow/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Push the Branch (same either way)

```bash
git push -u origin HEAD
```

For existing tracked branches or dual-repo work, push each repo explicitly and verify HEAD equals the remote-tracking ref before reporting success:

```bash
# Existing tracked branch
git push origin $(git branch --show-current)

# Verify clean + remote parity
git status -sb
git rev-parse HEAD
git rev-parse @{u}
```

If the branch was rebased or history was rewritten, use lease-protected force push, not plain force:

```bash
git push --force-with-lease origin $(git branch --show-current)
git fetch origin $(git branch --show-current) --prune
git status -sb
git rev-parse --short HEAD
git rev-parse --short @{u}
```

**Pitfall: `--force-with-lease` fails on first push of a new branch.** When pushing a branch for the first time (no remote tracking ref exists), `--force-with-lease` is rejected with `stale info` because there's no upstream ref to lease against. Detect this case and fall back to `--force`:

```bash
if git ls-remote --exit-code --heads origin "$(git branch --show-current)" &>/dev/null; then
  git push --force-with-lease origin "$(git branch --show-current)"
else
  git push --force origin "$(git branch --show-current)"
fi
```

Before starting or continuing a rebase, check for in-progress state (`.git/rebase-merge`, `.git/rebase-apply`, detached `HEAD`) and resolve/continue the existing rebase rather than nesting another one. When rebasing a feature branch that already has a PR, do not assume the target is local `main` or the repo default branch: fetch first, inspect the PR's current `baseRefName` (`gh pr list/view --head <branch>` or equivalent), and rebase onto the fetched remote base ref such as `origin/main`. This avoids accidentally rebasing onto a stale local branch or the wrong target after the PR base changed. See `references/dual-repo-rebase-push.md` for the coordinated frontend/backend rebase + push closeout pattern.

If there are unrelated/untracked probe files, remove/ignore them or leave them unstaged intentionally; do not `git add -A` during a commit/push request in a long-lived dirty repo. On macOS, watch for Finder ` 2` duplicate files and `.tmp/` directories — they sneak into commits silently. See `references/junk-file-cleanup.md` for detection and cleanup patterns.
