# Private Hermes repo distribution UX

Use this reference when designing or auditing distribution of a private/custom Hermes line (for example `private/main`) to end users who should not need to understand git remotes, branches, venvs, or upstream sync.

## Recommended end-user contract

When the maintainer can grant private GitHub access before install, use GitHub CLI as the P0 default and hide the rest behind an automated bootstrap plus a private finalizer script:

```bash
gh auth login
gh auth setup-git
gh api -H "Accept: application/vnd.github.raw" \
  repos/<owner>/<private-repo>/contents/scripts/bootstrap-private.sh?ref=private/main \
  | bash
```

The bootstrap should print the recommendation, verify private-repo access, clone or refresh `~/.hermes/hermes-agent`, handle official-checkout migration by moving only the code checkout aside, then delegate to the repo-local finalizer (`scripts/install-private.sh`).

Manual SSH fallback for technical users remains available:

```bash
mkdir -p ~/.hermes
git clone --branch private/main --single-branch git@github.com:<owner>/<private-repo>.git ~/.hermes/hermes-agent
~/.hermes/hermes-agent/scripts/install-private.sh
```

Updates remain one command:

```bash
hermes update
```

The finalizer script should configure `origin`, fetch-only `upstream`, install metadata, and setup; end users should not manually pass `--branch private/main`, configure remotes, paste PATs, or know the upstream/origin split.

Long-term non-technical UX can still expose exactly one stable bootstrap command per OS family:

- macOS / Linux / WSL / Termux: `curl -fsSL https://<stable-domain>/hermes-private/install.sh | bash`
- Windows PowerShell: `iex (irm https://<stable-domain>/hermes-private/install.ps1)`

That bootstrap should only validate auth/clone and then call the private checkout's `scripts/install-private.sh`.

## Installer architecture

Prefer a tiny public bootstrap installer plus private GitHub repo access:

1. Public bootstrap contains no private source and no credentials.
2. Private repo remains protected by GitHub permissions.
3. Bootstrap configures the regular installer with private defaults:
   - origin SSH/HTTPS = private repo
   - upstream = official NousResearch repo
   - branch = private distribution branch, e.g. `private/main`
   - channel = private distribution channel, e.g. `charles-private`
4. The common `install.sh` / `install.ps1` should accept repo URL, upstream URL, branch, and channel as parameters or env vars so the private line does not fork installer logic permanently.

Avoid raw private GitHub curl URLs as the primary path: browser login state does not apply to curl, and PAT/header setup is hostile to non-technical users.

## Bootstrap script contract

For the recommended “user already has private GitHub access” path, add a small repo-hosted bootstrap such as `scripts/bootstrap-private.sh`. It should:

1. Start by printing the recommended install path so users learn the stable command before automation runs.
2. Refuse unsafe install directories (`/`, `$HOME`, or `$HERMES_HOME` itself); default to `$HERMES_HOME/hermes-agent`.
3. Verify private repo access through `gh auth`/`gh repo view` first; fall back to SSH `git ls-remote` for technical users.
4. Never accept GitHub tokens on the command line and never construct token-bearing URLs.
5. Clone the private branch when no checkout exists.
6. Refresh an existing private checkout with a scoped `git fetch origin <private-branch>` and `checkout -B <branch> origin/<branch>`.
7. If an official checkout exists at the target path, explain that user data under `$HERMES_HOME` is preserved, confirm unless `--yes`, move only the code checkout to an `.official-backup.<timestamp>` path, then clone the private repo.
8. Delegate to `scripts/install-private.sh --yes`, passing `--dry-run` / `--skip-setup` through.
9. End with the durable update command: `hermes update`.

Test the bootstrap with `bash -n` and a dry run (`scripts/bootstrap-private.sh --dry-run --skip-setup --yes`) before publishing README instructions.

## Private finalizer script contract

For the P0 “user already has private repo access” path, add a repo-local finalizer such as `scripts/install-private.sh`. It should:

1. Run only inside the authorized private checkout; fail closed if `origin` is the official `NousResearch/hermes-agent` repo.
2. Ensure the checkout is on the private branch (`private/main` by default), fetching `origin/<branch>` if needed.
3. Preserve the user's clone style where possible: SSH clones keep SSH origin; HTTPS/GitHub CLI clones keep HTTPS origin.
4. Set `upstream` to the official repo for maintainer fetches and disable its push URL (for example `git remote set-url --push upstream DISABLED`).
5. Write `$HERMES_HOME/install.json` with channel/origin/upstream/branch/installer_version and stamp `$HERMES_HOME/.install_method` as `git`.
6. Delegate dependency/bootstrap work to `./setup-hermes.sh`, with `--skip-setup`, `--dry-run`, and `--yes` for verification/automation.
7. Print a success summary ending with the single update command: `hermes update`.

Test the script with `bash -n` and a dry run (`scripts/install-private.sh --dry-run --skip-setup --yes`) before publishing the README.

## Install metadata is part of the UX

Write an install metadata file such as `~/.hermes/install.json` after install/migration:

```json
{
  "channel": "charles-private",
  "origin": "https://github.com/<owner>/<private-repo>.git",
  "upstream": "https://github.com/NousResearch/hermes-agent.git",
  "branch": "private/main",
  "installed_at": "...",
  "installer_version": 1
}
```

Consumers should use it:

- `hermes update` default branch resolution should prefer explicit `--branch`, then install metadata branch, then current tracking branch, and only then fallback to `main`.
- `hermes doctor` should display channel, origin, upstream, branch, and update target.
- Repair flows can detect drift and offer a single corrective command such as `hermes repair install-channel`.

Without metadata, private users can accidentally update against `main` or lose the private channel through a generic update path.

## Migration from official install

If `~/.hermes/hermes-agent` already exists and origin is the official repo, treat private install as a channel migration, not a fresh install:

1. Verify private repo access first (`git ls-remote <private-origin> <private-branch>`).
2. Explain that user data under `~/.hermes` is preserved and only program code changes.
3. Back up the existing code checkout before mutation.
4. Stash any local code changes with an explicit migration label.
5. Set remotes: private repo as `origin`, official repo as `upstream`.
6. Fetch and checkout/reset the private branch.
7. Reinstall dependencies and write install metadata.
8. Verify with `hermes --version` and a quick doctor/self-check.

Never delete config, `.env`, skills, session DB, gateway pairing, cron jobs, or memories during this migration.

## Error message style

Translate git/auth failures into user-actionable causes:

- `Repository not found`, `Authentication failed`, `could not read Username`, or `Permission denied (publickey)` => explain GitHub authorization/login and tell the user to open the private repo URL in a browser; 404 usually means not logged in or not invited.
- Missing Git => give OS-specific install/fallback guidance; Windows installer may install portable Git.
- Missing private branch => classify as maintainer release/config problem, not user fault.
- Existing non-git install dir => move-aside/backup offer; never delete blindly.
- Update conflict => say changes were preserved in stash and provide the stash label/ref.
- PATH not refreshed => tell user to reopen the terminal or source shell rc.

Format errors as: what happened, likely cause, exact next action, and what to send the maintainer if stuck.

## Tradeoffs

Public bootstrap + private clone is the best default: minimum commands, preserves GitHub ACLs, and enables migration/update repair. It does reveal that a private distribution entrypoint exists and requires maintaining a stable bootstrap URL.

Private README-only instructions are acceptable as a temporary fallback, but private raw URLs and multi-command clone/setup flows are poor for non-technical users.

GUI installers are the best eventual non-technical experience, but signing, packaging, antivirus, and updater complexity make them a second phase after the CLI bootstrap path is reliable.
