# Branch-specific contract drift pitfall

Applicability: use for any repository investigation where the correctness of an API, route, schema, protocol, or UI contract depends on a named branch/ref rather than the currently checked-out worktree.

Anti-conditions: do not use this as a reason to switch branches or overwrite local work. It is an inspection procedure only. Do not store project-specific routes, filenames, or branch policies here; put those in the project profile or a scoped project reference.

## Problem pattern

A local working branch can be behind or diverged from the branch that actually defines the current contract. Searching only the checked-out worktree can produce a false negative, such as concluding a route, schema, migration, or protocol model is missing when it exists on the target ref.

## Required procedure

1. Establish the target ref before drawing contract conclusions.
   - `git branch --show-current`
   - `git status -sb`
   - `git fetch origin --prune`
   - `git rev-parse --short <target-ref>`
2. Search the target ref directly, without relying on the current worktree:
   - `git grep -n -i -E '<contract terms>' <target-ref> -- <paths>`
   - `git show <target-ref>:<path>` for exact controller/service/frontend files.
3. Compare the local branch to the target ref when results conflict:
   - `git log --oneline --decorate --left-right HEAD...<target-ref> --max-count=30`
   - `git diff --name-status HEAD..<target-ref> -- <relevant paths>`
4. Treat absence from the current worktree as non-evidence until the target ref has been searched.
5. Search by contract fields as well as route names:
   - route strings and controller annotations
   - DTO/entity/service names
   - database columns/migrations
   - protocol-specific field names
6. In the final answer, explicitly state which branch/ref was used for the conclusion.

## Anti-patterns

- Do not say a backend lacks a contract after searching only the checked-out local branch.
- Do not switch branches just to inspect unless necessary; prefer `git grep <target-ref>` and `git show <target-ref>:path` first.
- Do not collapse adjacent systems into one conclusion. Distinguish similarly named integration models before proposing fixes.

## Verification checklist

- [ ] Current branch identified.
- [ ] Target ref identified and fetched.
- [ ] Contract searched on target ref, not just worktree.
- [ ] Frontend and backend contract names/fields matched.
- [ ] Final conclusion names the exact ref used as evidence.
