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
4. Add a deterministic sanitizer/selfcheck that rejects forbidden basenames, path parts, secret-like text, owner-local paths, and lived-state payloads. It should fail on concrete owner paths such as `/Users/<owner>`, real credentials, `.env`, auth/OAuth files, memory/profile/session DBs, logs, locks, backups, `docs/private`, `state.db`, and runtime cache DB payloads such as `contextcards*.db`. Policy docs may name forbidden payload classes, and templates may use `$HERMES_HOME/...` placeholders, but actual state files must not be packaged.
5. Keep the pack manifest explicit: `package: capability_shape`, `exclude: lived_state`, `overwrite_existing: false`, `default_enabled: false`, and activation gates such as `cron: manual_enable`, `gateway_delivery: manual_configure`, `shell_hooks: user_approval_required`, `contextcard_promotion: explicit_promote_flag`, and `taskpool_mutation: explicit_authority`.
6. Extend the installer to copy missing template files into `$HERMES_HOME/templates/<bundle>` without overwriting user edits.
7. Provide an opt-out flag such as `--skip-experience-pack`.
8. Test sanitizer pass/fail fixtures, default install dry-run, install no-overwrite behavior, and skip dry-run.
9. Commit only the scoped bundle/installer/test files; leave unrelated runtime dirtiness unstaged.

## Enterprise-grade minimum bundle shape

A production-grade first slice should include at least:

- `manifest.yaml` declaring copy policy, forbidden payloads, and activation gates;
- `README.md` explaining that the pack carries capability shape, not lived state;
- template task(s), for example external capability absorption with evidence/reproduction/harness/rollback/maintenance/promotion gates;
- hook registry examples that default to disabled and classify hooks as `gate`/`advisor`/`observer` with fail policy;
- promotion checklists for shadow/staging → production paths;
- optional config examples using `$HERMES_HOME` placeholders only;
- a sanitizer script plus tests proving clean packs pass and owner paths/runtime DBs/secrets/private paths fail.

Do not count the pack as distributable until the sanitizer passes on the pack directory and the sanitizer’s own negative fixtures fail as expected.

## Anti-conditions

- Do not use this pattern as a backup/restore mechanism for the owner.
- Do not turn one user’s project facts into global defaults.
- Do not silently enable external delivery, publication, task enqueue, or executors; examples must remain gated by exact target and approval.
