# Shadowrocket active-config and browser-vs-Git diagnostics

Use when Git/SSH starts working after Shadowrocket rule edits but browsers still time out, or when a script modifies a Shadowrocket database that may not be the active rule file.

## Core lesson

Shadowrocket on macOS can have multiple SQLite config databases under iCloud Documents. The newest `sub*.db` is not necessarily the active rule file. The active rule file is recorded in the group container preference:

```bash
plutil -p "$HOME/Library/Group Containers/group.com.liguangming.Shadowrocket/Library/Preferences/group.com.liguangming.Shadowrocket.plist" \
  | grep CurrentRuleFileName -A1
```

Edit that active `*.db`, not just the newest subscription DB.

## Diagnosis ladder

1. Check active rule file:

```bash
plutil -p "$HOME/Library/Group Containers/group.com.liguangming.Shadowrocket/Library/Preferences/group.com.liguangming.Shadowrocket.plist" \
  | grep CurrentRuleFileName -A1
```

2. Inspect system proxy and fake-IP symptoms:

```bash
scutil --proxy
nslookup gitlab.uaec.net
 dscacheutil -q host -a name gitlab.uaec.net
```

`nslookup` may query Shadowrocket fake-IP DNS and return `198.18.*` while the system resolver returns the real IP. Do not conclude from `nslookup` alone.

3. Split Git/SSH from browser/HTTPS:

```bash
ssh -T git@gitlab.uaec.net
curl -Iv https://gitlab.uaec.net
HTTPS_PROXY=http://127.0.0.1:1082 curl -Iv https://gitlab.uaec.net
```

If direct `curl`/SSH works but the `HTTPS_PROXY=127.0.0.1:1082` probe times out, the browser is likely failing through the local HTTP proxy CONNECT path even though Git/SSH succeeds.

4. In the active config DB, add the target domain to all relevant surfaces by key name, not by hard-coded docid:

- `rule`: `DOMAIN`, `<domain>`, `DIRECT`
- `general skip-proxy`: append `<domain>`
- `general always-real-ip`: append `<domain>`

Do not assume `docid=2` is `skip-proxy`; inspect `c1name='skip-proxy'`.

5. Restart Shadowrocket/MacPacketTunnel and re-test both paths:

```bash
killall Shadowrocket MacPacketTunnel 2>/dev/null || true
open /Applications/Shadowrocket.app
ssh -T git@gitlab.uaec.net
curl -Iv https://gitlab.uaec.net
HTTPS_PROXY=http://127.0.0.1:1082 curl -Iv https://gitlab.uaec.net
```

## Reporting rule

Report browser and Git results separately. “Git fetch works” does not prove browser access, because browser HTTPS may still be using the macOS HTTP proxy while Git SSH is taking a different route.

## Anti-conditions

- Do not store proxy credentials, subscription URLs, or tokens in skill files.
- Do not generalize a specific domain/IP as globally special; parameterize the domain.
- Do not claim Shadowrocket is broken. Capture the active-config lookup and split-path diagnostic pattern.
