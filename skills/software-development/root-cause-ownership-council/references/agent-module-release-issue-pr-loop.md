# Agent Module Release Issue/PR Loop

Use when a reusable agent-module skill is ready to be treated as a versioned release instead of a local-only edit.

Scope: class-level release hygiene for agent-module skill changes. Do not encode concrete repositories, branch names, issue numbers, PR numbers, or project URLs here; resolve them from the active repo and live issue/PR readback each time.

## When to use

Use this loop when:

- an agent-module skill version was bumped;
- supporting files were added under `references/`, `templates/`, or `scripts/`;
- the user says the module is acceptable as a version release;
- the change should be reviewed/merged through normal repo workflow rather than remaining only in local skills.

Do not use when:

- the edit is temporary/private local state;
- no repo or remote review workflow exists;
- the user explicitly asked for local-only changes;
- validation failures remain unresolved.

## Procedure

1. Validate the package before publication.
   - Frontmatter starts at byte 0 with `---` and parses as YAML.
   - `name`, `description`, and `version` are present.
   - All newly referenced support files exist.
   - The body states authority boundaries if the module could be mistaken for runtime permission.

2. Use a scoped release branch from the intended base.
   - Prefer a clean temporary worktree when the home/control-plane repo is dirty.
   - Copy/stage only the intended skill/module directory.
   - Run `git diff --cached --check` before commit.
   - Run a lightweight secret-pattern scan that looks for credential-shaped values, not ordinary words such as "token" in explanatory prose.

3. Push the branch and read back the remote ref.
   - Verify remote branch SHA equals the local commit.
   - Read back a key file from the remote ref and confirm the expected version string.

4. Create a tracking issue when the user says to handle issues or when a release needs review traceability.
   - The issue should describe summary, scope, acceptance criteria, verification evidence, and non-goals.
   - Label it according to the repo taxonomy.
   - Remove triage labels only after a concrete PR or decision is attached.

5. Create a PR from the release branch.
   - Include `Closes #<issue>` only when the PR actually satisfies the issue acceptance criteria.
   - Summarize changed files/classes, validation commands, and authority boundaries.
   - Do not auto-merge unless separately authorized.

6. Read back both issue and PR state.
   - Issue: number, state, labels, comments/triage note.
   - PR: number, state, draft flag, mergeability, head/base, linked closing issue.
   - Report links and exact readback evidence.

## Pitfalls

1. Treating a pushed branch as a release without remote file/version readback.
2. Letting a dirty home/control-plane repo leak unrelated files into a module release.
3. Using over-broad secret grep that fails on documentation words; scan credential-shaped values instead.
4. Creating an issue but leaving it untriaged after a PR exists.
5. Adding `Closes #...` before the PR truly satisfies the acceptance criteria.
6. Auto-merging from a generic "handle issue" request; issue/PR creation is not merge authority.
