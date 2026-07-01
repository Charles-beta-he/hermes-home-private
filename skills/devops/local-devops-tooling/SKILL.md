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
- Diagnosing OAuth-backed CLI/model providers that show "logged in" but fail at runtime; split auth presence, direct adapter smoke, backend authorization, and router eligibility.

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
3. **Private Git SSH split test**: For private GitLab/Gitea/Bitbucket fetch failures, separate DNS/proxy/TUN, raw TCP reachability, SSH banner exchange, and Git authentication. See `references/private-git-ssh-network-triage.md`.
4. Inspect macOS system proxy settings with `networksetup` for the active service.
4. Check proxy process and listening ports (`lsof`, `ps`).
5. Locate proxy app config and subscription sources.
6. Test subscription/upstream reachability and handle proxy chicken-and-egg explicitly.

## Cloud Mac / VPS Network Split Pattern

When a cloud macOS host is both a remote graphical workstation and part of a VPN design, split management, performance exit, and workload roles:

1. Use the cloud Mac for macOS GUI / browser / Apple-only execution, not as the primary VPN exit just because it is overseas.
2. Use a domestic-friendly optimized VPS as the edge acceleration / VPN / SSH jump layer when direct AWS links are slow.
3. Use Tailscale/WireGuard as the private management overlay for SSH, VNC, dashboards, and internal APIs; do not assume it is the best high-throughput exit path.
4. Keep VNC/ARD/Screen Sharing and dashboards off the public internet; reach them through overlay IPs or SSH tunnels.
5. Keep the edge VPS low-trust and replaceable: no canonical data, no broad secrets, and minimal open ports.
6. Always provide a rescue path independent of the primary edge node (fixed-IP SSH, AWS console/SSM, or alternate overlay route).

## OAuth CLI Provider Runtime Diagnosis Pattern

For OAuth-backed local providers, a successful login is only the first gate. If a model/provider reports `logged in` but calls fail, verify direct runtime behavior before changing router state:

1. Check native auth status and credential presence.
2. Run a bounded direct smoke with a unique token.
3. If the high-level CLI collapses the failure into a generic message, call the lower adapter/CLI directly to capture the upstream error class.
4. Only mark a provider recovered after a token-matching smoke succeeds.
5. If the backend returns account/product policy denial, stop at a human gate and keep the provider filtered unavailable.

See `references/oauth-cli-provider-runtime-diagnostics.md`.

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

- `references/oauth-cli-provider-runtime-diagnostics.md` — diagnose OAuth-backed CLI/model providers that are logged in but fail at runtime; includes direct adapter smoke, backend policy/TOS denial handling, recovery-state rules, and router verification.
- `references/cli-tool-installation.md` — install script templates, wrapper pattern, TLS fallback UX, and verification script details.
- `references/macos-network-admin.md` — networksetup commands, proxy app discovery, Shadowrocket/Clash/Mihomo diagnostics.
- `references/private-git-ssh-network-triage.md` — split private Git fetch failures into branch-state boundary, DNS/fake-IP, TCP reachability, SSH banner/auth, and proxy/TUN routing before changing Git config or claiming remote freshness.
- `references/macos-ios-app-network-triage.md` — Apple Silicon iPhone/iPad app network triage: installed app variant checks, packet-tunnel/Fake-IP detection, CFNetwork 403 vs connectivity failures, and safe proxy/DIRECT testing boundaries.
- `references/shadowrocket-node-validation.md` — extract individual Shadowrocket nodes from local SQLite config and verify TCP, HTTP/CONNECT, real egress IP/geo, and active system exit without leaking credentials.
- `references/shadowrocket-node-validation.md` — extract individual Shadowrocket nodes from local SQLite config and verify TCP, HTTP/CONNECT, real egress IP/geo, and active system exit without leaking credentials.
- `references/shadowrocket-webshare-qr-import.md` — generate Shadowrocket-importable QR codes from current Webshare dashboard/export rows; prefer plain proxy URL QR when `shadowrocket://add` scans do nothing; verify import success with real phone egress.
- `references/shadowrocket-service-specific-blocking.md` — diagnose service-specific IP blocking (e.g., OpenAI blocks VPN/proxy exit IPs): TUN mode fake DNS detection, multi-site isolation testing, Webshare "Working" status unreliability, HTTP proxy vs TUN incompatibility, missing proxy group, and Webshare static proxy screening with `--interface en0`, API pool username, and replacement API pitfalls.
- `references/shadowrocket-config-vs-proxy-mimo.md` — diagnose Shadowrocket macOS `GlobalRoutingMethod=Proxy` vs `Config`, TUN/fake-ip routing, and Xiaomi MiMo/token-plan-cn endpoint reachability; includes safe read-only checks, permissioned Config switch, and MiMo-specific endpoint pitfalls.
- `references/shadowrocket-active-config-browser-vs-git.md` — diagnose macOS Shadowrocket cases where Git/SSH works but browser HTTPS times out: identify the active rule DB, avoid hard-coded config docids, distinguish fake-IP DNS from system resolver, and test direct curl vs local HTTP proxy CONNECT.
- `references/shadowrocket-active-config-gitlab-direct.md` — repair private Git host access by editing the active Shadowrocket rule DB: resolve `CurrentRuleFileName`, back up the DB, add host to `skip-proxy`/`always-real-ip`/`DOMAIN DIRECT` by semantic row names, restart Shadowrocket, and verify SSH/git fetch.
- `references/xiaohongshu-fake-ip-browser-triage.md` — diagnose Xiaohongshu browser `ERR_SSL_PROTOCOL_ERROR` caused by fake-IP DNS plus proxy exceptions; includes read-only checks and a temporary Chrome host-resolver workaround for user-controlled QR login.
