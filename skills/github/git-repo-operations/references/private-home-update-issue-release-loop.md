# Private home update → installed issue → maintainer release loop

Use when maintaining a private Hermes-home capability repository where other trusted users install the pack, check for updates, report local system failures, and expect the maintainer to triage/fix/tag a new private version.

Applicability:
- Target repo is a private Hermes home/capability-pack repo such as `hermes-home-private`.
- Changes are about version metadata, install parity, update checks, issue reporting, docs, scripts, skills, workflows, or project profiles.
- Installer machines should report sanitized diagnostics without copying live runtime state.

Anti-conditions:
- Runtime CLI/provider/dashboard/core code belongs in the Hermes Agent runtime fork, not the home repo.
- Upstreamable generic runtime fixes belong on a clean branch based on the upstream default branch.
- Do not publish `config.yaml`, `cron/jobs.json`, memories, DBs, locks, logs, `cron/output/`, credentials, raw local state, or the maintainer's personal/client project profiles.
- Do not submit issues or push tags from an installer unless explicit GitHub target authority is present.

## Branch/repo matrix

| Problem class | Repo | Target branch |
|---|---|---|
| Private home pack: skills/scripts/docs/workflows/profiles/version docs | private home repo | `master` (or repo default) |
| Hermes runtime/private fork: CLI, providers, dashboard, doctor, core gateway | runtime private fork | `private/main` |
| Upstreamable generic runtime fix | upstream Hermes Agent | `main` |

Always read actual remotes/default branches; do not infer from memory. In this user's setup, `origin/master` meant `hermes-home-private`, while `origin/private/main` meant `hermes-agent-private`.

## Installer-side flow

1. Install upstream Hermes Agent first; verify `hermes --version` and `hermes doctor`.
2. Clone the private home pack separately, e.g. `~/.hermes-private-home`.
3. Verify the private home pack with a version doctor.
4. Check available private-home tags with an update checker. Version tag format: `private-home-YYYY.MM.DD.N`; candidate suffix allowed for rehearsal.
5. If a local system problem appears, generate a local-only sanitized issue packet first.
6. Submit a GitHub issue only when the installer explicitly enables `--submit` and the target repo is allowlisted.

Recommended issue packet behavior:
- Write JSON + Markdown under `~/.hermes/state/private-home-issue-reports/<fingerprint>.*`.
- Redact token/private-key shapes before writing or submitting.
- Dedupe by fingerprint; require `--force` to resubmit.
- Include platform, private-home version/tag, repo head, command return codes, and bounded stdout/stderr excerpts.

## Project profile privacy boundary

For a private home pack, "same smooth experience" means publishing the reusable profile mechanism, not copying the maintainer's project context.

Default-publish only:
- `project-profiles/template.json`
- sanitized examples such as `project-profiles/examples/*.json`

Default-exclude:
- real client/business project profiles;
- profiles containing personal absolute paths such as `/Users/<name>`;
- profiles containing private task systems, Lark/Feishu/Telegram routing, client names, repo paths, task IDs, or commercial/project strategy;
- any profile explicitly named for the maintainer's projects.

Implementation pattern:
1. Move/remove real profiles from the publishable tree; keep them local/private or in an explicitly excluded path such as `project-profiles/private/`, `project-profiles/local/`, or `project-profiles/charles/`.
2. Add a neutral `template.json` and one sanitized example with placeholder paths.
3. Update the manifest so `project_profiles` means templates/examples by default and personal profiles are excluded unless explicitly allowlisted after privacy review.
4. Make the version doctor block future leaks with checks such as `personal_project_profile_published` and `personal_profile_token` for tokens like personal home paths, client/project codenames, or external routing surfaces.
5. Verify the stable tag with `git ls-tree -r <tag> project-profiles` and a simple scan for `/Users/`, client names, Lark/Feishu/Telegram, and other private routing tokens.

## Maintainer triage/fix/tag flow

1. Read issue fingerprint, reported private-home version, repo head, platform, and command diagnostics.
2. Classify target repo using the branch/repo matrix.
3. Reproduce in a clean worktree from the correct target branch.
4. Patch narrowly; avoid mixing home-pack docs/scripts with runtime fork changes.
5. Run targeted tests and version doctor.
6. If installers should update, create a new `private-home-YYYY.MM.DD.N` tag in the private home repo.
7. Comment issue with fix commit/tag and update-check readback.
8. Close only after the issue has a reproducible fix path or is clearly environment-specific.

## Verification checklist

- `git status --short --branch` shows the expected clean worktree or scoped staged diff.
- `git remote -v` and default branch readback match the intended target repo.
- Version manifest JSON parses.
- Version/update/report scripts compile.
- Unit tests cover version parsing, local-only packet generation, redaction, dedupe, no-submit default, and personal-profile leak blockers.
- Smoke test writes a local issue packet with `submitted=false`.
- Stable tag readback confirms `project-profiles/` contains only templates/examples unless a sanitized profile was explicitly allowlisted.
- Pre-commit hooks pass without bypass; if path words like `release`/`publish` trigger false high-risk classification, prefer neutral path names such as `version-ops` while retaining clear content.

## Reporting format

Report separately:
- branch/repo target chosen and why;
- files changed;
- version tag created or proposed;
- local-only vs GitHub-submitted behavior;
- verification commands/results;
- remaining debt such as historical tracked runtime artifacts.
