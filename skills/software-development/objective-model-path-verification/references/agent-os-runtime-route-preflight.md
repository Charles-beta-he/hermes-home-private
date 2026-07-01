# Agent OS Runtime Route Preflight

Scope: Hermes Agent self-architecture / workflow-control-plane runtime transitions where the advisory Agent OS surface is already live and the user explicitly authorizes opening the next local routing boundary.

Applicability: use after `agent.agent_os_advisory_guidance=true` has been verified and the next safe step is to make Agent OS routing advice participate in path selection. This is still a local prompt/runtime-preflight layer, not an executor.

Anti-conditions:
- Do not treat route preflight as permission for Agent OS to invoke tools, spawn workers, write scheduler/taskpool/mission lifecycle, send external messages, push, deploy, publish, or perform destructive actions.
- Do not invent an external target or payload from broad wording such as “全部允许” / “授权继续”. Consume only the next already-named boundary.
- Do not call the route command with unsupported flags. Current CLI shape is positional: `hermes agent-os route --json '<intent>'`, not `--intent <intent>`.

## Procedure

1. Read back current Agent OS state first:
   - `hermes agent-os status --json`
   - `hermes agent-os doctor --json`
2. Confirm advisory is already live and doctor is clean.
3. Land the next smallest code/config boundary: `agent.agent_os_runtime_routing` / equivalent local route-preflight switch.
4. Prompt wording must require route preflight for governed Hermes/workflow/high-side-effect intents, while explicitly saying suggested nodes are not executed automatically.
5. Status/readback should project both:
   - `agent_os_runtime_routing=true` / `real_runtime_routing=true` for local route preflight;
   - `tool_invocation_from_agent_os=false` and `external_dispatch=false` for neighboring gates.
6. Add tests for enabled prompt injection and status readback; avoid scattering route-preflight tests into unrelated test classes just because helper names are similar.
7. Enable the config via canonical CLI, then verify fresh prompt construction and a real route smoke:
   - prompt contains the route-preflight guidance and “do not execute the suggested node automatically”;
   - `hermes agent-os route --json '<intent>'` returns `would_execute=false`.
8. Update SSOT/profile/ledger/remaining-gates index, then scoped commit.

## Verification checklist

- `hermes agent-os status --json` shows route preflight enabled and neighboring executor/external gates closed.
- Fresh system prompt contains route-preflight text and no-auto-execute wording.
- Route smoke uses positional CLI syntax and returns `would_execute=false`.
- Focused tests pass.
- Ledger states the precise boundary consumed and the still-closed gates.
