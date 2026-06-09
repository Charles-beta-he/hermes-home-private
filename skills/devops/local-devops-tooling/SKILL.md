---
name: local-devops-tooling
description: "Use when operating local developer tooling and machine-level DevOps: CLI install/upgrade scripts, rollback/versioning, macOS proxy/VPN/network diagnosis, local service wrappers, and verification scripts."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [devops, cli, install, macos, network, proxy, tooling]
    related_skills: [devops]
---

# Local DevOps Tooling

## Overview

This umbrella covers local operational tooling: install/upgrade scripts for CLI tools, service wrappers, verification/rollback mechanics, and macOS network/proxy diagnosis. It is for making a user's machine and local tools reliable, not for cloud infrastructure design.

## When to Use

- Creating or fixing `curl | bash`, install, update, rollback, or verification scripts
- Preserving config across CLI upgrades
- Diagnosing macOS proxy/VPN/network failures, DNS issues, or sites that won't load
- Checking local proxy ports/processes and system proxy settings
- Building local service wrappers with status/logs/restart/update commands

Don't use for:
- Kubernetes/cloud deployment workflows
- Application business logic bugs
- Generic Git operations (use Git repo operations)

## CLI Install/Upgrade Pattern

1. Detect existing installation and current version.
2. Backup critical files before overwriting.
3. Preserve user config; write `.new` config when upstream defaults change.
4. Download with safe TLS defaults; insecure fallback must be explicit and named.
5. Generate a wrapper with `start`, `stop`, `restart`, `status`, `logs`, `config`, `update`, `rollback`, and `uninstall` where appropriate.
6. Verify files, CLI path, process health, ports, dependencies, and config.

## macOS Network Diagnosis Pattern

1. Compare domestic/international reachability to distinguish physical network vs proxy/GFW class.
2. Inspect macOS system proxy settings with `networksetup` for the active service.
3. Check proxy process and listening ports (`lsof`, `ps`).
4. Locate proxy app config and subscription sources.
5. Test subscription/upstream reachability and handle proxy chicken-and-egg explicitly.

## Common Pitfalls

1. **Blind config overwrite.** Preserve config and surface new defaults separately.
2. **Wrong symlink path.** Wrapper scripts must resolve their real directory, not just `dirname $0`.
3. **Silent insecure TLS.** Never default to `curl -k`; require explicit user/env opt-in.
4. **Proxy port configured but app not running.** System proxy can break all browsing if it points at a dead localhost port.
5. **Wrong network service.** `Wi-Fi` commands don't affect Ethernet/USB services.
6. **Encrypted proxy config files.** Preferences plists may carry the usable subscription/settings when app data is encoded.

## Verification Checklist

- [ ] Existing install state and version were detected before writes.
- [ ] Config preservation/backup path was tested.
- [ ] CLI wrapper resolves symlinked paths correctly.
- [ ] Local service/process/port health was verified.
- [ ] macOS proxy changes were applied to the active network service and re-tested.
- [ ] Wrapper safety: any side effect is followed by target-state read-back before reporting completion.
## Support Files

- `references/cli-tool-installation.md` — install script templates, wrapper pattern, TLS fallback UX, and verification script details.
- `references/macos-network-admin.md` — networksetup commands, proxy app discovery, Shadowrocket/Clash/Mihomo diagnostics.
