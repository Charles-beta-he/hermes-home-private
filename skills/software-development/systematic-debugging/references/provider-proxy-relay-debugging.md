# Provider proxy/TUN relay debugging

Use when an LLM provider endpoint times out or behaves differently through a CLI wrapper than through a raw API probe, especially on macOS with VPN/TUN/fake-ip products.

## Applicability

- Provider calls hang, return empty output, or time out through an agent/CLI wrapper.
- Raw HTTP probes, DNS, or curl show different behavior depending on proxy/TUN state.
- The endpoint is provider-specific (for example a token-plan or account-scoped base URL), not the vendor's public default endpoint.

Anti-conditions:
- Do not conclude the provider is generally broken from one network path.
- Do not replace an account-scoped base URL with a generic vendor endpoint unless the provider docs/account page confirms the key is valid there.
- Do not store API keys in skills, reports, command-line args, or logs.

## Debugging path

1. Identify the configured base URL from the account console/config, not from memory.
2. Redact and verify credential presence only by variable name, length, or prefix class; never print the full key.
3. Compare three layers separately:
   - raw OpenAI-compatible request to the configured endpoint;
   - the agent/CLI wrapper path;
   - DNS/proxy/TUN routing.
4. Check whether the hostname resolves to fake-ip ranges such as `198.18.0.0/15`. If it does, ordinary `NO_PROXY` may not be enough because the TUN layer has already intercepted the route.
5. Query public/resolver DNS for the real A records, then test both proxy and no-proxy paths. Use this to distinguish:
   - provider/auth/model error (fast HTTP 401/403/404/429);
   - network/TUN timeout (TLS/SSL timeout, remote IP in fake-ip range);
   - wrapper/adapter opacity (raw API returns quickly but wrapper times out silently).
6. If the local VPN is global-only and cannot add per-domain DIRECT rules, do not keep fighting local proxy env vars. Introduce a remote relay/off-machine adapter that runs on a network path allowed to reach the provider.

## Durable fix pattern

- Prefer a direct provider adapter with bounded timeout and structured errors over a black-box CLI wrapper for certification fan-out.
- Add health/circuit-breaker state so a bad provider does not block quorum indefinitely.
- Make health filtering min-quorum aware: hard-skip auth/model-invalid failures, but allow transient failures to be restored if filtering would starve the quorum.
- For global-only VPN/TUN setups, support a relay command that accepts request JSON on stdin and returns provider JSON on stdout. Keep secrets out of argv.

Example relay shape:

```bash
export PROVIDER_RELAY_COMMAND='ssh host python3 ~/provider_relay_worker.py'
```

The local adapter should pass `{base_url, model, messages, temperature, max_tokens, api_key}` over stdin. The remote worker performs the HTTPS call and prints the OpenAI-compatible JSON response.

## Verification checklist

- DNS: configured provider host does not unexpectedly resolve only to fake-ip, or fake-ip behavior is understood.
- Raw API: configured endpoint returns either model output or a fast, classified HTTP/provider error.
- Wrapper/adapter: fails fast with the same class instead of silent timeout.
- Health cache: records provider, adapter, reason, and unhealthy TTL without leaking credentials.
- Relay path: validated with a fake relay first, then with a real remote host if available.
