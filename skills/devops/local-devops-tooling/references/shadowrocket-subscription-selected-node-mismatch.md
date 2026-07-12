---
name: shadowrocket-subscription-selected-node-mismatch
description: "Read-only diagnostic recipe for Shadowrocket macOS cases where enabling VPN breaks network because local selected-node state, active config DB, and subscription contents are out of sync."
version: 1.0.0
---

# Shadowrocket Selected Node / Subscription Mismatch

## Scope and applicability

This reference is a reusable diagnostic pattern for macOS Shadowrocket. It intentionally stores no concrete user subscription URL, credential, account name, node name, private token, or provider-specific status. Use it when:

- direct network is healthy,
- other users say the provider/node class works,
- enabling Shadowrocket breaks broad network access,
- and the suspected class is local app state: selected node, route mode, active rule DB, subscription import, or expired subscription residue.

Anti-condition: do not treat any node name, IP, provider, or account state observed in one session as durable. Re-read live preferences and DBs every time.

## Read-only diagnostic path

1. Establish the machine is not generally offline:
   - inspect default route,
   - inspect `scutil --proxy`,
   - curl one domestic site, one international site, and one IP echo endpoint with timeouts.
2. Confirm whether Shadowrocket is running and whether macOS system proxy is involved:
   - check Shadowrocket processes,
   - check common local proxy listener ports,
   - if system proxy is off and no local proxy port is listening, suspect TUN/VPN/app routing rather than stale macOS HTTP proxy.
3. Read Shadowrocket group preferences without changing state:
   - active rule/config file name,
   - global routing method,
   - selected server name,
   - selected server UUID if present.
4. Inspect local Shadowrocket databases:
   - main app DB,
   - subscription DB,
   - active config DB named by current preferences.
   Query section counts and `section='proxy'` rows from the FTS3 `config` table.
5. Compare selected server against actual local rows:
   - search for selected name/UUID/host fragments,
   - if selected server is absent from local proxy rows, suspect stale selected-node preference or failed import.
6. Fetch each `general/update-url` subscription read-only:
   - report HTTP status, content type, size, and whether it looks like a real proxy config or an expired/renewal notice,
   - redact the full URL and token.
7. Parse current subscription YAML if possible:
   - count proxies, groups, and rules,
   - print only node name/type/server/port,
   - do not print UUIDs, passwords, private keys, or raw subscription text.
8. TCP-check current subscription node entrypoints only as a weak reachability signal.
   TCP success proves the entrypoint accepts connections; it does not prove protocol-level proxy usability.

## Common findings and meaning

- Global routing set to Proxy plus selected server missing from active subscription/config can blackhole all traffic by forcing every request through a stale node pointer.
- Active config has rule/group sections but no proxy-node rows: rules/groups landed but actual nodes did not, or local DB state is out of sync with the subscription.
- One subscription returns a real config while another returns only an expired/renewal warning config: stale subscription residue may confuse selection/import state.
- Old HTTP proxy rows may accept TCP but return application-level payment/auth/permission errors on CONNECT; do not treat TCP success as working proxy evidence.
- Current subscription entrypoints are TCP-reachable while the selected node is absent: provider-wide outage is less likely; fix local selected-node/subscription state first.

## Safe remediation suggestions

Do not modify or switch nodes without explicit user permission. Recommend in order:

1. Refresh or re-import the live subscription that returns real nodes.
2. Delete or disable expired subscriptions that return warning-only configs.
3. Select a node that is actually present in the current subscription.
4. Prefer Config/rule routing over global Proxy while recovering, so stale single-node selection does not break all traffic.
5. Re-enable Shadowrocket and verify domestic, international, and IP echo endpoints.

## Reporting pattern

Report current-state evidence, not a provider accusation:

- direct network OK/FAIL,
- system proxy on/off and target if on,
- Shadowrocket process/local ports present/absent,
- routing mode and selected server state,
- whether selected server exists in active DB/subscription,
- subscription status summary with tokens redacted,
- node entrypoint TCP summary,
- concrete next safe remediation steps.
