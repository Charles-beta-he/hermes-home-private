# LAN Cross-Device Deployment

Extracted from `/Users/charles/.hermes/skills/.archive/software-development/cloud-edge-architecture/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### LAN Cross-Device Deployment

Adding edge workers on other computers in the same LAN:

```bash
# On main node: serve deploy script
cd ~/.hermes/edge-worker/deploy-package && python3 -m http.server 8080

# On other computer: one-liner install
curl -sSL http://192.168.x.x:8080/deploy-worker.sh | bash -s -- 192.168.x.x
```

The deploy script is self-contained (all Python embedded, stdlib only). It:
1. Tests main node connectivity
2. Installs edge_worker.py + CLI wrapper + launchd auto-start
3. Registers with main node
4. Verifies end-to-end connection

See `references/lan-cross-device-deployment.md` for full pattern, verification, and pitfalls.

**SSL/Network Failure Fallback**

Remote install may fail with SSL errors — two distinct variants:

| Error | Code | Meaning | Common Cause |
|-------|------|---------|--------------|
| `SSL_ERROR_SYSCALL` | curl 35 | TLS handshake aborted | GFW, corporate firewall, Cloudflare blocked |
| `SSL: no alternative certificate subject name matches` | curl 60 | Certificate SAN mismatch | Proxy/VPN intercepting TLS, DNS hijacking to wrong IP |

**Critical gotcha**: `curl --insecure` on the outer command does NOT propagate into the piped bash script's internal curl calls. The script itself must use `-k` on every download.

**Fallback chain**:
1. **Local install** (if `~/.hermes/scripts/` or `~/.hermes/edge-worker/install-edge-pro.sh` exists):
   ```bash
   bash ~/.hermes/edge-worker/install-edge-pro.sh
   ```
2. **Insecure install script** (all curl calls use `-k`):
   ```bash
   curl -sSLk https://raw.githubusercontent.com/Charles-beta-he/hermes-edge-worker/main/install-insecure.sh | bash
   ```
3. **wget alternative**:
   ```bash
   wget --no-check-certificate -qO- https://raw.githubusercontent.com/Charles-beta-he/hermes-edge-worker/main/install.sh | bash
   ```
4. **Proxy**: `export https_proxy=http://proxy:port` then retry
5. **Manual download**: Use browser to download files, then follow `MANUAL-INSTALL.md` in the repo
6. **gh CLI** (authenticated API bypasses CDN):
   ```bash
   gh api repos/Charles-beta-he/hermes-edge-worker/contents/install.sh --jq '.content' | base64 -d | bash
   ```

**Key insight**: If `~/.hermes/edge-worker/` already exists with working files, skip remote install entirely — just verify with `hermes-edge status`.

**Auto-connect**: 7-state FSM (DISCOVERING→CONNECTING→REGISTERED→HEALTHY→DEGRADED→RECONNECTING→OFFLINE) with exponential backoff + jitter. UDP broadcast primary, TCP probe fallback.

See `references/production-deployment.md` for full config schema, service files, deployment patterns, and pitfalls.
