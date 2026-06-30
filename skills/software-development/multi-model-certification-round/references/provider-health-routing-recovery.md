# Multi-model provider health and routing recovery

Use this reference when multi-model certification/fanout reports false failures because one provider is timing out, provider CLI errors are hidden behind adapter timeouts, or a local network mode makes a provider unreachable.

## Pattern

1. Separate three layers before changing quorum:
   - model name / provider migration (e.g. V2 -> V2.5)
   - endpoint/API-key scope (dedicated token-plan endpoint vs generic API endpoint)
   - local transport path (proxy/TUN/DNS/fake-ip/CLI adapter)
2. Prefer direct provider probes over black-box agent CLI calls for health classification.
3. Record model health as structured states: `healthy`, `unhealthy`, `last_reason`, `unhealthy_until`, `adapter`, `provider`.
4. Do not permanently remove a model from the quorum. Use a TTL circuit breaker and let successful probes re-enable it.
5. Health filtering must not starve quorum. Treat auth/model-invalid as hard skips, but allow transient timeout/runtime failures to be restored when filtering would leave fewer than `min_quorum` planners.
6. Make every routing entrypoint honor the same runtime health source. `consult_models.py` may already filter `~/.hermes/state/model-health.json`, while `model-router.py`/probe paths can still only check provider credentials unless explicitly wired. Add regression tests that active `status=unhealthy` + future `unhealthy_until` excludes the model, expired health does not, and OAuth presence does not override runtime failure.
7. Provider env maps must distinguish OAuth adapters from plain API providers. Example: `openai-codex` may be OAuth-capable, but plain `openai` should require `OPENAI_API_KEY`; otherwise catalog-only models such as `gpt-5.4` can be routed without a callable runtime.
8. For CLI adapters that may use tools, disable tools in pure JSON planner/verifier calls when max-turns is low. Example: Claude Code with `--max-turns 1` should use `--tools ""` to avoid `error_max_turns` caused by tool_use.

## Provider-specific transport lessons

- If an adapter uses a generic `hermes chat` path and hangs without surfacing HTTP 401/timeout, add or prefer a direct OpenAI-compatible adapter for the provider. The adapter should return bounded, structured failures rather than long silent timeouts.
- If a local VPN/TUN/fake-ip layer makes an endpoint unreachable, support an optional relay command that accepts request JSON on stdin and returns provider JSON on stdout. Do not pass API keys in argv.
- If a provider offers dedicated subscription/token-plan endpoints, do not blindly switch to a generic endpoint when debugging. A key may be valid only on the dedicated base URL.

## Verification checklist

- Tiny raw provider probe returns either 200 or a clear API-level error; transport timeouts are classified separately.
- Planner-level call returns parseable plan JSON or a structured shadow plan with `adapter`, `provider`, and a bounded latency.
- Health snapshot shows successful provider recovery (`status=healthy`, `unhealthy_until=0`) before re-adding it to quorum.
- Full fanout with the target tier meets `min_quorum` after health filtering.
- A failure in one provider does not produce a fake all-model acceptance or a fake all-model outage.

## Anti-conditions

Do not encode a transient provider outage or local credential failure as a durable rule that a provider is unusable. Capture the recovery mechanism and classification path instead.
