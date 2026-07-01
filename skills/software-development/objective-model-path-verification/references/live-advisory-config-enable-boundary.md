# Live advisory config enable boundary

Scope: Hermes/agent-control-plane projects where a local advisory/readback surface is already implemented behind a default-off config key, and the user gives broad wording such as “全部允许”, “项目级别授权”, or “继续全盘推进”.

Applicability: the next safe action is to enable a **prompt/advisory/readback** surface in live config, not to connect real execution. Anti-condition: do not use this pattern to silently enable real routing, tool invocation, cron/scheduler writes, taskpool/mission lifecycle mutation, worker leases, external dispatch, publish/deploy, credentialed operations, payment, or destructive actions.

## Procedure

1. Consume the broad authorization only as far as the smallest already-defined live boundary.
   - Example: enable `agent.agent_os_advisory_guidance=true` when the code default remains false and the prompt text explicitly says it is not execution permission.
2. Use the product CLI/config command rather than hand-editing config when available.
   - Example: `hermes config set agent.agent_os_advisory_guidance true`.
3. Read back the live config from the canonical config file or CLI.
4. Add/read back status fields that distinguish the opened advisory boundary from still-closed execution gates.
   - Example shape:
     ```json
     {
       "config": {
         "agent_os_advisory_guidance": true,
         "real_runtime_routing": false,
         "tool_invocation_from_agent_os": false,
         "external_dispatch": false
       }
     }
     ```
5. Smoke the prompt/runtime surface that the config affects.
   - For a prompt gate, construct a fresh agent/system prompt and assert both:
     - the advisory command/surface is present;
     - the “not permission to execute/mutate/send/publish/destruct” boundary text is present.
6. Update the SSOT/profile/ledger and remaining-gates index.
7. Run focused tests for both the config/readback surface and the prompt gate.
8. Commit only code changes. Keep user config/profile/ledger artifacts out of source commits unless that repo intentionally tracks them.

## Stop conditions

Stop after the advisory surface is live if the next step lacks an exact target or payload. Broad phrases like “全部允许” reduce conversational friction, but they do not define:

- which real router branch to mutate;
- which tool to invoke on what input;
- which cron/job to create or change;
- which taskpool/mission lifecycle record to write;
- which external target to send to;
- what publish/deploy/destructive action and rollback scope are intended.

For those, produce/read back a next authority packet or ask for the exact target. Do not invent a target just to consume broad authority.

## Verification checklist

- [ ] Config key is read back as enabled.
- [ ] Prompt/advisory surface is present in a fresh runtime construction.
- [ ] Boundary text explicitly says advisory is not execution permission.
- [ ] Status/readback still shows real routing/tool invocation/external dispatch as false.
- [ ] Doctor/report remains OK.
- [ ] Focused tests pass.
- [ ] Ledger records the opened boundary and the still-closed gates.
