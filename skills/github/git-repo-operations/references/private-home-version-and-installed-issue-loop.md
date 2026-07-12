# Private home versioning + installed-system issue loop

Use this when a private Hermes-home / capability-pack repository needs a reproducible version lane and a maintainer loop for installer-reported problems.

Applicability:
- Private home/capability-pack repos where durable assets live in the repo, while live runtime state stays local.
- Versioned releases intended for trusted installers to check/update.
- Installed-system diagnostics that may open GitHub issues in the private repo.

Anti-conditions:
- Runtime Hermes Agent core changes: land those in the runtime fork branch first, then update the home repo gitlink if needed.
- Open-source upstream contributions: branch from upstream main and keep private home assets out.
- Full third-party installer UX certification: requires a real separate installer machine/user and should be named as an exclusion unless performed.

## Branch / repo matrix

Before changing anything, write down the target matrix:

```text
home/capability pack:   <private-home-repo>:master or default branch
runtime private fork:   <runtime-private-fork>:private/main or configured fork branch
upstream runtime:       <upstream-runtime-repo>:main
```

Do not treat `origin/master` generically. In a home repo, `origin/master` may be the private home branch, while runtime code may live in a child repo with a different private branch.

## Safe implementation path

1. Create a clean worktree from the private home remote branch, not from a dirty live `~/.hermes` checkout.
2. Add or update:
   - version manifest with `current_version` / `candidate_version`;
   - install-same-experience runbook;
   - update checker script;
   - installed-system issue reporter with local-only default;
   - issue template and labels;
   - version doctor and tests.
3. For private/fork installs, make update detection use one shared **UpdateTarget** resolver rather than scattering `origin/main`, `upstream/main`, or PyPI assumptions across CLI surfaces. The resolver should derive `{channel, source, remote, branch, compare_ref, update_command, can_apply}` from explicit flags first, then install metadata such as `install.json`, then the current branch tracking ref, then private-origin/official-origin fallbacks. Wire every surface to that resolver: `update --check`, actual `update`, `version`, CLI/TUI update badge, dashboard update endpoint, and recent-commits/changelog range.
4. Add a self-check for the split-brain pitfall: a checkout whose origin is a private fork but whose install metadata is absent or stale may update-check against public upstream/main in some surfaces while `hermes update` targets a fork branch elsewhere. Treat this as a warning/proposal to restamp install metadata or set the intended branch, not as proof the runtime is outdated.
5. Keep installer diagnostics local-only by default. Require explicit `--submit --github-repo OWNER/REPO` before `gh issue create`.
6. Redact token/private-key-shaped values before writing issue body.
7. Dedupe issue submissions by a stable fingerprint; require `--force` to resubmit duplicates.
8. Open a PR from the candidate branch, merge only after tests/readbacks pass.
9. Create stable tag after the merged commit is final and the manifest's `current_version` is stable, not candidate.
10. Read back remote branch/tag with `git ls-remote` and the manifest from the tag.
11. Smoke the installed-system issue loop with a clearly marked smoke issue, then comment and close it.
12. Record a certification/closure receipt if the release is intended to be claimed as closed.

## UpdateTarget split-brain hardening checklist

When unifying private/public update checks, make the resolver the only source of target facts, and make old caches target-aware:

- Resolution precedence: explicit CLI flag → installer metadata (`install.json` or equivalent) → private-origin fallback → current branch tracking ref → public fallback.
- Cache entries must include a stable target key such as `remote/branch:source:channel`; invalidate old cache entries when install metadata appears, disappears, or changes channel/branch. Do not reuse an `origin/main` result after a private-channel restamp.
- Shallow checkouts must fetch only the resolved remote/branch with `--depth 1`, then compare tip SHAs. Do not run `rev-list --count` across a shallow boundary.
- Dashboard or UI changelog ranges must use the same `compare_ref` as the behind-count path (`HEAD..<compare_ref>`). A count from one target and commit list from another is a split-brain bug.
- Add a read-only startup/selfcheck probe for update target health. For private origin + missing install metadata, report a warning with a restamp command/proposal; do not auto-write metadata during ordinary startup.
- Verification should cover the CLI apply/check path, passive banner/version path, dashboard endpoint/changelog path, startup/selfcheck probe, side-effect flags, and a real readback on the active checkout.

## Stable tag consistency pitfall

If a stable tag is cut while the manifest still says `*-candidate`, fix immediately:

1. Commit a manifest-only correction on the target branch setting `current_version` to the stable tag.
2. Push the corrected branch.
3. Move the just-created stable tag to the corrected commit.
4. Force-push only that tag, then read back:

```bash
git ls-remote origin refs/heads/<branch> refs/tags/<stable-tag> refs/tags/<stable-tag>^{}
git show refs/tags/<stable-tag>:docs/private/version-ops/private-version-manifest.json
```

This is acceptable only for a freshly created candidate/stable tag that has not been externally consumed; otherwise publish a new patch version instead.

## Verification checklist

Minimum evidence before claiming scoped release closure:

```text
PR state: merged/read back
origin branch commit: exact hash
stable tag peeled commit: same exact hash as branch
manifest from stable tag: current_version == stable tag
update checker: current == latest == stable tag, update_available false
version doctor: ok true, blockers 0
unit tests: pass
changed scripts: py_compile pass
issue reporter smoke: issue created/read/commented/closed or explicitly excluded
```

When using multi-model / independent verifier gates, make evidence IDs support the normalized claim IDs consumed by the verifier (for example `C-001`, not only `C1`) or the truth gate may show 0 coverage despite valid raw evidence.
