# Self-Managed GitLab MR Automation and Auto-Merge

Applicability: use this reference for any repository hosted on GitLab or a self-managed GitLab-compatible instance when the user asks for automatic MR creation, auto-merge, or merge-when-pipeline-succeeds. Anti-conditions: do not encode a concrete host, project path, branch name, token, or company policy here; resolve those from the active repository, project profile, and live GitLab API each time.

## Capability ladder

1. **SSH push-options only**: can often create MRs without a PAT, but cannot reliably read back MR state, approvals, pipeline result, or merge result.
2. **glab/API with PAT or project token**: preferred for a verifiable automation loop; can create MR, inspect branch protections/approvals/pipelines, set auto-merge, and verify final state.
3. **CI-owned merge bot**: most production-grade; the merge authority lives inside GitLab CI with audited project/group tokens and explicit policy gates.

## Safe token handling

- Do not extract browser cookies, localStorage, session tokens, or saved credentials from a logged-in browser. Even with user authorization, this is credential extraction and is not an auditable automation path.
- Ask the user to create a GitLab PAT/project access token in the GitLab UI and pipe it into the CLI without showing it to the agent:

```bash
pbpaste | glab auth login --hostname <gitlab-host> --stdin --git-protocol ssh --use-keyring
```

- Recommended scopes for MR creation/merge automation: `api`, `read_repository`, `write_repository`.
- If `glab auth status` says "Token found" but `/api/v4/user` returns `401 Unauthorized`, the token is present but invalid for that host/API. Common causes: wrong clipboard content, expired/revoked token, missing scopes, or token from a different GitLab instance. Re-create the token; do not try to recover it from browser state.
- For self-managed GitLab OAuth/web login, `glab auth login --web` may fail with `Set 'client_id' first...` unless the instance has an OAuth application configured for glab. Use PAT stdin auth unless admin OAuth configuration is available.

## Readiness checks before automatic merge

Run these before claiming an auto-merge workflow is available:

```bash
git fetch origin --prune
git status --short --branch
glab auth status --hostname <gitlab-host>
glab api user
```

Then inspect project/MR capabilities through glab/API:

- project path and numeric id
- target branch protection and who can merge
- whether approvals are required
- whether pipeline must pass
- whether merge trains or squash are required
- whether `merge_when_pipeline_succeeds` / auto-merge is accepted by the instance

If auth is unavailable, only claim push-option MR creation as a possible path, not verified auto-merge.

## Push-option MR creation fallback

When API auth is unavailable but SSH push works, GitLab push options may create an MR:

```bash
git push origin HEAD \
  -o merge_request.create \
  -o merge_request.target=<target-branch> \
  -o merge_request.title="<title>" \
  -o merge_request.remove_source_branch
```

Some instances support:

```bash
-o merge_request.merge_when_pipeline_succeeds
```

Treat this as best-effort unless you can read back MR state via API or UI. It does not prove the MR merged.

## Verification evidence

A complete GitLab auto-merge claim needs fresh evidence from the same task slice:

- fresh remote refs after fetch
- authenticated `glab api user` or equivalent API success
- created MR iid/web_url
- MR mergeability/conflict status
- pipeline/check status or explicit statement that no pipeline is configured
- approval/protected-branch blockers, if any
- final MR state after merge or explicit queued auto-merge state
