# Installed System Issue and Version Update Flow

Status: proposed
Scope: trusted installs of `Charles-beta-he/hermes-home-private`

## Goal

Create a closed operational loop:

```text
installer checks private-home version
→ local system doctor detects problem
→ sanitized issue packet is written locally
→ optional GitHub issue is submitted to the private home repo
→ maintainer triages the issue
→ maintainer decides target repo and patches in a clean worktree
→ tests/readbacks pass
→ private-home version tag is cut
→ installer update check sees the new version
```

## Roles

| Role | Responsibility |
|---|---|
| Installer machine | Run local doctors, redact diagnostics, write issue packets, optionally submit GitHub issue |
| Private home maintainer | Triage issue, decide target repo, patch, verify, tag private-home version |
| Hermes Agent private fork maintainer | Patch runtime code under `hermes-agent-private:private/main` when the issue is runtime/core |
| Upstream maintainer | Receives only clean upstream-suitable patches based on `NousResearch/hermes-agent:main` |

## Repositories and target branches

| Problem class | Repo | Target branch |
|---|---|---|
| skills/scripts/docs/workflows/project-profiles/install pack | `Charles-beta-he/hermes-home-private` | `master` |
| Hermes runtime/CLI/provider/dashboard/doctor/core gateway code | `Charles-beta-he/hermes-agent-private` | `private/main` |
| Upstreamable generic Hermes Agent fix | `NousResearch/hermes-agent` | `main` |

Do not submit private home state, private workflow docs, credentials, or local runtime artifacts to upstream.

## Installer-side update check

From a private-home checkout:

```bash
python3 scripts/private_home_update_check.py check --repo-root . --remote origin --json
```

The checker reads:

```text
docs/private/version-ops/private-version-manifest.json
remote tags matching private-home-*
```

Stable tags use:

```text
private-home-YYYY.MM.DD.N
```

Candidate tags may use:

```text
private-home-YYYY.MM.DD.N-candidate
```

## Installer-side issue packet

Local-only packet, no network submit:

```bash
python3 scripts/private_home_update_check.py report \
  --repo-root ~/.hermes-private-home \
  --hermes-home ~/.hermes \
  --reason "hermes doctor failed after private-home install" \
  --json
```

This writes:

```text
~/.hermes/state/private-home-issue-reports/<fingerprint>.json
~/.hermes/state/private-home-issue-reports/<fingerprint>.md
```

The report redacts common token/private-key shapes and records command return codes/stdout/stderr excerpts.

## Optional auto-submit to GitHub issue

External side effect. Only enable when the installer has GitHub CLI auth and explicit repo allowlist.

```bash
python3 scripts/private_home_update_check.py report \
  --repo-root ~/.hermes-private-home \
  --hermes-home ~/.hermes \
  --reason "hermes doctor failed after private-home install" \
  --github-repo Charles-beta-he/hermes-home-private \
  --submit \
  --json
```

Safety properties:

- default is local-only;
- `--submit` is explicit;
- duplicate fingerprints are not resubmitted unless `--force` is used;
- issue body is written locally before any GitHub call;
- labels: `installed-system`, `automated-report`;
- no credentials are read from repo files.

## Maintainer triage flow

When an issue arrives:

1. Read issue fingerprint, private-home version, repo head, platform, and command diagnostics.
2. Classify target:
   - private home capability pack;
   - Hermes Agent private runtime fork;
   - upstream Hermes Agent;
   - installer-specific environment/config.
3. Reproduce in clean worktree:
   - home pack: clean worktree from `hermes-home-private:master`;
   - runtime fork: clean worktree from `hermes-agent-private:private/main`;
   - upstream: clean branch from `NousResearch/hermes-agent:main`.
4. Patch narrowly.
5. Run targeted tests and private version doctor.
6. Comment issue with commit/tag/readback.
7. Tag new private-home version when installers should update.
8. Close issue only after the fix path and update check are documented.

## Maintainer fix-to-version commands

Home pack fix:

```bash
git fetch origin --prune
git worktree add /tmp/hermes-home-fix origin/master
cd /tmp/hermes-home-fix
# patch
python3 scripts/private_version_doctor.py . --json
python3 -m unittest scripts/test_private_version_doctor.py scripts/test_private_home_update_check.py
python3 -m pytest scripts/tests/test_dynamic_selfcheck_coverage.py -q
git commit -m "fix(private-home): <issue summary>"
git tag -a private-home-YYYY.MM.DD.N -m "Private home version YYYY.MM.DD.N"
git push origin HEAD:master
git push origin private-home-YYYY.MM.DD.N
```

Runtime fork fix:

```bash
cd ~/.hermes/hermes-agent
git fetch origin upstream --prune
git checkout -B fix/<issue-id> origin/private/main
# patch runtime code
# run focused tests
git push origin HEAD:fix/<issue-id>
```

Then update the parent `hermes-home-private` gitlink only after the runtime private fork commit is pushed and read back.

## Issue states

| State | Meaning |
|---|---|
| `needs-triage` | New installed-system report |
| `home-pack` | Fix belongs in `hermes-home-private` |
| `runtime-fork` | Fix belongs in `hermes-agent-private` |
| `upstream-candidate` | May be suitable for `NousResearch/hermes-agent` |
| `environment-specific` | Installer config/system issue, no version change yet |
| `fixed-pending-version` | Patch exists; waiting for private-home tag |
| `released` | Version tag pushed and update check can discover it |

## Non-goals

- No automatic patching from issue content.
- No automatic close without maintainer readback.
- No automatic push/deploy from installer machines.
- No secret upload.
- No broad fanout notifications.
