# Bytebot desktop-agent reference patterns

Source-verified reference for analyzing desktop-agent/computer-use repos and extracting patterns for Hermes without direct integration.

## Source surface checked

- Repository: `https://github.com/bytebot-ai/bytebot`
- Canonical repo: `bytebot-ai/bytebot`
- Verified surfaces: `README.md`, `docs/core-concepts/architecture.mdx`, `docs/guides/takeover-mode.mdx`, `docs/rest-api/computer-use.mdx`, `docker/docker-compose.yml`, `packages/bytebotd/src/computer-use/*`, `packages/bytebotd/src/mcp/computer-use.tools.ts`, `packages/bytebot-agent/src/agent/*`, `packages/bytebot-agent/prisma/schema.prisma`.

## Architecture pattern

Bytebot is a self-hosted desktop agent, not a browser-only or API-only automation system:

- Containerized Ubuntu 22.04 + XFCE desktop.
- noVNC live desktop access.
- `bytebotd` daemon performs GUI actions via nut.js.
- REST `/computer-use` and MCP computer tools expose actions.
- Agent service orchestrates LLM planning, task/message persistence, summaries, and tool execution.
- UI provides task creation, live viewing, and takeover mode.

Typical ports in the default compose:

- `9990`: desktop daemon / noVNC / computer-use.
- `9991`: agent API.
- `9992`: UI.
- `5432`: PostgreSQL.

## Verified action space

The desktop daemon handles actions including:

- mouse: `move_mouse`, `trace_mouse`, `click_mouse`, `press_mouse`, `drag_mouse`, `scroll`.
- keyboard: `type_keys`, `press_keys`, `type_text`, `paste_text`.
- observation/control: `screenshot`, `cursor_position`, `wait`, `application`.
- file bridge: `write_file`, `read_file`.

The MCP layer exposes corresponding `computer_*` tools.

## Task-state pattern

The Prisma schema uses explicit task states:

- `PENDING`, `RUNNING`, `NEEDS_HELP`, `NEEDS_REVIEW`, `COMPLETED`, `CANCELLED`, `FAILED`.

For Hermes, the durable pattern is: do not fake completion when a GUI agent stalls. Map ambiguous/blocked GUI states to `NEEDS_HELP`/blocked and completed-but-needs-human-validation states to review.

## Takeover mode pattern

Takeover mode is a high-signal pattern for future Hermes computer-use workflows:

- User can interrupt an in-flight task.
- Human input actions are captured into the same action space as agent actions.
- Agent resumes from the demonstrated state.
- Desktop setup mode can be unrecorded, while task takeover is recorded.

Use this as a reference for converting human demonstrations into reusable skill/checklist candidates, not for immediate blind replay.

## Hermes extraction guidance

Absorb as patterns:

1. Containerized disposable desktop boundary instead of controlling the user's host desktop.
2. Unified observe → act → screenshot → verify loop.
3. Explicit `NEEDS_HELP` / `NEEDS_REVIEW` state transitions.
4. Human takeover traces as learning artifacts.
5. REST + MCP dual surface for optional integration.

Reject or gate before adoption:

1. Default unauthenticated local ports must not be exposed beyond loopback.
2. `privileged: true` desktop containers are not a safe default.
3. Screenshot/action traces can contain credentials and require retention/redaction policy.
4. Broad mouse/keyboard/file actions need permission tiers and audit before becoming Hermes tools.
5. Do not treat upstream README demos as reliability evidence; verify deterministic workflows.

## Recommended analysis workflow for similar repos

1. Clone/query canonical repo metadata and commit hash.
2. Read repo-local agent instructions before source inspection.
3. Separate marketing claims from verified code paths.
4. Inspect: deployment boundary, action API, task state machine, auth/default exposure, data retention, and human takeover behavior.
5. Produce a gap matrix: absorb / reject / gated spike / long-term design.
6. If adding to Hermes, start with isolated read-only probes: screenshot/cursor only, no credentials, no host mounts, no mutating actions.
