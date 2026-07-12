# Agent CLI Startup Handshake Control Plane

Applicability: use when designing or auditing terminal-native Agent startup UX, readiness banners, statusline badges, mode/plugin visibility, or startup self-test flows for Hermes-like CLI agents.

Anti-conditions: do not use this pattern to justify automatic LLM calls, OAuth refreshes, config writes, gateway sends, plugin enablement, deep diagnostics, or session-history mutation during startup.

## Pattern

Treat startup as a read-only control-plane handshake, not as the first assistant turn.

Recommended framing:

```text
CLI launch
  -> fast local read-only probes
  -> health/mode/capability reducer
  -> banner/statusline/widget projection
  -> explicit slash-command repair paths
```

This is Runtime Engineering, not ordinary prompt engineering. The prompt/cache/data plane remains stable while the UI/control plane renders current runtime facts.

## Startup probe contract

Every default startup probe should be:

- read-only: no config/auth/plugin/session mutation
- local-only: no network, no provider call, no LLM call
- fast: bounded by a small timeout and never blocks first input
- fail-soft: probe failures become warnings, not startup failure
- redacted: no raw keys/tokens/secrets
- cache-safe: no dynamic probe output inserted into the frozen system prompt
- history-safe: no synthetic user/assistant turn added to conversation history
- actionable: warnings point to explicit commands such as `/status`, `/doctor`, `/plugins`, `/auth`, or `hermes setup`

## Layering

1. Hot path handshake: compact summary in banner/statusline, based on local config, profile, provider selection, terminal backend, project context presence, skill index, mode flags, cached gateway/cron status, and plugin/mode registry.
2. Deferred probes: async slow-but-safe checks that update a widget/status indicator without blocking input.
3. Deep doctor: explicit command only for network, refresh, repair, write, or high-latency checks.

## UI projection

Prefer small, composable projections:

- banner: one-time compact readiness summary
- statusline: persistent mode/risk badges (`[SAFE]`, `[YOLO]`, `[CAVEMAN]`, `[WARN 2]`)
- extra widget/panel: collapsible startup detail
- slash command: full local readback and repair routing

Mode/plugin badges should register through a shared Runtime Mode Registry rather than each plugin patching UI independently.

## Pitfalls

- Do not auto-send a “test” prompt to the model at launch; it wastes tokens, slows startup, pollutes history, and can break prompt-cache assumptions.
- Do not treat optional unconfigured providers as startup errors unless the active mode requires them.
- Do not display all possible missing integrations; show only actionable gaps relevant to the current profile/session.
- Do not let startup checks become hidden side-effect executors.

## Verification checklist

- Startup path works offline.
- No LLM/API call occurs before the first user prompt.
- Probe timeout/failure does not block input.
- Secrets are redacted.
- `off | compact | full` display modes work if configurable.
- Statusline remains readable on narrow terminals.
- `/startup` or `/status` readback matches the compact banner summary.
- System prompt bytes remain stable for a fixed config; dynamic probe output is not injected into cached prompt layers.
