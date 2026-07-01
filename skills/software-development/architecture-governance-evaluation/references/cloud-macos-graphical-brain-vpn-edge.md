# Cloud macOS Graphical Brain + VPN Edge Pattern

## Applicability

Use this when designing an overseas personal-assistant / agent "core brain" that needs a real macOS graphical session, browser login state, Apple ecosystem tooling, or GUI automation, while the user also needs a VPN / optimized network exit.

Anti-conditions:
- Do not use this pattern when the workload is pure Linux CLI/API automation; a normal Linux VPS/control node is cheaper and easier.
- Do not treat the VPN edge as the trusted state store.
- Do not expose macOS Screen Sharing/VNC, Hermes dashboard, databases, or control panels directly to the public internet.
- Do not frame the network layer as bypassing law or policy; describe it as private remote access, development connectivity, privacy, and reliability.

## Core architecture

Split responsibilities instead of making the cloud Mac do everything:

```text
Local devices
  -> optimized edge VPS / VPN exit / jump host
  -> private overlay network
  -> AWS EC2 Mac graphical executor
  -> durable backup/state layer
```

Recommended role split:

- AWS EC2 Mac: overseas macOS graphical brain, GUI executor, browser automation node, Safari/Xcode/Keychain/Apple-ecosystem work, Hermes desktop runtime.
- Optimized VPS edge, e.g. CN2/GIA/three-network optimized US VPS: domestic-friendly VPN/proxy/SSH jump/traffic edge; low-trust and replaceable.
- Tailscale/WireGuard overlay: private management plane between local devices, edge VPS, cloud Mac, and optional Linux control node.
- Optional Linux control node: monitoring, gateway/webhook ingress, cron, queue, logs, health checks, and other non-macOS work.
- S3/EBS snapshots/Git/object storage: recovery, evidence, config, and backup layer.

## AWS EC2 Mac positioning

AWS EC2 Mac is acceptable as a paid overseas macOS workstation when the user values a real GUI session. Treat it as expensive graphical execution capacity, not the default VPN server.

Durable constraints to account for:
- EC2 Mac runs on Dedicated Hosts; plan for host-level cost and minimum allocation/release windows.
- One Mac instance per host is the normal operating model.
- Startup/readiness is slower than normal EC2; design recovery around minutes, not seconds.
- Use encrypted EBS and avoid FileVault on EC2 Mac boot volumes.
- Use high-performance gp3 for serious GUI/browser/Xcode workloads; AWS documentation recommends around 10,000 IOPS and 400 MiB/s throughput for optimal Mac instance performance.

## Graphical access design

Use layered access:

1. Management path: local device -> Tailscale/SSH -> cloud Mac.
2. GUI path: local device -> private overlay or edge VPS -> macOS Screen Sharing / ARD / VNC on port 5900.
3. Experience-enhancement path if needed: Jump Desktop, Parsec, RustDesk, AnyDesk, or NICE DCV, after the native Screen Sharing baseline is verified.

Baseline setup steps to include in runbooks:

```bash
sudo passwd ec2-user
sudo launchctl enable system/com.apple.screensharing
sudo launchctl kickstart -k system/com.apple.screensharing
sudo lsof -iTCP:5900 -sTCP:LISTEN -n -P
```

Safer client access options:

```bash
open vnc://<cloud-mac-tailnet-ip>
# or tunnel Screen Sharing
ssh -L 5901:127.0.0.1:5900 ec2-user@<cloud-mac>
open vnc://127.0.0.1:5901
```

## Network edge design

Recommended split:
- Tailscale: private control plane, device identity, ACLs, MagicDNS, private SSH, dashboard/VNC reachability.
- Optimized VPS: main user-facing exit or relay when routes from China/domestic networks to AWS are slow.
- WireGuard: simple static fallback tunnel.
- Hysteria2 / TUIC / Xray REALITY: optional performance/complex-routing layer for high-latency/lossy networks, only in lawful privacy/development access contexts.
- AWS Linux VPN: backup or AWS-internal jump path, not the default domestic performance exit when an optimized edge is faster.

Security group / firewall defaults:
- Cloud Mac SSH: allow only fixed admin IP, edge VPS IP, or overlay network.
- Cloud Mac 5900: never public; overlay/tunnel only.
- Hermes dashboard: localhost or overlay only.
- Edge VPS: expose only required authenticated transport ports; do not store core state or secrets there.

## Verification checklist

Network:
```bash
curl ipinfo.io
curl https://www.cloudflare.com/cdn-cgi/trace
ping -c 5 github.com
curl -I https://github.com
```

Cloud Mac:
```bash
sw_vers
uname -m
df -h
tailscale status
sudo lsof -iTCP:5900 -sTCP:LISTEN -n -P
```

Hermes graphical brain:
```bash
hermes --version
# dashboard should be reached via local/overlay/tunnel, not public internet
ssh -L 9119:127.0.0.1:9119 ec2-user@<cloud-mac>
```

Operational drills:
- Edge VPS down -> use Tailscale/AWS backup path.
- Screen Sharing hung -> kickstart service or reboot.
- Cloud Mac unavailable -> inspect AWS instance/host status, security group, EBS/snapshot recovery.
- Tailscale unstable -> use static WireGuard or direct locked-down SSH as emergency path.

## Common pitfalls

1. Collapsing all responsibilities into EC2 Mac. Keep VPN edge, control plane, durable state, and GUI executor separate.
2. Public VNC/ARD exposure. Port 5900 is convenient but high-risk; require overlay/tunnel/security-group restriction.
3. Using an optimized VPS as a trusted database/control node. It is an edge relay, not the brain.
4. Treating AWS public networking as automatically fast from domestic networks. Measure direct AWS vs optimized VPS relay and choose by evidence.
5. Calling a mock/dashboard-only setup a delivered brain. Verify real GUI login, browser persistence, Hermes runtime, private access, health checks, and recovery path.
