# GitLab self-managed MR automation reference

Applicability: generic self-managed GitLab projects where an agent needs to validate `glab` authentication, MR creation, merge permissions, or auto-merge behavior. Anti-conditions: do not copy any concrete host, project path, branch name, token, MR ID, or session timestamp from a prior run; resolve all values from the active repository and live GitLab API.

## Safe credential handling

- Do not scrape browser login state, cookies, localStorage, or session tokens.
- Do not use tokens pasted into chat; treat them as leaked and ask the user to revoke/regenerate.
- Preferred PAT install path:

```bash
pbpaste | glab auth login --hostname <gitlab-host> --stdin --git-protocol ssh --use-keyring
```

- Verify with both commands:

```bash
glab auth status --hostname <gitlab-host>
glab api user
```

A status line that says `Token found` is not sufficient; `/api/v4/user` must return the authenticated user instead of `401 Unauthorized`.

## Self-managed OAuth pitfall

`glab auth login --web` on a self-managed instance may fail with:

```text
Set 'client_id' first with `glab config set client_id <client_id> -g --host <host>`.
```

This means glab OAuth has not been configured for the instance. Use PAT + keyring unless an admin supplies a client ID.

## Project policy inspection checklist

Resolve the project path from `git remote get-url origin`, URL-encode it, then query:

```bash
enc=$(python3 - <<'PY'
import urllib.parse
print(urllib.parse.quote('<group/subgroup/repo>', safe=''))
PY
)
glab api "/projects/$enc"
glab api "/projects/$enc/protected_branches"
glab mr list -R '<group/subgroup/repo>' -P 20 -F json
glab ci list -R '<group/subgroup/repo>' -r <target-branch> -P 5
```

Capture at least:

- access level / ability to create MR
- default branch
- protected branches and merge/push access levels
- MR enabled / jobs enabled
- merge method / squash option
- `only_allow_merge_if_pipeline_succeeds`
- discussion/approval gates
- whether source branches are removed after merge

## Safe capability probe pattern

Only run this after explicit user authorization. Probe a temporary target branch, not a shared integration/release branch.

1. `git fetch origin --prune`
2. create a clean temp worktree from the chosen base
3. push temp target branch
4. create temp source branch with a harmless marker commit
5. push temp source branch
6. create MR source -> temp target
7. read MR state (`has_conflicts`, `detailed_merge_status`, discussions)
8. try `glab mr merge --auto-merge --remove-source-branch --yes`
9. read back MR state and `merged_at`
10. delete temp source/target branches and remove worktree
11. verify no probe branch/worktree residue remains

Important interpretation:

- If no pipeline exists and the project does not require successful pipelines, `--auto-merge` may merge immediately.
- This proves MR/API/merge permissions and temporary-target merge mechanics, not that protected production branches should be auto-merged.
- For production-grade auto-merge, require a CI gate or explicit project policy that enforces pipeline success.

## Report shape

Report capability as separate levels:

1. authentication works
2. project policy can be read
3. MR creation works
4. merge into non-protected temp target works
5. protected branch merge permission exists or is blocked
6. CI-gated auto-merge exists or is absent

This avoids overclaiming from a successful temporary MR merge.
