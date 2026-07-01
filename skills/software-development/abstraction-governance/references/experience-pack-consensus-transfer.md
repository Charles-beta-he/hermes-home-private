# Experience Pack Consensus Transfer

Use when a mature local Hermes setup contains valuable operating consensus that should help new users without copying the owner's private state.

## Core rule

Transfer the capability shape, not the lived state.

A new user may inherit:
- class-level workflow rules;
- templates and schemas;
- default-off optional modules;
- deterministic selfchecks and doctors;
- anonymized examples;
- explicit activation gates.

A new user must not inherit:
- memories, user profile, project profiles, taskpool history, state/session DBs, logs, private docs, OAuth/auth files, shell-hook approvals, delivery targets, local absolute paths, or runtime caches.

## Consensus layers

Package consensus in layers so users can opt in deliberately:

1. **Core governance** — abstraction governance, SSOT discipline, evidence gates, rollback/fallback, memory/skill landing-zone classifier, hook class/fail policy, open-source capability absorption.
2. **Taskpool control** — status inspection, blocked certification recovery, review/done proof boundary, external capability intake, provider-auth recovery.
3. **Projection/offline companion** — source-authoritative ContextCard/projection schema, exporter/writer templates, staging-to-production promotion, self-ingestion guards, health reports; default disabled.
4. **Local codegraph/intelligence packs** — MCP config templates and smoke-test checklists for local graph indexers such as codebase-memory-mcp; default disabled until binary trust, cache boundary, and project-root indexing authority are verified. Graph output is advisory navigation, not final truth evidence.
5. **Domain delivery packs** — PWA/mobile delivery, Gateway/Telegram reliability, travel execution, or other domain runbooks; optional and sanitized.
6. **Examples** — anonymized case shapes only; no real project names, domains, paths, screenshots, chat IDs, or private evidence.

## Artifact shape

Prefer this bundle structure:

```text
experience-pack/
  manifest.yaml
  README.md
  templates/
    taskpool/
    hooks/
    project-profile/
    cron/
  skills/
  scripts/
    sanitize_check.py
  examples/anonymized/
```

The manifest should declare:
- `package: capability_shape`;
- `exclude: lived_state`;
- `overwrite_existing: false`;
- `default_enabled: false`;
- allowed payload classes;
- forbidden payload classes;
- activation gates for cron, gateway, hooks, promotion, and taskpool mutation.

## Sanitizer requirements

Before packaging or installing, run a deterministic scanner that fails on:
- `.env`, auth/OAuth/token/session files;
- `state.db`, `contextcards*.db`, logs, locks, backups;
- `docs/private`, memories, user profiles, real project profiles, task evidence;
- owner-local absolute paths such as `/Users/<owner>`;
- chat IDs, bot tokens, API keys, bearer tokens, refresh tokens;
- real client/project names when the bundle is intended to be public or generic.

## Rule format for transferable consensus

Convert local experience into rules with this shape:

```text
Name:
Scope:
Applicability:
Anti-conditions:
Rule:
Required evidence:
Operationalization:
Failure mode:
Rollback:
Example:
```

Avoid imperative owner preferences or project-specific facts. If the rule still needs a real project name, branch, path, domain, or person to make sense, it is not ready for a generic experience pack.

## Install behavior

Default install should:
- copy only missing templates;
- never overwrite user edits;
- keep cron, shell hooks, gateway delivery, taskpool mutation, and production promotion disabled until the new user explicitly enables them;
- initialize empty runtime stores instead of copying the owner's databases;
- run a dry-run summary before applying changes.

## Open-box automation standard

A production-grade experience pack is not finished when it only produces an inventory report, sanitizer result, or manually copied template directory. For new-user install, the minimum automated path is:

```text
inventory local consensus/assets
  -> classify landing zones
  -> build or select sanitized pack
  -> doctor/sanitizer fail-close
  -> install into target HERMES_HOME
  -> write activation state with all side effects disabled
  -> write install receipt
  -> verify repeat install skips existing user files
```

Required commands or equivalent surfaces:

- `list` — discover available packs;
- `doctor` — run sanitizer and explain blockers;
- `install --dry-run` — show exact mkdir/copy/write/skip operations without writing;
- `install` — copy safe payloads and create runtime skeleton;
- repeat `install` — no-overwrite by default, report `skip` for existing files.

The installed result should be immediately useful without requiring the user to understand the owner's history: templates, checklists, example configs, receipts, and disabled activation state should all be present. However, "开箱即用" does not mean auto-enabling cron, gateway delivery, shell hooks, taskpool mutation, or production promotion; those remain explicit activation gates.

Verification checklist for this automation:

- focused installer tests cover dry-run, real install, no-overwrite, sanitizer fail-close, and CLI JSON output;
- sanitizer tests cover owner paths, runtime DB payloads, secret-like assignments, forbidden state directories, and placeholder exceptions;
- real pack `doctor` returns ok with zero findings;
- real pack dry-run and real install both succeed into a temporary target home;
- second install produces `skip`/`exists`, not overwrites;
- installed activation state has side-effectful modules disabled.

## Pitfalls

- Copying a working `$HERMES_HOME` as a shortcut. This leaks state and teaches the wrong abstraction boundary.
- Shipping private evidence as examples. Convert to anonymized case shapes or omit.
- Enabling automation on install. Examples and templates must be inert by default.
- Treating optional domain packs as global defaults. Keep them opt-in.
- Promoting local project lessons into global rules without scope, anti-conditions, and falsifiers.
