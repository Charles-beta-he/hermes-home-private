# Downstream release target vs upstream sync boundary

Use this reference for forked/downstream projects that have both:

- a downstream release branch that ordinary installations should update from; and
- an upstream source branch that maintainers periodically absorb.

Applicability: class-level fork/downstream release governance. This is not a record of any one repository's current branch names, remotes, or progress.

## Core distinction

Do not collapse these into one update target.

- `release_target`: what ordinary users/installations update to. This is the blessed, verified distribution target.
- `sync_source`: what maintainers compare against when preparing the next downstream release.
- `owner/maintainer mode`: explicit, read-only by default, and separate from ordinary update/apply commands.

Ordinary update commands should answer only: "is this installation behind its release target?"

Maintainer sync commands should answer only: "is the downstream release target behind the upstream source, and what plan would safely absorb it?"

Keep these output surfaces separate so a user who is up to date with the downstream release is not incorrectly told to update directly from upstream.

## Safe command shape

A first landing should be read-only:

```text
<tool> update --upstream-check
<tool> update --upstream-sync --plan
```

These may fetch and compare refs, but must not:

- merge;
- rebase;
- push;
- install dependencies;
- mutate lifecycle state;
- rewrite install metadata.

If an apply command exists later, require a separate explicit authority gate and fresh readback evidence.

## Maintainer sync plan ladder

A plan-only maintainer command can print a ladder like:

1. create an isolated integration branch from the downstream release target;
2. merge or rebase the upstream source inside that isolated branch;
3. resolve conflicts while preserving downstream/private overlays;
4. run tests and post-update validation;
5. merge/push to the downstream release target only after verification.

## Detection hints

Prefer explicit metadata over heuristics. Useful signals include:

- install metadata channel/branch/origin/upstream;
- origin remote canonical repository;
- upstream remote canonical repository;
- current branch tracking ref;
- explicit CLI flags.

Do not use push permission alone to silently enter maintainer mode. Owner/dev behavior should require an explicit command such as `--upstream-check` or `--upstream-sync --plan`.

## Verification checklist

- Ordinary update/check still compares against the downstream release target.
- Maintainer check compares downstream release target against upstream source.
- Tests assert no accidental `pull`, `merge`, `rebase`, `push`, or dependency install occurs in read-only maintainer checks.
- CLI output states side effects explicitly.
- Real command readback shows the target refs and side-effect boundary.

## Anti-conditions

Do not use this reference for:

- public installs with no downstream release branch;
- one-off local feature branches;
- external project sync where branch policy is unknown;
- automatically deciding that upstream is authoritative for an end user install.
