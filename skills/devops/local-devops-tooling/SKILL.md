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
2. **Multi-site isolation test**: If VPN is connected but a specific service fails, test 4+ sites (google, github, target service, cloudflare) to distinguish "VPN broken" from "service-specific IP blocking". See `references/shadowrocket-service-specific-blocking.md`.
3. Inspect macOS system proxy settings with `networksetup` for the active service.
4. Check proxy process and listening ports (`lsof`, `ps`).
5. Locate proxy app config and subscription sources.
6. Test subscription/upstream reachability and handle proxy chicken-and-egg explicitly.

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
- `references/macos-ios-app-network-triage.md` — Apple Silicon iPhone/iPad app network triage: installed app variant checks, packet-tunnel/Fake-IP detection, CFNetwork 403 vs connectivity failures, and safe proxy/DIRECT testing boundaries.
- `references/shadowrocket-node-validation.md` — extract individual Shadowrocket nodes from local SQLite config and verify TCP, HTTP/CONNECT, real egress IP/geo, and active system exit without leaking credentials.
- `references/shadowrocket-node-validation.md` — extract individual Shadowrocket nodes from local SQLite config and verify TCP, HTTP/CONNECT, real egress IP/geo, and active system exit without leaking credentials.
- `references/shadowrocket-webshare-qr-import.md` — generate Shadowrocket-importable QR codes from current Webshare dashboard/export rows; prefer plain proxy URL QR when `shadowrocket://add` scans do nothing; verify import success with real phone egress.
- `references/shadowrocket-service-specific-blocking.md` — diagnose service-specific IP blocking (e.g., OpenAI blocks VPN/proxy exit IPs): TUN mode fake DNS detection, multi-site isolation testing, Webshare "Working" status unreliability, HTTP proxy vs TUN incompatibility, missing proxy group, and Webshare static proxy screening with `--interface en0`, API pool username, and replacement API pitfalls.
