# Shadowrocket Config vs Proxy mode: MiMo/token-plan-cn diagnostics

Use this reference when a macOS Shadowrocket user says a domain only works in global mode, CLI traffic behaves differently from browser traffic, or a China/domestic API such as Xiaomi MiMo `token-plan-cn.xiaomimimo.com` times out behind VPN/proxy.

## Key lesson

Do not assume `NO_PROXY` or changing an app's base URL will fix macOS Shadowrocket failures. First distinguish:

- `GlobalRoutingMethod = Proxy`: global proxy mode; rules/config do not decide DIRECT/PROXY even if the rule file contains the domain.
- `GlobalRoutingMethod = Config`: rule/config mode; TUN/fake-ip may still exist, but Shadowrocket should apply the selected rule file.

A domain can appear in a `.db.rule` file and still be ignored if the active global routing method is `Proxy`.

## Read-only diagnosis commands

```bash
BASE="$HOME/Library/Group Containers/group.com.liguangming.Shadowrocket"
PREF="$BASE/Library/Preferences/group.com.liguangming.Shadowrocket.plist"

plutil -p "$PREF" | grep -E 'GlobalRoutingMethod|CurrentRuleFileName'
scutil --proxy
scutil --dns | sed -n '1,120p'
route -n get default
ifconfig | grep -E '^(utun|en)[0-9]*:|inet '
lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(1082|1080|7890|7891)\\b' || true
ps axww -o pid,ppid,command | grep -Ei 'Shadowrocket|MacPacketTunnel' | grep -v grep || true

dig +short token-plan-cn.xiaomimimo.com A
strings "$BASE"/*.rule 2>/dev/null | grep -Ei 'token-plan-cn|xiaomimimo' || true
```

Interpretation:

- default route on `utun*` + DNS resolver `198.18.0.2` + domains resolving to `198.18.x.x` means NetworkExtension/TUN/fake-ip is active.
- `HTTPProxy : 127.0.0.1` and port `1082` only shows the local proxy listener; it does not explain TUN-layer capture.
- If `GlobalRoutingMethod=Proxy`, domain rules are not the active routing decision path.

## Safe switch test: Proxy -> Config

Only do this with user permission because it affects the whole machine's network.

1. Back up preferences:

```bash
BASE="$HOME/Library/Group Containers/group.com.liguangming.Shadowrocket"
PREF="$BASE/Library/Preferences/group.com.liguangming.Shadowrocket.plist"
cp "$PREF" "$PREF.backup-config-switch-$(date +%Y%m%d-%H%M%S)"
```

2. Set routing method to Config:

```bash
python3 - <<'PY'
from pathlib import Path
import plistlib
p = Path.home() / 'Library/Group Containers/group.com.liguangming.Shadowrocket/Library/Preferences/group.com.liguangming.Shadowrocket.plist'
with p.open('rb') as f:
    data = plistlib.load(f)
old = data.get('group.com.liguangming.GlobalRoutingMethod')
data['group.com.liguangming.GlobalRoutingMethod'] = 'Config'
with p.open('wb') as f:
    plistlib.dump(data, f, fmt=plistlib.FMT_BINARY)
print({'old': old, 'new': data.get('group.com.liguangming.GlobalRoutingMethod')})
PY
```

3. Restart Shadowrocket / packet tunnel:

```bash
osascript -e 'tell application "Shadowrocket" to quit' || true
sleep 2
pkill -TERM -f '/Applications/Shadowrocket.app/Contents/PlugIns/MacPacketTunnel.appex' || true
pkill -TERM -x Shadowrocket || true
sleep 3
open -a Shadowrocket
sleep 8
```

4. Verify:

```bash
plutil -p "$PREF" | grep -E 'GlobalRoutingMethod|CurrentRuleFileName'
dig +short token-plan-cn.xiaomimimo.com A
curl -sS --connect-timeout 8 --max-time 20 https://token-plan-cn.xiaomimimo.com/v1/models
```

`/v1/models` may return 401 without an Authorization header; that is still better than SSL timeout because it proves endpoint reachability.

## Xiaomi MiMo-specific checklist

- Use the Token Plan console's dedicated OpenAI-compatible Base URL, commonly:
  `https://token-plan-cn.xiaomimimo.com/v1`
- Do not blindly switch to `https://api.xiaomimimo.com/v1`; token-plan API keys may be scoped to the dedicated endpoint.
- V2 -> V2.5 notifications are model-name migration signals, not necessarily endpoint migration signals. First verify current model names and endpoint separately.
- Probe with a tiny `/chat/completions` request and a short timeout; classify timeout vs 401/auth vs 200 separately.

## Anti-conditions

Do not save a durable conclusion that Shadowrocket, Xiaomi MiMo, or a provider is globally broken. This is a local mode/routing diagnosis pattern. If Config mode or a relay fixes it, capture the fix path, not the transient failure.
