# Shadowrocket active config direct-route repair for private Git hosts

Use when a private Git host resolves to a Shadowrocket/MacPacket fake IP (often `198.18.0.0/15`) and `git fetch`/SSH fails, but the host should bypass VPN/proxy.

Applicability:
- macOS Shadowrocket with iCloud/group-container config DBs.
- Symptoms like `Connection closed by 198.18.x.x port 22`, `kex_exchange_identification`, or SSH reaching a fake-IP/TUN path.
- Private/company hosts that should be DIRECT, e.g. self-hosted GitLab.

Anti-conditions:
- Do not record project-specific hostnames as global defaults; substitute the current host.
- Do not assume the newest `sub*.db` is the active rule file.
- Do not hard-code row ids such as `docid=2` for `skip-proxy`; schemas/configs differ.
- Do not edit proxy config without backup and user approval, because restarting Shadowrocket disrupts networking.

Procedure:
1. Identify the active Shadowrocket rule file:
   - Read `~/Library/Group Containers/group.com.liguangming.Shadowrocket/Library/Preferences/group.com.liguangming.Shadowrocket.plist`.
   - Key: `group.com.liguangming.CurrentRuleFileName`.
   - Active DB usually lives under `~/Library/Mobile Documents/iCloud~com~liguangming~Shadowrocket/Documents/<CurrentRuleFileName>`.
2. Back up the active DB before writes:
   - `cp active.db active.db.bak_<purpose>_<timestamp>`.
3. Inspect SQLite rows by semantic keys, not fixed docids:
   - `config_content` with columns `c0section,c1name,c2value,c3option,...`.
   - Find `general/skip-proxy`, `general/always-real-ip`, and the `rule/FINAL` row.
4. Add the host to all required places:
   - `general skip-proxy`: append host to comma-separated `c2value`.
   - `general always-real-ip`: append host to comma-separated `c2value` so fake-IP DNS is bypassed.
   - `rule DOMAIN <host> DIRECT`: insert before `FINAL`, then reinsert `FINAL` after it preserving the old final policy.
5. Restart Shadowrocket / PacketTunnel only after backup:
   - `killall Shadowrocket MacPacketTunnel 2>/dev/null || true`
   - `open /Applications/Shadowrocket.app`
6. Verify target behavior, not just config rows:
   - DNS may still print `198.18.*` transiently, so test the real workflow too.
   - `ssh -o BatchMode=yes -o ConnectTimeout=10 -T git@<host>` should reach the Git server banner/auth response.
   - `git fetch origin --prune` in the affected repo should succeed.

Pitfall learned:
A helper script that picks the latest `sub*.db` and updates `docid=2` can modify the wrong database and the wrong row. Always resolve `CurrentRuleFileName` first and update rows by `c1name`/section.
