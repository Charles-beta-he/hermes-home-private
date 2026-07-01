# Private Git SSH Network Triage

Use when `git fetch`, `git pull`, or `ssh -T git@<host>` fails for a private Git service and the repository state itself is otherwise clean.

Applicability:
- Private GitLab/Gitea/Bitbucket/GitHub Enterprise over SSH.
- macOS or local developer machines with VPN/TUN/proxy apps that may synthesize fake-IP DNS ranges.
- Failures before Git authentication or before refs are advertised.

Anti-conditions:
- Do not treat this as proof that the Git tool or repository is broken.
- Do not encode the user's current hostname, IP, proxy app, or branch names as a durable rule.
- If fetch succeeds after a retry, capture only the retry/freshness gate, not the transient outage.

## Procedure

1. Preserve branch-state truth boundaries.
   - Run `git status --short --branch` and record current branch/dirty state.
   - Attempt `git fetch origin --prune`.
   - If fetch fails at transport, label all `origin/*` refs as cached-local evidence. Do not call them latest remote state.

2. Split Git from SSH.
   - `git remote -v`
   - `ssh -o BatchMode=yes -o ConnectTimeout=8 -T git@<host>`
   - If SSH fails before auth/banner, this is network/SSH service reachability, not branch divergence.

3. Split DNS/fake-IP from real DNS.
   - Python/socket or `host <host>` shows system resolver result.
   - Query public DNS separately, e.g. `dig +short @223.5.5.5 <host> A`, `@119.29.29.29`, `@8.8.8.8`, `@1.1.1.1`.
   - If the system resolver returns a private/fake-IP range while public DNS returns a real IP, inspect TUN/proxy routing before changing Git config.

4. Split TCP reachability from SSH banner.
   - `nc -vz -w 5 <host> 22`
   - `ssh -vvv -o BatchMode=yes -o ConnectTimeout=10 -T git@<host>`
   - TCP success plus `kex_exchange_identification: Connection closed by remote host` means the port is reachable but the SSH service/proxy path closes before banner/auth. Do not report this as a key/password failure.

5. Inspect local proxy/TUN state without mutating it.
   - `scutil --proxy`
   - `route get <host>`
   - `lsof -nP -iTCP:<proxy-port> -sTCP:LISTEN`
   - `ifconfig utunX` for the interface named by `route get`.
   - If system proxy excludes the fake-IP range, SSH may bypass HTTP proxy while still being routed through a TUN interface.

6. Test explicit proxy paths only as diagnostics.
   - HTTP CONNECT proxy: `nc -X connect -x 127.0.0.1:<port> -vz -w 8 <host> 22`
   - Alternate SSH ports only if the service documents them; otherwise treat open TCP ports without SSH banner as inconclusive.

7. Safe resolution suggestions.
   - Switch the proxy/VPN rule for the Git host to the correct path (often DIRECT for corporate/internal Git, or a known working company VPN route).
   - Flush/refresh DNS in the proxy app if fake-IP mapping is stale.
   - Try another network or approved VPN if the server blocks the current egress IP.
   - Only after SSH banner/auth works, rerun `git fetch origin --prune && git pull --ff-only`.

## Reporting checklist

- Current branch and dirty state.
- Whether fetch reached the remote or failed before refs.
- System DNS result vs public DNS result.
- TCP result vs SSH banner result.
- Proxy/TUN route evidence.
- Clear boundary: no branch freshness, merge-readiness, or task-branch creation from cached refs unless explicitly accepted.
