# AWS Mac Graphical Brain Deployment Pattern

Applicability: use when designing a cloud-hosted personal/agent "core brain" that genuinely needs macOS GUI, browser sessions, Apple ecosystem tooling, Safari/Xcode/keychain, or desktop automation. Anti-condition: do not use AWS EC2 Mac merely as a generic VPN, cheap server, or sole control plane when Linux/VPS infrastructure is enough.

## Core architecture

Separate the system into responsibility layers instead of making EC2 Mac a single overloaded node:

1. Graphical macOS execution layer: AWS EC2 Mac Dedicated Host running macOS GUI, browser automation, Hermes desktop workflows, Apple Remote Desktop / Screen Sharing, Safari/Xcode/macOS-only tasks.
2. Edge acceleration / VPN layer: domestic-friendly optimized VPS such as CN2/GIA/tri-net optimized US VPS. It provides user-facing VPN/proxy/SSH jump/edge relay, not canonical state.
3. Private control overlay: Tailscale or WireGuard connects local devices, edge VPS, AWS Mac, and optional Linux control nodes. Use it for SSH, dashboard, VNC, and private APIs.
4. Linux control plane, optional but preferred: ordinary EC2/VPS handles monitoring, cron/gateway, queues, logs, health checks, and recovery orchestration.
5. Durable data/recovery layer: Git/S3/EBS snapshots/object storage hold scripts, configs, evidence, logs, and backups.

## AWS EC2 Mac facts to check

- EC2 Mac is billed as a Dedicated Host; the Mac instance itself may show zero charge while the host carries the hourly cost.
- There is a 24-hour minimum allocation/billing window before host release.
- One Mac Dedicated Host runs one Mac instance.
- Choose region and capacity deliberately; `us-west-2` is a common starting point, but verify live availability.
- AWS recommends high-performance EBS for Mac workloads; a practical default is gp3 500GB, 10,000 IOPS, 400 MiB/s, encrypted.
- Do not enable FileVault on EC2 Mac; use EBS encryption.
- First readiness can take minutes; plan for 6-20 minute launch/connection windows.

## Cost-model procedure

When asked for cost, fetch current AWS public pricing or AWS Pricing Calculator rather than relying on memory.

Estimate separately:

1. Dedicated Host hourly price × 730.5 hours/month.
2. 24-hour minimum cost: hourly price × 24.
3. gp3 storage: GB × storage price.
4. gp3 extra IOPS: max(0, requested_iops - baseline_iops) × IOPS price.
5. gp3 extra throughput: max(0, requested_mibps - baseline_mibps) × throughput price.
6. Edge VPS monthly plan.
7. Optional Linux control node, snapshots, AWS data egress, monitoring, domain/DNS.

Recommended decision tiers:

- Trial: M2-class Mac for 24-72h to validate GUI, Tailscale, VNC, Hermes, and edge path.
- Long-term default: M4-class Mac when budget accepts always-on graphical brain costs.
- Pro/Max/Ultra: only after evidence shows GUI/build/multi-browser workloads saturate lower tiers.

## GUI access pattern

- Enable Screen Sharing / ARD on the Mac, but never expose TCP 5900 to the public internet.
- Prefer Tailscale or WireGuard IP for GUI access.
- Alternative: SSH tunnel local port to `127.0.0.1:5900` on the Mac.
- Use Jump Desktop/Parsec/RustDesk only after native Screen Sharing is validated and latency/quality requires enhancement.
- Verify with real login, browser open, session persistence, copy/paste, resolution, and restart recovery.

## Security boundary

- AWS Mac should not expose SSH/VNC/dashboard to `0.0.0.0/0`.
- Hermes dashboard should bind to localhost or private overlay; access via SSH tunnel/Tailscale.
- Edge VPS is low-trust and replaceable: keep no canonical data or broad secrets there.
- Use Security Groups to allow SSH only from fixed admin IPs, edge VPS IP, or overlay access.
- Use Tailscale ACL/device approval instead of default all-to-all trust.
- Keep at least one rescue path independent of the primary edge VPS: AWS console/SSM/temporary fixed-IP SSH/Tailscale DERP.

## Verification checklist

- [ ] Current AWS Mac pricing and 24h minimum are stated with source/date.
- [ ] User has explicitly authorized paid resource creation before running creation scripts.
- [ ] Edge node, control overlay, and graphical Mac roles are separated.
- [ ] 5900/VNC and Hermes dashboard are not public.
- [ ] Tailscale/WireGuard connectivity works among local device, edge VPS, and AWS Mac.
- [ ] GUI login works over private path and survives disconnect/reconnect.
- [ ] EBS encryption, snapshots, and config/script backup are planned.
- [ ] Release/rollback path covers data backup, instance termination, host release after billing window, and rescue access.

## Pitfalls

1. Treating AWS Mac as a VPN node because it is overseas. It is expensive and operationally heavier than a Linux edge VPS; use it for macOS GUI execution.
2. Hiding the Dedicated Host cost by quoting only instance price. Quote host price and the 24-hour minimum explicitly.
3. Conflating management overlay with performance exit. Tailscale is excellent for control; domestic-friendly optimized VPS may still be needed for fast user-facing traffic.
4. Making the edge VPS the canonical brain. It should be replaceable; state and secrets belong in controlled stores.
5. Producing a plan but no landing package. For full-landing requests, produce runbooks/templates/scripts up to the first real human boundary: paid resource authorization, credentials, account quota, or provider purchase.
