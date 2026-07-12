# Private home version pack from a dirty/diverged control-plane repo

Applicability: use when a Hermes/control-plane home repository is dirty, diverged, or contains local runtime state, and the user asks to prepare version/release/install documentation or a publishable private-home package. This is for packaging durable capability surfaces; it is not a substitute for pushing/deploying.

Anti-conditions:
- Do not run directly in the user's dirty home worktree when it has unrelated state.
- Do not publish `config.yaml`, `cron/jobs.json`, memories, DBs, locks, logs, cron output, gateway state, credentials, or live runtime queues.
- Do not move a parent repo's submodule pointer unless the child repo was separately cleaned, committed, tested, and pushed.
- Do not interpret a versioning/package commit as authorization to push tags or branches.

## Procedure

1. Create a clean worktree from the remote baseline:
   ```bash
   cd ~/.hermes
   git fetch origin --prune
   git worktree add -b private-version-pack-YYYYMMDD /tmp/hermes-private-version-pack origin/master
   cd /tmp/hermes-private-version-pack
   git status --short --branch
   ```

2. Land version/package artifacts only in the clean worktree:
   - top-level private versioning index, e.g. `PRIVATE_VERSIONING.md`;
   - `docs/private/version-ops/` runbooks and manifest;
   - a deterministic doctor script plus tests, e.g. `scripts/private_version_doctor.py` and `scripts/test_private_version_doctor.py`.

3. Keep path names low-side-effect for local precommit gates.
   - Words such as `release`, `publish`, `deploy`, and `push` in staged paths or generated summaries may be classified as high-risk side-effect surfaces.
   - Prefer `version-ops`, `private_version_*`, or `home-pack` path names for documentation-only packaging work.
   - Preserve the actual release/version argument inside prose, but avoid path names that trip side-effect classifiers.

4. Versioning document content should separate four strata:
   - runtime substrate: upstream/private Hermes Agent checkout and CLI;
   - capability pack: skills, scripts, profiles, workflows, durable docs/tests;
   - local activation: config, cron jobs, gateways, memories, DBs, state;
   - high-risk adapters: external delivery, push/deploy/publish, hardware, destructive, credential/payment.

5. Install-same-experience runbooks should be layered:
   - L0 upstream runtime healthy (`hermes doctor`);
   - L1 private skills;
   - L2 private scripts;
   - L3 project profiles;
   - L4 workflow SSOTs;
   - L5 optional local-only cron/selfcheck;
   - L6 optional gateway/external delivery with exact target/readback;
   - L7 optional hardware/embodied adapters with safety gates.

6. Add a repository doctor that is strict about blockers but tolerant of known historical debt:
   - block on missing required version files, invalid manifest, or real token/private-key-shaped values;
   - warn, do not block, on historical tracked runtime artifacts when the task is not a cleanup release;
   - treat placeholder/example tokens in tests/docs as warnings or allowed placeholders, not real secrets.

7. Verify before commit:
   ```bash
   python3 -m py_compile scripts/private_version_doctor.py
   python3 -m unittest scripts/test_private_version_doctor.py
   python3 scripts/private_version_doctor.py . --json
   python3 -m json.tool docs/private/version-ops/private-version-manifest.json >/tmp/private-version-manifest.pretty.json
   git diff --check
   ```

8. Commit locally with evidence in the message. Do not push unless the user names the remote branch/tag.

## Reporting template

Report:
- worktree path;
- base remote commit;
- local branch and commit;
- tag if created locally;
- files added/changed;
- doctor result (`ok`, readiness, blockers, warnings);
- tests run and outputs;
- explicit statement that push/tag publication was not performed unless authorized.
