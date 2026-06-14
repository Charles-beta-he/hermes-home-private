# macOS iPhone/iPad App Network Triage

Scope: diagnosing a macOS Apple Silicon environment where an iPhone/iPad App Store app opens but app features report network/login failures. Anti-condition: do not persistently classify a specific app, proxy, or site as broken; re-test live state each session.

## Pattern

1. Separate system reachability from app-specific failures.
   - Test domestic and international endpoints with `curl -L --connect-timeout 8 --max-time 15`.
   - Test the target vendor's public website separately from the app.
   - If public websites return 200 but the app feature fails, treat it as app/API/auth/proxy interaction rather than general network failure.

2. Inspect routing and proxy mode.
   - `route -n get default`
   - `scutil --dns`
   - `networksetup -getwebproxy <service>` / `-getsecurewebproxy` / `-getsocksfirewallproxy`
   - `lsof -nP -iTCP -sTCP:LISTEN` for local proxy ports
   - `ps aux | egrep -i 'Shadowrocket|Clash|mihomo|sing-box|Surge|V2ray|Quantumult'`

3. Recognize packet-tunnel/Fake-IP mode.
   - Default route on `utun*` plus DNS answers in `198.18.0.0/15` indicate a tunnel/Fake-IP proxy path even when macOS HTTP/SOCKS proxy settings are disabled.
   - In this mode, app traffic may be captured by the tunnel and fail with HTTP 403 or endpoint policy responses even though generic web browsing works.

4. Verify the installed app variant.
   - Use `mdfind "kMDItemDisplayName == '<app>*'"` and inspect app bundle metadata.
   - iPhone/iPad apps installed on Apple Silicon can have HD/iPad variants with different bundle IDs and older API behavior than the main phone app.
   - Do not assume an HD/iPad app is equivalent to the primary iPhone app.

5. Use CFNetwork logs for app-specific status.
   - `log show --last 5m --style compact --predicate 'process CONTAINS "<ProcessName>"'`
   - Look for `response_status=403`, timeout, DNS failures, or path/interface details.
   - A 403 from CFNetwork is not a connectivity failure; classify it as endpoint/auth/proxy-policy/app-variant interaction.

6. Avoid disruptive fixes by default.
   - Do not turn off VPN/proxy/tunnel or edit routing while the user may be in calls or active sessions.
   - Present a low-risk next step first: try the main/current app variant, use a browser source, or ask permission to test DIRECT rules.
   - If testing proxy impact, prefer a targeted DIRECT rule for the vendor domains over global tunnel shutdown.

## Report format

- System network: OK / degraded / down, with endpoint evidence.
- Proxy/tunnel: mode and evidence (`utun`, Fake-IP, process).
- App variant: installed path, bundle id, version if available.
- App failure class: login-required / endpoint 403 / timeout / DNS / blocked page.
- Next action: app replacement, source fallback, targeted DIRECT test, or manual login boundary.
