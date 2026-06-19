# Hermes Personal Assistant Governance Experience Pack

This pack preserves transferable Hermes operating consensus for new users without copying the owner's lived state.

## What this pack contains

- Template-only taskpool and hook examples.
- Governance checklists for external capability absorption, shadow promotion, and taskpool proof boundaries.
- Example configuration with placeholders only.
- A sanitizer gate that must pass before distribution.
- A local codegraph manager (`scripts/codegraph_manager.py`) for controlled `codebase-memory-mcp` install/doctor/enable/smoke workflows.

## What this pack must never contain

- Live config, `.env`, private login material, sessions, or auth files.
- Memory, user profile, project profiles, session DBs, taskpool evidence, logs, locks, backups, or `docs/private`.
- Real channel IDs, production URLs, owner-local paths, or runtime databases such as `state.db` or `contextcards.db`.

## Activation model

Installers should copy missing templates only and must not enable cron, shell hooks, gateway delivery, taskpool mutation, or ContextCard promotion by default.

Run before packaging or installation:

```bash
python3 $HERMES_HOME/scripts/experience_pack_sanitize.py $HERMES_HOME/templates/experience-pack/personal-assistant-governance
```

## Install this pack

```bash
python3 $HERMES_HOME/scripts/experience_pack_install.py install personal-assistant-governance --target-home $HERMES_HOME --dry-run
python3 $HERMES_HOME/scripts/experience_pack_install.py install personal-assistant-governance --target-home $HERMES_HOME
```

## Local codegraph quickstart

Prefer the formal Hermes CLI when available:

```bash
hermes codegraph list
hermes codegraph install --dry-run
hermes codegraph install
hermes codegraph enable
hermes codegraph smoke --repo /path/to/project --query "important symbol"
```

If the formal CLI is not available yet, use the bundled script fallback:

```bash
python3 scripts/codegraph_manager.py list
python3 scripts/codegraph_manager.py install --dry-run
python3 scripts/codegraph_manager.py install
python3 scripts/codegraph_manager.py enable
python3 scripts/codegraph_manager.py smoke --repo /path/to/project --query "important symbol"
```

`enable` is side-effect safe by default: it writes a config snippet and activation record, but does not merge into `$HERMES_HOME/config.yaml` unless `--merge-config` is explicit.
