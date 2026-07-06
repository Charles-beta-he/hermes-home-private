# Hermes Private Home Release Index

This repository is the private Hermes home distribution layer: skills, scripts, project profiles, workflow SSOTs, release governance, and local-first automation around the upstream Hermes Agent runtime.

Authoritative release docs:

- `docs/private/version-ops/private-repo-versioning.md` — release argument, channel model, version policy, repository boundaries, and promotion gates.
- `docs/private/version-ops/install-same-experience.md` — how another trusted operator installs enough of this private home to approach the same smoothness and experience without inheriting secrets or live runtime state.
- `docs/private/version-ops/private-version-manifest.json` — machine-readable capability/channel manifest for this release lane.
- `scripts/private_version_doctor.py` — local release readiness scanner.

Core rule: publish durable capabilities, docs, skills, scripts, tests, profiles, and workflow SSOTs; never publish live config, secrets, logs, DBs, locks, runtime queues, or delivery credentials.

Current release posture:

- Stable capability core: skills, scripts, project profiles, HEWOS implementation, dynamic self-check coverage.
- Runtime activation: local-only and disabled-by-default for other installers.
- External side effects: exact target + payload + readback authority required.
