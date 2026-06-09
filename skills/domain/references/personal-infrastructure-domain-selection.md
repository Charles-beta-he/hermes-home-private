# Personal infrastructure domain selection

Use when choosing a domain for a user's personal assistant, webhook, tunnel, or long-lived infrastructure endpoint.

## Pattern

Prefer a user-owned/personal umbrella domain plus purpose subdomains over vendor/product-name domains.

Good shape:

```text
<user-name-or-brand>.dev
rokid.<user-domain>
hermes.<user-domain>
api.<user-domain>
brain.<user-domain>
```

Why:

- Keeps the domain useful after a single device/vendor changes.
- Avoids trademark/brand-risk names such as `rokidagent.com` or other vendor-product combinations.
- Lets one verified DNS Zone support multiple future services.
- Works well with Cloudflare named tunnels because the Zone must exist before `cloudflared tunnel login` can authorize.

## Quick availability check

Use RDAP/DNS as a fast precheck, but treat it as advisory until the registrar confirms purchase availability.

```bash
python3 - <<'PY'
import socket
for d in ['example.dev','example.cloud']:
    try:
        socket.getaddrinfo(d, 80)
        print(d, 'has_dns')
    except socket.gaierror:
        print(d, 'no_dns_or_available_candidate')
PY
```

## Recommendation rule

When the endpoint is for a personal assistant or agent control plane, recommend the personal umbrella first; use subdomains for vendors/devices.
