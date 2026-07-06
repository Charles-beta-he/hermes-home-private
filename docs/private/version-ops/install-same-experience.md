# Install the Same Private Hermes Experience

Status: proposed runbook
Audience: trusted operator with access to `Charles-beta-he/hermes-home-private`
Goal: approach Charles' Hermes smoothness while keeping secrets, memories, gateways, and runtime state local.

## What this can and cannot reproduce

Can reproduce:

- skills and procedural memory;
- local automation scripts and doctors;
- project profiles and workflow SSOTs;
- HEWOS implementation/tests/workbench artifacts;
- dynamic self-check coverage code and runbook;
- private release policy and capability manifest.

Cannot safely reproduce by clone alone:

- model provider credentials;
- Telegram/Lark/GitHub/Cloudflare gateway credentials;
- live cron state, delivery queues, logs, DBs, task runtime state;
- Charles' personal memories;
- exact hardware/phone/glasses/NAS environment;
- external delivery/push/deploy authority.

## Layered install plan

### L0. Install upstream Hermes Agent

Use the official Hermes Agent installation path first. Then verify:

```bash
hermes --version
hermes doctor
```

Do not copy this private repo over a fresh Hermes install until the base runtime is healthy.

### L1. Clone private capability source separately

Recommended layout:

```bash
git clone git@github.com:Charles-beta-he/hermes-home-private.git ~/.hermes-private-home
cd ~/.hermes-private-home
git checkout <private-home-tag-or-commit>
python3 scripts/private_version_doctor.py . --json
```

Keep it separate from `~/.hermes` until the doctor has been read.

### L2. Copy/import durable capability directories

Minimum useful set:

```text
skills/
scripts/
project-profiles/
docs/private/version-ops/
workflows/projects/hermes-embodied-workflow-os/        optional but recommended
workflows/projects/hermes-agent-os-control-plane/      optional architecture/read-only
```

Do not copy these from the private repo into another user's home:

```text
config.yaml
cron/jobs.json
memories/
state/
sessions/
logs/
cron/output/
*.db
*.lock
credentials/
secrets/
.env*
```

Recommended first import is conservative:

```bash
mkdir -p ~/.hermes
rsync -a --ignore-existing ~/.hermes-private-home/skills/ ~/.hermes/skills/
rsync -a --ignore-existing ~/.hermes-private-home/scripts/ ~/.hermes/scripts/
rsync -a --ignore-existing ~/.hermes-private-home/project-profiles/ ~/.hermes/project-profiles/
rsync -a --ignore-existing ~/.hermes-private-home/docs/private/version-ops/ ~/.hermes/docs/private/version-ops/
```

Use `--ignore-existing` for first install so local user edits are not overwritten.

### L3. Verify imported capability pack

```bash
python3 ~/.hermes/scripts/private_version_doctor.py ~/.hermes-private-home --json
python3 -m py_compile ~/.hermes/scripts/dynamic_selfcheck_coverage.py
python3 -m pytest ~/.hermes/scripts/tests/test_dynamic_selfcheck_coverage.py -q
```

If `pytest` is not installed, run at least:

```bash
python3 -m py_compile ~/.hermes/scripts/dynamic_selfcheck_coverage.py
python3 ~/.hermes/scripts/dynamic_selfcheck_coverage.py run --home ~/.hermes --output-dir ~/.hermes/state/selfcheck --quiet-success
```

### L4. Configure local secrets manually

The installer must configure providers and gateways locally. Do not paste secrets into repo files, docs, skills, or memories.

Typical local-only targets:

```text
~/.hermes/config.yaml
~/.hermes/config/quorum.yaml
provider-specific keychain / env vars
gateway platform credentials
```

Then verify:

```bash
hermes doctor
python3 ~/.hermes/scripts/post-update-check.py --fix
```

### L5. Recreate optional local-only jobs

Cron jobs are not shipped as `cron/jobs.json`. Recreate jobs one by one from known runbooks. Default policy for other installers:

- `deliver=local` only;
- `no_agent=true` for script-only monitors;
- success-silent where possible;
- no external delivery until a platform target and readback are verified.

Dynamic self-check example:

```bash
hermes cron create \
  --name dynamic-selfcheck-coverage-control-plane \
  --schedule 'every 60m' \
  --script ~/.hermes/scripts/dynamic_selfcheck_coverage_cron.sh \
  --deliver local \
  --no-agent
```

If the local CLI syntax differs, use Hermes' current cron command help and keep the same semantics: local-only, no-agent, success-silent.

### L6. Activate gateway/external delivery only after smoke tests

External delivery is not part of the base install. To enable Telegram/Lark/GitHub/Cloudflare/etc.:

1. configure credentials locally;
2. send a small allowlisted smoke message to the current operator only;
3. read back receipt/status;
4. keep broad fanout disabled;
5. document rollback.

### L7. Activate hardware/embodied adapters only with exact safety gates

HEWOS and Rokid/hardware docs are safe to read and run locally. Real devices require:

- exact device/target;
- reversible dry-run;
- telemetry/readback;
- emergency stop/rollback;
- human approval for credentials/payment/physical effects.

## Smoothness parity checklist

A trusted install is "experience-close" when these pass:

```bash
hermes --version
hermes doctor
python3 ~/.hermes/scripts/private_version_doctor.py ~/.hermes-private-home --json
python3 ~/.hermes/scripts/dynamic_selfcheck_coverage.py run --home ~/.hermes --output-dir ~/.hermes/state/selfcheck --quiet-success
python3 -m py_compile ~/.hermes/scripts/dynamic_selfcheck_coverage.py
```

Optional if HEWOS is installed:

```bash
cd ~/.hermes/workflows/projects/hermes-embodied-workflow-os/implementation
python3 -m pytest tests -q
```

Optional if provider quorum is configured:

```bash
python3 ~/.hermes/scripts/consult_models.py status
```

## Version pinning recommendation

Record this tuple in the install receipt:

```text
private-home repo URL
private-home commit/tag
hermes-agent child commit
Hermes CLI version
Python version
enabled local cron job IDs
provider/gateway activation state: disabled/local-only/external-enabled
```

Do not record actual secret values.
