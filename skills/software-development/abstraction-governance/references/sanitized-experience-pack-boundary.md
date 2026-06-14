# Sanitized Experience Pack Boundary

Use when turning a mature personal/local Hermes setup into something other users can install without inheriting private memory, credentials, or runtime state.

## Principle

Package the *capability shape*, not the owner's lived state.

Safe to distribute:

- setup and post-install checklists;
- non-secret config templates with placeholders;
- persona/style templates without personal memories;
- project-profile schema examples with fake URLs and roles;
- cron/job examples that default to local/origin delivery;
- installer metadata and update-channel wiring;
- deterministic selfcheck scripts that scan the bundle for forbidden files/text.

Do not distribute:

- live `config.yaml`, `.env`, auth files, OAuth sessions, API keys, tokens;
- memory/user profile/session DBs;
- real project profiles, client facts, production URLs, local brain vaults;
- logs, checkpoints, runtime DBs, taskpool evidence, cron/gateway state;
- local absolute user paths or owner-specific repo/org names except the distribution repo itself.

## Implementation pattern

1. Inventory local experience sources and classify them as: code, reusable template, optional overlay, secret, runtime state, personal memory, project fact.
2. Create a template-only bundle under the code distribution repo.
3. Add a manifest with `copied` and `not_copied` lists.
4. Add a deterministic selfcheck that rejects forbidden basenames, path parts, secret-like text, and owner-local paths.
5. Extend the installer to copy missing template files into `$HERMES_HOME/templates/<bundle>` without overwriting user edits.
6. Provide an opt-out flag such as `--skip-experience-pack`.
7. Test both default install dry-run and skip dry-run.
8. Commit only the scoped bundle/installer/test files; leave unrelated runtime dirtiness unstaged.

## Anti-conditions

- Do not use this pattern as a backup/restore mechanism for the owner.
- Do not turn one user’s project facts into global defaults.
- Do not silently enable external delivery, publication, task enqueue, or executors; examples must remain gated by exact target and approval.
