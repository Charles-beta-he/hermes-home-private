# P1 Runtime Target Analysis — Context Engineering OS

Timestamp: 2026-07-08T03:18:00Z
Mode: read-only Hermes repo inspection.

## Readback

Hermes source checkout:

```text
/Users/charles/.hermes/hermes-agent
branch: private/main...origin/private/main
head: b638a0194 feat(cli): add dependency health startup probe
```

Relevant Hermes AGENTS.md constraints discovered during read-only inspection:

- Per-conversation prompt caching is sacred.
- Core is a narrow waist; capability should live at edges where possible.
- Prefer, in order: extend existing code -> CLI command + skill -> service-gated tool -> plugin -> MCP -> new core tool as last resort.
- System prompt should remain byte-stable for a conversation.

## Decision

Do not immediately wire Context Engineering Packet guidance into the core system prompt from this session.

Reason: Context Engineering OS is currently better landed as an edge capability: skill + SSOT + local scripts + future CLI/eval harness. Direct runtime prompt assembly changes risk prompt-cache invalidation, core prompt bloat, or global behavior drift unless a default-off config gate and focused tests are designed in the Hermes source repo.

## Revised P1 Path

Preferred next P1 ladder:

1. Add edge CLI/helper, not core prompt mutation:
   - candidate command shape: `hermes context packet lint <packet.json>`
   - candidate command shape: `hermes context eval run <project-fixtures>`
2. Keep `context-engineering-os` skill as the routing surface.
3. Only after CLI/eval proves useful, consider config-gated prompt preflight:
   - `agent.context_engineering_packet_preflight: false` by default;
   - inject only for complex/high-risk tasks;
   - prove enabled/disabled/tool-unavailable paths;
   - prove prompt-cache invariants and byte-stable behavior for ongoing conversations.

## Boundary

Core runtime modification is not performed in this slice.

Opening condition for next slice:
- exact Hermes source target and permission to edit core/CLI files;
- focused test path identified;
- rollback/readback command set;
- acceptance that default-off config-gated behavior is the maximum safe initial runtime exposure.
