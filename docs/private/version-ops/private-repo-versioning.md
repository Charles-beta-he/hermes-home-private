# Private Hermes Home Release Argument and Version Management

Date: 2026-07-06
Status: proposed
Scope: `Charles-beta-he/hermes-home-private` / private Hermes home repository

## Objective model

Success means a trusted installer can reproduce the high-leverage parts of Charles' Hermes experience without inheriting live secrets, local runtime drift, personal memories, or unsafe side effects.

The private repository should therefore publish:

1. durable capability assets: skills, scripts, project profiles, workflow SSOTs, tests, docs, version manifests;
2. exact version evidence: commit, tag, release lane, capability manifest, verification commands;
3. safe bootstrap instructions: disabled-by-default activation, local-only receipts, explicit gates for external effects;
4. operational boundaries: what is intentionally not versioned and what must be recreated locally.

It should not publish:

- credentials, API keys, OAuth tokens, cards, passwords, cookies;
- live config such as `config.yaml` or `cron/jobs.json`;
- DBs, locks, logs, session histories, gateway state, delivery queues;
- runtime output such as `cron/output/`;
- personal memories or private one-off task state unless explicitly transformed into durable skills/docs.

## Release thesis

The repo is not a normal app binary. It is a private "Hermes home distribution" with four separable strata:

| Stratum | Contents | Release posture |
|---|---|---|
| Runtime substrate | upstream/private `hermes-agent` checkout, CLI, provider adapters | pinned by submodule/ref; released in child repo first |
| Capability pack | `skills/`, `scripts/`, `project-profiles/`, `workflows/`, `docs/private/` | versioned here |
| Local activation | config, cron jobs, gateways, memories, DBs, state | not versioned; recreated by installer/runbook |
| High-risk adapters | push/deploy/external delivery/hardware/payment/destructive actions | gated; never auto-enabled |

The same smoothness comes from the interaction of all four strata. A private release can only ship the first two and provide safe recipes for the third/fourth.

## Version model

Use release names that make it obvious this is not upstream Hermes Agent:

- Stable tag: `private-home-YYYY.MM.DD.N`
- Candidate branch: `release/private-home/YYYYMMDD-N`
- Local lab branch: `lab/<topic>`
- Scoped feature branch: `feat/<capability>` or `docs/<capability>`

Example:

```text
private-home-2026.07.06.1
release/private-home/20260706-1
```

Each stable private-home tag must have a version manifest under:

```text
docs/private/version-ops/private-version-manifest.json
```

and a release note or ADR-style document that answers:

1. What capability surface changed?
2. What must another installer copy or activate?
3. What remains local-only or gated?
4. What tests/readbacks passed?
5. What upstream `hermes-agent` ref is expected?

## Channel model

| Channel | Use | Allowed surfaces | Promotion gate |
|---|---|---|---|
| `stable` | trusted operator install | skills, scripts, docs, profiles, HEWOS/static workflows | doctor no blockers + tests + manifest |
| `candidate` | release rehearsal | same as stable plus new docs/scripts | install dry-run + targeted tests |
| `lab` | active experiments | branch-local docs/scripts/evidence | no installer claims |
| `local-only` | this machine's runtime | cron jobs, configs, DBs, gateway, delivery state | never push as release |

## Repository content contract

Publishable:

- `skills/**`: reusable procedures and references;
- `scripts/**`: local automation and tests, with py_compile/targeted tests;
- `project-profiles/*.json`: durable project navigation and policies;
- `workflows/**`: SSOTs, project docs, local harnesses, tests, verification artifacts;
- `docs/private/**`: durable private evidence and architecture notes;
- `schemas/**`, `templates/**`, selected `fixtures/**` when no secrets;
- `hermes-agent` pointer only after the child repo is itself clean and pushed.

Non-publishable:

- `config.yaml`, `config/quorum.yaml`, `cron/jobs.json`, `memories/`;
- `state/`, `sessions/`, `logs/`, `cron/output/`, `gateway_state.json`;
- `*.db`, `*.lock`, `*.pid`, cache directories, runtime queues;
- raw screenshots/media unless promoted through a manifest-backed evidence directory;
- secrets/auth material of any form.

Historical debt note: the current repo still contains some old tracked runtime artifacts such as `cron/output/*` and lock files. New releases should not add more. A future cleanup release should remove historical runtime artifacts behind a separate backup/readback gate.

## Private repo publication gates

Before tagging or pushing a private-home release:

```bash
python3 scripts/private_version_doctor.py . --json
python3 -m py_compile scripts/private_version_doctor.py
python3 -m unittest scripts/test_private_version_doctor.py
python3 -m py_compile scripts/dynamic_selfcheck_coverage.py
python3 -m pytest scripts/tests/test_dynamic_selfcheck_coverage.py -q
```

If the release touches HEWOS:

```bash
python3 -m pytest workflows/projects/hermes-embodied-workflow-os/implementation/tests -q
```

If the release touches `hermes-agent` child repo:

```bash
git -C hermes-agent status --short --branch
# then use the child repo's focused pytest or scripts/run_tests.sh
```

## Other-person install argument

Another person cannot get the exact same experience by cloning the repo alone. They need:

1. official Hermes Agent installed and healthy;
2. this private capability pack copied/imported;
3. model provider credentials configured locally by the human;
4. optional gateway/platform credentials configured locally;
5. local-only cron/selfcheck jobs recreated from runbooks;
6. external actions intentionally activated one by one with readback.

The install process must be staged because the smoothness comes from safe local activation, not from shipping live state.

## Release checklist

- [ ] `git status --short --branch` clean in the release worktree.
- [ ] `private_version_doctor.py` returns no blockers.
- [ ] Manifest updated when capability surface changes.
- [ ] Install-same-experience runbook updated when activation steps change.
- [ ] New scripts compile and have tests or explicit scoped reason.
- [ ] Runtime artifacts are not newly tracked.
- [ ] Child `hermes-agent` changes are committed/pushed in the child repo before parent pointer moves.
- [ ] Tag or push target explicitly named.
- [ ] Post-push readback uses `git ls-remote`/commit hash.

## Consequence

This separates "release a reproducible private capability pack" from "copy Charles' live machine". The first is safe and useful; the second is both unsafe and impossible without secrets and runtime state.
