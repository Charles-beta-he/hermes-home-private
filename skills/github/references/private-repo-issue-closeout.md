# Private Repo Issue Closeout

Scope: fixing issues in the user's own private GitHub repositories, especially Hermes/private forks where the local checkout may already contain commits that are not pushed.

Applicability:
- User asks to fix a private repo issue but initially gives an ambiguous target such as “your own remote private repo issue”.
- A reported GitHub issue describes a regression that may already be fixed locally on a branch that is ahead of origin.
- The fix requires remote readback and issue closeout, not only local tests.

Anti-conditions:
- Do not apply this to unrelated public repo triage or generic OSS analysis.
- Do not close issues from stale local evidence; close only after remote branch/readback proves the fix exists remotely.
- Do not push broad dirty worktree state. Inspect scope first and push only the intended private-repo branch/commits.

## Procedure

1. Resolve the target repository.
   - Inspect candidate local repos/remotes only if the user’s wording is ambiguous.
   - For Hermes self-repo work, distinguish the Hermes home repo from the Hermes agent source repo.
   - List open issues on likely private repos with `gh issue list --repo <owner/repo> --state open`.

2. Read the issue body before editing.
   - Capture reported command, exception, branch, bad commit, mitigation, and suggested fix.
   - Treat the issue body as a reproduction/evidence packet, not as proof the current tree is still broken.

3. Compare local and remote state.
   - Run `git fetch origin --prune`.
   - Read `git rev-list --left-right --count origin/<branch>...<branch>`.
   - Inspect `git log origin/<branch>..<branch>` for local commits that may already contain the fix.
   - If the issue says files/modules are missing, check both local tree and `origin/<branch>` with `git ls-tree`/GitHub API before deciding whether to code or push.

4. If local commits already implement the fix, verify locally before pushing.
   - Use the repo’s venv/interpreter when present.
   - Minimum for CLI import regressions: `python -m py_compile` for touched modules, direct import smoke, focused tests, and the exact CLI smoke command from the issue when feasible.

5. Push only after verification and read back remote state.
   - `git push origin <branch>`.
   - Re-fetch and confirm `origin/<branch> == <branch>`.
   - Use GitHub API or `git ls-tree origin/<branch>` to prove the missing/changed files are present remotely.

6. Close the issue with evidence.
   - Comment the exact commits/branch, remote readback, focused test outputs, CLI smoke outputs, and the reason it resolves the issue.
   - Then close the issue and read back `state=CLOSED`.

## Pitfalls

- **Local-ahead fix mistaken for unfixed code**: a private repo issue may be valid on `origin/<branch>` while local `<branch>` already contains the fix. The correct action may be verify → push → remote readback → close, not another code patch.
- **Wrong private repo target**: Hermes has both a home/private data repo and an agent source private repo. List issues/remotes to avoid fixing the wrong one.
- **Import smoke partial failure**: if `python` is absent but `./venv/bin/python` exists, use the repo venv for verification. Do not store the missing `python` binary as a durable repo problem.
