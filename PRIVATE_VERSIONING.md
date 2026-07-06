# Hermes Private Home Release Index

This repository is the private Hermes home distribution layer: skills, scripts, project profiles, workflow SSOTs, release governance, and local-first automation around the upstream Hermes Agent runtime.

Authoritative version docs:

- `docs/private/version-ops/private-repo-versioning.md` — version argument, channel model, version policy, repository boundaries, and promotion gates.
- `docs/private/version-ops/install-same-experience.md` — how another trusted operator installs enough of this private home to approach the same smoothness and experience without inheriting secrets or live runtime state.
- `docs/private/version-ops/installed-system-issue-flow.md` — installed-machine update check and sanitized GitHub issue report flow.
- `docs/private/version-ops/private-version-manifest.json` — machine-readable capability/channel manifest for this version lane.
- `scripts/private_version_doctor.py` — local version readiness scanner.
- `scripts/private_home_update_check.py` — installer-side update checker and issue packet/submission helper.

Core rule: publish durable capabilities, docs, skills, scripts, tests, profiles, and workflow SSOTs; never publish live config, secrets, logs, DBs, locks, runtime queues, or delivery credentials.

Current release posture:

- Stable capability core: skills, scripts, project profiles, HEWOS implementation, dynamic self-check coverage.
- Runtime activation: local-only and disabled-by-default for other installers.
- External side effects: exact target + payload + readback authority required.
